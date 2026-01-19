# ✨ Best Practices для Porto Architecture

## 🎯 Основные принципы

### 1. Single Responsibility Principle (SRP)

```python
# ❌ Плохо: множественная ответственность
class UserService:
    async def create_user_and_send_email_and_log(self, data):
        # Создание пользователя
        user = await User.create(data)
        # Отправка email
        await send_email(user.email)
        # Логирование
        logger.info(f"User created: {user.id}")
        return user

# ✅ Хорошо: разделение ответственности
class CreateUserAction(Action):
    def __init__(self, 
                 create_task: CreateUserTask,
                 email_task: SendWelcomeEmailTask,
                 log_task: LogUserCreationTask):
        self.create = create_task
        self.email = email_task
        self.log = log_task
    
    async def run(self, data: UserDTO) -> User:
        user = await self.create.run(data)
        await self.email.run(user)
        await self.log.run(user)
        return user
```

### 2. Dependency Injection

```python
# ❌ Плохо: жёсткие зависимости
class CreateBookAction:
    async def run(self, data):
        # Прямое создание зависимостей
        validator = BookValidator()
        repository = BookRepository()
        notifier = EmailNotifier()
        
        await validator.validate(data)
        book = await repository.create(data)
        await notifier.notify(book)

# ✅ Хорошо: инъекция зависимостей
class CreateBookAction(Action):
    def __init__(self,
                 validator: BookValidator,
                 repository: BookRepository,
                 notifier: NotificationService):
        self.validator = validator
        self.repository = repository
        self.notifier = notifier
    
    async def run(self, data: BookDTO) -> Book:
        await self.validator.validate(data)
        book = await self.repository.create(data)
        await self.notifier.notify(book)
        return book
```

## 📁 Организация кода

### Структура Container

```
📦 Book/
├── 📄 __init__.py              # Публичный API контейнера
├── 📁 Actions/                 # Бизнес-операции
│   ├── 📄 __init__.py         # Экспорт всех Actions
│   ├── 📄 CreateBookAction.py # Одна операция = один файл
│   └── 📄 UpdateBookAction.py
├── 📁 Tasks/                   # Атомарные задачи
│   ├── 📄 __init__.py
│   ├── 📄 CreateBookTask.py   # Одна задача = один файл
│   └── 📄 ValidateISBNTask.py
├── 📁 Models/                  # Модели данных
│   ├── 📄 __init__.py
│   └── 📄 Book.py             # Одна сущность = один файл
├── 📁 Exceptions/              # Исключения контейнера
│   ├── 📄 __init__.py
│   └── 📄 BookExceptions.py   # Все исключения в одном файле
└── 📄 Providers.py            # DI конфигурация
```

### Правила импортов

```python
# ✅ Хорошо: абсолютные импорты
from src.Containers.AppSection.Book.Models import Book
from src.Containers.AppSection.Book.Tasks import CreateBookTask
from src.Ship.Parents.Action import Action

# ❌ Плохо: относительные импорты
from ..Models import Book
from ...Ship.Parents import Action

# ✅ Хорошо: группировка импортов
# Стандартная библиотека
import asyncio
from datetime import datetime
from typing import List, Optional

# Сторонние библиотеки
from litestar import Controller, get, post
from piccolo.table import Table
import logfire

# Локальные импорты
from src.Ship.Parents.Action import Action
from src.Containers.AppSection.Book.Models import Book
```

## 🎨 Паттерны проектирования

### Repository Pattern

```python
# src/Containers/AppSection/Book/Repositories/BookRepository.py
from src.Ship.Parents.Repository import Repository
from src.Containers.AppSection.Book.Models import Book
from typing import List, Optional

class BookRepository(Repository):
    """Инкапсуляция доступа к данным"""
    
    model = Book
    
    async def find_by_isbn(self, isbn: str) -> Optional[Book]:
        """Поиск книги по ISBN"""
        return await Book.objects.where(
            Book.isbn == isbn
        ).first()
    
    async def find_available(self, limit: int = 10) -> List[Book]:
        """Получение доступных книг"""
        return await Book.select().where(
            Book.is_available == True
        ).limit(limit).order_by(Book.created_at, ascending=False)
    
    async def search(self, query: str) -> List[Book]:
        """Полнотекстовый поиск"""
        return await Book.select().where(
            Book.title.ilike(f"%{query}%") |
            Book.author.ilike(f"%{query}%")
        ).limit(50)
```

