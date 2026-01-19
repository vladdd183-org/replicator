# 🧩 Компоненты Hyper-Porto

> **Версия:** 4.3 | **Дата:** Январь 2026

В этом разделе подробно описаны все компоненты архитектуры с **реальными примерами из проекта**.

---

## 📋 Обзор компонентов

| Компонент | Слой | Назначение | Примеры |
|-----------|------|------------|---------|
| **Controller** | UI | HTTP/GraphQL/CLI входные точки | `UserController`, `AuthController` |
| **Action** | Business | Use Cases (CQRS Command) | `CreateUserAction`, `AuthenticateAction` |
| **Task** | Business | Атомарные операции | `HashPasswordTask`, `VerifyPasswordTask`, `GenerateTokenTask` |
| **Query** | Business | CQRS Queries (Read) | `GetUserQuery`, `ListUsersQuery` |
| **Repository** | Data | Абстракция над ORM | `UserRepository` |
| **UnitOfWork** | Data | Транзакции + события | `UserUnitOfWork` |
| **Gateway** | Infrastructure | Межмодульное взаимодействие | `PaymentGateway`, `DirectPaymentAdapter` |
| **Model** | Data | ORM Entity (Piccolo Table) | `AppUser` |
| **Event** | Domain | Domain Events | `UserCreated`, `UserUpdated`, `UserDeleted` |
| **Schema** | Data | Pydantic DTOs | `CreateUserRequest`, `UserResponse`, `AuthResponse` |
| **Error** | Domain | Типизированные ошибки | `UserNotFoundError`, `InvalidCredentialsError` |
| **Listener** | Infrastructure | Обработчики событий | `on_user_created`, `on_user_updated` |
| **Provider** | Infrastructure | DI регистрация (Dishka) | `UserModuleProvider`, `UserRequestProvider` |
| **GraphQL** | UI | Strawberry resolvers | `UserQuery`, `UserMutation` |
| **CLI** | UI | Click commands | `users_group` |
| **Worker** | UI | TaskIQ background tasks | `send_welcome_email_task` |
| **WebSocket** | UI | Real-time handlers | `user_updates_handler` |

---

## 🎬 Action (Use Case)

**Назначение:** Инкапсуляция бизнес-логики. Оркестрирует Tasks, Repositories, UoW.

### Принципы:

1. **Один Action — одна бизнес-операция**
2. **Возвращает `Result[T, E]`** — явная обработка ошибок
3. **Transport-agnostic** — не знает о HTTP/GraphQL/CLI
4. **Orchestration** — координирует Tasks и Repositories
5. **Транзакционность** — через UnitOfWork
6. **DI через __init__** — зависимости инъектируются через Dishka

### Базовый класс

```python
# src/Ship/Parents/Action.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from returns.result import Result

InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)
ErrorT = TypeVar("ErrorT", covariant=True)


class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    """Base Action class.
    
    Actions represent the Use Cases of the Application.
    Every Action should be responsible for performing a single use case.
    
    Rules:
    - One Action = one Use Case (Single Responsibility)
    - Always returns Result[OutputT, ErrorT]
    - Orchestrates Tasks, does not contain low-level logic
    - Does NOT know about HTTP, WebSocket, etc.
    - Does NOT call other Actions directly (use SubAction pattern)
    
    Example:
        class CreateUserAction(Action[CreateUserRequest, User, UserError]):
            async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
                ...
    """
    
    @abstractmethod
    async def run(self, data: InputT) -> Result[OutputT, ErrorT]:
        """Execute the action.
        
        Args:
            data: Input data for the action
            
        Returns:
            Result[OutputT, ErrorT]: Success with output or Failure with error
        """
        ...
```

### Реальный пример: CreateUserAction

```python
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py
import anyio
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserAlreadyExistsError
from src.Containers.AppSection.UserModule.Events import UserCreated
from src.Containers.AppSection.UserModule.Models.User import AppUser
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask


class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create a new user.
    
    Steps:
    1. Check if email already exists
    2. Hash password
    3. Create user entity
    4. Save to database
    5. Publish UserCreated event
    
    Example:
        result = await action.run(CreateUserRequest(
            email="user@example.com",
            password="password123",
            name="John Doe",
        ))
    """
    
    def __init__(
        self,
        hash_password: HashPasswordTask,
        uow: UserUnitOfWork,
    ) -> None:
        self.hash_password = hash_password
        self.uow = uow
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # Step 1: Check if email already exists
        existing_user = await self.uow.users.find_by_email(data.email)
        if existing_user is not None:
            return Failure(UserAlreadyExistsError(email=data.email))
        
        # Step 2: Hash password (offload to thread to avoid blocking event loop)
        password_hash = await anyio.to_thread.run_sync(self.hash_password.run, data.password)
        
        # Step 3: Create user entity
        user = AppUser(
            email=data.email,
            password_hash=password_hash,
            name=data.name,
        )
        
        # Step 4-5: Save to database and publish event
        async with self.uow:
            await self.uow.users.add(user)
            
            # Add domain event (published after commit)
            self.uow.add_event(UserCreated(
                user_id=user.id,
                email=user.email,
            ))
            
            await self.uow.commit()
        
        return Success(user)
```

### Реальный пример: DeleteUserAction

```python
# src/Containers/AppSection/UserModule/Actions/DeleteUserAction.py
from uuid import UUID
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Events import UserDeleted


class DeleteUserAction(Action[UUID, None, UserError]):
    """Use Case: Delete user by ID (soft delete).
    
    Returns Result[None, UserError] for compatibility with @result_handler.
    
    Example:
        result = await action.run(user_id)
        
        match result:
            case Success(None):
                print("User deleted")
            case Failure(UserNotFoundError()):
                print("User not found")
    """
    
    def __init__(self, uow: UserUnitOfWork) -> None:
        self.uow = uow
    
    async def run(self, data: UUID) -> Result[None, UserError]:
        user = await self.uow.users.get(data)
        
        if user is None:
            return Failure(UserNotFoundError(user_id=data))
        
        async with self.uow:
            # Soft delete - deactivate user
            await self.uow.users.deactivate(user)
            
            # Add domain event
            self.uow.add_event(UserDeleted(
                user_id=user.id,
                email=user.email,
            ))
            
            await self.uow.commit()
        
        return Success(None)
```

### Реальный пример: UpdateUserAction

```python
# src/Containers/AppSection/UserModule/Actions/UpdateUserAction.py
from uuid import UUID
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import UpdateUserRequest
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Events import UserUpdated
from src.Containers.AppSection.UserModule.Models.User import AppUser


class UpdateUserInput(BaseModel):
    """Input for UpdateUserAction."""
    model_config = {"frozen": True}
    
    user_id: UUID
    data: UpdateUserRequest


class UpdateUserAction(Action[UpdateUserInput, AppUser, UserError]):
    """Use Case: Update an existing user.
    
    Uses separate Input DTO to combine user_id with update data.
    """
    
    def __init__(self, uow: UserUnitOfWork) -> None:
        self.uow = uow
    
    async def run(self, request: UpdateUserInput) -> Result[AppUser, UserError]:
        # Find user
        user = await self.uow.users.get(request.user_id)
        if user is None:
            return Failure(UserNotFoundError(user_id=request.user_id))
        
        # Track changed fields
        changed_fields: list[str] = []
        
        # Update provided fields
        if request.data.name is not None:
            user.name = request.data.name
            changed_fields.append("name")
        
        if request.data.is_active is not None:
            user.is_active = request.data.is_active
            changed_fields.append("is_active")
        
        # Save and publish event
        if changed_fields:
            async with self.uow:
                await self.uow.users.update(user)
                self.uow.add_event(UserUpdated(
                    user_id=user.id,
                    updated_fields=changed_fields,
                ))
                await self.uow.commit()
        
        return Success(user)
```

### Реальный пример: AuthenticateAction

```python
# src/Containers/AppSection/UserModule/Actions/AuthenticateAction.py
import anyio
from pydantic import BaseModel
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import (
    VerifyPasswordTask,
    VerifyPasswordInput,
)
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import (
    GenerateTokenTask,
    GenerateTokenInput,
    TokenPair,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import LoginRequest
from src.Containers.AppSection.UserModule.Errors import (
    UserError,
    InvalidCredentialsError,
    UserInactiveError,
)


class AuthResult(BaseModel):
    """Result of successful authentication."""
    model_config = {"frozen": True}
    
    tokens: TokenPair
    user_id: str
    email: str


class AuthenticateAction(Action[LoginRequest, AuthResult, UserError]):
    """Use Case: Authenticate user and return JWT tokens.
    
    Example:
        result = await action.run(LoginRequest(
            email="user@example.com",
            password="password123",
        ))
        
        match result:
            case Success(auth):
                print(f"Access token: {auth.tokens.access_token}")
            case Failure(error):
                print(f"Login failed: {error.message}")
    """
    
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
        # Find user by email
        user = await self.uow.users.find_by_email(data.email)
        
        if user is None:
            return Failure(InvalidCredentialsError())
        
        # Verify password (offload to thread to avoid blocking)
        is_valid = await anyio.to_thread.run_sync(
            self.verify_password_task.run,
            VerifyPasswordInput(
                password=data.password,
                password_hash=user.password_hash,
            ),
        )
        
        if not is_valid:
            return Failure(InvalidCredentialsError())
        
        # Check if user is active
        if not user.is_active:
            return Failure(UserInactiveError(user_id=user.id))
        
        # Generate tokens (lightweight CPU operation, no offload needed)
        tokens = self.generate_token_task.run(
            GenerateTokenInput(
                user_id=user.id,
                email=user.email,
            )
        )
        
        return Success(AuthResult(
            tokens=tokens,
            user_id=str(user.id),
            email=user.email,
        ))
```

---

## ⚙️ Task (Atomic Operation)

**Назначение:** Атомарная, переиспользуемая операция. Не содержит бизнес-логику.

### Принципы:

1. **Атомарность** — одно конкретное действие
2. **Переиспользуемость** — между разными Actions
3. **Без бизнес-логики** — только техническая операция
4. **Может быть sync или async** — `Task` для I/O, `SyncTask` для CPU-bound
5. **Pydantic Input** — используйте frozen Pydantic модели для входных данных

### Базовые классы

```python
# src/Ship/Parents/Task.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Task(ABC, Generic[InputT, OutputT]):
    """Base async Task class.
    
    Use for operations that require I/O:
    - External API calls
    - Email sending
    - File operations
    
    Example:
        class SendEmailTask(Task[EmailData, bool]):
            async def run(self, data: EmailData) -> bool:
                await email_client.send(data)
                return True
    """
    
    @abstractmethod
    async def run(self, data: InputT) -> OutputT:
        """Execute the async task."""
        ...


class SyncTask(ABC, Generic[InputT, OutputT]):
    """Synchronous Task class for CPU-bound operations.
    
    Use for operations that don't require I/O:
    - Password hashing
    - Data transformation  
    - Calculations
    - Token generation
    
    For CPU-heavy operations in async context:
        import anyio
        result = await anyio.to_thread.run_sync(task.run, data)
    """
    
    @abstractmethod
    def run(self, data: InputT) -> OutputT:
        """Execute the synchronous task."""
        ...
```

### Реальный пример: HashPasswordTask

```python
# src/Containers/AppSection/UserModule/Tasks/HashPasswordTask.py
import bcrypt

from src.Ship.Parents.Task import SyncTask
from src.Ship.Configs import get_settings


class HashPasswordTask(SyncTask[str, str]):
    """Synchronous task for hashing passwords using bcrypt.
    
    Uses SyncTask because bcrypt is CPU-bound and doesn't require I/O.
    For async context, wrap with anyio.to_thread.run_sync().
    
    Example:
        task = HashPasswordTask()
        # Sync call:
        password_hash = task.run("user_password")
        # Async call (recommended for web handlers):
        password_hash = await anyio.to_thread.run_sync(task.run, "user_password")
    """
    
    def __init__(self) -> None:
        """Initialize task with settings."""
        settings = get_settings()
        self.rounds = settings.bcrypt_rounds
    
    def run(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=self.rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
```

