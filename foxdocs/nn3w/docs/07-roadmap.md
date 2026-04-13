# 📋 Roadmap — Фазы миграции и порядок действий

> Поэтапная миграция без "большого взрыва". Каждая фаза — рабочее состояние.
> Можно остановиться на любой фазе и продолжить позже.
> Текущий Snowfall компании работает параллельно до самого конца.

---

## 🗺️ Общая карта фаз

```mermaid
gantt
  title 📋 Roadmap миграции nn3w
  dateFormat YYYY-MM-DD
  axisFormat %b

  section 🏗️ Фаза 1 — Фундамент
    Создать монорепу + flake.nix          :f1a, 2026-03-20, 2d
    Den schema + базовые aspects          :f1b, after f1a, 3d
    Десктоп конфиг (vladOS)               :f1c, after f1b, 5d
    Переключить десктоп на nn3w           :f1d, after f1c, 1d
    Ноутбук конфиг (vladLaptop)           :f1e, after f1d, 3d

  section 📦 Фаза 2 — Exclaves
    Exclave slot модуль для компании      :f2a, after f1e, 2d
    WireGuard mesh (десктоп ↔ exclave)   :f2b, after f2a, 3d
    Первый deploy-rs деплой              :f2c, after f2b, 2d
    sops-nix секреты для exclaves        :f2d, after f2c, 2d

  section 🌐 Фаза 3 — Mesh и сервисы
    Clan fleet config                     :f3a, after f2d, 3d
    Личный сервер (vladServer)            :f3b, after f3a, 3d
    Перенос сервисов в exclaves           :f3c, after f3b, 5d
    Full mesh (все машины)                :f3d, after f3c, 2d

  section 🧹 Фаза 4 — Финализация
    Удалить личное из Snowfall            :f4a, after f3d, 1d
    Проверить всё работает               :f4b, after f4a, 2d
    Документация финальная               :f4c, after f4b, 1d
```

---

## 🏗️ Фаза 1 — Фундамент

> **Цель:** десктоп и ноутбук работают на nn3w (Den), полностью независимо от Snowfall компании.

```mermaid
flowchart TD
  subgraph phase1 ["🏗️ Фаза 1"]
    step1["1.1 Создать монорепу\nflake.nix + inputs"]
    step2["1.2 Den schema\n+ базовые aspects"]
    step3["1.3 Десктоп vladOS\nhardware + aspects"]
    step4["1.4 Переключить\nдесктоп на nn3w"]
    step5["1.5 Ноутбук\nvladLaptop"]

    step1 --> step2 --> step3 --> step4 --> step5
  end

  before["❄️ Snowfall компании\nвсё ещё работает\nпараллельно"]
  before -.-> phase1

  step5 --> result1["✅ Результат:\nДесктоп + ноутбук\nна Den, независимы\nот компании"]
```

### 📝 Шаг 1.1 — Создать монорепу

```bash
mkdir nn3w && cd nn3w
git init
# Создаём структуру
mkdir -p modules aspects/{core,desktop,dev,server,exclave/services}
mkdir -p hosts/{vladOS,vladLaptop,vladServer,exclaves/{angron-exc,perturabo-exc}}
mkdir -p users/vladdd183 secrets/{personal,exclaves} lib overlays docs
```

**Создать `flake.nix`:**

```nix
{
  description = "nn3w — personal sovereign infrastructure";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";

    # Den + Dendritic tools
    den.url = "github:vic/den";
    import-tree.url = "github:vic/import-tree";

    # Home Manager
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Секреты
    sops-nix = {
      url = "github:Mic92/sops-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # Диски
    disko = {
      url = "github:nix-community/disko";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.den.flakeModule
        # Наши модули
        (inputs.import-tree.importTree ./modules)
      ];

      systems = [ "x86_64-linux" ];
    };
}
```

**Чеклист шага 1.1:**
- [ ] `git init`
- [ ] Структура папок создана
- [ ] `flake.nix` с базовыми inputs
- [ ] `nix flake check` проходит

### 📝 Шаг 1.2 — Den schema + базовые aspects

