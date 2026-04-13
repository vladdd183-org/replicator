# 🔗 Интеграция Den + Clan + std + CI/CD — как связать всё вместе

> **Ключевой вопрос:** Den, Clan, std, Nixago, deploy-rs, treefmt, nix2container, Cachix...
> Как это всё живёт в одном flake.nix и не конфликтует?
> **Ответ:** Через flake-parts module system — единый интеграционный слой.

---

## 🏗️ Общая архитектура связки

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          flake.nix                                      │
│                                                                         │
│  inputs = {                                                             │
│    nixpkgs, den, flake-aspects, clan, std,                             │
│    treefmt-nix, nix-oci, deploy-rs, ...                                │
│  };                                                                     │
│                                                                         │
│  outputs = inputs:                                                      │
│    inputs.flake-parts.lib.mkFlake { inherit inputs; } {                │
│                                                                         │
│      imports = [                                                        │
│        ┌─────────────────────────────────────────────┐                 │
│        │  inputs.den.flakeModule          ← Den      │                 │
│        │  inputs.std.flakeModule          ← std      │                 │
│        │  inputs.treefmt-nix.flakeModule  ← Treefmt  │                 │
│        │  inputs.nix-oci.flakeModule      ← OCI      │                 │
│        │  ./modules                       ← Наши     │                 │
│        └─────────────────────────────────────────────┘                 │
│      ];                                                                 │
│                                                                         │
│      # Den: hosts, aspects, schema, ctx                                │
│      # std: Cells, Cell Blocks                                         │
│      # treefmt: formatters                                             │
│      # nix-oci: container images                                       │
│      # perSystem: packages, devShells, checks                          │
│    };                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Принцип:** flake-parts — это шина. Каждый инструмент подключается как flakeModule. Они не конфликтуют потому что работают в разных option namespaces.

---

## 📋 Конкретный flake.nix для nn3w-infra

```nix
{
  description = "nn3w infrastructure";

  inputs = {
    # ── Базовые ──
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";

    # ── Конфигурация ──
    den.url = "github:vic/den";
    flake-aspects.url = "github:vic/flake-aspects";
    home-manager.url = "github:nix-community/home-manager";

    # ── Инфраструктура ──
    clan-core.url = "https://git.clan.lol/clan/clan-core/archive/main.tar.gz";
    microvm.url = "github:astro/microvm.nix";
    disko.url = "github:nix-community/disko";
    sops-nix.url = "github:Mic92/sops-nix";

    # ── DevOps / CI ──
    std.url = "github:divnix/std";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    nix-oci.url = "github:dauliac/nix-oci";
    deploy-rs.url = "github:serokell/deploy-rs";

    # ── Framework ──
    nn3w-framework.url = "git+ssh://..."; # или github:
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        # Den — аспекты, хосты, ctx pipeline
        inputs.den.flakeModule

        # std — Cells, Cell Blocks, TUI
        inputs.std.flakeModule

        # Форматирование
        inputs.treefmt-nix.flakeModule

        # OCI контейнеры
        inputs.nix-oci.flakeModule

        # Clan (если как flake-parts module)
        # inputs.clan-core.flakeModule  -- зависит от версии

        # Наши модули
        ./modules
      ];

      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];

      # ─── ВСЁ ЧТО НИЖЕ — ПОДРОБНО ПО СЕКЦИЯМ ───
    };
}
```

---

## 🌿 Секция Den — конфигурация хостов

```nix
# modules/hosts.nix
{ den, inputs, ... }: {

  den.hosts.x86_64-linux.vladOS = {
    users.vladdd183 = {};
  };

  den.hosts.x86_64-linux.angron = {
    trustDomain = "personal";
    users.kubeadmin = {};
    roles = [ "compute" "ci" "storage" ];
  };

  den.hosts.x86_64-linux.perturabo = {
    trustDomain = "personal";
    users.kubeadmin = {};
    enclaves.vladdd183-dev = {
      isolation = "confidential";
      owner = "vladdd183";
      resources = { cpu.cores = 4; memory = "8G"; elastic = true; };
    };
  };

  den.homes.x86_64-linux.vladdd183 = {};
}
```

