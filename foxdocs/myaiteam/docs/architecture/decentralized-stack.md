# 🌐 Децентрализованный технологический стек

> **Связанные документы:**
> - [Architecture Overview](overview.md)
> - [Privacy & Access Control](privacy-access.md)
> - [Concepts: Decentralized Technologies](../concepts/decentralized-tech.md)

---

## 1. Обзор стека

### 1.1 Проблемы, которые решаем

| Проблема | Решение |
|----------|---------|
| Где хранить файлы? | IPFS (content-addressed storage) |
| Как связывать данные? | IPLD (linked data model) |
| Как обновлять ссылки? | IPNS (mutable pointers) |
| Как контролировать доступ? | UCAN (authorization) |
| Как защитить данные? | Lit Protocol (encryption) |
| Как синхронизировать? | PubSub (real-time) |
| Как делать queries? | Ceramic/ComposeDB (structured data) |

### 1.2 Многослойный стек

```
╔═══════════════════════════════════════════════════════════════════╗
║                DECENTRALIZED KNOWLEDGE STACK                      ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │  APPLICATION LAYER                                          │  ║
║  │  UI, Agents, Services                                       │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                │                                  ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │  AUTHORIZATION: UCAN                                        │  ║
║  │  "Кто что МОЖЕТ делать"                                     │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                │                                  ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │  ENCRYPTION: Lit Protocol                                   │  ║
║  │  "Кто может РАСШИФРОВАТЬ данные"                            │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                │                                  ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │  STRUCTURED DATA: Ceramic + ComposeDB                       │  ║
║  │  "Метаданные, схемы, queries"                               │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                │                                  ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │  STORAGE: IPFS + IPLD + IPNS                                │  ║
║  │  "Content-addressed blobs + linked data + mutable pointers" │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### 1.3 Аналогия: Офис компании

| Компонент | Аналогия | Функция |
|-----------|----------|---------|
| **IPFS** | Склад | Полки с коробками (CID как номер) |
| **IPLD** | Способ упаковки | Как связать коробки между собой |
| **IPNS** | Табличка на двери | "Актуальные документы → коробка #789" |
| **Ceramic** | Каталог + журнал | Метаданные и история изменений |
| **UCAN** | Пропуск + права | "Alice может входить в HR" |
| **Lit Protocol** | Замок на коробке | Даже если украдёшь — не откроешь |
| **PubSub** | Громкоговоритель | Уведомления для подписчиков |

---

## 2. IPFS Ecosystem

### 2.1 Карта экосистемы

```
┌─────────────────────────────────────────────────────────────────┐
│                    IPFS ECOSYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│  CORE LAYER:                                                    │
│  ├── IPFS (Storage)                                             │
│  ├── IPLD (Data linking)                                        │
│  ├── libp2p (Networking)                                        │
│  └── Multiformats (Formats)                                     │
├─────────────────────────────────────────────────────────────────┤
│  FEATURES LAYER:                                                │
│  ├── IPNS (Mutable names)                                       │
│  ├── MFS (File system API)                                      │
│  ├── UnixFS (File format)                                       │
│  └── PubSub (Real-time)                                         │
├─────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE:                                                │
│  ├── DHT (Discovery)                                            │
│  ├── IPFS Cluster (Replication)                                 │
│  ├── DNSLink (Human URLs)                                       │
│  └── Gateways (HTTP access)                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 IPFS (Core Storage)

**Content-addressed storage** — файлы идентифицируются по хэшу содержимого.

```
Файл → hash(content) → CID → Хранится в сети

Пример:
"Hello World" → sha256 → QmWATWQ7fVPP2EFGu71UkfnqhYXDYH566qy47CnJDgvs8u
```

**Ключевые свойства:**

| Свойство | Описание |
|----------|----------|
| **Content-addressed** | CID = hash(content), один файл = один CID везде |
| **Immutable** | Изменение контента = новый CID |
| **Distributed** | Файлы на множестве nodes |
| **Deduplicated** | Одинаковые файлы не дублируются |

**Использовать для:**
- ✅ Хранение encrypted blobs
- ✅ Большие файлы (документы, медиа)
- ✅ Immutable snapshots
- ❌ Мутабельные данные напрямую (нужен IPNS)
- ❌ Structured queries (нужен Ceramic)

### 2.3 IPLD (InterPlanetary Linked Data)

Data model для **связанных данных** — ссылки на другие объекты по CID.

```json
// Обычный JSON:
{
  "name": "Bitcoin",
  "relatedTo": "Ethereum"  // строка, не ссылка!
}

// IPLD (с CID-ссылками):
{
  "name": "Bitcoin",
  "relatedTo": {
    "/": "bafyreic3..."     // настоящая ссылка на объект!
  }
}
```

**Идеально для Knowledge Graph:**
- Entities ссылаются на другие entities через CID
- Граф строится естественно из ссылок
- Можно traverse по ссылкам
- Универсальный формат

