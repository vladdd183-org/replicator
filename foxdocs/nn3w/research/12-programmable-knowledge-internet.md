# Программируемый Интернет Знаний

> **nn3w North Star:** Гетерогенный-темпоральный-децентрализованный-мета-граф-мультимодальный.
> Фактически — новый интернет, где единица обмена не страница, а верифицируемый факт.
> Программирование на интернете: контракты, агенты, composability.
> **Дата:** 2026-03-18

---

## 1. Видение: от Web of Pages к Web of Knowledge

```
Web 1.0:  Страницы → Ссылки → Читай
Web 2.0:  Платформы → API → Потребляй / Создавай (но не владей)
Web 3.0:  Токены → Смарт-контракты → Владей (но только финансы)

nn3w:     Propositions → Meta-Graph → Программируй знания
          Content-addressed. Verifiable. Composable. AI-native.
```

**Центральная идея:** интернет, где атомарная единица — не файл и не страница,
а **Proposition** (верифицируемый факт с контекстом), организованная в
**Гетерогенный Мета-Граф**, и доступная для программирования через контракты,
агентов, и composable API.

---

## 2. Полная архитектура: 7 слоёв

```
╔═════════════════════════════════════════════════════════════════════════════════╗
║                      PROGRAMMABLE KNOWLEDGE INTERNET                            ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║                                                                                 ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 6: CONTRACTS & COMPOSITION                                         │  ║
║  │  Knowledge Contracts ── Composable Pipelines ── Inter-Graph Protocols     │  ║
║  │  "Программирование на интернете"                                          │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                          ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 5: AUTONOMOUS AGENTS (Factory)                                     │  ║
║  │  COMPASS(стратегия) + MAKER(надёжность) + DSPy(self-improvement)          │  ║
║  │  "AI который создаёт, деплоит, учится"                                    │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                          ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 4: HETEROGENEOUS META-GRAPH                                        │  ║
║  │  Propositions ── Entities ── Clusters ── Communities ── Themes             │  ║
║  │  "Знания, организованные в 6-уровневую иерархию"                          │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                          ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 3: ACCESS & IDENTITY                                               │  ║
║  │  DID(identity) ── UCAN(authorization) ── Lit Protocol(encryption)         │  ║
║  │  "Кто ты, что можешь, что видишь"                                         │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                          ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 2: MUTABLE DATA (Ceramic)                                          │  ║
║  │  Event Streams ── ComposeDB(GraphQL) ── OrbisDB(SQL)                      │  ║
║  │  "Мутабельная база данных с верифицируемой историей"                       │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                          ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 1: COMMUNICATION (Lattica)                                         │  ║
║  │  P2P Mesh ── RPC Streaming ── CRDT State ── NAT Traversal                │  ║
║  │  "Real-time связь между нодами без центрального сервера"                   │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                          ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 0: IMMUTABLE STORAGE (IPFS + Nix)                                 │  ║
║  │  Content-Addressed Blobs ── IPLD ── Nix Binary Cache ── Bitswap CDN      │  ║
║  │  "Фундамент: hash(content) = identity"                                    │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                          ║
║  ┌───────────────────────────────────────────────────────────────────────────┐  ║
║  │  FOUNDATION: libp2p                                                       │  ║
║  │  DHT ── NAT Traversal ── Encryption ── Peer Discovery ── Transports      │  ║
║  │  "Один PeerID, одна сеть, все слои"                                       │  ║
║  └───────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Layer 6: Knowledge Contracts — программирование на интернете

### 3.1 Что такое Knowledge Contract

Knowledge Contract — декларативное соглашение между участниками Meta-Graph,
определяющее правила создания, обмена, валидации и композиции знаний.

Это НЕ Ethereum smart contract (хотя может использовать anchoring).
Это **протокол взаимодействия** между нодами, агентами, и графами.

```yaml
knowledge_contract:
  id: kc_research_exchange
  name: "Research Exchange Protocol"
  version: "1.0.0"

  parties:
    - did:key:alice    # исследователь
    - did:key:factory  # AI-фабрика
    - did:key:bob      # рецензент

  # Что каждая сторона предоставляет и получает
  obligations:
    alice:
      provides:
        - type: Proposition
          model: ceramic://model/proposition-v2
          min_confidence: 0.8
          domains: ["ai", "ml"]
      receives:
        - type: ReviewVerdict
          from: bob

    factory:
      provides:
        - type: EntityExtraction
          from_propositions: alice.provides
          model: ceramic://model/entity-v1
      receives:
        - type: Proposition
          from: alice

    bob:
      provides:
        - type: ReviewVerdict
          model: ceramic://model/review-v1
          for: alice.provides
      receives:
        - type: ReputationToken
          amount_per_review: 10

  # Правила валидации
  validation:
    proposition:
      required_fields: [text, entities, temporal, confidence, source_chunk]
      min_entities: 1
      embedding_model: "text-embedding-3-large"
    entity:
      require_resolution: true
      external_ids: ["wikidata"]  # желательно

  # Как данные становятся видимыми
  publication:
    visibility: "contract_members"          # только участники
    promotion_to_public:
      requires: review_verdict.approved
      min_reviews: 2
    composability: true                     # другие контракты могут ссылаться

  # Lifecycle
  duration: "6 months"
  renewal: "auto"
  anchoring: "ethereum"                     # верифицируемый таймстамп
