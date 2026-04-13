# 💡 Представление знаний

> **Связанные документы:**
> - [Architecture: Knowledge Graph](../architecture/knowledge-graph.md)
> - [Reference: Relation Types](../reference/relation-types.md)

---

## 1. Философия: Propositions > Triples

### 1.1 Почему НЕ триплеты

**Триплеты (Subject, Predicate, Object)** — классический подход, но он устарел:

```
❌ ТРИПЛЕТЫ (Context Collapse)

(GPT-4, released_by, OpenAI)

Проблемы:
• Где дата релиза? 
• Откуда информация?
• Насколько достоверно?
• Какие условия?
```

**PropRAG (EMNLP 2025)** напрямую критикует:
> "Triples suffer from **context collapse** — a lossy compression that discards conditionality, provenance, and n-ary relationships"

### 1.2 Наш выбор: Propositions

```
✅ PROPOSITIONS (Context Preserved)

{
  text: "OpenAI выпустила GPT-4 14 марта 2023 года",
  entities: [OpenAI, GPT-4],
  temporal: "2023-03-14",
  confidence: 0.98,
  source: chunk_789,
  provenance: "official_announcement"
}

Преимущества:
• Полный контекст сохранён
• Читаемо для человека
• Читаемо для LLM
• Легко обновлять
```

### 1.3 Ключевые принципы

| Принцип | Описание |
|---------|----------|
| **Propositions First** | Атомарные утверждения на естественном языке |
| **Rich Entities** | Сущности — контейнеры со свойствами |
| **Nested Subgraphs** | Вложенные подграфы для организации |
| **Maximal Connectivity** | На низком уровне связываем всё что можно |
| **Progressive Abstraction** | Снизу вверх: детали → абстракции |
| **Context Never Lost** | Provenance и источник всегда сохранены |

---

## 2. Proposition: Базовая единица знания

### 2.1 Что такое Proposition

**Proposition** — атомарное, самодостаточное утверждение, которое:
- Содержит ровно **один факт**
- Написано на **естественном языке**
- Сохраняет **весь контекст** (время, условия, источник)
- Связано с **сущностями** которые упоминает
- Имеет **embedding** для поиска

### 2.2 Структура Proposition

```yaml
proposition:
  # Уникальный ID
  id: prop_gpt4_release
  
  # Сам текст — читаемый человеком и LLM
  text: "OpenAI выпустила GPT-4 14 марта 2023 года"
  
  # Тип утверждения
  type: temporal  # factual, relational, causal, conditional...
  
  # Связанные сущности (автоматически извлечены)
  entities:
    - id: ent_openai
      role: agent
      span: [0, 6]  # позиция в тексте
    - id: ent_gpt4
      role: product
      span: [16, 21]
  
  # КОНТЕКСТ (то что теряется в триплетах!)
  temporal:
    point: 2023-03-14
    precision: day
  
  modality: factual  # vs hypothetical, conditional
  
  # Метаданные
  confidence: 0.98
  source_chunk: chunk_789
  provenance: "official_announcement"
  
  # Для семантического поиска
  embedding: [0.12, 0.34, ...]
  
  # Квалификаторы для сложных случаев
  qualifiers:
    event_type: product_release
    audience: public
```

### 2.3 Типы Propositions

| Тип | Описание | Пример |
|-----|----------|--------|
| **Factual** | Конкретный факт | "GPT-4 имеет 128K токенов контекста" |
| **Temporal** | Событие во времени | "OpenAI основана в декабре 2015" |
| **Relational** | Связь сущностей | "Sam Altman — CEO OpenAI" |
| **Attributive** | Свойство | "GPT-4 мультимодальный" |
| **Causal** | Причина-следствие | "Увеличение данных улучшило качество" |
| **Conditional** | Условное | "При temperature=0 вывод детерминирован" |
| **Comparative** | Сравнение | "Claude-3 превосходит GPT-4 в coding" |
| **Negation** | Отрицание | "GPT-4 не имеет доступа к интернету" |

### 2.4 Сравнение: Proposition vs Triple

