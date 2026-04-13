# 📊 Архитектура Knowledge Graph

> **Связанные документы:**
> - [Architecture Overview](overview.md)
> - [Concepts: Knowledge Representation](../concepts/knowledge-representation.md)
> - [Reference: Relation Types](../reference/relation-types.md)

---

## 1. Философия: Почему НЕ триплеты

### 1.1 Фундаментальные проблемы триплетов

Классические Knowledge Graphs используют триплеты `(Subject, Predicate, Object)`.
**Это плохо по нескольким причинам:**

| Проблема | Описание | Пример |
|----------|----------|--------|
| **Context Collapse** | Триплеты теряют контекст, условия, нюансы | "X уволил 500 человек" теряет причину и дату |
| **Forced Binarization** | N-арные факты требуют искусственных узлов | 5-стороннее соглашение → 10+ триплетов |
| **Semantic Similarity ≠ Relevance** | "Waiter" и "Waitress" похожи, но для вопроса о поле релевантно "Male" |
| **Brittleness** | Изменение схемы ломает весь граф | Добавление поля → миграция данных |
| **Cognitive Overhead** | Нечитаемо для человека | Граф из 1000 триплетов vs 50 пропозиций |

### 1.2 Что говорит наука (2024-2025)

**PropRAG (EMNLP 2025):**
> "Triples suffer from context collapse — a lossy compression that discards conditionality, provenance, and n-ary relationships"

**Dense-X Retrieval (EMNLP 2024):**
> "Propositions significantly outperform both passage and sentence-based retrieval... more condensed with query-relevant information"

**SlimRAG (2025):**
> "Semantic similarity does not imply semantic relevance... Graph-based methods face fundamental challenges"

---

## 2. Наш подход: Гетерогенный Метаграф