```

### 3.2 Типы Knowledge Contracts

```
KNOWLEDGE CONTRACTS
═══════════════════

DATA CONTRACTS (правила данных)
├── Schema Contract       — "Propositions в этой сети используют модель X"
├── Quality Contract      — "Минимальный confidence 0.8, обязательный source"
├── Privacy Contract      — "Lit Protocol условия для этого домена"
└── Retention Contract    — "Данные хранятся минимум N эпох на Ceramic"

EXCHANGE CONTRACTS (правила обмена)
├── Feed Contract         — "Нода A подписана на propositions ноды B по теме X"
├── Enrichment Contract   — "Factory обогащает propositions entity extraction"
├── Review Contract       — "Рецензент валидирует propositions, получает репутацию"
└── Merge Contract        — "Два графа объединяют entities по таким-то правилам"

COMPUTATION CONTRACTS (правила вычислений)
├── Extraction Pipeline   — "Этот pipeline превращает documents в propositions"
├── Clustering Contract   — "Leiden с resolution=1.0, каждые 1000 новых entities"
├── Summarization Contract— "LLM суммаризация кластеров при > 50 propositions"
└── Inference Contract    — "Sharded inference через Lattica, модель X по шардам Y"

COMPOSITION CONTRACTS (правила композиции)
├── Import Contract       — "Импортировать entities из графа Z с confidence > 0.9"
├── Federation Contract   — "Два Meta-Graph обмениваются communities по теме AI"
├── Fork Contract         — "Форк подграфа с правом изменения, sync обратно"
└── Overlay Contract      — "Наложить свои propositions поверх чужого графа"
```

### 3.3 Как это работает технически

```
Knowledge Contract = Ceramic ComposeDB Model + UCAN Capabilities + Lattica RPC

1. Контракт публикуется как ComposeDB Model на Ceramic
   → Получает StreamID (глобально уникальный)
   → GraphQL schema = формальная спецификация

2. Участники подписывают контракт через DID
   → UCAN tokens выпускаются с capabilities контракта
   → Lit Protocol условия привязываются к контракту

3. Данные текут по правилам контракта
   → Propositions создаются → попадают в Ceramic stream
   → Factory обогащает → entities в Ceramic
   → Lattica RPC координирует real-time обмен
   → IPFS хранит bulk data (документы, модели)

4. Валидация автоматическая
   → Ceramic event → проверка schema
   → UCAN → проверка capabilities
   → Контракт rules → проверка quality (confidence, fields)

5. Composability
   → Другой контракт ссылается на StreamID первого
   → Import/Federation/Overlay по правилам
```

---

## 4. Meta-Graph на Ceramic: конкретные модели

### 4.1 ComposeDB Models для Meta-Graph

```graphql
# ═══ LEVEL 0-1: Documents & Chunks ═══

type Document @createModel(
  accountRelation: LIST
  description: "Raw source document"
) {
  title: String! @string(maxLength: 500)
  mediaType: String! @string(maxLength: 50)    # pdf, audio, video, html
  contentCID: CeramicStreamID!                  # IPFS CID зашифрованного блоба
  litConditions: String @string(maxLength: 5000) # Lit Protocol access conditions
  createdAt: DateTime!
  author: DID!
}

