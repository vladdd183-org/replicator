# Слои архитектуры Replicator

> Детальное описание каждого слоя: от транспорта до метауровня репликации.

---

## Общая картина

```
+=========================================================================+
|  L5  РЕПЛИКАЦИЯ                                                          |
|  SpecModule, TemplateModule, EvolutionModule, CellRegistryModule        |
+=========================================================================+
|  L4  ИНТЕЛЛЕКТ                                                           |
|  CompassModule (стратегия), MakerModule (надежность), DSPy (оптимизация)|
+=========================================================================+
|  L3  СТРУКТУРА КОДА (Porto)                                              |
|  Containers/{Section}/{Module}/ -> Actions, Tasks, Queries, Events      |
+=========================================================================+
|  L2  РАНТАЙМ (Cell Engine)                                               |
|  Ship/Cell/ -> CellSpec, Supervisor, Capabilities                       |
+=========================================================================+
|  L1  ИНФРАСТРУКТУРА (Ship)                                               |
|  Ship/ -> Core, Parents, Providers, Infrastructure, Auth, CLI, Middleware|
+=========================================================================+
|  L0  ТРАНСПОРТНАЯ ТКАНЬ                                                  |
|  Ship/Adapters/ -> StoragePort, MessagingPort, IdentityPort, StatePort  |
+=========================================================================+
```

---

## L0: Транспортная ткань

**Ответственность:** как данные перемещаются между компонентами и внешним миром.

**Реализация:** `Ship/Adapters/` -- набор Protocol-интерфейсов с подменяемыми реализациями.

| Port (Protocol) | Web2 реализация | Web3 реализация (будущее) |
|---|---|---|
| `StoragePort` | LocalFS, S3, MinIO | IPFS, Filecoin |
| `StatePort` | PostgreSQL, SQLite, Redis | Ceramic (ComposeDB) |
| `MessagingPort` | InMemory, NATS, Redis Pub/Sub | libp2p (Lattica) |
| `IdentityPort` | JWT, OAuth2 | DID + UCAN |
| `ComputePort` | Docker, subprocess | IPVM (Homestar) |

**Принцип переключения:** через Dishka DI Provider. Один Provider на окружение:

```python
class Web2AdapterProvider(Provider):
    scope = Scope.APP
    storage = provide(LocalStorageAdapter, provides=StoragePort)
    messaging = provide(NATSMessagingAdapter, provides=MessagingPort)
    identity = provide(JWTIdentityAdapter, provides=IdentityPort)

class Web3AdapterProvider(Provider):
    scope = Scope.APP
    storage = provide(IPFSStorageAdapter, provides=StoragePort)
    messaging = provide(LatticaMessagingAdapter, provides=MessagingPort)
    identity = provide(UCANIdentityAdapter, provides=IdentityPort)
```

**Порядок прогрессивной децентрализации:**
1. Storage первым (минимальный риск, дедупликация)
2. State вторым (Ceramic для мутабельных данных)
3. Identity третьим (DID+UCAN вместо JWT)
4. Messaging последним (самый чувствительный к latency)

---

## L1: Инфраструктура (Ship)

**Ответственность:** общий код для всех Container-ов. Фундамент.

**Структура:**

```
Ship/
  Core/                     Базовые типы, Result, Protocols, ошибки
    BaseSchema.py           EntitySchema (from_entity)
    Errors.py               BaseError, ErrorWithTemplate, DomainException
    Protocols.py            typing.Protocol интерфейсы
    Types.py                Общие типы (CID, Identity, Capability)

  Parents/                  Абстрактные базовые классы
    Action.py               Action[Input, Output, Error] -> Result
    Task.py                 Task[Input, Output], SyncTask
    Query.py                Query[Input, Output], SyncQuery
    Repository.py           Repository[T]
    UnitOfWork.py           BaseUnitOfWork (транзакции + events)
    Event.py                DomainEvent

  Adapters/                 Порты и адаптеры (L0)
    Protocols.py            StoragePort, MessagingPort, IdentityPort, StatePort
    Storage/                Реализации StoragePort
    Messaging/              Реализации MessagingPort
    Identity/               Реализации IdentityPort
    State/                  Реализации StatePort

  Providers/                DI провайдеры (Dishka)
    AppProvider.py          Settings, JWT, общие сервисы
    AdapterProvider.py      Выбор адаптеров по окружению

  Infrastructure/           Внешние сервисы
    Cache/                  Кеширование
    Database/               Утилиты БД
    Telemetry/              Logfire + RequestLogging
    Workers/                TaskIQ фоновые задачи

  Auth/                     Аутентификация
  CLI/                      Команды CLI + генераторы
  Configs/                  Pydantic BaseSettings
  Decorators/               @result_handler и другие
  Exceptions/               RFC 9457 Problem Details
  Middleware/               Idempotency, Rate Limiting
```

**Правило:** Ship НИКОГДА не импортирует из Containers. Containers импортируют из Ship.

---

## L2: Рантайм (Cell Engine)

**Ответственность:** жизненный цикл Cell (= Container в runtime), изоляция, capabilities.

**Структура:**

```
Ship/Cell/
  CellSpec.py               Спецификация Cell: что она умеет, что ей нужно
  Supervisor.py             Lifecycle: spawn, health check, restart, shutdown
  Capabilities.py           UCAN-подобные capability tokens
  Budget.py                 Ресурсные лимиты (CPU, RAM, network)
```

