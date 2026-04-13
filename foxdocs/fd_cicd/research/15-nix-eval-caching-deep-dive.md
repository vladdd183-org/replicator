# Глубокое исследование кеширования Nix eval и fetcher для CI/CD runners

> Дата: 2026-04-10
> Контекст: nspawn-runners с общим snix castore. eval делается каждый раз, не кешируется.
> Ошибка: `attempt to write a readonly database` на `fetcher-cache-v4.sqlite`.
> Цель: максимально ускорить eval + fetcher + build, обеспечить параллельную работу runners.

---

## 1. Анатомия Nix кешей под `$XDG_CACHE_HOME/nix/`

Nix хранит несколько баз данных и каталогов под `$XDG_CACHE_HOME/nix/`:

```
$XDG_CACHE_HOME/nix/
├── fetcher-cache-v4.sqlite          ← ОДИН файл на все операции
│   ├── fetcher-cache-v4.sqlite-wal  ← WAL journal (создаётся SQLite)
│   └── fetcher-cache-v4.sqlite-shm  ← Shared memory (создаётся SQLite)
├── eval-cache-v6/                   ← Директория с PER-FLAKE SQLite файлами
│   ├── <fingerprint-hex-1>.sqlite   ← Кеш eval'а для flake с fingerprint 1
│   ├── <fingerprint-hex-2>.sqlite   ← Кеш eval'а для flake с fingerprint 2
│   └── ...
├── gitv3/                           ← Клонированные git-репозитории (flake inputs)
│   ├── <hash-1>/                    ← Bare git clone
│   ├── <hash-2>/
│   └── ...
├── tarball-cache/                   ← Скачанные tarball'ы
└── flake-registry.json              ← Кешированный глобальный реестр flake'ов
```

### 1.1 `fetcher-cache-v4.sqlite` — Метаданные fetcher'а

**Что хранит**: маппинг `(domain, key) → (value, timestamp)` для всех fetch-операций:
- `gitRevision` → SHA и дата последнего коммита
- `gitLastModified` → timestamp lastModified для git input'ов
- `tarballHash` → narHash скачанных tarball'ов
- `githubApiResult` → ответы GitHub API (rev → tarball URL)

**Критично**: это ОДИН файл на ВСЕ операции. Каждый `nix build`, `nix flake check`,
`nix eval` пишет в него при разрешении input'ов.

**Размер**: обычно 50-500 KB (метаданные, не контент).

### 1.2 `eval-cache-v6/` — Кеш результатов evaluation

**Что хранит**: Каждый flake получает свой SQLite файл, названный по fingerprint'у
(хеш lock file). Внутри — дерево атрибутов:

```sql
CREATE TABLE Attributes (
    parent  integer not null,
    name    text,
    type    integer not null,  -- 0=Placeholder, 1=FullAttrs, 2=String, 3=Bool, ...
    value   text,
    context text,
    primary key (parent, name)
);
```

**Пример содержимого** (после `nix shell nixpkgs#firefox`):
```
(0, '', Placeholder, NULL)
(1, 'legacyPackages', FullAttrs, NULL)
(1, 'packages', Missing, NULL)         ← «отрицательный» кеш
(3, 'x86_64-linux', Placeholder, NULL)
(4, 'firefox', Placeholder, NULL)
(5, 'type', String, 'derivation')
(5, 'drvPath', String, '/nix/store/...-firefox-75.0.drv')
(5, 'outPath', String, '/nix/store/...-firefox-75.0')
```

**Инвалидация**: Fingerprint = хеш содержимого lock file.
Новый коммит → новый lock → новый fingerprint → новый SQLite файл.
Старые кеши не удаляются автоматически (accumulate).

**Эффект**:
- Первый eval (`nix shell nixpkgs#firefox`): ~250ms
- Второй eval с кешем: **~30ms** (8x ускорение)
- `nix search nixpkgs blender` первый: ~6s, второй: **~0.4s** (15x)

### 1.3 `gitv3/` — Git clone cache

**Что хранит**: bare git clones всех flake input'ов типа `github:` и `git+`.

**Размер**: может быть значительным (nixpkgs clone ~500MB).

**Критично для скорости**: без кеша каждый eval скачивает git repo заново.

---

## 2. Диагностика ошибки `attempt to write a readonly database`

### 2.1 Воспроизведение

```
error: executing SQLite statement 'insert or replace into Cache(domain, key, value, timestamp)
values ('gitLastModified', '{"rev":"a8ccdac9..."}', '{"lastModified":1775762510}', 1775762528)':
attempt to write a readonly database, attempt to write a readonly database
(in '/var/cache/nix-runners-shared/nix/fetcher-cache-v4.sqlite')
```

