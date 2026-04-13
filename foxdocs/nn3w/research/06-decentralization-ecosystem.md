# 🌐 Децентрализация + Nix — Экосистема технологий

> **Контекст:** nn3w — суверенная инфраструктура на стыке NixOS и web3
> **Цель:** Понять текущее состояние интеграции Nix с децентрализованными технологиями

---

## 🗺️ Общая картина

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ДЕЦЕНТРАЛИЗОВАННЫЙ СТЕК                               │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     СЛОЙ ПРИЛОЖЕНИЙ                                │ │
│  │                                                                    │ │
│  │  DApps ── DAO Desktop ── Spaces (Clan) ── P2P Services            │ │
│  └───────────────────────────┬────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────▼────────────────────────────────────────┐ │
│  │                     СЛОЙ КОНФИГУРАЦИИ                              │ │
│  │                                                                    │ │
│  │  Den (аспекты, ctx-pipeline) ── flake-parts ── std (CI/CD)        │ │
│  └───────────────────────────┬────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────▼────────────────────────────────────────┐ │
│  │                     СЛОЙ ИНФРАСТРУКТУРЫ                            │ │
│  │                                                                    │ │
│  │  Clan (fleet) ── Overlay Networks ── MicroVM ── Enclaves          │ │
│  └───────────────────────────┬────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────▼────────────────────────────────────────┐ │
│  │                     СЛОЙ КОДА                                      │ │
│  │                                                                    │ │
│  │  Tangled (AT Proto) ── Radicle (P2P Git) ── Forgejo (federated)   │ │
│  └───────────────────────────┬────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────▼────────────────────────────────────────┐ │
│  │                     СЛОЙ ХРАНИЛИЩА                                 │ │
│  │                                                                    │ │
│  │  IPFS ── Content-Addressed Nix Store ── nix-casync ── IPLD        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Content-Addressed Nix Store

### Текущее состояние (Nix 2.28.6)

Content-addressed store objects — уже в стабильном Nix:

```
Input-addressed (классический):          Content-addressed:
────────────────────────────             ──────────────────
/nix/store/<hash-of-inputs>-name         /nix/store/<hash-of-content>-name
  │                                        │
  │ Hash зависит от:                       │ Hash зависит от:
  │ • Всех build inputs                    │ • Только от содержимого файлов
  │ • Build environment                    │ • Имя + references + FSO graph
  │ • Derivation                           │
  │                                        │
  │ Одинаковый результат ≠                 │ Одинаковый результат =
  │ одинаковый hash                        │ одинаковый hash ✅
```

**Команда:**
```bash
nix store make-content-addressed /nix/store/xxx-hello
```

### Почему это фундамент для IPFS

```
Content-Addressed Nix Store ←──── одинаковый принцип ────► IPFS
     hash(content) = path             CID = hash(content)

Если два разных build дают одинаковый результат:
  CA Nix:   один и тот же store path
  IPFS:     один и тот же CID

Следовательно: CA Nix store path ←→ IPFS CID
                     (теоретически)
```

---

## 🌍 IPFS + Nix

### PR #3727: Trustful IPFS Store (Draft, обновлён ноябрь 2024)

```
┌──────────────────────────────────────────────────────┐
│            Trustful IPFS Store (PR #3727)              │
│                                                        │
│  Что делает:                                           │
│  • Upload support для IPFS binary caches               │
│  • Store graph представлен через IPLD                  │
│  • Нативная работа с IPFS без extra content addressing │
│                                                        │
│  Статус: WIP Draft                                     │
│  Формат store: subject to change                       │
│  Автор: flokli                                         │
│                                                        │
│  ┌─────────┐    IPLD    ┌─────────┐   gossip  ┌─────┐│
│  │ Nix     │───────────►│  IPFS   │◄─────────►│IPFS ││
│  │ Store   │            │  Node   │           │Peers││
│  └─────────┘            └─────────┘           └─────┘│
└──────────────────────────────────────────────────────┘
```

### Pre-RFC: Generic Content-Addressed Fetchers