| Аспект | Triple | Proposition |
|--------|--------|-------------|
| **Формат** | (S, P, O) | Natural Language + metadata |
| **Контекст** | ❌ Потерян | ✅ Сохранён полностью |
| **N-арность** | Reification hell | ✅ Native в тексте |
| **Читаемость человеком** | Низкая | ✅ Высокая |
| **Читаемость LLM** | Требует сериализации | ✅ Native |
| **Обновление** | Сложно (миграции) | ✅ Просто |
| **Reasoning** | Символьный | LLM-native |

---

## 3. Entity: Богатый узел графа

### 3.1 Структура Entity

Entity — не просто имя, а **контейнер со свойствами**:

```yaml
entity:
  # Идентификация
  id: ent_gpt4
  canonical_name: "GPT-4"
  
  # Типизация (множественная!)
  type:
    primary: AI_Model
    secondary: [LLM, Product, Technology]
  
  # Альтернативные названия (для resolution)
  aliases:
    - text: "gpt-4"
      frequency: 1250
    - text: "GPT4" 
      frequency: 340
    - text: "gpt4o"
      frequency: 567
  
  # Свойства (schema-less, любые)
  properties:
    parameters: "~1.7T"
    context_window: 128000
    release_date: 2023-03-14
    modalities: ["text", "vision", "audio"]
  
  # Прямые связи с другими сущностями
  relations:
    - target: ent_openai
      type: created_by
    - target: ent_gpt35
      type: successor_of
  
  # Индекс: какие propositions упоминают
  proposition_index: [prop_123, prop_456, ...]
  
  # Внешние идентификаторы
  external_ids:
    wikidata: Q115753512
    wikipedia: "GPT-4"
  
  # Embedding для поиска
  embedding: [0.56, 0.78, ...]
```

### 3.2 Типы сущностей

```
ENTITY TYPES (гетерогенность)
════════════════════════════════

NAMED ENTITIES
├── Person          — люди
├── Organization    — компании, институты
├── Location        — места
├── Product         — продукты, сервисы
└── Event           — конференции, релизы

DOMAIN ENTITIES
├── AI_Model        — GPT-4, Claude, Llama
├── Technology      — Transformer, RLHF
├── Dataset         — CommonCrawl, RedPajama
├── Metric          — MMLU, HumanEval
└── Paper           — научные статьи

ABSTRACT CONCEPTS
├── Concept         — decentralization, attention
├── Method          — fine-tuning, RAG
└── Theory          — scaling laws

STRUCTURAL
├── Document        — источник
├── Chunk           — фрагмент текста
└── Cluster         — группа сущностей
```

---

## 4. Многоуровневая иерархия

### 4.1 6 уровней абстракции

```
╔═══════════════════════════════════════════════════════════════════════════╗
║ LEVEL 5: GLOBAL THEMES                                                    ║
║ ─────────────────────────────────────────────────────────────────────────║
║ LLM-суммаризации кластеров верхнего уровня                               ║
║ Пример: "Artificial Intelligence", "FinTech"                              ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ LEVEL 4: COMMUNITIES                                                      ║
║ ─────────────────────────────────────────────────────────────────────────║
║ Семантически связанные группы кластеров                                  ║
║ Пример: "Large Language Models", "Crypto Trading"                         ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ LEVEL 3: LOCAL CLUSTERS (вложенные подграфы)                             ║
║ ─────────────────────────────────────────────────────────────────────────║
║ Группы сущностей с общим контекстом                                      ║
║ Пример: "OpenAI Models", "Anthropic Products"                             ║
║ Каждый кластер = подграф со своей суммаризацией                          ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ LEVEL 2: ENTITIES + PROPOSITIONS                                         ║
║ ─────────────────────────────────────────────────────────────────────────║
║ Богатые сущности + атомарные утверждения                                 ║
║ Entity → linked to → Propositions → linked to → Chunks                    ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ LEVEL 1: CHUNKS                                                          ║
║ ─────────────────────────────────────────────────────────────────────────║
║ Семантические фрагменты текста (500-1500 токенов)                        ║
║ Сохраняют позицию в документе                                            ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ LEVEL 0: RAW DOCUMENTS                                                   ║
║ ─────────────────────────────────────────────────────────────────────────║
║ PDF, HTML, Audio, Video, Images, Tables                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

### 4.2 Поток построения

```
Document (Level 0)
     │
     ▼ [Chunking: semantic boundaries]
