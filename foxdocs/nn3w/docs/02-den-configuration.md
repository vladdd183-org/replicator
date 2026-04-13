# 🌿 Den — Конфигурация nn3w

> **Den** — аспект-ориентированный, контекстно-управляемый фреймворк
> для Dendritic Nix конфигураций. Ядро всей монорепы nn3w.
> Заменяет Snowfall полностью, добавляя кастомные классы, параметрический
> dispatch и кросс-flake шаринг.

---

## 🏗️ Как Den устроен

```mermaid
flowchart TD
  subgraph schema ["📋 den.schema — Декларация"]
    hosts["den.hosts\nx86_64-linux:\n  vladOS, vladLaptop,\n  vladServer, angron-exc,\n  perturabo-exc"]
    users["users внутри host:\nvladOS.users.vladdd183 = {}"]
    homes["den.homes\nstandalone HM конфиги"]
  end

  subgraph aspects ["🧩 den.aspects — Фичи"]
    bluetooth["den.aspects.bluetooth\n{ nixos, homeManager }"]
    devTools["den.aspects.dev-tools\n{ nixos, homeManager }"]
    sshAsp["den.aspects.ssh-server\n{ nixos }"]
    exclaveAsp["den.aspects.exclave-base\n{ exclave }"]
  end

  subgraph ctx ["⚙️ den.ctx — Контекстный Pipeline"]
    hostCtx["den.ctx.host\n{ class, system, users }"]
    userCtx["den.ctx.user\n{ userName, aspect }"]
    hmCtx["den.ctx.hm-user\n{ userName, homeDir }"]
  end

  subgraph provides ["🔌 den.provides — Batteries"]
    hostname["hostname\nавто-имя хоста"]
    primaryUser["primary-user\nпервый юзер → настройки"]
    userShell["user-shell\nвыбор оболочки"]
    forward["forward\nкастомные классы"]
  end

  subgraph outputs ["📤 Результат"]
    nixosCfgs["nixosConfigurations.*"]
    homeCfgs["homeConfigurations.*"]
    customOutputs["кастомные outputs\n(exclave images, etc.)"]
  end

  schema -->|"определяет"| ctx
  aspects -->|"применяются через"| ctx
  provides -->|"обогащает"| ctx
  ctx -->|"разрешается в"| outputs
```

---

## 📋 Den Schema — Определение хостов и пользователей

### Основной `modules/den.nix`

```nix
{ inputs, ... }:
{
  den.hosts.x86_64-linux = {

    # 🖥️ Десктоп
    vladOS = {
      users.vladdd183 = {};
    };

    # 💻 Ноутбук
    vladLaptop = {
      users.vladdd183 = {};
    };

    # 🖧 Личный сервер
    vladServer = {
      users.vladdd183 = {};
    };

    # 📦 Exclave на сервере компании #1
    angron-exc = {
      users.vladdd183 = {};
    };

    # 📦 Exclave на сервере компании #2
    perturabo-exc = {
      users.vladdd183 = {};
    };
  };

  # 🏠 Standalone Home Manager (для non-NixOS машин)
  den.homes.x86_64-linux = {
    vladdd183 = {};
  };
}
```

### Что происходит за кулисами

```mermaid
flowchart LR
  schema["den.hosts.x86_64-linux.vladOS\n.users.vladdd183 = {}"]

  schema -->|"создаёт"| hostCtx["den.ctx.host\n{ class = nixos\n  system = x86_64-linux\n  name = vladOS\n  users = [ vladdd183 ] }"]

  hostCtx -->|"для каждого user"| userCtx["den.ctx.user\n{ userName = vladdd183\n  aspect = vladdd183 }"]

  userCtx -->|"если есть HM"| hmCtx["den.ctx.hm-user\n{ userName = vladdd183\n  homeDirectory = /home/... }"]

  hostCtx -->|"выход"| nixosCfg["nixosConfigurations.vladOS"]
  hmCtx -->|"выход"| hmCfg["home-manager.users.vladdd183"]
```

