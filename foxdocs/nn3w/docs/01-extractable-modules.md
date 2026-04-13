# 🧩 Извлекаемые модули — Extractability-First паттерн

> **Суть:** Каждая директория в `aspects/` — самодостаточный набор flake-parts модулей.
> В любой момент можно вынести её в отдельный репозиторий, а в монорепе
> подключить обратно через flake input. Без рефакторинга, без боли.

---

## 🎯 Зачем это нужно

| Проблема | Как решает extractability |
|:---|:---|
| 🔒 Хочу расшарить `dev/` аспекты с коллегой | Выносишь `aspects/dev/` в публичную репу |
| 🌐 Хочу сделать open-source фреймворк | Выносишь `aspects/core/` + `aspects/exclave/` + `lib/` |
| 🏢 Компания хочет использовать мои наработки | Выносишь нужные аспекты, компания подключает через input |
| 📦 Монорепа стала слишком большой | Выносишь крупные блоки, оставляя wiring |

---

## 🏗️ Архитектура: модуль как единица извлечения

```mermaid
graph TB
  subgraph monorepo ["🏠 nn3w монорепа"]
    subgraph extractable ["🧩 Извлекаемые блоки"]
      core["aspects/core/\nbase, networking,\nsecurity, nix-settings"]
      desktop["aspects/desktop/\nhyprland, audio,\nbluetooth, fonts, gtk-qt"]
      dev["aspects/dev/\ngit, neovim,\nlanguages/, containers"]
      server["aspects/server/\nssh, monitoring, backup"]
      exclave["aspects/exclave/\n_forward-class, base,\nwireguard, services/"]
      libDir["lib/\nhelpers, exclave utils"]
    end

    subgraph nonExtractable ["⚙️ Wiring (не извлекается)"]
      modules["modules/\nden.nix, clan.nix,\ndeploy.nix"]
      hosts["hosts/\nhardware, aspect selection"]
      secrets["secrets/\nзашифрованные данные"]
    end
  end

  core -.->|"можно вынести"| coreRepo["📦 nn3w-core\n(отдельная репа)"]
  desktop -.->|"можно вынести"| desktopRepo["📦 nn3w-desktop\n(отдельная репа)"]
  dev -.->|"можно вынести"| devRepo["📦 nn3w-dev\n(отдельная репа)"]
  server -.->|"можно вынести"| serverRepo["📦 nn3w-server\n(отдельная репа)"]
  exclave -.->|"можно вынести"| exclaveRepo["📦 nn3w-exclave\n(отдельная репа)"]
```

---

## 📏 Правила написания извлекаемого модуля

### ✅ Что ДЕЛАТЬ

| Правило | Пример | Почему |
|:---|:---|:---|
| Использовать `den.ctx` для контекста | `{ host, user, ... }:` | Не привязан к конкретному хосту |
| Один аспект = один файл | `bluetooth.nix` | Гранулярная переиспользуемость |
| Зависимости через `includes` | `includes = [ den.aspects.audio ]` | Явные, прослеживаемые связи |
| Параметрические значения | `{ OS, ... }: { nixos = ...; darwin = ...; }` | Работает на любой платформе |
| Валидный flake-parts модуль | `{ ... }: { den.aspects.X = ...; }` | Можно импортировать откуда угодно |

### ❌ Чего НЕ делать

| Антипаттерн | Почему плохо | Как правильно |
|:---|:---|:---|
| `den.hosts.vladOS.nixos.hardware.bluetooth` | Хардкод имени хоста | `den.aspects.bluetooth = { nixos = ...; }` |
| `users.users.vladdd183.packages = [...]` | Хардкод имени юзера | `den.aspects.X.user = { packages = [...]; }` |
| `import ../hosts/vladOS/hardware.nix` | Relative import вне aspect | Использовать `den.ctx` |
| Секреты внутри aspect-файла | Утечка при извлечении | Секреты в `secrets/`, ссылка через sops |

---

## 🔬 Анатомия извлекаемого модуля

### Пример: `aspects/desktop/bluetooth.nix`

```nix
# Это валидный flake-parts модуль.
# Не знает на каком хосте будет применён.
# Не знает имя пользователя.
# Работает на NixOS и (при желании) Darwin.
{ ... }:
{
  den.aspects.bluetooth = {
    # Зависимость — аудио нужен для A2DP профиля
    includes = [ den.aspects.audio ];

    # NixOS-часть аспекта
    nixos = { pkgs, ... }: {
      hardware.bluetooth = {
        enable = true;
        powerOnBoot = true;
        settings.General.Experimental = true;
      };
      services.blueman.enable = true;
    };

    # Home-Manager часть аспекта
    homeManager = { ... }: {
      services.blueman-applet.enable = true;
    };
  };
}
```