Обсуждение на NixOS Discourse (февраль 2025):
- **Проблема:** `fetchipfs` использует UnixFS tarballs → только Kubo RPC API (порт 5001)
- **Предложение:** Generic CA fetchers для IPFS, Radicle и др.
- **Решение:** `fetchGitIPFS` и подобные — в разработке
- **Блокер:** Bootstrapping — как скачать первый пакет через IPFS?

### ipfs-cluster в Nixpkgs

```nix
-- Уже доступен:
services.ipfs-cluster = {
  enable = true;
  -- Аллокация, репликация и трекинг пинов
  -- по кластеру IPFS-демонов
};
```

---

## 🧬 nix-casync — Content-Addressed Chunk Storage

```
┌──────────────────────────────────────────────────────┐
│                    nix-casync                          │
│                                                        │
│  Классический NAR:           nix-casync:               │
│  ┌──────────────────┐       ┌──────────────────┐      │
│  │   Весь файл      │       │  Chunk 1 (4KB)   │      │
│  │   целиком        │       │  Chunk 2 (4KB)   │      │
│  │   (100MB .nar)   │       │  Chunk 3 (4KB)   │      │
│  └──────────────────┘       │  ...              │      │
│                              │  Chunk N (2KB)   │      │
│  При изменении 1 байта:     └──────────────────┘      │
│  Передаётся 100MB            При изменении 1 байта:   │
│                              Передаётся 4KB (1 chunk) │
│                                                        │
│  Compression ratio:                                    │
│  zstd alone: 2.69x                                    │
│  casync:     6.55x  (x2.4 лучше!)                    │
│                                                        │
│  ⚠️ Репо архивирован (2023), но идеи живы в Nix core  │
└──────────────────────────────────────────────────────┘
```

**Идея nix-casync идеально ложится на IPFS:** чанки = content-addressed блоки, которые можно хранить и извлекать из IPFS по CID.

---

## 🔀 Radicle — Суверенный Git Forge

```
┌──────────────────────────────────────────────────────┐
│                     RADICLE                           │
│              "The Sovereign Forge"                    │
│                                                       │
│  ┌─────────┐   gossip    ┌─────────┐                │
│  │  Node   │◄───────────►│  Node   │                │
│  │ (peer)  │  protocol   │ (peer)  │                │
│  └────┬────┘             └────┬────┘                │
│       │                       │                      │
│       ▼                       ▼                      │
│  ┌─────────┐             ┌─────────┐                │
│  │  Git    │             │  Git    │                │
│  │  Repo   │             │  Repo   │                │
│  └─────────┘             └─────────┘                │
│                                                       │
│  Версия: 1.6.0 (Amaryllis, январь 2026)             │
│  ~2000 репозиториев, ~200 нод в неделю               │
│  Код-ревью, issues, patches — всё как Git-объекты    │
│  Криптографические идентичности (ED25519)             │
│  Работает офлайн                                      │
│                                                       │
│  🔗 Nix Pre-RFC обсуждает `fetchRadicle` fetcher     │
└──────────────────────────────────────────────────────┘
```

**Для nn3w:** Radicle может быть основой для хранения и распространения Nix-конфигураций в децентрализованной сети.

---

## 🪢 Tangled — Social Coding на AT Protocol

```
┌──────────────────────────────────────────────────────┐
│                     TANGLED                           │
│           "Tightly-knit Social Coding"               │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │                 AT Protocol                      │ │
│  │           (Bluesky infrastructure)               │ │
│  └──────────────────────┬──────────────────────────┘ │
│                         │                             │
│  ┌──────────────────────▼──────────────────────────┐ │
│  │              Tangled App View                    │ │
│  │           (tangled.sh — web interface)           │ │
│  └──────────────────────┬──────────────────────────┘ │
│                         │                             │
│         ┌───────────────┼───────────────┐            │
│         ▼               ▼               ▼            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │   Knot A   │  │   Knot B   │  │   Knot C   │     │
│  │ (self-host)│  │ (community)│  │ (RPi)      │     │
│  │ Git repos  │  │ Git repos  │  │ Git repos  │     │
│  └────────────┘  └────────────┘  └────────────┘     │
│                                                       │
│  Финансирование: €3.8M (март 2026)                   │
│  Backers: бывший CEO GitHub, CEO Tailscale,           │
│           бывший CEO MySQL                            │
│  NixOS deployment поддерживается нативно              │
│  CI/CD: Spindles (встроенный)                        │
│  Webhooks, website hosting                            │
│                                                       │
│  🔑 vic/den уже зеркалится на Tangled!               │
│     tangled.org/oeiuwq.com/den                       │
└──────────────────────────────────────────────────────┘
```

