# Ошибки категории: Логические ошибки

## Описание

Здесь собраны типичные ошибки связанные с логикой программы: неправильные условия, граничные случаи, off-by-one, null checks.

## Частые ошибки

### 1. Отсутствие проверки на None/пустое значение

**Симптом:** AttributeError: 'NoneType' has no attribute 'X'.
**Причина:** Не проверяется результат операции, которая может вернуть None.
**Решение:** Всегда проверять возвращаемое значение.

```python
# ❌ Плохо
user = await repo.get(user_id)
return user.name  # Упадет если user is None

# ✅ Хорошо
user = await repo.get(user_id)
if user is None:
    return Failure(UserNotFoundError(user_id=user_id))
return Success(user.name)
```

### 2. Неправильный pattern matching для Result

**Симптом:** Failure не обрабатывается, программа падает.
**Причина:** Пропущена ветка case Failure(...).
**Решение:** Всегда обрабатывать оба случая.

```python
# ❌ Плохо — нет обработки Failure
match result:
    case Success(user):
        return user

# ✅ Хорошо — полная обработка
match result:
    case Success(user):
        return user
    case Failure(UserNotFoundError() as e):
        raise HTTPException(404, e.message)
    case Failure(error):
        raise HTTPException(400, str(error))
```

### 3. Off-by-one ошибки в пагинации

**Симптом:** Пропущены или дублируются элементы при пагинации.
**Причина:** Неправильный расчет offset/limit.
**Решение:** Тщательно проверять граничные случаи.

```python
# ❌ Плохо
offset = page * limit  # При page=1 пропускает первые элементы

# ✅ Хорошо
offset = (page - 1) * limit  # page начинается с 1
```

### 4. Мутация аргументов функции

**Симптом:** Неожиданное изменение данных в вызывающем коде.
**Причина:** Функция модифицирует переданный mutable объект.
**Решение:** Создавать копию или использовать immutable структуры.

```python
# ❌ Плохо — мутация входного списка
def process(items: list[Item]) -> list[Item]:
    items.append(new_item)  # Меняет оригинальный список!
    return items

# ✅ Хорошо — создаем новый список
def process(items: list[Item]) -> list[Item]:
    return [*items, new_item]
```

### 5. Неправильное сравнение float

**Симптом:** Сравнение float дает неожиданный результат.
**Причина:** Погрешность представления float в памяти.
**Решение:** Использовать Decimal для денег, или epsilon для сравнения.

```python
# ❌ Плохо
if total == 0.1 + 0.2:  # False! 0.1 + 0.2 != 0.3

# ✅ Хорошо — для денег
from decimal import Decimal
total = Decimal("0.1") + Decimal("0.2")

# ✅ Хорошо — для приблизительного сравнения
import math
if math.isclose(a, b, rel_tol=1e-9):
    ...
```

### 6. Игнорирование пустых коллекций

**Симптом:** Ошибка при обращении к элементам пустого списка.
**Причина:** Не проверяется, что коллекция не пуста.
**Решение:** Проверять перед доступом к элементам.

```python
# ❌ Плохо
first_item = items[0]  # IndexError если items пуст

# ✅ Хорошо
if items:
    first_item = items[0]
else:
    return Failure(EmptyListError())
```

---

*Файл будет дополняться по мере обнаружения новых паттернов ошибок.*
