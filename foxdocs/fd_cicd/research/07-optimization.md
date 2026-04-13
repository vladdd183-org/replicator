# ⚡ Оптимизация и параллелизм Nix-сборок

> Как выжать максимум скорости из Nix: от настройки ядер
> до remote builders и стратегии слоёв.

---

## 🎛️ max-jobs и cores — основа параллелизма

### 📐 Как это работает

```
max-jobs = сколько деривейшнов собирать ПАРАЛЛЕЛЬНО
cores    = сколько ядер доступно КАЖДОМУ деривейшну

Максимум ядер = max-jobs × cores
```

### 📊 Примеры для 16-ядерной машины

| max-jobs | cores | Паттерн | Когда использовать |
|----------|-------|---------|-------------------|
| `auto` (16) | `0` (16) | Агрессивный | ✅ CI (одна задача, утилизировать всё) |
| `4` | `4` | Сбалансированный | Много мелких деривейшнов |
| `1` | `16` | Последовательный | Один тяжёлый build (GCC, LLVM) |
| `16` | `1` | Максимум параллелизма | Много независимых мелких задач |

### 🎯 Для CI (наш случай)

```nix
# В nix.conf или --option
max-jobs = auto   # все ядра = столько параллельных деривейшнов
cores = 0         # каждый деривейшн может использовать ВСЕ ядра
```

> ⚠️ `max-jobs = auto` + `cores = 0` может привести к oversubscription
> (если 16 деривейшнов по 16 ядер = 256 потоков на 16 ядер).
> Но на практике большинство деривейшнов лёгкие, и oversubscription не критичен.

### 📦 max-substitution-jobs — параллельные скачивания

```
max-substitution-jobs = 16  # сколько бинарников скачивать параллельно
```

> 💡 По умолчанию привязан к `max-jobs`. Можно увеличить отдельно
> для ускорения скачивания из binary cache.

---

## 🔧 Оптимизация nix.conf для CI

```nix
# /etc/nix/nix.conf на CI-сервере
max-jobs = auto
cores = 0
max-substitution-jobs = 32

# Не верифицировать подписи при локальной сборке (ускоряет)
# ⚠️ Только для CI, не для production machines!
require-sigs = false

# Garbage collection по расписанию, не во время сборки
auto-optimise-store = true
min-free = 5368709120   # 5 GB — запускать GC если меньше

# Публичные кеши
substituters = https://cache.nixos.org https://nix-community.cachix.org
trusted-public-keys = cache.nixos.org-1:... nix-community.cachix.org-1:...

# Логи
log-lines = 500
show-trace = true
```

---

## 🌐 Remote Builders (распределённые сборки)

### 🎯 Зачем

- Multi-arch: собирать aarch64 на aarch64 машине
- Распределение нагрузки между серверами
- Слабый CI-сервер + мощный build-сервер

### 📊 Схема

```
CI Runner (x86_64)
  ├── nix build .#oci-prod            → собрать на localhost
  ├── nix build .#oci-prod-arm        → делегировать на aarch64 builder
  └── nix build .#checks.lint         → собрать на localhost
                     │
                     ▼
         aarch64 Build Server
         ├── /nix/store (shared)
         └── SSH access для nix daemon
```

### 🔧 Настройка

```nix
# На CI-сервере: /etc/nix/machines
ssh://builder@aarch64-server x86_64-linux,aarch64-linux /etc/nix/builder-key.pem 8 2 big-parallel,kvm
#    ^host                   ^systems                   ^ssh-key                  ^jobs ^speed ^features
```

Или через NixOS module:
```nix
nix.buildMachines = [{
  hostName = "aarch64-builder";
  systems = [ "aarch64-linux" "x86_64-linux" ];
  maxJobs = 8;
  speedFactor = 2;
  supportedFeatures = [ "big-parallel" "kvm" ];
  sshUser = "builder";
  sshKey = "/etc/nix/builder-key";
}];
nix.distributedBuilds = true;
```

### ⚠️ Оптимизация SSH-соединений

Проблема: Nix переподключается по SSH для каждого build → latency.

Решение — SSH ControlMaster:
```
# ~/.ssh/config
Host aarch64-builder
  ControlMaster auto
  ControlPath /tmp/ssh-nix-%r@%h:%p
  ControlPersist 600
```

