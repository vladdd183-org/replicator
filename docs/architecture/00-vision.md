# Видение Replicator

> **Replicator** -- самоэволюционирующая модульная система, способная улучшать собственный код, генерировать новые репозитории и работать с существующими legacy-кодовыми базами.

---

## Суть

Replicator -- это не фреймворк и не библиотека. Это **живой организм кода**, построенный на принципах:

1. **Фрактальной модульности** -- каждый модуль имеет одинаковый интерфейс на любом масштабе
2. **Адаптерной нейтральности** -- бизнес-логика не знает, работает она через HTTP или libp2p
3. **Самореференции** -- система может применять свои инструменты к себе самой
4. **Прогрессивной децентрализации** -- работает на Web2 сегодня, архитектурно готова к Web3

---

## Три режима работы

### Режим 1: Самоэволюция

Система модифицирует собственный код через тот же pipeline, которым она обрабатывает любую задачу.

```
Intent: "Добавить поддержку нового транспорта gRPC"
    -> SpecModule компилирует в MissionSpec
    -> CompassModule формирует стратегию
    -> MakerModule декомпозирует на Beads
    -> OrchestratorModule исполняет через MCP + Git
    -> EvolutionModule верифицирует и промоутит
    -> Replicator теперь поддерживает gRPC
```

### Режим 2: Генерация новых репозиториев

Создание нового проекта с Porto-скелетом, Nix-сборкой, CI/CD и выбранным набором модулей.

```
Intent: "Создать микросервис обработки платежей"
    -> SpecModule формирует спецификацию проекта
    -> TemplateModule генерирует Porto-скелет
    -> NixModule создает flake.nix + OCI pipeline
    -> CICDModule формирует GitHub Actions workflow
    -> GitModule инициализирует и пушит репозиторий
```

### Режим 3: Работа с Legacy

Подключение к существующей кодовой базе и работа в привычном для неё стиле.

```
Intent: "Исправить баг #347 в legacy-сервисе авторизации"
    -> GitModule клонирует репозиторий
    -> KnowledgeGraphModule анализирует структуру и паттерны
    -> CompassModule формирует стратегию с учетом legacy-ограничений
    -> MakerModule декомпозирует, агенты исполняют
    -> EvolutionModule верифицирует в контексте legacy CI
```

---

## Слоистая архитектура

```
L0  ТРАНСПОРТНАЯ ТКАНЬ     Адаптеры: Web2 (HTTP/NATS/Redis) | Web3 (libp2p/IPFS/Ceramic)
L1  ИНФРАСТРУКТУРА (Ship)  Nix build, OCI, DI, телеметрия, аутентификация, конфигурация, CLI
L2  РАНТАЙМ (Cell Engine)  CellSpec, spawn, изоляция, capabilities, состояние
L3  СТРУКТУРА КОДА (Porto) Containers, Actions, Tasks, Queries, Events, Result Railway
L4  ИНТЕЛЛЕКТ (Агенты)     COMPASS стратегия, MAKER надежность, DSPy оптимизация
L5  РЕПЛИКАЦИЯ (Мета-слой) Самомодификация, генерация репозиториев, шаблоны, эволюция
```

Каждый слой зависит только от нижележащих. Каждый слой можно заменить, не трогая верхние.

---

## Фундаментальное уравнение

Из теории Фрактального Атома:

> **System = Sum Cell(Spec, Capabilities, State) composed via Aspects | over (Storage + State + Messaging) / Transport | adapted by (Local + Hybrid + P2P)**

В терминах Replicator:

> **Replicator = Sum Container(Actions, Tasks, Events) composed via Sections | over (StoragePort + StatePort + MessagingPort) / DI | adapted by (Web2Adapters + Web3Adapters)**

Маппинг:

| Фрактальный Атом | Porto / Replicator | Пояснение |
|---|---|---|
| Cell | Container | Самодостаточный модуль с четким интерфейсом |
| Spec_CID | Actions + Tasks + Models | Полная спецификация поведения модуля |
| Capabilities | Providers + DI | Что модулю разрешено использовать |
| State | UnitOfWork + Repository | Мутабельное состояние с транзакциями |
| Aspect | Section + composition в App.py | Как модули компонуются вместе |
| Layer | Ship/Adapters Protocols | Каналы коммуникации (Storage, Messaging, State) |
| Adapter | Конкретные реализации Protocols | Web2 или Web3 имплементации |

---

## Принципы проектирования

### 1. Container = Cell = Граница микросервиса

Каждый Container в Porto -- это будущий отдельный микросервис. В терминах Cell -- это единица вычислений с четким интерфейсом. Вынос Container в отдельный процесс -- механическая операция.

### 2. Ship = Общий рантайм

Ship содержит общую инфраструктуру: базовые классы (Action, Task, Query, Repository), адаптеры (StoragePort, MessagingPort), Cell engine (CellSpec, Supervisor), DI провайдеры.

### 3. Адаптеры, а не переписывание

Переход Web2 -> Web3 -- это замена адаптеров через DI, а не переписывание бизнес-логики. PostgreSQL -> Ceramic, NATS -> libp2p, JWT -> UCAN -- всё через один Protocol.

### 4. Result Railway -- явные ошибки

Каждый Action возвращает `Result[T, E]`. Нет скрытых исключений. Pattern matching в контроллерах. Детерминированное исполнение -- основа для будущей WASM-совместимости.

### 5. Domain Events -- event sourcing ready

Все мутации порождают события. События -- append-only лог. Это фундамент для Ceramic streams, audit trail и distributed саг.

### 6. Spec-first разработка

Любое изменение начинается со спецификации. Спецификация -- источник истины. Код -- производная спецификации. Это основа для автономной разработки через агентов.
