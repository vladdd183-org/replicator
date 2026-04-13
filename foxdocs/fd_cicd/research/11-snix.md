# 🚀 Snix — ускорение Nix сборок через content-addressed storage и overlay-store

> Глубокое исследование Snix (бывш. Tvix) — модульной Rust-реимплементации компонентов Nix.
> Content-addressed хранилище, overlay-store, pluggable builders, интеграция в CI/CD.

---

## 📋 Паспорт проекта

| Параметр | Значение |
|----------|----------|
| 📛 Название | Snix (ранее Tvix) |
| 🔗 Репозиторий | [git.snix.dev/snix/snix](https://git.snix.dev/snix/snix) |
| 🌐 Сайт | [snix.dev](https://snix.dev/) |
| 📝 Лицензия | GPLv3 |
| 🦀 Язык | Rust (39.9%) + Nix (58%) |
| 📊 Коммиты | 22 264+ |
| 💰 Финансирование | [NLnet](https://nlnet.nl/project/Snix-Store_Builder/) |
| 📅 Форк из Tvix | Март 2025 |
| 🏗️ Статус | Активная разработка, **не** drop-in замена Nix |

---

## 1. 🧬 Что такое Snix

### Происхождение

Snix — **форк проекта Tvix**, который развивался внутри TVL (The Virus Lounge) монорепозитория. В марте 2025 проект выделился в независимую инфраструктуру из-за:

- **Конфликтующих приоритетов** между нуждами TVL-сообщества и целями Tvix
- **Сложного онбординга** — новым контрибьюторам приходилось клонировать весь монорепозиторий и отправлять патчи по email
- **Проблем CI** — регрессионные тесты Tvix конфликтовали с обновлениями nixpkgs в TVL
- **Архитектурных разногласий** — какие части системы приоритизировать

### Что это НЕ является

```
⚠️  Snix — это НЕ drop-in замена Nix CLI.
⚠️  API нестабильны.
⚠️  Нет полнофункциональной замены nix-build.
```

### Что это ЯВЛЯЕТСЯ

Snix — это **модульная библиотечная реимплементация компонентов Nix на Rust**, которая:

1. **Предоставляет отдельные компоненты** — castore, store, evaluator, builder — которые можно комбинировать
2. **Library-first подход** — встраивается в другие проекты как библиотека
3. **Совместима с Nixpkgs** — генерирует те же build expressions bit-to-bit
4. **Использует content-addressed storage** — принципиально другая модель хранения данных

---

## 2. 🏛️ Архитектура компонентов

### Обзор модулей

```
┌──────────────────────────────────────────────────────┐
│                    snix-cli (REPL)                    │
├──────────────────────────────────────────────────────┤
│                     snix-glue                        │
│         (import builtins, fetchers, build dispatch)   │
├──────────────┬──────────────┬────────────────────────┤
│  snix-eval   │ snix-build   │     nar-bridge         │
│  (bytecode   │ (pluggable   │  (HTTP Binary Cache    │
│   VM, Nix    │  builders:   │   ← snix-[ca]store)    │
│   builtins)  │  OCI, gRPC)  │                        │
├──────────────┴──────────────┴────────────────────────┤
│                    snix-store                         │
│          (PathInfo, NAR calc, signing, refs)          │
├──────────────────────────────────────────────────────┤
│                   snix-castore                        │
│       (Merkle DAG, content-addressed blobs,          │
│        chunked storage, FUSE/virtiofs mount)         │
├──────────────────────────────────────────────────────┤
│                   nix-compat                          │
│    (ATerm, NAR, NARInfo, nix.conf, store paths,      │
│     signatures, binary cache protocol)               │
└──────────────────────────────────────────────────────┘
```

### Ключевые компоненты

#### snix-castore — движок хранения

- **Не Nix-специфичный** — универсальный content-addressed storage engine
- Хранит файловые деревья как **Merkle DAG** (аналогия: git tree/blobs, но BLAKE3)
- **Content-defined chunking** — файлы разбиваются на чанки по содержимому
- Идентичные чанки между разными версиями пакетов хранятся **только один раз**
- Поддерживает FUSE и virtiofs для монтирования store

#### snix-store — Nix store поверх castore

- Хранит метаданные: имена store path, NAR хеши, ссылки, подписи
- Делегирует хранение содержимого в snix-castore
- Предоставляет gRPC API для взаимодействия

#### snix-build — pluggable builder

- **OCI builder** — создаёт OCI Runtime Spec, монтирует inputs через castore, вызывает `runc`
- **gRPC client/server** — позволяет запускать сборки удалённо
- **Стандартизированный протокол** — не завязан на Nix internals
- Планируются бэкенды: Kubernetes, bwrap, gVisor, Cloud Hypervisor

#### nar-bridge — HTTP Binary Cache

- Nix HTTP Binary Cache сервер (read-write)
- Использует snix-[ca]store для хранения данных
- Позволяет хостить собственный binary cache

---

## 3. 📦 Content-Addressed Storage Model

### Как это работает

В отличие от Nix, где store paths адресуются по **входам** (input-addressed), snix-castore адресует данные по **содержимому** (content-addressed).

#### Три типа объектов

```
┌─────────────────────────────────────────────────────────┐
│  PathInfo                                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ output path hash → root node (Dir/File/Symlink)     │ │
│  │ + references, nar hash, nar size, signatures        │ │
│  └─────────────────────────────────────────────────────┘ │
│           │ указывает на ↓                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Directory (Merkle DAG)                              │ │
│  │ - child files: name + BLAKE3 hash                   │ │
│  │ - child dirs: name + BLAKE3 hash → рекурсия         │ │
│  │ - child symlinks: name + target                     │ │
│  └─────────────────────────────────────────────────────┘ │
│           │ файлы → ↓                                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Blob (chunked)                                      │ │
│  │ - содержимое файла, разбитое на чанки               │ │
│  │ - BLAKE3 tree hash → verified streaming             │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Дедупликация — реальные цифры

**Кейс Replit** (март 2025):
- У Replit был persistent disk с Nix store размером **6 ТБ** (20+ ТБ до оптимизации)
- Перешли на tvix-store (snix-castore) с content-defined chunking
- Результат: **6 ТБ → 1.2 ТБ** (сокращение на **80%**)
- Экономия на хранении: **~90%**

Почему это работает:

```
# Пример: два пакета python-3.11.8 и python-3.11.9
# Содержат ~95% идентичных файлов
# В обычном Nix store — полная копия обоих (~200 МБ × 2)
# В snix-castore — общие чанки хранятся 1 раз, только дельта отдельно

Обычный Nix store:
  /nix/store/abc...-python-3.11.8/ → 200 MB
  /nix/store/def...-python-3.11.9/ → 200 MB
  Итого: 400 MB

snix-castore (content-addressed + chunking):
  Общие чанки: ~190 MB (хранятся один раз)
  Уникальные чанки 3.11.8: ~10 MB
  Уникальные чанки 3.11.9: ~10 MB
  Итого: ~210 MB (экономия ~47%)
```

При масштабе тысяч пакетов и десятков версий эффект мультипликативный.

---

## 4. 🗂️ Overlay-Store — механизм наслаивания store

### Что такое Local Overlay Store

**Local Overlay Store** — экспериментальная фича Nix (с ~2024), использующая Linux OverlayFS для комбинирования нескольких store в один логический store.

```
                    ┌───────────────────────┐
                    │   Merged /nix/store    │  ← Nix видит это
                    │   (OverlayFS mount)    │
                    └───────┬───────────────┘
                            │
               ┌────────────┴────────────┐
               │                         │
    ┌──────────▼──────────┐   ┌──────────▼──────────┐
    │   Upper Layer (rw)  │   │  Lower Layer (ro)    │
    │  /opt/nix/store     │   │  snix FUSE mount     │
    │                     │   │  или host /nix/store │
    │  Новые сборки       │   │                      │
    │  идут сюда          │   │  Огромный кеш         │
    └─────────────────────┘   └──────────────────────┘
```

### Принцип работы

1. **Lower layer (read-only)** — большой store, который не модифицируется
   - Может быть: локальный store, daemon store, snix FUSE mount, другой overlay store
   - Nix **не перестраивает** пакеты, которые уже есть в lower layer
   
2. **Upper layer (read-write)** — "патч" поверх lower layer
   - Сюда записываются результаты новых сборок
   - Сам по себе невалидный store (dangling references на lower layer)
   
3. **Merged mountpoint** — OverlayFS объединяет оба слоя
   - Нижний слой "просвечивает" через верхний
   - Записи идут только в upper layer (copy-on-write)
   - **Нативная производительность** после open() файла

### Copy-on-Write через OverlayFS

```bash
# Чтение файла: OverlayFS ищет сначала в upper, потом в lower
# → если файл есть в lower — читает оттуда (zero copy)

# Запись нового файла: создаётся в upper layer
echo "new" > /nix/store/xxx-new-pkg/file
# → файл физически в /opt/nix/store/xxx-new-pkg/file

# Модификация файла из lower: копируется в upper (copy-on-write)
echo "modified" > /nix/store/yyy-existing-pkg/file
# → копия в upper, lower не затронут

# Удаление файла из lower: создаётся whiteout в upper
rm /nix/store/yyy-existing-pkg/old-file
# → whiteout-маркер в upper, lower не затронут
```

### Как Snix использует overlay-store

Snix может выступать **нижним слоем (lower store)** в Local Overlay Store:

```
┌─────────────────────────────────────────────────┐
│              Nix CLI / nix-daemon                │
│         (видит merged /nix/store)                │
├─────────────────────────────────────────────────┤
│              local-overlay-store                 │
│                                                  │
│  ┌─────────────┐     ┌────────────────────────┐ │
│  │ Upper Layer  │     │     Lower Layer        │ │
│  │ (локальный   │     │  (snix nix-daemon      │ │
│  │  Nix store)  │     │   + snix FUSE mount)   │ │
│  │              │     │                        │ │
│  │ Новые пакеты │     │  Огромная база         │ │
│  │ и сборки     │     │  пакетов с             │ │
│  │              │     │  дедупликацией          │ │
│  └─────────────┘     └────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**Преимущество**: snix-castore хранит lower layer **значительно компактнее** обычного Nix store (до 5-6× за счёт content-defined chunking), при этом Nix работает с ним прозрачно.

---

## 5. ⚡ Как Snix ускоряет сборки — конкретные механизмы

### 5.1 Дедупликация хранилища → меньше данных для скачивания/копирования

```
Механизм: Content-defined chunking + Merkle DAG
Эффект:   Объём store сокращается в 3-6 раз
Влияние:  Меньше I/O при копировании, меньше сетевого трафика
```

Когда store путь уже существует в castore (даже частично — на уровне чанков), Snix не скачивает/не копирует повторно идентичные данные.

### 5.2 Copy-on-Write через OverlayFS → мгновенное "подключение" store

```
Механизм: OverlayFS lower layer с большим кешем store paths
Эффект:   Новый CI job видит все пакеты "мгновенно"
Влияние:  Нет холодного старта (~0 секунд на "восстановление кеша")
```

В CI это означает: runner видит полный `/nix/store` с первой секунды, без `nix copy` или substitution.

### 5.3 Lazy materialization через FUSE → сборка без полного скачивания

```
Механизм: FUSE-монтирование snix-store, подгрузка файлов по запросу
Эффект:   Не нужно скачивать весь closure, только то что реально читается
Влияние:  Драматическое ускорение для больших dependency tree
```

При FUSE-монтировании:
- Файлы подгружаются **on-demand** при первом обращении
- Directory metadata доступна мгновенно
- Файлы которые никогда не читаются — никогда не скачиваются

### 5.4 Granular substitution → точечная загрузка

```
Механизм: Blob/Directory/PathInfo разделение; store-to-store sync
Эффект:   Только изменённые чанки передаются между stores
Влияние:  Инкрементальное обновление вместо полной пересылки NAR
```

В обычном Nix: substitution = скачать весь NAR файл целиком.
В Snix: substitution = скачать только отсутствующие чанки (остальное уже есть по content address).

### 5.5 Verified streaming с BLAKE3 → параллельная загрузка

```
Механизм: BLAKE3 tree hash позволяет верифицировать части файла
Эффект:   Можно стримить и верифицировать чанки параллельно
Влияние:  Не нужно ждать скачивания всего файла для проверки
```

### 5.6 Untrusted substitution → больше источников пакетов

```
Механизм: Blobs и Directories — content-addressed, не нужен trust
Эффект:   Можно скачивать из любых зеркал, IPFS, соседей по сети
Влияние:  Больше источников = быстрее substitution
```

Только PathInfo требует доверия (подписи). Всё остальное можно брать откуда угодно — BLAKE3 хеш гарантирует целостность.

---

## 6. 🔧 Примеры конфигурации

### 6.1 Запуск snix как lower store для Nix

#### Шаг 1: Запуск snix daemon

```bash
# Daemon для castore и store данных
# По умолчанию данные в /var/lib/snix-{castore,store}
snix store daemon
```

#### Шаг 2: FUSE-монтирование store

```bash
# Монтирует store paths как файловую систему
snix store mount /path/to/snix-mount

# С листингом корня (осторожно при большом store)
snix store mount --list-root /path/to/snix-mount
```

#### Шаг 3: Запуск snix nix-daemon

```bash
# nix-daemon для взаимодействия с Nix
snix nix-daemon -l /tmp/snix-daemon.sock \
    --unix-listen-unlink
```

#### Шаг 4: Создание OverlayFS mount

```bash
# Сохраняем реальный /nix store
mount --bind /nix /opt/nix

# Создаём overlay: snix (lower) + реальный nix store (upper) → /nix
mount -t overlay overlay \
  -o lowerdir=/path/to/snix-mount \
  -o upperdir=/opt/nix \
  /nix
```

#### Шаг 5: Конфигурация nix.conf

```ini
# /etc/nix/nix.conf — для nix-daemon
extra-experimental-features = local-overlay-store

store = local-overlay://?state=/opt/nix/var/nix&upper-layer=/opt/nix/store&check-mount=false&lower-store=unix%3A%2F%2F%2Ftmp%2Fsnix-daemon.sock
```

```ini
# ~/.config/nix/nix.conf — для пользовательского Nix CLI
# Чтобы CLI ходил через daemon, а не напрямую
store = daemon
```

### 6.2 Конфигурация Local Overlay Store (без snix, чистый Nix)

```ini
# /etc/nix/nix.conf
extra-experimental-features = local-overlay-store

# Формат store URL:
# local-overlay://?root=<merged>&lower-store=<lower>&upper-layer=<upper>
store = local-overlay://?root=/mnt/merged&lower-store=/mnt/store-base&upper-layer=/mnt/store-upper
```

```bash
# Предварительно: создать OverlayFS mount
mount -t overlay overlay \
  -o lowerdir="/mnt/store-base/nix/store" \
  -o upperdir="/mnt/store-upper" \
  -o workdir="/mnt/store-workdir" \
  "/mnt/merged/nix/store"
```

### 6.3 Параметры local-overlay-store

| Параметр | Описание | Default |
|----------|----------|---------|
| `lower-store` | Store URL для нижнего слоя | `auto` |
| `upper-layer` | Директория upper layer OverlayFS | — |
| `root` | Корневая директория merged store | — |
| `state` | Директория для state (SQLite DB) | `/dummy` |
| `check-mount` | Проверять ли корректность OverlayFS mount | `true` |
| `read-only` | Открывать ли SQLite DB в read-only | `false` |
| `require-sigs` | Требовать ли подписи при копировании | `true` |
| `path-info-cache-size` | Размер in-memory кеша метаданных | `65536` |
| `remount-hook` | Скрипт для ремонтирования при удалении paths | — |

---

## 7. 🔗 Совместимость с другими инструментами

### 7.1 Firecracker microVMs

| Аспект | Статус |
|--------|--------|
| Прямая интеграция | ❌ Нет встроенной |
| virtiofs backend | ✅ Реализован в snix-castore |
| Теоретическая совместимость | ✅ Высокая |

**virtiofs** — ключевой мост между Snix и microVMs:

```
┌─────────────────────┐     virtiofs      ┌──────────────────┐
│   Host              │ ◄──────────────►  │  Firecracker VM  │
│                     │                   │                  │
│   snix-castore      │   mount point     │  /nix/store      │
│   virtiofs daemon   │ ──────────────►   │  (гостевая ФС)   │
│                     │                   │                  │
└─────────────────────┘                   └──────────────────┘
```

- Snix-castore реализует **virtiofs daemon backend**, подключающийся к существующей FUSE-реализации
- Это позволяет примонтировать store внутрь microVM **без FUSE в госте**
- Для Firecracker: хост экспортирует snix-store через virtiofs → гостевая VM видит `/nix/store`
- Build inputs подгружаются **on-demand** — не нужно копировать весь closure в VM

**Сценарий для CI**: Firecracker VM стартует за ~125ms, видит огромный `/nix/store` через virtiofs, строит только то чего нет — и всё это без overhead копирования.

### 7.2 Self-hosted runners

Snix отлично вписывается в архитектуру с self-hosted runners:

```
┌─────────────────────────────────────────────────┐
│          Self-hosted Runner (NixOS)              │
│                                                  │
│  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ snix daemon  │  │ snix nix-daemon           │  │
│  │ (castore)    │  │ (nix-daemon protocol)     │  │
│  └──────┬──────┘  └──────────┬───────────────┘  │
│         │                     │                  │
│  ┌──────▼──────────────────────▼───────────────┐ │
│  │         OverlayFS /nix/store                 │ │
│  │   lower: snix FUSE mount (read-only)         │ │
│  │   upper: локальный store (read-write)        │ │
│  └──────────────────────────────────────────────┘ │
│                                                  │
│  Runner видит полный /nix/store с первой секунды │
│  Новые сборки пишутся только в upper layer       │
└─────────────────────────────────────────────────┘
```

**Выгода для CI**:
- **Персистентный lower store** — не пересобирать/не скачивать пакеты между job'ами
- **Изолированный upper layer** — каждый job может иметь свой upper (через mount namespace)
- **Компактное хранение** — lower store с дедупликацией вместо раздутого /nix/store

### 7.3 Attic / Harmonia cache servers

| Инструмент | Совместимость с Snix |
|-----------|---------------------|
| **Harmonia** | ✅ Snix сам использует Harmonia (`cache.snix.dev`) |
| **Attic** | ✅ Совместим на уровне Nix binary cache protocol |
| **nar-bridge** | ✅ Встроенный HTTP Binary Cache сервер Snix |

**nar-bridge** — это собственный binary cache сервер Snix:

```
                      Nix HTTP Binary Cache protocol
Nix CLI ◄─────────────────────────────────────────────► nar-bridge
                                                            │
                                                     snix-[ca]store
                                                     (content-addressed)
```

- nar-bridge предоставляет **read-write** HTTP Binary Cache endpoint
- Под капотом использует snix-castore для хранения (с дедупликацией)
- Nix работает с nar-bridge как с обычным substituter — полная совместимость

**Архитектура с Attic/Harmonia**: Snix не заменяет эти инструменты, а **дополняет**. Можно одновременно:
- Использовать Harmonia/Attic как внешний substituter
- Хранить данные локально в snix-castore (компактнее)
- Экспортировать через nar-bridge для других машин

### 7.4 nix2container

| Аспект | Совместимость |
|--------|---------------|
| Прямая интеграция | ⚠️ Непрямая — через OCI builder |
| OCI совместимость | ✅ Snix имеет OCI builder (runc) |
| Общая идеология | ✅ Layered/incremental подход |

Snix и nix2container решают **разные**, но **совместимые** задачи:

- **nix2container**: создаёт OCI образы из Nix derivations (без NAR/tarball копирования)
- **Snix OCI builder**: запускает Nix сборки внутри OCI-контейнеров
- **Мост**: nix2container работает через стандартный Nix — если Nix использует snix как lower store, nix2container автоматически получает преимущества overlay-store

```
nix2container.buildImage { ... }
        │
        ▼
   nix-build (с overlay-store)
        │
        ├── lower: snix-castore (дедуплицированный store)
        └── upper: локальные артефакты сборки
        │
        ▼
   OCI Image layers (incremental push)
```

---

## 8. 🧱 Snix как платформенный слой

### Можно ли использовать Snix как "фундамент"?

**Да, с оговорками.** Snix спроектирован как **composable** и **modular** — каждый компонент можно использовать независимо:

```
Уровень зрелости компонентов:

✅ Готово к использованию:
   - snix-castore (хранение, дедупликация)
   - snix store mount (FUSE)
   - snix nix-daemon (overlay store lower layer)
   - nar-bridge (HTTP binary cache)
   - nix-compat (библиотека парсинга Nix форматов)

⚠️ В разработке / есть ограничения:
   - snix-eval (bytecode VM, совместимость с nixpkgs)
   - snix-build (OCI builder работает, другие в планах)
   - Производительность FUSE mount (известные проблемы)

❌ Не готово:
   - Полная замена nix-build CLI
   - Non-readonly nix-daemon mode
```

### Архитектура "Snix как платформа"

```
┌─────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │ nix2container │  │ nix-build    │  │  nix flake    │ │
│  │ (OCI images)  │  │ (packages)   │  │  (evaluation) │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘ │
│         │                  │                 │          │
│         └──────────────────┼─────────────────┘          │
│                            │                            │
│                   ┌────────▼─────────┐                  │
│                   │  Nix с overlay   │                  │
│                   │  store           │                  │
│                   └────────┬─────────┘                  │
│                            │                            │
│  ┌─────────────────────────▼───────────────────────────┐│
│  │              Snix Platform Layer                     ││
│  │                                                     ││
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐ ││
│  │  │ snix daemon │  │ snix FUSE   │  │ nar-bridge   │ ││
│  │  │ (castore)   │  │ mount       │  │ (bin cache)  │ ││
│  │  └─────┬──────┘  └──────┬──────┘  └──────┬───────┘ ││
│  │        │                │                 │         ││
│  │        └────────────────┼─────────────────┘         ││
│  │                         │                           ││
│  │              snix-castore (BLAKE3, Merkle DAG)       ││
│  │              content-addressed, deduplicated          ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Инфраструктура: Self-hosted runner / Firecracker   ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### Сценарий: Snix + Firecracker + Self-hosted runner

```
1. Runner имеет persistent snix-castore (компактный, дедуплицированный)
2. При старте CI job'а:
   a. Firecracker VM стартует за ~125ms
   b. virtiofs экспортирует snix-store в VM как /nix/store (lower)
   c. tmpfs или block device — upper layer для новых сборок
   d. OverlayFS объединяет в /nix/store внутри VM
3. Nix видит полный store, строит только то чего нет
4. Новые артефакты (upper layer) сохраняются в snix-castore на хосте
5. VM уничтожается — чистая изоляция

Время от push до начала сборки: ~1-3 секунды
```

---

## 9. ⚠️ Ограничения и известные проблемы

| Проблема | Подробности |
|----------|-------------|
| **FUSE производительность** | snix-castore FUSE mount медленнее нативной ФС. Для чтения — приемлемо с кешированием. Для write-heavy — проблема. |
| **Experimental статус** | `local-overlay-store` — experimental feature в Nix. API может меняться. |
| **Неполная реализация nix-daemon** | snix nix-daemon поддерживает только subset операций (достаточно для overlay lower layer, но не для полноценного использования) |
| **Нет drop-in замены** | Нельзя просто заменить `nix` на `snix` в CI pipeline |
| **Lix совместимость** | Overlay store поддержка для Lix [в разработке](https://gerrit.lix.systems/c/lix/+/2859) |
| **Нужен root/privileged** | OverlayFS mount и FUSE требуют привилегий |
| **SQLite на OverlayFS** | Есть нюансы с работой SQLite DB при overlay, нужен отдельный state dir |

---

## 10. 📊 Сравнение подходов к ускорению store

| Подход | Экономия хранения | Скорость доступа | Сложность настройки | Зрелость |
|--------|--------------------|-------------------|---------------------|----------|
| Обычный `/nix/store` | 0% (baseline) | Нативная | Нет | ✅ Prod |
| Overlay с host store | 0% (тот же формат) | Нативная (overlayfs) | Средняя | ⚠️ Experimental |
| Snix castore (FUSE) | 70-90% | Медленнее (FUSE) | Высокая | ⚠️ Early |
| Snix + overlay-store | 70-90% (lower) | ~Нативная (overlay) | Высокая | ⚠️ Early |
| Attic/Harmonia (remote) | Зависит от dedup | Сетевая задержка | Средняя | ✅ Prod |

---

## 11. 🔮 Планы развития Snix

Из блога и документации:

1. **Расширение nix-daemon** — поддержка non-readonly mode: все substitutions идут в castore, upper nix store только для локальных сборок
2. **Упрощение setup** — запуск snix nix-daemon без необходимости поднимать несколько компонентов отдельно
3. **Дополнительные builder backends** — Kubernetes, bwrap, gVisor, Cloud Hypervisor
4. **Новый механизм подписей** — подпись PathInfo напрямую (вместо NAR-based), что откроет возможность для verified partial access
5. **REAPI совместимость** — обсуждается замена worker protocol на [Remote Execution API](https://discourse.nixos.org/t/a-proposal-for-replacing-the-nix-worker-protocol/20926/22)

---

## 12. 💡 Выводы для нашего CI/CD шаблона

### Где Snix полезен прямо сейчас

1. **Как lower store в overlay конфигурации** — самый зрелый use case
   - Позволяет иметь компактный persistent кеш на self-hosted runner
   - Nix работает поверх без модификаций

2. **Как nar-bridge** — собственный binary cache с дедупликацией
   - Альтернатива Attic/Harmonia с лучшей компрессией
   - Read-write, content-addressed

3. **Как хранилище для Replit-подобных сценариев** — массивный store, read-heavy workload

### Где пока рано использовать

1. **Как замена Nix CLI** — не готов
2. **Как единственный builder** — OCI builder работает, но не production-ready
3. **В критических production CI** — experimental status, возможны breaking changes

### Рекомендация

Для текущего шаблона CI/CD Snix представляет **стратегический интерес**, но **не рекомендуется как обязательный компонент**. Вместо этого:

- Использовать **overlay-store (чистый Nix)** с host `/nix/store` как lower — это уже даёт основной выигрыш
- Следить за развитием Snix — когда nix-daemon станет полнофункциональным, переход будет прозрачным
- Для сценариев с **очень большим store** (сотни ГБ+) — Snix castore уже оправдан