**Для nn3w:** Tangled может быть основой для social coding + CI/CD в децентрализованном контексте. NixOS deployment из коробки.

---

## 🏠 Nixda Stack — Sovereign Self-Hosting

```
┌──────────────────────────────────────────────────────┐
│                    NIXDA STACK                        │
│         "Declare once. Own forever."                 │
│                                                       │
│  Принципы:                                           │
│  • Один Nix-файл = один сервис                       │
│  • Socket activation (scale to zero)                 │
│  • Zone-based networking (service.zone.lan)           │
│  • Immutable root filesystem                         │
│  • Rebuild ~2 минуты на Dell R630                    │
│                                                       │
│  Без: Kubernetes, Docker Compose, Terraform, Ansible │
│  Всё: через nixos-rebuild switch                     │
│                                                       │
│  Runtime options: Native / Podman / MicroVM          │
│                                                       │
│  ROI: окупается за ~12 месяцев vs cloud              │
└──────────────────────────────────────────────────────┘
```

---

## 📊 Сводная таблица готовности к децентрализации

| Технология | Готовность | Роль в nn3w |
|:---|:---:|:---|
| **Content-Addressed Nix Store** | ✅ Стабильный | Фундамент — hash by content |
| **IPFS binary cache (PR #3727)** | 🟡 Draft WIP | Будущее — децентрализованный cache |
| **ipfs-cluster** | ✅ В nixpkgs | Репликация пинов по кластеру |
| **Generic CA fetchers** | 🟡 Pre-RFC | fetchipfs, fetchRadicle и др. |
| **nix-casync** | ⛔ Архивирован | Идеи живы → chunk-based IPFS |
| **Radicle** | ✅ v1.6.0 | P2P git forge для конфигов |
| **Tangled** | ✅ Финансирован | Social coding + NixOS deploy |
| **Clan mesh networking** | ✅ 25.11 stable | P2P fleet без центрального контроля |
| **Clan Data Mesher** | 🟡 v2 in progress | Gossip-based file sync |
| **Clan Spaces** | 🔴 Прототип | Изолированные суверенные окружения |
| **Nixda Stack** | ✅ Production | Self-hosted infra reference |

---

## 🔮 Видение: как это всё сойдётся

```
2026 (сейчас):
  CA Nix Store ✅ + Clan mesh ✅ + Den aspects ✅ + Radicle/Tangled ✅

2026-2027 (ближайшее):
  IPFS binary cache стабилизируется → CA Nix → IPFS прозрачно
  Clan Spaces → MicroVM-based изолированные окружения
  Generic CA fetchers → fetchipfs/fetchRadicle в nixpkgs

2027+ (горизонт):
  Nix Store полностью на IPFS → любая нода = binary cache
  Clan-to-Clan networking → inter-community resource sharing
  Den aspects через Dendrix → децентрализованный package registry
  LLM-медиаторы между Clan-ами → автоматический service discovery
```

---

## ⚠️ Текущие блокеры децентрализации в Nix

1. **IPFS bootstrapping** — как скачать первый пакет через IPFS если IPFS клиент ещё не установлен?
2. **fetchipfs ограничения** — работает только через Kubo RPC API (порт 5001), не через публичные gateways
3. **Производительность IPFS** — для одиночных загрузок IPFS менее эффективен чем HTTP
4. **Store format не финализирован** — IPLD представление Nix store ещё subject to change
5. **Отсутствие стандартного протокола** — нет единого fetcher для CA content (IPFS, Radicle, etc.)