```nix
# modules/aspects.nix
{ den, inputs, ... }: {

  den.aspects.vladdd183 = {
    includes = [
      den.provides.primary-user
      (den.provides.user-shell "fish")
      den.ful.nn3w.mesh-networking
    ];
    user.extraGroups = [ "wheel" "docker" ];
    homeManager = { pkgs, ... }: {
      programs.git.enable = true;
    };
  };

  den.aspects.angron = {
    includes = [
      den.provides.hostname
      den.ful.nn3w.cluster-compute
      den.ful.nn3w.sovereign-services
    ];
    nixos = { pkgs, ... }: {
      services.k3s.enable = true;
    };
  };
}
```

---

## ⚙️ Секция std — DevOps Cells

```nix
# modules/std-cells.nix — ИЛИ через cellsFrom = ./nix;
{ inputs, ... }: {

  # std через flake-parts:
  std = {
    cellsFrom = ./nix;
    cellBlocks = with inputs.std.blockTypes; [
      (installables "packages")
      (devshells "devshells")
      (nixago "configs")
      (runnables "apps")

      # OCI контейнеры для деплоя сервисов
      # (containers "containers")  -- через nix2container
    ];
  };
}
```

Структура `./nix/`:

```
nix/
├── ops/                          ← Cell: операции
│   ├── apps.nix                  ← runnables (deploy scripts, etc.)
│   ├── configs.nix               ← nixago (treefmt, conform, lefthook)
│   └── devshells.nix             ← dev environments
│
├── services/                     ← Cell: сервисы
│   ├── packages.nix              ← installables (custom packages)
│   └── containers.nix            ← OCI images
│
└── infra/                        ← Cell: инфраструктура
    ├── apps.nix                  ← deploy-rs runners, clan commands
    └── packages.nix              ← topology diagrams, docs
```

---

## 🔧 Секция Treefmt — единый форматтер

```nix
# modules/treefmt.nix
{ inputs, ... }: {
  perSystem = { pkgs, ... }: {
    treefmt = {
      projectRootFile = "flake.nix";
      programs = {
        nixpkgs-fmt.enable = true;   # .nix файлы
        prettier.enable = true;       # JSON, YAML, MD
        shellcheck.enable = true;     # .sh файлы
        shfmt.enable = true;
      };
    };
  };
}
```

Результат: `nix fmt` форматирует весь репо. CI проверяет через `nix flake check`.

---

## 📦 Секция OCI — контейнеры без Docker

```nix
# modules/containers.nix
{ inputs, ... }: {
  perSystem = { pkgs, system, ... }: {
    oci.containers = {
      # Минималистичный контейнер с kubectl
      kubectl = {
        package = pkgs.kubectl;
      };

      # Кастомный сервис
      my-api = {
        layers = [
          { deps = [ pkgs.cacert pkgs.busybox ]; }
        ];
        config = {
          entrypoint = [ "${pkgs.my-api}/bin/my-api" ];
          env = [ "PORT=8080" ];
          exposedPorts."8080/tcp" = {};
        };
      };
    };
  };
}
```

---

## 🚀 Секция Deploy — deploy-rs

```nix
# modules/deploy.nix
{ inputs, ... }: {
  flake.deploy.nodes = {
    angron = {
      hostname = "angron.mesh.local";
      profiles.system = {
        user = "root";
        sshUser = "kubeadmin";
        path = inputs.deploy-rs.lib.x86_64-linux.activate.nixos
          inputs.self.nixosConfigurations.angron;
        magicRollback = true;
        autoRollback = true;
      };
    };

    perturabo = {
      hostname = "perturabo.mesh.local";
      profiles.system = {
        user = "root";
        sshUser = "kubeadmin";
        path = inputs.deploy-rs.lib.x86_64-linux.activate.nixos
          inputs.self.nixosConfigurations.perturabo;
        magicRollback = true;
        autoRollback = true;
      };
    };
  };
}
```

---

## 🏰 Секция Clan — fleet management