Chunks (Level 1)
     │
     ▼ [LLM Extraction: propositions + entities]
Propositions + Entities (Level 2)
     │
     ▼ [Leiden Clustering on entity graph]
Local Clusters (Level 3)
     │
     ▼ [LLM Summarization per cluster]
Communities (Level 4)
     │
     ▼ [Theme extraction across communities]
Global Themes (Level 5)
```

---

## 5. Вложенные подграфы

### 5.1 Кластер как подграф

Каждый **кластер** — не просто набор узлов, а **полноценный подграф**:

```
┌───────────────────────────────────────────────────────────────────┐
│ CLUSTER: "OpenAI Language Models"                                 │
│ ════════════════════════════════════════════════════════════════ │
│                                                                   │
│  METADATA:                                                        │
│    id: cluster_openai_llm                                         │
│    level: 3                                                       │
│    entity_count: 8                                                │
│    proposition_count: 234                                         │
│                                                                   │
│  SUMMARY: "Семейство языковых моделей OpenAI включает GPT-3,     │
│            GPT-3.5, GPT-4 и их вариации. Модели демонстрируют    │
│            прогрессивное улучшение..."                            │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              INTERNAL GRAPH                                │   │
│  │                                                            │   │
│  │   [GPT-3] ─successor_of─▶ [GPT-3.5] ─successor_of─▶ [GPT-4]│   │
│  │      │                        │                        │   │   │
│  │      └────────── all created_by ──────────────────────▶│   │   │
│  │                                                 [OpenAI]│   │   │
│  │                                                        │   │   │
│  │   + 234 propositions connecting these entities         │   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  EXTERNAL LINKS:                                                  │
│    → cluster_anthropic (competes_with)                           │
│    → cluster_ai_safety (concerns)                                │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 5.2 Зачем вложенность

| Преимущество | Описание |
|--------------|----------|
| **Инкапсуляция** | Детали скрыты внутри, наружу — суммари |
| **Масштабируемость** | Можно работать на нужном уровне |
| **Навигация** | Drill-down / roll-up |
| **Retrieval** | Сначала найти кластер, потом детали |
| **Контекст** | Суммари кластера = контекст для LLM |

---

## 6. Индексирование

### 6.1 Entity-Centric Index

Основной паттерн — **от сущности к знаниям**:

```
ENTITY INDEX
════════════════════════════════════════════════════════════════════

entity_id → {
  propositions: [prop_1, prop_2, ...],    # Где упоминается
  chunks: [chunk_1, chunk_2, ...],        # Исходные тексты
  clusters: [cluster_1, ...],             # Принадлежность
  related_entities: [ent_1, ent_2, ...],  # Связанные
}

Пример:
────────────────────────────────────────────────────────────────────
ent_gpt4 → {
  propositions: [
    "OpenAI выпустила GPT-4 14 марта 2023",
    "GPT-4 имеет 128K контекст",
    "GPT-4 превосходит GPT-3.5 на 40%",
    ... (еще 200+)
  ],
  chunks: [chunk_789, chunk_802, ...],
  clusters: [cluster_openai_llm],
  related_entities: [ent_openai, ent_gpt35, ent_claude, ...],
}
```

### 6.2 Query Flow

```
QUERY: "Какие возможности у GPT-4?"
               │
               ▼
┌──────────────────────────────────┐
│ 1. Entity Extraction             │
│    → "GPT-4"                     │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│ 2. Entity Resolution             │
│    "GPT-4" → ent_gpt4            │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│ 3. Proposition Retrieval         │
│    ent_gpt4.propositions         │
│    filter by "capabilities"      │
│    → top_k relevant              │
└──────────────┬───────────────────┘
               ▼
┌──────────────────────────────────┐
│ 4. Context Assembly              │
│    propositions +                │
│    cluster_summary +             │
│    related entities if needed    │
└──────────────┬───────────────────┘
               ▼
         [LLM Generation]
```

---

## 7. Semantic Similarity ≠ Semantic Relevance

### 7.1 Ключевой инсайт

**SlimRAG (2025)** показал критическую проблему:

