# 🔗 Таксономия типов связей

> **Связанные документы:**
> - [Architecture: Knowledge Graph](../architecture/knowledge-graph.md)
> - [Glossary](glossary.md)

---

## 1. Обзор

Связи в Knowledge Graph должны быть **типизированными** и **богатыми метаданными**. Каждая связь может иметь:

```yaml
relation:
  from: entity_id_1
  to: entity_id_2
  type: relation_type       # Тип связи
  weight: 0.92              # Сила связи (0-1)
  confidence: 0.88          # Достоверность (0-1)
  source: claim_or_chunk_id # Откуда извлечено
  temporal_scope:           # Временной контекст
    valid_from: 2009-01-03
    valid_to: null
  context: "описание контекста связи"
```

---

## 2. SEMANTIC (Семантические)

Связи на основе **значения и смысла**.

| Тип | Описание | Пример |
|-----|----------|--------|
| `same_as` | Идентичность сущностей | "BTC" = "Bitcoin" |
| `similar_to` | Семантическая близость | "Ethereum" ~ "Solana" |
| `synonym_of` | Синонимия терминов | "AI" = "Искусственный интеллект" |
| `related_to` | Общая связанность | "Blockchain" ~ "Cryptocurrency" |
| `opposite_of` | Антонимия | "Централизация" ↔ "Децентрализация" |

### Использование

```yaml
# same_as: точное соответствие
- from: ent-btc
  to: ent-bitcoin
  type: same_as
  confidence: 0.99

# similar_to: похожие, но не идентичные
- from: ent-ethereum
  to: ent-solana
  type: similar_to
  weight: 0.75
  context: "Обе являются смарт-контракт платформами"
```

---

## 3. HIERARCHICAL (Иерархические)

Связи **классификации и структуры**.

| Тип | Описание | Пример |
|-----|----------|--------|
| `instance_of` | Экземпляр класса | "Bitcoin" → instance_of → "Cryptocurrency" |
| `subclass_of` | Подкласс | "DeFi" → subclass_of → "Finance" |
| `part_of` | Часть целого | "Block" → part_of → "Blockchain" |
| `member_of` | Член группы/коллекции | "Entity_1" → member_of → "Cluster_Finance" |
| `contains` | Содержит | "Document_1" → contains → "Chunk_1" |

### Свойства иерархических связей

```
part_of:
├── Транзитивность: A part_of B, B part_of C → A part_of C
├── Антисимметричность: A part_of B → NOT(B part_of A)
└── Reflexivity: опционально (A part_of A?)

subclass_of:
├── Транзитивность: ✅
├── Антисимметричность: ✅
└── Наследование свойств
```

---

## 4. EPISTEMIC (Эпистемические)

Связи **знания и доказательств**.

| Тип | Описание | Пример |
|-----|----------|--------|
| `supports` | Поддерживает утверждение | Claim_1 → supports → Claim_2 |
| `contradicts` | Противоречит | Claim_A → contradicts → Claim_B |
| `evidence_for` | Служит доказательством | Fact_1 → evidence_for → Theory_1 |
| `refutes` | Опровергает | Study_2 → refutes → Hypothesis_1 |
| `questions` | Ставит под вопрос | Comment_1 → questions → Claim_1 |

### Использование для reasoning

```yaml
# Поддержка утверждения
- from: claim-btc-decentralized
  to: claim-btc-no-single-point-of-failure
  type: supports
  confidence: 0.92
  reasoning: "Децентрализация implies no single point of failure"

# Противоречие
- from: claim-btc-anonymous
  to: claim-btc-traceable
  type: contradicts
  confidence: 0.85
  context: "Blockchain прозрачен, но псевдонимен"
```

---

## 5. CAUSAL (Причинно-следственные)

Связи **причины и следствия**.

| Тип | Описание | Пример |
|-----|----------|--------|
| `causes` | Вызывает | "Инфляция" → causes → "Рост цен" |
| `caused_by` | Вызвано | "Crash_2022" → caused_by → "FTX_collapse" |
| `enables` | Делает возможным | "Smart_contracts" → enables → "DeFi" |
| `prevents` | Предотвращает | "Consensus" → prevents → "Double_spending" |
| `influences` | Влияет на | "Fed_policy" → influences → "BTC_price" |

### Атрибуты каузальных связей

```yaml
- from: event-fed-rate-hike
  to: event-btc-price-drop
  type: causes
  confidence: 0.72
  lag: "1-3 days"           # Задержка эффекта
  strength: "moderate"      # Сила воздействия
  mechanism: "Risk-off sentiment leads to crypto selling"
```

---

## 6. TEMPORAL (Временные)

Связи **последовательности и времени**.

| Тип | Описание | Пример |
|-----|----------|--------|
| `precedes` | Предшествует | Event_1 → precedes → Event_2 |
| `follows` | Следует за | "Halving_2024" → follows → "Halving_2020" |
| `during` | Во время | "Bull_run" → during → "Year_2021" |
| `overlaps` | Перекрывается | "Project_A" → overlaps → "Project_B" |
| `contemporary` | Одновременно | "BTC_launch" → contemporary → "Financial_crisis_2008" |