### 2.1 Общая архитектура

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        HETEROGENEOUS META-GRAPH                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │ LAYER 5: GLOBAL THEMES (абстракции)                                     │  ║
║  │ ┌───────────┐  ┌───────────┐  ┌───────────┐                             │  ║
║  │ │ AI & ML   │──│ FinTech   │──│ Research  │  ← LLM-суммаризации        │  ║
║  │ └───────────┘  └───────────┘  └───────────┘    кластеров               │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                              ▲ aggregation                                    ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │ LAYER 4: COMMUNITIES (домены)                                           │  ║
║  │ ┌─────────────────────────────────┐  ┌─────────────────────────────┐    │  ║
║  │ │  "LLM Research Papers"          │  │  "Crypto Transactions"      │    │  ║
║  │ │  summary: "..."                 │  │  summary: "..."             │    │  ║
║  │ │  entities: [gpt-4, claude, ...] │  │  entities: [btc, eth, ...]  │    │  ║
║  │ └─────────────────────────────────┘  └─────────────────────────────┘    │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                              ▲ Leiden clustering                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │ LAYER 3: ENTITY CLUSTERS (локальные подграфы)                           │  ║
║  │ ┌────────────────────────────────────────────────────┐                  │  ║
║  │ │  Cluster: "GPT-4 Capabilities"                     │                  │  ║
║  │ │  ┌─────────────┐       ┌─────────────┐             │                  │  ║
║  │ │  │ ent:GPT-4   │──────▶│ ent:OpenAI  │             │                  │  ║
║  │ │  └──────┬──────┘       └─────────────┘             │                  │  ║
║  │ │         │ supports                                 │                  │  ║
║  │ │         ▼                                          │                  │  ║
║  │ │  ┌─────────────────────────────────────────────┐  │                  │  ║
║  │ │  │ prop: "GPT-4 passes bar exam with 90%"      │  │                  │  ║
║  │ │  └─────────────────────────────────────────────┘  │                  │  ║
║  │ └────────────────────────────────────────────────────┘                  │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                              ▲ entity linking                                 ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │ LAYER 2: ENTITIES + PROPOSITIONS (богатые единицы)                      │  ║
║  │                                                                          │  ║
║  │  ┌──────────────────────────────────────────────────────────────────┐   │  ║
║  │  │ PROPOSITION (атомарная единица знания)                           │   │  ║
║  │  │ ──────────────────────────────────────────────────────────────── │   │  ║
║  │  │ id: prop_12345                                                   │   │  ║
║  │  │ text: "OpenAI выпустила GPT-4 в марте 2023 года"                 │   │  ║
║  │  │ ────────────────────────────────────────────────                 │   │  ║
║  │  │ entities: [ent:OpenAI, ent:GPT-4]                                │   │  ║
║  │  │ temporal: 2023-03                                                │   │  ║
║  │  │ confidence: 0.98                                                 │   │  ║
║  │  │ source: chunk_789                                                │   │  ║
║  │  │ embedding: [0.12, 0.34, ...]                                     │   │  ║
║  │  │ ────────────────────────────────────────────────                 │   │  ║
║  │  │ qualifiers:                                                      │   │  ║
║  │  │   - event_type: "product_release"                                │   │  ║
║  │  │   - provenance: "official_announcement"                          │   │  ║
║  │  └──────────────────────────────────────────────────────────────────┘   │  ║
║  │                                                                          │  ║
║  │  ┌──────────────────────────────────────────────────────────────────┐   │  ║
║  │  │ ENTITY (богатый узел)                                            │   │  ║
║  │  │ ──────────────────────────────────────────────────────────────── │   │  ║
║  │  │ id: ent_gpt4                                                     │   │  ║
║  │  │ canonical_name: "GPT-4"                                          │   │  ║
║  │  │ type: [AI_Model, LLM, Product]                                   │   │  ║
║  │  │ aliases: ["gpt4", "gpt-4-turbo", "gpt4o"]                        │   │  ║
║  │  │ ────────────────────────────────────────────────                 │   │  ║
║  │  │ properties:                                                      │   │  ║
║  │  │   parameters: "1.7T (estimated)"                                 │   │  ║
║  │  │   release_date: 2023-03-14                                       │   │  ║
║  │  │   creator: ent:OpenAI                                            │   │  ║
║  │  │ ────────────────────────────────────────────────                 │   │  ║
║  │  │ linked_propositions: [prop_12345, prop_12346, ...]               │   │  ║
║  │  │ embedding: [0.56, 0.78, ...]                                     │   │  ║
║  │  │ external_ids:                                                    │   │  ║
║  │  │   wikidata: Q115753512                                           │   │  ║
║  │  └──────────────────────────────────────────────────────────────────┘   │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                              ▲ extraction                                     ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │ LAYER 1: CHUNKS (сырые фрагменты)                                       │  ║
║  │ ┌──────────────────────────────────────────────────────────────────┐    │  ║
║  │ │ chunk_789                                                         │    │  ║
║  │ │ text: "On March 14, 2023, OpenAI announced GPT-4, their most     │    │  ║
║  │ │        capable model to date. The model demonstrates remarkable   │    │  ║
║  │ │        capabilities including passing the bar exam..."            │    │  ║
║  │ │ source: doc_openai_blog                                           │    │  ║
║  │ │ position: {start: 1200, end: 1800}                                │    │  ║
║  │ │ embedding: [...]                                                  │    │  ║
║  │ └──────────────────────────────────────────────────────────────────┘    │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                              ▲ chunking                                       ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │ LAYER 0: RAW DOCUMENTS                                                  │  ║
║  │ PDF, HTML, Audio, Video, Images, Tables...                              │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### 2.2 Ключевые принципы

