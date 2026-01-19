# 📋 План разработки Hyper-Porto проекта

> Поэтапный план для разработки проекта на основе архитектуры Hyper-Porto v4.3

---

## 🎯 Обзор фаз

```
Phase 0: Подготовка окружения        (1-2 дня)
Phase 1: Ship Layer (Инфраструктура) (2-3 дня)
Phase 2: Первый Container            (2-3 дня)
Phase 3: Транспорты                  (1-2 дня)
Phase 4: Дополнительные Containers   (по необходимости)
Phase 5: Production Ready            (2-3 дня)
```

---

## 🔧 Phase 0: Подготовка окружения

### Цель
Настроить проект, зависимости и базовую структуру папок.

### Задачи

#### 0.1 Инициализация проекта
```bash
# Создать виртуальное окружение
uv venv
source .venv/bin/activate

# Инициализировать проект
uv init hyper-porto-app
```

#### 0.2 Установка зависимостей
Скопировать `pyproject.toml` из `docs/08-libraries.md` и выполнить:
```bash
uv sync
```

**Основные зависимости:**
- [x] litestar[standard]
- [x] strawberry-graphql[litestar]
- [x] taskiq + taskiq-redis + taskiq-litestar
- [x] returns
- [x] anyio
- [x] dishka
- [x] piccolo[all] + litestar-piccolo
- [x] pydantic + pydantic-settings
- [x] logfire
- [x] tenacity
- [x] cashews

#### 0.3 Создание структуры папок
```
src/
├── Ship/
│   ├── Parents/
│   ├── Core/
│   ├── Infrastructure/
│   ├── Decorators/
│   ├── Providers/
│   ├── Configs/
│   ├── Exceptions/
│   └── Plugins/
├── Containers/
│   └── AppSection/
└── App.py

tests/
├── unit/
├── integration/
└── e2e/

specs/
```

#### 0.4 Конфигурация
- [x] Создать `piccolo_conf.py`
- [x] Создать `.env` и `src/Ship/Configs/Settings.py`
- [x] Настроить `pyproject.toml` (ruff, mypy)
- [ ] Настроить pre-commit hooks

### Документы для чтения
- `docs/02-project-structure.md`
- `docs/08-libraries.md`

---

## 🚢 Phase 1: Ship Layer (Инфраструктура)

### Цель
Создать базовые классы и инфраструктуру, которые будут использоваться всеми Containers.

### Задачи

#### 1.1 Parents/ — Базовые классы

**Action.py**
```python
# Читай: docs/03-components.md -> Action
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from returns.result import Result

InputT = TypeVar("InputT", contravariant=True)
OutputT = TypeVar("OutputT", covariant=True)
ErrorT = TypeVar("ErrorT", covariant=True)

class Action(ABC, Generic[InputT, OutputT, ErrorT]):
    @abstractmethod
    async def run(self, data: InputT) -> Result[OutputT, ErrorT]:
        ...
```

- [x] `Action.py` — базовый Action
- [x] `Task.py` — базовый Task
- [x] `UnitOfWork.py` — BaseUnitOfWork с интеграцией litestar.events
- [x] `Model.py` — базовая Piccolo модель
- [ ] `Query.py` — базовый CQRS Query

#### 1.2 Core/ — Ядро системы

- [x] `Result.py` — re-export из returns
- [x] `Types.py` — общие типы (DomainEvent, etc.)
- [x] `BaseSchema.py` — EntitySchema для Response DTOs
- [x] `Errors.py` — базовые ошибки (BaseError, NotFoundError, etc.)
- [x] `Protocols.py` — typing.Protocol интерфейсы

#### 1.3 Infrastructure/ — Инфраструктура

- [x] `Database/Connection.py` — подключение к БД
- [ ] `Database/Session.py` — async session factory
- [x] `Cache/Redis.py` — Redis клиент (для cashews)
- [x] `Telemetry/Logging.py` — structured logging (structlog + logfire)

#### 1.4 Decorators/

- [x] `result_handler.py` — @result_handler для авто-маппинга Result → Response

#### 1.5 Providers/

- [x] `AppProvider.py` — глобальные зависимости (Settings, DB, Cache)
- [ ] `DatabaseProvider.py` — DB sessions

#### 1.6 Configs/

- [x] `Settings.py` — Pydantic BaseSettings

#### 1.7 Exceptions/

- [x] `Handlers.py` — глобальные exception handlers для Litestar