### 2.2 Корневая причина: DynamicUser + SQLite file permissions

```
Runner A (UID 63001)                    Runner B (UID 63002)
─────────────────────                   ─────────────────────
nix flake check                         nix flake check
  │                                       │
  ├─ resolve git input                    ├─ resolve git input
  │                                       │
  ├─ open() fetcher-cache-v4.sqlite       ├─ open() fetcher-cache-v4.sqlite
  │  → O_CREAT|O_RDWR, mode 0644         │  → O_RDWR
  │  → файл создан: -rw-r--r-- 63001     │  → ОШИБКА: permission denied
  │                                       │    (63002 не может писать в файл 63001)
  ├─ SQLite creates .sqlite-wal           │
  │  → -rw-r--r-- 63001                  └─ SQLITE_READONLY error ✗
  │
  └─ INSERT succeeds ✓
```

**Цепочка причин**:

1. `services.github-runners` использует `DynamicUser=yes` — каждый runner получает
   случайный UID из диапазона 61184-65519
2. SQLite создаёт файлы с `open(path, O_CREAT|O_RDWR, 0644)` — только owner может писать
3. `UMask=0000` на systemd service НЕ помогает, потому что `0644 & ~0000 = 0644`
   (umask снимает биты, но 0644 уже не содержит лишних)
4. SQLite WAL/SHM файлы создаются с теми же ограничениями
5. Timer нормализации прав (`chmod a+rw`) запускается раз в 10 минут — race condition

### 2.3 Дополнительная проблема: SQLite concurrent writes

Даже если permissions исправлены, `fetcher-cache-v4.sqlite` — единственный файл,
в который пишут ВСЕ runners одновременно. SQLite WAL mode (с Nix 2.25+) позволяет:
- Множественные concurrent reads ✓
- Один writer + множественные readers ✓
- Множественные writers → SQLITE_BUSY → retry или fail ✗

При параллельной работе 2-3 runners каждый пытается обновить fetcher-cache
при разрешении git input'ов → contention.

---

## 3. Решение: Гибридная архитектура кешей

### 3.1 Принцип: разделяем «горячие» и «общие» кеши