| Принцип | Описание |
|---------|----------|
| **Propositions > Triples** | Атомарные утверждения на естественном языке вместо (S,P,O) |
| **Rich Nodes** | Каждый узел — контейнер со свойствами, типами, связями |
| **Nested Subgraphs** | Кластеры и сообщества — это подграфы с метаданными |
| **Maximal Connectivity** | На низком уровне связываем всё что можно |
| **Progressive Abstraction** | Выше → более абстрактно и сжато |
| **Entity-Centric Indexing** | Быстрый доступ: Entity → Propositions → Chunks |

---

## 3. Базовая единица: Proposition (не триплет!)

### 3.1 Что такое Proposition

**Proposition** — атомарное, самодостаточное утверждение на естественном языке, которое:
- Содержит ровно один факт
- Сохраняет контекст (время, условия, источник)
- Связано с сущностями которые упоминает
- Имеет embedding для семантического поиска

```yaml
# ❌ ПЛОХО: Триплет
(GPT-4, released_by, OpenAI)
# Где дата? Где источник? Где контекст?

# ✅ ХОРОШО: Proposition
proposition:
  id: prop_gpt4_release
  text: "OpenAI выпустила GPT-4 14 марта 2023 года"
  
  # Связанные сущности (автоматически извлечены)
  entities:
    - id: ent_openai
      role: agent
      span: [0, 6]
    - id: ent_gpt4
      role: product
      span: [16, 21]
  
  # Контекст (то что теряется в триплетах)
  temporal:
    point: 2023-03-14
    precision: day
  
  # Метаданные
  confidence: 0.98
  source_chunk: chunk_789
  provenance: "official_announcement"
  
  # Для поиска
  embedding: [0.12, 0.34, ...]
  
  # Квалификаторы для сложных случаев
  qualifiers:
    event_type: product_release
    modality: factual  # vs hypothetical, conditional
```

### 3.2 Типы Propositions

| Тип | Описание | Пример |
|-----|----------|--------|
| **Factual** | Конкретный факт | "GPT-4 имеет 1.7T параметров" |
| **Temporal** | Событие во времени | "OpenAI основана в 2015 году" |
| **Relational** | Связь между сущностями | "Sam Altman — CEO OpenAI" |
| **Attributive** | Свойство сущности | "GPT-4 мультимодальный" |
| **Causal** | Причинно-следственная связь | "GPT-4 обучен на большем датасете, поэтому умнее" |
| **Conditional** | Условное утверждение | "При temperature=0 GPT-4 детерминирован" |
| **Comparative** | Сравнение | "GPT-4 превосходит GPT-3.5 на 40% в reasoning" |

### 3.3 Извлечение Propositions (LLM Pipeline)

```python
EXTRACTION_PROMPT = """
Extract atomic propositions from the text.

Rules:
1. Each proposition = ONE self-contained fact
2. Preserve temporal context (dates, periods)
3. Preserve conditional context (if, when, unless)
4. Preserve source attribution (according to, as stated by)
5. Mark entities with <e>entity</e> tags
6. Output as JSON array

Text: {chunk_text}

Output format:
[
  {
    "text": "proposition text with <e>entities</e>",
    "type": "factual|temporal|relational|...",
    "confidence": 0.0-1.0,
    "temporal": {"point": "...", "range": [...], "precision": "..."},
    "modality": "factual|hypothetical|conditional"
  }
]
"""
```

---

## 4. Entity как богатый узел

### 4.1 Структура Entity

