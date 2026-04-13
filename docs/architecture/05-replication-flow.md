# Pipeline репликации

> Intent -> Spec -> Strategy -> Beads -> Execute -> Verify -> Promote. Единый pipeline для самоэволюции, генерации и legacy-работы.

---

## Общий pipeline

```
                              ЧЕЛОВЕК / АГЕНТ
                                    |
                              формулирует intent
                                    |
                                    v
                    +-------------------------------+
                    |  1. КОМПИЛЯЦИЯ (SpecModule)   |
                    |  intent -> MissionSpec         |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    |  2. СТРАТЕГИЯ (CompassModule)  |
                    |  MissionSpec -> StrategyPlan   |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    |  3. ДЕКОМПОЗИЦИЯ (MakerModule) |
                    |  StrategyPlan -> BeadGraph     |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    |  4. ИСПОЛНЕНИЕ (Orchestrator)  |
                    |  BeadGraph -> Artifacts        |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    |  5. ВЕРИФИКАЦИЯ (Evolution)    |
                    |  Artifacts -> EvidenceBundle   |
                    +---------|----------|----------+
                              |          |
                           pass        fail
                              |          |
                              v          v
                    +------------+  +-----------+
                    | 6. PROMOTE |  | RETRY /   |
                    |   merge,   |  | ESCALATE  |
                    |   publish  |  | -> шаг 2  |
                    +------------+  +-----------+
```

---

## Шаг 1: Компиляция (SpecModule)

**Action:** `CompileSpecAction`
**Вход:** Intent (текст на естественном языке или структурированный запрос)
**Выход:** `MissionSpec`

```python
@dataclass(frozen=True)
class MissionSpec:
    title: str                          # краткое название
    description: str                    # полное описание
    intent_type: IntentType             # self_evolve | generate | legacy
    target: str                         # на что направлен (self / repo URL / spec file)
    acceptance_criteria: list[str]      # когда задача считается выполненной
    constraints: list[str]              # ограничения (не ломать API, не менять БД, ...)
    risks: list[str]                    # идентифицированные риски
    context: dict                       # дополнительный контекст
    priority: Priority                  # critical / high / medium / low

class IntentType(str, Enum):
    SELF_EVOLVE = "self_evolve"         # модификация Replicator
    GENERATE = "generate"               # создание нового проекта
    LEGACY = "legacy"                   # работа с существующим проектом
```

---

## Шаг 2: Стратегия (CompassModule)

**Action:** `StrategizeAction`
**Вход:** `MissionSpec` + контекст (текущее состояние системы, доступные ресурсы, история)
**Выход:** `StrategyPlan`

```python
@dataclass(frozen=True)
class StrategyPlan:
    approach: str                       # общий подход
    phases: list[StrategyPhase]         # фазы исполнения
    risk_mitigations: list[str]         # как митигировать риски
    rollback_plan: str                  # план отката
    estimated_beads: int                # примерное количество beads
    confidence: float                   # уверенность Meta-Thinker (0-1)

@dataclass(frozen=True)
class StrategyPhase:
    name: str
    description: str
    dependencies: list[str]             # от каких фаз зависит
    parallel: bool                      # можно ли параллелить
```

**Внутри COMPASS:**
- Meta-Thinker анализирует MissionSpec и формирует стратегию
- Context Manager подтягивает релевантный контекст из KnowledgeGraph
- Если уверенность низкая, Meta-Thinker может запросить уточнение

---

## Шаг 3: Декомпозиция (MakerModule)

**Action:** `DecomposeAction`
**Вход:** `StrategyPlan`
**Выход:** `BeadGraph`