---

## 🧩 Den Aspects — Фичи, не хосты

### Анатомия аспекта

```mermaid
graph TB
  subgraph aspect ["🧩 den.aspects.bluetooth"]
    includes["includes = [\n  den.aspects.audio\n]"]
    nixos["nixos = { pkgs, ... }:\n{\n  hardware.bluetooth.enable = true;\n  services.blueman.enable = true;\n}"]
    hm["homeManager = { ... }:\n{\n  services.blueman-applet.enable = true;\n}"]
    darwin["darwin = { ... }:\n{ ... }"]
  end

  includes -->|"зависимость"| audioAspect["🔊 den.aspects.audio"]
  nixos -->|"применяется к"| nixosClass["NixOS хостам"]
  hm -->|"применяется к"| hmClass["Home Manager юзерам"]
  darwin -->|"применяется к"| darwinClass["macOS хостам"]
```

### Классы в Den

| Класс | Куда применяется | Когда используется |
|:---|:---|:---|
| `nixos` | `nixosConfigurations.*` | Любой NixOS хост |
| `darwin` | `darwinConfigurations.*` | macOS машины |
| `homeManager` | `home-manager.users.*` | Home Manager конфиг юзера |
| `user` | `users.users.${userName}` | OS-уровень юзера (groups, shell) |
| `exclave` | **Кастомный** → forward в MicroVM | Exclave VM на сервере компании |

### Как аспекты подключаются к хостам

```nix
# hosts/vladOS/default.nix
{ ... }:
{
  den.aspects.vladOS = {
    includes = [
      # Базовые
      den.aspects.base
      den.aspects.networking
      den.aspects.security
      den.aspects.nix-settings

      # Десктоп
      den.aspects.hyprland
      den.aspects.audio
      den.aspects.bluetooth
      den.aspects.fonts
      den.aspects.gtk-qt

      # Разработка
      den.aspects.git
      den.aspects.neovim
      den.aspects.nix-lang
      den.aspects.rust-lang
      den.aspects.containers
    ];

    # Специфичное для этого хоста (hardware и т.д.)
    nixos = { ... }: {
      imports = [ ./hardware.nix ./disko.nix ];
      boot.loader.systemd-boot.enable = true;
    };
  };
}
```

```nix
# hosts/exclaves/angron-exc/default.nix
{ ... }:
{
  den.aspects.angron-exc = {
    includes = [
      # Базовые серверные
      den.aspects.base
      den.aspects.security
      den.aspects.ssh-server

      # Exclave-специфичные
      den.aspects.exclave-base
      den.aspects.exclave-wireguard

      # Сервисы внутри exclave
      den.aspects.nextcloud
      den.aspects.gitea
    ];

    nixos = { ... }: {
      # Exclave-специфичные настройки
      networking.hostName = "angron-exc";
    };
  };
}
```

---

## ⚙️ Den Context Pipeline — Параметрический dispatch

### Как контекст течёт через систему

```mermaid
sequenceDiagram
  participant Schema as 📋 den.schema
  participant Host as ⚙️ den.ctx.host
  participant User as 👤 den.ctx.user
  participant HM as 🏠 den.ctx.hm-user
  participant Aspect as 🧩 den.aspects.*
  participant Output as 📤 nixosConfiguration

  Schema->>Host: vladOS { users.vladdd183 }
  Host->>Host: class = "nixos"<br/>system = "x86_64-linux"
  Host->>User: для каждого user
  User->>User: userName = "vladdd183"<br/>aspect = "vladdd183"
  User->>HM: если homeManager подключен
  HM->>HM: homeDirectory = "/home/vladdd183"

  Host->>Aspect: den.aspects.vladOS.nixos
  Note over Aspect: Аспект получает контекст:<br/>{ host, ... } — хост<br/>{ user, ... } — юзер<br/>{ OS, ... } — платформа

  Aspect->>Output: Итоговый NixOS конфиг
```

### Параметрический аспект — пример

