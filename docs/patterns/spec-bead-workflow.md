# Паттерн: Spec-Bead Workflow

> От Intent к атомарным единицам работы: Intent -> MissionSpec -> Formula -> Molecule -> Bead.

---

## Иерархия единиц работы

```
Intent (текст)
  |
  v
MissionSpec (структурированная спецификация)
  |
  v
Formula (декларативный шаблон workflow)
  |
  v
Molecule (связанный граф шагов)
  |
  v
Bead (атомарная единица с acceptance criteria)
```

---

## Intent

Высокоуровневое намерение. Может быть:
- Текст на естественном языке: "Добавить поддержку WebSocket в OrderModule"
- Структурированный запрос: JSON/YAML с полями target, action, constraints
- Ссылка на issue: "Huly #347" или "GitHub issue #42"

Intent -- это ВХОД. Он не является source of truth.

---

## MissionSpec

Структурированная формулировка intent с рисками, границами и acceptance gates.

```python
@dataclass(frozen=True)
class MissionSpec:
    title: str
    description: str
    intent_type: IntentType             # self_evolve / generate / legacy
    target: str                         # self / repo URL / spec file
    acceptance_criteria: list[str]
    constraints: list[str]
    risks: list[str]
    context: dict
    priority: Priority
```

MissionSpec -- это SOURCE OF TRUTH для данного изменения. Код -- производная спецификации.

---

## Formula

Декларативный шаблон workflow, из которого можно инстанцировать Molecule. Formula -- это РЕЦЕПТ.

```python
@dataclass(frozen=True)
class Formula:
    name: str                           # "add-websocket-handler"
    description: str
    phases: list[FormulaPhase]
    variables: dict[str, str]           # параметры, которые задаются при инстанцировании
    preconditions: list[str]            # что должно быть true перед запуском

@dataclass(frozen=True)
class FormulaPhase:
    name: str
    bead_templates: list[BeadTemplate]
    parallel: bool                      # можно ли beads этой фазы параллелить
    gate: str                           # условие перехода к следующей фазе
```

Formula можно переиспользовать. Для типовых задач (add module, add action, refactor) создаются стандартные Formula в `SpecLibraryModule`.

---

## Molecule

Конкретный инстанс Formula с подставленными переменными. Molecule -- это ПЛАН ИСПОЛНЕНИЯ.

```python
@dataclass(frozen=True)
class Molecule:
    formula_name: str
    variables_resolved: dict[str, str]
    beads: list[Bead]
    edges: list[tuple[str, str]]        # граф зависимостей
    status: MoleculeStatus              # pending / in_progress / completed / failed
```

---

## Bead

Атомарная единица работы. Один Bead = одна четкая задача с явным acceptance criteria.

```python
@dataclass(frozen=True)
class Bead:
    id: str
    title: str
    description: str
    bead_type: BeadType                 # code / test / config / doc / review
    acceptance_criteria: list[str]
    input_artifacts: list[str]
    output_artifacts: list[str]
    dependencies: list[str]             # от каких beads зависит
    tools_required: list[str]           # MCP tools
    estimated_complexity: Complexity
    workcell: WorkcellType              # где исполнять: worktree / container / sandbox
```

### BeadType

| Тип | Пояснение |
|---|---|
| `code` | Написание/модификация кода |
| `test` | Написание/запуск тестов |
| `config` | Изменение конфигурации (flake.nix, settings) |
| `doc` | Написание/обновление документации |
| `review` | Ревью кода или результата |

### Acceptance Criteria

Каждый Bead имеет явные, проверяемые criteria:

```python
Bead(
    id="bead-001",
    title="Создать WebSocketHandler для OrderModule",
    acceptance_criteria=[
        "Файл src/Containers/AppSection/OrderModule/UI/WebSocket/Handlers.py существует",
        "Handler принимает подключения на /ws/orders/{order_id}",
        "Handler использует anyio.create_task_group для structured concurrency",
        "Тесты проходят: test_websocket_connect, test_websocket_receive",
    ],
    bead_type=BeadType.CODE,
    tools_required=["file_write", "git_stage"],
    dependencies=[],
)
```

---

## Workcell -- изолированная среда исполнения

| WorkcellType | Что | Когда |
|---|---|---|
| `worktree` | Git worktree (отдельная рабочая копия) | Большинство задач |
| `container` | Docker/OCI контейнер | Тесты с зависимостями, опасные операции |
| `sandbox` | Nix sandbox (bubblewrap) | Высокая изоляция, untrusted код |
| `preview` | Preview environment (namespace-per-PR) | Интеграционное тестирование |

---

## Pipeline: от Intent до Code

```
Человек: "Добавить WebSocket в OrderModule"
    |
    v
SpecModule.CompileSpecAction:
    MissionSpec(
        title="WebSocket для OrderModule",
        intent_type=SELF_EVOLVE,
        target="self",
        acceptance_criteria=["WebSocket /ws/orders/{id} работает", "Тесты проходят"],
        constraints=["Не менять API REST", "Использовать Litestar Channels"],
    )
    |
    v
CompassModule.StrategizeAction:
    StrategyPlan(
        approach="Добавить WebSocket handler по паттерну UserModule",
        phases=[
            Phase("handler", "Создать Handler + Routes"),
            Phase("test", "Написать тесты"),
            Phase("wire", "Подключить в App.py"),
        ],
    )
    |
    v
MakerModule.DecomposeAction:
    BeadGraph(
        beads=[
            Bead("bead-001", "Создать Handlers.py", type=CODE),
            Bead("bead-002", "Создать Routes.py", type=CODE, deps=["bead-001"]),
            Bead("bead-003", "Написать тесты", type=TEST, deps=["bead-002"]),
            Bead("bead-004", "Подключить в App.py", type=CONFIG, deps=["bead-002"]),
            Bead("bead-005", "Ревью", type=REVIEW, deps=["bead-003", "bead-004"]),
        ],
    )
    |
    v
OrchestratorModule.ExecuteBeadGraphAction:
    -> Исполняет beads по графу зависимостей
    -> bead-001 и bead-002 последовательно
    -> bead-003 и bead-004 параллельно (оба зависят от bead-002)
    -> bead-005 после обоих
    |
    v
EvolutionModule.VerifyAction:
    -> Тесты, lint, type check, architecture guards
    -> pass -> PromoteAction -> merge
```

---

## Стандартные Formula (библиотека)

```
specs/formulas/
  add-action.formula.yaml           # добавить Action в существующий Module
  add-module.formula.yaml           # добавить Module в Section
  add-section.formula.yaml          # добавить Section
  add-websocket.formula.yaml        # добавить WebSocket handler
  add-adapter.formula.yaml          # добавить новый адаптер
  refactor-extract-task.formula.yaml # извлечь Task из Action
  fix-bug.formula.yaml              # исправить баг
  generate-project.formula.yaml    # сгенерировать новый проект
```

Формулы хранятся в `KnowledgeSection/SpecLibraryModule` и могут эволюционировать.