```nix
# modules/clan.nix
{ inputs, ... }: {

  # Clan работает либо как flake-parts module,
  # либо как отдельный overlay поверх den-сгенерированных nixosConfigurations

  # Вариант: Clan inventory
  clan = {
    meta.name = "nn3w-personal";
    directory = inputs.self;

    inventory.instances = {
      # Mesh VPN на всех машинах
      zerotier = {
        roles.controller.machines.angron = {};
        roles.peer.tags = [ "all" ];
      };

      # Мониторинг
      monitoring = {
        roles.server.machines.angron = {};
        roles.client.tags = [ "all" ];
      };

      # Бэкапы
      borgbackup = {
        roles.server.machines.angron = {};
        roles.client.tags = [ "workstations" ];
      };
    };

    machines = {
      vladOS.tags = [ "all" "workstations" ];
      angron.tags = [ "all" "servers" ];
      perturabo.tags = [ "all" "servers" "gpu" ];
    };
  };
}
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: cachix/install-nix-action@v25
        with:
          extra_nix_config: |
            accept-flake-config = true
      - uses: cachix/cachix-action@v14
        with:
          name: nn3w
          authToken: '${{ secrets.CACHIX_AUTH_TOKEN }}'

      # Проверяем форматирование (treefmt)
      - run: nix fmt -- --check

      # Запускаем все checks (включая Den CI tests)
      - run: nix flake check

      # Собираем все хосты
      - run: nix build .#nixosConfigurations.vladOS.config.system.build.toplevel
      - run: nix build .#nixosConfigurations.angron.config.system.build.toplevel

  deploy:
    needs: check
    if: github.ref == 'refs/heads/main'
    runs-on: self-hosted  # на angron, через GitHub Runner
    steps:
      - uses: actions/checkout@v4
      - uses: cachix/install-nix-action@v25
      - uses: cachix/cachix-action@v14
        with:
          name: nn3w
          authToken: '${{ secrets.CACHIX_AUTH_TOKEN }}'

      # Deploy через deploy-rs
      - run: nix run .#deploy-rs -- .#angron
      - run: nix run .#deploy-rs -- .#perturabo

      # ИЛИ через Clan
      - run: nix run .#clan -- machines update angron
      - run: nix run .#clan -- machines update perturabo
```

### Tangled Spindles (децентрализованный CI)

```yaml
# .tangled/workflows/ci.yml (когда мигрируем на Tangled)
name: CI
on: push

jobs:
  check:
    runs-on: nix
    steps:
      - run: nix fmt -- --check
      - run: nix flake check

  deploy:
    needs: check
    runs-on: self-hosted
    steps:
      - run: nix run .#deploy-rs -- .#angron
```

---

## 🗺️ Полная карта: что с чем связано

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                        flake-parts (шина)                               │
│                                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │   Den    │  │   std    │  │ treefmt  │  │ nix-oci  │  │deploy-rs││
│  │ .flake   │  │ .flake   │  │ .flake   │  │ .flake   │  │         ││
│  │ Module   │  │ Module   │  │ Module   │  │ Module   │  │ (flake) ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘│
│       │              │             │              │              │     │
│  ┌────▼─────────────────────────────────────────────────────────────┐ │
│  │                      flake outputs                               │ │
│  │                                                                   │ │
│  │  nixosConfigurations.* ◄── Den ctx pipeline                      │ │
│  │  homeConfigurations.*  ◄── Den ctx pipeline                      │ │
│  │  deploy.nodes.*        ◄── deploy-rs + Den hosts                 │ │
│  │  packages.*            ◄── std installables + nix-oci + Den      │ │
│  │  devShells.*           ◄── std devshells                         │ │
│  │  formatter.*           ◄── treefmt                               │ │
│  │  checks.*              ◄── treefmt + Den tests + nix flake check │ │
│  │  apps.*                ◄── std runnables + Den nh apps           │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                         │
│              ┌───────────────┼───────────────┐                        │
│              ▼               ▼               ▼                        │
│  ┌────────────────┐ ┌──────────────┐ ┌─────────────────┐            │
│  │   CI/CD        │ │   Clan CLI   │ │  Developer      │            │
│  │                │ │              │ │  Workflow        │            │
│  │ nix flake check│ │ clan update  │ │ nix develop     │            │
│  │ nix build      │ │ clan flash   │ │ nix fmt         │            │
│  │ deploy-rs      │ │ clan secrets │ │ std //cell/block│            │
│  │ cachix push    │ │ clan backup  │ │ nix run .#app   │            │
│  └────────────────┘ └──────────────┘ └─────────────────┘            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Developer Workflow (день разработчика)