```nix
# Аспект который ведёт себя по-разному в зависимости от контекста
den.aspects.dev-environment = {
  includes = [
    den.aspects.git
    den.aspects.neovim
  ];

  # OS-уровень: разный для NixOS и Darwin
  nixos = { pkgs, ... }: {
    programs.nix-ld.enable = true;
    environment.systemPackages = with pkgs; [ gcc gnumake ];
  };

  darwin = { pkgs, ... }: {
    environment.systemPackages = with pkgs; [ darwin.cctools ];
  };

  # User-уровень: shell, groups
  user = { ... }: {
    extraGroups = [ "wheel" "docker" "video" ];
  };

  # Home Manager: пользовательские пакеты
  homeManager = { pkgs, ... }: {
    home.packages = with pkgs; [
      ripgrep fd bat eza zoxide
      lazygit delta
    ];
  };
};
```

**Ключевой момент:** этот аспект НЕ знает что `vladdd183` — это юзер на `vladOS`. Он получает контекст автоматически через `den.ctx`, и `user.extraGroups` автоматически расширяется в `users.users.vladdd183.extraGroups` через forward class `user`.

---

## 🔌 Den Provides — Встроенные batteries

```mermaid
graph LR
  subgraph batteries ["🔌 den.provides"]
    hostname["hostname\nавтоматически ставит\nnetworking.hostName\nиз имени хоста в schema"]
    primaryUser["primary-user\nпервый юзер хоста\nстановится primary:\nautoLogin, sudo, etc."]
    userShell["user-shell shell\nустанавливает shell\nдля юзера:\nbash, zsh, fish, nushell"]
    forward["forward\nсоздаёт кастомный\nforward class"]
  end

  hostname -->|"автоматически"| hostName["networking.hostName = vladOS"]
  primaryUser -->|"автоматически"| autoLogin["displayManager.autoLogin.user = vladdd183"]
  userShell -->|"автоматически"| shell["users.users.vladdd183.shell = pkgs.fish"]
```

### Подключение batteries к аспекту пользователя

```nix
# users/vladdd183/default.nix
{ ... }:
{
  den.aspects.vladdd183 = {
    includes = [
      den.provides.primary-user
      (den.provides.user-shell "fish")
      den.aspects.dev-environment
    ];

    user = { ... }: {
      description = "Vladdd183";
      extraGroups = [ "wheel" "networkmanager" ];
    };

    homeManager = { pkgs, ... }: {
      home.stateVersion = "24.11";
      programs.fish.enable = true;
      programs.starship.enable = true;
    };
  };
}
```

---

## 🏗️ Custom Forward Class — Exclave

### Что такое forward class

Forward class — это механизм Den, который берёт один "псевдо-класс" (например `exclave`) и перенаправляет его содержимое в реальный NixOS конфиг по определённому пути.

```mermaid
flowchart TD
  subgraph write ["✏️ Что пишешь"]
    aspectCode["den.aspects.angron-exc.exclave = {\n  services.nextcloud.enable = true;\n}"]
  end

  subgraph forward ["⚙️ Forward class преобразует"]
    forwardClass["exclaveClass:\nберёт exclave.*\nи вставляет в\nmicrovm.vms.angron-exc.config.*"]
  end

  subgraph result ["📤 Результат"]
    nixosCode["nixosConfigurations.angron-srv = {\n  microvm.vms.angron-exc.config = {\n    services.nextcloud.enable = true;\n  };\n}"]
  end

  write --> forward --> result
```

### Реализация exclave forward class

```nix
# aspects/exclave/_forward-class.nix
{ lib, ... }:
{
  # Определяем кастомный forward class для exclaves
  den.aspects.exclave-system = {
    includes = [ exclaveForward ];
  };
}

# Суть forward:
# 1. Для каждого exclave-хоста в den.schema
# 2. Берём его аспекты с классом "exclave"
# 3. Forward-им в microvm.vms.${name}.config
# 4. Guard: только если microvm подключен

# Упрощённая схема (реальный код использует den._.forward):
# den._.forward {
#   each = exclaveHosts;
#   fromClass = exc: "exclave";
#   intoClass = _: "nixos";
#   intoPath = exc: [ "microvm" "vms" exc.name "config" ];
#   fromAspect = exc: den.aspects.${exc.aspect};
#   guard = { options, ... }: options ? microvm.vms;
# };
```

