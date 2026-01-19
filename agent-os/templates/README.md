# 📦 Agent OS Templates

> Готовые шаблоны кода для быстрого создания компонентов Hyper-Porto.

---

## 🎯 Как использовать

1. Скопировать нужный шаблон
2. Заменить переменные (см. таблицу ниже)
3. Удалить комментарии с примерами (опционально)

---

## 📋 Переменные шаблонов

| Переменная | Описание | Пример |
|------------|----------|--------|
| `${Section}` | Название секции | `AppSection` |
| `${Module}` | Название модуля | `UserModule` |
| `${module_lower}` | Модуль в snake_case | `user_module` |
| `${Entity}` | Название сущности (PascalCase) | `User`, `Order` |
| `${entity_lower}` | Сущность в snake_case | `user`, `order` |
| `${Entities}` | Множественное число (PascalCase) | `Users`, `Orders` |
| `${entities_lower}` | Множественное в snake_case | `users`, `orders` |
| `${ActionName}` | Название Action | `CreateUser`, `UpdateOrder` |
| `${action_verb}` | Глагол действия | `create`, `update`, `delete` |
| `${TaskName}` | Название Task | `HashPassword`, `SendEmail` |
| `${QueryName}` | Название Query | `GetUser`, `ListOrders` |
| `${MODULE_UPPER}` | Модуль в UPPER_CASE | `USER`, `ORDER` |
| `${ENTITY_UPPER}` | Сущность в UPPER_CASE | `USER`, `ORDER` |
| `${description}` | Описание компонента | `creating new users` |
| `${InputType}` | Тип входных данных | `str`, `CreateUserRequest` |
| `${OutputType}` | Тип выходных данных | `str`, `User` |

---

## 📁 Доступные шаблоны

### Core (основные)

| Шаблон | Описание |
|--------|----------|
| `action.py.template` | Action (Use Case) с Result |
| `task.py.template` | Task (Async/Sync атомарная операция) |
| `query.py.template` | Query (CQRS Read) |
| `controller.py.template` | REST Controller с CRUD |
| `repository.py.template` | Repository с hooks |
| `unit-of-work.py.template` | UnitOfWork с events |
| `error.py.template` | Errors (Pydantic frozen) |
| `event.py.template` | Events + Listeners |
| `schemas.py.template` | Request/Response DTOs |
| `providers.py.template` | Dishka DI Providers |
| `model.py.template` | Piccolo ORM Model |

### Extended (дополнительные)

| Шаблон | Описание |
|--------|----------|
| `graphql-resolver.py.template` | Strawberry GraphQL Resolvers |
| `websocket-handler.py.template` | Litestar Channels WebSocket |
| `cli-command.py.template` | Click CLI Commands |
| `background-task.py.template` | TaskIQ Background Tasks |

---

## 🚀 Пример: Создание UserModule

### 1. Заменить переменные:

```
${Section}       → AppSection
${Module}        → UserModule
${module_lower}  → user
${Entity}        → User
${entity_lower}  → user
${Entities}      → Users
${entities_lower}→ users
${MODULE_UPPER}  → USER
${ENTITY_UPPER}  → USER
```

### 2. Создать структуру:

```
Containers/AppSection/UserModule/
├── __init__.py
├── Actions/
│   ├── __init__.py
│   └── CreateUserAction.py      ← action.py.template
├── Tasks/
│   ├── __init__.py
│   └── HashPasswordTask.py      ← task.py.template
├── Queries/
│   ├── __init__.py
│   └── GetUserQuery.py          ← query.py.template
├── Data/
│   ├── Repositories/
│   │   └── UserRepository.py    ← repository.py.template
│   ├── Schemas/
│   │   ├── Requests.py          ← schemas.py.template
│   │   └── Responses.py         ← schemas.py.template
│   └── UnitOfWork.py            ← unit-of-work.py.template
├── Models/
│   ├── PiccoloApp.py
│   ├── User.py                  ← model.py.template
│   └── migrations/
├── UI/
│   └── API/
│       └── Controllers/
│           └── UserController.py ← controller.py.template
├── Events.py                     ← event.py.template
├── Listeners.py                  ← event.py.template
├── Errors.py                     ← error.py.template
└── Providers.py                  ← providers.py.template
```

---

## 🔗 Связанные документы

- **Workflows:** `../workflows/` — пошаговые инструкции
- **Checklists:** `../checklists/` — чеклисты создания
- **Standards:** `../standards/` — правила написания кода

