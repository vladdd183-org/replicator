# ⚙️ std + Paisano + Nixago — DevOps-слой Nix

> **std:** github:divnix/std | ~480 ⭐ | std.divnix.com
> **Paisano:** github:paisano-nix/core | Ядро std, может использоваться отдельно
> **Nixago:** github:nix-community/nixago | nix-community проект

---

## 🏗️ std (Standard) — DevOps Framework

### Что решает

std решает проблему хаоса в Nix-репозиториях по мере их роста:

```
БЕЗ std:                              С std:
─────────                              ──────
flake.nix (500+ строк)                flake.nix (30 строк)
├── packages.nix (всё в одном)         ├── nix/
├── shell.nix                          │   ├── backend/
├── modules/ (плоский)                 │   │   ├── packages.nix    ← Cell Block
├── ...хаос...                         │   │   ├── devshells.nix   ← Cell Block
                                       │   │   └── configs.nix     ← Cell Block (Nixago)
                                       │   ├── frontend/
                                       │   │   ├── packages.nix
                                       │   │   └── devshells.nix
                                       │   └── ops/
                                       │       ├── containers.nix  ← OCI images
                                       │       └── microvms.nix    ← MicroVM
```

### Cells и Cell Blocks

```
┌─────────────────────────────────────────────────────────┐
│                    REPOSITORY                            │
│                                                          │
│  ┌────────────────────────────────────┐                  │
│  │          CELL: backend             │                  │
│  │                                    │                  │
│  │  ┌──────────┐  ┌──────────┐       │                  │
│  │  │ runnables│  │installbls│       │                  │
│  │  │ (apps)   │  │(packages)│       │                  │
│  │  │          │  │          │       │                  │
│  │  │ • run    │  │ • build  │       │                  │
│  │  │          │  │ • install│       │                  │
│  │  └──────────┘  └──────────┘       │                  │
│  │                                    │                  │
│  │  ┌──────────┐  ┌──────────┐       │                  │
│  │  │devshells │  │  nixago  │       │                  │
│  │  │          │  │ (configs)│       │                  │
│  │  │ • enter  │  │          │       │                  │
│  │  │          │  │ • .fmt   │       │                  │
│  │  │          │  │ • .lint  │       │                  │
│  │  └──────────┘  └──────────┘       │                  │
│  └────────────────────────────────────┘                  │
│                                                          │
│  ┌────────────────────────────────────┐                  │
│  │          CELL: ops                 │                  │
│  │  ┌──────────┐  ┌──────────┐       │                  │
│  │  │   OCI    │  │ microvm  │       │                  │
│  │  │(contanrs)│  │          │       │                  │
│  │  │          │  │ • run    │       │                  │
│  │  │ • push   │  │          │       │                  │
│  │  │ • publish│  │          │       │                  │
│  │  └──────────┘  └──────────┘       │                  │
│  └────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

### Типы Cell Blocks

| Тип | Назначение | Действия |
|:---|:---|:---|
| `runnables` | Запускаемые приложения | `run` |
| `installables` | Устанавливаемые пакеты | `build`, `install`, `upgrade`, `remove`, `bundle` |
| `devshells` | Dev-окружения | `enter` |
| `nixago` | Конфигурации инструментов | генерация конфиг-файлов |
| `functions` | Переиспользуемые функции | вызов из других блоков |
| `pkgs` | Варианты nixpkgs с overlays | использование другими блоками |
| `arion` | Docker Compose задачи | `up`, `ps`, `stop`, `rm`, `config` |

### CLI / TUI

```bash
# Обнаружение возможностей репозитория
std list

# Запуск по пути Cell//Block/Target:Action
std //backend/apps/api:run
std //backend/packages/server:build
std //ops/containers/api:push

# TUI — интерактивная навигация
std
```

### Интеграция с flake-parts

```nix
{
  inputs.std.url = "github:divnix/std";
  outputs = inputs: inputs.std.growOn {
    inherit inputs;
    cellsFrom = ./nix;
    cellBlocks = with inputs.std.blockTypes; [
      (installables "packages")
      (devshells "devshells")
      (nixago "configs")
      (runnables "apps")
    ];
  };
}

-- ИЛИ через flake-parts:
{
  imports = [ inputs.std.flakeModule ];
}
```

---

## 🧩 Paisano — Ядро std

### Что это

Paisano — вынесенное из std ядро, содержащее "grow function family":

```
┌─────────────────────────────────────┐
│           Paisano Core               │
│                                      │
│  grow      ── организует cells       │
│  pick      ── выбирает target        │
│  harvest   ── собирает outputs       │
│  fertilise ── расширяет контекст     │
│                                      │
│  Layout Schema:                      │
│    ./nix/<cell>/<block>.nix          │
│                                      │
│  Планы: переход на Haumea            │
│  (динамическая загрузка модулей)     │
└─────────────────────────────────────┘
```

### Может использоваться отдельно от std

```
paisano-nix/core    ── базовая библиотека
paisano-nix/tui     ── CLI/TUI (Go)
paisano-nix/direnv  ── интеграция с direnv
paisano-nix/onboarding ── онбординг
```

### TUI (standalone)

```bash
nix profile install github:paisano-nix/tui