### Реальный пример: VerifyPasswordTask

```python
# src/Containers/AppSection/UserModule/Tasks/VerifyPasswordTask.py
import bcrypt
from pydantic import BaseModel

from src.Ship.Parents.Task import SyncTask


class VerifyPasswordInput(BaseModel):
    """Input for password verification.
    
    Uses frozen Pydantic model for immutability.
    """
    model_config = {"frozen": True}
    
    password: str
    password_hash: str


class VerifyPasswordTask(SyncTask[VerifyPasswordInput, bool]):
    """Verify password against bcrypt hash.
    
    Returns True if password matches, False otherwise.
    Never raises exceptions — returns False on error.
    
    Example:
        task = VerifyPasswordTask()
        is_valid = task.run(VerifyPasswordInput(
            password="password",
            password_hash=stored_hash,
        ))
    """
    
    def run(self, data: VerifyPasswordInput) -> bool:
        try:
            return bcrypt.checkpw(
                data.password.encode("utf-8"),
                data.password_hash.encode("utf-8"),
            )
        except Exception:
            return False
```

### Реальный пример: GenerateTokenTask

```python
# src/Containers/AppSection/UserModule/Tasks/GenerateTokenTask.py
from uuid import UUID
from pydantic import BaseModel

from src.Ship.Parents.Task import SyncTask
from src.Ship.Auth.JWT import JWTService


class TokenPair(BaseModel):
    """Pair of access and refresh tokens."""
    model_config = {"frozen": True}
    
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 86400  # 24 hours in seconds


class GenerateTokenInput(BaseModel):
    """Input for token generation."""
    model_config = {"frozen": True}
    
    user_id: UUID
    email: str


class GenerateTokenTask(SyncTask[GenerateTokenInput, TokenPair]):
    """Synchronous task for generating JWT token pairs.
    
    Uses SyncTask because JWTService is CPU-bound and doesn't require I/O.
    
    Example:
        jwt_service = JWTService()
        task = GenerateTokenTask(jwt_service)
        tokens = task.run(GenerateTokenInput(
            user_id=user.id,
            email=user.email,
        ))
    """
    
    def __init__(self, jwt_service: JWTService) -> None:
        """Initialize task with JWT service (injected via DI)."""
        self.jwt_service = jwt_service
    
    def run(self, data: GenerateTokenInput) -> TokenPair:
        """Generate access and refresh tokens."""
        access_token = self.jwt_service.create_access_token(
            user_id=data.user_id,
            email=data.email,
        )
        
        refresh_token = self.jwt_service.create_refresh_token(
            user_id=data.user_id,
            email=data.email,
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_service.expiration_hours * 3600,
        )
```

### Реальный пример: SendWelcomeEmailTask (Async Task)

```python
# src/Containers/AppSection/UserModule/Tasks/SendWelcomeEmailTask.py
import logfire
from pydantic import BaseModel

from src.Ship.Parents.Task import Task


class WelcomeEmailData(BaseModel):
    """Input for welcome email."""
    model_config = {"frozen": True}
    
    email: str
    name: str


class SendWelcomeEmailTask(Task[WelcomeEmailData, bool]):
    """Async task for sending welcome emails.
    
    Uses Task (async) because email sending is I/O-bound.
    
    Example:
        task = SendWelcomeEmailTask()
        success = await task.run(WelcomeEmailData(
            email="user@example.com",
            name="John",
        ))
    """
    
    async def run(self, data: WelcomeEmailData) -> bool:
        """Send welcome email to new user."""
        logfire.info(
            "📧 Sending welcome email",
            email=data.email,
            name=data.name,
        )
        # TODO: Integrate with email service
        return True
```

---

## 📖 Query (CQRS Read)

**Назначение:** Оптимизированные read-операции. Обходят UoW для производительности.

### Принципы:

1. **Read-only** — только чтение данных
2. **Bypass UoW** — прямой доступ к ORM
3. **Возвращает plain values** — не Result (Query не может fail)
4. **Оптимизация** — специализированные запросы
5. **Pydantic Input** — используйте frozen Pydantic модели для параметров
6. **dataclass Output** — используйте dataclass для сложных выходных данных

### Базовые классы

```python
# src/Ship/Parents/Query.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class Query(ABC, Generic[InputT, OutputT]):
    """Base Query class for CQRS read operations.
    
    Rules:
    - One Query = one read operation (Single Responsibility)
    - Read-only — does NOT modify state
    - Bypasses UnitOfWork for better performance
    - Can be called from Controller directly
    - Returns plain value T (not Result)
    
    Example:
        class GetUserQuery(Query[UUID, AppUser | None]):
            async def execute(self, user_id: UUID) -> AppUser | None:
                return await AppUser.objects().where(
                    AppUser.id == user_id
                ).first()
    """
    
    @abstractmethod
    async def execute(self, data: InputT) -> OutputT:
        """Execute the query."""
        ...


class SyncQuery(ABC, Generic[InputT, OutputT]):
    """Synchronous Query class.
    
    For read operations that don't require I/O:
    - In-memory lookups
    - Cached data retrieval
    - Configuration reads
    """
    
    @abstractmethod
    def execute(self, data: InputT) -> OutputT:
        """Execute the synchronous query."""
        ...
```

### Реальный пример: GetUserQuery

```python
# src/Containers/AppSection/UserModule/Queries/GetUserQuery.py
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class GetUserQueryInput(BaseModel):
    """Input parameters for GetUserQuery.
    
    Uses frozen Pydantic model for immutability.
    """
    model_config = ConfigDict(frozen=True)
    
    user_id: UUID


class GetUserQuery(Query[GetUserQueryInput, AppUser | None]):
    """CQRS Query: Get user by ID.
    
    Read-only operation optimized for data retrieval.
    Does not go through UnitOfWork for better performance.
    
    Example:
        query = GetUserQuery()
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        if user:
            return UserResponse.from_entity(user)
    """
    
    async def execute(self, input: GetUserQueryInput) -> AppUser | None:
        """Execute query to get user by ID.
        
        Returns:
            User or None if not found
        """
        return await AppUser.objects().where(AppUser.id == input.user_id).first()
```

### Реальный пример: ListUsersQuery

```python
# src/Containers/AppSection/UserModule/Queries/ListUsersQuery.py
from dataclasses import dataclass
from pydantic import BaseModel, Field, ConfigDict

from src.Ship.Parents.Query import Query
from src.Containers.AppSection.UserModule.Models.User import AppUser


class ListUsersQueryInput(BaseModel):
    """Input parameters for ListUsersQuery.
    
    Uses Pydantic for consistency with other DTOs.
    Field validators ensure valid pagination values.
    """
    model_config = ConfigDict(frozen=True)
    
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    active_only: bool = False


@dataclass(frozen=True)
class ListUsersQueryOutput:
    """Output of ListUsersQuery.
    
    Uses dataclass instead of Pydantic to avoid arbitrary_types_allowed
    for ORM models. ORM models are handled at Query layer, not serialized to JSON.
    """
    users: list[AppUser]
    total: int
    limit: int
    offset: int


class ListUsersQuery(Query[ListUsersQueryInput, ListUsersQueryOutput]):
    """CQRS Query: List users with pagination.
    
    Read-only operation optimized for data retrieval.
    Does not go through UnitOfWork for better performance.
    
    Example:
        query = ListUsersQuery()
        result = await query.execute(ListUsersQueryInput(limit=10, active_only=True))
        return UserListResponse(users=result.users, total=result.total)
    """
    
    async def execute(self, params: ListUsersQueryInput) -> ListUsersQueryOutput:
        """Execute query to list users."""
        query = AppUser.objects()
        count_query = AppUser.count()
        
        if params.active_only:
            query = query.where(AppUser.is_active == True)
            count_query = count_query.where(AppUser.is_active == True)
        
        total = await count_query
        users = await (
            query
            .limit(params.limit)
            .offset(params.offset)
            .order_by(AppUser.created_at, ascending=False)
        )
        
        return ListUsersQueryOutput(
            users=users,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )
```

---

## 🗄️ Repository

**Назначение:** Абстракция над ORM. Инкапсулирует доступ к данным.

### Принципы:

1. **Один Repository — один Entity**
2. **CRUD + domain queries** — специфичные для entity
3. **Lifecycle hooks** — для кэширования, аудита
4. **Не знает о UoW** — используется внутри UoW
5. **Testability** — легко мокать для тестов

### Базовый класс

```python
# src/Ship/Parents/Repository.py
from abc import ABC
from typing import Generic, TypeVar
from uuid import UUID
from piccolo.table import Table
from piccolo.columns import Column

ModelT = TypeVar("ModelT", bound=Table)


class Repository(ABC, Generic[ModelT]):
    """Base Repository class.
    
    Lightweight wrapper over Piccolo Table API.
    Subclasses should add domain-specific query methods.
    
    Lifecycle hooks:
    - _on_add(entity): Called after entity is added
    - _on_update(entity): Called after entity is updated  
    - _on_delete(entity): Called after entity is deleted
    
    Override hooks in subclasses for cache invalidation, events, etc.
    
    Advantages:
    - Uniform interface — Action doesn't know ORM details
    - Testability — easy to mock repositories
    - Query encapsulation — complex queries in one place
    - Extensible via hooks — no need to override CRUD methods
    """
    
    def __init__(self, model: type[ModelT]) -> None:
        """Initialize repository with model class."""
        self.model = model
    
    # --- Lifecycle hooks (override in subclasses) ---
    
    async def _on_add(self, entity: ModelT) -> None:
        """Hook called after entity is added."""
        pass
    
    async def _on_update(self, entity: ModelT) -> None:
        """Hook called after entity is updated."""
        pass
    
    async def _on_delete(self, entity: ModelT) -> None:
        """Hook called after entity is deleted."""
        pass
    
    # --- Basic CRUD operations ---
    
    async def get(self, id: UUID) -> ModelT | None:
        """Get entity by ID."""
        return await self.model.objects().where(self.model.id == id).first()
    
    async def get_one_or_none(self, **filters: object) -> ModelT | None:
        """Get entity by arbitrary filters."""
        query = self.model.objects()
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        return await query.first()
    
    async def add(self, entity: ModelT) -> ModelT:
        """Add entity and return with generated fields."""
        await entity.save()
        await entity.refresh()
        await self._on_add(entity)
        return entity
    
    async def update(self, entity: ModelT) -> ModelT:
        """Update entity."""
        await entity.save()
        await self._on_update(entity)
        return entity
    
    async def delete(self, entity: ModelT) -> None:
        """Delete entity."""
        await entity.remove()
        await self._on_delete(entity)
    
    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
        order_by: Column | None = None,
        ascending: bool = False,
    ) -> list[ModelT]:
        """List entities with pagination and optional ordering."""
        query = self.model.objects().limit(limit).offset(offset)
        
        if order_by is not None:
            query = query.order_by(order_by, ascending=ascending)
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at, ascending=ascending)
        
        return await query
    
    async def count(self) -> int:
        """Count total entities."""
        return await self.model.count()
    
    async def exists(self, **filters: object) -> bool:
        """Check if entity exists with given filters."""
        query = self.model.exists()
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        return await query
```

### Реальный пример: UserRepository

