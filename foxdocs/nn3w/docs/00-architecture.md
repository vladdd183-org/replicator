# 🏛️ nn3w — Архитектура монорепы

> **nn3w** — приватная монорепа на Den для управления всей личной инфраструктурой.
> Десктоп, ноутбук, личный сервер, exclaves на серверах компании.
> Каждый модуль — самодостаточный и готов к выносу в отдельную репу.

---

## 📐 Принципы проектирования

| Принцип | Суть | Почему важно |
|:---|:---|:---|
| 🧩 **Extractability-first** | Каждый aspect — self-contained flake-parts модуль | В любой момент вынести в отдельную репу без рефакторинга |
| 🎯 **Aspect-oriented** | Конфиг по фичам (bluetooth, dev-tools), не по хостам | Одна фича = один файл, работает на всех платформах |
| ⚙️ **Parametric** | Aspects — функции от контекста `{ host, user }` | Нет хардкода имён хостов/юзеров, всё переиспользуемо |
| 🔐 **Trust isolation** | Exclave-секреты зашифрованы только личными ключами | Компания физически не может прочитать содержимое |
| 📏 **Flexible resources** | Exclaves без жёстких лимитов по умолчанию | Используешь все ресурсы сервера, ограничиваешь только при желании |
| 🔄 **Declarative everything** | Вся инфраструктура = Nix-код в git | Воспроизводимость, аудируемость, откат |

---

## 🗺️ Общая картина

```mermaid
graph TB
  subgraph monorepo ["🏠 nn3w монорепа (приватная)"]
    direction TB
    aspects["🧩 aspects/\nCore, Desktop, Dev,\nServer, Exclave"]
    hosts["🖥️ hosts/\nvladOS, vladLaptop,\nvladServer, exclaves"]
    modules["⚙️ modules/\nDen, Clan, Deploy,\nDevShell"]
    secrets["🔐 secrets/\nPersonal, Exclaves"]
    users["👤 users/\nvladdd183"]
  end

  subgraph targets ["🎯 Целевые машины"]
    desktop["🖥️ Десктоп\nvladOS"]
    laptop["💻 Ноутбук\nvladLaptop"]
    server["🖧 Личный сервер\nvladServer"]
    exc1["📦 Exclave #1\nна сервере компании"]
    exc2["📦 Exclave #2\nна сервере компании"]
  end

  subgraph company ["🏢 Snowfall компании"]
    snowfall["❄️ company-infra\nSnowfall конфиг"]
    srv1["🖧 Сервер #1\n(angron)"]
    srv2["🖧 Сервер #2\n(perturabo)"]
  end

  monorepo -->|"nixos-rebuild"| desktop
  monorepo -->|"nixos-rebuild"| laptop
  monorepo -->|"nixos-rebuild"| server
  monorepo -->|"deploy-rs"| exc1
  monorepo -->|"deploy-rs"| exc2

  snowfall -->|"nixos-rebuild"| srv1
  snowfall -->|"nixos-rebuild"| srv2
  srv1 -->|"MicroVM slot"| exc1
  srv2 -->|"MicroVM slot"| exc2
```

---

## 🧱 Стек технологий

```mermaid
graph TB
  subgraph userLayer ["👤 Слой пользователя"]
    nh["nh CLI\nбыстрый rebuild/switch"]
    devshell["nix develop\ndevShell с инструментами"]
  end

  subgraph configLayer ["🌿 Слой конфигурации — Den"]
    schema["den.schema\nхосты, юзеры, exclaves"]
    aspects["den.aspects\nфича-first модули"]
    ctx["den.ctx\nконтекстный pipeline"]
    provides["den.provides\nforward classes"]
  end

  subgraph infraLayer ["🏰 Слой инфраструктуры — Clan"]
    fleet["Fleet Management\nбез центр. контроллера"]
    mesh["Mesh VPN\nWireGuard/ZeroTier"]
    vars["Vars / Secrets\nsops-nix интеграция"]
    backup["Backups\nBorgBackup"]
  end

  subgraph deployLayer ["🚀 Слой деплоя"]
    deployrs["deploy-rs\nremote deploy + rollback"]
    disko["disko\nдекларативная разметка"]
    microvm["microvm.nix\nVM для exclaves"]
  end

  subgraph foundation ["🔧 Фундамент"]
    fp["flake-parts\nмодульная шина"]
    fa["flake-aspects\nаспект-зависимости"]
    it["import-tree\nавто-импорт .nix"]
    ff["flake-file\nсамодостаточные модули"]
  end

  userLayer --> configLayer
  configLayer --> infraLayer
  infraLayer --> deployLayer
  deployLayer --> foundation
```