### Unit of Work Pattern

```python
# src/Ship/Core/UnitOfWork.py
from contextlib import asynccontextmanager
from piccolo.engine import engine_finder

class UnitOfWork:
    """Паттерн Unit of Work для транзакций"""
    
    @asynccontextmanager
    async def transaction(self):
        """Контекстный менеджер для транзакций"""
        async with engine_finder().transaction():
            try:
                yield
            except Exception:
                # Автоматический rollback при исключении
                raise

# Использование в Action
class TransferBookAction(Action):
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def run(self, book_id: int, from_user: int, to_user: int):
        async with self.uow.transaction():
            # Все операции в одной транзакции
            await self.return_book_task.run(book_id, from_user)
            await self.borrow_book_task.run(book_id, to_user)
```

### Factory Pattern

```python
# src/Containers/AppSection/Notification/Factories/NotifierFactory.py
from enum import Enum
from typing import Protocol

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class Notifier(Protocol):
    async def send(self, user_id: int, message: str) -> None: ...

class NotifierFactory:
    """Фабрика для создания нотификаторов"""
    
    def __init__(self,
                 email_notifier: EmailNotifier,
                 sms_notifier: SMSNotifier,
                 push_notifier: PushNotifier):
        self.notifiers = {
            NotificationType.EMAIL: email_notifier,
            NotificationType.SMS: sms_notifier,
            NotificationType.PUSH: push_notifier,
        }
    
    def create(self, notification_type: NotificationType) -> Notifier:
        """Создаёт нотификатор по типу"""
        return self.notifiers[notification_type]
```

## 🔒 Безопасность

### Валидация данных

```python
# src/Containers/AppSection/Book/Validators/BookValidator.py
from pydantic import BaseModel, validator, Field
from typing import Optional

class BookCreateValidator(BaseModel):
    """Валидатор создания книги"""
    
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=100)
    isbn: str = Field(..., regex=r"^(?:\d{10}|\d{13})$")
    pages: int = Field(..., ge=1, le=10000)
    price: Optional[float] = Field(None, ge=0, le=999999.99)
    
    @validator('isbn')
    def validate_isbn(cls, v):
        """Проверка контрольной суммы ISBN"""
        clean_isbn = v.replace('-', '').replace(' ', '')
        
        if len(clean_isbn) == 10:
            if not cls._validate_isbn10(clean_isbn):
                raise ValueError("Invalid ISBN-10 checksum")
        elif len(clean_isbn) == 13:
            if not cls._validate_isbn13(clean_isbn):
                raise ValueError("Invalid ISBN-13 checksum")
        else:
            raise ValueError("ISBN must be 10 or 13 digits")
        
        return clean_isbn
    
    @validator('title', 'author')
    def sanitize_text(cls, v):
        """Санитизация текста от XSS"""
        import html
        return html.escape(v.strip())
```

### Аутентификация и авторизация

```python
# src/Ship/Middleware/AuthMiddleware.py
from litestar.middleware import AbstractMiddleware
from litestar.exceptions import NotAuthorizedException

class AuthMiddleware(AbstractMiddleware):
    """Middleware для проверки аутентификации"""
    
    async def __call__(self, scope, receive, send):
        # Пропускаем публичные endpoints
        if scope["path"] in ["/health", "/docs", "/schema"]:
            return await self.app(scope, receive, send)
        
        # Проверка токена
        token = self.get_token_from_header(scope)
        if not token:
            raise NotAuthorizedException("Token required")
        
        # Валидация токена
        user = await self.validate_token(token)
        if not user:
            raise NotAuthorizedException("Invalid token")
        
        # Добавление пользователя в scope
        scope["user"] = user
        return await self.app(scope, receive, send)
```

## 🧪 Тестирование

### Структура тестов

```
tests/
├── 📁 unit/                    # Unit тесты
│   ├── 📁 Containers/
│   │   └── 📁 Book/
│   │       ├── test_actions.py
│   │       └── test_tasks.py
│   └── 📁 Ship/
│       └── test_core.py
├── 📁 integration/             # Интеграционные тесты
│   └── test_book_workflow.py
├── 📁 fixtures/                # Фикстуры
│   ├── database.py
│   └── models.py
└── conftest.py                # Общая конфигурация pytest
```

### Unit тестирование Actions

