# Глоссарий Replicator

> Все ключевые термины в одном месте.

---

## Архитектурные концепции

| Термин | Определение |
|---|---|
| **Cell** | Единица вычислений: f(Spec, Capabilities, State). Маппится на Porto Container. |
| **CellSpec** | Декларативная спецификация Cell: actions, capabilities, dependencies, resources. |
| **Aspect** | Параметрическая композиция: как Cell-ы компонуются вместе. В Porto = Section + App.py. |
| **Layer** | Канал коммуникации: Storage, State, Messaging. В Porto = Ship/Adapters. |
| **Adapter** | Конкретная реализация Layer-а для определенного окружения. Web2 или Web3. |
| **Port** | Protocol-интерфейс адаптера (StoragePort, MessagingPort). Абстракция транспорта. |

## Porto-терминология

| Термин | Определение |
|---|---|
| **Ship** | Общая инфраструктура: Parents, Core, Providers, Adapters. НЕ импортирует из Containers. |
| **Container** | Изолированный бизнес-модуль: Actions + Tasks + Queries + Data + UI + Events. |
| **Section** | Группа Container-ов по домену: CoreSection, AgentSection, ToolSection. |
| **Action** | Use Case. Всегда возвращает Result[T, E]. Оркестрирует Tasks. |
| **Task** | Атомарная операция. Переиспользуема между Actions. |
| **SyncTask** | Синхронный Task для CPU-bound операций (хеширование, парсинг). |
| **Query** | CQRS Query: read-only операция. Не модифицирует состояние. |
| **Repository** | Доступ к данным. Инкапсулирует ORM/SQL. |
| **UnitOfWork** | Транзакция + события. Commit публикует Domain Events. |
| **Domain Event** | Событие бизнес-домена: UserCreated, OrderCancelled. |
| **Gateway** | Protocol для синхронной межмодульной связи. Direct / HTTP реализации. |
| **Provider** | DI-провайдер (Dishka). Связывает Protocol с реализацией. |

## Spec-Bead Workflow

| Термин | Определение |
|---|---|
| **Intent** | Высокоуровневое намерение: что нужно изменить и зачем. |
| **MissionSpec** | Структурированная формулировка Intent: acceptance criteria, constraints, risks. |
| **Formula** | Декларативный шаблон workflow. Рецепт, из которого инстанцируется Molecule. |
| **Molecule** | Связанный граф Bead-ов -- конкретный инстанс Formula. |
| **Bead** | Атомарная единица работы с четким acceptance criteria. |
| **BeadGraph** | DAG из Bead-ов с зависимостями и параллельными группами. |
| **Workcell** | Изолированная среда исполнения Bead: worktree, container, sandbox. |
| **Evidence Bundle** | Пакет доказательств: тесты, логи, метрики, diff, review verdict. |

## Агентская архитектура

| Термин | Определение |
|---|---|
| **COMPASS** | Стратегическое мышление: Meta-Thinker + Context Manager. |
| **Meta-Thinker** | Стратег: формирует план, мониторит прогресс, обнаруживает аномалии. |
| **Context Manager** | Управляет контекстом: Notes (долгосрочные), Briefs (краткие для агентов). |
| **MAKER** | Надежное исполнение: MAD + K-Voting + Red-Flagging. |
| **MAD** | Micro-Agent Decomposition: разбиение задачи на микрошаги. |
| **K-Voting** | K параллельных агентов голосуют за лучший результат. |
| **Red-Flagging** | Фильтрация ненадежных ответов по confidence score. |
| **DSPy** | Фреймворк: сигнатуры вместо промптов, автоматическая оптимизация. |
| **MCP** | Model Context Protocol: стандартный протокол для подключения инструментов. |
| **A2A** | Agent-to-Agent: протокол координации между агентами. |

## Эволюция

| Термин | Определение |
|---|---|
| **Мутация** | Создание новой версии CellSpec (расширение, модификация, рефакторинг). |
| **Fitness Test** | Verification Lattice: тесты, lint, type check, architecture guards, review. |
| **Promotion** | Перевод VERIFIED версии в ACTIVE: merge, publish, deploy. |
| **Rollback** | Откат к предыдущей ACTIVE версии при failure. |
| **Governance** | Правила: кто решает о promotion (автомат / агент / человек / ADR). |

## Децентрализация (Web3, будущее)

| Термин | Определение |
|---|---|
| **CID** | Content Identifier. hash(content + links). Уникальный, детерминированный, вечный. |
| **IPFS** | InterPlanetary File System. Content-addressed хранилище. |
| **Ceramic** | Мутабельные потоки данных с верифицируемой историей. |
| **libp2p** | P2P networking stack: transports, encryption, discovery. |
| **UCAN** | User Controlled Authorization Network. Capability-based auth с delegation. |
| **DID** | Decentralized Identifier. Самосуверенная криптографическая идентичность. |
| **IPVM** | InterPlanetary Virtual Machine. WASM execution на IPFS данных. |

## Инфраструктура

| Термин | Определение |
|---|---|
| **Nix** | Декларативный package manager и build system. Reproducible builds. |
| **nix2container** | Инкрементальная OCI-сборка из Nix: минимальные слои, контроль. |
| **Litestar** | ASGI web framework: HTTP, WebSocket, GraphQL, CLI. |
| **Dishka** | DI container: scoped providers, auto-resolution. |
| **Returns** | Функциональные контейнеры: Result[T, E], Maybe, IO. |
| **anyio** | Structured concurrency: TaskGroups, backend-agnostic async. |
| **Temporal** | Durable workflow engine: retries, timeouts, long-running. |
| **Piccolo** | Async ORM для PostgreSQL/SQLite. |
