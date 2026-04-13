# 🔐 Секреты — sops-nix, мульти-ключи, Trust Isolation

> Все секреты (пароли, SSH-ключи, WireGuard ключи, API-токены) хранятся
> зашифрованными в git через sops-nix. Каждый trust domain имеет свои ключи.
> Exclave-секреты **никогда** не шифруются ключами компании.

---

## 🧭 Модель секретов

```mermaid
flowchart TD
  subgraph sopsFiles ["📁 secrets/ (зашифровано в git)"]
    personalCommon["🔑 personal/common.yaml\nAPI keys, tokens, пароли"]
    personalWG["🔑 personal/wireguard.yaml\nWG private keys всех машин"]
    exclaveAngron["🔑 exclaves/angron.yaml\nСекреты для exclave #1"]
    exclavePerturabo["🔑 exclaves/perturabo.yaml\nСекреты для exclave #2"]
  end

  subgraph keys ["🔐 Ключи шифрования"]
    personalKey["👤 Личный age-ключ\n(vladdd183)"]
    vladOSKey["🖥️ vladOS host key\n(из SSH)"]
    laptopKey["💻 vladLaptop host key"]
    serverKey["🖧 vladServer host key"]
    angronExcKey["📦 angron-exc VM key"]
    perturaboExcKey["📦 perturabo-exc VM key"]
  end

  personalKey -->|"шифрует"| personalCommon
  personalKey -->|"шифрует"| personalWG
  vladOSKey -->|"шифрует"| personalCommon
  laptopKey -->|"шифрует"| personalCommon
  serverKey -->|"шифрует"| personalCommon
  serverKey -->|"шифрует"| personalWG

  personalKey -->|"шифрует"| exclaveAngron
  angronExcKey -->|"шифрует"| exclaveAngron

  personalKey -->|"шифрует"| exclavePerturabo
  perturaboExcKey -->|"шифрует"| exclavePerturabo
```

---

## 🔑 Типы ключей

| Тип ключа | Откуда берётся | Для чего | Кто имеет доступ |
|:---|:---|:---|:---|
| 👤 **Личный age-ключ** | Генерируешь сам (`age-keygen`) | Мастер-ключ для всех секретов | Только ты |
| 🖥️ **Host SSH-ключ** | `/etc/ssh/ssh_host_ed25519_key` | Расшифровка секретов на конкретном хосте | Конкретная машина |
| 📦 **Exclave VM-ключ** | Генерируется при создании VM | Расшифровка exclave-секретов | Конкретный exclave |

### Как ключи связаны

```mermaid
graph TB
  subgraph master ["👤 Мастер-ключ (age)"]
    personalAge["age1...\n(хранится на десктопе\nи в бэкапе)"]
  end

  subgraph hostKeys ["🖥️ Host-ключи (из SSH → age)"]
    vladOSAge["vladOS\nssh-to-age → age1..."]
    laptopAge["vladLaptop\nssh-to-age → age1..."]
    serverAge["vladServer\nssh-to-age → age1..."]
  end

  subgraph exclaveKeys ["📦 Exclave-ключи (age)"]
    angronAge["angron-exc\nage-keygen → age1..."]
    perturaboAge["perturabo-exc\nage-keygen → age1..."]
  end

  personalAge -->|"может расшифровать ВСЁ"| allSecrets["Все секреты"]
  vladOSAge -->|"может расшифровать"| personalSecrets["personal/*.yaml"]
  laptopAge -->|"может расшифровать"| personalSecrets
  serverAge -->|"может расшифровать"| personalSecrets
  angronAge -->|"может расшифровать\nТОЛЬКО"| angronSecrets["exclaves/angron.yaml"]
  perturaboAge -->|"может расшифровать\nТОЛЬКО"| perturaboSecrets["exclaves/perturabo.yaml"]
```

---

## 📋 Конфигурация .sops.yaml

```yaml
# .sops.yaml — правила шифрования по путям файлов
keys:
  # 👤 Личный мастер-ключ (может расшифровать всё)
  - &personal age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

  # 🖥️ Host-ключи (из SSH: ssh-to-age -i /etc/ssh/ssh_host_ed25519_key.pub)
  - &vladOS    age1aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
  - &vladLaptop age1bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  - &vladServer age1cccccccccccccccccccccccccccccccccccccccccccccccccccccccc

  # 📦 Exclave VM-ключи
  - &angron-exc    age1dddddddddddddddddddddddddddddddddddddddddddddddddd
  - &perturabo-exc age1eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee

creation_rules:
  # 🔐 Personal secrets — доступны на всех ЛИЧНЫХ машинах
  - path_regex: secrets/personal/.*\.yaml$
    key_groups:
      - age:
          - *personal      # мастер-ключ
          - *vladOS         # десктоп
          - *vladLaptop     # ноутбук
          - *vladServer     # личный сервер

  # 📦 Exclave #1 — только мастер-ключ + exclave
  - path_regex: secrets/exclaves/angron\.yaml$
    key_groups:
      - age:
          - *personal       # мастер-ключ (для редактирования)
          - *angron-exc     # VM (для расшифровки на месте)

  # 📦 Exclave #2 — только мастер-ключ + exclave
  - path_regex: secrets/exclaves/perturabo\.yaml$
    key_groups:
      - age:
          - *personal
          - *perturabo-exc
```

---

## 🔒 Критическое правило: Trust Isolation

```mermaid
graph TB
  subgraph rule ["⚠️ ПРАВИЛО"]
    text["Exclave-секреты НИКОГДА\nне шифруются ключами компании"]
  end

  subgraph correct ["✅ Правильно"]
    good["exclaves/angron.yaml\nЗашифрован:\n• personal age-key\n• angron-exc VM key"]
  end

  subgraph wrong ["❌ Неправильно"]
    bad["exclaves/angron.yaml\nЗашифрован:\n• personal age-key\n• angron HOST key\n(компанейский!)"]
  end

  rule --> correct
  rule --> wrong
```

