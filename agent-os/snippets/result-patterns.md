# 🧩 Snippets: Result Patterns

> Готовые паттерны работы с `Result[T, E]`.

---

## Pattern Matching

### Базовый match
```python
match result:
    case Success(value):
        return value
    case Failure(error):
        raise DomainException(error)
```

### Match с конкретными ошибками
```python
match result:
    case Success(user):
        return UserResponse.from_entity(user)
    case Failure(UserNotFoundError(user_id=uid)):
        raise DomainException(UserNotFoundError(user_id=uid))
    case Failure(UserInactiveError()):
        raise DomainException(UserInactiveError())
    case Failure(error):
        raise DomainException(error)
```

### Match для GraphQL
```python
match result:
    case Success(user):
        return CreateUserPayload(user=user_to_graphql(user))
    case Failure(error):
        return CreateUserPayload(error=ErrorType(
            message=error.message,
            code=error.code,
        ))
```

---

## Early Return Pattern

### Последовательные проверки
```python
async def run(self, data) -> Result[User, UserError]:
    # Check 1
    existing = await self.uow.users.find_by_email(data.email)
    if existing:
        return Failure(UserAlreadyExistsError(email=data.email))
    
    # Check 2
    if not is_valid_domain(data.email):
        return Failure(InvalidEmailDomainError(email=data.email))
    
    # Check 3
    if data.age < 18:
        return Failure(UserTooYoungError(age=data.age))
    
    # Success path
    user = User(...)
    return Success(user)
```

---

## Композиция Results

### Последовательная с early return
```python
async def run(self, data) -> Result[Order, OrderError]:
    # Step 1: Validate user
    user_result = await self.validate_user(data.user_id)
    if isinstance(user_result, Failure):
        return user_result
    user = user_result.unwrap()
    
    # Step 2: Validate products
    products_result = await self.validate_products(data.product_ids)
    if isinstance(products_result, Failure):
        return products_result
    products = products_result.unwrap()
    
    # Step 3: Create order
    order = Order(user=user, products=products)
    return Success(order)
```

### С flow и bind (функциональный стиль)
```python
from returns.pipeline import flow
from returns.pointfree import bind

result = flow(
    Success(data),
    bind(validate_email),
    bind(check_unique),
    bind(create_user),
)
```

---

## Конвертация

### Optional → Result
```python
def optional_to_result(value: T | None, error: E) -> Result[T, E]:
    if value is None:
        return Failure(error)
    return Success(value)

# Использование
user = await repo.get(user_id)
result = optional_to_result(user, UserNotFoundError(user_id=user_id))
```

### Result → HTTP Response (автоматически)
```python
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(...) -> Result[User, UserError]:
    return await action.run(data)
# Success → Response(UserResponse, 201)
# Failure → DomainException → Problem Details
```

---

## Обработка списка Results

### Собрать все успехи или первую ошибку
```python
from returns.iterables import Fold

results: list[Result[User, Error]] = [...]

# Все Success → Success(list[User])
# Любой Failure → первый Failure
combined = Fold.collect(results, Success(()))
```

### Параллельная обработка
```python
async def process_batch(items: list[Item]) -> list[Result[Output, Error]]:
    results = []
    async with anyio.create_task_group() as tg:
        for item in items:
            tg.start_soon(process_one, item, results)
    return results
```

---

## Value Extraction

### Безопасное извлечение
```python
# С дефолтом
value = result.value_or(default_value)

# Только для Success (иначе exception)
value = result.unwrap()  # Осторожно!

# Проверка типа
if isinstance(result, Success):
    value = result.unwrap()
```