type Chunk @createModel(
  accountRelation: LIST
  description: "Semantic fragment of a document"
) {
  text: String! @string(maxLength: 5000)
  documentID: StreamID! @documentReference(model: "Document")
  document: Document! @relationDocument(property: "documentID")
  position: ChunkPosition!
  embedding: [Float!]! @list(maxLength: 3072)
  createdAt: DateTime!
}

# ═══ LEVEL 2: Propositions & Entities ═══

type Proposition @createModel(
  accountRelation: LIST
  description: "Atomic verifiable fact — base unit of knowledge"
) {
  text: String! @string(maxLength: 2000)
  type: PropositionType!        # factual, temporal, causal, conditional...
  confidence: Float!
  modality: Modality!           # factual, hypothetical, conditional

  # Temporal context (что теряется в триплетах!)
  temporalPoint: DateTime
  temporalRange: [DateTime!] @list(maxLength: 2)
  temporalPrecision: String @string(maxLength: 20)

  # Provenance
  sourceChunkID: StreamID! @documentReference(model: "Chunk")
  sourceChunk: Chunk! @relationDocument(property: "sourceChunkID")
  provenance: String @string(maxLength: 200)

  # Entities mentioned (resolved IDs)
  entityIDs: [StreamID!]! @list(maxLength: 50)

  # Qualifiers
  qualifiers: String @string(maxLength: 2000)   # JSON

  # Semantic search
  embedding: [Float!]! @list(maxLength: 3072)

  createdAt: DateTime!
  author: DID!
}

type Entity @createModel(
  accountRelation: LIST
  description: "Rich node — person, org, concept, model, etc."
) {
  canonicalName: String! @string(maxLength: 200)
  type: EntityType!
  secondaryTypes: [EntityType!] @list(maxLength: 10)
  aliases: [String!]! @list(maxLength: 50)

  # Schema-less properties (JSON)
  properties: String @string(maxLength: 10000)

  # External identifiers
  wikidataID: String @string(maxLength: 20)
  wikipediaSlug: String @string(maxLength: 200)

  # Linked propositions (index)
  propositionIDs: [StreamID!]! @list(maxLength: 10000)

  # Semantic search
  embedding: [Float!]! @list(maxLength: 3072)

  mentionCount: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
  author: DID!
}

type Relation @createModel(
  accountRelation: LIST
  description: "Typed edge between entities"
) {
  fromEntityID: StreamID! @documentReference(model: "Entity")
  toEntityID: StreamID! @documentReference(model: "Entity")
  type: RelationType!         # created_by, successor_of, competes_with...
  properties: String @string(maxLength: 2000)  # JSON
  confidence: Float!
  temporalValidFrom: DateTime
  temporalValidTo: DateTime
  sourcePropositionID: StreamID @documentReference(model: "Proposition")
  author: DID!
}

# ═══ LEVEL 3-5: Clusters, Communities, Themes ═══

type Cluster @createModel(
  accountRelation: LIST
  description: "Local subgraph — group of related entities"
) {
  name: String! @string(maxLength: 200)
  level: Int!                   # 3 = local, 4 = community, 5 = theme
  summary: String! @string(maxLength: 5000)
  entityIDs: [StreamID!]! @list(maxLength: 1000)
  propositionCount: Int!
  externalLinks: [ClusterLink!] @list(maxLength: 100)
  embedding: [Float!]! @list(maxLength: 3072)
  parentClusterID: StreamID @documentReference(model: "Cluster")
  createdAt: DateTime!
  updatedAt: DateTime!
  author: DID!
}
```

### 4.2 Composability в действии

```
Graph A (команда исследователей):
  → Публикует Propositions по модели Proposition-v2
  → Entities по модели Entity-v1
  → Knowledge Contract: "Quality ≥ 0.8, reviewed"

Graph B (AI-фабрика):
  → Подписывается на Feed Contract с Graph A
  → Импортирует Entities + Propositions (тот же ComposeDB model!)
  → Обогащает: extraction → новые relations, clusters
  → Публикует обратно через Enrichment Contract

Graph C (публичный агрегатор):
  → Federation Contract с A и B
  → Видит composable dataset:
    все Propositions от A + enrichments от B
  → Строит Communities и Themes
  → Публикует как открытый Knowledge Graph

