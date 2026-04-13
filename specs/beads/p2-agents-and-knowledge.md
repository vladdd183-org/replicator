# P2 Beads: AgentSection + KnowledgeSection + EvolutionModule

> Feature layer. Интеллект, знания, эволюция.

---

## AgentSection/CompassModule

### B-AGENT-COMP-001: DSPy Signatures для COMPASS

- **Компонент:** `Containers/AgentSection/CompassModule/Tasks/`
- **Acceptance:**
  - [ ] StrategizeSignature (DSPy) -- mission_spec + context -> approach + phases + risks + confidence
  - [ ] ScoreConfidenceTask -- оценка confidence стратегии
  - [ ] BuildContextBriefTask -- формирование Brief для агента-исполнителя
- **Зависимости:** P1 CoreSection
- **Приоритет:** P2

### B-AGENT-COMP-002: StrategizeAction

- **Компонент:** `Containers/AgentSection/CompassModule/Actions/StrategizeAction.py`
- **Acceptance:**
  - [ ] Принимает MissionSpec + ContextBundle
  - [ ] Использует DSPy для формирования StrategyPlan
  - [ ] Возвращает Result[StrategyPlan, CompassError]
  - [ ] Генерирует событие StrategyFormed
- **Зависимости:** B-AGENT-COMP-001, B-CORE-SPEC-001
- **Приоритет:** P2

---

## AgentSection/MakerModule

### B-AGENT-MAKER-001: MAD Decomposition

- **Компонент:** `Containers/AgentSection/MakerModule/Actions/DecomposeAction.py`
- **Acceptance:**
  - [ ] Принимает StrategyPlan
  - [ ] Декомпозирует на Beads (через DSPy или LLM)
  - [ ] Строит граф зависимостей
  - [ ] Определяет параллельные группы
  - [ ] Возвращает Result[BeadGraph, MakerError]
- **Зависимости:** B-AGENT-COMP-002, B-CORE-SPEC-001
- **Приоритет:** P2

### B-AGENT-MAKER-002: K-Voting

- **Компонент:** `Containers/AgentSection/MakerModule/Actions/VoteAction.py`
- **Acceptance:**
  - [ ] Запускает K агентов параллельно (anyio TaskGroup)
  - [ ] MajorityVoteTask подсчитывает голоса
  - [ ] ConsistencyCheckTask проверяет согласованность
  - [ ] При низком confidence -> Failure(NoConsensusError)
- **Зависимости:** B-AGENT-MAKER-001
- **Приоритет:** P2

---

## AgentSection/OrchestratorModule

### B-AGENT-ORCH-001: BeadGraph Executor

- **Компонент:** `Containers/AgentSection/OrchestratorModule/Actions/ExecuteBeadGraphAction.py`
- **Acceptance:**
  - [ ] Топологическая сортировка BeadGraph
  - [ ] Параллельное исполнение независимых Beads (anyio TaskGroup)
  - [ ] Последовательное для зависимых
  - [ ] Сбор evidence для каждого Bead
  - [ ] Retry при failure (configurable max_retries)
  - [ ] Возвращает Result[ExecutionResult, OrchestratorError]
- **Зависимости:** B-AGENT-MAKER-001, B-TOOL-MCP-001, B-TOOL-GIT-001
- **Приоритет:** P2

---

## CoreSection/EvolutionModule

### B-CORE-EVOL-001: VerifyAction

- **Компонент:** `Containers/CoreSection/EvolutionModule/Actions/VerifyAction.py`
- **Acceptance:**
  - [ ] Запускает тесты, lint, type check
  - [ ] Проверяет architecture guards
  - [ ] Собирает EvidenceBundle
  - [ ] Возвращает Result[EvidenceBundle, EvolutionError]
- **Зависимости:** B-AGENT-ORCH-001
- **Приоритет:** P2

### B-CORE-EVOL-002: PromoteAction

- **Компонент:** `Containers/CoreSection/EvolutionModule/Actions/PromoteAction.py`
- **Acceptance:**
  - [ ] Принимает EvidenceBundle (status=pass)
  - [ ] Для self_evolve: merge в main
  - [ ] Для generate: push нового репозитория
  - [ ] Для legacy: создание PR
  - [ ] Обновляет CellRegistry
  - [ ] Генерирует событие VersionPromoted
- **Зависимости:** B-CORE-EVOL-001, B-CORE-REG-002, B-TOOL-GIT-002
- **Приоритет:** P2

---

## KnowledgeSection/MemoryModule

### B-KNOW-MEM-001: Agent Memory базовый

- **Компонент:** `Containers/KnowledgeSection/MemoryModule/`
- **Acceptance:**
  - [ ] StoreMemoryAction -- сохранить текст с тегами
  - [ ] SearchMemoryAction -- поиск по тексту (substring match для MVP)
  - [ ] Хранение через StatePort (адаптерная нейтральность)
  - [ ] Тест: store -> search -> find
- **Зависимости:** B-SHIP-ADAPT-006
- **Приоритет:** P2

---

## KnowledgeSection/KnowledgeGraphModule

### B-KNOW-KG-001: Knowledge Graph базовый

- **Компонент:** `Containers/KnowledgeSection/KnowledgeGraphModule/`
- **Acceptance:**
  - [ ] AddFactAction -- добавить факт (KGNode)
  - [ ] AddRelationAction -- связать два факта (KGEdge)
  - [ ] QueryGraphAction -- текстовый поиск по фактам
  - [ ] AddDecisionAction -- сохранить Architecture Decision Record
  - [ ] Хранение через StatePort
  - [ ] Тест: add fact -> add relation -> query -> find
- **Зависимости:** B-SHIP-ADAPT-006
- **Приоритет:** P2

---

## Сводка P2

| Bead | Компонент | Зависит от |
|---|---|---|
| B-AGENT-COMP-001 | COMPASS DSPy | P1 CoreSection |
| B-AGENT-COMP-002 | StrategizeAction | COMP-001 |
| B-AGENT-MAKER-001 | MAD Decompose | COMP-002 |
| B-AGENT-MAKER-002 | K-Voting | MAKER-001 |
| B-AGENT-ORCH-001 | BeadGraph Executor | MAKER-001, MCP, Git |
| B-CORE-EVOL-001 | VerifyAction | ORCH-001 |
| B-CORE-EVOL-002 | PromoteAction | EVOL-001, REG-002, GIT-002 |
| B-KNOW-MEM-001 | Agent Memory | ADAPT-006 |
| B-KNOW-KG-001 | Knowledge Graph | ADAPT-006 |

**Итого: 9 Beads, P2 features. Параллелизм: AgentSection и KnowledgeSection могут идти параллельно.**
