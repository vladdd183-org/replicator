# ПЕРЕДАЧА КОНТЕКСТА: Replicator

> Полная заметка для следующего AI-агента. Содержит ВСЁ: идеи, концепции, текущее состояние, что делать дальше.

---

## ЧАСТЬ 1: ЧТО ТАКОЕ REPLICATOR И ЗАЧЕМ

### Идея владельца

Владелец (vladdd183) хочет создать **репозиторий, который развивает сам себя и может создавать другие репозитории**. Ключевые слова: "репликатор", "самоэволюционирующая система".

Три режима:
1. **Самоэволюция** -- система применяет свои инструменты к себе, улучшая собственный код
2. **Генерация** -- создание новых проектов (Porto-скелет, Nix-сборка, CI/CD)
3. **Legacy** -- работа с существующими кодовыми базами в их привычном стиле

### Философская основа

Владелец мыслит в терминах **децентрализации**:
- Web2 -- частный случай Web3 (централизация -- частный случай децентрализации)
- Система СЕЙЧАС работает на Web2 технологиях, но АРХИТЕКТУРНО готова к Web3
- Переход Web2 -> Web3 = замена адаптеров через DI, не переписывание логики
- Content-addressing (CID/хеш), DAG (Merkle-DAG), IPFS, Ceramic, libp2p -- всё это будущее, но архитектура уже заложена

### Что нравится владельцу

- **Porto** архитектура -- модульность, Ship/Containers, легко отсоединять модули в микросервисы
- **Nix** -- reproducible builds, декларативность
- **DSPy** -- сигнатуры вместо промптов, автооптимизация
- **MCP** -- стандартный tool protocol
- Слоистая архитектура -- легко менять и слои, и модули
- "Франкенштейн" -- собрать из имеющихся наработок

### Конкретные пожелания на следующий этап

Владелец хочет:
- **Чтобы система стала ЛУЧШЕ курсора** и могла сама себя улучшать
- **Opencode** (opencode.ai) -- open-source AI coding agent, можно интегрировать
- **OpenRouter** как провайдер для разных LLM моделей
- **AutoCrew или LangGraph** для мульти-агентной оркестрации
- Разные модели для разных задач (дешевая для тривиальных, мощная для сложных)

---

## ЧАСТЬ 2: ЧТО УЖЕ СДЕЛАНО

### Репозитории

- `vladdd183-org/hyper-porto` -- showcase/прототип Hyper-Porto v4.3 (GitHub, public)
- `vladdd183-org/replicator` -- форк hyper-porto, рабочая копия (GitHub, public)
- Локальная копия: `~/Desktop/kwork/replicator`

### Инфраструктура организации

- GitHub org: `vladdd183-org`
- Self-hosted NixOS runners (5 штук: `vladdd183-org-general-1..5`, idle)
- Runners: обычные, без snix (snix планируется позже)

### Документация (29 файлов, ~4000 строк)

Всё в `replicator/docs/`:

**Архитектура** (`docs/architecture/`):
- `00-vision.md` -- три режима, слои L0-L5, маппинг Cell -> Porto
- `01-layers.md` -- детали каждого слоя (Transport, Ship, Cell, Porto, Intelligence, Replication)
- `02-cell-model.md` -- CellSpec, Supervisor, Capabilities, фрактальность
- `03-adapter-neutrality.md` -- 5 Protocols, Web2/Web3 адаптеры, DI-переключение
- `04-porto-extensions.md` -- Ship/Adapters, Ship/Cell, 4 новых Section
- `05-replication-flow.md` -- Intent -> Spec -> Strategy -> Beads -> Execute -> Verify -> Promote
- `06-evolution-model.md` -- мутация, fitness test, promotion, governance

**Паттерны** (`docs/patterns/`):
- `result-railway.md` -- Result[T, E], @result_handler
- `gateway-adapter.md` -- Gateway (межмодульный) и Adapter (транспортный)
- `event-driven.md` -- Domain Events, подменяемые бэкенды
- `compass-maker.md` -- COMPASS + MAKER в Porto Containers
- `spec-bead-workflow.md` -- Intent -> MissionSpec -> Formula -> Molecule -> Bead
- `microservice-extraction.md` -- вынос Container

**Справочники** (`docs/reference/`): glossary, tech-stack, file-map

### Спецификации (specs/)

- `ship-adapters.spec.md` -- 5 Protocol-ов с acceptance criteria
- `ship-cell.spec.md` -- CellSpec, Supervisor, Capabilities, Registry
- `core-section.spec.md` -- SpecModule, CellRegistryModule, TemplateModule, EvolutionModule
- `agent-section.spec.md` -- CompassModule, MakerModule, OrchestratorModule
- `tool-section.spec.md` -- MCPClientModule, GitModule, NixModule, CICDModule
- `knowledge-section.spec.md` -- MemoryModule, KnowledgeGraphModule, SpecLibraryModule
- `cleanup-plan.md` -- что удалить (выполнено)
- `addition-plan.md` -- порядок добавления (6 этапов)

