# 🔧 Agent OS Troubleshooting

> Решения частых проблем в Hyper-Porto проекте.

---

## 📋 Доступные гайды

| Гайд | Описание | Частота |
|------|----------|---------|
| [di-errors.md](di-errors.md) | Ошибки Dishka DI | 🔴 Высокая |
| [result-errors.md](result-errors.md) | Ошибки Result pattern | 🔴 Высокая |
| [import-errors.md](import-errors.md) | Ошибки импортов | 🟡 Средняя |

---

## 🚨 Quick Fixes

### DI не находит зависимость
```python
# Добавить в Providers.py:
action_name = provide(ActionName)
```

### Result не конвертируется в Response
```python
# Добавить декоратор:
@result_handler(ResponseDTO, success_status=HTTP_201_CREATED)
```

### Circular import
```python
# Использовать TYPE_CHECKING:
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.Module.Class import Class
```

### Import error
```python
# Заменить относительные на абсолютные:
from src.Containers.Section.Module.Component import Component
```

---

## 🔗 Связанные

- **Standards:** `../standards/`
- **Workflows:** `../workflows/`
- **Checklists:** `../checklists/`



