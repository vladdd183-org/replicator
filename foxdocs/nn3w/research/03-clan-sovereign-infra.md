# 🏰 Clan — Суверенная P2P-инфраструктура

> **Версия:** 25.11 (первый стабильный релиз)
> **Команда:** clan-lol (Lassulus — казначей NixOS Foundation)
> **Репо:** git.clan.lol/clan/clan-core | **Доки:** docs.clan.lol
> **Спонсор:** Golem Network (децентрализованные вычисления)
> **Философия:** "Sovereign Infrastructure by Design"

---

## 🧠 Что такое Clan на самом деле

Clan — НЕ просто конфигурационный фреймворк (как Den или Snowfall).
Clan — это **платформа управления флотом машин** без центрального контроллера.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLAN                                     │
│                                                                  │
│   ┌─────────┐    mesh VPN     ┌─────────┐    mesh VPN          │
│   │ Machine │◄───────────────►│ Machine │◄──────────►...       │
│   │   A     │                 │   B     │                       │
│   └────┬────┘                 └────┬────┘                       │
│        │                           │                             │
│        │  Clan CLI / GUI           │  Clan CLI / GUI            │
│        │                           │                             │
│   ┌────▼────┐                 ┌────▼────┐                       │
│   │ NixOS   │                 │ NixOS/  │                       │
│   │ Config  │                 │ macOS   │                       │
│   │ (flake) │                 │ Config  │                       │
│   └─────────┘                 └─────────┘                       │
│                                                                  │
│   🔑 Secrets (sops-nix, vars)                                   │
│   🌐 Networking (ZeroTier, Tor, overlay networks)               │
│   💾 Backups (declarative)                                      │
│   📦 Services (inventory-based, cross-machine)                  │
│   🖥️ GUI (GTK, визуализация инфраструктуры)                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Архитектура Clan

### Inventory — от машин к инфраструктуре

```nix
inventory.instances = {
  -- Одна декларация включает VPN на ВСЕХ машинах
  zerotier = {
    roles.controller.machines.server = { };
    roles.peer.tags = [ "all" ];
  };

  -- Мониторинг
  monitoring = {
    roles.server.machines.server = { };
    roles.client.tags = [ "all" ];
  };

  -- Бэкапы
  borgbackup = {
    roles.server.machines.backup-server = { };
    roles.client.tags = [ "workstations" ];
  };
};
```

### Networking — мультисетевая абстракция

```
┌──────────────────────────────────────────────────────────┐
│                   Clan Networking Layer                    │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ ZeroTier │  │   Tor    │  │ Mycelium │  │ Custom  │ │
│  │   VPN    │  │ Onion    │  │  (mesh)  │  │ Overlay │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │             │              │      │
│       └──────────┬───┴─────────┬──┘──────────────┘      │
│                  │             │                          │
│           ┌──────▼─────────────▼──────┐                  │
│           │  Priority-based selector  │                  │
│           │  (auto-picks best route)  │                  │
│           └───────────────────────────┘                  │
└──────────────────────────────────────────────────────────┘
```

**Ключевое:** Clan не привязан к одному VPN. Можно подключить несколько сетевых технологий, и система автоматически выберет лучший маршрут.

### Data Mesher v2 — децентрализованная синхронизация

```
┌─────────────────────────────────────────────────────┐
│                  Data Mesher v2                       │
│                                                      │
│  Gossip Protocol ─── Eventually Consistent           │
│                                                      │
│  Node A ◄───gossip───► Node B ◄───gossip───► Node C │
│    │                      │                     │    │
│    ▼                      ▼                     ▼    │
│  /files/               /files/               /files/ │
│  signed by             signed by             signed  │
│  ED25519               ED25519               ED25519 │
│                                                      │
│  Roles: default | signer | peer | bootstrap | admin  │
│  Port: 7946 (configurable)                           │
│  Transport: encrypted                                │
└─────────────────────────────────────────────────────┘
```

### Vars — декларативное управление секретами

```
Старый подход (facts):          Новый подход (vars):
  Ручная генерация                Декларативный — сервис описывает
  Привязка к машине               свои секреты сам
  Ручная ротация                  Автоматическая генерация
                                  Привязка к сервису
                                  Интеграция с CLI/GUI
                                  Кросс-машинная координация
```

### Service Exports — межсервисная композабельность

```nix
-- Сервис A экспортирует значения
perInstance = { mkExports, machine, ... }: {
  exports = mkExports {
    peer.hosts = [{
      plain = clanLib.getPublicValue {
        machine = machine.name;
        generator = "mycelium";
        file = "ip";
        flake = directory;
      };
    }];
  };
};

-- Сервис B потребляет экспорты сервиса A
-- Автоматическая проводка без ручного glue-code
```