```yaml
entity:
  # Идентификация
  id: ent_gpt4
  canonical_name: "GPT-4"
  type: 
    primary: AI_Model
    secondary: [LLM, Product, Technology]
  
  # Альтернативные названия (для resolution)
  aliases:
    - text: "gpt-4"
      frequency: 1250
    - text: "GPT4"
      frequency: 340
    - text: "gpt-4-turbo"
      frequency: 89
    - text: "gpt4o"
      frequency: 567
  
  # Свойства (schema-less, любые key-value)
  properties:
    parameters: "~1.7T (estimated)"
    context_window: 128000
    training_cutoff: "2023-12"
    pricing_input: "$0.01/1K tokens"
    pricing_output: "$0.03/1K tokens"
    modalities: ["text", "vision", "audio"]
  
  # Связи с другими сущностями
  relations:
    - target: ent_openai
      type: created_by
      props: {announced: "2023-03-14"}
    - target: ent_gpt35
      type: successor_of
      props: {improvement: "40% on reasoning"}
    - target: ent_claude
      type: competes_with
  
  # Индекс: какие propositions упоминают эту сущность
  proposition_index:
    - prop_gpt4_release
    - prop_gpt4_capabilities
    - prop_gpt4_pricing
    # ... (может быть тысячи)
  
  # Внешние идентификаторы
  external_ids:
    wikidata: Q115753512
    wikipedia: "GPT-4"
    crunchbase: "gpt-4"
  
  # Embedding для семантического поиска
  embedding: [0.56, 0.78, ...]
  
  # Метаданные
  created_at: 2024-01-15T10:30:00Z
  updated_at: 2024-06-20T15:45:00Z
  mention_count: 2847
```

### 4.2 Entity Types (гетерогенность)

```
ENTITY TYPES
├── NAMED ENTITIES
│   ├── Person (люди)
│   ├── Organization (компании, институты)
│   ├── Location (места)
│   ├── Product (продукты, сервисы)
│   └── Event (конференции, релизы)
│
├── DOMAIN ENTITIES  
│   ├── AI_Model (GPT-4, Claude, Llama)
│   ├── Technology (Transformer, RLHF)
│   ├── Dataset (CommonCrawl, RedPajama)
│   ├── Metric (MMLU, HumanEval)
│   └── Paper (arXiv papers)
│
├── ABSTRACT CONCEPTS
│   ├── Concept (decentralization, attention)
│   ├── Method (fine-tuning, RAG)
│   └── Theory (scaling laws)
│
└── STRUCTURAL
    ├── Document (источник)
    ├── Chunk (фрагмент)
    └── Cluster (группа)
```

---

## 5. Вложенные подграфы (Nested Subgraphs)

### 5.1 Концепция

Каждый **кластер** — это не просто набор узлов, а **полноценный подграф** со своими:
- Метаданными
- Суммаризацией
- Внутренними связями
- Границами (что внутри, что снаружи)

```
┌─────────────────────────────────────────────────────────────────┐
│ CLUSTER: "OpenAI Language Models"                               │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                 │
│  metadata:                                                      │
│    id: cluster_openai_llm                                       │
│    level: 3 (local cluster)                                     │
│    created: 2024-01-15                                          │
│    entity_count: 12                                             │
│    proposition_count: 847                                       │
│                                                                 │
│  summary: "Семейство языковых моделей OpenAI включает GPT-3,   │
│            GPT-3.5, GPT-4 и их вариации. Модели демонстрируют   │
│            прогрессивное улучшение capabilities..."              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   INTERNAL GRAPH                         │   │
│  │                                                          │   │
│  │    [GPT-3] ──successor_of──▶ [GPT-3.5]                  │   │
│  │       │                          │                       │   │
│  │       │                          │ successor_of          │   │
│  │       │                          ▼                       │   │
│  │       │                      [GPT-4]                     │   │
│  │       │                          │                       │   │
│  │       └─────── all created_by ───┼──▶ [OpenAI]          │   │
│  │                                  │                       │   │
│  │                          [GPT-4 Turbo]                   │   │
│  │                          [GPT-4o]                        │   │
│  │                          [GPT-4o-mini]                   │   │
│  │                                                          │   │
│  │   + 847 propositions linking these entities              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  external_links:                                                │
│    - → cluster_anthropic_llm (competes_with)                   │
│    - → cluster_ai_safety (concerns)                            │
│    - → cluster_enterprise_ai (use_case)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Иерархия вложенности

```
LEVEL 5: Global Theme
└── LEVEL 4: Community
    └── LEVEL 3: Local Cluster
        └── LEVEL 2: Entity + Propositions
            └── LEVEL 1: Chunk
                └── LEVEL 0: Raw Document