```python
# src/Containers/AppSection/UserModule/Data/Repositories/UserRepository.py
from datetime import datetime, timezone

from src.Ship.Parents.Repository import Repository
from src.Ship.Decorators.cache_utils import invalidate_cache
from src.Containers.AppSection.UserModule.Models.User import AppUser


class UserRepository(Repository[AppUser]):
    """Repository for AppUser entity.
    
    Extends base Repository with user-specific queries.
    Uses hooks for automatic cache invalidation.
    """
    
    def __init__(self) -> None:
        """Initialize repository with AppUser model."""
        super().__init__(AppUser)
    
    # --- Lifecycle hooks for cache invalidation ---
    
    async def _on_add(self, entity: AppUser) -> None:
        """Invalidate cache after adding user."""
        await invalidate_cache("users:list:*", "users:count")
    
    async def _on_update(self, entity: AppUser) -> None:
        """Invalidate cache after updating user."""
        await invalidate_cache(
            f"user:{entity.id}",
            "user:email:*",
            "users:list:*",
            "users:count",
        )
    
    async def _on_delete(self, entity: AppUser) -> None:
        """Invalidate cache after deleting user."""
        await invalidate_cache(
            f"user:{entity.id}",
            "user:email:*",
            "users:list:*",
            "users:count",
        )
    
    # --- User-specific queries ---
    
    async def find_by_email(self, email: str) -> AppUser | None:
        """Find user by email address."""
        return await AppUser.objects().where(AppUser.email == email).first()
    
    async def find_active(self, limit: int = 20, offset: int = 0) -> list[AppUser]:
        """Find active users with pagination."""
        return await (
            AppUser.objects()
            .where(AppUser.is_active == True)
            .limit(limit)
            .offset(offset)
            .order_by(AppUser.created_at, ascending=False)
        )
    
    async def count_active(self) -> int:
        """Count active users."""
        return await AppUser.count().where(AppUser.is_active == True)
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return (await self.find_by_email(email)) is not None
    
    async def deactivate(self, user: AppUser) -> AppUser:
        """Deactivate user account."""
        user.is_active = False
        return await self.update(user)
    
    # --- Override update for SQLite compatibility ---
    
    async def update(self, user: AppUser) -> AppUser:
        """Update user with SQLite-compatible timestamp handling.
        
        Uses raw UPDATE to avoid SQLite TimestamptzNow issues.
        This is a known SQLite limitation with Piccolo ORM.
        """
        await AppUser.update({
            AppUser.email: user.email,
            AppUser.password_hash: user.password_hash,
            AppUser.name: user.name,
            AppUser.is_active: user.is_active,
            AppUser.updated_at: datetime.now(timezone.utc),
        }).where(AppUser.id == user.id)
        
        # Refresh to get updated timestamp
        updated = await AppUser.objects().where(AppUser.id == user.id).first()
        if updated:
            user.updated_at = updated.updated_at
        
        # Call hook for cache invalidation
        await self._on_update(user)
        return user
```

---

## 🔄 UnitOfWork

**Назначение:** Транзакционная граница + сбор Domain Events.

### Принципы:

1. **Транзакционность** — все операции или ничего
2. **Event collection** — события публикуются после commit
3. **Repository aggregation** — доступ к repositories через UoW
4. **Litestar Events integration** — события публикуются через `app.emit()`
5. **Context-aware** — разные провайдеры для HTTP и CLI контекстов

### Базовый класс

```python
# src/Ship/Parents/UnitOfWork.py
from dataclasses import dataclass, field
from typing import TypeVar, TYPE_CHECKING, Any, Callable, Coroutine

from piccolo.engine import engine_finder

if TYPE_CHECKING:
    from piccolo.engine.sqlite import SQLiteEngine
    from piccolo.engine.postgres import PostgresEngine
    from litestar import Litestar
    from src.Ship.Parents.Event import DomainEvent

Self = TypeVar("Self", bound="BaseUnitOfWork")

# Type alias for event emitter function
EventEmitterFunc = Callable[[str, Any], None] | None


@dataclass
class BaseUnitOfWork:
    """Unit of Work pattern implementation.
    
    Features:
    - Database transaction management via Piccolo
    - Domain event collection and publishing
    - Context manager interface
    
    Events are published AFTER successful commit via litestar.events.
    This ensures events are only sent for committed transactions.
    
    Example:
        @dataclass
        class UserUnitOfWork(BaseUnitOfWork):
            users: UserRepository = field(default_factory=UserRepository)
            
        # Usage in Action:
        async with self.uow:
            user = User(email=data.email, ...)
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id))
            await self.uow.commit()
    """
    
    # Event emitter function from Litestar (injected via DI)
    _emit: EventEmitterFunc = field(default=None, repr=False)
    
    # Litestar app instance for passing to event listeners
    _app: "Litestar | None" = field(default=None, repr=False)
    
    # Internal state
    _events: list["DomainEvent"] = field(default_factory=list, init=False, repr=False)
    _committed: bool = field(default=False, init=False, repr=False)
    _transaction: object | None = field(default=None, init=False, repr=False)
    
    def _get_engine(self) -> "SQLiteEngine | PostgresEngine":
        """Get database engine from Piccolo configuration."""
        engine = engine_finder()
        if engine is None:
            raise RuntimeError("No Piccolo engine configured. Check piccolo_conf.py")
        return engine
    
    async def __aenter__(self: Self) -> Self:
        """Enter transaction context."""
        self._committed = False
        engine = self._get_engine()
        self._transaction = engine.transaction()
        await self._transaction.__aenter__()
        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit transaction context (rollback on exception if not committed)."""
        if self._transaction is not None:
            if exc_type and not self._committed:
                await self.rollback()
            await self._transaction.__aexit__(exc_type, exc_val, exc_tb)
            self._transaction = None
    
    def add_event(self, event: "DomainEvent") -> None:
        """Add domain event for publishing after commit."""
        self._events.append(event)
    
    async def commit(self) -> None:
        """Commit transaction and publish events.
        
        Events are published AFTER successful commit via litestar.events.
        If no emitter is available (e.g., in CLI context), events are logged.
        """
        self._committed = True
        
        # Publish events via litestar.events emitter
        if self._emit is not None:
            for event in self._events:
                # Emit event with app instance and all event data as kwargs
                self._emit(event.event_name, app=self._app, **event.model_dump(mode="json"))
        else:
            # Log events when no emitter is available (CLI, tests, etc.)
            import logfire
            for event in self._events:
                logfire.info(
                    f"📤 Event (no emitter): {event.event_name}",
                    event_name=event.event_name,
                    event_data=event.model_dump(mode="json"),
                )
        
        self._events.clear()
    
    async def rollback(self) -> None:
        """Rollback transaction and clear events."""
        self._events.clear()
        self._committed = False
    
    @property
    def events(self) -> list["DomainEvent"]:
        """Get pending events."""
        return self._events.copy()
    
    async def execute_with_event(
        self: Self,
        operation: Coroutine[Any, Any, Any],
        event: "DomainEvent",
    ) -> None:
        """Execute operation within transaction and publish event after commit.
        
        Reduces boilerplate for common pattern:
            async with self.uow:
                await operation
                self.uow.add_event(event)
                await self.uow.commit()
        
        Example:
            await self.uow.execute_with_event(
                self.uow.users.add(user),
                UserCreated(user_id=user.id, email=user.email),
            )
        """
        async with self:
            await operation
            self.add_event(event)
            await self.commit()
```

### Реальный пример: UserUnitOfWork

```python
# src/Containers/AppSection/UserModule/Data/UnitOfWork.py
from dataclasses import dataclass, field

from src.Ship.Parents.UnitOfWork import BaseUnitOfWork, EventEmitterFunc
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository


@dataclass
class UserUnitOfWork(BaseUnitOfWork):
    """Unit of Work for UserModule.
    
    Provides transactional access to user-related repositories.
    Inherits event management from BaseUnitOfWork.
    
    The _emit parameter is inherited from BaseUnitOfWork and injected via DI.
    
    Example:
        async with uow:
            user = User(email=data.email, ...)
            await uow.users.add(user)
            uow.add_event(UserCreated(user_id=user.id))
            await uow.commit()  # Events published here
    """
    
    # Repositories - initialized with default_factory for proper per-instance creation
    users: UserRepository = field(default_factory=UserRepository)
```

### DI провайдеры для UnitOfWork

```python
# src/Containers/AppSection/UserModule/Providers.py (фрагмент)
from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork


class UserRequestProvider(Provider):
    """HTTP request-scoped provider for UserModule."""
    
    scope = Scope.REQUEST
    
    @provide
    def provide_user_uow(self, request: Request) -> UserUnitOfWork:
        """Provide UserUnitOfWork with event emitter from request."""
        return UserUnitOfWork(_emit=request.app.emit, _app=request.app)


class UserCLIProvider(Provider):
    """CLI-specific provider for UserModule."""
    
    scope = Scope.REQUEST
    
    @provide
    def provide_user_uow(self) -> UserUnitOfWork:
        """Provide UserUnitOfWork without event emitter for CLI."""
        return UserUnitOfWork(_emit=None, _app=None)
```

### Transactional Outbox

BaseUnitOfWork поддерживает Transactional Outbox pattern для гарантированной доставки событий:

```python
# Отслеживание агрегата
self.uow.set_aggregate_info("User", str(user.id))

# События сохраняются в outbox таблицу при commit
self.uow.add_event(UserCreated(user_id=user.id))
await self.uow.commit()
```

Методы:
- `set_aggregate_info(type, id)` — привязка событий к агрегату
- `_is_outbox_enabled()` — проверка включён ли Outbox
- `_save_events_to_outbox()` — сохранение событий в таблицу

См. также: `docs/17-unified-event-bus.md`

---

## 🌉 Gateway (Module Gateway Pattern)

**Назначение:** Абстракция для межмодульного взаимодействия. Позволяет модулям общаться без прямых импортов.

### Принципы:

1. **Ports & Adapters** — Gateway = Port (интерфейс), Adapter = реализация
2. **Consumer defines contract** — потребитель определяет, что ему нужно
3. **Transport-agnostic** — бизнес-логика не знает о способе доставки
4. **Swappable adapters** — смена адаптера = смена deployment mode
5. **Result[T, E]** — все методы возвращают Result

### Когда использовать Gateway vs Events

| Сценарий | Используй |
|----------|-----------|
| Fire-and-forget (уведомления) | **Events** |
| Нужен ответ (проверка статуса) | **Gateway** |
| Async workflow | **Events** |
| Sync операция с результатом | **Gateway** |

### Базовый протокол

```python
# src/Ship/Parents/Gateway.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class GatewayProtocol(Protocol):
    """Base protocol marker for all gateways.
    
    All gateway protocols should be runtime_checkable to allow
    isinstance() checks for debugging and validation.
    """
    pass
```

### Базовый класс Gateway

```python
from abc import ABC
from typing import Generic, TypeVar
from returns.result import Result

RequestT = TypeVar("RequestT", contravariant=True)
ResponseT = TypeVar("ResponseT", covariant=True)
ErrorT = TypeVar("ErrorT", covariant=True)


class BaseGateway(ABC, Generic[RequestT, ResponseT, ErrorT]):
    """Abstract base class for gateway implementations.
    
    Provides hooks for logging, metrics, error mapping.
    """
    
    async def _pre_call(self, method: str, request: RequestT) -> None:
        """Hook before gateway operation (logging, metrics)."""
        pass
    
    async def _post_call(
        self,
        method: str,
        request: RequestT,
        result: Result[ResponseT, ErrorT],
    ) -> None:
        """Hook after gateway operation."""
        pass
    
    async def _on_error(self, method: str, request: RequestT, error: Exception) -> ErrorT:
        """Map transport errors to domain errors."""
        raise error
```

### Адаптеры

