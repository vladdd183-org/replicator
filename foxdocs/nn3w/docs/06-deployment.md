# 🚀 Deployment — Стратегии деплоя для разных типов машин

> Разные машины обновляются по-разному: десктоп — локальным rebuild,
> exclaves — через deploy-rs по WireGuard, флот — через Clan.
> Каждая стратегия оптимизирована под свой сценарий.

---

## 🗺️ Карта стратегий деплоя

```mermaid
flowchart TD
  subgraph machine ["🤔 Какую машину обновляем?"]
    desktop["🖥️ Десктоп / Ноутбук\n(локальная машина)"]
    server["🖧 Личный сервер\n(удалённый, полный контроль)"]
    exclave["📦 Exclave\n(VM на сервере компании)"]
    nspawn["📦 L0 nspawn Exclave\n(контейнер на сервере компании)"]
    fleet["🌐 Весь флот\n(все машины разом)"]
  end

  desktop -->|"nh os switch"| nhStrategy["⚡ nh CLI\nБыстрый локальный rebuild"]
  server -->|"deploy-rs"| deployStrategy["🚀 deploy-rs\nRemote deploy + rollback"]
  exclave -->|"deploy-rs через WG"| exclaveStrategy["🔐 deploy-rs\nЧерез WireGuard mesh"]
  nspawn -->|"nix build + nix copy"| nspawnStrategy["🔒 Приватный деплой\nnix build локально → nix copy → systemd-run -M"]
  fleet -->|"clan machines update"| clanStrategy["🌐 Clan\nFleet-wide update"]
```

---

## ⚡ Стратегия 1: Локальный rebuild (десктоп/ноутбук)

### Когда использовать

Ты сидишь за машиной, внёс изменения в монорепу, хочешь применить.

### Команды

```bash
# Стандартный NixOS rebuild
sudo nixos-rebuild switch --flake .#vladOS

# Или через nh (быстрее, красивее)
nh os switch . -- --hostname vladOS

# Только Home Manager (без перестроения системы)
nh home switch . -- --configuration vladdd183
```

### Как это работает

```mermaid
sequenceDiagram
  participant Dev as 👨‍💻 Ты
  participant Repo as 📦 nn3w/
  participant Nix as ❄️ Nix
  participant System as 🐧 NixOS

  Dev->>Repo: git commit (изменения)
  Dev->>Nix: nh os switch .
  Nix->>Nix: Evaluates flake<br/>Den pipeline<br/>→ nixosConfigurations.vladOS
  Nix->>Nix: Builds closure
  Nix->>System: Активирует новую конфигурацию
  System->>System: switch-to-configuration
  Note over System: Новый конфиг активен!<br/>Предыдущий в GRUB для отката
```

---

## 🚀 Стратегия 2: deploy-rs (удалённые машины)

### Когда использовать

Обновление личного сервера или exclave — удалённо, через SSH.

### Конфигурация deploy-rs

```nix
# modules/deploy.nix
{ inputs, ... }:
{
  imports = [ inputs.deploy-rs.flakeModule ];

  # Личный сервер
  deploy.nodes.vladServer = {
    hostname = "vladServer.mesh";    # через WG mesh
    sshUser = "root";
    fastConnection = true;           # сервер мощный

    profiles.system = {
      path = inputs.deploy-rs.lib.x86_64-linux.activate.nixos
        inputs.self.nixosConfigurations.vladServer;
    };
  };

  # Exclave #1
  deploy.nodes.angron-exc = {
    hostname = "angron-exc.mesh";    # через WG mesh
    sshUser = "root";
    fastConnection = false;          # через VPN, медленнее

    profiles.system = {
      path = inputs.deploy-rs.lib.x86_64-linux.activate.nixos
        inputs.self.nixosConfigurations.angron-exc;
      # Magic rollback — если SSH теряется после деплоя,
      # автоматически откатывает через 60 сек
      autoRollback = true;
      magicRollback = true;
    };
  };

  # Exclave #2
  deploy.nodes.perturabo-exc = {
    hostname = "perturabo-exc.mesh";
    sshUser = "root";
    fastConnection = false;

    profiles.system = {
      path = inputs.deploy-rs.lib.x86_64-linux.activate.nixos
        inputs.self.nixosConfigurations.perturabo-exc;
      autoRollback = true;
      magicRollback = true;
    };
  };
}
```

### Команды deploy-rs

```bash
# Деплой на конкретную машину
deploy .#vladServer
deploy .#angron-exc
deploy .#perturabo-exc

# L0 nspawn exclave — приватный деплой (см. секцию ниже)
# Используется nix build + nix copy + systemd-run -M
# вместо deploy-rs CLI, чтобы исходники не попадали на хост.

# Деплой на все ноды
deploy .

# Dry-run (только проверка, без изменений)
deploy --dry-activate .#angron-exc

# Без rollback (для отладки)
deploy --auto-rollback false .#angron-exc
```