### Что делает этот модуль самодостаточным:

```mermaid
flowchart LR
  subgraph module ["📄 bluetooth.nix"]
    aspect["den.aspects.bluetooth"]
    includes["includes =\n[ den.aspects.audio ]"]
    nixos["nixos = { ... }\nhardware.bluetooth\nservices.blueman"]
    hm["homeManager = { ... }\nblueman-applet"]
  end

  aspect --> includes
  aspect --> nixos
  aspect --> hm

  includes -.->|"зависимость"| audio["aspects/desktop/audio.nix"]
```

- ✅ Знает свои зависимости (`includes`)
- ✅ Содержит конфиг для всех классов (nixos + homeManager)
- ❌ Не знает имя хоста
- ❌ Не знает имя пользователя
- ❌ Не содержит секретов

---

## 🔄 Процесс извлечения: шаг за шагом

### Сценарий: выносим `aspects/desktop/` в отдельную репу

```mermaid
sequenceDiagram
  participant Mono as 🏠 nn3w (монорепа)
  participant New as 📦 nn3w-desktop (новая репа)
  participant Git as 🌐 Git (GitHub/Radicle)

  Note over Mono: ШАГ 1: Копируем файлы
  Mono->>New: cp -r aspects/desktop/* → src/
  Mono->>New: Создаём flake.nix

  Note over New: ШАГ 2: Делаем flake
  New->>Git: git init && git push

  Note over Mono: ШАГ 3: Подключаем обратно
  Mono->>Mono: flake.nix: inputs.nn3w-desktop.url = "github:..."
  Mono->>Mono: Удаляем aspects/desktop/
  Mono->>Mono: aspects.nix: import nn3w-desktop modules

  Note over Mono: ШАГ 4: Всё работает как раньше
  Mono->>Mono: nix flake check ✅
```

### ШАГ 1: Структура новой репы

```
nn3w-desktop/
├── flake.nix           # Inputs: den, flake-parts
├── flake.lock
└── aspects/
    ├── hyprland.nix
    ├── audio.nix
    ├── bluetooth.nix
    ├── fonts.nix
    └── gtk-qt.nix
```

### ШАГ 2: flake.nix извлечённой репы

```nix
{
  description = "nn3w desktop aspects — Wayland, audio, bluetooth, theming";

  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    den.url = "github:vic/den";
    import-tree.url = "github:vic/import-tree";
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.den.flakeModule
        # Импортируем все .nix из aspects/
        (inputs.import-tree.importTree ./aspects)
      ];
    };
}
```

### ШАГ 3: Подключение в монорепе

```nix
# nn3w/flake.nix — добавляем input
{
  inputs = {
    # ... остальные inputs ...
    nn3w-desktop.url = "github:vladdd183/nn3w-desktop";
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        # Раньше: (inputs.import-tree.importTree ./aspects/desktop)
        # Теперь: импорт из отдельной репы
        inputs.nn3w-desktop.flakeModule
        # Остальные aspects по-прежнему локальные
        (inputs.import-tree.importTree ./aspects/core)
        (inputs.import-tree.importTree ./aspects/dev)
        (inputs.import-tree.importTree ./aspects/server)
        (inputs.import-tree.importTree ./aspects/exclave)
      ];
    };
}
```

---

## 🧰 Инструменты, обеспечивающие extractability

### 📦 import-tree — авто-импорт файлов

```mermaid
flowchart LR
  tree["import-tree\n./aspects/core/"] --> base["base.nix"]
  tree --> net["networking.nix"]
  tree --> sec["security.nix"]
  tree --> nix["nix-settings.nix"]

  base -->|"flake-parts module"| fp["flake-parts\nmodule bus"]
  net --> fp
  sec --> fp
  nix --> fp
```

`import-tree` рекурсивно обходит директорию и импортирует каждый `.nix` файл как flake-parts модуль. Не нужно поддерживать список импортов — кинул файл, он подхватился.

### 📄 flake-file — модуль несёт свои inputs

```nix
# aspects/dev/neovim.nix
{ inputs, ... }:
{
  # flake-file позволяет модулю декларировать свои inputs
  flake.file.inputs.nixvim.url = "github:nix-community/nixvim";

  den.aspects.neovim = {
    homeManager = { ... }: {
      imports = [ inputs.nixvim.homeManagerModules.nixvim ];
      programs.nixvim.enable = true;
    };
  };
}
```

