# 🌐 Networking — Clan Mesh, WireGuard, Trust Domains

> Все личные машины (десктоп, ноут, сервер) + exclaves на серверах компании
> объединены в единую зашифрованную mesh-сеть. Clan управляет сетью декларативно.
> Компания видит зашифрованный WireGuard трафик, но не содержимое.

---

## 🗺️ Топология сети

```mermaid
graph TB
  subgraph personalMesh ["🔒 Личная Mesh-сеть (WireGuard)"]
    desktop["🖥️ vladOS\nДесктоп\n10.100.0.1"]
    laptop["💻 vladLaptop\nНоутбук\n10.100.0.2"]
    server["🖧 vladServer\nЛичный сервер\n10.100.0.3"]
  end

  subgraph companyA ["🏢 Сеть компании — Сервер #1 (angron)"]
    hostA["🖧 angron\n(Snowfall host)"]
    excA["📦 angron-exc\nExclave VM\n10.100.0.10"]
  end

  subgraph companyB ["🏢 Сеть компании — Сервер #2 (perturabo)"]
    hostB["🖧 perturabo\n(Snowfall host)"]
    excB["📦 perturabo-exc\nExclave VM\n10.100.0.11"]
  end

  desktop <-->|"WG mesh"| laptop
  desktop <-->|"WG mesh"| server
  laptop <-->|"WG mesh"| server

  desktop <-->|"WG tunnel\nчерез компанейскую\nсеть"| excA
  desktop <-->|"WG tunnel"| excB
  server <-->|"WG mesh"| excA
  server <-->|"WG mesh"| excB
  excA <-->|"WG mesh"| excB

  hostA -->|"TAP bridge"| excA
  hostB -->|"TAP bridge"| excB
```

---

## 🔌 Как Clan управляет сетью

### Clan = декларативный fleet manager без центрального контроллера

```mermaid
flowchart TD
  subgraph clanConfig ["📋 Clan конфигурация в nn3w"]
    inventory["clan.inventory\nмашины, роли, теги"]
    networking["clan.networking\nmesh VPN, fallback"]
    vars["clan.vars\nсекреты, ключи WG"]
  end

  subgraph machines ["🖥️ Машины"]
    vladOS["vladOS\ntag: workstation"]
    vladLaptop["vladLaptop\ntag: workstation"]
    vladServer["vladServer\ntag: server"]
    angronExc["angron-exc\ntag: exclave"]
    perturaboExc["perturabo-exc\ntag: exclave"]
  end

  subgraph operations ["⚡ Операции"]
    list["clan network list\nПоказать все машины"]
    ping["clan network ping\nПроверить связность"]
    overview["clan network overview\nКарта сети"]
    update["clan machines update\nОбновить все"]
  end

  clanConfig --> machines
  machines --> operations
```

### modules/clan.nix

```nix
# modules/clan.nix
{ inputs, ... }:
{
  imports = [ inputs.clan-core.flakeModules.default ];

  clan = {
    meta.name = "nn3w-fleet";

    # Инвентарь машин
    inventory = {
      machines = {
        vladOS = {
          tags = [ "workstation" "desktop" ];
          description = "Основной десктоп";
        };
        vladLaptop = {
          tags = [ "workstation" "laptop" ];
          description = "Ноутбук";
        };
        vladServer = {
          tags = [ "server" "personal" ];
          description = "Личный сервер";
        };
        angron-exc = {
          tags = [ "exclave" "server" ];
          description = "Exclave на сервере компании #1";
        };
        perturabo-exc = {
          tags = [ "exclave" "server" ];
          description = "Exclave на сервере компании #2";
        };
      };

      # Сервисы применяются по тегам
      services = {
        borgbackup.default = {
          roles.server.machines = [ "vladServer" ];
          roles.client.tags = [ "workstation" "exclave" ];
        };
      };
    };
  };
}
```

---

## 🔐 WireGuard Mesh — Конфигурация