```
Query: "What is the gender of this waiter?"

Cosine Similarity:
  "Waiter" ↔ "Waitress"  = 0.94  (очень похожи!)
  "Waiter" ↔ "Male"      = 0.31  (не похожи)

Но для ответа на вопрос:
  "Male" — РЕЛЕВАНТНО
  "Waitress" — НЕ релевантно (даже misleading)
```

### 7.2 Решение

Разделяем:
- **Similarity** — для организации (индексирование, кластеризация)
- **Relevance** — для retrieval (ответ на вопрос)

```
┌─────────────────────────────────────────────────────────────────┐
│  INDEXING PHASE                                                 │
│  Используем similarity для:                                     │
│  • Entity resolution (похожие имена = одна сущность)            │
│  • Clustering (похожие сущности в один кластер)                │
│  • Embedding space organization                                 │
├─────────────────────────────────────────────────────────────────┤
│  RETRIEVAL PHASE                                                │
│  Используем relevance для:                                      │
│  • Query-proposition matching                                   │
│  • Entity mention scoring                                       │
│  • Context selection                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Практические рекомендации

### 8.1 При проектировании

| Рекомендация | Пояснение |
|--------------|-----------|
| **Начните с propositions** | Не пытайтесь сразу делать сложную схему |
| **Entity resolution — приоритет** | Плохой resolution = плохой граф |
| **Сохраняйте source_chunk** | Всегда можно вернуться к оригиналу |
| **Confidence на всё** | Не все факты равны |
| **Incremental updates** | Не перестраивать весь граф |

### 8.2 При extraction

```python
# Хороший prompt для extraction

PROMPT = """
Extract atomic propositions from the text.

Rules:
1. ONE proposition = ONE fact (cannot be split further)
2. PRESERVE temporal context (dates, periods, "в то время")
3. PRESERVE conditional context (if, when, unless)  
4. PRESERVE source attribution (according to, said, reported)
5. MARK entities with tags: <e>entity name</e>
6. Include CONFIDENCE based on language certainty

Bad: "Einstein developed relativity and won Nobel"
Good: 
  - "<e>Einstein</e> developed <e>special relativity</e> in <e>1905</e>"
  - "<e>Einstein</e> won <e>Nobel Prize</e> in <e>1921</e>"
"""
```

### 8.3 При retrieval

```python
def retrieve_context(query: str) -> str:
    # 1. Extract entities from query
    query_entities = extract_entities(query)
    
    # 2. Resolve to known entities
    resolved = [resolve(e) for e in query_entities]
    
    # 3. Get propositions (entity-centric!)
    props = []
    for entity in resolved:
        props.extend(entity.proposition_index)
    
    # 4. Filter by semantic RELEVANCE (not just similarity!)
    relevant = rank_by_relevance(props, query)
    
    # 5. Add cluster context if needed
    if needs_more_context(relevant):
        clusters = get_clusters(resolved)
        relevant += [c.summary for c in clusters]
    
    # 6. Assemble within token budget
    return assemble_context(relevant, max_tokens=4000)
```

---

## 9. Сравнение подходов

| Подход | Base Unit | Context | Human Readable | LLM Native | Complexity |
|--------|-----------|---------|----------------|------------|------------|
| **RDF Triples** | (S,P,O) | ❌ | ❌ | ❌ | Medium |
| **Semantic Units** | Triple groups | ✅ | Medium | Medium | High |
| **Propositions (наш)** | NL sentence | ✅ | ✅ | ✅ | Low |
| **Hyper-Relational** | N-tuples | Partial | ❌ | ❌ | High |
| **Pure Chunks** | Text | ✅ | ✅ | ✅ | Lowest |

**Наш выбор: Propositions** — баланс структурированности и простоты.

---

## 10. Навигация

| Документ | Тема |
|----------|------|
| → [architecture/knowledge-graph.md](../architecture/knowledge-graph.md) | Полная архитектура графа |
| → [reference/relation-types.md](../reference/relation-types.md) | Таксономия связей |
| → [concepts/ai-integration.md](ai-integration.md) | Интеграция с AI |

---

*Обновлено на основе: PropRAG (2025), Dense-X Retrieval (2024), SlimRAG (2025), Semantic Units (2024)*