Результат: три независимых участника, нет центрального сервера,
данные composable через общие ComposeDB модели.
```

---

## 5. Web2 ↔ Web3 бимодальность

Каждый компонент имеет Web2-эквивалент. Приложение не знает через что работает.

```
Layer 0 Storage:
  Web2: S3 + PostgreSQL + content hashing
  Web3: IPFS + IPLD + Content-Addressed Nix Store

Layer 1 Communication:
  Web2: NATS + gRPC + WebSocket
  Web3: Lattica (P2P mesh + RPC + CRDT)

Layer 2 Mutable Data:
  Web2: PostgreSQL + event sourcing
  Web3: Ceramic + ComposeDB + OrbisDB

Layer 3 Access:
  Web2: JWT + OAuth + server-side encryption
  Web3: DID + UCAN + Lit Protocol

Layer 4 Meta-Graph:
  Web2: Neo4j + Qdrant + local graph
  Web3: ComposeDB models + IPLD links + distributed graph

Layer 5 Agents:
  Web2: NATS workers + systemd (oblakagent)
  Web3: Lattica RPC + Ceramic events + P2P coordination

Layer 6 Contracts:
  Web2: API agreements + OpenAPI specs + rate limits
  Web3: Knowledge Contracts (ComposeDB models + UCAN + Lit)
```

Transport Adapter pattern: единый интерфейс, разный backend.

---

## 6. Factory на этом стеке

```
ЗАДАЧА: "Создать landing page для продукта X"

1. COMPASS Meta-Thinker
   └─ Читает контекст из Ceramic ComposeDB (GraphQL)
      → Предыдущие проекты, паттерны, knowledge graph
      → Кластер "Landing Pages" → суммари → стратегия

2. MAKER декомпозиция
   └─ Каждый микрошаг = Ceramic event (Proposition с type=task)
      → Верифицируемый audit trail
      → UCAN capability на каждого агента

3. AI-агенты работают
   └─ Claude Code / Aider в sandboxai Cell
      → stdout стримится через Lattica RPC
      → Координация через Lattica CRDT (статусы, прогресс)
      → Артефакты (код) → IPFS (CID)

4. Результат публикуется
   └─ Код → IPFS → CID записывается в Ceramic stream проекта
      → Docker/OCI image → IPFS Bitswap (децентрализованный CDN)
      → Deploy через nn3w (Nix + deploy-rs)
      → Binary cache через IPFS

5. Knowledge System обновляется
   └─ ComposeDB: новые Propositions
      "Factory создала landing page для продукта X за 7 минут,
       использовала шаблон Y, модель Z, confidence 0.95"
      → Другие Factory-ноды учатся (composability)
      → Clustering обновляется
      → Communities пересчитываются
```

---

## 7. Самовоспроизводящийся цикл

```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  ┌──────────┐    спецификация    ┌──────────────────┐   │
│  │ Knowledge│───────────────────▶│     Factory       │   │
│  │  Graph   │                    │  (AI-агенты)      │   │
│  │(Ceramic) │◀───────────────────│                    │   │
│  └──────────┘   новые знания     └────────┬─────────┘   │
│       ▲                                    │              │
│       │                                    │ код          │
│       │ опыт                               ▼              │
│  ┌──────────┐                    ┌──────────────────┐   │
│  │  DSPy    │◀───────────────────│    sandboxai      │   │
│  │Optimizer │   метрики          │   (Cell/Nix)      │   │
│  └──────────┘                    └────────┬─────────┘   │
│                                           │              │
│                                           │ артефакты    │
│                                           ▼              │
│                                  ┌──────────────────┐   │
│                                  │   nn3w / vladOS   │   │
│                                  │  (Nix deploy)     │   │
│                                  └────────┬─────────┘   │
│                                           │              │
│                                           │ IPFS CID     │
│                                           ▼              │
│                                  ┌──────────────────┐   │
│                                  │   IPFS + Ceramic  │   │
│                                  │  (хранение +      │   │
│                                  │   публикация)     │   │
│                                  └──────────────────┘   │
│                                                          │
│  Каждый цикл: Factory становится умнее,                 │
│  Knowledge Graph богаче, Optimizer точнее.                │
│  Autopoietic system — производит компоненты              │
│  для собственного воспроизводства.                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Сравнение с существующими подходами

