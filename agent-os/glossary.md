# 📚 Glossary — Словарь терминов Hyper-Porto

> Определения ключевых терминов архитектуры.

---

## 🏗️ Архитектурные термины

### Container
**Изолированный бизнес-модуль.** Содержит всю логику одной функциональной области (Users, Orders, Payments). Containers не могут импортировать друг друга.

### Ship
**Общая инфраструктура.** Содержит базовые классы (Parents), конфигурации, декораторы, общие сервисы. Все Containers могут импортировать из Ship.

### Section
**Группа Containers.** Логическая организация модулей (AppSection — основные, VendorSection — внешние интеграции).

---

## 🎯 Компоненты

### Action
**Use Case / Command.** Выполняет одну бизнес-операцию. Всегда возвращает `Result[T, E]`. Оркестрирует Tasks и работает с UoW.

```python
class CreateUserAction(Action[CreateUserRequest, User, UserError]):
    async def run(self, data) -> Result[User, UserError]: ...
```

### Task
**Атомарная операция.** Выполняет одно техническое действие (хеширование, отправка email). Возвращает plain value, не Result. Переиспользуется между Actions.

```python
class HashPasswordTask(SyncTask[str, str]):
    def run(self, password: str) -> str: ...
```

### Query
**CQRS Read операция.** Только чтение данных, без модификации. Не использует UoW, не публикует события. Прямой доступ к ORM.

```python
class GetUserQuery(Query[GetUserQueryInput, User | None]):
    async def execute(self, input) -> User | None: ...
```

### Repository
**Абстракция над ORM.** Предоставляет CRUD + доменные запросы. Управляется через UoW.

### UnitOfWork (UoW)
**Паттерн транзакций.** Управляет транзакциями БД и публикацией событий. События публикуются только после успешного commit.

### Controller
**HTTP endpoint.** Принимает запросы, вызывает Actions/Queries, возвращает Responses.

### Event
**Доменное событие.** Факт произошедшего в системе (UserCreated, OrderPaid). Публикуется через UoW, обрабатывается Listeners.

### Listener
**Обработчик событий.** Реагирует на Domain Events. Регистрируется в App.py.

### Provider
**DI регистрация.** Определяет как создавать зависимости. APP scope для stateless, REQUEST scope для per-request.

---

## 🔄 Паттерны

### Result Pattern
**Явная обработка ошибок.** Вместо exceptions используется `Result[T, E]` — `Success(value)` или `Failure(error)`.

### Railway-Oriented Programming
**Парадигма Result.** Код разделён на Success track и Failure track. Переключение между ними — явное.

### CQRS
**Command Query Responsibility Segregation.** Разделение операций записи (Actions) и чтения (Queries).

### Domain Events
**События предметной области.** Уведомления о произошедших фактах. Обеспечивают слабую связанность модулей.

### Structured Concurrency
**Паттерн anyio.** Все параллельные задачи управляются через TaskGroup. Нет "забытых" задач.

---

## 📦 Типы данных

### Request DTO
**Входящие данные.** Pydantic BaseModel с валидацией. Используется в Controllers.

### Response DTO  
**Исходящие данные.** EntitySchema с `from_entity()`. Сериализация для API.

### Error
**Ошибка бизнес-логики.** Pydantic frozen модель с `http_status` и `code`.

### Model
**ORM сущность.** Piccolo Table, представляет данные в БД.

---

## 🔧 Инфраструктура

### Dishka
**DI фреймворк.** Dependency Injection с поддержкой scopes.

### Litestar
**Web фреймворк.** HTTP, WebSocket, CLI, Events.

### Piccolo
**Async ORM.** База данных + миграции.

### returns
**Функциональная библиотека.** Result, Maybe, flow, bind.

### anyio
**Async runtime.** Structured Concurrency, TaskGroups.

---

## 📐 Naming Conventions

| Термин | Паттерн | Пример |
|--------|---------|--------|
| Action | `{Verb}{Noun}Action` | `CreateUserAction` |
| Task | `{Verb}{Noun}Task` | `HashPasswordTask` |
| Query | `{Verb}{Noun}Query` | `GetUserQuery` |
| Repository | `{Noun}Repository` | `UserRepository` |
| Controller | `{Noun}Controller` | `UserController` |
| Error | `{Noun}Error` | `UserNotFoundError` |
| Event | `{Noun}{PastVerb}` | `UserCreated` |
| Request | `{Action}Request` | `CreateUserRequest` |
| Response | `{Noun}Response` | `UserResponse` |

---

## 🔗 Связанные

- **Philosophy:** `docs/00-philosophy.md`
- **Architecture:** `docs/01-architecture.md`
- **Components:** `docs/03-components.md`