```
┌─────────────────────────────────────────────────────────────────────┐
│ PER-RUNNER: $XDG_CACHE_HOME = /var/cache/nix-runner-<name>         │
│                                                                     │
│ /var/cache/nix-runner-<name>/nix/                                   │
│   ├── fetcher-cache-v4.sqlite     ← PER-RUNNER (нет contention)    │
│   ├── eval-cache-v6/              ← SYMLINK → shared               │
│   ├── gitv3/                      ← SYMLINK → shared               │
│   └── flake-registry.json         ← SYMLINK → shared               │
└─────────────────────────────────────────────────────────────────────┘
         │ symlinks                          │ symlinks
         ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ SHARED: /var/cache/nix-runners-shared/nix/                          │
│                                                                     │
│   ├── eval-cache-v6/     ← PER-FLAKE SQLite файлы                  │
│   │     ├── aabbcc.sqlite   (low collision: разные flakes)          │
│   │     └── ddeeff.sqlite                                           │
│   ├── gitv3/             ← git clones (directory-level locks)       │
│   └── flake-registry.json                                           │
│                                                                     │
│ POSIX Default ACLs: u::rwx,g::rwx,o::rwx                           │
│ → ВСЕ новые файлы автоматически world-readable+writable             │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Почему это работает

| Cache файл | Shared? | Обоснование |
|------------|---------|-------------|
| `fetcher-cache-v4.sqlite` | **PER-RUNNER** | Один файл, все пишут. Contention + readonly. Размер ~100KB, пересоздаётся за миллисекунды |
| `eval-cache-v6/*.sqlite` | **SHARED** | Per-flake файлы (названы по fingerprint). Collision только если 2 runner'а eval'ят ОДИН flake в ОДНО время. Основной выигрыш от кеширования |
| `gitv3/` | **SHARED** | Directory-based, git handles concurrent access. Экономит network I/O |
| `flake-registry.json` | **SHARED** | Read-mostly, обновляется редко |

### 3.3 Обработка concurrent access к shared eval-cache

Два runner'а могут eval'ить один flake (один fingerprint) одновременно:
- Runner A: `nix build python-uv-nix#oci-prod`
- Runner B: `nix flake check python-uv-nix`

Оба пишут в `eval-cache-v6/<same-fingerprint>.sqlite`.

**Решение**: POSIX default ACLs + SQLite WAL mode:

1. Default ACL на `eval-cache-v6/` → новые `.sqlite` файлы создаются с `o::rw-`
2. SQLite WAL mode (Nix ≥2.25) → concurrent reader + single writer
3. При SQLITE_BUSY Nix ретраится или работает без кеша (graceful degradation)

### 3.4 POSIX Default ACLs — ключевой механизм

```bash
# Устанавливаем default ACL на общие директории
setfacl -d -m u::rwx,g::rwx,o::rwx /var/cache/nix-runners-shared/nix/eval-cache-v6
setfacl -d -m u::rwx,g::rwx,o::rwx /var/cache/nix-runners-shared/nix/gitv3

# Результат: ЛЮБОЙ новый файл в этих директориях
# автоматически получает o::rw- (для файлов) или o::rwx (для директорий)
# НЕЗАВИСИМО от UID создателя и mode в open()
```

Это работает потому что:
- Default ACL наследуется из родительской директории при создании файла
- ACL проверяется В ДОПОЛНЕНИЕ к стандартным Unix permissions
- Даже если SQLite создаёт файл с `mode 0644`, ACL `o::rw-` разрешает запись для всех

---

## 4. Конкретные изменения в nspawn-runners module

### 4.1 Изменения в `nspawn-runners/default.nix`

**Было**:
```nix
# Все runners делят один XDG_CACHE_HOME
environment = {
  XDG_CACHE_HOME = sharedCachePath;  # = "/var/cache/nix-runners-shared"
};
```

**Стало**:
```nix
# Per-runner XDG_CACHE_HOME с symlinks на shared кеши
environment = {
  XDG_CACHE_HOME = "/var/cache/nix-runner-${name}";
};
```

Плюс setup-скрипт (ExecStartPre) создаёт symlink-структуру:
```bash
RUNNER_CACHE="/var/cache/nix-runner-${name}/nix"
SHARED="/var/cache/nix-runners-shared/nix"
mkdir -p "$RUNNER_CACHE"
ln -sfn "$SHARED/eval-cache-v6" "$RUNNER_CACHE/eval-cache-v6"
ln -sfn "$SHARED/gitv3" "$RUNNER_CACHE/gitv3"
ln -sfn "$SHARED/flake-registry.json" "$RUNNER_CACHE/flake-registry.json"
```

### 4.2 Tmpfiles rules update

```nix
systemd.tmpfiles.rules = [
  "d ${sharedCachePath} 1777 root root -"
  "d ${sharedCachePath}/nix 1777 root root -"
  "d ${sharedCachePath}/nix/eval-cache-v6 1777 root root -"
  "d ${sharedCachePath}/nix/gitv3 1777 root root -"
];
```

### 4.3 ACL setup (ExecStartPre на нормализацию)

Вместо timer (раз в 10 мин), запускаем нормализацию ПЕРЕД каждым контейнером:

```nix
systemd.services."container@${r.fullName}" = {
  serviceConfig.ExecStartPre = [
    "+${sharedCacheNormalizeScript}"  # + = run as root
  ];
};
```

### 4.4 Улучшенный скрипт нормализации

```bash
set -euo pipefail
cache="/var/cache/nix-runners-shared"
[ -d "$cache" ] || exit 0

# Директории: sticky bit + world-rwx
find "$cache" -type d -exec chmod 1777 {} +

# Файлы: world-rw (включая SQLite WAL/SHM)
find "$cache" -type f -exec chmod a+rw {} +

# Default POSIX ACLs для НОВЫХ файлов (ключевое исправление)
setfacl -R -d -m u::rwx,g::rwx,o::rwx "$cache/nix/eval-cache-v6" 2>/dev/null || true
setfacl -R -d -m u::rwx,g::rwx,o::rwx "$cache/nix/gitv3" 2>/dev/null || true

# Существующие файлы — добавляем o::rw- через ACL
setfacl -R -m o::rwX "$cache" 2>/dev/null || true
```

---

## 5. Кросс-проектное кеширование eval

### 5.1 Как это работает

Flake eval-cache fingerprint = хеш содержимого `flake.lock`.

Если два проекта используют ОДНУ ревизию nixpkgs (один и тот же lock entry):
- `python-uv-nix` с `nixpkgs/nixos-unstable` @ rev `abc123`
- `AutoPosterMonolith` с `nixpkgs/nixos-unstable` @ rev `abc123`

Они НЕ делят eval-cache, потому что fingerprint = хеш ВСЕГО lock file,
а не отдельных input'ов. У каждого flake свой набор input'ов → свой fingerprint.

### 5.2 Что реально переиспользуется

```
Проект A: nix build .#oci-prod
  → eval: python.nix, oci.nix, devshell.nix
  → fetch: nixpkgs (git clone), uv2nix, nix2container
  → build: python venv, OCI image

Проект B: nix build .#oci-prod  (другой проект, те же зависимости)
  → eval: своя конфигурация, СВОЙ eval-cache (другой fingerprint)
  → fetch: nixpkgs — HIT в gitv3/ (тот же clone!) ✓
  → build: python packages — HIT в snix castore (те же derivation'ы!) ✓
```

**Кросс-проектный кеш работает на уровнях**:
1. **gitv3/** — git clones переиспользуются (shared) ✓
2. **snix castore** — build outputs дедуплицируются (content-addressed) ✓
3. **eval-cache** — НЕ переиспользуется между разными flake'ами ✗

### 5.3 Оптимизация: `--override-input` для общего nixpkgs

Если вы хотите, чтобы eval-cache от nixpkgs переиспользовался:

```bash
# Pin nixpkgs к конкретному rev через flake reference
nix build .#oci-prod --override-input nixpkgs github:NixOS/nixpkgs/abc123
```

Но это не практично. Реальный выигрыш — из shared git cache и snix castore.

### 5.4 Issue #10570: Share evaluation caches across installables

Nix issue [#10570](https://github.com/NixOS/nix/issues/10570) предлагает шарить
eval-cache между installables из ОДНОГО flake. Пример:

```bash
# Сейчас: каждая команда eval'ит заново
nix build .#oci-prod    # eval flake → cache
nix build .#oci-stage   # eval flake → ЗАНОВО (другой installable)

# После #10570: один eval кеш для всего flake
nix build .#oci-prod    # eval flake → cache
nix build .#oci-stage   # cache HIT (тот же flake) ✓
```

Это ускоряет CI workflow, где в одном job делается `nix flake check` + `nix build`.
PR с 20x ускорением для 276 packages из одного flake уже существует.

---

## 6. Concurrent runners: полный анализ блокировок

### 6.1 Матрица concurrent access

| Ресурс | Тип | Concurrent readers | Concurrent writers | Стратегия |
|--------|-----|-------------------|--------------------|-----------|
| `fetcher-cache-v4.sqlite` | SQLite WAL | ✅ Множественные | ⚠️ Один (BUSY retry) | **Per-runner** |
| `eval-cache-v6/<fp>.sqlite` | SQLite WAL | ✅ Множественные | ⚠️ Один (BUSY retry) | **Shared + ACLs** |
| `gitv3/<hash>/` | Git bare repo | ✅ Git handles | ✅ Git lock files | **Shared** |
| `flake-registry.json` | JSON файл | ✅ Read-only mostly | ⚠️ Atomic replace | **Shared** |
| snix castore (gRPC) | gRPC service | ✅ Множественные | ✅ Множественные | **Shared** (server) |
| `/nix/store` (overlay upper) | Per-runner FS | ✅ | ✅ | **Per-runner** |

### 6.2 SQLite WAL mode (Nix ≥2.25, PR #13800)

С августа 2025 Nix использует WAL mode для SQLite кешей:

```
Reader A ──read──▶ [WAL] ◀──write── Writer B
Reader C ──read──▶ [WAL]

WAL mode:
  - Readers НИКОГДА не блокируются writers'ами
  - Writers используют file-level lock
  - При конфликте: SQLITE_BUSY → Nix retry с timeout
  - ЕСЛИ timeout истёк: Nix работает без кеша (graceful degradation)
```

**Важно**: WAL mode требует, чтобы `-wal` и `-shm` файлы были доступны ВСЕМ
процессам. Это именно то, что ломается с DynamicUser.

### 6.3 snix castore — concurrent access

snix store daemon — gRPC сервер. Множественные клиенты (runners) обращаются к нему
параллельно. Daemon внутри использует:
- **redb** (embedded key-value store с MVCC) для metadata
- **objectstore** для блобов (файловая система, atomic writes)

Concurrent access обеспечивается на уровне gRPC сервера + redb transactions.
Runners НЕ блокируют друг друга при `nix copy --to snix` или чтении через FUSE.

---

## 7. Полный план оптимизации

### 7.1 Уровни ускорения (от наибольшего эффекта к наименьшему)

| # | Оптимизация | Эффект | Сложность | Статус |
|---|------------|--------|-----------|--------|
| 1 | snix castore (shared build cache) | 10-100x для повторных build'ов | ✅ Уже работает | Done |
| 2 | Shared eval-cache | 5-15x для повторных eval'ов | 🔧 Нужен fix permissions | **TODO** |
| 3 | Shared gitv3 cache | 2-5x для fetch input'ов | 🔧 Нужен fix permissions | **TODO** |
| 4 | Per-runner fetcher-cache (fix readonly) | Убирает crashes | 🔧 Архитектурное изменение | **TODO** |
| 5 | Pre-populated eval cache | 2-5x для первого eval на новом rev | 🔮 Будущее | Planned |
| 6 | `--eval-store` (centralized eval) | Eliminates eval entirely | 🔮 Экспериментальное | Research |
| 7 | Параллелизация eval в CI workflow | 1.5-2x для multi-step CI | ✅ Уже в python-uv-nix CI | Done |

### 7.2 Будущие оптимизации

#### Pre-populated eval cache (download from binary cache)

Из статьи Eelco Dolstra (2020): в будущем Nix может скачивать готовые eval-cache
с cache.nixos.org. Для нашего случая:

```bash
# Гипотетический flow:
# 1. CI на main: eval flake → upload eval-cache sqlite в S3/Attic
# 2. CI на branch: download eval-cache → eval мгновенный

# Это можно реализовать уже сейчас вручную:
FINGERPRINT=$(nix flake metadata --json | jq -r '.fingerprint')
# Upload:
aws s3 cp ~/.cache/nix/eval-cache-v6/${FINGERPRINT}.sqlite s3://nix-caches/eval/
# Download на другом runner'е:
aws s3 cp s3://nix-caches/eval/${FINGERPRINT}.sqlite ~/.cache/nix/eval-cache-v6/
```

#### `--eval-store` для централизованного eval

```bash
# Eval на центральном сервере, build на runner'е
nix path-info --eval-store ssh-ng://eval-server .#oci-prod
```

Это полностью убирает eval на runner'е. Но требует:
- Отдельный eval-server с мощным CPU
- nix daemon protocol поддержка на eval-store
- Не поддерживается для всех store implementations

---

## 8. Сравнение с Docker layer caching

| Аспект | Docker layers | Nix + snix castore |
|--------|--------------|-------------------|
| Гранулярность | Layer (десятки MB) | Store path (~1 package) или chunk (4KB-1MB) |
| Инвалидация | Каскадная (изменение layer N → rebuild N+1, N+2, ...) | **Точечная** (изменился 1 пакет → пересобирается только он) |
| Дедупликация | По layer hash (грубая) | **Content-addressed chunking** (тонкая, cross-project) |
| Eval overhead | Нет (Dockerfile — императивный) | Есть (Nix lang — оценка 0.3-6s) |
| Кросс-проект sharing | Только base image layers | **Полное**: packages, chunks, git clones |
| Concurrent builds | Docker BuildKit handles | Nix daemon + snix handles |

**Пример**:
```
Docker: изменился apt install → пересобираем pip install + COPY . → 3-5 мин
Nix:    изменился один system dep → пересобирается ТОЛЬКО он → 5-10 сек
        pip deps не изменились → snix cache hit → 0 сек
```

---

## 9. Рекомендуемый порядок внедрения

1. **Немедленно**: Исправить permissions в nspawn-runners (POSIX default ACLs)
2. **Немедленно**: Per-runner fetcher-cache + shared eval-cache/gitv3 (symlinks)
3. **Немедленно**: ExecStartPre нормализация вместо timer-only
4. **Краткосрочно**: Добавить `NIX_CACHE_HOME` env var (Nix-специфичный, приоритет над XDG)
5. **Среднесрочно**: Eval-cache upload/download между CI runs
6. **Долгосрочно**: Централизованный eval-store

---

## Ресурсы

| Документ | URL / Путь |
|----------|-----------|
| Nix eval-cache source | https://github.com/NixOS/nix/blob/main/src/libexpr/eval-cache.cc |
| PR #13800 (WAL mode) | https://github.com/NixOS/nix/pull/13800 |
| Issue #10570 (shared eval cache) | https://github.com/NixOS/nix/issues/10570 |
| Issue #3794 (SQLite busy) | https://github.com/NixOS/nix/issues/3794 |
| PR #11351 (NIX_CACHE_HOME) | https://github.com/NixOS/nix/pull/11351 |
| DeepWiki: Evaluation Cache | https://deepwiki.com/NixOS/nix/2.5-evaluation-cache |
| Eelco Dolstra: Flakes eval caching | https://www.tweag.io/blog/2020-06-25-eval-cache/ |
| SQLite WAL + multi-user | https://stackoverflow.com/questions/69728806 |
| nspawn-runners module | vladOS-v2/modules/nixos/services/nspawn-runners/default.nix |
| snix module | vladOS-v2/modules/nixos/services/snix/default.nix |