| Аспект | Ethereum | Ceramic only | nn3w Meta-Graph |
|:-------|:--------:|:------------:|:---------------:|
| Единица данных | Transaction | Stream event | **Proposition** |
| Composability | Smart contracts | ComposeDB models | **Knowledge Contracts** |
| Identity | Wallet address | DID | **DID + UCAN chain** |
| Запросы | Events/logs | GraphQL | **GraphQL + Vector + Graph** |
| AI-native | Нет | Нет | **COMPASS + MAKER + DSPy** |
| Мутабельные данные | Нет (append-only) | Да (streams) | **Да + temporal context** |
| Real-time | Нет (blocks) | Ограничено | **Lattica RPC + CRDT** |
| Шифрование | Нет | Через Lit | **Lit + UCAN (два уровня)** |
| Storage | On-chain (дорого) | IPFS | **IPFS + Nix CA store** |
| Self-improvement | Нет | Нет | **DSPy optimizers** |

---

## 9. Ключевые ссылки и источники

### Исследования (arxiv)

| Paper | Релевантность |
|:------|:-------------|
| Lattica (2510.00183) | P2P mesh для AI, CRDT + DHT |
| Reproducible Builds (2104.06020) | Content-addressed supply chain |
| Self-verifiable IPFS + DID (2105.08395) | Мутабельный контент через DID |
| SWE-Gym (2412.21139) | Тренировка SWE-агентов |
| Context Engineering Multi-Agent (2508.08322) | Multi-agent code generation |
| PropRAG (EMNLP 2025) | Propositions > Triples для RAG |
| SlimRAG (2025) | Similarity ≠ Relevance |

### Технологии

| Технология | Роль в стеке |
|:-----------|:------------|
| IPFS + IPLD | Layer 0: immutable content-addressed storage |
| Lattica (Gradient) | Layer 1: P2P communication for AI |
| Ceramic + ComposeDB | Layer 2: mutable structured data |
| OrbisDB | Layer 2: SQL interface to Ceramic |
| DID + UCAN | Layer 3: decentralized identity + authorization |
| Lit Protocol | Layer 3: threshold encryption |
| Nix + Den | Infrastructure: reproducible, aspect-oriented |
| Bacalhau | Compute-over-data on IPFS |
| Unison | Content-addressed code (conceptual reference) |
| Holochain | Agent-centric DHT (alternative architecture) |

### Проекты экосистемы nn3w

| Проект | Роль |
|:-------|:-----|
| nn3w | Nix infrastructure (Den + Clan + deploy) |
| sandboxai (NixBox) | Isolated environments (Cell + Supervisor) |
| oblakagent | Self-hosted AI agent runtime |
| nixvimde | AI-IDE с Context Provider |
| COMPASS_MAKER | AI agent strategy + reliability |
| factory-ai-framework | Grand Architecture (vladOS + sandboxai + Factory) |
| myaiteam | Knowledge System design + team OS |

---

## 10. Roadmap

### Phase 0: Фундамент (сейчас)
- [x] nn3w на Den (миграция с Snowfall Lib)
- [x] Архитектура Meta-Graph (myaiteam docs)
- [x] COMPASS + MAKER дизайн
- [ ] Den aspects для IPFS node, Ceramic node

### Phase 1: Минимальный Meta-Graph
- [ ] ComposeDB модели: Proposition, Entity, Relation
- [ ] ML Pipeline: Document → Chunks → Propositions → Entities
- [ ] Локальный кэш: Qdrant (vectors) + SurrealDB (graph)
- [ ] CLI для ingestion и query

### Phase 2: P2P Communication
- [ ] Lattica SDK интеграция (Python)
- [ ] Transport Adapter: NATS (Web2) ↔ Lattica (Web3)
- [ ] CRDT state для координации агентов
- [ ] oblakagent → Lattica RPC для стриминга

### Phase 3: Knowledge Contracts
- [ ] Schema Contract: общие ComposeDB модели
- [ ] Feed Contract: подписка между графами
- [ ] Enrichment Contract: Factory обогащает propositions
- [ ] UCAN capability management

### Phase 4: Self-Reproducing Factory
- [ ] Factory полный цикл: задача → код → deploy → knowledge update
- [ ] DSPy optimizer loop
- [ ] Composability: несколько Factory-нод обмениваются знаниями
- [ ] Ouroboros-подобный self-improvement

### Phase 5: Federation
- [ ] Inter-Graph protocols
- [ ] Community-level Federation Contracts
- [ ] Public Knowledge Graph (opt-in composability)
- [ ] Reputation system (review contracts)
