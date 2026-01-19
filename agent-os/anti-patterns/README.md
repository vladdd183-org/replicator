# 🚫 Agent OS Anti-patterns

> Чего НЕ делать в Hyper-Porto проекте.

---

## 📋 Доступные гайды

| Файл | Содержимое |
|------|------------|
| [common-mistakes.md](common-mistakes.md) | Топ-10 ошибок новичков |
| [bad-async.md](bad-async.md) | Ошибки асинхронного кода |

---

## 🔴 Critical — Никогда не делай

```python
# 1. Exceptions в бизнес-логике
raise UserNotFoundException()  # → return Failure(...)

# 2. Относительные импорты
from ....Actions import X  # → from src.Containers...

# 3. Импорт между Containers
from src.Containers.OrderModule import X  # → Events

# 4. dataclass для DTO
@dataclass  # → pydantic.BaseModel

# 5. Fire-and-forget
asyncio.create_task(x)  # → anyio.create_task_group()
```

---

## 🔗 Связанные

- **Standards:** `../standards/`
- **Troubleshooting:** `../troubleshooting/`
- **Checklists:** `../checklists/code-review.md`