### Полная картина forward classes в nn3w

```mermaid
graph TB
  subgraph classes ["📋 Классы в nn3w"]
    nixos["nixos\n→ nixosConfigurations.*"]
    darwin["darwin\n→ darwinConfigurations.*"]
    hm["homeManager\n→ home-manager.users.*"]
    user_class["user (forward)\n→ users.users.userName.*"]
    exclave_class["exclave (forward)\n→ microvm.vms.name.config.*"]
  end

  subgraph native ["✅ Встроенные в Den"]
    nixos
    darwin
    hm
  end

  subgraph custom ["🔧 Наши кастомные"]
    user_class
    exclave_class
  end

  subgraph provid ["🔌 den.provides.forward"]
    userFwd["user forward:\nuser.X → users.users.name.X"]
    excFwd["exclave forward:\nexclave.X → microvm.vms.name.config.X"]
  end

  provid --> user_class
  provid --> exclave_class
```

---

## 📁 Wiring: modules/aspects.nix

Этот файл — мост между aspects/ директориями и Den.

```nix
# modules/aspects.nix
{ inputs, ... }:
{
  imports = [
    # Авто-импорт всех .nix из каждой директории аспектов
    (inputs.import-tree.importTree ../aspects/core)
    (inputs.import-tree.importTree ../aspects/desktop)
    (inputs.import-tree.importTree ../aspects/dev)
    (inputs.import-tree.importTree ../aspects/server)
    (inputs.import-tree.importTree ../aspects/exclave)

    # Хосты и юзеры
    (inputs.import-tree.importTree ../hosts)
    (inputs.import-tree.importTree ../users)
  ];
}
```

---

## 📊 Полная картина: от файла до машины

```mermaid
flowchart TD
  subgraph files ["📁 Файлы"]
    btNix["aspects/desktop/\nbluetooth.nix"]
    vladOsNix["hosts/vladOS/\ndefault.nix"]
    vladUserNix["users/vladdd183/\ndefault.nix"]
  end

  subgraph importPhase ["📥 Import"]
    importTree["import-tree\nавто-обнаружение"]
  end

  subgraph denPhase ["🌿 Den Pipeline"]
    aspects["den.aspects\nbluetooth, vladOS,\nvladdd183"]
    schema["den.schema\nvladOS → x86_64-linux\nusers → vladdd183"]
    ctx["den.ctx\nhost → user → hm-user"]
    resolution["Resolution:\naspect.nixos → NixOS config\naspect.homeManager → HM config\naspect.user → users.users.*"]
  end

  subgraph output ["📤 Результат"]
    nixosCfg["nixosConfigurations.vladOS\n= {\n  hardware.bluetooth.enable = true;\n  services.blueman.enable = true;\n  users.users.vladdd183 = { ... };\n  home-manager.users.vladdd183 = {\n    services.blueman-applet.enable = true;\n  };\n}"]
  end

  subgraph deploy ["🚀 Деплой"]
    rebuild["nixos-rebuild switch\n--flake .#vladOS"]
  end

  files --> importTree
  importTree --> aspects
  aspects --> schema
  schema --> ctx
  ctx --> resolution
  resolution --> nixosCfg
  nixosCfg --> rebuild
```

---

## 🔗 Связанные документы

| Документ | Тема |
|:---|:---|
| [00-architecture.md](00-architecture.md) | 🏛️ Общая архитектура монорепы |
| [01-extractable-modules.md](01-extractable-modules.md) | 🧩 Паттерн извлечения модулей |
| [03-exclave-mechanism.md](03-exclave-mechanism.md) | 📦 Exclave forward class в деталях |
