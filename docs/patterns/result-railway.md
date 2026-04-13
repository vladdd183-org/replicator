# Паттерн: Result Railway

> Все Actions возвращают `Result[T, E]`. Успех и ошибка -- два явных трека. Никаких скрытых исключений.

---

## Суть

```python
from returns.result import Result, Success, Failure

async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    if user_exists:
        return Failure(UserAlreadyExistsError(email=data.email))
    # ...
    return Success(user)
```

Success track: данные текут через pipeline без прерываний.
Failure track: ошибка немедленно прерывает pipeline, но ЯВНО.

---

## Контракт Action

```python
class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    @abstractmethod
    async def run(self, data: InputT) -> Result[OutputT, ErrorT]:
        ...
```

- `InputT` -- тип входных данных (Pydantic model)
- `OutputT` -- тип успешного результата
- `ErrorT` -- тип ошибки (наследник BaseError, Pydantic frozen)

---

## Ошибки как данные

```python
from pydantic import BaseModel

class BaseError(BaseModel, frozen=True):
    code: str
    message: str
    http_status: int = 400

class ErrorWithTemplate(BaseError):
    _message_template: ClassVar[str]
    # message генерируется автоматически из шаблона + полей

class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "Пользователь с id {user_id} не найден"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID
```

Ошибки -- Pydantic frozen models. Они сериализуемы, типизированы, immutable.

---

## Pattern Matching в контроллерах

```python
@post("/")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(
    self,
    data: CreateUserRequest,
    action: FromDishka[CreateUserAction],
) -> Result[AppUser, UserError]:
    return await action.run(data)
```

`@result_handler` автоматически преобразует:
- `Success(user)` -> `Response(UserResponse.from_entity(user), status=201)`
- `Failure(error)` -> `DomainException(error)` -> Problem Details (RFC 9457)

---

## Почему это важно для Replicator

1. **Детерминированность** -- Result можно сериализовать, кешировать, передавать между агентами
2. **Evidence** -- Failure содержит полную информацию об ошибке для evidence bundle
3. **Web3 ready** -- Result = чистая функция, совместима с WASM и IPVM
4. **Agent-friendly** -- агент может pattern match на результат и принять решение