**CellSpec** -- декларативное описание Container как исполняемой единицы:

```python
@dataclass(frozen=True)
class CellSpec:
    name: str                           # уникальное имя
    version: str                        # семантическая версия
    spec_hash: str                      # хеш спецификации (-> CID в будущем)
    capabilities_required: list[str]    # какие capabilities нужны
    dependencies: list[str]             # от каких Cell зависит
    resources: ResourceBudget           # лимиты ресурсов
    health_check: HealthCheckConfig     # как проверять здоровье
```

В Web2 это метаданные. В Web3 `spec_hash` станет CID, а `capabilities_required` станут UCAN tokens.

---

## L3: Структура кода (Porto)

**Ответственность:** организация бизнес-логики внутри модулей.

**Принцип:** Ship + Containers. Каждый Container -- изолированный бизнес-модуль.

```
Containers/
  {Section}/
    {Module}/
      Actions/              Use Cases (CQRS Commands)
      Tasks/                Атомарные операции
      Queries/              CQRS Queries (read-only)
      Data/
        Repositories/       Доступ к данным
        Schemas/            Request/Response DTO (Pydantic)
        UnitOfWork.py       Транзакции + Events
      Models/               Domain Models (Piccolo Tables)
      UI/
        API/                HTTP REST Controllers
        CLI/                Click Commands
        WebSocket/          Litestar Channels
        Workers/            TaskIQ Background Tasks
      Events.py             Domain Events
      Listeners.py          Event Handlers
      Errors.py             Ошибки модуля (Pydantic frozen)
      Providers.py          DI регистрация (Dishka)
```

**Правила:**
- Container НЕ импортирует из другого Container напрямую
- Межмодульное общение -- через Domain Events
- Синхронные зависимости -- через Gateway Pattern (Protocol + Adapter)
- Все Actions возвращают `Result[T, E]`
- CQRS: Actions для записи, Queries для чтения

---

## L4: Интеллект (Агенты)

**Ответственность:** стратегическое мышление, надежное исполнение, самоулучшение.

**Три подсистемы:**

| Подсистема | Источник | Реализация в Porto |
|---|---|---|
| **COMPASS** | Meta-Thinker + Context Manager | `AgentSection/CompassModule/` |
| **MAKER** | MAD + K-Voting + Red-Flagging | `AgentSection/MakerModule/` |
| **DSPy** | Prompt optimization, MIPROv2 | DSPy-модули внутри Actions |

**COMPASS** решает ЧТО делать:
- Meta-Thinker анализирует контекст и формирует стратегию
- Context Manager поддерживает долгосрочные заметки и формирует briefы

**MAKER** решает КАК делать надежно:
- MAD декомпозирует задачу на микрошаги
- K-Voting запускает K параллельных решений и голосует
- Red-Flagging фильтрует ненадежные ответы

**DSPy** решает КАК делать оптимально:
- Сигнатуры вместо промптов
- MIPROv2 optimizer автоматически подбирает промпты
- Метрики -> оптимизация -> лучшие промпты

---

## L5: Репликация (Мета-слой)

**Ответственность:** самомодификация системы, генерация новых репозиториев, эволюция.

**Четыре модуля:**

| Модуль | Ответственность |
|---|---|
| `SpecModule` | Компиляция intent -> MissionSpec -> Formula |
| `TemplateModule` | Генерация Porto-скелетов, flake.nix, CI |
| `CellRegistryModule` | Реестр всех спецификаций Cell/Container |
| `EvolutionModule` | Мутация, fitness test, promotion |

**Pipeline репликации:**

```
Intent (человек/агент)
    |
    v
SpecModule.CompileSpecAction
    |   Вход: текст intent
    |   Выход: MissionSpec (структурированная спецификация)
    v
CompassModule.StrategizeAction
    |   Вход: MissionSpec + контекст
    |   Выход: StrategyPlan (стратегия + риски + подход)
    v
MakerModule.DecomposeAction
    |   Вход: StrategyPlan
    |   Выход: BeadGraph (граф атомарных задач)
    v
OrchestratorModule.ExecuteAction
    |   Вход: BeadGraph
    |   Выход: ExecutionResult (артефакты + evidence)
    v
EvolutionModule.VerifyAction
    |   Вход: ExecutionResult
    |   Выход: VerificationReport (pass/fail + evidence bundle)
    v
EvolutionModule.PromoteAction (если pass)
    |   Вход: VerificationReport + артефакты
    |   Выход: Promoted artifacts (merge, publish, deploy)
    v
CellRegistryModule.RegisterAction
        Вход: новая/обновленная спецификация
        Выход: обновленный реестр
```

---

## Взаимодействие слоев

```
L5 Репликация         использует     L4 (стратегия), L3 (структура), L2 (CellSpec)
L4 Интеллект          живет внутри   L3 (Porto Containers), использует L1 (Ship)
L3 Porto              использует     L1 (Parents, Core), L0 (Adapters)
L2 Cell Engine        расширяет      L1 (Ship), использует L0 (Adapters)
L1 Ship               использует     L0 (Adapters)
L0 Adapters           самостоятелен   (протоколы + реализации)
```

Ключевое: L5 (Репликация) может модифицировать ЛЮБОЙ слой, включая себя. Это и делает систему самоэволюционирующей.