---

## 📦 Стратегия слоёв для быстрых push

### 🎯 Принцип: минимизировать размер часто-меняющегося слоя

```
┌─────────────────────────────────┐
│ Слой N: app source (< 10 MB)   │ ← КАЖДЫЙ коммит → push ~2-5s
├─────────────────────────────────┤
│ Слой 2: deps (100-500 MB)      │ ← РЕДКО → push только при dep change
├─────────────────────────────────┤
│ Слой 1: runtime (30-80 MB)     │ ← ПОЧТИ НИКОГДА → push раз в месяц
└─────────────────────────────────┘
```

### 🧩 Борьба с дупликатами между слоями

```nix
runtimeLayer = n2c.buildLayer { deps = runtimeDeps; };

depsLayer = n2c.buildLayer {
  deps = [ venv ];
  layers = [ runtimeLayer ];  # ← "вычесть" paths из runtime слоя
};

appLayer = n2c.buildLayer {
  deps = [ appSrc ];
  layers = [ runtimeLayer depsLayer ];  # ← "вычесть" всё предыдущее
};

image = n2c.buildImage {
  layers = [ runtimeLayer depsLayer appLayer ];
  # ...
};
```

> 💡 Без дедупликации: один store path может быть в 2-3 слоях.
> С дедупликацией: каждый store path ровно в одном слое.
> Экономия: 40-60% размера образа.

---

## 🐍 Оптимизация Python (uv2nix)

### Decoupled venv от source code

```nix
# ❌ Плохо: изменение src → пересборка venv
autopost-bot = prev.autopost-bot.overrideAttrs { src = ./.; };

# ✅ Хорошо: только metadata в venv, код через PYTHONPATH
autopost-bot = prev.autopost-bot.overrideAttrs (old: {
  src = pkgs.runCommand "meta-only" {} ''
    mkdir -p $out/src
    cp ${./pyproject.toml} $out/pyproject.toml
    touch $out/src/__init__.py
  '';
});
# Код монтируется как отдельный слой через PYTHONPATH=/app
```

### Pre-compile .pyc

```nix
appSrc = pkgs.stdenv.mkDerivation {
  # ...
  installPhase = ''
    # ... copy source ...
    ${python}/bin/python3 -m compileall -q -j 0 $out/app/src
  '';
};
```

> 💡 `-j 0` = компиляция на всех ядрах. Ускоряет startup контейнера.

### Prefer wheels

```nix
overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
```

> 💡 Binary wheels не нужно компилировать → быстрее в 10x.
> Оверрайды для C-зависимостей только при необходимости.

---

## 🟢 Оптимизация JS (bun2nix)

### bun2nix — быстрая генерация

```bash
# ~50ms для проекта с 2000 пакетов!
bun2nix
```

### Фиксированный node_modules слой

```nix
nodeModules = bun2nix.lib.mkNodeModules {
  src = ./.;
  lockfile = ./bun.lockb;
};

# В отдельном слое — не пересобирается при изменении кода
(n2c.buildLayer { deps = [ nodeModules ]; maxLayers = 1; })
```

---

## 📊 nix-output-monitor — наблюдение за сборкой

```bash
nix build .#oci-prod \
  --log-format internal-json --max-jobs auto --cores 0 \
  2>&1 | nix run nixpkgs#nix-output-monitor -- --json
```

Показывает:
- 📊 Прогресс-бар по деривейшнам
- 🔄 Что собирается прямо сейчас
- 💾 Что скачивается из кеша
- ⏱️ Время на каждый derivation

---

## 🚀 Чеклист оптимизаций

```
✅ max-jobs = auto, cores = 0
✅ max-substitution-jobs = 32
✅ Публичные кеши (cache.nixos.org + nix-community)
✅ Приватный кеш (Attic/Harmonia) для своих деривейшнов
✅ post-build-hook queue для автопуша
✅ NVMe для /nix/store
✅ 3+ слоя в OCI: runtime / deps / app
✅ Дедупликация store paths между слоями
✅ sourcePreference = "wheel" для Python
✅ Decoupled venv от app source
✅ Pre-compile .pyc
✅ nix-output-monitor для наблюдения
✅ Remote builders для multi-arch
✅ SSH ControlMaster для remote builders
✅ auto-optimise-store = true
```
