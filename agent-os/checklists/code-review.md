# ✅ Checklist: Code Review

> Чеклист для code review в Hyper-Porto проекте.

---

## 📜 Архитектура

- [ ] **Импорты абсолютные** от `src.`
- [ ] **Нет импортов между Containers** (только через Events)
- [ ] **Компонент в правильной папке** (Action в Actions/, Query в Queries/)
- [ ] **Именование по конвенции** (`{Verb}{Noun}Action`, `{Noun}Repository`)

## 🎯 Actions

- [ ] **Возвращает `Result[T, E]`** — не исключения
- [ ] **Использует UoW** для транзакций
- [ ] **События через `uow.add_event()`** — не напрямую
- [ ] **Декоратор `@audited`** для логирования
- [ ] **Один Use Case** — Single Responsibility

## 📖 Queries

- [ ] **НЕ возвращает Result** — возвращает `T | None`
- [ ] **НЕ использует UoW** — прямой ORM доступ
- [ ] **НЕ модифицирует данные** — только чтение
- [ ] **Input — Pydantic с `frozen=True`**
- [ ] **Output — `@dataclass(frozen=True)`** для ORM

## 🔧 Tasks

- [ ] **Атомарная операция** — одно действие
- [ ] **Возвращает plain value** — не Result
- [ ] **SyncTask для CPU-bound** — вызывается через `anyio.to_thread.run_sync()`
- [ ] **Без бизнес-логики** — только техническая операция

## 📦 DTOs

- [ ] **Request — Pydantic BaseModel** с валидацией
- [ ] **Response — EntitySchema** с `from_entity()`
- [ ] **Errors — Pydantic frozen** с `http_status`
- [ ] **НЕ dataclass** для DTOs

## 🔄 Error Handling

- [ ] **Используется `Failure(Error)`** — не `raise`
- [ ] **Pattern matching** для Result
- [ ] **Error с `http_status`** для HTTP маппинга
- [ ] **ErrorWithTemplate** для динамических сообщений

## 💉 DI

- [ ] **`FromDishka[T]`** в Controller
- [ ] **Зарегистрирован в Providers**
- [ ] **Правильный scope** (APP для stateless, REQUEST для stateful)

## ⚡ Async

- [ ] **`anyio`** для concurrency (не asyncio)
- [ ] **`anyio.to_thread.run_sync()`** для CPU-bound
- [ ] **`async with anyio.create_task_group()`** для параллельных задач
- [ ] **Нет fire-and-forget** задач

## 📝 Типизация

- [ ] **Все функции типизированы**
- [ ] **Generic типы** для базовых классов
- [ ] **Нет `Any`** без причины

## 🧪 Тесты

- [ ] **Unit тест** для нового Action
- [ ] **Integration тест** для нового endpoint
- [ ] **Тест на ошибки** (Failure cases)

---

## 🚫 Red Flags (немедленно исправить)

```python
# ❌ Относительные импорты
from ....Actions import SomeAction

# ❌ Исключения в бизнес-логике
raise UserNotFoundError()

# ❌ dataclass для DTO
@dataclass
class CreateUserRequest:

# ❌ Action без Result
async def run(self) -> User:

# ❌ Импорт между Containers
from src.Containers.OrderModule import CreateOrderAction

# ❌ asyncio.create_task()
asyncio.create_task(do_something())

# ❌ Service Locator
container.resolve(SomeService)
```

---

## 🔗 Связанные

- **Standards:** `../standards/`
- **Constitution:** `../standards/architecture/constitution.md`