# В любом Paisano-совместимом репо:
paisano list           # индексация возможностей
paisano //cell/block   # навигация
```

### Зачем помнить о Paisano

- Если std слишком тяжёл — можно взять только Paisano для организации Cell-структуры
- TUI полезен для discoverability репозитория
- Планируемая интеграция с Haumea (которая уже используется в vladOS-v2 для topology)

---

## 📋 Nixago — генерация конфигов из Nix

### Проблема

```
Корень репозитория:
  .prettierrc          ← ручной
  .eslintrc.json       ← ручной
  treefmt.toml         ← ручной
  .conform.yaml        ← ручной
  lefthook.yaml        ← ручной
  .pre-commit.yaml     ← ручной
  ... 10+ файлов которые нужно поддерживать
```

### Решение Nixago

```
flake.nix:
  nixago.lib.make {
    data = { ... };           ← конфиг как Nix-выражение
    output = "treefmt.toml";  ← выходной файл
    format = "toml";          ← формат
  }

  ↓ при входе в devShell автоматически ↓

Корень репозитория:
  treefmt.toml → /nix/store/...-treefmt.toml  (симлинк)
```

### Как работает

```
┌──────────────────────────────────────────────────┐
│                   Nixago Flow                     │
│                                                   │
│  ┌─────────┐    ┌───────────┐    ┌────────────┐ │
│  │ Nix     │───►│ Engine    │───►│ configFile │ │
│  │ AttrSet │    │ (pkgs.    │    │ (derivation│ │
│  │ (data)  │    │  formats) │    │  in store) │ │
│  └─────────┘    └───────────┘    └─────┬──────┘ │
│                                        │         │
│                                  ┌─────▼──────┐ │
│                                  │ shellHook  │ │
│                                  │ (symlink   │ │
│                                  │  to $PRJ)  │ │
│                                  └────────────┘ │
└──────────────────────────────────────────────────┘
```

### Поддерживаемые форматы

JSON, YAML, TOML и любые другие через `pkgs.formats`

### Готовые пресеты (в составе std)

| Пресет | Инструмент | Что генерирует |
|:---|:---|:---|
| `conform` | Conform | `.conform.yaml` — политики коммитов |
| `lefthook` | Lefthook | `lefthook.yaml` — pre-commit hooks |
| `treefmt` | Treefmt | `treefmt.toml` — единый formatter |
| `prettier` | Prettier | `.prettierrc` — форматирование |
| `editorconfig` | EditorConfig | `.editorconfig` |

### Пример интеграции с devShell

```nix
devShells.default = pkgs.mkShell {
  shellHook = lib.concatStringsSep "\n" [
    (nixago.lib.make treefmtConfig).shellHook
    (nixago.lib.make conformConfig).shellHook
    (nixago.lib.make lefthookConfig).shellHook
  ];
};
```

### Зачем Nixago в nn3w

- **Single source of truth** — все конфиги dev-инструментов описаны в Nix
- **Воспроизводимость** — одинаковые настройки на всех машинах
- **Не захламляет репо** — конфиги генерируются, не коммитятся
- **Интегрируется с std** — как block type `nixago`

---

## 🔗 Как std + Paisano + Nixago работают вместе

```
┌─────────────────────────────────────────────────────────┐
│                    std Framework                         │
│                                                          │
│  flake.nix ──► std.growOn {                              │
│                  cellsFrom = ./nix;                      │
│                  cellBlocks = [                           │
│                    installables "packages"                │
│                    devshells "devshells"                  │
│                    nixago "configs"  ◄── Nixago блок     │
│                    runnables "apps"                       │
│                  ];                                       │
│                }                                         │
│                     │                                    │
│                     ▼                                    │
│  ┌──────────── Paisano Core ────────────┐               │
│  │  grow() ── организует cells          │               │
│  │  pick() ── разрешает targets         │               │
│  │  harvest() ── собирает outputs       │               │
│  └──────────────────────────────────────┘               │
│                     │                                    │
│                     ▼                                    │
│  ┌──────────── Paisano TUI ─────────────┐               │
│  │  $ std list                          │               │
│  │  $ std //backend/configs/treefmt     │               │
│  │  $ std //backend/packages/api:build  │               │
│  └──────────────────────────────────────┘               │
│                                                          │
│  Nixago shell hooks автоматически                        │
│  включаются в std devshells                              │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Когда что использовать

| Ситуация | Инструмент |
|:---|:---|
| Один пакет, простой проект | Не нужен std, достаточно flake-parts |
| Монорепо с несколькими сервисами | **std** с Cells на каждый сервис |
| Нужен CLI для навигации по репо | **Paisano TUI** (standalone или через std) |
| Генерация .prettierrc, treefmt.toml и т.д. | **Nixago** (standalone или через std) |
| CI/CD пайплайны в Nix | **std** с runnables/installables |
| OCI контейнеры | **std** + nix2container |
| MicroVM | **std** + Astro MicroVM |

---

## ⚠️ Нюансы

- **std имеет кривую обучения** — Cells/Cell Blocks нужно осознать
- **Paisano переходит на Haumea** — ветка `paisano-haumea` в разработке
- **Nixago архивирован на GitHub** (nix-casync тоже) — но nix-community версия жива
- **std vs flake-parts** — не конкуренты, std может использовать flake-parts через `std.flakeModule`
