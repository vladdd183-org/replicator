# Карта файлов Replicator

> Какой файл за что отвечает. Текущая структура + планируемые расширения.

---

## Текущая структура (наследие Hyper-Porto)

```
src/
  App.py                                # Точка входа. Сборка роутеров, listeners, DI, plugins.
  Providers.py                          # Агрегатор всех DI providers.

  Ship/                                 # ИНФРАСТРУКТУРНОЕ ЯДРО (L1)
    Core/
      __init__.py
      BaseSchema.py                     # EntitySchema: автоматический from_entity()
      Errors.py                         # BaseError, ErrorWithTemplate, DomainException
      GatewayErrors.py                  # Ошибки Gateway (межмодульная связь)
      Protocols.py                      # typing.Protocol интерфейсы
      Types.py                          # Общие типы
    Parents/
      Action.py                         # Action[Input, Output, Error] -> Result
      Task.py                           # Task[Input, Output], SyncTask[Input, Output]
      Query.py                          # Query[Input, Output], SyncQuery
      Repository.py                     # Repository[T]
      UnitOfWork.py                     # BaseUnitOfWork (транзакции + events)
      Event.py                          # DomainEvent base class
    Providers/
      AppProvider.py                    # Settings, JWT, get_all_providers()
      __init__.py
    Auth/
      Guards.py                         # auth_guard, optional_auth_guard
      JWT.py                            # JWTService
      Middleware.py                      # AuthenticationMiddleware
    CLI/
      PortoCLI.py                       # CLI entry point
      Generator.py                      # Генератор компонентов
      Templates/                        # Jinja2 шаблоны для генерации
    Configs/
      Settings.py                       # Pydantic BaseSettings
    Decorators/
      result_handler.py                 # @result_handler (Result -> Response)
      cache_utils.py                    # invalidate_cache
    Exceptions/
      ProblemDetails.py                 # RFC 9457 Problem Details
    GraphQL/
      Context.py                        # GraphQL context
      Schema.py                         # Root Query + Mutation
    Infrastructure/
      Cache/                            # Cashews + Redis
      Concurrency/                      # Limiter, TaskGroup helpers
      Database/                         # DB utilities
      Events/                           # Event Bus infrastructure
        Factory.py                      # EventBus factory
        Provider.py                     # EventBus provider
        Protocol.py                     # EventBus protocol
        Backends/
          InMemory.py                   # In-memory backend
        Outbox/                         # Transactional Outbox
      HealthCheck.py                    # Liveness/Readiness
      Telemetry/                        # Logfire + RequestLogging
      Temporal/                         # Temporal integration
        Saga/                           # SAGA patterns
      Workers/                          # TaskIQ broker
    Middleware/
      Idempotency.py                    # Idempotency middleware
      Errors.py                         # Middleware errors
      __init__.py

  Containers/                           # БИЗНЕС-МОДУЛИ (L3)
    AppSection/                         # [DEMO -- будет заменен на CoreSection etc.]
      UserModule/                       # Пример полного модуля
        Actions/                        # CreateUser, Authenticate, UpdateUser, DeleteUser, ...
        Tasks/                          # HashPassword, VerifyPassword, GenerateToken, ...
        Queries/                        # GetUser, ListUsers
        Data/
          Repositories/                 # UserRepository
          Schemas/                      # Request/Response DTOs
          UnitOfWork.py                 # UserUnitOfWork
        Models/                         # AppUser (Piccolo Table) + migrations
        UI/
          API/Controllers/              # UserController, AuthController
          API/Routes.py                 # Router
          CLI/Commands.py               # CLI commands
          GraphQL/Resolvers.py          # GraphQL resolvers
          WebSocket/Handlers.py         # WebSocket handlers
          Workers/Tasks.py              # TaskIQ background tasks
        Gateways/                       # PaymentGateway (Protocol + types)
        Events.py                       # UserCreated, UserUpdated, UserDeleted
        Listeners.py                    # Event handlers
        Errors.py                       # UserError, UserNotFoundError, ...
        Providers.py                    # UserModuleProvider, UserRequestProvider
      OrderModule/                      # Пример с Saga patterns
      NotificationModule/               # Пример Events
      SearchModule/                     # Пример indexing
      SettingsModule/                   # Пример feature flags
      AuditModule/                      # Пример audit trail
    VendorSection/                      # [DEMO -- будет удален]
      EmailModule/
      PaymentModule/
      WebhookModule/
```

---

## Планируемые расширения

```
  Ship/                                 # Расширения к существующему Ship
    Adapters/                           # [НОВОЕ] Порты и адаптеры (L0)
      __init__.py
      Protocols.py                      # StoragePort, MessagingPort, IdentityPort, StatePort, ComputePort
      Storage/
        LocalAdapter.py
      Messaging/
        InMemoryAdapter.py
        LitestarEventsAdapter.py
      Identity/
        JWTAdapter.py                   # обертка над существующим Ship/Auth/JWT
      State/
        PostgresAdapter.py              # обертка над существующим Infrastructure/Database
        SQLiteAdapter.py
      Compute/
        SubprocessAdapter.py

    Cell/                               # [НОВОЕ] Cell Engine (L2)
      __init__.py
      CellSpec.py                       # Спецификация Cell
      Supervisor.py                     # Lifecycle management
      Capabilities.py                   # Capability tokens
      Budget.py                         # Resource budgets
      Registry.py                       # Registry Protocol

    Providers/
      AdapterProvider.py                # [НОВОЕ] DI для адаптеров по окружению

  Containers/
    CoreSection/                        # [НОВОЕ] Ядро репликатора
      SpecModule/                       # Intent -> MissionSpec -> Formula
      CellRegistryModule/               # Реестр спецификаций
      TemplateModule/                   # Генерация Porto-скелетов
      EvolutionModule/                  # Мутация, fitness, promotion

    AgentSection/                       # [НОВОЕ] Интеллект
      CompassModule/                    # Meta-Thinker + Context Manager
      MakerModule/                      # MAD + K-Voting + Red-Flagging
      OrchestratorModule/               # Координация агентов

    ToolSection/                        # [НОВОЕ] Инструменты
      MCPClientModule/                  # MCP tool integration
      GitModule/                        # Git operations
      NixModule/                        # Nix build, flake generation
      CICDModule/                       # Pipeline generation

    KnowledgeSection/                   # [НОВОЕ] Знания
      MemoryModule/                     # Agent memory
      KnowledgeGraphModule/             # Temporal KG
      SpecLibraryModule/                # Библиотека Formula/шаблонов

docs/                                   # [НОВОЕ] Документация
  architecture/                         # Архитектурные решения
  patterns/                             # Паттерны
  reference/                            # Справочники
specs/                                  # [НОВОЕ] Спецификации
  beads/                                # Декомпозиция на beads
```

---

## Правила навигации

- Ищешь **как что-то устроено** -> `docs/architecture/`
- Ищешь **какой паттерн использовать** -> `docs/patterns/`
- Ищешь **что означает термин** -> `docs/reference/glossary.md`
- Ищешь **какую библиотеку использовать** -> `docs/reference/tech-stack.md`
- Ищешь **где лежит файл** -> `docs/reference/file-map.md` (этот файл)
- Ищешь **что делать** -> `specs/` (спецификации)
- Ищешь **базовый класс** -> `src/Ship/Parents/`
- Ищешь **примеры** -> `src/Containers/AppSection/UserModule/` (showcase)