| Адаптер | Deployment | Описание |
|---------|------------|----------|
| **DirectAdapterBase** | Монолит | Прямые вызовы Actions |
| **HttpAdapterBase** | Микросервисы | HTTP вызовы через httpx |
| **GrpcAdapterBase** | High-performance | gRPC (placeholder) |

### Реальный пример: PaymentGateway

#### 1. Определение Gateway Protocol (в OrderModule — потребитель)

```python
# src/Containers/AppSection/OrderModule/Gateways/PaymentGateway.py
from typing import Protocol
from returns.result import Result
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal


class CreatePaymentRequest(BaseModel):
    """Request DTO для создания платежа."""
    model_config = {"frozen": True}
    
    user_id: UUID
    order_id: UUID
    amount: Decimal
    currency: str = "RUB"


class PaymentResult(BaseModel):
    """Response DTO с результатом платежа."""
    model_config = {"frozen": True}
    
    payment_id: UUID
    status: str  # "pending", "completed", "failed"
    transaction_id: str | None = None


class PaymentError(BaseModel):
    """Ошибки платежного шлюза."""
    model_config = {"frozen": True}
    
    message: str
    code: str = "PAYMENT_ERROR"


class PaymentGateway(Protocol):
    """Gateway для взаимодействия с PaymentModule."""
    
    async def create_payment(
        self, request: CreatePaymentRequest
    ) -> Result[PaymentResult, PaymentError]:
        """Создать платёж."""
        ...
    
    async def check_status(self, payment_id: UUID) -> Result[PaymentResult, PaymentError]:
        """Проверить статус платежа."""
        ...
```

#### 2. DirectAdapter (для монолита)

```python
# src/Containers/AppSection/OrderModule/Gateways/Adapters/DirectPaymentAdapter.py
from dataclasses import dataclass
from returns.result import Result, Success, Failure

from src.Ship.Parents.Gateway import DirectAdapterBase
from src.Containers.AppSection.PaymentModule.Actions.CreatePaymentAction import (
    CreatePaymentAction,
)
from src.Containers.AppSection.PaymentModule.Data.Schemas.Requests import (
    CreatePaymentRequest as ProviderRequest,
)
from ..PaymentGateway import (
    CreatePaymentRequest,
    PaymentResult,
    PaymentError,
    PaymentGateway,
)


@dataclass
class DirectPaymentAdapter(DirectAdapterBase[CreatePaymentRequest, PaymentResult, PaymentError]):
    """Direct adapter — вызывает PaymentModule Actions напрямую."""
    
    create_payment_action: CreatePaymentAction
    
    async def create_payment(
        self, request: CreatePaymentRequest
    ) -> Result[PaymentResult, PaymentError]:
        # Map consumer DTO → provider DTO
        provider_request = ProviderRequest(
            user_id=request.user_id,
            order_id=request.order_id,
            amount=request.amount,
            currency=request.currency,
        )
        
        # Call provider Action
        result = await self.create_payment_action.run(provider_request)
        
        # Map provider result → consumer DTO
        return result.map(
            lambda p: PaymentResult(
                payment_id=p.id,
                status=p.status,
                transaction_id=p.transaction_id,
            )
        ).map_failure(
            lambda e: PaymentError(message=e.message, code=e.code)
        )
```

#### 3. HttpAdapter (для микросервисов)

```python
# src/Containers/AppSection/OrderModule/Gateways/Adapters/HttpPaymentAdapter.py
from dataclasses import dataclass
import httpx
from returns.result import Result, Success, Failure

from src.Ship.Parents.Gateway import HttpAdapterBase
from ..PaymentGateway import (
    CreatePaymentRequest,
    PaymentResult,
    PaymentError,
)


@dataclass
class HttpPaymentAdapter(HttpAdapterBase[CreatePaymentRequest, PaymentResult, PaymentError]):
    """HTTP adapter — вызывает Payment Service через HTTP."""
    
    base_url: str
    client: httpx.AsyncClient
    
    def _get_base_url(self) -> str:
        return self.base_url
    
    async def create_payment(
        self, request: CreatePaymentRequest
    ) -> Result[PaymentResult, PaymentError]:
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/payments",
                json=request.model_dump(mode="json"),
                headers=self._get_default_headers(),
                timeout=self._get_timeout(),
            )
            response.raise_for_status()
            return Success(PaymentResult.model_validate(response.json()))
        except httpx.HTTPStatusError as e:
            error_data = e.response.json()
            return Failure(PaymentError(
                message=error_data.get("message", str(e)),
                code=error_data.get("code", "HTTP_ERROR"),
            ))
        except httpx.RequestError as e:
            return Failure(PaymentError(
                message=f"Connection error: {e}",
                code="CONNECTION_ERROR",
            ))
```

#### 4. DI регистрация (выбор адаптера)

```python
# src/Containers/AppSection/OrderModule/Providers.py
from dishka import Provider, Scope, provide
import httpx

from src.Ship.Configs import Settings
from .Gateways.PaymentGateway import PaymentGateway
from .Gateways.Adapters.DirectPaymentAdapter import DirectPaymentAdapter
from .Gateways.Adapters.HttpPaymentAdapter import HttpPaymentAdapter


class OrderGatewayProvider(Provider):
    """Provider для Gateway зависимостей."""
    
    scope = Scope.REQUEST
    
    @provide
    async def payment_gateway(
        self,
        settings: Settings,
        # DirectAdapter dependencies (only for monolith)
        create_payment_action: CreatePaymentAction | None = None,
    ) -> PaymentGateway:
        """Provide PaymentGateway based on deployment mode."""
        if settings.deployment_mode == "microservices":
            async with httpx.AsyncClient() as client:
                return HttpPaymentAdapter(
                    base_url=settings.payment_service_url,
                    client=client,
                )
        
        # Monolith mode — direct calls
        assert create_payment_action is not None
        return DirectPaymentAdapter(
            create_payment_action=create_payment_action,
        )
```

#### 5. Использование в Action

```python
# src/Containers/AppSection/OrderModule/Actions/CreateOrderAction.py
from dataclasses import dataclass
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from ..Gateways.PaymentGateway import PaymentGateway, CreatePaymentRequest
from ..Errors import OrderError, OrderPaymentFailedError


@dataclass
class CreateOrderAction(Action[CreateOrderInput, Order, OrderError]):
    """Use Case: Create order with payment."""
    
    payment_gateway: PaymentGateway  # Injected — не знает о реализации
    uow: OrderUnitOfWork
    
    async def run(self, data: CreateOrderInput) -> Result[Order, OrderError]:
        # Create order
        order = Order(user_id=data.user_id, items=data.items)
        
        # Call payment gateway
        payment_result = await self.payment_gateway.create_payment(
            CreatePaymentRequest(
                user_id=data.user_id,
                order_id=order.id,
                amount=order.total,
            )
        )
        
        # Handle result
        match payment_result:
            case Success(payment):
                order.payment_id = payment.payment_id
                order.status = "paid"
            case Failure(error):
                return Failure(OrderPaymentFailedError(
                    order_id=order.id,
                    reason=error.message,
                ))
        
        # Save order
        async with self.uow:
            await self.uow.orders.add(order)
            await self.uow.commit()
        
        return Success(order)
```

### Структура папок Gateway

```
OrderModule/
├── Gateways/
│   ├── __init__.py
│   ├── PaymentGateway.py      # Protocol + DTOs
│   └── Adapters/
│       ├── __init__.py
│       ├── DirectPaymentAdapter.py
│       └── HttpPaymentAdapter.py
```

### Best Practices

1. **Consumer defines contract** — Gateway Protocol и DTOs определяются в модуле-потребителе
2. **DTO mapping** — адаптеры маппят между consumer и provider DTOs
3. **Error mapping** — транспортные ошибки маппятся в domain errors
4. **Timeout & Retry** — HttpAdapter должен использовать timeout и tenacity для retry
5. **Circuit Breaker** — для microservices используйте circuit breaker pattern

> 📚 **См. также:** `docs/14-module-gateway-pattern.md` — полное руководство по Gateway Pattern

---

## 🏷️ Model (Piccolo Table)

**Назначение:** ORM entity. Определяет структуру таблицы.

### Принципы:

1. **Наследование от Model** — базовый класс из Ship
2. **Именование** — избегайте зарезервированных слов SQL (`User` → `AppUser`)
3. **UUID primary key** — используйте UUID4 вместо автоинкремента
4. **Timestamps** — `created_at` и `updated_at` для аудита

### Базовый класс

```python
# src/Ship/Parents/Model.py
from piccolo.table import Table


class Model(Table):
    """Base Model class.
    
    All models should inherit from this class.
    It provides common functionality for all models.
    
    Example:
        class User(Model):
            id = UUID(primary_key=True, default=UUID4())
            email = Varchar(length=255, unique=True)
            name = Varchar(length=100)
    """
    
    class Meta:
        """Piccolo meta configuration."""
        abstract = True
```

### Реальный пример: AppUser

```python
# src/Containers/AppSection/UserModule/Models/User.py
from piccolo.columns import UUID, Varchar, Boolean, Timestamptz
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.defaults.timestamptz import TimestamptzNow

from src.Ship.Parents.Model import Model


class AppUser(Model):
    """User entity.
    
    Represents a user in the system with authentication data.
    Named AppUser to avoid SQL reserved word 'user'.
    
    Attributes:
        id: Unique identifier (UUID)
        email: User's email address (unique, indexed)
        password_hash: Hashed password
        name: User's display name
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    
    id = UUID(primary_key=True, default=UUID4())
    email = Varchar(length=255, unique=True, required=True, index=True)
    password_hash = Varchar(length=255, required=True)
    name = Varchar(length=100, required=True)
    is_active = Boolean(default=True)
    created_at = Timestamptz(default=TimestamptzNow())
    # Note: auto_update removed due to SQLite incompatibility with TimestamptzNow
    # updated_at is set manually in repository.update()
    updated_at = Timestamptz(default=TimestamptzNow())
    
    class Meta:
        """Piccolo meta configuration."""
        tablename = "app_users"


# Alias for backward compatibility
User = AppUser
```

---

## 📢 Event (Domain Event)

**Назначение:** Уведомление о произошедшем в домене. Используется для слабой связанности между модулями.

### Принципы:

1. **Immutable** — события неизменяемы (frozen)
2. **Past tense** — называйте как прошедшее событие (`UserCreated`, `OrderPlaced`)
3. **Published after commit** — публикуются только после успешного commit
4. **Litestar Events integration** — обрабатываются через `@listener` декоратор

### Базовый класс

```python
# src/Ship/Parents/Event.py
from datetime import datetime, timezone
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class DomainEvent(BaseModel):
    """Base class for domain events.
    
    Events are immutable (frozen) Pydantic models.
    Published after successful UnitOfWork commit via litestar.events.
    
    Rules:
    - Immutable (frozen=True)
    - Named as past tense verb (e.g., UserCreated, OrderPlaced)
    - Contains only data needed by listeners
    - Published AFTER successful transaction commit
    
    Example:
        class UserCreated(DomainEvent):
            user_id: UUID
            email: str
            
        # Usage in Action:
        async with self.uow:
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
            await self.uow.commit()  # Event published here
    """
    
    model_config = {"frozen": True}
    
    # Timestamp when event occurred (auto-generated, timezone-aware UTC)
    occurred_at: datetime = Field(default_factory=_utc_now)
    
    @property
    def event_name(self) -> str:
        """Get event name from class name."""
        return self.__class__.__name__
```

### Реальные примеры