### 2.4 IPNS (InterPlanetary Name System)

**Проблема:** CID меняется при изменении контента. Как поделиться стабильной ссылкой?

**Решение:** IPNS — мутабельные указатели.

```
IPNS name ────────────────────► CID (можно обновлять!)
k51qzi5uqu...                   QmCurrentVersion

Обновление:
k51qzi5uqu... ──► QmVersion1
k51qzi5uqu... ──► QmVersion2  (та же name, новый CID)
k51qzi5uqu... ──► QmVersion3

IPNS name = hash(public_key)
Обновить может только владелец private_key
```

**Использовать для:**
- "Моя база знаний" → ipns://k51... → всегда последняя версия
- Каждый user/agent имеет свой IPNS name
- Публикация текущего состояния KG

### 2.5 PubSub

**Real-time messaging** — подписка на топики.

```
Agent 1 ──┐
          │  TOPIC: "project-alpha-updates"
Agent 2 ──┼──────────────────────────────────►  All Subscribers
          │
Human  ───┘

Примеры topics:
├── "kg/project-alpha/entities" — новые entities
├── "kg/project-alpha/claims"   — новые claims
├── "kg/agents/status"          — статусы агентов
└── "kg/sync/requests"          — запросы на sync
```

---

## 3. Ceramic Network

### 3.1 Что это

**Decentralized data network** для мутабельных структурированных данных.

| IPFS | Ceramic |
|------|---------|
| Raw bytes | Structured JSON |
| Immutable | Mutable (streams) |
| No schema | GraphQL schema |
| Query by CID | Query by fields |

### 3.2 Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                    CERAMIC ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│  ComposeDB         ◄── GraphQL queries, schemas                 │
│       │                                                         │
│  Streams           ◄── Append-only event logs                   │
│       │                                                         │
│  Events            ◄── Signed by DID (Init, Data, Time)         │
│       │                                                         │
│  IPFS              ◄── Storage layer                            │
└─────────────────────────────────────────────────────────────────┘

Scale (2024): 350M events, 10M streams, 1.5M accounts, 400 apps
```

### 3.3 Streams

**Stream = Append-only log of events**

```
Stream: "Alice's Profile"

Event 1 (Init):     { name: "Alice", bio: "Developer" }
     │
     ▼
Event 2 (Update):   { bio: "Senior Developer" }
     │
     ▼
Event 3 (Update):   { location: "Berlin" }
     │
     ▼
Current State:      { name: "Alice",
                      bio: "Senior Developer",
                      location: "Berlin" }

Каждый event подписан DID автора
```

### 3.4 ComposeDB

GraphQL layer поверх Ceramic streams:

```graphql
# Schema
type Entity @createModel {
  name: String! @string(maxLength: 100)
  type: String! @string(maxLength: 50)
  description: String @string(maxLength: 1000)
  relatedTo: [StreamID!]
  createdBy: DID!
  createdAt: DateTime!
}

# Query
query {
  entityIndex(
    first: 10, 
    filters: { where: { type: { equalTo: "cryptocurrency" }}}
  ) {
    edges {
      node {
        name
        description
      }
    }
  }
}
```

### 3.5 Когда использовать Ceramic

| ✅ Использовать | ❌ Не использовать |
|----------------|-------------------|
| Structured queries (GraphQL) | Личная локальная база |
| История изменений | Strong consistency |
| Multi-user collaboration | Нет Web3/DID требований |
| Cross-app data sharing | Простой прототип |

---

## 4. OrbitDB vs Ceramic

### 4.1 Ключевое различие: Real-Time

```
CERAMIC (Event Sourcing + Blockchain Anchoring):
Event 1 ──► Event 2 ──► Event 3 ──► TimeEvent (anchor)
                                        │
                                        ▼
                              Blockchain (Ethereum)

Anchoring батчами → ЗАДЕРЖКА (минуты, не миллисекунды!)

────────────────────────────────────────────────────────

OrbitDB (Merkle-CRDTs):
Peer A: op1 ──► op2 ──► op3
                  ╲
                   ╲ merge (instant!)
                    ╲
Peer B: op1 ──► op4 ──► merged state