**`modules/den.nix`** — определение хостов:

```nix
{ ... }:
{
  den.hosts.x86_64-linux = {
    vladOS = {
      users.vladdd183 = {};
    };
  };
}
```

**`aspects/core/base.nix`** — минимальный базовый аспект:

```nix
{ ... }:
{
  den.aspects.base = {
    nixos = { pkgs, ... }: {
      time.timeZone = "Europe/Moscow";
      i18n.defaultLocale = "ru_RU.UTF-8";

      nix.settings = {
        experimental-features = [ "nix-command" "flakes" ];
        auto-optimise-store = true;
      };

      environment.systemPackages = with pkgs; [
        vim git curl wget htop
      ];
    };
  };
}
```

**Чеклист шага 1.2:**
- [ ] `modules/den.nix` — vladOS host
- [ ] `aspects/core/base.nix` — locale, timezone, nix settings
- [ ] `aspects/core/networking.nix` — NetworkManager, firewall
- [ ] `aspects/core/security.nix` — sudo, hardening
- [ ] `users/vladdd183/default.nix` — user aspect
- [ ] `nix flake check` проходит

### 📝 Шаг 1.3 — Десктоп vladOS

Перенести hardware-configuration.nix с текущего десктопа:

```bash
cp /etc/nixos/hardware-configuration.nix hosts/vladOS/hardware.nix
```

Создать `hosts/vladOS/default.nix` с выбором aspects.

**Чеклист шага 1.3:**
- [ ] `hosts/vladOS/hardware.nix` скопирован
- [ ] `hosts/vladOS/disko.nix` (если используется disko)
- [ ] `hosts/vladOS/default.nix` — выбор aspects
- [ ] `aspects/desktop/*.nix` — hyprland, audio, bluetooth, fonts, gtk-qt
- [ ] `aspects/dev/*.nix` — git, neovim, languages
- [ ] `nix build .#nixosConfigurations.vladOS.config.system.build.toplevel`

### 📝 Шаг 1.4 — Переключить десктоп

```bash
# Тест: собрать без активации
sudo nixos-rebuild build --flake .#vladOS

# Если билд успешен:
sudo nixos-rebuild switch --flake .#vladOS

# Откат если что-то не так:
sudo nixos-rebuild switch --rollback
```

**Чеклист шага 1.4:**
- [ ] `nixos-rebuild build` проходит
- [ ] `nixos-rebuild switch` — десктоп работает
- [ ] GUI запускается
- [ ] Сеть работает
- [ ] Все нужные программы на месте

### 📝 Шаг 1.5 — Ноутбук

Аналогично шагу 1.3-1.4 для vladLaptop.

**Чеклист шага 1.5:**
- [ ] `hosts/vladLaptop/hardware.nix`
- [ ] `hosts/vladLaptop/default.nix`
- [ ] `nixos-rebuild switch --flake .#vladLaptop`
- [ ] Ноутбук работает на nn3w

---

## 📦 Фаза 2 — Exclaves

> **Цель:** первый exclave на сервере компании работает, WireGuard туннель установлен, deploy-rs настроен.

```mermaid
flowchart TD
  subgraph phase2 ["📦 Фаза 2"]
    step1["2.1 Exclave slot\nмодуль для Snowfall"]
    step2["2.2 WireGuard\nдесктоп ↔ exclave"]
    step3["2.3 deploy-rs\nпервый деплой"]
    step4["2.4 sops-nix\nsecrets для exclave"]

    step1 --> step2 --> step3 --> step4
  end

  phase1Result["✅ Фаза 1:\nДесктоп + ноутбук на nn3w"]
  phase1Result --> phase2

  step4 --> result2["✅ Результат:\nExclave #1 работает,\nWG tunnel активен,\nsecrets зашифрованы"]
```

### 📝 Шаг 2.1 — Exclave slot модуль

Отдаёшь компании файл `exclave-slots.nix` для их Snowfall:

```nix
# Минимальный модуль — см. docs/03-exclave-mechanism.md
{ inputs, ... }:
{
  imports = [ inputs.microvm.nixosModules.host ];
  microvm.autostart = [ "vladdd183-exclave" ];
  microvm.vms.vladdd183-exclave = { ... };
}
```