### Документы для чтения
- `docs/03-components.md` — компоненты
- `docs/04-result-railway.md` — Result и Railway
- `docs/12-reducing-boilerplate.md` — справочник реализации

### Проверка
```bash
# Должны работать импорты
python -c "from src.Ship.Parents.Action import Action"
python -c "from src.Ship.Core.Result import Result, Success, Failure"
```

---

## 📦 Phase 2: Первый Container (UserModule)

### Цель
Создать полноценный бизнес-модуль для работы с пользователями.

### Задачи

#### 2.1 Структура Container

```
Containers/AppSection/UserModule/
├── __init__.py
├── UI/
│   ├── API/
│   │   ├── Routes.py
│   │   └── Controllers/
│   │       └── UserController.py
│   └── __init__.py
├── Actions/
│   ├── CreateUserAction.py
│   ├── GetUserAction.py
│   └── AuthenticateAction.py
├── Tasks/
│   ├── HashPasswordTask.py
│   ├── ValidateEmailTask.py
│   └── GenerateTokenTask.py
├── Data/
│   ├── Repositories/
│   │   └── UserRepository.py
│   ├── Schemas/
│   │   ├── Requests.py
│   │   └── Responses.py
│   └── UnitOfWork.py
├── Models/
│   ├── User.py
│   ├── PiccoloApp.py
│   └── migrations/
├── Events/
│   ├── UserCreated.py
│   └── UserUpdated.py
├── Errors.py
└── Providers.py
```

#### 2.2 Models/ — Piccolo Tables

- [x] `User.py` — Piccolo Table с полями (id, email, password_hash, name, is_active, created_at)
- [x] `PiccoloApp.py` — конфигурация для миграций
- [x] Запустить миграции

#### 2.3 Errors.py — Ошибки модуля

```python
from pydantic import BaseModel

class UserError(BaseModel):
    model_config = {"frozen": True}
    message: str
    code: str = "USER_ERROR"

class UserNotFoundError(UserError):
    code: str = "USER_NOT_FOUND"
    user_id: UUID
```

- [x] `UserError` — базовая ошибка
- [x] `UserNotFoundError`
- [x] `UserAlreadyExistsError`
- [ ] `InvalidCredentialsError`

#### 2.4 Data/Schemas/ — DTOs

- [x] `Requests.py` — CreateUserRequest, LoginRequest, UpdateUserRequest
- [x] `Responses.py` — UserResponse (наследует EntitySchema)

#### 2.5 Data/Repositories/

- [x] `UserRepository.py` — обёртка над Piccolo Table API

#### 2.6 Data/UnitOfWork.py

- [x] `UserUnitOfWork` — наследник BaseUnitOfWork с users: UserRepository

#### 2.7 Tasks/

- [x] `HashPasswordTask.py` — bcrypt хеширование
- [ ] `ValidateEmailTask.py` — валидация email
- [ ] `GenerateTokenTask.py` — генерация JWT
- [x] `VerifyPasswordTask.py` — проверка пароля

#### 2.8 Actions/

- [x] `CreateUserAction.py` — регистрация пользователя
- [x] `GetUserAction.py` — получение пользователя по ID
- [x] `ListUsersAction.py` — список пользователей
- [x] `DeleteUserAction.py` — удаление пользователя
- [ ] `AuthenticateAction.py` — аутентификация (login)

#### 2.9 Events/

- [x] `UserCreated.py` — событие создания пользователя
- [x] `UserDeleted.py` — событие удаления пользователя

#### 2.10 Providers.py — DI регистрация

```python
from dishka import Provider, Scope, provide

class UserModuleProvider(Provider):
    scope = Scope.REQUEST
    
    hash_password = provide(HashPasswordTask)
    validate_email = provide(ValidateEmailTask)
    user_repository = provide(UserRepository)
    uow = provide(UserUnitOfWork)
    create_user_action = provide(CreateUserAction)
    get_user_action = provide(GetUserAction)
```

#### 2.11 UI/API/ — HTTP Controllers

- [x] `Controllers/UserController.py` — CRUD endpoints
- [x] `Routes.py` — DishkaRouter

### Документы для чтения
- `docs/03-components.md` — все компоненты
- `docs/04-result-railway.md` — Result и flow

### Проверка
```bash
# Тесты Actions
pytest tests/unit/containers/user_module/

# Запуск сервера
python -m litestar run src.App:app --reload
```

---

## 🌐 Phase 3: Транспорты

### Цель
Подключить дополнительные транспорты: GraphQL, CLI, WebSocket, Background Tasks.