Пример:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
theme: "Artificial Intelligence"
└── community: "Large Language Models"
    ├── cluster: "OpenAI Models"
    │   ├── entity: GPT-4
    │   │   ├── prop: "GPT-4 выпущен в марте 2023"
    │   │   │   └── chunk_789 (source)
    │   │   ├── prop: "GPT-4 имеет 128K контекст"
    │   │   └── prop: "GPT-4 стоит $0.03 за 1K output"
    │   ├── entity: GPT-3.5
    │   └── entity: OpenAI
    │
    ├── cluster: "Anthropic Models"
    │   ├── entity: Claude-3
    │   └── entity: Anthropic
    │
    └── cluster: "Open Source Models"
        ├── entity: Llama-3
        └── entity: Mistral
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 6. Система индексирования

### 6.1 Entity-Centric Index (как SlimRAG, но богаче)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                         MULTI-LEVEL INDEX                                  ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ENTITY INDEX (primary)                                                    ║
║  ──────────────────────────────────────────────────────────────────────── ║
║  entity_id → {                                                             ║
║    propositions: [prop_1, prop_2, ...],      # Где упоминается            ║
║    chunks: [chunk_1, chunk_2, ...],          # Источники                  ║
║    clusters: [cluster_1, ...],               # Принадлежность             ║
║    related_entities: [ent_1, ent_2, ...],    # Связанные                  ║
║  }                                                                         ║
║                                                                            ║
║  PROPOSITION INDEX                                                         ║
║  ──────────────────────────────────────────────────────────────────────── ║
║  prop_id → {                                                               ║
║    entities: [ent_1, ent_2],                 # Упомянутые сущности        ║
║    source_chunk: chunk_id,                   # Откуда извлечено           ║
║    cluster: cluster_id,                      # В каком кластере           ║
║  }                                                                         ║
║                                                                            ║
║  CHUNK INDEX                                                               ║
║  ──────────────────────────────────────────────────────────────────────── ║
║  chunk_id → {                                                              ║
║    propositions: [prop_1, ...],              # Извлечённые пропозиции     ║
║    entities: [ent_1, ...],                   # Упомянутые сущности        ║
║    document: doc_id,                         # Источник                   ║
║  }                                                                         ║
║                                                                            ║
║  VECTOR INDEXES (для семантического поиска)                               ║
║  ──────────────────────────────────────────────────────────────────────── ║
║  entity_vectors: HNSW index                                                ║
║  proposition_vectors: HNSW index                                           ║
║  chunk_vectors: HNSW index                                                 ║
║  cluster_summary_vectors: HNSW index                                       ║
║                                                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### 6.2 Query Flow

```
QUERY: "Какие возможности у GPT-4?"
          │
          ▼
┌─────────────────────────────────────┐
│ 1. ENTITY EXTRACTION                │
│    → entities: ["GPT-4"]            │
│    → query_type: "capabilities"     │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ 2. ENTITY RESOLUTION                │
│    "GPT-4" → ent_gpt4               │
│    (match by alias index)           │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ 3. PROPOSITION RETRIEVAL            │
│    ent_gpt4.propositions            │
│    → filter by semantic relevance   │
│    → "capabilities" embedding match │
│    → top_k propositions             │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ 4. CONTEXT EXPANSION                │
│    → related entities (OpenAI,...)  │
│    → cluster summary                │
│    → supporting chunks if needed    │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ 5. CONTEXT ASSEMBLY                 │
│    propositions + cluster_summary   │
│    → ranked by relevance            │
│    → token budget aware             │
└──────────────┬──────────────────────┘
               ▼
         [LLM GENERATION]
```

---

## 7. Связи (Hyperedges)

### 7.1 Почему Hyperedges