Операции коммутативны → Merge МГНОВЕННО
```

### 4.2 Сравнение

| Аспект | Ceramic | OrbitDB |
|--------|---------|---------|
| **Update latency** | Seconds + minutes (anchor) | Milliseconds |
| **Concurrent edits** | Last-write-wins | CRDT auto-merge |
| **Real-time collab** | ⚠️ Limited | ✅ Native |
| **Global ordering** | ✅ Via blockchain | ❌ Partial (causal) |
| **Tamper-proof** | ✅ Blockchain anchors | ❌ No external proof |
| **Structured queries** | ✅ GraphQL | ❌ Limited |
| **Schema ecosystem** | ✅ ComposeDB | ❌ None |

### 4.3 Выбор по сценарию

| Сценарий | Выбор |
|----------|-------|
| Collaborative editing (Google Docs style) | **OrbitDB + Automerge/Yjs** |
| Knowledge base с auditability | **Ceramic** |
| Multi-agent parallel writes | **OrbitDB** |
| Cross-app data sharing | **Ceramic** |
| Private team knowledge base | Оба работают |
| Public verifiable data | **Ceramic** |

---

## 5. Что где хранится

```
┌─────────────────────────────────────────────────────────────────┐
│                    ЧТО ГДЕ ХРАНИТСЯ                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  IPFS (публичный, но зашифрованный):                            │
│  ├── CID: QmXyz123...                                           │
│  ├── Content: 0x8f4a2b3c... (зашифрованный blob)                │
│  └── Любой скачает → получит мусор (ciphertext)                 │
│                                                                 │
│  LIT PROTOCOL (key management):                                 │
│  ├── Encrypted symmetric key (разделён между нодами)            │
│  ├── Access Control Conditions                                  │
│  └── НЕ хранит сам контент                                      │
│                                                                 │
│  CERAMIC (metadata + queries):                                  │
│  ├── documentId, encryptedCID, litConditions                    │
│  ├── owner (DID), type, tags                                    │
│  └── Можно искать по полям                                      │
│                                                                 │
│  UCAN (authorization tokens):                                   │
│  ├── JWT-like tokens с capability chains                        │
│  └── Проверяются при каждой операции                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Полный Flow: Добавление документа

```
┌─────────────────────────────────────────────────────────────────┐
│  FLOW: Agent добавляет документ в Project Alpha                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. UCAN — Проверка прав на ОПЕРАЦИЮ                            │
│     Agent предъявляет токен: "write:documents в project-alpha"  │
│     Проверка: подпись, цепочка, срок, capability                │
│                                                                 │
│  2. Lit Protocol — Шифрование ДАННЫХ                            │
│     Условия: "Только члены project-alpha"                       │
│     Результат: ciphertext                                       │
│                                                                 │
│  3. IPFS — Сохранение зашифрованного файла                      │
│     ipfs.add(ciphertext) → CID: "QmXyz..."                      │
│                                                                 │
│  4. IPLD — Создание linked object                               │
│     { type: "document", encryptedContent: {"/": "QmXyz..."} }   │
│                                                                 │
│  5. Ceramic — Сохранение метаданных                             │
│     ComposeDB record с metadata                                 │
│                                                                 │
│  6. IPNS — Обновление pointer на KG root                        │
│                                                                 │
│  7. PubSub — Уведомление subscribers                            │
│     Topic "project-alpha/updates"                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Сводная таблица компонентов

| Компонент | Функция | Для KG нужен? |
|-----------|---------|---------------|
| **IPFS** | Content-addressed storage | ✅ Да, основа |
| **IPLD** | Linked data model | ✅ Да, для графа |
| **IPNS** | Mutable pointers | ✅ Да, для обновлений |
| **PubSub** | Real-time messaging | ✅ Да, для sync |
| **MFS** | File system API | ⚡ Опционально |
| **DNSLink** | Human URLs | ⚡ Для production |
| **IPFS Cluster** | Replication | ⚡ Для production |
| **Ceramic** | Structured mutable data | ✅ Для команды |
| **OrbitDB** | Real-time P2P database | ⚡ Для real-time collab |
| **Lit Protocol** | Decentralized encryption | ✅ Для приватности |
| **UCAN** | Capability authorization | ✅ Для доступа |

---

## 8. Рекомендации по выбору

### 8.1 По типу использования

| Использование | Рекомендуемый стек |
|---------------|-------------------|
| **Личная база** | IPFS + IPNS + Lit (optional) |
| **Команда** | IPFS + Ceramic + Lit + UCAN + PubSub |
| **Real-time collab** | OrbitDB + Automerge |
| **Платформа** | Всё + IPFS Cluster + DNSLink |

### 8.2 Альтернативы (без Web3)

| Web3 Stack | Альтернатива | Trade-off |
|------------|--------------|-----------|
| IPFS | S3 + content hashing | Централизованно |
| Ceramic | PostgreSQL + events | Централизованно |
| Lit Protocol | AES + key server | Нужен свой сервер |
| UCAN | JWT + RBAC | Централизованная auth |

---

## 9. Навигация

| Следующий документ | Тема |
|--------------------|------|
| → [privacy-access.md](privacy-access.md) | Детали приватности и доступа |
| → [../implementation/ipfs-ceramic-setup.md](../implementation/ipfs-ceramic-setup.md) | Практическая настройка |

---

*Источники: Decentralized-Knowledge-Stack-Guide.md, Decentralized-Graph-Architecture.md*
