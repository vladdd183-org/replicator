# 🚂 Railway-Oriented Programming

> **Версия:** 4.1 | **Дата:** Январь 2026  
> Функциональная обработка ошибок с библиотекой `returns` и Pattern Matching

---

## 🎯 Философия

**Railway-oriented programming** — метафора для обработки ошибок:

```
Success Track  ═══════╦═══════╦═══════╦═══════► Success(user)
                      ║       ║       ║
                      ╠═══════╬═══════╬═══════► Failure(error)
Failure Track         ║       ║       ║
                      
                   Step 1  Step 2  Step 3
                   Check   Hash    Save
                   Email   Pass    User
```

- **Success Track** — всё хорошо, данные передаются дальше
- **Failure Track** — произошла ошибка, остальные шаги пропускаются

---

## 📦 Библиотека `returns`

### Основные типы

```python
from returns.result import Result, Success, Failure
from returns.maybe import Maybe, Some, Nothing
from returns.pipeline import flow
from returns.pointfree import bind
```

### Result[T, E] — основной контейнер

```python
from returns.result import Result, Success, Failure

# Пример функции, возвращающей Result
def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Failure("Division by zero")
    return Success(a / b)

# Использование
result = divide(10, 2)   # Success(5.0)
result = divide(10, 0)   # Failure("Division by zero")
```

---

## 🏗️ Реальные примеры из проекта

### CreateUserAction — полный пример

```python
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py

@dataclass
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create a new user."""
    
    hash_password: HashPasswordTask
    uow: UserUnitOfWork

    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # Step 1: Check if email exists → Failure track if exists
        existing_user = await self.uow.users.find_by_email(data.email)
        if existing_user is not None:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        # Step 2: Hash password (CPU-bound → thread pool)
        password_hash = await anyio.to_thread.run_sync(
            self.hash_password.run, data.password
        )
        
        # Step 3: Create user within transaction
        async with self.uow:
            user = AppUser(
                email=data.email,
                password_hash=password_hash,
                name=data.name,
            )
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
            await self.uow.commit()
        
        # Success track
        return Success(user)
```

### AuthenticateAction — множественные проверки

```python
# src/Containers/AppSection/UserModule/Actions/AuthenticateAction.py

class AuthenticateAction(Action[LoginRequest, AuthResult, UserError]):
    """Use Case: Authenticate user and return JWT tokens."""
    
    def __init__(
        self,
        uow: UserUnitOfWork,
        verify_password_task: VerifyPasswordTask,
        generate_token_task: GenerateTokenTask,
    ) -> None:
        self.uow = uow
        self.verify_password_task = verify_password_task
        self.generate_token_task = generate_token_task
    
    async def run(self, data: LoginRequest) -> Result[AuthResult, UserError]:
        # Step 1: Find user by email
        user = await self.uow.users.find_by_email(data.email)
        if user is None:
            return Failure(InvalidCredentialsError())  # → Failure track
        
        # Step 2: Verify password (offload to thread)
        is_valid = await anyio.to_thread.run_sync(
            self.verify_password_task.run,
            VerifyPasswordInput(
                password=data.password,
                password_hash=user.password_hash,
            ),
        )
        if not is_valid:
            return Failure(InvalidCredentialsError())  # → Failure track
        
        # Step 3: Check if user is active
        if not user.is_active:
            return Failure(UserInactiveError(user_id=user.id))  # → Failure track
        
        # Step 4: Generate tokens
        tokens = self.generate_token_task.run(
            GenerateTokenInput(user_id=user.id, email=user.email)
        )
        
        # Success track
        return Success(AuthResult(
            tokens=tokens,
            user_id=str(user.id),
            email=user.email,
        ))
```

---

## 🎭 Pattern Matching (Python 3.10+)

### Базовый match в Controller

```python
# БЕЗ @result_handler — ручной match
@post("/users")
async def create_user(data: CreateUserRequest, action: FromDishka[CreateUserAction]):
    result = await action.run(data)
    
    match result:
        case Success(user):
            return Response(
                content=UserResponse.from_entity(user),
                status_code=201
            )
        case Failure(UserAlreadyExistsError(email=email)):
            return Response(
                content={"error": f"Email {email} already exists"},
                status_code=409
            )
        case Failure(error):
            return Response(
                content={"error": error.message},
                status_code=error.http_status
            )
```

### С @result_handler — автоматический match

```python
# С @result_handler — автоматическая конвертация
@post("/users")
@result_handler(UserResponse, success_status=201)
async def create_user(data: CreateUserRequest, action: FromDishka[CreateUserAction]):
    return await action.run(data)  # Result автоматически конвертируется
```

