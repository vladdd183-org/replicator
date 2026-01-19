# 📦 Import Mistakes

> Ошибки, связанные с импортами Python

---

## 📊 Статистика

- **Всего ошибок:** 0
- **Critical:** 0 | **Major:** 0 | **Minor:** 0

---

## 🚨 Типичные проблемы

### 1. Относительные импорты

```python
# ❌ ЗАПРЕЩЕНО
from ....Actions.CreateUserAction import CreateUserAction
from ..Errors import UserNotFoundError

# ✅ ПРАВИЛЬНО
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Errors import UserNotFoundError
```

**Почему:** Относительные импорты ломаются при рефакторинге и затрудняют понимание зависимостей.

### 2. Циклические импорты

```python
# ❌ Модуль A импортирует B, B импортирует A
# a.py
from src.Containers.ModuleB.Actions import SomeAction

# b.py
from src.Containers.ModuleA.Actions import OtherAction  # Цикл!

# ✅ Решение: использовать Events или TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.Containers.ModuleA.Actions import OtherAction
```

### 3. Import в неправильном месте

```python
# ❌ Import внутри функции без причины
async def run(self):
    from src.Ship.Core.Errors import BaseError  # Медленно!
    
# ✅ Import на уровне модуля
from src.Ship.Core.Errors import BaseError

async def run(self):
    ...
```

---

## 📝 Записанные ошибки

<!-- AUTO-GENERATED: Список ошибок категории imports -->

| ID | Название | Серьёзность | Дата | Модуль |
|----|----------|-------------|------|--------|
| — | Нет записей | — | — | — |

---

## 🛡️ Чеклист предотвращения

- [ ] Все импорты абсолютные от `src.`
- [ ] Нет циклических зависимостей между модулями
- [ ] Импорты на уровне модуля (не внутри функций)
- [ ] Используется `TYPE_CHECKING` для type hints при циклах

---

## 🔗 Связи

- [Import Errors Troubleshooting](../../../../troubleshooting/import-errors.md)
- [Coding Style Standards](../../../../standards/global/coding-style.md)