### Приватный деплой L0 nspawn: `vladdd183-stage`

`vladdd183-stage` — `systemd-nspawn` guest на `perturabo`. Сборка происходит
**локально**, на хост копируются **только скомпилированные store paths** —
исходники nn3w на сервер компании не попадают.

```bash
# 1. Собрать closure ЛОКАЛЬНО
STORE_PATH=$(nix build \
  .#nixosConfigurations.vladdd183-stage.config.system.build.toplevel \
  --print-out-paths --no-link)

# 2. Скопировать только store paths на хост (не исходники!)
#    nspawn контейнер разделяет Nix store с хостом,
#    поэтому пути сразу доступны внутри guest.
NIX_SSHOPTS="-o ServerAliveInterval=30 -o ServerAliveCountMax=10" \
  nix copy --to ssh://kubeadmin@95.165.111.66 "$STORE_PATH"

# 3. Активировать внутри контейнера через systemd-run -M
ssh kubeadmin@95.165.111.66 \
  "sudo systemd-run -M vladdd183-stage --wait --pipe --service-type=exec \
   ${STORE_PATH}/bin/switch-to-configuration test"
ssh kubeadmin@95.165.111.66 \
  "sudo systemd-run -M vladdd183-stage --wait --pipe --service-type=exec \
   ${STORE_PATH}/bin/switch-to-configuration switch"

# 4. Smoke-test
curl -sk --resolve "stage.xn--80adh0ars.xn--j1adp.xn--p1acf:443:95.165.111.66" \
  "https://stage.xn--80adh0ars.xn--j1adp.xn--p1acf/"
```

> **Почему не rsync + build на хосте?** Старый runbook копировал **всю nn3w**
> на хост компании через `rsync`, что раскрывало приватные конфиги.
> Новый flow: `nix build` локально → `nix copy` store paths → `systemd-run -M`.
> Хост видит только скомпилированные `/nix/store/...`, не исходный Nix-код.
>
> **Почему не deploy-rs CLI?** deploy-rs CLI (`serokell/deploy-rs`) на текущем
> nixpkgs не собирается из-за `libkeyutils.so.1`. Ручной flow эквивалентен
> по результату и не требует сборки самого deploy-rs.
>
> **Нюансы nspawn guest:**
> - Внутри `vladdd183-stage` обязательно `networking.useDHCP = false` и
>   `networking.dhcpcd.enable = false` — адрес задаёт host-side slot.
> - Для smoke-test используется `Caddy tls internal`, поэтому внешний
>   `curl` должен идти с `-sk`, пока не подключён публичный ACME.

#### Что видит хост компании

| Компонент | Видит хост? |
|-----------|-------------|
| Исходный Nix-код nn3w | **Нет** — сборка локальная |
| Store paths (`/nix/store/...`) | Да — shared Nix store |
| Секреты sops | **Нет** — зашифрованы age-ключами |
| SSH-трафик внутрь guest | Зашифрован (ProxyJump) |

### Magic Rollback — защита от поломок

```mermaid
sequenceDiagram
  participant Dev as 👨‍💻 Ты
  participant DeployRS as 🚀 deploy-rs
  participant Exclave as 📦 Exclave VM

  Dev->>DeployRS: deploy .#angron-exc
  DeployRS->>Exclave: SSH: копирует closure
  DeployRS->>Exclave: SSH: activate-new-config
  Exclave->>Exclave: Активирует новый конфиг

  alt Конфиг рабочий
    DeployRS->>Exclave: SSH: подтверждение (confirm)
    Exclave->>Exclave: Закрепляет новый конфиг
    Note over Exclave: ✅ Успешный деплой
  else SSH потерялся (конфиг сломал сеть)
    Note over DeployRS: ⏰ Таймаут 60 сек<br/>без подтверждения
    Exclave->>Exclave: Автоматический откат<br/>к предыдущему конфигу
    Note over Exclave: 🔄 Откат выполнен!
  end
```

> **Magic rollback** критически важен для exclaves — если деплой сломает WireGuard, ты потеряешь SSH-доступ. Rollback автоматически вернёт рабочий конфиг через 60 секунд.

---

## 🌐 Стратегия 3: Clan fleet update (весь флот)

### Когда использовать

Обновление всех машин одной командой. Полезно после `nix flake update`.

### Команды Clan

```bash
# Обновить все машины
clan machines update

# Обновить по тегу
clan machines update --tag workstation
clan machines update --tag exclave
clan machines update --tag server

# Обновить конкретную
clan machines update vladServer

# Проверить статус всех
clan machines list
clan network ping
clan network overview
```

