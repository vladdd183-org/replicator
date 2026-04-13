# 🏗️ Обзор архитектуры системы

> **Связанные документы:**
> - [Knowledge Graph Design](knowledge-graph.md)
> - [Decentralized Stack](decentralized-stack.md)
> - [Privacy & Access Control](privacy-access.md)
> - [Human-AI Collaboration](human-ai-collab.md)

---

## 1. Философия архитектуры

### 1.1 Ключевые принципы

| Принцип | Описание |
|---------|----------|
| **File-First** | Всё существует как файл. БД — это кэш для скорости |
| **Links = Graph** | Граф возникает из ссылок, а не проектируется заранее |
| **Context Never Lost** | Любой элемент сохраняет связь с источником |
| **Emergent Abstraction** | Высокоуровневые концепции возникают из анализа связей |
| **Decentralization-First** | Централизованные решения — только как кэш |

### 1.2 Цели системы

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ЦЕЛИ СИСТЕМЫ                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ДЛЯ ЧЕЛОВЕКА:                                                      │
│  ├── Читаемость — понятно без специальных инструментов              │
│  ├── Навигируемость — легко найти нужное                            │
│  └── Контроль — приватность и владение данными                      │
│                                                                     │
│  ДЛЯ AI/LLM:                                                        │
│  ├── Структурированность — эффективный retrieval                    │
│  ├── Контекстность — понимание связей                               │
│  └── Reasoning — возможность делать выводы                          │
│                                                                     │
│  ДЛЯ СИСТЕМЫ:                                                       │
│  ├── Универсальность — любые типы данных                            │
│  ├── Расширяемость — легко добавлять новое                          │
│  └── Трассируемость — каждый факт связан с источником               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Многослойная архитектура

### 2.1 Полный стек системы

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         SYSTEM ARCHITECTURE                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 6: APPLICATION                                                   │  ║
║  │  ├── UI: Obsidian-like interface, Web dashboard                         │  ║
║  │  ├── AI Agents: Research, Extraction, Synthesis                         │  ║
║  │  └── APIs: REST, GraphQL, MCP                                           │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 5: HUMAN-AI COLLABORATION                                        │  ║
║  │  ├── Task Allocation: Who does what                                     │  ║
║  │  ├── Trust Calibration: Confidence scores                               │  ║
║  │  ├── Shared Context: Common understanding                               │  ║
║  │  └── Escalation: When to involve human                                  │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 4: QUERY & RETRIEVAL                                             │  ║
║  │  ├── Vector Search: Semantic similarity (Qdrant, ChromaDB)              │  ║
║  │  ├── Graph Queries: Traversal, patterns (Neo4j, SPARQL)                 │  ║
║  │  ├── Full-text: Keyword search (MeiliSearch, Typesense)                 │  ║
║  │  └── RAG: GraphRAG, LightRAG, RAPTOR                                    │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 3: KNOWLEDGE GRAPH                                               │  ║
║  │  ├── Atoms: Entities, Claims, Chunks (Level 0-1)                        │  ║
║  │  ├── Clusters: Local groups (Level 2)                                   │  ║
║  │  ├── Communities: Semantic domains (Level 3)                            │  ║
║  │  ├── Themes: Global topics (Level 4)                                    │  ║
║  │  └── Relations: Typed, weighted, contextual                             │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 2: ACCESS CONTROL                                                │  ║
║  │  ├── Authorization: UCAN (who CAN do what)                              │  ║
║  │  ├── Encryption: Lit Protocol (who can READ)                            │  ║
║  │  └── Identity: DIDs (decentralized identifiers)                         │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 1: DECENTRALIZED STORAGE                                         │  ║
║  │  ├── Content Storage: IPFS (content-addressed blobs)                    │  ║
║  │  ├── Linked Data: IPLD (graph of CIDs)                                  │  ║
║  │  ├── Mutable Pointers: IPNS (updateable references)                     │  ║
║  │  ├── Structured Data: Ceramic/ComposeDB (schemas, queries)              │  ║
║  │  └── Real-time: OrbitDB/PubSub (collaboration)                          │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  LAYER 0: ML PIPELINE                                                   │  ║
║  │  ├── Embeddings: OpenAI, sentence-transformers                          │  ║
║  │  ├── Entity Extraction: GLiNER, spaCy, LLM                              │  ║
║  │  ├── Transcription: Whisper (audio → text)                              │  ║
║  │  ├── OCR: Tesseract, PaddleOCR (images → text)                          │  ║
║  │  └── LLM: GPT, Claude, local models                                     │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 2.2 Взаимодействие слоёв

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT DATA                                                                 │
│  (PDF, Audio, Video, Text, Tables)                                          │
│         │                                                                   │
│         ▼                                                                   │
│  ┌──────────────────┐                                                       │
│  │  ML PIPELINE     │ → Transcription, OCR, Embeddings, Entity Extraction  │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │  KNOWLEDGE GRAPH │ → Atoms, Relations, Clusters, Communities            │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │  ACCESS CONTROL  │ → Encryption, Authorization check                    │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │  DECENTRALIZED   │ → IPFS (storage), Ceramic (metadata), IPNS (pointers)│
│  │  STORAGE         │                                                       │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │  QUERY LAYER     │ → Vector search, Graph queries, RAG                  │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │  HUMAN-AI        │ → Task allocation, Trust calibration                 │
│  │  COLLABORATION   │                                                       │
│  └────────┬─────────┘                                                       │
│           │                                                                 │
│           ▼                                                                 │
│  ┌──────────────────┐                                                       │
│  │  APPLICATION     │ → UI, AI Agents, APIs                                │
│  └──────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Ключевые подсистемы

### 3.1 Knowledge Graph

**Подробнее:** [knowledge-graph.md](knowledge-graph.md)