**Чеклист шага 2.1:**
- [ ] Модуль написан и протестирован
- [ ] Компания добавила в Snowfall
- [ ] `nixos-rebuild switch` на сервере компании
- [ ] MicroVM slot создан (`systemctl status microvm@vladdd183-exclave`)

### 📝 Шаг 2.2 — WireGuard

**Чеклист шага 2.2:**
- [ ] `aspects/exclave/wireguard.nix` создан
- [ ] WG ключи сгенерированы
- [ ] `ping 10.100.0.10` с десктопа работает
- [ ] `ssh root@10.100.0.10` работает

### 📝 Шаг 2.3 — Первый deploy-rs

**Чеклист шага 2.3:**
- [ ] `modules/deploy.nix` — конфиг deploy-rs
- [ ] `hosts/exclaves/angron-exc/default.nix` — хост exclave
- [ ] `deploy .#angron-exc` — успешный деплой
- [ ] Magic rollback тестирован

### 📝 Шаг 2.4 — sops-nix для exclave

**Чеклист шага 2.4:**
- [ ] `.sops.yaml` создан (см. docs/05-secrets.md)
- [ ] `secrets/exclaves/angron.yaml` зашифрован
- [ ] Exclave расшифровывает секреты при деплое
- [ ] WG private key из sops работает

---

## 🌐 Фаза 3 — Mesh и сервисы

> **Цель:** все машины в mesh-сети, сервисы перенесены в exclaves, Clan управляет флотом.

```mermaid
flowchart TD
  subgraph phase3 ["🌐 Фаза 3"]
    step1["3.1 Clan fleet\nконфигурация"]
    step2["3.2 Личный сервер\nvladServer"]
    step3["3.3 Перенос сервисов\nв exclaves"]
    step4["3.4 Full mesh\nвсе 5 машин"]

    step1 --> step2 --> step3 --> step4
  end

  phase2Result["✅ Фаза 2:\nExclave #1 работает"]
  phase2Result --> phase3

  step4 --> result3["✅ Результат:\n5 машин в mesh,\nсервисы в exclaves,\nClan управляет флотом"]
```

### 📝 Шаг 3.1 — Clan

**Чеклист:**
- [ ] `modules/clan.nix` — inventory, tags
- [ ] `clan machines list` показывает все машины
- [ ] `clan network ping` — все отвечают

### 📝 Шаг 3.2 — Личный сервер

**Чеклист:**
- [ ] `hosts/vladServer/` — hardware, disko, default
- [ ] Deploy через `deploy .#vladServer` или `nixos-rebuild`
- [ ] Сервер в mesh-сети (`10.100.0.3`)
- [ ] Сервер как WG relay для exclaves

### 📝 Шаг 3.3 — Перенос сервисов

| Сервис | Откуда | Куда | Аспект |
|:---|:---|:---|:---|
| Nextcloud | Текущий сервер | angron-exc | `aspects/exclave/services/nextcloud.nix` |
| Gitea | Текущий сервер | angron-exc | `aspects/exclave/services/gitea.nix` |
| Мониторинг | Разбросан | vladServer | `aspects/server/monitoring.nix` |
| Backup | Нет | vladServer → все | `aspects/server/backup.nix` |
| Медиа | Нет | perturabo-exc | `aspects/exclave/services/media.nix` |

**Чеклист:**
- [ ] Каждый сервис имеет свой aspect
- [ ] Данные мигрированы
- [ ] Секреты зашифрованы в sops
- [ ] Сервисы доступны через mesh DNS

### 📝 Шаг 3.4 — Full mesh

**Чеклист:**
- [ ] vladOS ↔ vladLaptop ↔ vladServer — ping работает
- [ ] vladOS ↔ angron-exc ↔ perturabo-exc — ping работает
- [ ] Все 5 машин видят друг друга
- [ ] `clan network overview` — полная карта сети
- [ ] DNS (`.mesh` домены) резолвятся

---

## 🧹 Фаза 4 — Финализация