### Как устроена mesh-сеть

```mermaid
graph LR
  subgraph wgMesh ["🔐 WireGuard Mesh (full mesh)"]
    direction LR
    A["vladOS\n10.100.0.1\npublic: дом IP"]
    B["vladLaptop\n10.100.0.2\npublic: мобильный"]
    C["vladServer\n10.100.0.3\npublic: VPS IP"]
    D["angron-exc\n10.100.0.10\npublic: через TAP → компания"]
    E["perturabo-exc\n10.100.0.11\npublic: через TAP → компания"]
  end

  A <--> B
  A <--> C
  A <--> D
  A <--> E
  B <--> C
  B <--> D
  B <--> E
  C <--> D
  C <--> E
  D <--> E
```

### 📋 Адресация

| Машина | WG IP | Публичный endpoint | Роль |
|:---|:---|:---|:---|
| vladOS | `10.100.0.1/24` | `home.dyn.ip:51820` | Десктоп |
| vladLaptop | `10.100.0.2/24` | Roaming (мобильный) | Ноутбук |
| vladServer | `10.100.0.3/24` | `vps.static.ip:51820` | Личный сервер, relay |
| angron-exc | `10.100.0.10/24` | Через TAP → NAT компании | Exclave #1 |
| perturabo-exc | `10.100.0.11/24` | Через TAP → NAT компании | Exclave #2 |

### WireGuard aspect

```nix
# aspects/exclave/wireguard.nix
{ ... }:
{
  den.aspects.exclave-wireguard = {
    nixos = { config, ... }: {
      networking.wireguard.interfaces.wg-mesh = {
        # Порт для WG
        listenPort = 51820;

        # Приватный ключ из sops-nix
        privateKeyFile = config.sops.secrets."wireguard/private-key".path;

        peers = [
          {
            # vladOS (десктоп)
            publicKey = "DESKTOP_PUBLIC_KEY_HERE";
            allowedIPs = [ "10.100.0.1/32" ];
            endpoint = "home.dyn.ip:51820";
            persistentKeepalive = 25;
          }
          {
            # vladServer (relay)
            publicKey = "SERVER_PUBLIC_KEY_HERE";
            allowedIPs = [ "10.100.0.0/24" ];
            endpoint = "vps.static.ip:51820";
            persistentKeepalive = 25;
          }
        ];
      };
    };
  };
}
```

---

## 🔄 Clan Networking — Автоматический Fallback

Clan поддерживает автоматический fallback между типами подключения:

```mermaid
flowchart TD
  connect["🔌 Подключение к машине"]

  connect -->|"Приоритет 1"| direct["🌐 Прямое подключение\n(LAN / публичный IP)"]
  direct -->|"Недоступен"| wg["🔐 WireGuard mesh\n(через relay)"]
  wg -->|"Недоступен"| zerotier["🌐 ZeroTier\n(fallback VPN)"]
  zerotier -->|"Недоступен"| tor["🧅 Tor\n(hidden service)"]

  direct -->|"✅"| connected["✅ Подключено"]
  wg -->|"✅"| connected
  zerotier -->|"✅"| connected
  tor -->|"✅"| connected
```

### Конфигурация Clan networking

```nix
# В clan.nix или отдельном модуле
clan.networking = {
  # Основной VPN
  wireguard = {
    enable = true;
    # Ключи управляются через clan vars
  };

  # Fallback — ZeroTier (опционально)
  zerotier = {
    enable = false; # Включить при необходимости
    networkId = "YOUR_ZEROTIER_NETWORK_ID";
  };
};
```

---

## 🌐 Как Exclaves подключаются к сети

### Проблема: exclave за NAT компании

