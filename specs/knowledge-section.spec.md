# Спецификация: KnowledgeSection

> Знания: память агентов, граф знаний, библиотека спецификаций.

---

## Модули

### 1. MemoryModule -- память агентов

**Назначение:** персональная память агентов: наблюдения, preferences, learned context. Аналог Mem0.

**Actions:**
- `StoreMemoryAction(agent_id: str, content: str, tags: list[str]) -> Result[MemoryEntry, MemoryError]`
- `SearchMemoryAction(agent_id: str, query: str, limit: int) -> Result[list[MemoryEntry], MemoryError]`
- `UpdateMemoryAction(memory_id: str, content: str) -> Result[MemoryEntry, MemoryError]`

**Tasks:**
- `EmbedContentTask(content: str) -> list[float]` -- векторное представление
- `RankRelevanceTask(query_embedding: list[float], memories: list[MemoryEntry]) -> list[MemoryEntry]` -- ранжирование по релевантности

**Queries:**
- `GetAgentMemoriesQuery(agent_id: str, limit: int) -> list[MemoryEntry]`
- `GetMemoryStatsQuery(agent_id: str) -> MemoryStats`

**Events:** `MemoryStored`, `MemoryUpdated`, `MemoryPruned`
**Errors:** `MemoryStorageError`, `MemorySearchError`, `EmbeddingError`

---

### 2. KnowledgeGraphModule -- граф знаний

**Назначение:** долгоживущий temporal граф знаний: решения, факты, ограничения, их происхождение. Аналог Graphiti.

**Actions:**
- `AddFactAction(fact: Fact) -> Result[KGNode, KGError]` -- добавить факт
- `AddRelationAction(source: str, target: str, relation_type: str, metadata: dict) -> Result[KGEdge, KGError]`
- `QueryGraphAction(query: str) -> Result[list[KGNode], KGError]` -- семантический поиск по графу
- `AddDecisionAction(decision: ArchitectureDecision) -> Result[KGNode, KGError]` -- добавить ADR

**Tasks:**
- `ExtractEntitiesTask(text: str) -> list[Entity]` -- извлечь сущности из текста
- `ExtractRelationsTask(text: str, entities: list[Entity]) -> list[Relation]` -- извлечь связи
- `MergeNodesTask(node_a: KGNode, node_b: KGNode) -> KGNode` -- слить дублирующиеся ноды

**Queries:**
- `GetNodeQuery(node_id: str) -> KGNode | None`
- `GetNeighborsQuery(node_id: str, depth: int) -> list[KGNode]`
- `GetDecisionsQuery(domain: str) -> list[ArchitectureDecision]`
- `SearchByEmbeddingQuery(embedding: list[float], limit: int) -> list[KGNode]`

**Data Models:**

```python
@dataclass(frozen=True)
class KGNode:
    id: str
    label: str
    node_type: str              # fact / decision / constraint / entity / concept
    content: str
    embedding: list[float] | None
    metadata: dict
    created_at: datetime
    source: str                 # откуда пришел факт

@dataclass(frozen=True)
class KGEdge:
    source_id: str
    target_id: str
    relation_type: str          # depends_on / contradicts / extends / implements / ...
    weight: float
    metadata: dict
    created_at: datetime

@dataclass(frozen=True)
class ArchitectureDecision:
    title: str
    context: str
    decision: str
    consequences: list[str]
    status: str                 # proposed / accepted / deprecated / superseded
    superseded_by: str | None
```

**Events:** `FactAdded`, `RelationAdded`, `DecisionRecorded`, `NodesMerged`
**Errors:** `NodeNotFoundError`, `DuplicateNodeError`, `GraphQueryError`

---

### 3. SpecLibraryModule -- библиотека спецификаций

**Назначение:** хранение и управление Formula-шаблонами, стандартными спецификациями, best practices.

**Actions:**
- `AddFormulaAction(formula: Formula) -> Result[Formula, LibraryError]`
- `UpdateFormulaAction(name: str, updates: FormulaUpdate) -> Result[Formula, LibraryError]`
- `SearchFormulasAction(query: str) -> Result[list[Formula], LibraryError]` -- семантический поиск

**Queries:**
- `GetFormulaQuery(name: str) -> Formula | None`
- `ListFormulasQuery(category: str | None) -> list[FormulaSummary]`
- `GetBestPracticesQuery(domain: str) -> list[BestPractice]`

**Стандартные Formula (pre-loaded):**

```
add-action          -- добавить Action в Module
add-task            -- добавить Task в Module
add-module          -- добавить Module в Section
add-section         -- добавить Section
add-websocket       -- добавить WebSocket handler
add-adapter         -- добавить новый адаптер
refactor-extract    -- извлечь Task из Action
fix-bug             -- исправить баг
generate-project    -- сгенерировать новый Porto-проект
add-test            -- добавить тест
add-migration       -- добавить миграцию БД
```

**Events:** `FormulaAdded`, `FormulaUpdated`, `FormulaDeprecated`
**Errors:** `FormulaNotFoundError`, `DuplicateFormulaError`, `LibrarySearchError`

---

## Общие Acceptance Criteria

- [ ] MemoryModule поддерживает векторный поиск (embedding)
- [ ] KnowledgeGraphModule поддерживает temporal queries (факты с timestamps)
- [ ] SpecLibraryModule содержит минимум 5 стандартных Formula
- [ ] Все модули хранят данные через StatePort (адаптерная нейтральность)
- [ ] ADR хранятся в KG и экспортируются как Markdown
- [ ] Все Actions возвращают Result[T, E]
- [ ] Все модели -- Pydantic frozen