```python
# src/Containers/AppSection/UserModule/Events.py
from uuid import UUID
from pydantic import Field
from src.Ship.Parents.Event import DomainEvent


class UserCreated(DomainEvent):
    """Event raised when a new user is created."""
    user_id: UUID
    email: str


class UserUpdated(DomainEvent):
    """Event raised when a user is updated."""
    user_id: UUID
    updated_fields: list[str] = Field(default_factory=list)


class UserDeleted(DomainEvent):
    """Event raised when a user is deleted."""
    user_id: UUID
    email: str


# Export all events
__all__ = ["UserCreated", "UserUpdated", "UserDeleted"]
```

---

## 📝 Schema (Pydantic DTO)

**Назначение:** Data Transfer Objects для валидации и сериализации.

### Принципы:

1. **Request DTOs** — используют `BaseModel` с валидаторами
2. **Response DTOs** — наследуют `EntitySchema` для автоматического преобразования из ORM
3. **Frozen для внутренних** — используйте `frozen=True` для immutability
4. **No dataclass** — всегда Pydantic, не dataclass

### Базовый класс для Response DTO

```python
# src/Ship/Core/BaseSchema.py
from typing import TypeVar, Type
from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="EntitySchema")


class EntitySchema(BaseModel):
    """Base class for Response DTOs with automatic conversion from Entity.
    
    Uses Pydantic V2 from_attributes for automatic mapping from ORM objects.
    
    Example:
        class UserResponse(EntitySchema):
            id: UUID
            email: str
            name: str
            is_active: bool
            # from_entity is already available from base class!
            
        # Usage:
        user_response = UserResponse.from_entity(user)
        
        # Для списков:
        # Способ 1: list comprehension
        responses = [UserResponse.from_entity(u) for u in users]
        
        # Способ 2: from_entities (рекомендуется)
        responses = UserResponse.from_entities(users)
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )
    
    @classmethod
    def from_entity(cls: Type[T], entity: object) -> T:
        """Create DTO from Entity (ORM model)."""
        return cls.model_validate(entity)
```

### Request DTOs

```python
# src/Containers/AppSection/UserModule/Data/Schemas/Requests.py
from pydantic import BaseModel, EmailStr, Field, field_validator


class CreateUserRequest(BaseModel):
    """Request DTO for creating a new user."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    name: str = Field(..., min_length=2, max_length=100, description="Display name")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UpdateUserRequest(BaseModel):
    """Request DTO for updating a user.
    
    All fields are optional - only provided fields will be updated.
    """
    name: str | None = Field(None, min_length=2, max_length=100)
    is_active: bool | None = None


class ChangePasswordRequest(BaseModel):
    """Request DTO for changing user password."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Request DTO for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    """Request DTO for token refresh."""
    model_config = {"frozen": True}
    
    refresh_token: str = Field(..., min_length=1)
```

### Response DTOs

```python
# src/Containers/AppSection/UserModule/Data/Schemas/Responses.py
from datetime import datetime
from uuid import UUID
from pydantic import ConfigDict
from src.Ship.Core.BaseSchema import EntitySchema
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import TokenPair


class UserResponse(EntitySchema):
    """Response DTO for User entity.
    
    Inherits from_entity() from EntitySchema for automatic conversion.
    Note: password_hash is excluded by not being in the schema.
    """
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(EntitySchema):
    """Response DTO for list of users."""
    users: list[UserResponse]
    total: int
    limit: int
    offset: int


class TokenRefreshResponse(TokenPair):
    """Response DTO for token refresh.
    
    Inherits directly from TokenPair - no field duplication.
    """
    @classmethod
    def from_entity(cls, token_pair: TokenPair) -> "TokenRefreshResponse":
        """Create from TokenPair."""
        return cls.model_validate(token_pair, from_attributes=True)


class AuthResponse(EntitySchema):
    """Response DTO for authentication result.
    
    Flattens TokenPair fields for API compatibility.
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Token fields (flattened from TokenPair)
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    
    # User fields
    user_id: str
    email: str
    
    @classmethod
    def from_entity(cls, auth_result) -> "AuthResponse":
        """Create from AuthResult object (called by result_handler decorator)."""
        return cls(
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            token_type=auth_result.tokens.token_type,
            expires_in=auth_result.tokens.expires_in,
            user_id=auth_result.user_id,
            email=auth_result.email,
        )
```

---

## ⚠️ Error (Domain Error)

**Назначение:** Типизированные ошибки домена с HTTP-маппингом.

### Принципы:

1. **Pydantic frozen models** — ошибки неизменяемы
2. **Explicit http_status** — каждая ошибка знает свой HTTP код
3. **ErrorWithTemplate** — автогенерация сообщений
4. **DomainException** — обёртка для raise
5. **Problem Details (RFC 9457)** — стандартизированные ответы

### Базовые классы

```python
# src/Ship/Core/Errors.py
from typing import Any, ClassVar
from uuid import UUID
from pydantic import BaseModel, model_validator


class BaseError(BaseModel):
    """Base error class for all domain errors.
    
    All errors should inherit from this class.
    Errors are frozen (immutable) Pydantic models.
    
    For raising as exceptions, use DomainException wrapper.
    
    Example:
        class UserError(BaseError):
            code: str = "USER_ERROR"
            
        class UserNotFoundError(UserError):
            code: str = "USER_NOT_FOUND"
            http_status: int = 404
            user_id: UUID
    """
    
    model_config = {"frozen": True}
    
    message: str
    code: str = "ERROR"
    http_status: int = 400  # Default to Bad Request
    
    def __str__(self) -> str:
        return self.message


class ErrorWithTemplate(BaseError):
    """Base error with automatic message generation from template.
    
    Reduces boilerplate for errors that need dynamic messages.
    Uses model_validator for auto-generation before instance creation.
    
    Example:
        class UserNotFoundError(ErrorWithTemplate):
            _message_template: ClassVar[str] = "User with id {user_id} not found"
            code: str = "USER_NOT_FOUND"
            http_status: int = 404
            user_id: UUID
            
        # Usage:
        error = UserNotFoundError(user_id=some_uuid)
        # error.message == "User with id <uuid> not found"
    """
    
    _message_template: ClassVar[str] = ""
    
    @model_validator(mode="before")
    @classmethod
    def auto_generate_message(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Auto-generate message from template if not provided."""
        if isinstance(data, dict) and "message" not in data and cls._message_template:
            try:
                data["message"] = cls._message_template.format(**data)
            except KeyError:
                data["message"] = cls._message_template
        return data


class DomainException(Exception):
    """Exception wrapper for domain errors.
    
    Wraps BaseError so it can be raised as exception.
    ProblemDetailsPlugin catches this and converts to RFC 9457 response.
    
    Example:
        error = UserNotFoundError(user_id=uuid)
        raise DomainException(error)
    """
    
    def __init__(self, error: BaseError) -> None:
        self.error = error
        super().__init__(error.message)


# Common reusable errors
class NotFoundError(BaseError):
    """Error raised when entity is not found."""
    code: str = "NOT_FOUND"
    http_status: int = 404
    entity_type: str
    entity_id: UUID | str | int


class ValidationError(BaseError):
    """Error raised when validation fails."""
    code: str = "VALIDATION_ERROR"
    http_status: int = 422
    field: str | None = None
    details: dict[str, Any] | None = None


class UnauthorizedError(BaseError):
    """Error raised when user is not authenticated."""
    code: str = "UNAUTHORIZED"
    http_status: int = 401
    message: str = "Authentication required"


class ForbiddenError(BaseError):
    """Error raised when user doesn't have permission."""
    code: str = "FORBIDDEN"
    http_status: int = 403
    message: str = "Permission denied"
```

### Реальные примеры

```python
# src/Containers/AppSection/UserModule/Errors.py
from typing import ClassVar
from uuid import UUID
from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class UserError(BaseError):
    """Base error for UserModule."""
    code: str = "USER_ERROR"


class UserNotFoundError(ErrorWithTemplate, UserError):
    """Error raised when user is not found."""
    _message_template: ClassVar[str] = "User with id {user_id} not found"
    code: str = "USER_NOT_FOUND"
    http_status: int = 404
    user_id: UUID


class UserAlreadyExistsError(ErrorWithTemplate, UserError):
    """Error raised when user with email already exists."""
    _message_template: ClassVar[str] = "User with email {email} already exists"
    code: str = "USER_ALREADY_EXISTS"
    http_status: int = 409
    email: str


class InvalidCredentialsError(UserError):
    """Error raised when credentials are invalid."""
    code: str = "INVALID_CREDENTIALS"
    http_status: int = 401
    message: str = "Invalid email or password"


class UserInactiveError(ErrorWithTemplate, UserError):
    """Error raised when user account is inactive."""
    _message_template: ClassVar[str] = "User account {user_id} is inactive"
    code: str = "USER_INACTIVE"
    http_status: int = 403
    user_id: UUID
```

---

## 🎯 @audited — Декоратор аудита

**Назначение:** Автоматическое логирование и аудит выполнения Actions.

### Принципы:

1. **Декоратор класса** — применяется к Action классам
2. **Event-driven** — публикует `ActionExecuted` события
3. **Redaction** — автоматически скрывает чувствительные данные (passwords, tokens)
4. **Loose coupling** — живёт в Ship, не зависит от AuditModule

### Использование

```python
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py
from src.Ship.Decorators.audited import audited

@audited(action="create", entity_type="User")
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Use Case: Create a new user.
    
    @audited automatically:
    - Logs action start/end with timing
    - Publishes ActionExecuted event
    - Redacts sensitive fields (password, token, etc.)
    - Captures actor info if available
    """
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # ... action logic ...
        return Success(user)
```

### Параметры

```python
@audited(
    action="create",           # Действие (create, update, delete, etc.)
    entity_type="User",        # Тип сущности (опционально)
    capture_input=True,        # Логировать входные данные (default: True)
    capture_output=False,      # Логировать выходные данные (default: False)
)
```

### Что происходит под капотом

1. **Перед выполнением:** Записывает начало, извлекает actor info из `self.current_user`
2. **После выполнения:** Вычисляет duration, статус (success/failure)
3. **Публикация события:** `ActionExecuted` через UoW._emit
4. **Redaction:** Поля `password`, `token`, `secret`, `api_key` заменяются на `***REDACTED***`

### Архитектура

```
@audited (Ship/Decorators)
       │
       ▼ publishes
ActionExecuted event
       │
       ▼ listened by
AuditModule/Listeners.py
       │
       ▼ creates
AuditLog entry in DB
```

---

## 📦 EntitySchema — Response DTO Base Class

**Назначение:** Базовый класс для Response DTOs с автоматической конвертацией из ORM entities.

### Принципы:

1. **from_attributes** — автоматический маппинг из ORM объектов
2. **from_entity()** — единый метод конвертации
3. **Type safety** — сохраняет типизацию при конвертации
4. **No boilerplate** — не нужно писать ручной маппинг

### Базовый класс

```python
# src/Ship/Core/BaseSchema.py
from typing import TypeVar, Type
from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="EntitySchema")


class EntitySchema(BaseModel):
    """Base class for Response DTOs with automatic conversion from Entity.
    
    Uses Pydantic V2 from_attributes for automatic mapping from ORM objects.
    """
    
    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode
        populate_by_name=True,  # Allow field aliases
    )
    
    @classmethod
    def from_entity(cls: Type[T], entity: object) -> T:
        """Create DTO from Entity (ORM model)."""
        return cls.model_validate(entity)
    
    @classmethod
    def from_entities(cls: Type[T], entities: list[object]) -> list[T]:
        """Create list of DTOs from list of Entities."""
        return [cls.model_validate(e) for e in entities]
```

### Использование в Response DTOs