### Beads (specs/beads/)

33 атомарных задачи:
- **P0 (12 beads)**: Ship Foundation -- Core Types, Adapter Protocols, 5 Adapter реализаций, AdapterProvider, CellSpec, Capabilities, RegistryPort
- **P1 (12 beads)**: CoreSection (Spec, Registry, Template) + ToolSection (MCP, Git, Nix)
- **P2 (9 beads)**: AgentSection (COMPASS, MAKER, Orchestrator) + EvolutionModule + KnowledgeSection

### Cursor подмостки (.cursor/)

**Rules:**
- `replicator-core.mdc` (alwaysApply) -- главные правила
- `adapter-ports.mdc` -- правила адаптеров
- `cell-engine.mdc` -- правила CellSpec
- `sections.mdc` -- правила Sections
- + сохранены полезные: async-concurrency, result-pattern, events, testing, security, performance

**Agents:**
- `replicator-orchestrator.md` -- главный координатор
- `architect.md` -- архитектор
- `bead-executor.md` -- исполнитель задач
- + сохранены: implementer, refactorer, test-writer, implementation-verifier

**AGENTS.md** -- точка входа для AI

### foxdocs/ -- референс (430 md файлов)

Копии всех проектов-наработок:
- `research/` -- Fractal Atom, Sovereign Mesh, Autonomous Dev Mesh (12 заметок)
- `nn3w/` -- NixOS монорепа, Den aspects
- `factory-ai/` -- Grand Architecture, DSPy, frameworks
- `compass-maker/` -- COMPASS, MAKER, TRIFORCE
- `myaiteam/` -- Knowledge Graph, IPFS, team OS
- `fd_cicd/` -- Nix CI/CD research
- `python-uv-nix/` -- шаблон Python + Nix
- `hyper-porto-docs/` -- оригинальная документация Porto v4.3

### Очистка (выполнена)

Удалены 540 файлов (~87600 строк):
- Все demo-модули (AppSection: User, Order, Notification, Search, Settings, Audit; VendorSection: Email, Payment, Webhook)
- agent-os/, CLAUDE.md, DEVELOPMENT_PLAN.md, Docker-файлы
- Старые docs/, специфичные cursor-компоненты

Оставлено:
- Ship/ полностью (Core, Parents, Providers, Auth, CLI, Infrastructure, Middleware)
- Наша документация, спецификации, cursor-подмостки, foxdocs
- src/App.py -- минимальная точка входа
- src/Providers.py -- только AppProvider

---

## ЧАСТЬ 3: АРХИТЕКТУРА (КРАТКАЯ СВОДКА)

### Слои

```
L0  ТРАНСПОРТ        Ship/Adapters/   (StoragePort, MessagingPort, IdentityPort, StatePort, ComputePort)
L1  ИНФРАСТРУКТУРА   Ship/            (Core, Parents, Providers, Infrastructure, Auth, CLI)
L2  РАНТАЙМ          Ship/Cell/       (CellSpec, Supervisor, Capabilities)
L3  СТРУКТУРА КОДА   Containers/      (Actions, Tasks, Queries, Events -- Porto)
L4  ИНТЕЛЛЕКТ        AgentSection/    (COMPASS стратегия, MAKER надежность, DSPy оптимизация)
L5  РЕПЛИКАЦИЯ       CoreSection/     (Spec, Registry, Templates, Evolution)
```

### Маппинг

| Концепция | Porto реализация |
|---|---|
| Cell (единица вычислений) | Container (папка с Actions, Tasks, Events) |
| Spec (ДНК) | CellSpec (frozen dataclass) |
| Capabilities (мембрана) | DI providers + Capability tokens |
| State (память) | UnitOfWork + Repository + Events |
| Aspect (композиция) | Section + App.py |
| Layer (коммуникация) | Ship/Adapters/ Protocols |
| Adapter (окружение) | Конкретные реализации Protocols |

### 5 портов

```python
StoragePort   -- put/get/exists/delete/list_prefix (LocalFS | S3 | IPFS)
StatePort     -- get/update/create/history (SQLite | Postgres | Ceramic)
MessagingPort -- publish/subscribe/request (InMemory | NATS | libp2p)
IdentityPort  -- verify/issue/delegate/revoke (JWT | UCAN)
ComputePort   -- execute (subprocess | Docker | IPVM)
```

