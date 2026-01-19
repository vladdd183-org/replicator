# Actions & Tasks — Quick Reference

> Краткий справочник для AI-агентов. **Полная документация:** [`docs/03-components.md`](../../../docs/03-components.md)

---

## 📖 Основной источник

Этот файл — **компактный чеклист**. Детальные примеры, базовые классы и реальный код смотри в:

- **[docs/03-components.md](../../../docs/03-components.md)** — полное описание Action, Task, Query, Repository, UoW
- **[docs/04-result-railway.md](../../../docs/04-result-railway.md)** — Result pattern и Railway-oriented programming
- **[docs/12-reducing-boilerplate.md](../../../docs/12-reducing-boilerplate.md)** — EntitySchema, @result_handler, @audited

---

## ✅ Action Checklist

| Правило | Проверка |
|---------|----------|
| Возвращает `Result[T, E]` | `async def run(...) -> Result[Output, Error]` |
| Использует UoW для транзакций | `async with self.uow: ... await self.uow.commit()` |
| Публикует события через UoW | `self.uow.add_event(UserCreated(...))` |
| CPU-bound через anyio | `await anyio.to_thread.run_sync(task.run, data)` |
| DI через конструктор | `def __init__(self, task: Task, uow: UoW)` |
| Именование | `{Verb}{Noun}Action` → `CreateUserAction` |

---

## ✅ Task Checklist

| Правило | Проверка |
|---------|----------|
| Возвращает plain value | `def run(...) -> str` (не Result!) |
| Stateless и переиспользуемый | Без бизнес-логики |
| Async для I/O | `Task[Input, Output]` → `async def run()` |
| Sync для CPU | `SyncTask[Input, Output]` → `def run()` |
| Именование | `{Verb}{Noun}Task` → `HashPasswordTask` |

---

## ✅ Правила вызовов

```
Controller → Action, Query
Action → Task, Repository, UoW, SubAction
Task → (stateless, опционально Repository)
```

**❌ Запрещено:**
- Controller → Task напрямую
- Action из модуля A → Action из модуля B (используй Events!)

---

## 🎨 @audited декоратор

```python
from src.Ship.Decorators.audited import audited

@audited(action="create", entity_type="User")
class CreateUserAction(Action[...]):
    ...
```

→ Подробнее: [`docs/03-components.md`](../../../docs/03-components.md) (раздел @audited)

---

## 📁 Расположение

```
Containers/{Section}/{Module}/
├── Actions/          # Use Cases (CQRS Commands)
└── Tasks/            # Атомарные операции
```

---

## 🔗 Связанные документы

| Тема | Документ |
|------|----------|
| Полное описание компонентов | [`docs/03-components.md`](../../../docs/03-components.md) |
| Result и Railway | [`docs/04-result-railway.md`](../../../docs/04-result-railway.md) |
| Базовые классы | `src/Ship/Parents/Action.py`, `src/Ship/Parents/Task.py` |
| @audited декоратор | `src/Ship/Decorators/audited.py` |