```python
# src/Containers/AppSection/UserModule/Data/Schemas/Responses.py
from datetime import datetime
from uuid import UUID
from src.Ship.Core.BaseSchema import EntitySchema


class UserResponse(EntitySchema):
    """Response DTO for User entity.
    
    Inherits from_entity() from EntitySchema — no manual mapping needed!
    Note: password_hash excluded by not being in schema.
    """
    
    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Использование в Controller
user = await query.execute(GetUserQueryInput(user_id=user_id))
return UserResponse.from_entity(user)  # Автоматическая конвертация!

# Для списков:
# Способ 1: list comprehension
users = result.users
return [UserResponse.from_entity(u) for u in users]

# Способ 2: from_entities (рекомендуется)
return UserResponse.from_entities(result.users)
```

### Кастомизация конвертации

```python
class AuthResponse(EntitySchema):
    """Response with custom from_entity for complex mapping."""
    
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    
    @classmethod
    def from_entity(cls, auth_result) -> "AuthResponse":
        """Custom conversion for flattened token fields."""
        return cls(
            access_token=auth_result.tokens.access_token,
            refresh_token=auth_result.tokens.refresh_token,
            user_id=auth_result.user_id,
            email=auth_result.email,
        )
```

### Сравнение

```python
# ❌ БЕЗ EntitySchema — ручной маппинг
class UserResponse(BaseModel):
    id: UUID
    email: str
    
    @classmethod
    def from_user(cls, user: AppUser) -> "UserResponse":
        return cls(id=user.id, email=user.email)  # Дублирование!


# ✅ С EntitySchema — автоматический маппинг
class UserResponse(EntitySchema):
    id: UUID
    email: str
    # from_entity() уже есть и работает автоматически!
```

---

## 🎮 Controller

**Назначение:** HTTP endpoint. Маршрутизация и преобразование Request/Response.

### Принципы:

1. **CQRS** — Actions для write, Queries для read
2. **@result_handler** — автоматическое преобразование Result → Response
3. **FromDishka** — DI инъекция (без @inject при использовании DishkaRouter)
4. **DomainException** — для ошибок в Query endpoints
5. **Tags** — для группировки в OpenAPI

### Декоратор @result_handler

```python
# src/Ship/Decorators/result_handler.py
from functools import wraps
from typing import TypeVar, Callable, Type, Any
from litestar import Response
from pydantic import BaseModel
from returns.result import Result, Success, Failure
from src.Ship.Core.Errors import BaseError, DomainException


def result_handler(
    response_dto: Type[BaseModel] | None,
    success_status: int = 200,
) -> Callable[[Callable[..., Result]], Callable[..., Any]]:
    """Decorator for automatic Result -> Response conversion.
    
    On Success: returns HTTP response with serialized DTO.
    On Failure: raises DomainException for Problem Details handling.
    
    Example:
        @post("/users")
        @result_handler(UserResponse, success_status=201)
        async def create_user(
            data: CreateUserRequest,
            action: FromDishka[CreateUserAction],
        ) -> Result[User, UserError]:
            return await action.run(data)
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
                    raise Exception(str(error))
        return wrapper
    return decorator
```

### Реальный пример: UserController

```python
# src/Containers/AppSection/UserModule/UI/API/Controllers/UserController.py
from uuid import UUID
from dishka.integrations.litestar import FromDishka
from litestar import Controller, get, post, delete, patch
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_200_OK
from returns.result import Result

from src.Ship.Core.Errors import DomainException
from src.Ship.Decorators.result_handler import result_handler
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Actions.UpdateUserAction import (
    UpdateUserAction,
    UpdateUserInput,
)
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    CreateUserRequest,
    UpdateUserRequest,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserResponse,
    UserListResponse,
)
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError
from src.Containers.AppSection.UserModule.Models.User import AppUser


class UserController(Controller):
    """HTTP API controller for User operations.
    
    Uses Actions for write operations and Queries for read operations (CQRS).
    Note: @inject is not needed when using DishkaRouter.
    """
    
    path = "/users"
    tags = ["Users"]
    
    @post("/")
    @result_handler(UserResponse, success_status=HTTP_201_CREATED)
    async def create_user(
        self,
        data: CreateUserRequest,
        action: FromDishka[CreateUserAction],
    ) -> Result[AppUser, UserError]:
        """Create a new user."""
        return await action.run(data)
    
    @get("/{user_id:uuid}")
    async def get_user(
        self,
        user_id: UUID,
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        """Get user by ID."""
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        if user is None:
            raise DomainException(UserNotFoundError(user_id=user_id))
        return UserResponse.from_entity(user)
    
    @get("/")
    async def list_users(
        self,
        query: FromDishka[ListUsersQuery],
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False,
    ) -> UserListResponse:
        """List users with pagination (CQRS Query directly)."""
        result = await query.execute(ListUsersQueryInput(
            limit=limit,
            offset=offset,
            active_only=active_only,
        ))
        return UserListResponse(
            users=[UserResponse.from_entity(u) for u in result.users],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )
    
    @patch("/{user_id:uuid}")
    @result_handler(UserResponse, success_status=HTTP_200_OK)
    async def update_user(
        self,
        user_id: UUID,
        data: UpdateUserRequest,
        action: FromDishka[UpdateUserAction],
    ) -> Result[AppUser, UserError]:
        """Update user by ID."""
        return await action.run(UpdateUserInput(user_id=user_id, data=data))
    
    @delete("/{user_id:uuid}", status_code=HTTP_200_OK)
    @result_handler(None, success_status=HTTP_204_NO_CONTENT)
    async def delete_user(
        self,
        user_id: UUID,
        action: FromDishka[DeleteUserAction],
    ) -> Result[None, UserError]:
        """Delete user by ID (soft delete)."""
        return await action.run(user_id)
```

### Реальный пример: AuthController

```python
# src/Containers/AppSection/UserModule/UI/API/Controllers/AuthController.py
from litestar import Controller, get, post, Response
from litestar.status_codes import HTTP_200_OK
from dishka.integrations.litestar import FromDishka
from returns.result import Result

from src.Ship.Auth.Guards import auth_guard, CurrentUser
from src.Ship.Core.Errors import DomainException
from src.Ship.Decorators.result_handler import result_handler
from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import (
    AuthenticateAction,
    AuthResult,
)
from src.Containers.AppSection.UserModule.Actions.ChangePasswordAction import (
    ChangePasswordAction,
    ChangePasswordInput,
)
from src.Containers.AppSection.UserModule.Actions.RefreshTokenAction import RefreshTokenAction
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import TokenPair
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    LoginRequest,
    ChangePasswordRequest,
    RefreshTokenRequest,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserResponse,
    AuthResponse,
    TokenRefreshResponse,
)
from src.Containers.AppSection.UserModule.Errors import UserError, UserNotFoundError


class AuthController(Controller):
    """Authentication API endpoints."""
    
    path = "/auth"
    tags = ["Authentication"]
    
    @post("/login")
    @result_handler(AuthResponse, success_status=HTTP_200_OK)
    async def login(
        self,
        data: LoginRequest,
        action: FromDishka[AuthenticateAction],
    ) -> Result[AuthResult, UserError]:
        """Authenticate user and return tokens."""
        return await action.run(data)
    
    @get(
        "/me",
        dependencies={"current_user": auth_guard},
    )
    async def get_current_user(
        self,
        current_user: CurrentUser,
        query: FromDishka[GetUserQuery],
    ) -> UserResponse:
        """Get current authenticated user (requires JWT)."""
        user = await query.execute(GetUserQueryInput(user_id=current_user.id))
        if user is None:
            raise DomainException(UserNotFoundError(user_id=current_user.id))
        return UserResponse.from_entity(user)
    
    @post(
        "/change-password",
        dependencies={"current_user": auth_guard},
    )
    @result_handler(None, success_status=HTTP_200_OK)
    async def change_password(
        self,
        current_user: CurrentUser,
        data: ChangePasswordRequest,
        action: FromDishka[ChangePasswordAction],
    ) -> Result[None, UserError]:
        """Change current user's password (requires JWT)."""
        return await action.run(ChangePasswordInput(
            user_id=current_user.id,
            data=data,
        ))
    
    @post("/refresh")
    @result_handler(TokenRefreshResponse, success_status=HTTP_200_OK)
    async def refresh_token(
        self,
        data: RefreshTokenRequest,
        action: FromDishka[RefreshTokenAction],
    ) -> Result[TokenPair, UserError]:
        """Refresh access token using refresh token."""
        return await action.run(data)
    
    @post("/logout")
    async def logout(self) -> Response:
        """Logout user (client-side token invalidation).
        
        Since JWT is stateless, actual invalidation happens client-side.
        """
        return Response(
            content={"message": "Successfully logged out"},
            status_code=HTTP_200_OK,
        )
```

### Authentication Guards

```python
# src/Ship/Auth/Guards.py
from uuid import UUID
from typing import Annotated
from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.params import Dependency

from src.Ship.Auth.Middleware import AuthUser, get_auth_user_from_request


async def auth_guard(request: Request) -> AuthUser:
    """Guard that requires authentication.
    
    Use as a dependency to protect routes.
    
    Example:
        @get("/protected", dependencies={"current_user": auth_guard})
        async def protected_route(current_user: CurrentUser) -> dict:
            return {"user_id": str(current_user.id)}
    """
    auth_user = get_auth_user_from_request(request)
    
    if auth_user is None:
        raise NotAuthorizedException(
            detail="Authentication required",
            extra={"code": "AUTH_REQUIRED"},
        )
    
    return auth_user


async def optional_auth_guard(request: Request) -> AuthUser | None:
    """Guard that optionally extracts authentication.
    
    Useful for routes that work both authenticated and anonymously.
    """
    return get_auth_user_from_request(request)


# Type aliases for dependency injection
CurrentUser = Annotated[AuthUser, Dependency(skip_validation=True)]
OptionalUser = Annotated[AuthUser | None, Dependency(skip_validation=True)]
```

---

## 👂 Listener (Event Handler)

**Назначение:** Обработка Domain Events. Слабая связанность между модулями.

### Принципы:

1. **@listener декоратор** — регистрация в Litestar Events
2. **Async handlers** — асинхронные обработчики
3. **Multiple events** — один listener может слушать несколько событий
4. **WebSocket broadcast** — публикация в ChannelsPlugin

### Реальные примеры

```python
# src/Containers/AppSection/UserModule/Listeners.py
import logfire
from litestar import Litestar
from litestar.events import listener
from litestar.channels import ChannelsPlugin


def _publish_to_channel(
    app: Litestar | None,
    user_id: str,
    event_type: str,
    data: dict | None = None,
) -> None:
    """Publish event to user's WebSocket channel.
    
    Note: channels.publish() is non-blocking (synchronous).
    """
    if app is None:
        return
    
    channels = app.plugins.get(ChannelsPlugin)
    if channels:
        message = {"event": event_type, "user_id": user_id, **(data or {})}
        channels.publish(message, channels=[f"user:{user_id}"])


@listener("UserCreated")
async def on_user_created(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle UserCreated event.
    
    Triggered after a new user is successfully created.
    Publishes to WebSocket channel for real-time updates.
    """
    logfire.info(
        "🎉 User created event received",
        user_id=user_id,
        email=email,
    )
    
    # Publish to WebSocket channel
    _publish_to_channel(app, user_id, "user_created", {"email": email})


@listener("UserDeleted")
async def on_user_deleted(
    user_id: str,
    email: str,
    app: Litestar | None = None,
    **kwargs,
) -> None:
    """Handle UserDeleted event."""
    logfire.info("🗑️ User deleted", user_id=user_id, email=email)
    _publish_to_channel(app, user_id, "user_deleted", {"email": email})


@listener("UserUpdated")
async def on_user_updated(
    user_id: str,
    app: Litestar | None = None,
    updated_fields: list[str] | None = None,
    **kwargs,
) -> None:
    """Handle UserUpdated event."""
    logfire.info("✏️ User updated", user_id=user_id, updated_fields=updated_fields)
    _publish_to_channel(app, user_id, "user_updated", {"updated_fields": updated_fields})


@listener("UserCreated", "UserDeleted", "UserUpdated")
async def on_user_changed(
    user_id: str,
    occurred_at: str | None = None,
    **kwargs,
) -> None:
    """Handle any user change event for audit logging."""
    logfire.info("📝 User change audit", user_id=user_id)
```

