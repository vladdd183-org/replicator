# 🏛️ nn3w — Архитектурное видение суверенного стека

> **nn3w** = New Nix 3 Web 3.0
> Суверенная, децентрализованная, модульная Nix-инфраструктура
> Проектируется изначально для P2P/web3, но работает и в классическом режиме

---

## 🎯 Принципы проектирования

```
┌─────────────────────────────────────────────────────────────┐
│                     nn3w PRINCIPLES                          │
│                                                              │
│  🔒 СУВЕРЕННОСТЬ        Полный контроль над инфраструктурой │
│                         Нет vendor lock-in, нет SaaS        │
│                                                              │
│  🌐 ДЕЦЕНТРАЛИЗАЦИЯ     P2P by default, серверы optional    │
│                         Content-addressed storage            │
│                                                              │
│  🧩 МОДУЛЬНОСТЬ         Аспект-ориентированная архитектура  │
│                         Всё переиспользуемо, всё заменяемо  │
│                                                              │
│  📐 ДЕКЛАРАТИВНОСТЬ     Вся инфраструктура = код            │
│                         Воспроизводимость, аудируемость      │
│                                                              │
│  🔄 КОМПОЗАБЕЛЬНОСТЬ    Части стека работают независимо      │
│                         Можно взять только нужное            │
│                                                              │
│  ⚡ PRODUCTION-READY    Не эксперимент, а рабочая система   │
│                         Стабильные зависимости               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Полная архитектура стека

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ╔═══════════════════════════════════════════════════════════════════╗  │
│  ║                    🖥️  СЛОЙ ПОЛЬЗОВАТЕЛЯ                         ║  │
│  ║                                                                   ║  │
│  ║  Spaces (Clan)     ── изолированные рабочие пространства         ║  │
│  ║  Clan GUI          ── визуальное управление                      ║  │
│  ║  nh CLI            ── быстрый rebuild/switch                     ║  │
│  ║  std TUI (Paisano) ── навигация по репозиторию                   ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                              │                                         │
│  ╔═══════════════════════════▼═══════════════════════════════════════╗  │
│  ║                    🌿 СЛОЙ КОНФИГУРАЦИИ (Den)                    ║  │
│  ║                                                                   ║  │
│  ║  den.schema ── хосты, юзеры, хомы, анклавы                      ║  │
│  ║  den.aspects ── фича-first модули по классам                     ║  │
│  ║  den.ctx ── context pipeline (parametric dispatch)                ║  │
│  ║  den.provides ── batteries (hostname, user-shell, forward...)    ║  │
│  ║  den.ful.<ns> ── кросс-flake шаринг аспектов                    ║  │
│  ║                                                                   ║  │
│  ║  Кастомные классы nn3w:                                          ║  │
│  ║    • enclave (L0-L4 isolation levels)                            ║  │
│  ║    • mesh-node (IPFS/libp2p participant config)                  ║  │
│  ║    • sovereign-service (self-hosted service template)            ║  │
│  ║    • cluster-role (K3s/nomad workload identity)                  ║  │
│  ║                                                                   ║  │
│  ║  ← flake-aspects v0.7.0 ← flake-parts (модульность)            ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                              │                                         │
│  ╔═══════════════════════════▼═══════════════════════════════════════╗  │
│  ║                    🏰 СЛОЙ ИНФРАСТРУКТУРЫ (Clan)                 ║  │
│  ║                                                                   ║  │
│  ║  Fleet Management ── P2P без центрального контроллера            ║  │
│  ║  Inventory ── сервисы, роли, теги → группы машин                 ║  │
│  ║  Networking ── мульти-VPN (ZeroTier, Tor, Mycelium, custom)     ║  │
│  ║  Secrets (vars) ── декларативные, привязаны к сервисам           ║  │
│  ║  Data Mesher v2 ── gossip-based P2P file sync                    ║  │
│  ║  Backups ── декларативные, cross-machine                         ║  │
│  ║  MicroVM ── GPU-accelerated isolated workloads                   ║  │
│  ║  Service Exports ── межсервисная композабельность                ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                              │                                         │
│  ╔═══════════════════════════▼═══════════════════════════════════════╗  │
│  ║                    ⚙️  СЛОЙ DEVOPS (std)                         ║  │
│  ║                                                                   ║  │
│  ║  Cells: backend, frontend, ops, infra                            ║  │
│  ║  Cell Blocks: packages, devshells, containers, configs           ║  │
│  ║  Nixago ── генерация конфигов (.prettier, treefmt, conform)     ║  │
│  ║  nix2container ── OCI images без Docker                          ║  │
│  ║  deploy-rs ── rolling updates с magic rollback                   ║  │
│  ║  CI/CD ── std runnables + Tangled Spindles                       ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                              │                                         │
│  ╔═══════════════════════════▼═══════════════════════════════════════╗  │
│  ║                    🔀 СЛОЙ КОДА (децентрализованный)             ║  │
│  ║                                                                   ║  │
│  ║  Tangled ── social coding на AT Protocol                         ║  │
│  ║    • Knots (self-hosted git servers)                              ║  │
│  ║    • Spindles (CI/CD)                                             ║  │
│  ║    • NixOS deployment из коробки                                 ║  │
│  ║                                                                   ║  │
│  ║  Radicle ── P2P git forge (backup/alternative)                   ║  │
│  ║    • Gossip protocol для metadata                                ║  │
│  ║    • Офлайн-first                                                ║  │
│  ║    • Issues/patches как Git-объекты                              ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                              │                                         │
│  ╔═══════════════════════════▼═══════════════════════════════════════╗  │
│  ║                    📦 СЛОЙ ХРАНИЛИЩА                              ║  │
│  ║                                                                   ║  │
│  ║  Content-Addressed Nix Store                                     ║  │
│  ║    ↓ (когда стабилизируется)                                     ║  │
│  ║  IPFS Binary Cache (PR #3727 → Trustful IPFS Store)             ║  │
│  ║    ↓                                                              ║  │
│  ║  IPFS Cluster ── репликация по кластеру                          ║  │
│  ║    ↓                                                              ║  │
│  ║  Каждая нода = binary cache + IPFS peer                          ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура репозиториев (3-repo архитектура)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  REPO 1: nn3w-framework                                                │
│  ═══════════════════════                                                │
│  Общая платформа. Экспортирует через Den namespaces.                   │
│                                                                         │
│  modules/                                                               │
│  ├── classes/                          Den кастомные классы             │
│  │   ├── enclave.nix                   L0-L4 forwarding                │
│  │   ├── mesh-node.nix                 IPFS/libp2p конфиг             │
│  │   ├── sovereign-service.nix         Self-hosted шаблон             │
│  │   └── cluster-role.nix              K3s/workload identity          │
│  ├── aspects/                          Общие аспекты                   │
│  │   ├── security/                     TPM, SEV, attestation          │
│  │   ├── networking/                   WireGuard, mesh, overlay       │
│  │   ├── monitoring/                   Prometheus, Grafana            │
│  │   ├── storage/                      IPFS, MinIO, backup            │
│  │   └── compute/                      K3s, MicroVM, GPU             │
│  ├── schema/                           Расширения den.schema          │
│  │   ├── enclave.nix                   options для анклавов           │
│  │   └── mesh.nix                      options для mesh nodes         │
│  └── ctx/                              Кастомные ctx pipelines        │
│      ├── enclave-host.nix              ctx.enclave-host               │
│      └── mesh-participant.nix          ctx.mesh-participant           │
│                                                                         │
│  Экспортирует:                                                          │
│    den.ful.nn3w.enclave-system                                         │
│    den.ful.nn3w.mesh-networking                                        │
│    den.ful.nn3w.sovereign-services                                     │
│    den.ful.nn3w.cluster-compute                                        │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  REPO 2: nn3w-infra                                                    │
│  ══════════════════                                                    │
│  Конкретная инфраструктура. Хосты, Clan fleet, деплой.                │
│                                                                         │
│  inputs: nn3w-framework, den, clan, std                                │
│                                                                         │
│  hosts/                                Den hosts                        │
│  │  den.hosts.x86_64-linux.                                            │
│  │    vladOS = { users.vladdd183; };   Рабочая станция                │
│  │    angron = { users.kubeadmin;      K3s + CI + storage             │
│  │              roles = ["compute"]; };                                 │
│  │    perturabo = { users.kubeadmin;   K3s + GPU + enclaves           │
│  │                  enclaves = [...]; };                                │
│  │                                                                      │
│  aspects/                              Инфра-специфичные аспекты       │
│  │  den.aspects.angron = {                                             │
│  │    includes = [                                                      │
│  │      den.ful.nn3w.cluster-compute                                   │
│  │      den.ful.nn3w.sovereign-services                                │
│  │    ];                                                                │
│  │    nixos.services.k3s = { ... };                                    │
│  │  };                                                                  │
│  │                                                                      │
│  clan/                                 Clan fleet config               │
│  │  inventory.instances = {                                            │
│  │    zerotier = { ... };                                              │
│  │    monitoring = { ... };                                            │
│  │    borgbackup = { ... };                                            │
│  │  };                                                                  │
│  │                                                                      │
│  ops/                                  std Cells для CI/CD             │
│  │  nix/ops/                                                            │
│  │    containers.nix                   OCI images                      │
│  │    deploys.nix                      deploy-rs targets               │
│  │    configs.nix                      Nixago configs                  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  REPO 3: nn3w-personal                                                 │
│  ═════════════════════                                                 │
│  Десктоп, home, личные аспекты.                                        │
│                                                                         │
│  inputs: nn3w-framework, den                                           │
│                                                                         │
│  den.aspects.vladdd183 = {                                             │
│    includes = [                                                         │
│      den.ful.nn3w.mesh-networking                                      │
│      den.provides.primary-user                                         │
│      (den.provides.user-shell "xonsh")                                 │
│    ];                                                                   │
│    homeManager = { ... };                                              │
│    user.extraGroups = [ "wheel" "docker" ];                            │
│    darwin.services.karabiner-elements.enable = true;                   │
│  };                                                                     │
│                                                                         │
│  den.aspects.desktop = {                                               │
│    includes = [ den.aspects.audio den.aspects.bluetooth ];             │
│    nixos.services.desktopManager.plasma6.enable = true;                │
│  };                                                                     │
│                                                                         │
│  configs/                              Dotfiles: nvim, zellij, xonsh   │
│  secrets/                              Personal SOPS secrets           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Как стек работает вместе (data flow)

```
                    nn3w-framework
                    (Den namespaces)
                         │
            ┌────────────┼────────────┐
            │            │            │
            ▼            ▼            ▼
      nn3w-infra    nn3w-personal   (future: others)
      (Den + Clan    (Den aspects)   (anyone can import
       + std)                         nn3w namespaces)
            │            │
            │  imports    │ imports
            ▼            ▼
      ┌──────────────────────┐
      │   Den Resolution     │
      │                      │
      │ den.ctx.host ──►     │
      │   den.ctx.user ──►   │
      │     den.ctx.hm-user  │
      │       + custom ctx   │
      │         (enclave,    │
      │          mesh, etc.) │
      └───────────┬──────────┘
                  │
      ┌───────────▼──────────┐
      │   Output Generation  │
      │                      │
      │ nixosConfigurations  │
      │ homeConfigurations   │
      │ deploy nodes         │
      │ OCI containers       │
      │ MicroVM images       │
      └───────────┬──────────┘
                  │
      ┌───────────▼──────────┐
      │   Clan Fleet Mgmt    │
      │                      │
      │ mesh VPN ── secrets  │
      │ backups ── services  │
      │ data mesher ── GUI   │
      └──────────────────────┘
