# Подсказки: Создание модуля User

## Шаг 1: Структура папок

### Уровень 1
Посмотри структуру существующих модулей в `src/Containers/`.

### Уровень 2
Каждая папка должна содержать `__init__.py`.

### Уровень 3
```bash
mkdir -p src/Containers/AppSection/UserModule/{Models,Data,Actions,UI/API}
touch src/Containers/AppSection/UserModule/__init__.py
```

---

## Шаг 2: Модель User

### Уровень 1
Посмотри `src/Ship/Parents/Model.py` и документацию Piccolo.

### Уровень 2
Модель наследует `Table`. Используй `UUID()`, `Varchar()`, `Boolean()`, `Timestamptz()`.

### Уровень 3
```python
from piccolo.table import Table
from piccolo.columns import UUID, Varchar, Boolean, Timestamptz

class User(Table):
    id = UUID(primary_key=True)
    email = Varchar(length=255, unique=True)
    # ...
```

---

## Шаг 3: Ошибки

### Уровень 1
Посмотри `src/Ship/Core/Errors.py`.

### Уровень 2
Наследуй от `BaseError` и `ErrorWithTemplate`. Добавь `http_status`.

### Уровень 3
```python
class UserNotFoundError(ErrorWithTemplate, UserError):
    _message_template: ClassVar[str] = "User {user_id} not found"
    http_status: int = 404
    user_id: UUID
```

---

## Шаг 4: Schemas

### Уровень 1
Request — `BaseModel`, Response — `EntitySchema`.

### Уровень 2
Используй `Field()` для валидации, `EmailStr` для email.

### Уровень 3
```python
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
```

---

## Шаг 5: Repository

### Уровень 1
Посмотри `src/Ship/Parents/Repository.py`.

### Уровень 2
Repository работает с одной моделью. Методы: `get(id)`, `add(entity)`, `find_by_*(field)`.

### Уровень 3
```python
class UserRepository(BaseRepository[User]):
    async def find_by_email(self, email: str) -> User | None:
        return await User.select().where(User.email == email).first()
```

---

## Шаг 6: UnitOfWork

### Уровень 1
Посмотри `src/Ship/Parents/UnitOfWork.py`.

### Уровень 2
UoW содержит repositories и управляет транзакцией.

### Уровень 3
```python
@dataclass
class UserUnitOfWork(BaseUnitOfWork):
    users: UserRepository = field(default=None)
```

---

## Шаг 7: Actions

### Уровень 1
Action возвращает `Result[T, E]`. Используй `Success()` и `Failure()`.

### Уровень 2
```python
async with self.uow:
    # операции
    await self.uow.commit()
return Success(result)
```

### Уровень 3
```python
@dataclass
class CreateUserAction(Action[CreateUserRequest, User, UserError]):
    uow: UserUnitOfWork
    
    async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
        existing = await self.uow.users.find_by_email(data.email)
        if existing:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        async with self.uow:
            user = User(email=data.email, name=data.name, ...)
            await self.uow.users.add(user)
            await self.uow.commit()
        
        return Success(user)
```

---

## Шаг 8: Controller

### Уровень 1
Используй `@result_handler` для POST/PATCH, прямой return для GET.

### Уровень 2
Инжекти Action через `FromDishka[ActionClass]`.

### Уровень 3
```python
class UserController(Controller):
    path = "/api/v1/users"
    
    @post("/")
    @result_handler(UserResponse, success_status=201)
    async def create_user(
        self, data: CreateUserRequest, action: FromDishka[CreateUserAction]
    ) -> Result[User, UserError]:
        return await action.run(data)
```

---

## Шаг 9: Providers

### Уровень 1
Каждый компонент регистрируется через `provide()`.

### Уровень 2
APP scope — синглтоны, REQUEST scope — per-request.

### Уровень 3
```python
class UserModuleProvider(Provider):
    scope = Scope.REQUEST
    
    user_repository = provide(UserRepository)
    user_uow = provide(UserUnitOfWork)
    create_user_action = provide(CreateUserAction)
```