### Регистрация в App

```python
# src/App.py (фрагмент)
from src.Containers.AppSection.UserModule.Listeners import (
    on_user_created,
    on_user_updated,
    on_user_deleted,
    on_user_changed,
)

app = Litestar(
    # ...
    listeners=[
        on_user_created,
        on_user_updated,
        on_user_deleted,
        on_user_changed,
    ],
)
```

---

## 🔷 GraphQL (Strawberry)

**Назначение:** GraphQL API с автоматической генерацией типов из Pydantic.

### Принципы:

1. **Strawberry + Pydantic** — автогенерация типов
2. **CQRS** — Mutations = Actions, Queries = Query classes
3. **get_dependency** — helper для DI в resolvers
4. **Pattern matching** — для Result обработки

### GraphQL Types

```python
# src/Containers/AppSection/UserModule/UI/GraphQL/Types.py
import strawberry
from strawberry.experimental.pydantic import type as pydantic_type, input as pydantic_input

from src.Containers.AppSection.UserModule.Data.Schemas.Responses import (
    UserResponse,
    UserListResponse,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import (
    CreateUserRequest,
)


# Auto-generate GraphQL types from Pydantic models
@pydantic_type(model=UserResponse, all_fields=True)
class UserType:
    """GraphQL type for User - auto-generated from UserResponse."""
    pass


@pydantic_type(model=UserListResponse, all_fields=True)
class UserListType:
    """GraphQL type for paginated user list."""
    pass


@pydantic_input(model=CreateUserRequest, all_fields=True)
class CreateUserInput:
    """Input for creating a user."""
    pass


# Error and payload types (GraphQL-specific)
@strawberry.type
class UserError:
    """GraphQL error type."""
    message: str
    code: str


@strawberry.type
class CreateUserPayload:
    """Payload for createUser mutation."""
    user: UserType | None = None
    error: UserError | None = None
```

### GraphQL Resolvers

```python
# src/Containers/AppSection/UserModule/UI/GraphQL/Resolvers.py
import strawberry
from uuid import UUID
from returns.result import Success, Failure

from src.Ship.GraphQL.Helpers import get_dependency
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.UI.GraphQL.Types import (
    UserType,
    UserListType,
    CreateUserInput,
    CreateUserPayload,
    UserError as UserErrorType,
)


@strawberry.type
class UserQuery:
    """GraphQL queries for users (CQRS read side)."""

    @strawberry.field
    async def user(self, id: UUID, info: strawberry.Info) -> UserType | None:
        """Get user by ID."""
        query = await get_dependency(info, GetUserQuery)
        user = await query.execute(GetUserQueryInput(user_id=id))
        return UserType.from_pydantic(UserResponse.from_entity(user)) if user else None

    @strawberry.field
    async def users(
        self,
        info: strawberry.Info,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False,
    ) -> UserListType:
        """List users with pagination."""
        query = await get_dependency(info, ListUsersQuery)
        result = await query.execute(ListUsersQueryInput(
            limit=limit,
            offset=offset,
            active_only=active_only,
        ))
        # Convert to Pydantic then to Strawberry
        return UserListType.from_pydantic(UserListResponse(
            users=[UserResponse.from_entity(u) for u in result.users],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        ))


@strawberry.type
class UserMutation:
    """GraphQL mutations for users (CQRS write side)."""

    @strawberry.mutation
    async def create_user(
        self,
        input: CreateUserInput,
        info: strawberry.Info,
    ) -> CreateUserPayload:
        """Create a new user."""
        action = await get_dependency(info, CreateUserAction)
        request = input.to_pydantic()
        result = await action.run(request)
        
        match result:
            case Success(user):
                return CreateUserPayload(user=UserType.from_pydantic(
                    UserResponse.from_entity(user)
                ))
            case Failure(error):
                return CreateUserPayload(error=UserErrorType(
                    message=error.message,
                    code=error.code,
                ))
```

---

## 💻 CLI (Click Commands)

**Назначение:** Командная строка для администрирования.

### Принципы:

1. **Click groups** — иерархия команд
2. **@with_container** — DI контейнер для CLI
3. **Rich output** — красивый вывод в терминал
4. **Pattern matching** — для Result обработки

### Реальные примеры

```python
# src/Containers/AppSection/UserModule/UI/CLI/Commands.py
import click
from uuid import UUID
from rich.console import Console
from rich.table import Table
from returns.result import Success, Failure

from src.Ship.CLI.Decorators import with_container
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import (
    ListUsersQuery,
    ListUsersQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest

console = Console()


@click.group(name="users")
def users_group() -> None:
    """User management commands.
    
    Available via Litestar CLI: litestar users <command>
    """
    pass


@users_group.command(name="create")
@click.option("--email", "-e", required=True, help="User email address")
@click.option("--password", "-p", required=True, help="User password (min 8 chars)")
@click.option("--name", "-n", required=True, help="User display name")
@with_container
async def create_user(container, email: str, password: str, name: str) -> None:
    """Create a new user.
    
    Example:
        litestar users create -e user@example.com -p password123 -n "John Doe"
    """
    action = await container.get(CreateUserAction)
    request = CreateUserRequest(email=email, password=password, name=name)
    result = await action.run(request)
    
    match result:
        case Success(user):
            console.print(f"[green]✓[/green] User created successfully!")
            console.print(f"  ID: {user.id}")
            console.print(f"  Email: {user.email}")
            console.print(f"  Name: {user.name}")
        case Failure(error):
            console.print(f"[red]✗[/red] Error: {error.message}")
            raise SystemExit(1)


@users_group.command(name="list")
@click.option("--limit", "-l", default=20, help="Maximum number of users")
@click.option("--offset", "-o", default=0, help="Number of users to skip")
@click.option("--active-only", "-a", is_flag=True, help="Show only active users")
@with_container
async def list_users(container, limit: int, offset: int, active_only: bool) -> None:
    """List all users with pagination.
    
    Example:
        litestar users list --limit 10 --active-only
    """
    query = await container.get(ListUsersQuery)
    output = await query.execute(
        ListUsersQueryInput(limit=limit, offset=offset, active_only=active_only)
    )

    table = Table(title="Users")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Email")
    table.add_column("Name")
    table.add_column("Active", justify="center")
    table.add_column("Created")

    for user in output.users:
        table.add_row(
            str(user.id)[:8] + "...",
            user.email,
            user.name,
            "✓" if user.is_active else "✗",
            str(user.created_at)[:19],
        )

    console.print(table)
    console.print(f"\nTotal: {output.total} | Showing: {len(output.users)}")
```

---

## ⚡ Workers (TaskIQ Background Tasks)

**Назначение:** Асинхронные фоновые задачи.

### Принципы:

1. **@broker.task** — регистрация задачи
2. **@inject + FromDishka** — DI в workers
3. **task.kiq()** — отправка задачи в очередь
4. **Pattern matching** — для Result обработки

### Реальные примеры

```python
# src/Containers/AppSection/UserModule/UI/Workers/Tasks.py
from uuid import UUID
from dishka.integrations.taskiq import FromDishka, inject
from returns.result import Success, Failure

from src.Ship.Infrastructure.Workers.Broker import broker
from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Tasks.SendWelcomeEmailTask import (
    SendWelcomeEmailTask,
    WelcomeEmailData,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Requests import CreateUserRequest


@broker.task
@inject
async def send_welcome_email_task(
    email: str,
    name: str,
    task: FromDishka[SendWelcomeEmailTask],
) -> dict:
    """Background task: Send welcome email to new user."""
    result = await task.run(WelcomeEmailData(email=email, name=name))
    
    return {
        "status": "sent" if result else "failed",
        "email": email,
        "name": name,
    }


@broker.task
@inject
async def create_user_async_task(
    email: str,
    password: str,
    name: str,
    action: FromDishka[CreateUserAction],
) -> dict:
    """Background task: Create user asynchronously.
    
    Useful for bulk imports or delayed user creation.
    """
    request = CreateUserRequest(email=email, password=password, name=name)
    result = await action.run(request)

    match result:
        case Success(user):
            # Schedule welcome email
            await send_welcome_email_task.kiq(email=user.email, name=user.name)
            return {
                "status": "created",
                "user_id": str(user.id),
                "email": user.email,
            }
        case Failure(error):
            return {
                "status": "failed",
                "error": error.message,
                "code": error.code,
            }


@broker.task
async def bulk_create_users_task(users_data: list[dict]) -> dict:
    """Background task: Create multiple users in bulk."""
    results = {"created": [], "failed": []}

    for user_data in users_data:
        task = await create_user_async_task.kiq(
            email=user_data["email"],
            password=user_data["password"],
            name=user_data["name"],
        )
        results["created"].append({
            "email": user_data["email"],
            "task_id": str(task.task_id),
        })

    return {"status": "scheduled", "total": len(users_data), "tasks": results}
```

---

## 🔌 WebSocket (Real-time Updates)

**Назначение:** Real-time обновления через WebSocket + Litestar Channels.

### Принципы:

1. **ChannelsPlugin** — pub/sub для WebSocket
2. **JWT authentication** — через query param или header
3. **anyio TaskGroup** — параллельная обработка команд и сообщений
4. **Channel naming** — `user:{user_id}` для user-specific updates

### Реальный пример

```python
# src/Containers/AppSection/UserModule/UI/WebSocket/Handlers.py
import anyio
from uuid import UUID
from litestar import WebSocket, websocket
from litestar.channels import ChannelsPlugin

from src.Ship.Auth.JWT import get_jwt_service
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import (
    GetUserQuery,
    GetUserQueryInput,
)
from src.Containers.AppSection.UserModule.Data.Schemas.Responses import UserResponse


def _authenticate_websocket(socket: WebSocket) -> UUID | None:
    """Authenticate WebSocket connection via JWT token.
    
    Checks for token in:
    1. Query parameter: ?token=<jwt_token>
    2. Sec-WebSocket-Protocol header
    """
    jwt_service = get_jwt_service()
    token = socket.query_params.get("token")
    
    if not token:
        protocol = socket.headers.get("sec-websocket-protocol")
        if protocol:
            parts = protocol.split(",")
            if len(parts) >= 2:
                token = parts[1].strip()
    
    if not token:
        return None
    
    payload = jwt_service.verify_token(token)
    return payload.sub if payload else None


@websocket("/ws/users/{user_id:uuid}")
async def user_updates_handler(
    socket: WebSocket,
    user_id: UUID,
    channels: ChannelsPlugin,
) -> None:
    """WebSocket handler for user updates using Litestar Channels.
    
    Protocol:
    - Connect: Receive current user state, auto-subscribe to channel
    - Messages: Receive real-time updates via channel subscription
    - Commands:
        - {"command": "refresh"} - Get latest user data
        - {"command": "ping"} - Keep-alive ping
    """
    await socket.accept()
    
    container = socket.app.state.dishka_container
    
    async with container() as request_container:
        query = await request_container.get(GetUserQuery)
        channel_name = f"user:{user_id}"
        
        # Send initial state
        user = await query.execute(GetUserQueryInput(user_id=user_id))
        if not user:
            await socket.send_json({"event": "error", "message": "User not found"})
            await socket.close()
            return
        
        response = UserResponse.from_entity(user)
        await socket.send_json({
            "event": "connected",
            "channel": channel_name,
            "user": response.model_dump(mode="json"),
        })
        
        # Subscribe to channel and handle messages
        async with channels.start_subscription([channel_name]) as subscriber:
            
            async def handle_commands():
                while True:
                    try:
                        message = await socket.receive_json()
                    except Exception:
                        return
                    
                    match message.get("command"):
                        case "refresh":
                            user = await query.execute(GetUserQueryInput(user_id=user_id))
                            if user:
                                await socket.send_json({
                                    "event": "user_data",
                                    "user": UserResponse.from_entity(user).model_dump(mode="json"),
                                })
                        case "ping":
                            await socket.send_json({"event": "pong"})
            
            async def handle_channel_messages():
                async for message in subscriber.iter_events():
                    await socket.send_json(message)
            
            async with anyio.create_task_group() as tg:
                tg.start_soon(handle_commands)
                tg.start_soon(handle_channel_messages)


@websocket("/ws/me")
async def authenticated_user_updates_handler(
    socket: WebSocket,
    channels: ChannelsPlugin,
) -> None:
    """Authenticated WebSocket handler for current user updates.
    
    Requires JWT token via query parameter or header.
    """
    auth_user_id = _authenticate_websocket(socket)
    
    if auth_user_id is None:
        await socket.close(code=4001, reason="Authentication required")
        return
    
    await socket.accept()
    # ... same logic as user_updates_handler but with auth_user_id
```