### 📋 Конкретные версии и роли

| Компонент | Версия | Роль в стеке |
|:---|:---:|:---|
| **Den** | v0.12+ | Ядро конфигурации: schema, aspects, ctx pipeline, custom forward classes |
| **flake-aspects** | v0.7+ | Composable cross-class зависимости между аспектами |
| **flake-file** | latest | Модули декларируют свои flake inputs (для будущего извлечения) |
| **import-tree** | latest | Авто-импорт .nix файлов из директорий |
| **Clan** | 25.11 | Fleet management, mesh VPN, vars/secrets, backups |
| **microvm.nix** | latest | Декларативные VM для exclaves на серверах компании |
| **sops-nix** | latest | Шифрованные секреты per trust domain (age/GPG) |
| **deploy-rs** | latest | Remote deployment в exclaves с magic rollback |
| **disko** | latest | Декларативная разметка дисков (LUKS, Btrfs, subvolumes) |
| **flake-parts** | latest | Модульная шина — всё стыкуется через него |

---

## 📁 Структура монорепы

```mermaid
graph LR
  subgraph root ["📦 nn3w/"]
    flake["📄 flake.nix"]
    sops["🔑 .sops.yaml"]

    subgraph mod ["⚙️ modules/"]
      den_nix["den.nix"]
      aspects_nix["aspects.nix"]
      clan_nix["clan.nix"]
      deploy_nix["deploy.nix"]
      devshell_nix["devshell.nix"]
    end

    subgraph asp ["🧩 aspects/"]
      core["core/\nbase, networking,\nsecurity, nix-settings"]
      desktop["desktop/\nhyprland, audio,\nbluetooth, fonts, gtk-qt"]
      dev["dev/\ngit, neovim,\nlanguages/, containers"]
      srv["server/\nssh, monitoring, backup"]
      exc["exclave/\n_forward-class, base,\nwireguard, services/"]
    end

    subgraph hst ["🖥️ hosts/"]
      vladOS["vladOS/"]
      vladLaptop["vladLaptop/"]
      vladServer["vladServer/"]
      exclaves["exclaves/\nangron-exc/\nperturabo-exc/"]
    end

    subgraph other ["📂 Остальное"]
      usersDir["users/vladdd183/"]
      secretsDir["secrets/\npersonal/ exclaves/"]
      libDir["lib/"]
      overlaysDir["overlays/"]
      docsDir["docs/"]
    end
  end
```

### 📂 Подробная файловая структура