```python
@dataclass(frozen=True)
class Bead:
    id: str                             # уникальный идентификатор
    title: str
    description: str
    bead_type: BeadType                 # code | test | config | doc | review
    acceptance_criteria: list[str]      # когда bead считается выполненным
    input_artifacts: list[str]          # какие артефакты нужны на входе
    output_artifacts: list[str]         # какие артефакты производит
    dependencies: list[str]             # от каких beads зависит
    tools_required: list[str]           # какие MCP-инструменты нужны
    estimated_complexity: Complexity    # trivial / simple / moderate / complex

@dataclass(frozen=True)
class BeadGraph:
    beads: list[Bead]
    edges: list[tuple[str, str]]        # (from_bead_id, to_bead_id)
    critical_path: list[str]            # beads на критическом пути
    parallel_groups: list[list[str]]    # группы beads для параллельного исполнения
```

**Внутри MAKER:**
- MAD (Micro-Agent Decomposition) разбивает StrategyPlan на атомарные Beads
- Каждый Bead -- одна четкая задача с acceptance criteria
- Граф зависимостей определяет порядок исполнения и возможности параллелизма

---

## Шаг 4: Исполнение (OrchestratorModule)

**Action:** `ExecuteBeadGraphAction`
**Вход:** `BeadGraph`
**Выход:** `ExecutionResult`

```python
@dataclass(frozen=True)
class BeadResult:
    bead_id: str
    status: BeadStatus                  # success | failure | skipped
    artifacts: list[str]                # идентификаторы произведенных артефактов
    evidence: dict                      # доказательства (логи, метрики, traces)
    duration_ms: int
    agent_id: str                       # какой агент исполнял

@dataclass(frozen=True)
class ExecutionResult:
    bead_results: list[BeadResult]
    overall_status: str                 # success | partial_failure | failure
    total_duration_ms: int
    artifacts_produced: list[str]
```

**Внутри Orchestrator:**
- Определяет порядок исполнения по графу зависимостей
- Параллельные группы исполняет одновременно (anyio TaskGroup)
- Для каждого Bead выбирает агента и MCP-инструменты
- K-Voting: для критических beads запускает K параллельных агентов
- Red-Flagging: фильтрует ненадежные результаты

---

## Шаг 5: Верификация (EvolutionModule)

**Action:** `VerifyAction`
**Вход:** `ExecutionResult`
**Выход:** `EvidenceBundle`

```python
@dataclass(frozen=True)
class EvidenceBundle:
    status: VerificationStatus          # pass | fail | needs_review
    test_results: dict                  # результаты тестов
    lint_results: dict                  # результаты линтеров
    type_check_results: dict            # результаты проверки типов
    diff_summary: str                   # summary изменений
    metrics: dict                       # метрики (coverage, performance)
    risk_assessment: str                # оценка рисков изменений
    reviewer_notes: list[str]           # заметки от агента-ревьюера
```

**Верификация включает:**
- Запуск тестов (pytest, hypothesis)
- Линтер (ruff)
- Type checking (pyright/mypy)
- Архитектурные guardrails (проверка правил Porto)
- Semantic review (агент-ревьюер оценивает качество)

---

## Шаг 6: Promotion (EvolutionModule)

**Action:** `PromoteAction`
**Вход:** `EvidenceBundle` (status=pass) + артефакты
**Выход:** промоутированные изменения

В зависимости от intent_type:

| Режим | Promotion |
|---|---|
| `self_evolve` | Merge в main, обновление CellRegistry |
| `generate` | Создание нового репозитория, push |
| `legacy` | PR в целевой репозиторий, запуск legacy CI |

---

## Обработка ошибок (fail path)

Если верификация не прошла:

1. EvolutionModule анализирует причины failure
2. Формирует новый intent с контекстом ошибки
3. Отправляет обратно в CompassModule (шаг 2)
4. CompassModule формирует скорректированную стратегию
5. Pipeline повторяется с учетом предыдущих ошибок

Максимальное количество ретраев -- конфигурируемо. По умолчанию 3.

При исчерпании ретраев -- эскалация: система формирует детальный отчет и запрашивает человеческое вмешательство.