### Match в CLI

```python
# src/Containers/AppSection/UserModule/UI/CLI/Commands.py

@users_group.command(name="create")
@with_container
async def create_user(container, email: str, password: str, name: str) -> None:
    action = await container.get(CreateUserAction)
    request = CreateUserRequest(email=email, password=password, name=name)
    result = await action.run(request)
    
    match result:
        case Success(user):
            console.print(f"[green]✓[/green] User created successfully!")
            console.print(f"  ID: {user.id}")
            console.print(f"  Email: {user.email}")
        case Failure(error):
            console.print(f"[red]✗[/red] Error: {error.message}")
            raise SystemExit(1)
```

### Match в GraphQL

```python
# src/Containers/AppSection/UserModule/UI/GraphQL/Resolvers.py

@strawberry.mutation
async def create_user(self, input: CreateUserInput, info: strawberry.Info) -> CreateUserPayload:
    action = await get_dependency(info, CreateUserAction)
    request = input.to_pydantic()
    result = await action.run(request)
    
    match result:
        case Success(user):
            return CreateUserPayload(user=_user_to_graphql(user))
        case Failure(error):
            return CreateUserPayload(
                error=UserErrorType(message=error.message, code=error.code)
            )
```

---

## 🔗 Композиция операций

### Метод `map` — преобразование Success

```python
from returns.result import Success

result = Success(5)
doubled = result.map(lambda x: x * 2)  # Success(10)
```

### Метод `bind` — цепочка Result-функций

```python
from returns.result import Result, Success, Failure
from returns.pointfree import bind

def validate_email(email: str) -> Result[str, ValidationError]:
    if "@" not in email:
        return Failure(ValidationError("Invalid email"))
    return Success(email.lower())

def validate_name(name: str) -> Result[str, ValidationError]:
    if len(name) < 2:
        return Failure(ValidationError("Name too short"))
    return Success(name)

# Композиция с bind
final_result = (
    Success({"email": "Test@Example.com", "name": "John"})
    .bind(lambda d: validate_email(d["email"]).map(lambda e: {**d, "email": e}))
    .bind(lambda d: validate_name(d["name"]).map(lambda n: {**d, "name": n}))
)
```

### Функция `flow` — пайплайн

```python
from returns.pipeline import flow
from returns.pointfree import bind

async def create_user(data: CreateUserDTO) -> Result[User, UserError]:
    return await flow(
        data,
        validate_email,           # → Result[ValidatedEmail, ValidationError]
        bind(validate_password),  # → Result[ValidatedData, ValidationError]
        bind(hash_password),      # → Result[HashedData, HashError]
        bind(save_to_db),         # → Result[User, DBError]
    )
```

---

## ⚠️ Типизированные ошибки

### Базовые классы ошибок

```python
# src/Ship/Core/Errors.py

class BaseError(BaseModel):
    """Base error with HTTP status mapping."""
    model_config = {"frozen": True}
    
    message: str
    code: str = "ERROR"
    http_status: int = 400


class ErrorWithTemplate(BaseError):
    """Auto-generates message from template."""
    _message_template: ClassVar[str] = ""
    
    @model_validator(mode="before")
    @classmethod
    def auto_generate_message(cls, data: dict[str, Any]) -> dict[str, Any]:
        if isinstance(data, dict) and "message" not in data and cls._message_template:
            data["message"] = cls._message_template.format(**data)
        return data
```

### Модульные ошибки

```python
# src/Containers/AppSection/UserModule/Errors.py

class UserError(BaseError):
    """Base error for UserModule."""
    pass


class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID


class UserAlreadyExistsError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User with email {email} already exists"
    code: str = "USER_ALREADY_EXISTS"
    http_status: int = 409
    email: str


class InvalidCredentialsError(UserError):
    message: str = "Invalid email or password"
    code: str = "INVALID_CREDENTIALS"
    http_status: int = 401


class UserInactiveError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User account {user_id} is deactivated"
    code: str = "USER_INACTIVE"
    http_status: int = 403
    user_id: UUID
```

### Использование в match

```python
match result:
    case Failure(UserNotFoundError(user_id=uid)):
        console.print(f"User {uid} not found")
    
    case Failure(UserAlreadyExistsError(email=email)):
        console.print(f"Email {email} already taken")
    
    case Failure(InvalidCredentialsError()):
        console.print("Invalid credentials")
    
    case Failure(error):
        console.print(f"Unknown error: {error.message}")
```