```
nn3w/
├── 📄 flake.nix                        # Корневой flake: inputs + import-tree modules/
├── 📄 flake.lock                       # Зафиксированные версии зависимостей
├── 🔑 .sops.yaml                       # sops-nix: правила шифрования по путям
│
├── ⚙️ modules/                         # flake-parts модули (wiring)
│   ├── den.nix                         # Den schema: hosts, users, exclaves
│   ├── aspects.nix                     # Подключение aspects → hosts
│   ├── clan.nix                        # Clan fleet, mesh, vars, backups
│   ├── deploy.nix                      # deploy-rs targets для exclaves
│   └── devshell.nix                    # nix develop — инструменты разработки
│
├── 🧩 aspects/                         # Den aspects (ИЗВЛЕКАЕМЫЕ МОДУЛИ)
│   │
│   ├── core/                           # ── будущая репа: nn3w-core ──
│   │   ├── base.nix                    #   locale, timezone, nix daemon
│   │   ├── networking.nix              #   NetworkManager, firewall базовый
│   │   ├── security.nix                #   sudo, PAM, hardening
│   │   └── nix-settings.nix            #   nix.conf, substituters, gc
│   │
│   ├── desktop/                        # ── будущая репа: nn3w-desktop ──
│   │   ├── hyprland.nix                #   Wayland compositor + конфиг
│   │   ├── audio.nix                   #   Pipewire + WirePlumber
│   │   ├── bluetooth.nix              #   Bluez + Blueman
│   │   ├── fonts.nix                   #   Nerd Fonts, системные шрифты
│   │   └── gtk-qt.nix                  #   GTK/Qt темы, курсоры, иконки
│   │
│   ├── dev/                            # ── будущая репа: nn3w-dev ──
│   │   ├── git.nix                     #   Git + lazygit + delta
│   │   ├── neovim.nix                  #   Neovim + плагины
│   │   ├── languages/                  #   Языковые тулчейны
│   │   │   ├── nix.nix                 #     nil, nixd, alejandra
│   │   │   ├── rust.nix                #     rustup, cargo, rust-analyzer
│   │   │   └── python.nix              #     python3, poetry, ruff
│   │   └── containers.nix              #   Docker/Podman + compose
│   │
│   ├── server/                         # ── будущая репа: nn3w-server ──
│   │   ├── ssh.nix                     #   OpenSSH server + hardening
│   │   ├── monitoring.nix              #   Prometheus + node-exporter
│   │   └── backup.nix                  #   BorgBackup + scheduling
│   │
│   └── exclave/                        # ── будущая репа: nn3w-exclave ──
│       ├── _forward-class.nix          #   Den custom forward class: exclave
│       ├── base.nix                    #   Базовый конфиг exclave VM
│       ├── wireguard.nix               #   WG tunnel в личный mesh
│       └── services/                   #   Сервисы для exclaves
│           ├── nextcloud.nix           #     Nextcloud + PostgreSQL
│           ├── gitea.nix               #     Gitea + runner
│           └── media.nix               #     Jellyfin / Plex
│
├── 🖥️ hosts/                           # Определения хостов (hardware + выбор aspects)
│   ├── vladOS/                         # 🖥️ Десктоп
│   │   ├── default.nix                 #   Den host: aspects, users
│   │   ├── hardware.nix                #   hardware-configuration.nix
│   │   └── disko.nix                   #   Разметка диска (LUKS + Btrfs)
│   ├── vladLaptop/                     # 💻 Ноутбук
│   │   ├── default.nix
│   │   ├── hardware.nix
│   │   └── disko.nix
│   ├── vladServer/                     # 🖧 Личный сервер
│   │   ├── default.nix
│   │   ├── hardware.nix
│   │   └── disko.nix
│   └── exclaves/                       # 📦 Exclaves на серверах компании
│       ├── angron-exc/                 #   Exclave на сервере #1
│       │   └── default.nix
│       └── perturabo-exc/              #   Exclave на сервере #2
│           └── default.nix
│
├── 👤 users/
│   └── vladdd183/
│       └── default.nix                 # User aspect: shell, пакеты, home
│
├── 🔐 secrets/
│   ├── personal/                       # Зашифровано личным age-ключом
│   │   ├── common.yaml                 #   Общие секреты (API keys, tokens)
│   │   └── wireguard.yaml              #   WireGuard private keys
│   └── exclaves/                       # Зашифровано exclave-ключами
│       ├── angron.yaml                 #   Секреты для exclave #1
│       └── perturabo.yaml              #   Секреты для exclave #2
│
├── 📚 lib/                             # Общие Nix-функции
│   ├── default.nix
│   └── exclave.nix                     # Хелперы для exclave-конфигурации
│
├── 🔧 overlays/
│   └── default.nix                     # Nixpkgs overlays
│
└── 📖 docs/                            # Документация (ты здесь)
    ├── 00-architecture.md
    ├── 01-extractable-modules.md
    ├── 02-den-configuration.md
    ├── 03-exclave-mechanism.md
    ├── 04-networking.md
    ├── 05-secrets.md
    ├── 06-deployment.md
    └── 07-roadmap.md
```

---

## 🔄 Потоки данных

### Как flake.nix связывает всё вместе