> **Цель:** личные конфиги полностью удалены из Snowfall компании. nn3w — единственный источник правды.

```mermaid
flowchart TD
  subgraph phase4 ["🧹 Фаза 4"]
    step1["4.1 Удалить личное\nиз Snowfall"]
    step2["4.2 Полная проверка"]
    step3["4.3 Обновить\nдокументацию"]

    step1 --> step2 --> step3
  end

  phase3Result["✅ Фаза 3:\nВсе 5 машин в mesh"]
  phase3Result --> phase4

  step3 --> result4["🎉 Миграция завершена!\nnn3w = единственный\nисточник правды"]
```

### 📝 Шаг 4.1 — Удалить личное из Snowfall

**Что удалить из Snowfall-конфига компании:**

- [ ] Хост десктопа (vladOS)
- [ ] Хост ноутбука (vladLaptop)
- [ ] Пользователь vladdd183 (кроме exclave slots)
- [ ] Личные модули, overlays, packages
- [ ] Личные secrets

**Что ОСТАВИТЬ в Snowfall:**

- [ ] Exclave slots модуль (`exclave-slots.nix`)
- [ ] Конфиги серверов компании

### 📝 Шаг 4.2 — Полная проверка

```bash
# Все машины работают?
clan network ping

# Все сервисы доступны?
curl http://angron-exc.mesh:8080  # Nextcloud
curl http://angron-exc.mesh:3000  # Gitea

# Секреты расшифровываются?
ssh angron-exc.mesh 'cat /run/secrets/nextcloud-admin-password'

# Deploy работает?
deploy --dry-activate .

# Flake check?
nix flake check
```

### 📝 Шаг 4.3 — Обновить документацию

- [ ] Все docs/ актуальны
- [ ] `README.md` в корне репы
- [ ] IP-адреса и ключи задокументированы (в зашифрованном виде)

---

## 🎯 Итоговая архитектура после миграции

```mermaid
graph TB
  subgraph nn3w ["🏠 nn3w монорепа (приватная)"]
    aspects["🧩 aspects/"]
    hosts["🖥️ hosts/"]
    secrets["🔐 secrets/"]
    modules["⚙️ modules/"]
  end

  subgraph machines ["🌐 Управляемые машины"]
    desktop["🖥️ vladOS\n(десктоп)"]
    laptop["💻 vladLaptop\n(ноутбук)"]
    server["🖧 vladServer\n(личный сервер)"]
    excA["📦 angron-exc\n(exclave #1)"]
    excB["📦 perturabo-exc\n(exclave #2)"]
  end

  subgraph mesh ["🔐 WireGuard Mesh"]
    wg["10.100.0.0/24\nВсе машины связаны"]
  end

  subgraph company ["🏢 Snowfall компании"]
    snowfall["❄️ company-infra\n• Серверы компании\n• Exclave slots"]
  end

  nn3w -->|"nh os switch"| desktop
  nn3w -->|"nh os switch"| laptop
  nn3w -->|"deploy-rs"| server
  nn3w -->|"deploy-rs"| excA
  nn3w -->|"deploy-rs"| excB

  desktop <--> mesh
  laptop <--> mesh
  server <--> mesh
  excA <--> mesh
  excB <--> mesh

  snowfall -->|"microvm slots"| excA
  snowfall -->|"microvm slots"| excB
```

---

## 🔗 Связанные документы

| Документ | Тема |
|:---|:---|
| [00-architecture.md](00-architecture.md) | 🏛️ Общая архитектура (куда идём) |
| [02-den-configuration.md](02-den-configuration.md) | 🌿 Как писать Den aspects (Фаза 1) |
| [03-exclave-mechanism.md](03-exclave-mechanism.md) | 📦 Exclave slot для компании (Фаза 2) |
| [04-networking.md](04-networking.md) | 🌐 WireGuard mesh настройка (Фаза 2-3) |
| [05-secrets.md](05-secrets.md) | 🔐 sops-nix настройка (Фаза 2) |
| [06-deployment.md](06-deployment.md) | 🚀 deploy-rs настройка (Фаза 2) |