Когда этот модуль извлекается в отдельную репу, его input (`nixvim`) уже задекларирован — не нужно вспоминать что ему требуется.

### 🌿 Den namespaces (`den.ful.*`) — кросс-flake шаринг

```nix
# В извлечённой репе nn3w-desktop:
den.ful.nn3w.desktop.hyprland = { ... };
den.ful.nn3w.desktop.audio = { ... };

# В монорепе после извлечения:
den.aspects.vladOS-desktop = {
  includes = [
    den.ful.nn3w.desktop.hyprland
    den.ful.nn3w.desktop.audio
  ];
};
```

---

## 📋 Карта извлечения: что можно вынести

```mermaid
graph TB
  subgraph tier1 ["🟢 Легко извлечь (нет зависимостей между собой)"]
    core["aspects/core/\n→ nn3w-core"]
    libDir["lib/\n→ nn3w-lib"]
    overlays["overlays/\n→ nn3w-overlays"]
  end

  subgraph tier2 ["🟡 Средне (зависят от core)"]
    desktop["aspects/desktop/\n→ nn3w-desktop"]
    dev["aspects/dev/\n→ nn3w-dev"]
    server["aspects/server/\n→ nn3w-server"]
  end

  subgraph tier3 ["🟠 Сложнее (зависят от core + server)"]
    exclave["aspects/exclave/\n→ nn3w-exclave"]
  end

  subgraph tier4 ["🔴 Не извлекается (wiring)"]
    modules["modules/"]
    hosts["hosts/"]
    users["users/"]
    secrets["secrets/"]
  end

  core -.-> desktop
  core -.-> dev
  core -.-> server
  core -.-> exclave
  server -.-> exclave
```

### Граф зависимостей аспектов

```mermaid
graph TD
  core_base["🔧 core/base"]
  core_net["🌐 core/networking"]
  core_sec["🔒 core/security"]
  core_nix["❄️ core/nix-settings"]

  desk_hypr["🖥️ desktop/hyprland"]
  desk_audio["🔊 desktop/audio"]
  desk_bt["📶 desktop/bluetooth"]
  desk_fonts["🔤 desktop/fonts"]
  desk_gtk["🎨 desktop/gtk-qt"]

  dev_git["📝 dev/git"]
  dev_nvim["✏️ dev/neovim"]
  dev_lang["💻 dev/languages/*"]
  dev_cont["📦 dev/containers"]

  srv_ssh["🔑 server/ssh"]
  srv_mon["📊 server/monitoring"]
  srv_bak["💾 server/backup"]

  exc_class["⚙️ exclave/_forward-class"]
  exc_base["📦 exclave/base"]
  exc_wg["🌐 exclave/wireguard"]
  exc_svc["🧩 exclave/services/*"]

  core_base --> core_net
  core_base --> core_sec
  core_base --> core_nix

  core_base --> desk_hypr
  desk_audio --> desk_bt
  core_base --> desk_audio
  core_base --> desk_fonts
  desk_fonts --> desk_gtk

  core_base --> dev_git
  core_base --> dev_nvim
  core_base --> dev_lang
  core_base --> dev_cont

  core_base --> srv_ssh
  core_sec --> srv_ssh
  core_base --> srv_mon
  core_base --> srv_bak

  exc_class --> exc_base
  core_net --> exc_wg
  srv_ssh --> exc_base
  exc_base --> exc_svc
  exc_wg --> exc_svc
```

---

## ⚡ Быстрый чеклист: мой модуль извлекаем?

- [ ] Файл — валидный flake-parts модуль (`{ ... }: { den.aspects.X = ...; }`)
- [ ] Нет хардкода имён хостов (`vladOS`, `angron`)
- [ ] Нет хардкода имён пользователей (`vladdd183`)
- [ ] Нет `import` путей вне своей директории
- [ ] Нет секретов внутри файла
- [ ] Зависимости заявлены через `includes`
- [ ] (Опционально) Inputs через `flake-file`
- [ ] Работает с `nix flake check` при изолированном тестировании

---

## 🔗 Связанные документы

| Документ | Тема |
|:---|:---|
| [00-architecture.md](00-architecture.md) | 🏛️ Общая архитектура монорепы |
| [02-den-configuration.md](02-den-configuration.md) | 🌿 Den aspects, schema, ctx — как писать аспекты |