```mermaid
flowchart TD
  subgraph inputs ["📥 Flake Inputs"]
    nixpkgs["nixpkgs\n(nixos-unstable)"]
    den["den\n(vic/den)"]
    clan["clan-core\n(clan.lol)"]
    hm["home-manager"]
    microvm["microvm.nix"]
    sops["sops-nix"]
    deployrs["deploy-rs"]
    disko_input["disko"]
    it["import-tree"]
    ff["flake-file"]
  end

  subgraph bus ["🔌 flake-parts (шина)"]
    fp["mkFlake\nimports = modules/"]
  end

  subgraph ourModules ["⚙️ modules/"]
    denMod["den.nix\nschema + hosts + users"]
    aspMod["aspects.nix\nimport-tree aspects/"]
    clanMod["clan.nix\nfleet + mesh + vars"]
    deplMod["deploy.nix\ntargets + profiles"]
    devMod["devshell.nix\nnix develop"]
  end

  subgraph outputs ["📤 Flake Outputs"]
    nixosCfg["nixosConfigurations\nvladOS, vladLaptop,\nvladServer"]
    homeCfg["homeConfigurations\nvladdd183"]
    deployCfg["deploy.nodes\nangron-exc,\nperturabo-exc"]
    devShell["devShells\nnix develop"]
    checks["checks\nnix flake check"]
  end

  inputs --> bus
  bus --> ourModules
  ourModules --> outputs
```

### Жизненный цикл аспекта: от кода до машины

```mermaid
sequenceDiagram
  participant Dev as 👨‍💻 Разработчик
  participant Repo as 📦 nn3w монорепа
  participant Den as 🌿 Den Pipeline
  participant NixOS as 🐧 NixOS Machine
  participant Exclave as 📦 Exclave VM

  Dev->>Repo: Пишет aspect (bluetooth.nix)
  Repo->>Den: import-tree подхватывает
  Den->>Den: den.ctx разрешает контекст
  Den->>Den: den.aspects.bluetooth → { nixos, homeManager }
  Den->>NixOS: nixos-rebuild switch (десктоп)
  Den->>Exclave: deploy-rs (exclave VM)

  Note over Den: Аспект НЕ знает на какой машине<br/>он будет применён — это parametric dispatch
```

---

## 🏗️ Роль каждой директории

| Директория | Роль | Извлекаемая? | Зависит от |
|:---|:---|:---:|:---|
| `modules/` | Wiring — связывает Den, Clan, deploy | ❌ Нет | Всё остальное |
| `aspects/core/` | Базовые NixOS настройки | ✅ Да | Ничего |
| `aspects/desktop/` | GUI, аудио, Wayland | ✅ Да | core/ |
| `aspects/dev/` | Инструменты разработки | ✅ Да | core/ |
| `aspects/server/` | Серверные сервисы | ✅ Да | core/ |
| `aspects/exclave/` | Exclave-механизм: forward class, WG, сервисы | ✅ Да | core/, server/ |
| `hosts/` | Hardware + выбор aspects для каждой машины | ❌ Нет | aspects/ |
| `users/` | User-level конфиг | ❌ Нет | aspects/ |
| `secrets/` | Зашифрованные данные | ❌ Нет | hosts/ |
| `lib/` | Общие хелпер-функции | ✅ Да | Ничего |
| `overlays/` | Nixpkgs патчи | ✅ Да | Ничего |

---

## 🔑 Ключевые архитектурные решения

### 1. Почему Den, а не Snowfall?

| Критерий | Snowfall | Den | Почему критично |
|:---|:---|:---|:---|
| Кастомные классы | ❌ | ✅ `den.provides.forward` | Exclave как first-class concept |
| Кросс-flake шаринг | ❌ | ✅ Namespaces | Извлечение модулей в отдельные репы |
| Parametric dispatch | ❌ | ✅ `den.ctx` | Аспекты без хардкода имён |
| Совместимость с flake-parts | ❌ | ✅ Нативная | Clan, std, treefmt — всё через flake-parts |
| Библиотечный режим | ❌ | ✅ `den.lib` | Не-OS домены (Terranix, NixVim) |