### 4 Section-а

```
CoreSection/      SpecModule, CellRegistryModule, TemplateModule, EvolutionModule
AgentSection/     CompassModule, MakerModule, OrchestratorModule
ToolSection/      MCPClientModule, GitModule, NixModule, CICDModule
KnowledgeSection/ MemoryModule, KnowledgeGraphModule, SpecLibraryModule
```

### Pipeline репликации

```
Intent -> SpecModule (MissionSpec) -> CompassModule (Strategy) -> MakerModule (Beads) -> OrchestratorModule (Execute) -> EvolutionModule (Verify + Promote)
```

### Ключевые паттерны

- **Result Railway** -- все Actions возвращают `Result[T, E]`
- **Domain Events** -- межмодульное общение через события
- **Gateway Pattern** -- синхронная межмодульная связь через Protocol
- **Adapter Pattern** -- инфраструктура за Protocol, DI-переключение
- **CQRS** -- Action для записи, Query для чтения
- **Structured Concurrency** -- anyio TaskGroup

---

## ЧАСТЬ 4: ЧТО ДЕЛАТЬ ДАЛЬШЕ

### Немедленно: P0 Ship Foundation (12 beads)

Это critical path. Без него ничто другое невозможно:

1. `Ship/Core/Types.py` -- расширить базовые типы (CID, Identity, Capability, ComputeResult)
2. `Ship/Adapters/Protocols.py` -- 5 Protocol-ов
3. `Ship/Adapters/Errors.py` -- типизированные ошибки
4. `Ship/Adapters/Storage/LocalAdapter.py` -- файловое хранилище
5. `Ship/Adapters/Messaging/InMemoryAdapter.py` -- in-memory pub/sub
6. `Ship/Adapters/Identity/JWTAdapter.py` -- обертка над Ship/Auth/JWT
7. `Ship/Adapters/State/SQLiteAdapter.py` -- SQLite state
8. `Ship/Adapters/Compute/SubprocessAdapter.py` -- subprocess execution
9. `Ship/Providers/AdapterProvider.py` -- DI для адаптеров
10. `Ship/Cell/CellSpec.py` -- спецификация Cell
11. `Ship/Cell/Capabilities.py` -- capability tokens
12. `Ship/Cell/Registry.py` -- Registry Protocol

Детальные acceptance criteria для каждого bead -- в `specs/beads/p0-ship-foundation.md`.

### Затем: интеграция AI-рантайма

Вот где система оживает. Варианты, которые рассматривает владелец:

#### Вариант A: Opencode + LangGraph

- **Opencode** (opencode.ai) -- open-source AI coding agent, terminal-based
- Можно интегрировать как ToolSection модуль или как внешний orchestrator
- **LangGraph** -- graph runtime для controllable agent workflows
- LangGraph как runtime для OrchestratorModule
- Opencode как execution engine для code beads

#### Вариант B: AutoCrew / CrewAI

- Multi-agent orchestration из коробки
- Но: слаб как durable execution core (из исследования 12-comparison-matrix)
- Подходит скорее для demos и простых workflow

#### Вариант C: Thin custom orchestrator + MCP + DSPy

- Рекомендуется исследованием 10-autonomous-dev-mesh
- Temporal как durable outer loop
- MCP для tool integration
- DSPy для prompt optimization
- Наибольший контроль, но больше работы

#### Рекомендация

**Гибрид: LangGraph для orchestration + MCP для tools + DSPy для prompts + OpenRouter для LLM providers.**

Почему:
- LangGraph (оценка 4/5 по всем метрикам в comparison matrix) -- лучший баланс
- MCP (оценка 5/5) -- стандартный tool plane
- DSPy -- самоулучшающиеся промпты
- OpenRouter -- доступ к любой модели (GPT-4, Claude, Gemini, Llama, GLM, ...)
- Temporal можно добавить позже для durability

### Порядок интеграции AI

1. **P0: Ship Foundation** (адаптеры + Cell engine)
2. **ToolSection/MCPClientModule** -- подключение MCP-инструментов
3. **Настройка OpenRouter** -- конфиг моделей в Settings
4. **AgentSection/CompassModule** -- стратегия (LangGraph graph + DSPy)
5. **AgentSection/MakerModule** -- декомпозиция (LangGraph + parallel execution)
6. **AgentSection/OrchestratorModule** -- исполнение BeadGraph (LangGraph runtime)
7. **CoreSection/EvolutionModule** -- verification + promotion
8. **CLI команды** -- `replicator evolve`, `replicator generate`

### Модели для разных задач