```

---

## 📋 Что берём — финальный чеклист

### ✅ Определённо берём

| Компонент | Зачем | Готовность |
|:---|:---|:---:|
| **Den v0.12.0** | Ядро конфигурации | ✅ |
| **flake-aspects v0.7.0** | Фундамент Den | ✅ |
| **flake-parts** | Модульная система | ✅ |
| **Clan 25.11** | Fleet management, mesh, secrets | ✅ |
| **std** | CI/CD, Cell organization, TUI | ✅ |
| **Nixago** | Генерация dev-конфигов | ✅ |
| **deploy-rs** | Production deployment + rollback | ✅ |
| **sops-nix** | Секреты (через Clan vars) | ✅ |

### 🟡 Берём когда стабилизируется / по необходимости

| Компонент | Зачем | Готовность |
|:---|:---|:---:|
| **Tangled** | Децентрализованный git + CI | 🟡 Ранний |
| **Radicle** | P2P git backup | 🟡 v1.6 |
| **Dendrix** | Community аспекты | 🟡 Зарождается |
| **Content-Addressed Nix → IPFS** | Децентр. binary cache | 🟡 WIP |
| **Clan Spaces** | Изолированные окружения | 🔴 Прототип |

### ❌ Не берём

| Компонент | Почему |
|:---|:---|
| **Snowfall Lib** | Den покрывает всё + больше, несовместим с flake-parts |
| **digga** | Deprecated |
| **Blueprint** | Слишком примитивен |
| **hive** | Den делает то же лучше |
| **flake-utils (голый)** | flake-parts делает то же + модульность |

### 📝 Сохранить на потом (knowledge base)

| Компонент | Зачем помнить |
|:---|:---|
| **Paisano** | Если нужен standalone TUI без полного std |
| **nix-casync (идеи)** | Chunk-based store для оптимизации IPFS интеграции |
| **Nixda Stack** | Reference architecture для sovereign self-hosting |
| **Golem Network** | Спонсор Clan, децентрализованные вычисления |

---

## 🚀 Следующие шаги

1. **Инициализировать nn3w-framework** с Den template (minimal или default)
2. **Спроектировать кастомные Den-классы** для enclave, mesh-node, sovereign-service
3. **Мигрировать ключевые аспекты из vladOS-v2** в Den формат
4. **Интегрировать Clan** для fleet management между хостами
5. **Настроить std** для CI/CD пайплайнов
6. **Следить за IPFS PR #3727** и Clan Spaces для будущей интеграции