### Allen's Interval Algebra

```
Полный набор временных отношений (Allen, 1983):

A before B:      |A|     |B|
A meets B:       |A||B|
A overlaps B:    |A--|
                   |--B|
A starts B:      |A--|
                 |----B|
A during B:        |A|
                 |----B|
A finishes B:      |--A|
                 |----B|
A equals B:      |--A--|
                 |--B--|
```

---

## 7. PROVENANCE (Происхождение)

Связи **источника и истории**.

| Тип | Описание | Пример |
|-----|----------|--------|
| `derived_from` | Производная от | Summary_1 → derived_from → Document_1 |
| `extracted_from` | Извлечено из | Entity_1 → extracted_from → Chunk_1 |
| `cited_by` | Цитируется | Paper_1 → cited_by → Paper_2 |
| `references` | Ссылается на | Doc_1 → references → Doc_2 |
| `version_of` | Версия чего-либо | Doc_v2 → version_of → Doc_v1 |

### Трассируемость

```yaml
# Полная цепочка происхождения
- atom: claim-btc-created-2009
  provenance:
    extracted_from: chunk-whitepaper-intro
    which_is_part_of: doc-btc-whitepaper
    processed_by: extraction-pipeline-v2
    on_date: 2026-02-01
    confidence: 0.98
```

---

## 8. CROSS-MODAL (Кросс-модальные)

Связи между **разными типами контента**.

| Тип | Описание | Пример |
|-----|----------|--------|
| `depicts` | Изображение изображает | Image_1 → depicts → Person_1 |
| `describes` | Текст описывает | Caption_1 → describes → Image_1 |
| `mentioned_in` | Упоминается в | Entity_1 → mentioned_in → Video_1 |
| `visualizes` | Визуализирует | Chart_1 → visualizes → Data_1 |
| `audio_of` | Аудио чего-либо | Audio_1 → audio_of → Meeting_1 |
| `transcription_of` | Транскрипция | Text_1 → transcription_of → Audio_1 |

---

## 9. INTER-LEVEL (Межуровневые)

Связи между **уровнями абстракции**.

| Связь | Формат | Пример |
|-------|--------|--------|
| `instance_of` | Entity → Class | "Bitcoin" → instance_of → "Cryptocurrency" |
| `subclass_of` | Class → Superclass | "DeFi_token" → subclass_of → "Token" |
| `member_of` | Entity → Community | "BTC_claim" → member_of → "Cluster_Crypto" |
| `summarizes` | Summary → Entities | "Summary_1" → summarizes → [Entity_1, Entity_2] |
| `abstracts` | Concept → Instances | "Transaction" → abstracts → [TX_1, TX_2, ...] |
| `contextualized_by` | Fact → Context | "Claim_1" → contextualized_by → "Document_A" |

---

## 10. Сводная таблица

| Категория | Типы | Основное применение |
|-----------|------|---------------------|
| **SEMANTIC** | same_as, similar_to, synonym, related, opposite | Entity resolution, search |
| **HIERARCHICAL** | instance_of, subclass_of, part_of, member_of, contains | Классификация, структура |
| **EPISTEMIC** | supports, contradicts, evidence_for, refutes, questions | Reasoning, fact-checking |
| **CAUSAL** | causes, caused_by, enables, prevents, influences | Analysis, prediction |
| **TEMPORAL** | precedes, follows, during, overlaps, contemporary | Timeline, history |
| **PROVENANCE** | derived_from, extracted_from, cited_by, references, version_of | Traceability |
| **CROSS-MODAL** | depicts, describes, mentioned_in, visualizes, audio_of | Multimodal linking |
| **INTER-LEVEL** | summarizes, abstracts, contextualized_by | Hierarchy navigation |

---

## 11. Рекомендации по использованию

### 11.1 Выбор типа связи

1. **Используйте наиболее специфичный тип** — `causes` лучше чем `related_to`
2. **Добавляйте confidence** — для неточных связей
3. **Указывайте source** — откуда извлечена связь
4. **Добавляйте context** — текстовое описание связи

### 11.2 Минимальная связь

```yaml
relation:
  from: entity_1
  to: entity_2
  type: related_to
```

### 11.3 Богатая связь

```yaml
relation:
  from: entity_1
  to: entity_2
  type: causes
  weight: 0.85
  confidence: 0.78
  source: claim_123
  temporal_scope:
    valid_from: 2020-01-01
    valid_to: 2023-12-31
  context: "Detailed explanation of the causal relationship"
  evidence:
    - chunk_45
    - chunk_67
  metadata:
    extracted_by: gpt-4
    extraction_date: 2026-02-01
```

---

*Источник: Ultimate-Knowledge-Graph-Architecture-Guide.md*