---

## 🖥️ Clan GUI

```
┌─────────────────────────────────────────────────┐
│                  Clan GUI (GTK)                  │
│                                                  │
│  ┌─────────────────────────────────────────────┐│
│  │  📊 Fleet Overview                          ││
│  │  ┌───────┐  ┌───────┐  ┌───────┐           ││
│  │  │Server │  │Laptop │  │MacBook│           ││
│  │  │  🟢   │  │  🟢   │  │  🟡   │           ││
│  │  └───────┘  └───────┘  └───────┘           ││
│  ├─────────────────────────────────────────────┤│
│  │  🔧 Services        🔑 Secrets              ││
│  │  🌐 Networks        💾 Backups              ││
│  │  📦 Deployments     🏷️ Tags & Groups        ││
│  └─────────────────────────────────────────────┘│
│                                                  │
│  Не заменяет CLI/Nix — надстройка для           │
│  визуализации и доступности                      │
└─────────────────────────────────────────────────┘
```

---

## 🔮 Будущее Clan: Spaces (2026+)

**Spaces** — следующий уровень: изолированные суверенные рабочие пространства.

```
┌──────────────────────────────────────────────────────────────┐
│                         SPACES                                │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Работа     │  │   Семья      │  │   Гейминг    │      │
│  │   🏢         │  │   🏠         │  │   🎮         │      │
│  │              │  │              │  │              │      │
│  │ MicroVM      │  │ MicroVM      │  │ MicroVM      │      │
│  │ Изоляция     │  │ Изоляция     │  │ GPU passthru │      │
│  │ VPN: корп.   │  │ VPN: семейн. │  │ VPN: open    │      │
│  │ Секреты: yes │  │ Фото: shared │  │ Латенси: low │      │
│  │              │  │              │  │              │      │
│  │ Встроенные:  │  │ Встроенные:  │  │ Встроенные:  │      │
│  │ docs, chat,  │  │ photos,      │  │ Steam,       │      │
│  │ IDE, deploy  │  │ calendar,    │  │ Discord,     │      │
│  │              │  │ messenger    │  │ streaming    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  🎯 Изоляция by design — MicroVM + Wayland + GPU            │
│  🤝 Multiplayer by default — Clan mesh networking            │
│  🔒 Суверенность — весь код/данные под контролем юзера       │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔗 Clan + Blockchain / Web3

Из 2025 Wrap-Up (clan.lol/blog/2025-wrap-up):

> "Clan can fix this" — о централизованной blockchain-инфраструктуре

**Конкретные направления:**
1. **Off-chain smart contracts** — эфемерные приватные L2 на Clan вместо application-specific L2s
2. **DAO Desktop** — члены DAO получают предконфигурированное окружение через Clan
3. **Communal hosting** — коллективизация node-ресурсов между Clan-ами
4. **LLM integration** — локальные LLM как медиаторы между Clan-ами для discovery и negotiation

**Спонсор Golem Network** — проект децентрализованных вычислений.

---

## ⚙️ CLI возможности

```bash
clan init                    # Создать новый Clan
clan machines list           # Список машин
clan machines install        # Удалённая установка (SSH / QR-код)
clan machines update         # Обновить конфигурацию
clan secrets                 # Управление секретами (vars)
clan backups                 # Управление бэкапами
clan flash                   # Прошить образ на USB/SD
```

---

## 🎯 Почему Clan для nn3w

| Потребность nn3w | Как решает Clan |
|:---|:---|
| P2P без центрального сервера | Архитектура без контроллера, mesh VPN |
| Overlay networks | Мульти-VPN абстракция (ZeroTier, Tor, Mycelium) |
| Суверенность данных | Data Mesher, encrypted transport, ED25519 |
| Управление секретами | Vars — декларативные, привязаны к сервисам |
| Cross-machine сервисы | Inventory + Service Exports |
| Децентрализованные ноды | Blueprint для blockchain node management |
| Масштабирование | Tags, groups, fleet-wide operations |
| macOS support | First-class nix-darwin интеграция |

---

## ⚠️ Ограничения

- **Только NixOS/macOS** — нет поддержки non-Nix Linux дистрибутивов
- **ZeroTier зависимость** — основной VPN требует ZeroTier controller (хоть и с децентрализацией)
- **GUI в early development** — пока complementary к CLI
- **Нет интеграции с Den** — нужно строить самим (но они совместимы через flake)