```
Утро:
  cd nn3w-infra
  nix develop                    ← std devshell (с Nixago конфигами)
  
Работа:
  vim modules/aspects/vpn.nix   ← редактируем Den аспект
  nix fmt                        ← treefmt форматирует
  nix flake check                ← проверяем (Den tests + treefmt + builds)

Деплой:
  # Вариант A: deploy-rs (SSH прямой)
  nix run .#deploy-rs -- .#angron

  # Вариант B: Clan (fleet-aware)
  clan machines update angron

  # Вариант C: nh (быстрый switch)
  nh os switch .#vladOS          ← для локальной машины

Контейнеры:
  nix build .#oci-my-api         ← собрать OCI image
  nix run .#oci-my-api.copyToPodman  ← загрузить в Podman
  # Или push в registry через CI

Навигация:
  std list                       ← TUI: что можно делать
  std //ops/configs/treefmt      ← конкретный target
```

---

## 🎯 Кто за что отвечает

```
┌───────────────┬──────────────────────────────────────────────────┐
│  Инструмент   │  Зона ответственности                           │
├───────────────┼──────────────────────────────────────────────────┤
│  Den          │  ЧТО на каждой машине: аспекты, классы, pipeline│
│  Clan         │  КАК машины общаются: VPN, secrets, fleet ops   │
│  std          │  КАК мы работаем: cells, devshells, CI targets  │
│  treefmt      │  КАК выглядит код: форматирование               │
│  Nixago       │  КАК настроены инструменты: generated configs   │
│  nix-oci      │  КАК пакуем сервисы: OCI контейнеры            │
│  deploy-rs    │  КАК деплоим: SSH + magic rollback              │
│  Cachix       │  КАК кэшируем: binary cache для CI и devs      │
│  sops-nix     │  КАК храним секреты: encryption at rest         │
│  disko        │  КАК размечаем диски: declarative partitioning  │
│  flake-parts  │  КАК всё связано: модульная шина                │
└───────────────┴──────────────────────────────────────────────────┘
```

---

## ⚡ Den + Clan: как они дополняют друг друга

```
Den создаёт:                       Clan использует:
─────────────                      ────────────────

nixosConfigurations.vladOS    ──►  clan machines update vladOS
nixosConfigurations.angron    ──►  clan machines update angron
nixosConfigurations.perturabo ──►  clan machines update perturabo

Den не знает о сети.               Clan знает о сети.
Den не знает о секретах.           Clan управляет секретами.
Den не знает о бэкапах.            Clan управляет бэкапами.
Den знает ЧТО.                     Clan знает КАК.
```

Den генерирует nixosConfigurations (через ctx pipeline + aspects).
Clan берёт эти конфигурации и деплоит их на реальные машины через mesh VPN, управляя секретами и бэкапами.

---

## ⚡ Den + std: как они дополняют друг друга

```
Den создаёт:                       std организует:
─────────────                      ────────────────

OS конфигурации (хосты, юзеры)     DevOps пайплайны (CI/CD targets)
Аспекты (фичи)                     Cell Blocks (packages, shells, configs)
Custom classes                      TUI для навигации по репо
Кросс-flake шаринг                 Nixago для dev tooling configs

Den не занимается CI/CD.            std не занимается OS конфигами.
Den — про декларативность ОС.       std — про операционный workflow.
```

---

## ⚡ Clan + std: как они дополняют друг друга

```
Clan даёт:                         std даёт:
──────────                         ─────────

Fleet management                    CI/CD организацию
VPN mesh                            Dev environments (devshells)
Remote deployment                   Container builds (OCI)
Secret management                   Tool configs (Nixago)
Backup management                   Repository navigation (TUI)

Clan — рантайм инфраструктуры.     std — dev-time workflow.
```

---

## 📊 Варианты деплоя — когда что использовать

| Сценарий | Инструмент | Почему |
|:---|:---|:---|
| Локальный switch на десктопе | `nh os switch` или `nixos-rebuild` | Быстро, прямой доступ |
| Деплой на один сервер | `deploy-rs` | SSH + magic rollback |
| Деплой на весь fleet | `clan machines update` | Awareness о сети, секретах, тегах |
| Первая установка на bare metal | `clan machines install` + disko | Автоматическая разметка + bootstrap |
| Прошивка на USB/SD | `clan flash` | Готовый образ |
| CI/CD автоматический | GitHub Actions + `deploy-rs` или `clan` | Автоматизация на push to main |
| Деплой exclave на чужой сервер | Кастомный `deploy-exclave` | Через VPN, LUKS image |
| OCI push в registry | `nix run .#oci-X.copyToRegistry` | Через CI |