Обычные рёбра: `A → B` (бинарные)
**Hyperedges**: `{A, B, C, D} → связь` (N-арные)

```
Пример: "OpenAI, Microsoft и Google соревнуются в области LLM"

❌ Триплеты (раздувание):
  (OpenAI, competes_with, Microsoft)
  (OpenAI, competes_with, Google)
  (Microsoft, competes_with, Google)
  + artificial node для "области LLM"

✅ Hyperedge:
  hyperedge:
    id: he_llm_competition
    type: competition
    participants: [ent_openai, ent_microsoft, ent_google]
    domain: ent_llm_field
    props:
      started: 2022
      intensity: high
    source_proposition: prop_xyz
```

### 7.2 Taxonomy связей

```yaml
# Все связи имеют богатую структуру
relation:
  id: rel_12345
  type: created_by
  from: ent_gpt4
  to: ent_openai
  
  # Свойства связи
  properties:
    announced_date: 2023-03-14
    collaboration: false
    
  # Контекст
  temporal:
    valid_from: 2023-03-14
    valid_to: null  # ongoing
    
  # Достоверность
  confidence: 0.99
  source: prop_gpt4_release
  
  # Квалификаторы
  qualifiers:
    role: "primary_developer"
    funding: "internal"
```

### 7.3 Relation Types

```
RELATIONS TAXONOMY
══════════════════

SEMANTIC
├── same_as          — идентичность (разные названия)
├── similar_to       — семантическая близость
├── related_to       — общая связанность
└── opposite_of      — противоположность

HIERARCHICAL
├── instance_of      — экземпляр класса
├── subclass_of      — подкласс
├── part_of          — часть целого
├── contains         — содержит
└── variant_of       — вариация

TEMPORAL
├── precedes         — предшествует
├── follows          — следует за
├── during           — во время
├── successor_of     — является преемником
└── contemporary     — одновременно существует

CAUSAL
├── causes           — вызывает
├── enables          — делает возможным
├── prevents         — предотвращает
├── influences       — влияет на
└── depends_on       — зависит от

ORGANIZATIONAL
├── created_by       — создано
├── owned_by         — принадлежит
├── works_for        — работает в
├── founded_by       — основано
└── acquired_by      — приобретено

EPISTEMIC
├── supports         — поддерживает утверждение
├── contradicts      — противоречит
├── evidence_for     — служит доказательством
├── derived_from     — получено из
└── cites            — цитирует

COMPETITIVE
├── competes_with    — конкурирует с
├── alternative_to   — альтернатива
├── superior_to      — превосходит
└── compatible_with  — совместим с
```

---

## 8. Алгоритм построения графа

### 8.1 Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GRAPH CONSTRUCTION PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 1: INGESTION (Level 0 → 1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Document (PDF, HTML, Audio, Video)
         │
         ▼
    [Preprocessing]
    - Text extraction (PyMuPDF, Trafilatura)
    - ASR for audio (Whisper)
    - OCR for images (PaddleOCR)
         │
         ▼
    [Semantic Chunking]
    - Not fixed size!
    - By semantic boundaries (paragraphs, sections)
    - Overlap for context preservation
    - Target: 500-1500 tokens per chunk
         │
         ▼
    Chunks (Level 1)