> ❄️ Snowfall остаётся в Snowfall-конфиге **компании**. Мы его не трогаем.
> 🌿 Den используется только в **нашей личной** монорепе.

### 2. Почему монорепа, а не мультирепа?

```mermaid
graph LR
  subgraph now ["🏠 Сейчас: одна монорепа"]
    mono["nn3w/\nвсё в одном месте"]
  end

  subgraph later ["🌐 Потом: гибридный подход"]
    framework["nn3w-framework\n(публичная)"]
    personal["nn3w-personal\n(приватная)"]
    extracted["nn3w-desktop\n(извлечённая)"]
    personal -->|"flake input"| framework
    personal -->|"flake input"| extracted
  end

  now -->|"при желании"| later
```

**Сейчас** — монорепа, потому что:
- Проще разрабатывать (один `nix flake update`, один lock-файл)
- Атомарные изменения (aspect + host в одном коммите)
- Нет overhead на координацию между репами

**Потом** — извлекаем что нужно, потому что:
- Каждый aspect уже self-contained (extractability-first)
- `flake-file` позволяет модулю нести свои inputs
- `import-tree` позволяет cherry-pick из любого источника
- Den namespaces (`den.ful.*`) для кросс-flake шаринга

### 3. Взаимодействие с компанией

```mermaid
flowchart LR
  subgraph personal ["🔒 Приватное (только ты)"]
    nn3w["nn3w монорепа\n• aspects\n• hosts\n• secrets\n• exclave configs"]
  end

  subgraph company ["🏢 Компания"]
    snowfall["company-infra\n(Snowfall)"]
    srv1["Сервер #1"]
    srv2["Сервер #2"]
  end

  subgraph boundary ["🔐 Граница доверия"]
    slot1["MicroVM slot\n(минимальный модуль\nв Snowfall)"]
    slot2["MicroVM slot"]
  end

  snowfall --> srv1
  snowfall --> srv2
  srv1 --- slot1
  srv2 --- slot2
  nn3w -->|"deploy-rs\nчерез WireGuard"| slot1
  nn3w -->|"deploy-rs\nчерез WireGuard"| slot2
```

**Что делает компания:** добавляет один NixOS-модуль `exclave-slots.nix` в свой Snowfall — создаёт MicroVM slot с TAP interface и диском.

**Что делаешь ты:** деплоишь содержимое VM из своей монорепы. Компания видит VM и ресурсы, но НЕ содержимое (LUKS).

---

## 📊 Матрица: что где живёт

| Сущность | nn3w (приватная) | Company Snowfall | Exclave VM |
|:---|:---:|:---:|:---:|
| Den aspects | ✅ | — | — |
| Host definitions | ✅ | — | — |
| User configs | ✅ | — | — |
| Exclave definitions | ✅ | — | — |
| Personal secrets | ✅ (sops) | — | — |
| Exclave secrets | ✅ (sops) | — | 🔓 расшифр. |
| MicroVM slot config | — | ✅ | — |
| Exclave NixOS | ✅ (собирает) | — | 🏃 работает |
| WireGuard tunnel | ✅ (инициирует) | — | ✅ (терминирует) |
| Clan mesh | ✅ (управляет) | — | ✅ (участник) |

---

## 🔗 Связанные документы

| Документ | Тема |
|:---|:---|
| [01-extractable-modules.md](01-extractable-modules.md) | 🧩 Паттерн извлечения модулей в отдельные репы |
| [02-den-configuration.md](02-den-configuration.md) | 🌿 Den schema, aspects, ctx, forward classes |
| [03-exclave-mechanism.md](03-exclave-mechanism.md) | 📦 Exclave: MicroVM, LUKS, уровни изоляции |
| [04-networking.md](04-networking.md) | 🌐 Clan mesh, WireGuard, топология |
| [05-secrets.md](05-secrets.md) | 🔐 sops-nix, мульти-ключи, trust isolation |
| [06-deployment.md](06-deployment.md) | 🚀 deploy-rs, Clan, стратегии деплоя |
| [07-roadmap.md](07-roadmap.md) | 📋 Фазы миграции, порядок действий |
