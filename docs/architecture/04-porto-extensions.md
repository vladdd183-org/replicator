# Расширения Porto для Replicator

> Что добавляется к базовому Hyper-Porto: Ship/Adapters, Ship/Cell, новые Sections.

---

## Базовый Hyper-Porto (что уже есть)

Hyper-Porto v4.3 дает:

- **Ship/** -- инфраструктурное ядро (Parents, Core, Providers, Auth, CLI, Middleware, Infrastructure)
- **Containers/{Section}/{Module}/** -- модульная структура с Actions, Tasks, Queries, Events
- **Result Railway** -- `Result[T, E]` через `returns` библиотеку
- **CQRS** -- разделение Action (write) и Query (read)
- **Domain Events** -- через UoW + litestar.events
- **DI** -- Dishka (scoped providers)
- **Structured Concurrency** -- anyio TaskGroups

Это рабочий, протестированный фундамент. Replicator не заменяет его, а расширяет.

---

## Расширение 1: Ship/Adapters (новое)

**Зачем:** Porto не имеет встроенной абстракции транспортного слоя. Adapters вводят Protocol-based абстракцию для storage, messaging, identity, state, compute.

**Структура:**

```
Ship/Adapters/
  __init__.py
  Protocols.py              # все Protocol-интерфейсы в одном месте
  Storage/
    __init__.py
    LocalAdapter.py         # LocalFS реализация
    S3Adapter.py            # S3/MinIO реализация (будущее)
  Messaging/
    __init__.py
    InMemoryAdapter.py      # для тестов
    LitestarEventsAdapter.py # litestar.events wrapper
    NATSAdapter.py          # NATS реализация (будущее)
  Identity/
    __init__.py
    JWTAdapter.py           # текущая JWT реализация
  State/
    __init__.py
    PostgresAdapter.py      # текущий PostgreSQL/Piccolo
    SQLiteAdapter.py        # для разработки
  Compute/
    __init__.py
    SubprocessAdapter.py    # subprocess/shell execution
```

**Интеграция с существующим Ship:** текущие Auth/JWT, Infrastructure/Database, litestar.events -- это и есть Web2 адаптеры. Мы не переписываем их, а оборачиваем в Protocol-интерфейс.

---

## Расширение 2: Ship/Cell (новое)

**Зачем:** Porto не имеет понятия "спецификация модуля как объект". CellSpec превращает Container из структуры папок в адресуемую, версионируемую, инстанцируемую единицу.

**Структура:**

```
Ship/Cell/
  __init__.py
  CellSpec.py               # @dataclass(frozen=True) спецификация
  Supervisor.py             # lifecycle: spawn, health, restart, evolve
  Capabilities.py           # capability tokens (RBAC сейчас, UCAN потом)
  Budget.py                 # ресурсные лимиты
  Registry.py               # Protocol для реестра спецификаций
```

**Связь с Porto:** каждый Container МОЖЕТ (не обязан) иметь `cell_spec.py` рядом с `Providers.py`. Это декларативное описание модуля.

---

## Расширение 3: Новые Sections (структура Containers)

### Текущий Hyper-Porto:

```
Containers/
  AppSection/               # бизнес-модули приложения
    UserModule/
    OrderModule/
    ...
  VendorSection/            # интеграции с внешними сервисами
    EmailModule/
    PaymentModule/
    ...
```

### Replicator добавляет:

```
Containers/
  CoreSection/              # ЯДРО репликатора
    SpecModule/             # intent -> MissionSpec -> Formula
    CellRegistryModule/     # реестр спецификаций Cell
    TemplateModule/         # генерация Porto-скелетов
    EvolutionModule/        # мутация, тестирование, promotion

  AgentSection/             # ИНТЕЛЛЕКТ
    CompassModule/          # Meta-Thinker + Context Manager (COMPASS)
    MakerModule/            # MAD + K-Voting + Red-Flagging (MAKER)
    OrchestratorModule/     # координация агентов, A2A contracts

  ToolSection/              # ИНСТРУМЕНТЫ
    MCPClientModule/        # MCP tool integration (стандартный протокол)
    GitModule/              # git operations, worktree management
    NixModule/              # Nix build, nix2container, flake generation
    CICDModule/             # pipeline generation, runners

  KnowledgeSection/         # ЗНАНИЯ
    MemoryModule/           # agent memory (Mem0-like)
    KnowledgeGraphModule/   # temporal knowledge graph (Graphiti-like)
    SpecLibraryModule/      # библиотека OpenSpec шаблонов

  AppSection/               # ПРИКЛАДНЫЕ (пользовательские)
    ...                     # любые бизнес-модули
```

---

## Расширение 4: Ship/CLI расширения

**Зачем:** Porto CLI генерирует стандартные компоненты (Action, Task, Query). Replicator добавляет мета-команды.

**Новые CLI команды:**

```bash
# Стандартные Porto (уже есть)
replicator make:action UserModule CreateUser
replicator make:task UserModule HashPassword
replicator make:module AppSection PaymentModule

# Новые Replicator
replicator init <name>              # инициализировать новый Porto-проект
replicator evolve <intent>          # запустить pipeline самоэволюции
replicator generate <spec-file>     # сгенерировать код из спецификации
replicator cell:list                # показать все зарегистрированные Cell
replicator cell:inspect <name>      # детали конкретной Cell
replicator cell:health              # здоровье всех Cell
replicator spec:compile <intent>    # скомпилировать intent в MissionSpec
replicator spec:validate <file>     # валидировать спецификацию
```

---

## Расширение 5: Усиленная Event Bus

**Базовый Porto:** `litestar.events` (in-memory) + `UoW.add_event()`.

**Replicator расширяет** через Unified Event Bus с подменяемыми бэкендами:

```python
class EventBusPort(Protocol):
    async def emit(self, event: DomainEvent) -> None: ...
    async def subscribe(self, event_type: str, handler: Callable) -> None: ...

class InMemoryEventBus(EventBusPort):     # тесты
class LitestarEventBus(EventBusPort):     # монолит
class NATSEventBus(EventBusPort):         # микросервисы
class LibP2PEventBus(EventBusPort):       # Web3 (будущее)
```

---

## Что НЕ меняется

| Компонент | Статус | Пояснение |
|---|---|---|
| Parents/Action.py | Без изменений | `Action[Input, Output, Error] -> Result` |
| Parents/Task.py | Без изменений | `Task[Input, Output]`, `SyncTask` |
| Parents/Query.py | Без изменений | `Query[Input, Output]` |
| Parents/Repository.py | Без изменений | `Repository[T]` |
| Parents/UnitOfWork.py | Без изменений | `BaseUnitOfWork` |
| Core/Errors.py | Без изменений | `BaseError`, `ErrorWithTemplate` |
| Decorators/result_handler.py | Без изменений | `@result_handler` |
| Providers/ | Расширяется | Добавляется `AdapterProvider` |
| Infrastructure/ | Расширяется | Существующий код становится адаптерами |

Ключевой принцип: **расширяем, не ломаем**. Весь существующий Hyper-Porto код продолжает работать.