| Задача | Рекомендуемая модель | Почему |
|---|---|---|
| Компиляция spec | Claude/GPT-4 | Нужно глубокое понимание |
| Стратегия (COMPASS) | Claude/GPT-4 | Нужно рассуждение |
| Декомпозиция (MAKER) | Claude/GPT-4o | Баланс цена/качество |
| Исполнение code beads | Claude/GPT-4 | Нужно качество кода |
| K-Voting agents | Gemini Flash / Llama | Дешевые, для параллелизма |
| Review | Claude | Лучший для review |
| Simple refactoring | GPT-4o-mini / GLM | Быстро и дешево |

Через OpenRouter можно маршрутизировать по сложности.

---

## ЧАСТЬ 5: ТЕХСТЕК

### Текущий (установлен)

- Python 3.13+, uv (package manager)
- Litestar (web), Dishka (DI), Returns (Result), anyio (async), Pydantic v2
- Piccolo ORM, Logfire (telemetry)
- Nix (flakes), nix2container

### Нужно добавить

- `langgraph` -- agent orchestration runtime
- `dspy-ai` -- prompt optimization framework
- `openai` или `litellm` -- LLM client (через OpenRouter)
- `mcp` -- Model Context Protocol SDK
- `graphiti-core` или аналог -- knowledge graph (позже)
- `mem0ai` -- agent memory (позже)

### CI/CD

- GitHub Actions с self-hosted NixOS runners (5 шт, уже работают)
- Обычные runners (без snix пока)
- nix2container для OCI-образов

---

## ЧАСТЬ 6: КЛЮЧЕВЫЕ ФАЙЛЫ ДЛЯ ИЗУЧЕНИЯ

### Обязательно прочитать первым делом

```
docs/architecture/00-vision.md          -- ЧТО и ЗАЧЕМ
docs/architecture/01-layers.md          -- КАК устроено
docs/reference/glossary.md              -- ТЕРМИНОЛОГИЯ
docs/reference/file-map.md              -- ГДЕ ЧТО ЛЕЖИТ
specs/addition-plan.md                  -- ПОРЯДОК РАБОТЫ
specs/beads/p0-ship-foundation.md       -- СЛЕДУЮЩИЕ ЗАДАЧИ
AGENTS.md                               -- КОНТЕКСТ ДЛЯ AI
```

### При работе с конкретными частями

```
docs/architecture/03-adapter-neutrality.md  -- при работе с адаптерами
docs/architecture/02-cell-model.md          -- при работе с CellSpec
docs/architecture/05-replication-flow.md    -- при работе с pipeline
docs/patterns/compass-maker.md              -- при работе с агентами
specs/agent-section.spec.md                 -- спецификация агентов
specs/tool-section.spec.md                  -- спецификация инструментов
```

### Референс прошлых проектов

```
foxdocs/research/00-FRACTAL-ATOM.md                    -- теория Cell
foxdocs/research/02-SOVEREIGN-MESH.md                  -- как проекты связаны
foxdocs/factory-ai/06-GRAND-ARCHITECTURE.md            -- 5-слойный стек
foxdocs/compass-maker/TRIFORCE_ARCHITECTURE_RU.md      -- COMPASS+MAKER+Porto
foxdocs/research/10-autonomous-dev-mesh/12-*.md         -- recommended stack
foxdocs/hyper-porto-docs/                              -- оригинальные Porto docs
```

---

## ЧАСТЬ 7: КОНКРЕТНЫЙ ПЛАН ДЕЙСТВИЙ

### Фаза 1: Ship Foundation (сейчас)

Реализовать 12 P0 beads из `specs/beads/p0-ship-foundation.md`. Каждый bead имеет acceptance criteria. После -- система имеет адаптерную абстракцию и Cell engine.

### Фаза 2: Core + Tools (следующая)

Параллельно:
- CoreSection: SpecModule, CellRegistryModule, TemplateModule
- ToolSection: MCPClientModule, GitModule, NixModule

### Фаза 3: AI Integration

- Настроить OpenRouter в Settings
- Реализовать AgentSection: CompassModule + MakerModule + OrchestratorModule
- Интегрировать LangGraph как runtime
- Интегрировать DSPy для prompt optimization

### Фаза 4: Self-Evolution

- EvolutionModule (verify + promote)
- CLI: `replicator evolve <intent>`
- Первый тест: система улучшает саму себя

### Фаза 5: Generation + Legacy

- CLI: `replicator generate <spec>`
- Работа с legacy репозиториями
- KnowledgeSection для долгосрочной памяти

### Фаза 6: Beyond Cursor

- Система работает автономно, не нуждается в IDE
- Интеграция с Opencode для terminal-based execution
- Webhook/API для запуска из Huly/GitHub Issues
- Мульти-модельная маршрутизация по сложности задач