### Как работает fleet update

```mermaid
sequenceDiagram
  participant Dev as 👨‍💻 Ты
  participant Clan as 🌐 Clan CLI
  participant VladOS as 🖥️ vladOS
  participant Server as 🖧 vladServer
  participant AngronExc as 📦 angron-exc
  participant PerturaboExc as 📦 perturabo-exc

  Dev->>Clan: clan machines update

  par Параллельное обновление
    Clan->>VladOS: SSH → nixos-rebuild
    Clan->>Server: SSH → nixos-rebuild
    Clan->>AngronExc: SSH (через WG) → nixos-rebuild
    Clan->>PerturaboExc: SSH (через WG) → nixos-rebuild
  end

  VladOS-->>Clan: ✅ Обновлено
  Server-->>Clan: ✅ Обновлено
  AngronExc-->>Clan: ✅ Обновлено
  PerturaboExc-->>Clan: ✅ Обновлено

  Clan-->>Dev: 🎉 Все 4 машины обновлены
```

---

## 📋 Сравнение стратегий

| Параметр | nh os switch | deploy-rs | nix build + copy | Clan update |
|:---|:---:|:---:|:---:|:---:|
| **Целевые машины** | Локальная | Одна удалённая | L0 nspawn exclave | Весь флот |
| **Транспорт** | Локально | SSH | SSH (nix copy) | SSH |
| **Сборка** | Локально | Локально | Локально | Удалённо |
| **Приватность** | — | Store paths | ✅ Store paths only | — |
| **Rollback** | GRUB (вручную) | ✅ Magic rollback | ❌ (вручную) | ❌ (вручную) |
| **Параллельность** | — | Одна за раз | Одна за раз | ✅ Параллельно |
| **Скорость** | ⚡ Быстро | 🚀 Средне | 🚀 Средне | 🌐 Зависит от кол-ва |
| **Идеально для** | Десктоп | Exclaves (VM) | nspawn Exclaves | Обновление nixpkgs |

---

## 🔄 Workflow: типичный день

```mermaid
flowchart TD
  start["👨‍💻 Утро: внёс изменения\nв nn3w монорепу"]

  start --> commit["git add && git commit"]

  commit --> whatChanged{"Что изменилось?"}

  whatChanged -->|"Desktop аспекты\n(hyprland, audio)"| localRebuild["⚡ nh os switch .\nЛокальный rebuild"]

  whatChanged -->|"Exclave сервисы\n(nextcloud, gitea)"| deployExclave["🚀 deploy .#angron-exc\nRemote deploy"]

  whatChanged -->|"nspawn stage конфиг\n(caddy, workspace)"| deployNspawn["🔒 nix build + nix copy\nПриватный деплой stage"]

  whatChanged -->|"nixpkgs обновление\n(flake update)"| fleetUpdate["🌐 clan machines update\nВсе машины"]

  whatChanged -->|"Server конфиг\n(monitoring, backup)"| deployServer["🚀 deploy .#vladServer\nRemote deploy"]

  localRebuild --> done["✅ Готово"]
  deployExclave --> done
  deployNspawn --> done
  fleetUpdate --> done
  deployServer --> done
```

---

## 🛡️ Безопасность деплоя

### SSH-ключи

```nix
# Каждая машина принимает SSH только с определённых ключей
den.aspects.ssh-server = {
  nixos = { ... }: {
    services.openssh = {
      enable = true;
      settings = {
        PasswordAuthentication = false;
        PermitRootLogin = "prohibit-password";
        KbdInteractiveAuthentication = false;
      };
    };

    # Только твой ключ может подключиться
    users.users.root.openssh.authorizedKeys.keys = [
      "ssh-ed25519 AAAA... vladdd183@vladOS"
    ];
  };
};
```

### Deploy через WireGuard

Весь трафик deploy-rs идёт через WireGuard mesh, даже SSH:

```
vladOS (10.100.0.1) → WG tunnel → angron-exc (10.100.0.10):22
```

Компания видит только зашифрованные WireGuard пакеты, не SSH-сессию.

---

## 🔗 Связанные документы

| Документ | Тема |
|:---|:---|
| [03-exclave-mechanism.md](03-exclave-mechanism.md) | 📦 Как устроен exclave (куда деплоим) |
| [04-networking.md](04-networking.md) | 🌐 WireGuard mesh (через что деплоим) |
| [05-secrets.md](05-secrets.md) | 🔐 Секреты, доставляемые при деплое |
| [07-roadmap.md](07-roadmap.md) | 📋 Порядок настройки деплоя |