```python
# tests/unit/Containers/Book/test_actions.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.Containers.AppSection.Book.Actions import CreateBookAction

@pytest.mark.asyncio
class TestCreateBookAction:
    """Тесты для CreateBookAction"""
    
    async def test_successful_creation(self):
        """Тест успешного создания книги"""
        # Arrange
        validate_task = AsyncMock()
        create_task = AsyncMock(return_value=MagicMock(id=1, title="Test"))
        notify_task = AsyncMock()
        
        action = CreateBookAction(
            validate_task=validate_task,
            create_task=create_task,
            notify_task=notify_task
        )
        
        # Act
        result = await action.run(
            title="Test Book",
            author="Test Author",
            isbn="1234567890"
        )
        
        # Assert
        assert result.id == 1
        assert result.title == "Test"
        validate_task.run.assert_called_once()
        create_task.run.assert_called_once()
        notify_task.run.assert_called_once()
    
    async def test_validation_failure(self):
        """Тест ошибки валидации"""
        # Arrange
        validate_task = AsyncMock(side_effect=ValidationError("Invalid ISBN"))
        create_task = AsyncMock()
        notify_task = AsyncMock()
        
        action = CreateBookAction(
            validate_task=validate_task,
            create_task=create_task,
            notify_task=notify_task
        )
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await action.run(
                title="Test Book",
                author="Test Author",
                isbn="invalid"
            )
        
        # Проверяем, что create и notify не вызывались
        create_task.run.assert_not_called()
        notify_task.run.assert_not_called()
```

### Integration тестирование

```python
# tests/integration/test_book_workflow.py
import pytest
from httpx import AsyncClient
from src.Main import create_app

@pytest.mark.asyncio
class TestBookWorkflow:
    """Интеграционные тесты workflow книг"""
    
    @pytest.fixture
    async def client(self):
        """HTTP клиент для тестов"""
        app = create_app()
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_complete_book_lifecycle(self, client, test_db):
        """Тест полного жизненного цикла книги"""
        # 1. Создание книги
        create_response = await client.post("/books", json={
            "title": "Integration Test Book",
            "author": "Test Author",
            "isbn": "1234567890123"
        })
        assert create_response.status_code == 201
        book_id = create_response.json()["id"]
        
        # 2. Получение книги
        get_response = await client.get(f"/books/{book_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Integration Test Book"
        
        # 3. Обновление книги
        update_response = await client.put(f"/books/{book_id}", json={
            "title": "Updated Book Title"
        })
        assert update_response.status_code == 200
        
        # 4. Удаление книги
        delete_response = await client.delete(f"/books/{book_id}")
        assert delete_response.status_code == 204
        
        # 5. Проверка удаления
        get_deleted_response = await client.get(f"/books/{book_id}")
        assert get_deleted_response.status_code == 404
```

## 📊 Логирование и мониторинг

### Структурированное логирование

```python
# src/Containers/AppSection/Book/Actions/CreateBookAction.py
import logfire
from src.Ship.Parents.Action import Action

class CreateBookAction(Action):
    """Action с детальным логированием"""
    
    async def run(self, data: BookDTO) -> Book:
        with logfire.span(
            "create_book_action",
            book_title=data.title,
            isbn=data.isbn
        ) as span:
            # Логирование начала операции
            logfire.info(
                "Starting book creation",
                data=data.dict(),
                user_id=self.context.user_id
            )
            
            try:
                # Валидация
                with span.span("validation"):
                    await self.validate_task.run(data)
                
                # Создание
                with span.span("database_insert"):
                    book = await self.create_task.run(data)
                    logfire.info(
                        "Book created successfully",
                        book_id=book.id
                    )
                
                # Уведомление
                with span.span("notification"):
                    await self.notify_task.run(book)
                
                # Метрика
                logfire.metric("books.created", 1, tags={"category": book.category})
                
                return book
                
            except Exception as e:
                logfire.error(
                    "Book creation failed",
                    error=str(e),
                    data=data.dict()
                )
                raise
```

## 🚀 Оптимизация производительности

### Асинхронная обработка

```python
# ✅ Хорошо: параллельное выполнение независимых задач
import asyncio

class ProcessBooksAction(Action):
    async def run(self, book_ids: List[int]) -> List[Book]:
        # Параллельная обработка книг
        tasks = [
            self.process_single_book(book_id)
            for book_id in book_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов и ошибок
        processed_books = []
        for result in results:
            if isinstance(result, Exception):
                logfire.error(f"Failed to process book: {result}")
            else:
                processed_books.append(result)
        
        return processed_books
```

