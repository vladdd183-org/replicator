# 🔧 Troubleshooting: Result Errors

> Частые ошибки при работе с `Result[T, E]` и их решения.

---

## ❌ Error: `AttributeError: 'Failure' object has no attribute 'unwrap'`

### Симптом
```python
result = await action.run(data)
value = result.unwrap()  # AttributeError!
```

### Причина
`unwrap()` кидает исключение для Failure.

### Решение
Используй pattern matching или `value_or`:

```python
# ✅ Pattern matching
match result:
    case Success(value):
        return value
    case Failure(error):
        raise DomainException(error)

# ✅ Или value_or для дефолта
value = result.value_or(default_value)
```

---

## ❌ Error: Type mismatch в return

### Симптом
```
mypy: Incompatible return value type (got "User", expected "Result[User, UserError]")
```

### Причина
Забыл обернуть в `Success()`.

### Решение
```python
# ❌ Плохо
async def run(self, data) -> Result[User, UserError]:
    user = User(...)
    return user  # Type error!

# ✅ Хорошо
async def run(self, data) -> Result[User, UserError]:
    user = User(...)
    return Success(user)
```

---

## ❌ Error: Неправильный Error type

### Симптом
```
mypy: Argument 1 to "Failure" has incompatible type "str"; expected "UserError"
```

### Причина
Передаёшь строку вместо Error объекта.

### Решение
```python
# ❌ Плохо
return Failure("User not found")

# ✅ Хорошо
return Failure(UserNotFoundError(user_id=user_id))
```

---

## ❌ Error: Pattern matching не работает

### Симптом
```
match result:
    case Success(user):  # Не срабатывает
```

### Причина
Неправильный синтаксис или Python < 3.10.

### Решение
```python
# ✅ Правильный синтаксис (Python 3.10+)
match result:
    case Success(user):
        return UserResponse.from_entity(user)
    case Failure(UserNotFoundError(user_id=uid)):
        raise DomainException(UserNotFoundError(user_id=uid))
    case Failure(error):
        raise DomainException(error)
```

---

## ❌ Error: `@result_handler` не конвертирует

### Симптом
Controller возвращает Result объект напрямую в JSON.

### Причина
1. `@result_handler` не применён
2. Порядок декораторов неправильный

### Решение
```python
# ✅ Правильный порядок
@post("/")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)  # Первый!
async def create_user(...) -> Result[User, UserError]:
    return await action.run(data)
```

---

## ❌ Error: Failure не преобразуется в HTTP error

### Симптом
Failure возвращает 500 вместо ожидаемого статуса.

### Причина
Error не имеет `http_status` атрибута.

### Решение
```python
# ✅ Добавить http_status в Error
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "..."
    code: str = "USER_NOT_FOUND"
    http_status: int = 404  # Обязательно!
    user_id: UUID
```

---

## ❌ Error: Композиция Result

### Симптом
Нужно объединить несколько Result, но получается сложно.

### Решение
Используй `flow` и `bind`:

```python
from returns.pipeline import flow
from returns.pointfree import bind

# ✅ Композиция через flow
result = flow(
    validate_email(data.email),
    bind(lambda _: check_unique(data.email)),
    bind(lambda _: create_user(data)),
)

# Или последовательно с early return
async def run(self, data) -> Result[User, Error]:
    # Каждый шаг может вернуть Failure
    email_result = validate_email(data.email)
    if isinstance(email_result, Failure):
        return email_result
    
    unique_result = await check_unique(data.email)
    if isinstance(unique_result, Failure):
        return unique_result
    
    return Success(User(...))
```

---

## ❌ Error: Result в async context

### Симптом
```
TypeError: object Result can't be used in 'await' expression
```

### Причина
Result — не awaitable.

### Решение
```python
# ❌ Плохо
user = await Success(User(...))

# ✅ Хорошо
result = Success(User(...))  # Без await

# Если нужен async в композиции:
from returns.future import FutureResult
```

---

## 📐 Best Practices

### 1. Всегда типизируй Result

```python
async def run(self, data: Input) -> Result[Output, Error]:  # Явные типы!
```

### 2. Используй ErrorWithTemplate

```python
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User {user_id} not found"
    # message генерируется автоматически!
```

### 3. Pattern match все случаи

```python
match result:
    case Success(value):
        ...
    case Failure(SpecificError()):
        ...
    case Failure(error):  # Catch-all
        ...
```

### 4. Не используй exceptions в бизнес-логике

```python
# ❌ Плохо
try:
    user = get_user(id)
except UserNotFound:
    return None

# ✅ Хорошо
result = await action.run(id)
match result:
    case Success(user): ...
    case Failure(UserNotFoundError()): ...
```

---

---

## ❌ Error: Sync код блокирует event loop

### Симптом
Приложение "зависает", медленный ответ, таймауты.

### Причина
CPU-bound операция (bcrypt, парсинг) блокирует async event loop.

### Решение
```python
# ❌ Плохо — блокирует event loop
async def run(self, data: CreateUserRequest) -> Result[User, Error]:
    # bcrypt — CPU-bound операция!
    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())
    ...

# ✅ Хорошо — выносим в thread pool
import anyio

async def run(self, data: CreateUserRequest) -> Result[User, Error]:
    password_hash = await anyio.to_thread.run_sync(
        lambda: bcrypt.hashpw(data.password.encode(), bcrypt.gensalt())
    )
    ...

# ✅ Или используй SyncTask
password_hash = await anyio.to_thread.run_sync(
    self.hash_password.run, data.password
)
```

---

## ❌ Error: Несовместимые Error типы

### Симптом
```
mypy: Incompatible types in return (got "Result[User, ValidationError]", 
expected "Result[User, UserError]")
```

### Решение
```python
# ✅ Решение 1 — общий базовый класс ошибок
class AppError(BaseError): ...
class UserError(AppError): ...
class ValidationError(AppError): ...

async def run(self, data: Request) -> Result[User, AppError]:
    validated = self.validate(data)  # OK!

# ✅ Решение 2 — map_failure для преобразования
async def run(self, data: Request) -> Result[User, UserError]:
    validated = self.validate(data).map_failure(
        lambda e: UserValidationError(message=str(e))
    )
```

---

## ✅ Quick Fix Checklist

```
Result Issue Debugging:
- [ ] Все ветки Action возвращают Success/Failure?
- [ ] Error классы имеют http_status?
- [ ] Controller использует @result_handler?
- [ ] Pattern matching exhaustive (обрабатывает все случаи)?
- [ ] CPU-bound код вынесен в anyio.to_thread?
- [ ] Нет raise в бизнес-логике?
- [ ] Типы ошибок совместимы в цепочке?
```

---

## 📊 Стандартные HTTP статусы

| Ошибка | http_status |
|--------|-------------|
| NotFound | 404 |
| AlreadyExists | 409 |
| ValidationError | 422 |
| Unauthorized | 401 |
| Forbidden | 403 |
| InternalError | 500 |

---

## 🔗 Связанные

- **Standards:** `../standards/global/error-handling.md`
- **Patterns:** `../standards/architecture/patterns.md`
- **Docs:** `foxdocs/returns-master/docs/`