**Почему это важно:**

- Host SSH-ключ сервера компании (`angron`) доступен админам компании
- Если зашифровать exclave-секрет этим ключом, компания сможет его расшифровать
- Exclave VM-ключ генерируется внутри VM, которой управляешь только ты
- Мастер-ключ нужен для редактирования секретов с десктопа

---

## 📂 Содержимое файлов секретов

### secrets/personal/common.yaml

```yaml
# Зашифровано sops (age) — здесь показано для примера
github-token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
cachix-auth-token: eyJhbGci...
smtp-password: my-secure-password
backup-encryption-key: borg-encryption-passphrase
```

### secrets/personal/wireguard.yaml

```yaml
# WireGuard приватные ключи для каждой машины
vladOS-private-key: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
vladLaptop-private-key: BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=
vladServer-private-key: CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=
angron-exc-private-key: DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD=
perturabo-exc-private-key: EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE=
```

### secrets/exclaves/angron.yaml

```yaml
# Секреты ТОЛЬКО для exclave angron-exc
nextcloud-admin-password: super-secure-password
nextcloud-db-password: postgres-password
gitea-db-password: gitea-pg-password
gitea-secret-key: xxxxxxxxxxxxxxxxxxxxxxx
```

---

## ⚙️ sops-nix в NixOS конфигурации

### Подключение sops-nix

```nix
# В modules/den.nix или отдельном модуле
{ inputs, ... }:
{
  imports = [ inputs.sops-nix.nixosModules.sops ];
}
```

### Использование секретов в аспектах

```nix
# aspects/exclave/services/nextcloud.nix
{ ... }:
{
  den.aspects.nextcloud = {
    nixos = { config, ... }: {
      # Объявляем секреты
      sops.secrets."nextcloud-admin-password" = {
        sopsFile = ../../../secrets/exclaves/angron.yaml;
        owner = "nextcloud";
      };
      sops.secrets."nextcloud-db-password" = {
        sopsFile = ../../../secrets/exclaves/angron.yaml;
        owner = "nextcloud";
      };

      # Используем секреты
      services.nextcloud = {
        enable = true;
        hostName = "cloud.angron-exc.mesh";
        config = {
          adminpassFile = config.sops.secrets."nextcloud-admin-password".path;
          dbpassFile = config.sops.secrets."nextcloud-db-password".path;
        };
      };
    };
  };
}
```

### Использование WireGuard ключей

```nix
# aspects/exclave/wireguard.nix
{ ... }:
{
  den.aspects.exclave-wireguard = {
    nixos = { config, ... }: {
      sops.secrets."wireguard/private-key" = {
        sopsFile = ../../secrets/personal/wireguard.yaml;
        # sops-nix подставит правильный ключ
        # по имени хоста (angron-exc-private-key)
      };

      networking.wireguard.interfaces.wg-mesh = {
        privateKeyFile = config.sops.secrets."wireguard/private-key".path;
        # ...
      };
    };
  };
}
```

---

## 🔄 Workflow: управление секретами

```mermaid
sequenceDiagram
  participant Dev as 👨‍💻 Разработчик<br/>(десктоп)
  participant Sops as 🔐 sops CLI
  participant Git as 📦 Git repo
  participant DeployRS as 🚀 deploy-rs
  participant Exclave as 📦 Exclave VM

  Note over Dev: Создание нового секрета
  Dev->>Sops: sops secrets/exclaves/angron.yaml
  Note over Sops: Открывает $EDITOR<br/>Показывает расшифрованный YAML
  Dev->>Sops: Добавляет новый секрет
  Sops->>Git: Сохраняет зашифрованный файл

  Note over Dev: Деплой
  Dev->>Git: git commit && git push
  Dev->>DeployRS: deploy .#angron-exc
  DeployRS->>Exclave: Копирует конфигурацию
  Exclave->>Exclave: sops-nix расшифровывает<br/>через age-key VM
  Note over Exclave: Секреты доступны в<br/>/run/secrets/*
```

### 📋 Команды

```bash
# Создать/редактировать секреты (на десктопе с мастер-ключом)
sops secrets/personal/common.yaml
sops secrets/exclaves/angron.yaml

# Получить age-ключ хоста из SSH
ssh-to-age -i /etc/ssh/ssh_host_ed25519_key.pub

# Сгенерировать новый age-ключ для exclave
age-keygen -o /tmp/exclave-key.txt

# Ротация ключей (пересоздание с новыми ключами)
sops updatekeys secrets/exclaves/angron.yaml
```

---

## 📊 Матрица доступа к секретам

| Секретный файл | 👤 Мастер | 🖥️ vladOS | 💻 Laptop | 🖧 Server | 📦 angron-exc | 📦 perturabo-exc | 🏢 Компания |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| personal/common.yaml | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| personal/wireguard.yaml | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| exclaves/angron.yaml | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| exclaves/perturabo.yaml | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

> **Компания никогда не имеет доступа** ни к одному секрету. Даже если админ прочитает `.sops.yaml` — у него нет age-ключей.

---

## 🔗 Связанные документы

| Документ | Тема |
|:---|:---|
| [03-exclave-mechanism.md](03-exclave-mechanism.md) | 📦 LUKS шифрование диска exclave |
| [04-networking.md](04-networking.md) | 🌐 WireGuard ключи в mesh-сети |
| [06-deployment.md](06-deployment.md) | 🚀 Как deploy-rs доставляет секреты |
