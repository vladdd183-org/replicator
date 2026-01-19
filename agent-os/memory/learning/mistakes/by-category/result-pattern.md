# 🚂 Result Pattern Mistakes

> Ошибки при использовании Result[T, E] и Railway-Oriented Programming

---

## 📊 Статистика

- **Всего ошибок:** 0
- **Critical:** 0 | **Major:** 0 | **Minor:** 0

---

## 🚨 Типичные проблемы

### 1. Raise вместо Failure

```python
# ❌ ЗАПРЕЩЕНО в бизнес-логике
async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
    if not data.email:
        raise ValueError("Email required")  # НЕТ!
    
# ✅ ПРАВИЛЬНО
async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
    if not data.email:
        return Failure(ValidationError(field="email", message="required"))
```

**Почему:** Exceptions ломают Railway, делают flow непредсказуемым.

### 2. Неправильный pattern matching

```python
# ❌ Забыли case для всех Failure
match result:
    case Success(user):
        return user
    # Failure не обработан — упадёт!

# ✅ ПРАВИЛЬНО
match result:
    case Success(user):
        return UserResponse.from_entity(user)
    case Failure(UserNotFoundError(user_id=uid)):
        raise DomainException(UserNotFoundError(user_id=uid))
    case Failure(error):
        raise DomainException(error)
```

### 3. Игнорирование Result

```python
# ❌ Результат не проверяется
await action.run(data)  # Result выброшен!
do_something_else()

# ✅ ПРАВИЛЬНО
result = await action.run(data)
match result:
    case Success(value):
        do_something_else()
    case Failure(error):
        handle_error(error)
```

### 4. Неправильный тип возврата

```python
# ❌ Action возвращает сырое значение
async def run(self, data) -> User:  # Должен быть Result!
    return user

# ✅ ПРАВИЛЬНО
async def run(self, data) -> Result[User, UserError]:
    return Success(user)
```

### 5. Смешивание Success/Failure с разными типами

```python
# ❌ Разные типы ошибок
async def run(self) -> Result[User, UserError]:
    if error1:
        return Failure(UserError(...))
    if error2:
        return Failure(str)  # Строка вместо Error!

# ✅ ПРАВИЛЬНО — единый тип ошибки
async def run(self) -> Result[User, UserError]:
    if error1:
        return Failure(UserNotFoundError(...))
    if error2:
        return Failure(UserValidationError(...))  # Наследует UserError
```

---

## 📝 Записанные ошибки

<!-- AUTO-GENERATED -->

| ID | Название | Серьёзность | Дата | Модуль |
|----|----------|-------------|------|--------|
| — | Нет записей | — | — | — |

---

## 🛡️ Чеклист предотвращения

- [ ] Action возвращает `Result[T, E]`, не сырое значение
- [ ] Бизнес-ошибки через `Failure()`, не `raise`
- [ ] Pattern matching покрывает все варианты Failure
- [ ] Result не игнорируется, всегда обрабатывается
- [ ] Единый базовый тип ошибки для модуля

---

## 🔗 Связи

- [Result Errors Troubleshooting](../../../../troubleshooting/result-errors.md)
- [Result Patterns Snippets](../../../../snippets/result-patterns.md)
- [Railway-Oriented Programming](../../../../../docs/04-result-railway.md)
