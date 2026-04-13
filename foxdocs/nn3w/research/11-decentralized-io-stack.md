# Децентрализованный I/O стек: IPFS + Ceramic + Lattica

> **Контекст:** nn3w строит суверенную инфраструктуру на Nix + P2P.
> Нужен полный I/O стек без единых точек отказа, работающий как в Web2 так и в Web3.
> **Дата:** 2026-03-18

---

## Проблема

IPFS решает хранение, но не решает:
- Мутабельные данные с историей (IPNS — костыль, нет GraphQL, нет composability)
- Real-time коммуникацию (RPC, стриминг, координацию агентов)
- Ephemeral state (статусы задач, координация воркеров)

Нужен **трёхуровневый стек** на одном фундаменте (libp2p).

---

## Архитектура: три слоя одного стека

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ПРИЛОЖЕНИЯ                                      │
│  Factory (AI-фабрика) ── Agents ── Knowledge System ── Dashboard   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  CERAMIC ── мутабельные данные с верифицируемой историей              │
│  ═════════════════════════════════════════════════════               │
│  Что:    Event streams (hash-linked chains поверх IPFS/IPLD)        │
│  Зачем:  Knowledge Graph, метаданные, audit trail, composability    │
│  API:    GraphQL (ComposeDB), SQL (OrbisDB), REST, TypeScript SDK   │
│  Auth:   DID + crypto wallet signing                                 │
│  Anchor: Ethereum (merkle root → immutable timestamps)              │
│  Sync:   Recon protocol (Rust + libp2p), 250 TPS                   │
│  Scale:  350M events, 10M streams, 1.5M accounts, 400 apps         │
│  Cost:   Self-hosted node от $5/мес                                  │
│                                                                      │
│  Экосистема:                                                         │
│  • ComposeDB — графовая БД, 5000+ plug-and-play моделей             │
│  • OrbisDB — реляционная БД (Postgres indexing)                     │
│  • Lit Protocol — threshold encryption, условия доступа              │
│  • ElizaOS integration — encrypted agent memory                      │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LATTICA ── real-time P2P коммуникация для AI                        │
│  ═════════════════════════════════════════════                       │
│  Что:    P2P communication framework (Rust + libp2p)                │
│  Зачем:  RPC между агентами, стриминг, координация inference        │
│  Автор:  Gradient Network (arxiv:2510.00183, 2025)                  │
│  SDK:    Python (pip install lattica), Rust core + FFI               │
│                                                                      │
│  Три компонента:                                                     │
│  1. NAT Traversal — DCUtR (TCP/QUIC), AutoNAT, relay fallback      │
│     ~70% прямых P2P, 100% связность, Noise/TLS шифрование          │
│  2. CRDT Data Store — eventually consistent, верифицируемый          │
│     Для ephemeral state: статусы задач, координация воркеров        │
│  3. Content Discovery — DHT (Kademlia) + Bitswap + RPC              │
│     Request-response (control plane) + streaming (data plane)        │
│                                                                      │
│  Производительность:                                                 │
│  • Локально: 10,000 QPS (128B), 850 QPS (256KB)                    │
│  • Межконтинент: 1,200 QPS (128B), 110 QPS (256KB)                 │
│                                                                      │
│  Сценарии:                                                           │
│  • Децентрализованный CDN для моделей (CID → Bitswap → peers)      │
│  • Sharded AI inference (модель по шардам → RPC координация)        │
│  • Collaborative RL (обмен policies через DHT)                      │
│  • Federated learning (обновления без центрального сервера)          │
│                                                                      │
│  Background: Gradient Sentry Node Open Beta —                        │
│  2+ млрд P2P подключений в 190+ регионах                            │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  IPFS ── иммутабельное content-addressed хранилище                   │
│  ═══════════════════════════════════════════════                     │
│  Что:    Distributed file system (content-addressed)                │
│  Зачем:  Nix binary cache, модели, артефакты, bulk distribution     │
│  Связь:  Content-Addressed Nix Store (PR #3727) → IPFS прозрачно   │
│                                                                      │
│  nix-casync идея: chunk-based storage (4KB blocks → CID per chunk)  │
│  Результат: изменение 1 байта → передаётся 4KB вместо 100MB        │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  libp2p ── общий P2P фундамент                                      │
│  ═══════════════════════════════                                    │
│  Один PeerID для всех трёх слоёв                                    │
│  DHT, NAT traversal, encryption, peer discovery, transports         │
│  TCP, QUIC, WebSocket, WebRTC                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Разделение ответственности

| Задача | IPFS | Ceramic | Lattica |
|:-------|:----:|:-------:|:-------:|
| Хранение файлов/блобов | **да** | нет | нет |
| Nix binary cache | **да** | нет | нет |
| Bulk distribution моделей | **да** | нет | Bitswap CDN |
| Мутабельные записи | нет | **да** | нет |
| Knowledge Graph | нет | **ComposeDB** | нет |
| Audit trail (кто/что/когда) | нет | **да** (DID + Ethereum anchor) | нет |
| GraphQL API | нет | **да** | нет |
| RPC между агентами | нет | нет | **да** |
| Стриминг stdout/данных | нет | нет | **да** |
| Координация inference | нет | нет | **да** (shard-aware RPC) |
| Ephemeral state | нет | нет | **да** (CRDT) |
| Encrypted data | нет | Lit Protocol | нет |

---

## Ceramic vs OrbitDB — выбор для nn3w

| Критерий | Ceramic + ComposeDB | OrbitDB |
|:---------|:-------------------:|:-------:|
| Мутабельность | Event streams | CRDT documents |
| Запросы | **GraphQL, SQL** | Key-value, docstore |
| Composability | **5000+ моделей, 400 apps** | Нет экосистемы |
| Верифицируемость | **DID + Ethereum anchor** | CRDT + IPFS (слабее) |
| Блокчейн зависимость | Ethereum (для anchoring) | Нет |
| Сложность | Выше | Ниже |
| Encrypted storage | **Lit Protocol (proven)** | Ручное |
| Agent memory | **ElizaOS integration** | Нет |
| Self-hosting | $5/мес нода | Просто IPFS + OrbitDB |

**Вывод:** Ceramic + ComposeDB для Knowledge Graph и audit trail.
Lattica CRDT для ephemeral state (координация, статусы).
OrbitDB — как fallback если не нужен блокчейн anchoring.

---

## Web2 ↔ Web3 бимодальность (Transport Adapter)

Приложения не знают через что работают — единый API, разный транспорт:

```
                     Web2.0 Mode                    Web3.0 Mode
                     ──────────                     ──────────
Storage:             S3 / PostgreSQL         →      IPFS / Ceramic (ComposeDB)
Messaging:           NATS (centralized)      →      Lattica (P2P mesh)
Task queue:          NATS JetStream          →      Lattica DHT + CRDT
Identity:            JWT / OAuth             →      DID + UCAN
Model distribution:  HTTP download           →      IPFS Bitswap (CDN)
State sync:          SQLite / Postgres       →      Ceramic streams + Lattica CRDT
Encryption:          Server-side             →      Lit Protocol (threshold)
Code hosting:        GitHub / Forgejo        →      Tangled / Radicle
Binary cache:        cache.nixos.org (HTTP)  →      IPFS binary cache (PR #3727)
```

---

## Применение к Factory (AI-фабрика)

```
Factory получает задачу "создать landing page"
  │
  ├─ COMPASS Meta-Thinker читает контекст из Ceramic (ComposeDB)
  │  → предыдущие проекты, паттерны, knowledge graph
  │
  ├─ MAKER декомпозирует на микрошаги
  │  → каждый шаг = Ceramic event (audit trail)
  │
  ├─ AI-агенты (Claude Code / Aider) запускаются в sandboxai Cell
  │  → stdout стримится через Lattica RPC
  │  → координация через Lattica CRDT (статусы, прогресс)
  │
  ├─ Артефакты (код, Docker images) публикуются в IPFS
  │  → CID записывается в Ceramic stream проекта
  │
  ├─ Деплой через vladOS/nn3w (Nix + deploy-rs)
  │  → binary cache через IPFS (content-addressed)
  │
  └─ Knowledge System обновляется
     → ComposeDB: новые propositions, entities
     → Другие Factory-ноды могут учиться на этих данных (composability)
```

---

## Ключевые ссылки

| Ресурс | URL |
|:-------|:----|
| Lattica paper | https://arxiv.org/abs/2510.00183 |
| Lattica Python SDK | `pip install lattica` (PyPI v1.0.16) |
| Gradient Network | https://gradient.network |
| Ceramic docs | https://developers.ceramic.network |
| ComposeDB | https://ceramic.network/composedb |
| OrbisDB | https://useorbis.com |
| Lit Protocol | https://litprotocol.com |
| ElizaOS + Lit + OrbisDB | https://github.com/ceramicstudio/eliza-with-lit-orbisdb |
| Recon protocol (CIP-124) | https://cips.ceramic.network/CIPs/cip-124 |
| Reproducible Builds (paper) | https://arxiv.org/abs/2104.06020 |
| IPFS + DID self-verifiable | https://arxiv.org/abs/2105.08395 |
| SWE-Gym (AI agents training) | https://arxiv.org/abs/2412.21139 |
| Unison language (CA code) | https://unison-lang.org |
| Bacalhau (compute over data) | https://bacalhau.org |
| Holochain (agent-centric DHT) | https://holochain.org |

---

## Связь с Dendritic паттерном

Dendritic (Den) организует **конфигурацию** (aspect-oriented .nix файлы).
Этот I/O стек организует **данные и коммуникацию** (decentralized layers).

Они сочетаются через **content-addressing**:
- Den aspect → Nix derivation → `/nix/store/<hash>` → IPFS CID
- Factory event → Ceramic stream → IPFS IPLD → CID
- Agent message → Lattica RPC → libp2p PeerID

Один PeerID. Один CID namespace. Разные слои.

---

## Что дальше

1. **Ближайшее:** интегрировать Ceramic node в nn3w как Den aspect (`aspects/p2p/ceramic.nix`)
2. **Среднесрочное:** Lattica SDK для коммуникации между exclaves через P2P mesh
3. **Долгосрочное:** полный I/O стек (IPFS + Ceramic + Lattica) как единый Den namespace `den.ful.nn3w.decentralized-io`
4. **Следить:** Nix IPFS PR #3727, Ceramic Recon стабилизация, Lattica SDK evolution