PHASE 2: EXTRACTION (Level 1 → 2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Chunks
         │
         ▼
    [LLM Proposition Extraction]
    - Extract atomic propositions
    - Preserve context (temporal, conditional)
    - Mark entity spans
         │
         ├──────────────────────┐
         ▼                      ▼
    Propositions           Mentioned Entities
         │                      │
         └──────────┬───────────┘
                    ▼
    [Entity Resolution]
    - Alias matching
    - Embedding similarity
    - Coreference resolution
    - External KB linking (Wikidata)
                    │
                    ▼
    Entities + Propositions (Level 2)


PHASE 3: LINKING (Level 2 → 3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Entities + Propositions
         │
         ▼
    [Relation Extraction]
    - Explicit relations from text
    - Inferred relations (co-occurrence, semantic)
    - Type-based relations (all AI_Models compete)
         │
         ▼
    [Graph Construction]
    - Entity nodes with properties
    - Proposition nodes linked to entities
    - Relation edges with qualifiers
         │
         ▼
    [Entity Clustering]
    - Leiden algorithm on entity graph
    - Parameters: resolution, quality function
         │
         ▼
    Local Clusters (Level 3)


PHASE 4: ABSTRACTION (Level 3 → 4 → 5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Local Clusters
         │
         ▼
    [Cluster Summarization]
    - Collect all propositions in cluster
    - LLM summarization
    - Extract key themes
         │
         ▼
    [Community Detection]
    - Higher-level Leiden clustering
    - Merge related clusters
         │
         ▼
    Communities (Level 4)
         │
         ▼
    [Theme Extraction]
    - Cross-community analysis
    - Topic modeling on summaries
         │
         ▼
    Global Themes (Level 5)


PHASE 5: INDEXING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    All Levels
         │
         ▼
    [Embedding Generation]
    - Entity embeddings
    - Proposition embeddings
    - Cluster summary embeddings
         │
         ▼
    [Index Construction]
    - Entity → Propositions mapping
    - Vector indexes (HNSW)
    - Full-text indexes
    - Alias lookup tables
```

### 8.2 Incremental Updates

```python
def add_document(doc):
    """Инкрементальное добавление документа"""
    
    # 1. Chunk
    chunks = semantic_chunk(doc)
    
    # 2. Extract propositions and entities
    for chunk in chunks:
        props = extract_propositions(chunk)
        
        for prop in props:
            # 3. Resolve entities
            resolved = resolve_entities(prop.entities)
            
            for entity in resolved:
                if entity.is_new:
                    # Новая сущность
                    add_entity(entity)
                else:
                    # Существующая — обновить индекс
                    entity.proposition_index.append(prop.id)
            
            # 4. Add proposition
            add_proposition(prop)
    
    # 5. Update clusters (lazy, by affected entities)
    affected_clusters = get_affected_clusters(resolved_entities)
    for cluster in affected_clusters:
        update_cluster_membership(cluster)
        regenerate_summary(cluster)  # async
    
    # 6. Rebuild indexes
    rebuild_indexes(affected_entities)
```

---

## 9. Сравнение с альтернативами

| Аспект | Наш подход | GraphRAG | LightRAG | SlimRAG |
|--------|------------|----------|----------|---------|
| **Base unit** | Proposition | Triple | Triple | Chunk |
| **Context preservation** | ✅ Full | ❌ Lost | ❌ Lost | Partial |
| **N-ary relations** | ✅ Native | ❌ Reification | ❌ Reification | N/A |
| **Nested subgraphs** | ✅ Yes | Partial | ❌ No | ❌ No |
| **Entity richness** | ✅ Full properties | Basic | Basic | Minimal |
| **Hierarchy levels** | 6 | 3 | 2 | 1 |
| **Incremental updates** | ✅ Yes | ❌ Limited | ✅ Yes | ✅ Yes |
| **Query speed** | Fast | Slow | Fast | Fastest |
| **Build cost** | Medium | High | Low | Lowest |

---

## 10. Навигация

| Следующий документ | Тема |
|--------------------|------|
| → [decentralized-stack.md](decentralized-stack.md) | Децентрализованный стек |
| → [../reference/relation-types.md](../reference/relation-types.md) | Полная таксономия связей |
| → [../concepts/knowledge-representation.md](../concepts/knowledge-representation.md) | Концепции представления знаний |

---

*Обновлено на основе исследований: PropRAG (2025), Dense-X Retrieval (2024), SlimRAG (2025), Semantic Units (2024)*
