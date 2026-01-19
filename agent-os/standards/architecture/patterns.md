# 🎨 Architectural Patterns — Шпаргалка

> Ключевые паттерны Hyper-Porto v4. Детали: [`docs/03-components.md`](../../../docs/03-components.md)

---

## 1️⃣ Result Pattern (Railway-Oriented Programming)

### Концепция
```
Success track: ────────────────────────────▶ Success(value)
                    ╲
Failure track:       ╲─────────────────────▶ Failure(error)
```

### Использование
```python
from returns.result import Result, Success, Failure

async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
    # Проверка → Failure track
    if await self.uow.users.find_by_email(data.email):
        return Failure(UserAlreadyExistsError(email=data.email))
    
    # Успех → Success track
    user = AppUser(email=data.email, ...)
    return Success(user)
```

### Pattern Matching
```python
match result:
    case Success(user):
        return UserResponse.from_entity(user)
    case Failure(UserNotFoundError(user_id=uid)):
        raise DomainException(UserNotFoundError(user_id=uid))
    case Failure(error):
        raise DomainException(error)
```

### @result_handler (автоматизация)
```python
@post("/users")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(action: FromDishka[CreateUserAction]) -> Result[AppUser, UserError]:
    return await action.run(data)
# Success → Response(UserResponse, 201)
# Failure → DomainException → Problem Details (RFC 9457)
```

---

## 2️⃣ CQRS (Command Query Responsibility Segregation)

### Концепция
```
┌─────────────┐     ┌─────────────┐
│   COMMAND   │     │    QUERY    │
│   (Write)   │     │   (Read)    │
├─────────────┤     ├─────────────┤
│   Action    │     │   Query     │
│   + UoW     │     │   Direct    │
│   + Events  │     │   ORM       │
└─────────────┘     └─────────────┘
```

### Command (Write) → Action
```python
@post("/users")
@result_handler(UserResponse, success_status=HTTP_201_CREATED)
async def create_user(action: FromDishka[CreateUserAction]):
    return await action.run(data)  # Через UoW + Events
```

### Query (Read) → Query class
```python
@get("/users/{user_id}")
async def get_user(query: FromDishka[GetUserQuery], user_id: UUID):
    user = await query.execute(GetUserQueryInput(user_id=user_id))
    if not user:
        raise DomainException(UserNotFoundError(user_id=user_id))
    return UserResponse.from_entity(user)
```

### Сравнение

| Аспект | Action (Command) | Query |
|--------|------------------|-------|
| Операция | Write (INSERT/UPDATE/DELETE) | Read (SELECT) |
| Return | `Result[T, Error]` | `T` или `T \| None` |
| UoW | Использует | НЕ использует |
| Events | Публикует | НЕ публикует |
| Method | `run()` | `execute()` |

---

## 3️⃣ Repository Pattern

### Концепция
```
Controller → Action → Repository → ORM (Piccolo)
                 ↓
             UnitOfWork (транзакции)
```

### Реализация
```python
class UserRepository(Repository[AppUser]):
    """Repository для AppUser."""
    
    model = AppUser
    
    async def find_by_email(self, email: str) -> AppUser | None:
        return await AppUser.objects().where(AppUser.email == email).first()
    
    # CRUD методы наследуются от Repository[T]:
    # - add(entity)
    # - update(entity) 
    # - delete(entity)
    # - get(id)
```

### Hooks (расширение)
```python
async def _on_add(self, entity: AppUser) -> None:
    """Hook called before adding entity."""
    entity.created_at = datetime.utcnow()

async def _on_update(self, entity: AppUser) -> None:
    """Hook called before updating entity."""
    entity.updated_at = datetime.utcnow()
```

---

## 4️⃣ Unit of Work Pattern

### Концепция
```
async with uow:
    ┌─────────────────────────────────────┐
    │         TRANSACTION                  │
    │  1. Repository operations            │
    │  2. Add events to queue              │
    │  3. commit() → _committed = True     │
    └─────────────────────────────────────┘
              ↓ __aexit__
    ┌─────────────────────────────────────┐
    │  4. DB COMMIT                        │
    │  5. Publish events via app.emit()    │
    └─────────────────────────────────────┘
```

### Использование
```python
async with self.uow:
    # 1. Операции с данными
    user = AppUser(email=data.email, ...)
    await self.uow.users.add(user)
    
    # 2. Добавление события
    self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
    
    # 3. Commit (ставит флаг)
    await self.uow.commit()

# 4-5. __aexit__: DB commit → events published
```

### Важно
- `commit()` только ставит флаг `_committed = True`
- Реальный DB commit в `__aexit__`
- События публикуются **ПОСЛЕ** успешного DB commit
- При exception → rollback, события НЕ публикуются

---

## 5️⃣ Domain Events Pattern

### Концепция
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Action     │────▶│    UoW       │────▶│  Listeners   │
│              │     │  add_event() │     │  @listener   │
│              │     │  commit()    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     app.emit("UserCreated", ...)
```

### Публикация (в Action через UoW)
```python
async with self.uow:
    await self.uow.users.add(user)
    self.uow.add_event(UserCreated(
        user_id=user.id,
        email=user.email,
        name=user.name,
    ))
    await self.uow.commit()
```

### Подписка (Listener)
```python
from litestar.events import listener

@listener("UserCreated")
async def on_user_created(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    logfire.info("🎉 User created", user_id=user_id, email=email)
    # WebSocket notification, send email, update cache, etc.
```

### Регистрация в App.py
```python
app = Litestar(
    listeners=[
        on_user_created,
        on_user_updated,
        on_user_deleted,
    ],
)
```

---

## 6️⃣ Action/Task Pattern

### Иерархия
```
Controller
    ↓
Action (Use Case) ─────────▶ Result[T, E]
    │
    ├── Task (атомарная операция) ─▶ T
    ├── Task
    └── UoW (Repository + Events)
```

### Action = Use Case (оркестрация)
```python
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    def __init__(self, hash_password: HashPasswordTask, uow: UserUnitOfWork):
        self.hash_password = hash_password
        self.uow = uow
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # Orchestration of Tasks and Repository
        password_hash = await anyio.to_thread.run_sync(
            self.hash_password.run, data.password
        )
        # ...
```

### Task = Атомарная операция (переиспользуемая)
```python
class HashPasswordTask(SyncTask[str, str]):
    def run(self, password: str) -> str:
        salt = bcrypt.gensalt(rounds=self.rounds)
        return bcrypt.hashpw(password.encode(), salt).decode()
```

---

## 📐 Сводная таблица

| Паттерн | Где используется | Ключевая идея |
|---------|------------------|---------------|
| **Result** | Actions, Controllers | Явная обработка ошибок |
| **CQRS** | Actions (write), Queries (read) | Разделение чтения/записи |
| **Repository** | Data Layer | Абстракция над ORM |
| **UnitOfWork** | Actions | Транзакции + Events |
| **Domain Events** | UoW → Listeners | Межмодульное общение |
| **Action/Task** | Business Logic | Оркестрация vs атомарность |

---

## 📚 Детальная документация

- **Компоненты:** [`docs/03-components.md`](../../../docs/03-components.md)
- **Result/Railway:** [`docs/04-result-railway.md`](../../../docs/04-result-railway.md)
- **Events:** [`docs/11-litestar-features.md`](../../../docs/11-litestar-features.md)
- **Cross-module:** [`docs/13-cross-module-communication.md`](../../../docs/13-cross-module-communication.md)



