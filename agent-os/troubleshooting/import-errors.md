# 🔧 Troubleshooting: Import Errors

> Частые ошибки импортов и их решения.

---

## ❌ Error: `ModuleNotFoundError`

### Симптом
```
ModuleNotFoundError: No module named 'src'
```

### Причина
Python не видит `src` как пакет.

### Решение
1. Убедиться что есть `src/__init__.py`
2. Запускать из корня проекта
3. Или добавить в PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## ❌ Error: Relative Import Error

### Симптом
```
ImportError: attempted relative import with no known parent package
```

### Причина
Используются относительные импорты (ЗАПРЕЩЕНО в Hyper-Porto!).

### Решение
Заменить на абсолютные:

```python
# ❌ ЗАПРЕЩЕНО
from ....Actions.CreateUserAction import CreateUserAction
from ...Errors import UserNotFoundError

# ✅ ПРАВИЛЬНО
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Errors import UserNotFoundError
```

---

## ❌ Error: Circular Import

### Симптом
```
ImportError: cannot import name 'X' from partially initialized module
```

### Причина
Модуль A импортирует B, B импортирует A.

### Решение

**Вариант 1: TYPE_CHECKING**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.Containers.Module.SomeClass import SomeClass

class MyClass:
    def method(self, obj: "SomeClass") -> None:  # Строковая аннотация
        ...
```

**Вариант 2: Импорт внутри функции**
```python
def some_function():
    from src.Containers.Module.SomeClass import SomeClass
    return SomeClass()
```

**Вариант 3: Реструктуризация**
Вынести общие типы в отдельный модуль.

---

## ❌ Error: Import между Containers

### Симптом
```python
# В UserModule:
from src.Containers.AppSection.OrderModule.Actions import CreateOrderAction
```

### Причина
Это ЗАПРЕЩЕНО архитектурой!

### Решение
Использовать Events для межмодульного общения:

```python
# UserModule публикует событие
self.uow.add_event(UserCreated(user_id=user.id))

# OrderModule слушает
@listener("UserCreated")
async def create_initial_order(user_id: str, **kwargs):
    # Создать заказ для нового пользователя
```

---

## ❌ Error: `AttributeError` при импорте

### Симптом
```
AttributeError: module 'src.Containers.Module' has no attribute 'router'
```

### Причина
Не экспортировано в `__init__.py`.

### Решение
```python
# src/Containers/AppSection/UserModule/__init__.py
"""UserModule - User management module."""

from src.Containers.AppSection.UserModule.UI.API.Routes import user_router

__all__ = ["user_router"]  # Явный экспорт
```

---

## ❌ Error: Порядок импортов

### Симптом
Ruff/isort ругаются на порядок.

### Решение
Правильный порядок:

```python
# 1. Стандартная библиотека
from datetime import datetime
from uuid import UUID

# 2. Внешние библиотеки
from pydantic import BaseModel
from returns.result import Result, Success, Failure

# 3. Ship (общий код)
from src.Ship.Parents.Action import Action
from src.Ship.Core.Errors import BaseError

# 4. Текущий Container
from src.Containers.AppSection.UserModule.Errors import UserError
from src.Containers.AppSection.UserModule.Models.User import AppUser
```

---

## 📐 IDE Configuration

### VSCode settings.json
```json
{
    "python.analysis.extraPaths": ["${workspaceFolder}"],
    "python.autoComplete.extraPaths": ["${workspaceFolder}"]
}
```

### PyCharm
1. Right-click on `src` folder
2. Mark Directory as → Sources Root

---

## 🔍 Диагностика

### Проверить что видит Python
```python
import sys
print(sys.path)
```

### Проверить структуру пакета
```bash
find src -name "__init__.py" | head -20
```

### Проверить импорт вручную
```python
python -c "from src.Containers.AppSection.UserModule import user_router; print(user_router)"
```

---

## 🔗 Связанные

- **Constitution:** `../standards/architecture/constitution.md` (правило импортов)
- **Standards:** `../standards/global/coding-style.md`