### Кеширование

```python
# src/Ship/Core/Cache.py
from functools import wraps
import hashlib
import json
from typing import Any, Optional

class Cache:
    """Простой in-memory кеш"""
    
    def __init__(self):
        self._cache = {}
    
    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Генерация ключа кеша"""
        key_data = f"{prefix}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение из кеша"""
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Сохранение в кеш"""
        self._cache[key] = value
        # В продакшене используйте Redis с TTL

def cached(ttl: int = 300):
    """Декоратор для кеширования результатов"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            cache = self.cache  # Предполагаем, что cache инжектирован
            key = cache.cache_key(func.__name__, *args, **kwargs)
            
            # Проверка кеша
            result = await cache.get(key)
            if result is not None:
                return result
            
            # Выполнение и сохранение
            result = await func(self, *args, **kwargs)
            await cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Использование
class GetBookAction(Action):
    @cached(ttl=600)  # Кеш на 10 минут
    async def run(self, book_id: int) -> Book:
        return await self.find_task.run(book_id)
```

## 📝 Документирование кода

### Docstrings

```python
class CreateBookAction(Action):
    """
    Manages the book creation process.

    This action orchestrates the complete workflow of creating a book,
    including data validation, ISBN uniqueness checks, and database persistence.

    Attributes:
        find_by_isbn_task: Task to find book by ISBN
        create_book_task: Task to create book in database
        transformer: Task to transform model to DTO

    Example:
        >>> action = CreateBookAction(...)
        >>> book = await action.run(
        ...     title="Clean Code",
        ...     author="Robert Martin",
        ...     isbn="9780132350884"
        ... )
        >>> print(f"Book created: {book.id}")

    Raises:
        BookAlreadyExistsException: If book with ISBN already exists
        ValidationError: If input data is invalid
    """
    
    async def run(
        self,
        data: BookCreateDTO
    ) -> BookDTO:
        """
        Execute the book creation process.

        Args:
            data: Book creation data with validation

        Returns:
            BookDTO: The created book DTO

        Raises:
            BookAlreadyExistsException: If the book with ISBN already exists
            ValidationError: If input data is invalid
        """
        # Implementation...
```

## 🔍 Code Review Checklist

### Перед коммитом проверьте:

- [ ] **Single Responsibility**: Каждый компонент делает одно дело
- [ ] **Naming Convention**: Имена следуют паттерну `{Verb}{Entity}{Component}`
- [ ] **Type Hints**: Все параметры и возвраты типизированы
- [ ] **Error Handling**: Специфичные исключения для каждого случая
- [ ] **Async/Await**: Все I/O операции асинхронные
- [ ] **Dependency Injection**: Зависимости инжектируются, не создаются
- [ ] **Tests**: Unit тесты покрывают основные сценарии
- [ ] **Documentation**: Docstrings описывают "почему", а не "что"
- [ ] **Logging**: Структурированное логирование ключевых операций
- [ ] **Security**: Валидация входных данных, санитизация вывода

## 🎯 Анти-паттерны (чего избегать)

### ❌ God Object

```python
# Плохо: класс делает всё
class BookManager:
    def create_book(self): ...
    def update_book(self): ...
    def delete_book(self): ...
    def send_email(self): ...
    def generate_report(self): ...
    def validate_isbn(self): ...
    def calculate_price(self): ...
```

### ❌ Anemic Domain Model

```python
# Плохо: модель без поведения
class Book(Table):
    title = Varchar()
    price = Numeric()
    # Только данные, без методов

# Вся логика в сервисах
class BookService:
    def calculate_discount(self, book): ...
    def can_be_borrowed(self, book): ...
```

### ❌ Circular Dependencies

```python
# Плохо: циклические зависимости
# UserAction импортирует BookTask
from src.Containers.Book.Tasks import BookTask

# BookTask импортирует UserAction
from src.Containers.User.Actions import UserAction
```

## 📚 Следующие шаги

1. [**API Reference**](09-api-reference.md) - справочник по API
2. [**Архитектурные диаграммы**](10-diagrams.md) - визуализация архитектуры
3. [**AI Development**](11-ai-development.md) - работа с AI инструментами

---

<div align="center">

**✨ Clean Code + Porto = Excellence!**

[← Getting Started](07-getting-started.md) | [API Reference →](09-api-reference.md)

</div>