```mermaid
sequenceDiagram
  participant Desktop as 🖥️ vladOS<br/>(домашняя сеть)
  participant Internet as 🌐 Интернет
  participant CompanyNAT as 🏢 NAT компании
  participant Host as 🖧 Сервер компании
  participant Exclave as 📦 Exclave VM

  Note over Desktop,Exclave: Прямое подключение невозможно — Exclave за NAT

  Desktop->>Internet: WG пакет → vladServer (relay)
  Internet->>CompanyNAT: WG пакет → TAP bridge
  CompanyNAT->>Host: Проброс порта 51820
  Host->>Exclave: TAP → wg-mesh interface

  Note over Desktop,Exclave: Решение: vladServer как relay (hub-and-spoke)
```

### Решение: Hub-and-Spoke через vladServer

```mermaid
graph TB
  subgraph spoke1 ["🏠 Домашняя сеть"]
    desktop["🖥️ vladOS"]
    laptop["💻 vladLaptop"]
  end

  subgraph hub ["☁️ VPS (публичный IP)"]
    server["🖧 vladServer\n(relay/hub)\nvps.static.ip:51820"]
  end

  subgraph spoke2 ["🏢 Сеть компании (за NAT)"]
    excA["📦 angron-exc"]
    excB["📦 perturabo-exc"]
  end

  desktop -->|"WG"| server
  laptop -->|"WG"| server
  excA -->|"WG keepalive\n(пробивает NAT)"| server
  excB -->|"WG keepalive\n(пробивает NAT)"| server

  server -->|"route"| desktop
  server -->|"route"| laptop
  server -->|"route"| excA
  server -->|"route"| excB
```

**vladServer** — единственная машина с публичным IP. Все остальные подключаются к нему. Он маршрутизирует трафик между участниками mesh.

Exclaves используют `persistentKeepalive = 25` чтобы держать NAT-пробив живым.

---

## 🏷️ Trust Domains в сети

| Trust Domain | Машины | Видимость | Секреты |
|:---|:---|:---|:---|
| 🔒 **Personal** | vladOS, vladLaptop, vladServer | Полная видимость друг друга | Личные age-ключи |
| 📦 **Exclave** | angron-exc, perturabo-exc | Видят personal mesh | Exclave-специфичные ключи |
| 🏢 **Company** | angron, perturabo (hosts) | Видят только VM + трафик | Компанейские ключи |

```mermaid
graph TB
  subgraph personalTrust ["🔒 Personal Trust Domain"]
    desktop["vladOS"]
    laptop["vladLaptop"]
    server["vladServer"]
  end

  subgraph exclaveTrust ["📦 Exclave Trust Domain"]
    excA["angron-exc"]
    excB["perturabo-exc"]
  end

  subgraph companyTrust ["🏢 Company Trust Domain"]
    hostA["angron (host)"]
    hostB["perturabo (host)"]
  end

  personalTrust <-->|"🔐 WG mesh\nполный доступ"| exclaveTrust
  exclaveTrust ---|"🔐 WG encrypted\nкомпания видит\nтолько шифр. пакеты"| companyTrust
```

---

## 📋 DNS внутри mesh

| Домен | Резолвится в | Пример |
|:---|:---|:---|
| `vladOS.mesh` | `10.100.0.1` | `ssh vladOS.mesh` |
| `vladLaptop.mesh` | `10.100.0.2` | `ssh vladLaptop.mesh` |
| `vladServer.mesh` | `10.100.0.3` | `ssh vladServer.mesh` |
| `angron-exc.mesh` | `10.100.0.10` | `curl http://angron-exc.mesh:8080` |
| `perturabo-exc.mesh` | `10.100.0.11` | `curl http://perturabo-exc.mesh:8080` |

Реализация через CoreDNS или `/etc/hosts` (Clan генерирует автоматически).

---

## 🔗 Связанные документы

| Документ | Тема |
|:---|:---|
| [03-exclave-mechanism.md](03-exclave-mechanism.md) | 📦 Exclave TAP interface, MicroVM networking |
| [05-secrets.md](05-secrets.md) | 🔐 WireGuard ключи в sops-nix |
| [06-deployment.md](06-deployment.md) | 🚀 Деплой через mesh-сеть |