---

## 🔄 Error Recovery (lash)

```python
from returns.result import Result, Success, Failure

async def get_user_with_fallback(user_id: UUID) -> Result[User, UserError]:
    """Try cache first, fallback to database."""
    
    cache_result = await get_from_cache(user_id)
    
    # lash — handle Failure, possibly recover
    return await cache_result.lash(
        lambda _: get_from_database(user_id)  # Fallback
    )


# More sophisticated fallback
async def get_user_smart(user_id: UUID) -> Result[User, UserError]:
    cache_result = await get_from_cache(user_id)
    
    async def fallback(error: CacheError) -> Result[User, UserError]:
        match error:
            case CacheMissError():
                # Normal — just not in cache
                return await get_from_database(user_id)
            case CacheConnectionError():
                # Critical — log and go to DB
                logger.warning("Cache unavailable")
                return await get_from_database(user_id)
    
    return await cache_result.lash(fallback)
```

---

## 📋 Parallel Validation

```python
from returns.result import Result, Success, Failure
from typing import Sequence


def validate_all(validations: Sequence[Result[T, E]]) -> Result[Sequence[T], Sequence[E]]:
    """Collect all errors, don't stop at first."""
    
    successes = []
    failures = []
    
    for result in validations:
        match result:
            case Success(value):
                successes.append(value)
            case Failure(error):
                failures.append(error)
    
    if failures:
        return Failure(tuple(failures))
    return Success(tuple(successes))


# Usage
def validate_user_data(data: dict) -> Result[ValidatedData, tuple[ValidationError, ...]]:
    validations = [
        validate_email(data.get("email", "")),
        validate_password(data.get("password", "")),
        validate_name(data.get("name", "")),
    ]
    
    result = validate_all(validations)
    
    match result:
        case Success((email, password, name)):
            return Success(ValidatedData(email=email, password=password, name=name))
        case Failure(errors):
            return Failure(errors)
```

---

## 🎨 Декоратор @safe

```python
from returns.result import safe, Result


@safe
def parse_json(data: str) -> dict:
    """Automatically wraps exceptions in Failure."""
    import json
    return json.loads(data)


# parse_json("valid json") → Success({"key": "value"})
# parse_json("invalid") → Failure(JSONDecodeError(...))


# With exception filter
@safe(exceptions=(ValueError, TypeError))
def parse_int(data: str) -> int:
    return int(data)


# parse_int("123") → Success(123)
# parse_int("abc") → Failure(ValueError(...))
```

---

## 🚀 Интеграция с @result_handler

```python
# src/Ship/Decorators/result_handler.py

def result_handler(
    response_dto: Type[BaseModel] | None,
    success_status: int = 200,
):
    """Decorator for automatic Result → Response conversion.
    
    Success(value) → Response(dto.from_entity(value), success_status)
    Failure(error) → DomainException(error) → Problem Details (RFC 9457)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            match result:
                case Success(value):
                    if response_dto is None or value is None:
                        return Response(content=None, status_code=success_status)
                    content = _convert_to_dto(response_dto, value)
                    return Response(content=content, status_code=success_status)
                
                case Failure(error):
                    if isinstance(error, BaseError):
                        raise DomainException(error)
                    else:
                        raise Exception(str(error))
        
        return wrapper
    return decorator
```

---

## 📊 Когда использовать Result

### ✅ Используй Result когда:

- Операция может завершиться **ожидаемой** ошибкой
- Вызывающий код **должен** обработать ошибку
- Нужна **композиция** операций
- Важна **типизация** ошибок
- Публичный API (Actions)

### ❌ НЕ используй Result когда:

- Ошибка **невосстановимая** (используй Exception)
- Простая **валидация входных данных** (используй Pydantic)
- **Внутренний** код без публичного API
- Операция **не может** завершиться ошибкой

---

## 🔧 Настройка mypy

```toml
# pyproject.toml
[tool.mypy]
plugins = ["returns.contrib.mypy.returns_plugin"]
```

```python
# Теперь mypy понимает Result
from returns.result import Result, Success

def get_user(id: int) -> Result[User, NotFoundError]:
    ...

result = get_user(1)
# mypy знает: result может быть Success[User] или Failure[NotFoundError]

match result:
    case Success(user):
        # mypy знает: user это User
        print(user.name)
    case Failure(error):
        # mypy знает: error это NotFoundError
        print(error.entity)
```

---

<div align="center">

**Следующий раздел:** [05-concurrency.md](05-concurrency.md) — Structured Concurrency с anyio

</div>
