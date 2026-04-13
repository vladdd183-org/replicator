# 🏗️ std (Standard) — DevOps framework для Nix (divnix/std)

> Краткий обзор фреймворка std и сравнение с flake-parts для CI/CD шаблона.

**GitHub**: [divnix/std](https://github.com/divnix/std)
**Документация**: [std.divnix.com](https://std.divnix.com)
**flake-parts интеграция**: [flake.parts/options/std](https://flake.parts/options/std.html)

---

## 1. Основные концепции: Cells, Cell Blocks, Block Types

### 🧬 Cells (Ячейки)

**Cell** — папка первого уровня под `cellsFrom`. Представляет связную семантическую единицу функциональности.

```
nix/
├── app/          ← Cell "app" (бизнес-логика)
├── infra/        ← Cell "infra" (инфраструктура)
├── automation/   ← Cell "automation" (CI/CD)
└── _std/         ← Cell "_std" (встроенная, от std)
```

Каждая Cell — как «микросервис» в мире Nix-конфигурации. Содержит свой набор Cell Blocks.

### 🧱 Cell Blocks (Блоки ячеек)

**Cell Block** — именованный набор выходов внутри Cell. Каждый Cell Block имеет определённый **Block Type**, который определяет доступные действия.

```
nix/
└── app/                  ← Cell
    ├── packages.nix       ← Cell Block (тип: Installables)
    ├── devshells.nix      ← Cell Block (тип: Devshells)
    ├── containers.nix     ← Cell Block (тип: Containers)
    └── operables.nix      ← Cell Block (тип: Operables)
```

### 🏷️ Block Types (Типы блоков)

Block Type определяет **какие действия** доступны для Cell Block. Встроенные типы:

| Block Type | Назначение | Доступные действия |
|-----------|-----------|-------------------|
| **Runnables** | Запускаемые таргеты | `run` |
| **Installables** | Устанавливаемые пакеты | `install`, `upgrade`, `remove`, `build`, `bundle`, `bundleImage`, `bundleAppImage` |
| **Pkgs** | Кастомные nixpkgs варианты | (передача overlays) |
| **Arion** | Docker Compose через Nix | `up`, `ps`, `stop`, `rm`, `config`, `arion` |
| **Devshells** | Dev-окружения | `enter` |
| **Containers** | OCI-контейнеры | `build`, `publish`, `load` |
| **Operables** | Приложения для OCI | `build` → вход для Containers |
| **Functions** | Библиотечные функции | (без действий, для импорта) |
| **Data** | Конфигурационные данные | (без действий, для импорта) |

Можно создавать **свои Block Types** с кастомными действиями.

---

## 2. Как std организует CI/CD артефакты

### Структура проекта

```
my-project/
├── flake.nix              ← точка входа
├── flake.lock
└── nix/
    ├── app/               ← Cell: основное приложение
    │   ├── packages.nix    ← что собирать (Installables)
    │   ├── operables.nix   ← как запускать (Operables)  
    │   └── containers.nix  ← как паковать в OCI (Containers)
    │
    ├── repo/              ← Cell: инструменты репозитория
    │   ├── devshells.nix   ← dev-окружения
    │   └── configs.nix     ← конфигурации (nixago)
    │
    └── automation/        ← Cell: CI/CD
        ├── pipelines.nix   ← CI pipeline определения
        └── deploy.nix      ← деплой-скрипты
```

### TUI/CLI для обнаружения

std предоставляет интерактивный TUI для навигации по проекту:

```bash
# Показать все доступные таргеты и действия
nix run .#std

# Результат — интерактивное меню:
# app • packages • my-app         [build] [install]
# app • containers • my-app-oci   [build] [publish] [load]
# repo • devshells • default      [enter]
```

---

## 3. Операции: build, run, publish

### Build

```bash
# Собрать пакет
nix run .#std -- //app/packages/my-app:build

# Или через nix build
nix build .#app-packages-my-app
```

### Run

```bash
# Запустить Runnable
nix run .#std -- //app/runnables/my-service:run
```

### Publish (OCI контейнеры)

```bash
# Собрать OCI образ
nix run .#std -- //app/containers/my-app:build

# Загрузить в registry
nix run .#std -- //app/containers/my-app:publish

# Загрузить в Docker daemon для тестов
nix run .#std -- //app/containers/my-app:load
```

---

## 4. Интеграция с nix2container (Operables → OCI)

### Цепочка: Package → Operable → OCI

std определяет конвейер от кода до контейнера:

```
┌──────────┐     ┌──────────────┐     ┌────────────┐
│ Package   │────▸│  Operable     │────▸│  OCI Image  │
│ (сборка)  │     │ (+ runtime    │     │ (container) │
│           │     │   deps, env)  │     │             │
└──────────┘     └──────────────┘     └────────────┘
  Installable      mkOperable           mkOCI
                   (lib.ops)            (lib.ops)
```

**Operable** — обёртка над пакетом, добавляющая:
- Runtime-зависимости (`runtimeInputs`)
- Переменные окружения
- Readiness/liveness проверки
- Точку входа (entrypoint)

### Пример: operables.nix

```nix
# nix/app/operables.nix
{ inputs, cell }: {
  my-app = inputs.std.lib.ops.mkOperable {
    package = cell.packages.my-app;
    runtimeInputs = with inputs.nixpkgs; [
      cacert     # TLS-сертификаты
      bashInteractive
    ];
    runtimeEnv = {
      APP_ENV = "production";
    };
    # Проверка готовности (для k8s probes)
    readiness = ''
      curl -sf http://localhost:8080/health || exit 1
    '';
  };
}
```

### Пример: containers.nix (mkOCI через nix2container)

```nix
# nix/app/containers.nix
{ inputs, cell }: {
  my-app = inputs.std.lib.ops.mkOCI {
    name = "registry.example.com/my-app";
    entrypoint = cell.operables.my-app;
    tag = "latest";                    # или builtins.hashFile
    # Дополнительные setup-задачи
    setup = [
      inputs.std.lib.ops.mkdir "/tmp"
      inputs.std.lib.ops.mkdir "/var/log"
    ];
    uid = "65534";  # nobody
    gid = "65534";
    # Метаданные OCI
    labels = {
      "org.opencontainers.image.source" = "https://git.example.com/my-app";
    };
  };
}
```

### Под капотом: nix2container

`mkOCI` использует nix2container, который:
- **Не создаёт tarball** в Nix store (архивлесс подход)
- Пропускает уже загруженные слои при push
- Автоматически оптимизирует слоизацию (maxLayers)
- Поддерживает инкрементальные push (только изменённые слои)

---

## 5. Сравнение std vs flake-parts

### Архитектурное сравнение

| Аспект | std (divnix/std) | flake-parts |
|--------|------------------|-------------|
| **Философия** | Опинионированный фреймворк | Минимальное модульное ядро |
| **Структура** | Жёсткая: Cells → Cell Blocks → Block Types | Гибкая: любая структура модулей |
| **Learning curve** | Высокая (новые абстракции) | Средняя (близко к стандартным flakes) |
| **Документация** | Слабая (исторически сложная) | Хорошая (flake.parts) |
| **CLI/TUI** | Встроенный (обнаружение таргетов) | Нет (стандартный nix CLI) |
| **Горизонтальные интеграции** | Встроены (nix2container, treefmt, devshell...) | Через модули (независимые) |
| **Сообщество** | Небольшое | Большое, активное |
| **Совместимость** | Может работать как flake-parts модуль | Стандарт де-факто |

### CI/CD-специфичное сравнение

| Аспект | std | flake-parts |
|--------|-----|-------------|
| **OCI контейнеры** | mkOperable → mkOCI (встроено) | nix2container модуль (подключаемо) |
| **CI pipeline описание** | Специальные Block Types | Произвольные outputs |
| **Кеширование** | Интеграция с Cachix | Через модули |
| **pre-commit хуки** | Через Block Type | git-hooks.nix модуль |
| **Обнаружение CI-целей** | TUI + `ci.build = true` маркеры | Стандартный `nix flake show` |
| **Удобство для новичков** | Сложнее (надо понять Cells) | Проще (стандартные Nix-концепции) |

### Пример: одно и то же в std vs flake-parts

#### std вариант (flake.nix)

```nix
{
  inputs = {
    std.url = "github:divnix/std";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    n2c.url = "github:nlewo/nix2container";
  };

  outputs = { std, ... }@inputs:
    std.growOn {
      inherit inputs;
      cellsFrom = ./nix;
      cellBlocks = with std.blockTypes; [
        (installables "packages")
        (runnables "operables")
        (containers "containers")
        (devshells "devshells")
        (functions "lib")
      ];
    }
    # Совместимость с nix build / nix develop
    {
      devShells = std.harvest inputs.self [ "repo" "devshells" ];
      packages = std.harvest inputs.self [ "app" "packages" ];
    };
}
```

#### flake-parts вариант (flake.nix)

```nix
{
  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nix2container.url = "github:nlewo/nix2container";
    git-hooks-nix.url = "github:cachix/git-hooks.nix";
    treefmt-nix.url = "github:numtide/treefmt-nix";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.git-hooks-nix.flakeModule
        inputs.treefmt-nix.flakeModule
      ];

      systems = [ "x86_64-linux" "aarch64-linux" ];

      perSystem = { pkgs, config, ... }: {
        packages.default = pkgs.callPackage ./package.nix {};

        devShells.default = pkgs.mkShell {
          shellHook = config.pre-commit.installationScript;
        };

        pre-commit.settings.hooks = {
          nixfmt-rfc-style.enable = true;
          deadnix.enable = true;
        };
      };
    };
}
```

---

## 🏁 Вывод: что лучше для CI/CD шаблона?

### Рекомендация: flake-parts

Для нашей задачи (универсальный CI/CD шаблон) **flake-parts лучше** по следующим причинам:

| Критерий | Победитель | Почему |
|---------|-----------|--------|
| Простота входа | **flake-parts** | Стандартные Nix-концепции, не нужно учить Cells |
| Модульность | **flake-parts** | Любой модуль подключается через `imports` |
| Сообщество | **flake-parts** | Больше модулей, больше примеров |
| Документация | **flake-parts** | flake.parts — отличный справочник |
| Гибкость | **flake-parts** | Нет жёсткой структуры, подходит для любого проекта |
| OCI контейнеры | Паритет | Оба интегрируются с nix2container |
| Обнаружение | **std** | TUI удобнее для больших проектов |

### Когда выбрать std

- Большая команда с множеством микросервисов
- Нужна жёсткая стандартизация структуры
- Важен TUI для обнаружения таргетов
- Команда готова инвестировать в изучение фреймворка

### Когда выбрать flake-parts

- Универсальный шаблон для разных проектов (наш случай)
- Нужна лёгкость входа для новичков
- Важна экосистема модулей
- Проекты малого-среднего размера

### Компромисс

std может работать **как flake-parts модуль**:

```nix
imports = [ inputs.std.flakeModule ];
```

Это позволяет использовать отдельные возможности std (например, `mkOCI`) без полного принятия фреймворка. Но для нашего шаблона это избыточно — nix2container подключается напрямую проще.