### Задачи

#### 3.1 GraphQL (Strawberry)

- [x] `Ship/GraphQL/Schema.py` — корневая схема
- [x] `UserModule/UI/GraphQL/Types.py` — @strawberry.type
- [x] `UserModule/UI/GraphQL/Resolvers.py` — Query + Mutation

#### 3.2 CLI (Litestar CLIPlugin)

- [x] `UserModule/UI/CLI/Commands.py` — Click commands
- [x] Регистрация в pyproject.toml как entry point

#### 3.3 Background Tasks (TaskIQ)

- [x] `Ship/Infrastructure/Workers/Broker.py` — настройка брокера
- [x] `UserModule/UI/Workers/Tasks.py` — фоновые задачи (send_email, etc.)

#### 3.4 WebSocket

- [x] `UserModule/UI/WebSocket/Handlers.py` — WS handlers

### Документы для чтения
- `docs/09-transports.md` — все транспорты
- `docs/11-litestar-features.md` — Channels, Events

---

## 📦 Phase 4: Дополнительные Containers

### Цель
Добавить новые бизнес-модули по мере необходимости.

### Примеры модулей

#### OrderModule
- Создание заказов
- Статусы заказов
- История заказов

#### ProductModule
- Каталог продуктов
- Категории
- Поиск

#### NotificationModule (VendorSection)
- Email отправка
- Push уведомления
- SMS

### Шаблон для нового Container

```bash
# Скопировать структуру UserModule
cp -r src/Containers/AppSection/UserModule src/Containers/AppSection/NewModule

# Переименовать файлы и классы
# Обновить Providers.py
# Добавить роутер в App.py
```

---

## 🚀 Phase 5: Production Ready

### Цель
Подготовить проект к production.

### Задачи

#### 5.1 Observability

- [ ] Настроить Logfire для трассировки
- [ ] Добавить @traced декораторы на Actions
- [ ] Настроить structured logging

#### 5.2 Безопасность

- [ ] JWT аутентификация middleware
- [ ] Rate limiting
- [ ] CORS настройки

#### 5.3 Кэширование

- [ ] Настроить cashews с Redis
- [ ] Добавить @cached на Query endpoints

#### 5.4 Тестирование

- [ ] Unit tests для Actions
- [ ] Integration tests для Repositories
- [ ] E2E tests для API

#### 5.5 CI/CD

- [ ] GitHub Actions / GitLab CI
- [ ] Docker + docker-compose
- [ ] Health checks

#### 5.6 Документация

- [ ] OpenAPI (автогенерация Litestar)
- [ ] README с инструкциями

### Документы для чтения
- `docs/11-litestar-features.md` — middleware, stores, channels
- `docs/05-concurrency.md` — конкурентность

---

## 📊 Чеклист готовности

### Phase 0 ✅
- [x] pyproject.toml создан
- [x] Зависимости установлены
- [x] Структура папок создана
- [x] piccolo_conf.py настроен

### Phase 1 ✅
- [x] Ship/Parents/ заполнен
- [x] Ship/Core/ заполнен
- [x] Ship/Infrastructure/ базовый
- [x] Ship/Providers/ настроен

### Phase 2 ✅
- [x] UserModule полностью реализован
- [x] Миграции работают
- [x] API endpoints доступны
- [ ] Unit tests проходят

### Phase 3 ✅
- [x] GraphQL работает
- [x] CLI команды доступны
- [x] Background tasks запускаются
- [x] WebSocket handlers работают

### Phase 5
- [ ] Логирование настроено
- [ ] Тесты покрывают критические пути
- [ ] Docker образ собирается

---

## 💡 Советы по работе с AI

1. **Начинай с Phase 0** — без правильной структуры AI будет путаться
2. **Показывай документацию** — прикрепляй нужные файлы из `docs/`
3. **Используй Spec-Driven** — сначала spec.md, потом код
4. **Проверяй типы** — запускай mypy после генерации

---

## 🔗 Полезные команды

```bash
# Запуск сервера
python -m litestar run src.App:app --reload

# Миграции Piccolo
piccolo migrations new my_app --auto
piccolo migrations forwards my_app

# Тесты
pytest tests/ -v

# Линтинг
ruff check src/ --fix
mypy src/

# TaskIQ worker
taskiq worker src.Ship.Infrastructure.TaskIQ.Broker:broker
```

---

**Hyper-Porto v4.3** — Удачной разработки! 🚀