| Компонент | Описание |
|-----------|----------|
| **Semantic Units** | Альтернатива триплетам — осмысленные блоки с контекстом |
| **Multi-level Hierarchy** | Atoms → Clusters → Communities → Themes |
| **Typed Relations** | Семантические, причинные, временные, эпистемические |
| **Embeddings** | Гиперболические для иерархий, евклидовы для плоских |

### 3.2 Decentralized Storage

**Подробнее:** [decentralized-stack.md](decentralized-stack.md)

| Компонент | Роль |
|-----------|------|
| **IPFS** | Хранение зашифрованных blob'ов |
| **IPLD** | Связывание объектов через CID |
| **Ceramic** | Мутабельные структурированные данные |
| **OrbitDB** | Real-time collaboration с CRDTs |

### 3.3 Access Control

**Подробнее:** [privacy-access.md](privacy-access.md)

| Компонент | Функция |
|-----------|---------|
| **UCAN** | "Кто МОЖЕТ делать" — capability-based auth |
| **Lit Protocol** | "Кто может ЧИТАТЬ" — decentralized encryption |
| **DIDs** | Децентрализованная идентификация |

### 3.4 Human-AI Collaboration

**Подробнее:** [human-ai-collab.md](human-ai-collab.md)

| Компонент | Назначение |
|-----------|------------|
| **Mental Models** | Понимание как AI работает |
| **Task Allocation** | Кто что делает лучше |
| **Trust Calibration** | Уровни уверенности |
| **Escalation** | Когда передавать человеку |

---

## 4. Выбор технологий

### 4.1 Decision Matrix

| Сценарий | Рекомендуемый стек |
|----------|-------------------|
| **Личная база знаний** | IPFS + IPNS + локальный кэш |
| **Командная работа** | IPFS + Ceramic + Lit + UCAN + PubSub |
| **Real-time collaboration** | OrbitDB + Automerge/Yjs |
| **Enterprise** | Ceramic + ComposeDB + IPFS Cluster |

### 4.2 Компоненты по функциям

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPONENT SELECTION GUIDE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STORAGE:                                                           │
│  ├── Raw files: IPFS                                                │
│  ├── Structured data: Ceramic + ComposeDB                           │
│  ├── Real-time state: OrbitDB                                       │
│  └── Mutable pointers: IPNS                                         │
│                                                                     │
│  PRIVACY:                                                           │
│  ├── Encryption: Lit Protocol                                       │
│  ├── Authorization: UCAN                                            │
│  └── Identity: DIDs (did:key, did:web)                              │
│                                                                     │
│  KNOWLEDGE GRAPH:                                                   │
│  ├── Local cache: SurrealDB, Neo4j, DGraph                          │
│  ├── Vector search: Qdrant, Milvus, ChromaDB                        │
│  └── Full-text: MeiliSearch, Typesense                              │
│                                                                     │
│  RAG SYSTEMS:                                                       │
│  ├── Complex QA: GraphRAG (Microsoft)                               │
│  ├── Fast retrieval: LightRAG                                       │
│  ├── Long documents: RAPTOR                                         │
│  └── Domain-specific: TagRAG                                        │
│                                                                     │
│  AI AGENTS:                                                         │
│  ├── Orchestration: LangGraph, CrewAI                               │
│  ├── Protocols: MCP, A2A                                            │
│  └── Models: GPT-4, Claude, local LLMs                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Ключевые потоки данных

### 5.1 Добавление нового документа

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLOW: Добавление документа в систему                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. UCAN CHECK                                                      │
│     → Проверка прав на запись                                       │
│                                                                     │
│  2. ML PROCESSING                                                   │
│     → OCR/Transcription → Chunking → Entity Extraction → Embeddings │
│                                                                     │
│  3. KNOWLEDGE GRAPH                                                 │
│     → Create Atoms → Link to existing entities → Update clusters    │
│                                                                     │
│  4. ENCRYPTION (Lit Protocol)                                       │
│     → Encrypt content with access conditions                        │
│                                                                     │
│  5. STORAGE                                                         │
│     → IPFS: encrypted blob → CID                                    │
│     → Ceramic: metadata record                                      │
│     → IPNS: update pointer                                          │
│                                                                     │
│  6. NOTIFICATION                                                    │
│     → PubSub: notify subscribers                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Поиск и retrieval

```
┌─────────────────────────────────────────────────────────────────────┐
│  FLOW: Поиск информации                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. QUERY ANALYSIS                                                  │
│     → Embed query → Determine search type (semantic/exact/graph)    │
│                                                                     │
│  2. MULTI-MODAL RETRIEVAL                                           │
│     → Vector search (semantic) + Graph traversal + Full-text        │
│                                                                     │
│  3. ACCESS CHECK                                                    │
│     → Filter results by user's access rights                        │
│                                                                     │
│  4. DECRYPTION (Lit Protocol)                                       │
│     → Decrypt accessible content                                    │
│                                                                     │
│  5. CONTEXT ASSEMBLY (RAG)                                          │
│     → Build context from relevant atoms/chunks                      │
│                                                                     │
│  6. GENERATION/DISPLAY                                              │
│     → LLM generation OR direct display                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Навигация

| Следующий документ | Тема |
|--------------------|------|
| → [knowledge-graph.md](knowledge-graph.md) | Дизайн графа знаний |
| → [decentralized-stack.md](decentralized-stack.md) | Децентрализованный стек |
| → [privacy-access.md](privacy-access.md) | Приватность и доступ |
| → [human-ai-collab.md](human-ai-collab.md) | Human-AI взаимодействие |

---

*Источники: Ultimate-Knowledge-Graph-Architecture-Guide.md, Decentralized-Knowledge-Stack-Guide.md*
