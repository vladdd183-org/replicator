# 📚 Glossary — Словарь терминов Hyper-Porto

> Краткий справочник терминов. **Полные определения:** [`docs/00-philosophy.md`](../docs/00-philosophy.md), [`docs/01-architecture.md`](../docs/01-architecture.md)

---

## 🏗️ Архитектура Porto

| Термин | Определение | Подробнее |
|--------|-------------|-----------|
| **Container** | Изолированный бизнес-модуль (Users, Orders) | [docs/01-architecture.md](../docs/01-architecture.md) |
| **Ship** | Общая инфраструктура (Parents, Configs, Decorators) | [docs/02-project-structure.md](../docs/02-project-structure.md) |
| **Section** | Группа Containers (AppSection, VendorSection) | [docs/02-project-structure.md](../docs/02-project-structure.md) |

---

## 🎯 Компоненты

| Термин | Назначение | Return | Подробнее |
|--------|------------|--------|-----------|
| **Action** | Use Case, оркестрация | `Result[T, E]` | [docs/03-components.md](../docs/03-components.md#action-use-case) |
| **Task** | Атомарная операция | `T` (plain value) | [docs/03-components.md](../docs/03-components.md#task-atomic-operation) |
| **Query** | CQRS Read (прямой ORM) | `T \| None` | [docs/03-components.md](../docs/03-components.md#query-cqrs-read) |
| **Repository** | CRUD + domain queries | `ModelT` | [docs/03-components.md](../docs/03-components.md#repository) |
| **UnitOfWork** | Транзакции + Events | Context manager | [docs/03-components.md](../docs/03-components.md#unitofwork) |
| **Controller** | HTTP endpoint | Response | [docs/03-components.md](../docs/03-components.md#controller) |
| **Event** | Domain Event | Published via emit() | [docs/03-components.md](../docs/03-components.md#event-domain-event) |
| **Listener** | Обработчик событий | Side effects | [docs/03-components.md](../docs/03-components.md#listener-event-handler) |
| **Provider** | DI регистрация | Dependencies | [docs/03-components.md](../docs/03-components.md#provider-dependency-injection) |

---

## 🔄 Паттерны

| Паттерн | Описание | Подробнее |
|---------|----------|-----------|
| **Result Pattern** | `Success(value)` / `Failure(error)` | [docs/04-result-railway.md](../docs/04-result-railway.md) |
| **CQRS** | Actions (write) / Queries (read) | [docs/03-components.md](../docs/03-components.md) |
| **Structured Concurrency** | anyio TaskGroups | [docs/05-concurrency.md](../docs/05-concurrency.md) |
| **Gateway** | Protocol + Adapter для межмодульной связи | [docs/14-module-gateway-pattern.md](../docs/14-module-gateway-pattern.md) |
| **Saga** | Распределённые транзакции (Temporal) | [docs/15-saga-patterns.md](../docs/15-saga-patterns.md) |
| **Outbox** | Гарантированная доставка событий | [docs/18-unified-event-bus.md](../docs/18-unified-event-bus.md) |

---

## 📦 DTOs и данные

| Термин | Тип | Особенности |
|--------|-----|-------------|
| **Request DTO** | `BaseModel` + `frozen=True` | Валидация входных данных |
| **Response DTO** | `EntitySchema` | `from_entity()` для конвертации |
| **Error** | `BaseError` (frozen) | `http_status`, `code`, `message` |
| **Model** | Piccolo `Table` | ORM сущность |

---

## 📐 Naming Conventions

| Компонент | Паттерн | Пример |
|-----------|---------|--------|
| Action | `{Verb}{Noun}Action` | `CreateUserAction` |
| Task | `{Verb}{Noun}Task` | `HashPasswordTask` |
| Query | `{Verb}{Noun}Query` | `GetUserQuery` |
| Repository | `{Noun}Repository` | `UserRepository` |
| Controller | `{Noun}Controller` | `UserController` |
| Error | `{Noun}Error` | `UserNotFoundError` |
| Event | `{Noun}{PastVerb}` | `UserCreated` |

---

## 🔗 Полная документация

- [docs/00-philosophy.md](../docs/00-philosophy.md) — Философия и принципы
- [docs/01-architecture.md](../docs/01-architecture.md) — Архитектура слоёв
- [docs/03-components.md](../docs/03-components.md) — **Детальное описание всех компонентов**
- [docs/08-libraries.md](../docs/08-libraries.md) — Tech Stack