---

## 🏭 Provider (Dependency Injection)

**Назначение:** Регистрация зависимостей в Dishka DI контейнере.

### Принципы:

1. **Scope.APP** — singleton (Tasks, Settings)
2. **Scope.REQUEST** — per-request (Actions, Queries, UoW)
3. **provide()** — регистрация классов
4. **Разные провайдеры** — для HTTP и CLI контекстов

### Реальные примеры

```python
# src/Containers/AppSection/UserModule/Providers.py
from dishka import Provider, Scope, provide
from litestar import Request

from src.Containers.AppSection.UserModule.Actions.CreateUserAction import CreateUserAction
from src.Containers.AppSection.UserModule.Actions.DeleteUserAction import DeleteUserAction
from src.Containers.AppSection.UserModule.Actions.UpdateUserAction import UpdateUserAction
from src.Containers.AppSection.UserModule.Actions.AuthenticateAction import AuthenticateAction
from src.Containers.AppSection.UserModule.Actions.ChangePasswordAction import ChangePasswordAction
from src.Containers.AppSection.UserModule.Actions.RefreshTokenAction import RefreshTokenAction
from src.Containers.AppSection.UserModule.Queries.ListUsersQuery import ListUsersQuery
from src.Containers.AppSection.UserModule.Queries.GetUserQuery import GetUserQuery
from src.Containers.AppSection.UserModule.Data.Repositories.UserRepository import UserRepository
from src.Containers.AppSection.UserModule.Data.UnitOfWork import UserUnitOfWork
from src.Containers.AppSection.UserModule.Tasks.HashPasswordTask import HashPasswordTask
from src.Containers.AppSection.UserModule.Tasks.VerifyPasswordTask import VerifyPasswordTask
from src.Containers.AppSection.UserModule.Tasks.GenerateTokenTask import GenerateTokenTask
from src.Containers.AppSection.UserModule.Tasks.SendWelcomeEmailTask import SendWelcomeEmailTask


class UserModuleProvider(Provider):
    """Core provider for UserModule - APP scope (singletons).
    
    Stateless services that can be reused across requests.
    """
    
    scope = Scope.APP
    
    # Tasks - stateless, reusable
    hash_password_task = provide(HashPasswordTask)
    verify_password_task = provide(VerifyPasswordTask)
    generate_token_task = provide(GenerateTokenTask)
    send_welcome_email_task = provide(SendWelcomeEmailTask)


class _BaseUserRequestProvider(Provider):
    """Base provider with common REQUEST scope dependencies.
    
    Contains all dependencies shared between HTTP and CLI contexts.
    """
    
    scope = Scope.REQUEST
    
    # Data Layer
    user_repository = provide(UserRepository)
    
    # Queries - CQRS read side
    list_users_query = provide(ListUsersQuery)
    get_user_query = provide(GetUserQuery)
    
    # Actions - CQRS write side
    create_user_action = provide(CreateUserAction)
    update_user_action = provide(UpdateUserAction)
    delete_user_action = provide(DeleteUserAction)
    authenticate_action = provide(AuthenticateAction)
    change_password_action = provide(ChangePasswordAction)
    refresh_token_action = provide(RefreshTokenAction)


class UserRequestProvider(_BaseUserRequestProvider):
    """HTTP request-scoped provider for UserModule.
    
    Extends base provider with UnitOfWork that has event emitter.
    """
    
    @provide
    def provide_user_uow(self, request: Request) -> UserUnitOfWork:
        """Provide UserUnitOfWork with event emitter from request."""
        return UserUnitOfWork(_emit=request.app.emit, _app=request.app)


class UserCLIProvider(_BaseUserRequestProvider):
    """CLI-specific provider for UserModule.
    
    Extends base provider with UnitOfWork without event emitter.
    """
    
    @provide
    def provide_user_uow(self) -> UserUnitOfWork:
        """Provide UserUnitOfWork without event emitter for CLI."""
        return UserUnitOfWork(_emit=None, _app=None)
```

### App Provider

```python
# src/Ship/Providers/AppProvider.py
from dishka import Provider, Scope, provide
from dishka.integrations.litestar import LitestarProvider

from src.Ship.Configs import Settings, get_settings
from src.Ship.Auth.JWT import JWTService, get_jwt_service


class AppProvider(Provider):
    """Main application provider.
    
    Provides application-level dependencies like settings and JWT service.
    """
    
    @provide(scope=Scope.APP)
    def provide_settings(self) -> Settings:
        """Provide application settings."""
        return get_settings()
    
    @provide(scope=Scope.APP)
    def provide_jwt_service(self) -> JWTService:
        """Provide JWT service for token operations (singleton)."""
        return get_jwt_service()


def get_all_providers() -> list[Provider]:
    """Get all application providers for HTTP context."""
    from src.Containers.AppSection.UserModule.Providers import (
        UserModuleProvider,
        UserRequestProvider,
    )
    
    return [
        AppProvider(),
        LitestarProvider(),  # Provides Request in REQUEST scope
        UserModuleProvider(),
        UserRequestProvider(),
    ]


def get_cli_providers() -> list[Provider]:
    """Get providers for CLI context (without Request dependency)."""
    from src.Containers.AppSection.UserModule.Providers import (
        UserModuleProvider,
        UserCLIProvider,
    )
    
    return [
        AppProvider(),
        UserModuleProvider(),
        UserCLIProvider(),
    ]
```

---

## 📊 Диаграмма взаимодействия

```
                    ┌──────────────────────────────────────────┐
                    │              Client Request               │
                    └─────────────────┬────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────┐       ┌───────────────────┐       ┌─────────────────┐
│   HTTP REST     │       │     GraphQL       │       │    WebSocket    │
│   Controller    │       │     Resolver      │       │     Handler     │
└────────┬────────┘       └─────────┬─────────┘       └────────┬────────┘
         │                          │                          │
         │          ┌───────────────┴───────────────┐          │
         │          ▼                               ▼          │
         │  ┌───────────────┐             ┌───────────────┐    │
         │  │    Action     │             │     Query     │    │
         │  │ (Write/CQRS)  │             │ (Read/CQRS)   │    │
         │  │               │             │               │    │
         │  │ Result[T, E]  │             │ Returns T     │    │
         │  └───────┬───────┘             └───────┬───────┘    │
         │          │                             │            │
         │          ▼                             │            │
         │  ┌───────────────┐                     │            │
         │  │     Tasks     │                     │            │
         │  │ - HashPass    │                     │            │
         │  │ - VerifyPass  │                     │            │
         │  │ - GenToken    │                     │            │
         │  └───────┬───────┘                     │            │
         │          │                             │            │
         │          ▼                             ▼            │
         │  ┌─────────────────────────────────────────────┐    │
         │  │           Repository + UnitOfWork            │    │
         │  │                                              │    │
         │  │  UoW: Transactions + Domain Events          │    │
         │  │  Repository: CRUD + Domain Queries          │    │
         │  └──────────────────┬──────────────────────────┘    │
         │                     │                               │
         │                     ▼                               │
         │  ┌─────────────────────────────────────────────┐    │
         │  │           Piccolo ORM (Model)                │    │
         │  │   AppUser → PostgreSQL table "app_users"    │    │
         │  └─────────────────────────────────────────────┘    │
         │                     │                               │
         │                     │ commit()                      │
         │                     ▼                               │
         │  ┌─────────────────────────────────────────────┐    │
         │  │           Litestar Events                    │    │
         │  │   UserCreated, UserUpdated, UserDeleted     │    │
         │  └──────────────────┬──────────────────────────┘    │
         │                     │                               │
         │                     ▼                               │
         │  ┌─────────────────────────────────────────────┐    │
         │  │             Listeners                        │◄───┘
         │  │   - on_user_created                         │
         │  │   - on_user_updated                         │
         │  │   - Publish to WebSocket Channels           │
         │  └─────────────────────────────────────────────┘
         │
         │  Background Processing:
         │  ┌─────────────────────────────────────────────┐
         └─►│            TaskIQ Workers                   │
            │   - send_welcome_email_task                 │
            │   - create_user_async_task                  │
            │   - bulk_create_users_task                  │
            └─────────────────────────────────────────────┘
```

### Потоки данных

| Транспорт | Вход | Обработка | Выход |
|-----------|------|-----------|-------|
| **HTTP REST** | Request DTO → Controller | Action.run() / Query.execute() | Response DTO (JSON) |
| **GraphQL** | Input → Resolver | Action.run() / Query.execute() | Type / Payload |
| **WebSocket** | JSON Command | Query.execute() + Channels | JSON Event |
| **CLI** | Click Options | Action.run() / Query.execute() | Rich Console |
| **Workers** | Task Args | Action.run() | Dict Result |

---

## 📋 Сводная таблица компонентов

| Компонент | Базовый класс | Scope | Возвращает | Транспорт |
|-----------|---------------|-------|------------|-----------|
| Action | `Action[In, Out, Err]` | REQUEST | `Result[T, E]` | All |
| Task | `Task[In, Out]` / `SyncTask` | APP | `T` | Internal |
| Query | `Query[In, Out]` | REQUEST | `T` | All |
| Repository | `Repository[ModelT]` | REQUEST | `ModelT` | Internal |
| UnitOfWork | `BaseUnitOfWork` | REQUEST | Context manager | Internal |
| Model | `Model` (Piccolo Table) | - | ORM Entity | Internal |
| Event | `DomainEvent` | - | Published via emit() | Internal |
| Error | `BaseError` | - | HTTP status + message | All |
| Schema | `EntitySchema` / `BaseModel` | - | DTO | All |
| Controller | `Controller` (Litestar) | REQUEST | Response | HTTP |
| Resolver | `@strawberry.type` | REQUEST | GraphQL Type | GraphQL |
| Handler | `@websocket` | REQUEST | WebSocket messages | WebSocket |
| Command | `@click.command` | REQUEST | Console output | CLI |
| Worker | `@broker.task` | REQUEST | Dict result | Background |
| Listener | `@listener` | - | Side effects | Events |
| Provider | `Provider` (Dishka) | APP/REQUEST | Dependencies | DI |

---

<div align="center">

**Следующий раздел:** [04-result-railway.md](04-result-railway.md) — Railway-Oriented Programming

</div>
