# 🛠️ Технологии и библиотеки

## 🚀 Основной стек технологий

```mermaid
graph TB
    subgraph "Web Framework"
        L["⚡ Litestar<br/>Async Web Framework"]
    end
    
    subgraph "ORM & Database"
        P["🗄️ Piccolo ORM<br/>Async ORM"]
        S["💾 SQLite<br/>Database"]
    end
    
    subgraph "Dependency Injection"
        D["💉 Dishka<br/>DI Container"]
    end
    
    subgraph "Messaging"
        F["📨 FastStream<br/>Message Broker"]
        R["🐰 RabbitMQ<br/>Queue System"]
    end
    
    subgraph "Monitoring"
        LF["📊 Logfire<br/>Observability"]
    end
    
    L --> D
    L --> P
    P --> S
    L --> F
    F --> R
    L --> LF
    
    style L fill:#ff6b6b,stroke:#333,stroke-width:3px
    style P fill:#4ecdc4,stroke:#333,stroke-width:2px
    style D fill:#45b7d1,stroke:#333,stroke-width:2px
    style F fill:#96ceb4,stroke:#333,stroke-width:2px
    style LF fill:#ffeaa7,stroke:#333,stroke-width:2px
```

## ⚡ Litestar Framework

### 📖 Описание
**Litestar** - современный, высокопроизводительный асинхронный веб-фреймворк для Python, построенный на ASGI.

### ✨ Ключевые особенности
- 🚀 **Высокая производительность** - один из самых быстрых Python фреймворков
- 🔄 **Полностью асинхронный** - native async/await поддержка
- 📝 **Type hints** - полная поддержка типизации
- 📚 **OpenAPI** - автоматическая генерация документации
- 🔌 **Плагины** - расширяемая архитектура
- 🛡️ **Безопасность** - встроенная защита и middleware

### 💻 Пример использования

```python
from litestar import Litestar, get, post, Controller
from litestar.di import Provide
from typing import Dict, Any

class BookController(Controller):
    path = "/books"
    
    @get("/")
    async def list_books(self) -> list[Dict[str, Any]]:
        """Получение списка книг"""
        return [{"id": 1, "title": "Porto Architecture"}]
    
    @post("/")
    async def create_book(self, data: BookDTO) -> Dict[str, Any]:
        """Создание новой книги"""
        return {"id": 2, "title": data.title}

app = Litestar(
    route_handlers=[BookController],
    debug=True
)
```

### 📚 Документация
- [Официальная документация](https://docs.litestar.dev/)
- [GitHub репозиторий](https://github.com/litestar-org/litestar)
- [Примеры](https://github.com/litestar-org/litestar/tree/main/examples)

---

## 🗄️ Piccolo ORM

### 📖 Описание
**Piccolo** - современный, асинхронный ORM и миграционный инструмент для Python, с отличной поддержкой типов.

### ✨ Ключевые особенности
- 🔄 **Async/await** - нативная поддержка асинхронности
- 📝 **Type hints** - полная типизация
- 🔧 **Миграции** - автоматические и ручные миграции
- 🎨 **Query builder** - удобный конструктор запросов
- 🖥️ **Admin panel** - встроенная админка
- 🗄️ **Multiple DBs** - PostgreSQL, SQLite, CockroachDB

### 💻 Пример использования

```python
from piccolo.table import Table
from piccolo.columns import Varchar, Integer, Boolean, Timestamp
from datetime import datetime

class Book(Table):
    """Модель книги"""
    title = Varchar(length=255)
    author = Varchar(length=100)
    pages = Integer()
    is_available = Boolean(default=True)
    created_at = Timestamp(default=datetime.now)
    
    # Методы запросов
    @classmethod
    async def get_available(cls):
        return await cls.select().where(cls.is_available == True)
    
    @classmethod
    async def find_by_author(cls, author: str):
        return await cls.select().where(cls.author.ilike(f"%{author}%"))

# Использование
book = Book(title="Clean Code", author="Robert Martin")
await book.save()

# Запросы
available_books = await Book.get_available()
martin_books = await Book.find_by_author("Martin")
```

### 🔧 Миграции

```bash
# Создание миграции
piccolo migrations new book_app --auto

# Применение миграций
piccolo migrations forwards book_app

# Откат миграций
piccolo migrations backwards book_app 1
```

### 📚 Документация
- [Официальная документация](https://piccolo-orm.readthedocs.io/)
- [GitHub репозиторий](https://github.com/piccolo-orm/piccolo)
- [Piccolo Admin](https://github.com/piccolo-orm/piccolo_admin)

---

## 💉 Dishka - Dependency Injection

### 📖 Описание
**Dishka** - мощный и гибкий DI-контейнер для Python с поддержкой асинхронности.

### ✨ Ключевые особенности
- 🔄 **Async support** - полная поддержка async/await
- 📦 **Scopes** - управление жизненным циклом объектов
- 🔌 **Интеграции** - готовые интеграции с фреймворками
- 🎯 **Type safe** - типобезопасность
- 🏗️ **Factories** - фабрики и провайдеры

### 💻 Пример использования

```python
from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.litestar import DishkaPlugin

class DatabaseProvider(Provider):
    """Провайдер базы данных"""
    
    @provide(scope=Scope.APP)
    async def get_database(self) -> Database:
        """Singleton подключение к БД"""
        return Database(url="sqlite:///app.db")
    
    @provide(scope=Scope.REQUEST)
    async def get_session(self, db: Database) -> Session:
        """Сессия на каждый запрос"""
        return db.create_session()

class ServiceProvider(Provider):
    """Провайдер сервисов"""
    
    @provide(scope=Scope.REQUEST)
    def book_repository(self, session: Session) -> BookRepository:
        return BookRepository(session)
    
    @provide(scope=Scope.REQUEST)
    def book_service(self, repo: BookRepository) -> BookService:
        return BookService(repo)

# Создание контейнера
container = make_async_container(
    DatabaseProvider(),
    ServiceProvider()
)

# Интеграция с Litestar
app = Litestar(
    plugins=[DishkaPlugin(container)]
)
```

### 🔄 Scopes (Области видимости)

| Scope | Описание | Использование |
|-------|----------|---------------|
| `APP` | Singleton на всё приложение | БД, конфиги, клиенты |
| `REQUEST` | Новый на каждый запрос | Репозитории, сервисы |
| `STEP` | Новый на каждый шаг | Временные объекты |

### 📚 Документация
- [GitHub репозиторий](https://github.com/reagento/dishka)
- [Примеры использования](https://github.com/reagento/dishka/tree/main/examples)

---

## 📨 FastStream

### 📖 Описание
**FastStream** - фреймворк для работы с message brokers (RabbitMQ, Kafka, Redis) в асинхронном стиле.

### ✨ Ключевые особенности
- 🐰 **Multiple brokers** - RabbitMQ, Kafka, Redis, NATS
- 🔄 **Async** - полностью асинхронный
- 📝 **Type hints** - типизация сообщений
- 🧪 **Testing** - встроенные инструменты тестирования
- 📚 **Documentation** - автогенерация AsyncAPI

### 💻 Пример использования

```python
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from pydantic import BaseModel

# Создание брокера
broker = RabbitBroker("amqp://guest:guest@localhost/")
app = FastStream(broker)

# Модель сообщения
class BookCreatedEvent(BaseModel):
    book_id: int
    title: str
    author: str

# Обработчик сообщений
@broker.subscriber("book.created")
async def handle_book_created(event: BookCreatedEvent):
    """Обработка события создания книги"""
    print(f"New book created: {event.title} by {event.author}")
    
    # Отправка уведомления
    await broker.publish(
        {"message": f"Book {event.title} is now available"},
        queue="notifications"
    )

# Публикация сообщения
@broker.publisher("book.created")
async def publish_book_created(book: Book) -> BookCreatedEvent:
    return BookCreatedEvent(
        book_id=book.id,
        title=book.title,
        author=book.author
    )
```

### 🔄 Интеграция с Porto

```python
# src/Containers/AppSection/Book/Events/BookEventHandler.py
from faststream.rabbit import RabbitRouter
from src.Ship.Parents.EventHandler import EventHandler

router = RabbitRouter()

class BookEventHandler(EventHandler):
    """Обработчик событий книг"""
    
    @router.subscriber("books.created")
    async def on_book_created(self, event: BookCreatedEvent):
        # Вызов Action для обработки
        await self.notify_action.run(event)
    
    @router.subscriber("books.borrowed")
    async def on_book_borrowed(self, event: BookBorrowedEvent):
        # Обновление статистики
        await self.stats_action.run(event)
```

### 📚 Документация
- [Официальная документация](https://faststream.airt.ai/)
- [GitHub репозиторий](https://github.com/airtai/faststream)
- [Примеры](https://github.com/airtai/faststream/tree/main/examples)

---

## 📊 Logfire

### 📖 Описание
**Logfire** - современная система observability от создателей Pydantic, предоставляющая логирование, трейсинг и метрики.

### ✨ Ключевые особенности
- 🔍 **Auto-instrumentation** - автоматический трейсинг
- 📊 **Rich UI** - красивый веб-интерфейс
- 🔗 **Distributed tracing** - распределённый трейсинг
- 📈 **Metrics** - сбор метрик
- 🚨 **Alerts** - система алертов
- 🔌 **Integrations** - интеграции с популярными библиотеками

### 💻 Пример использования

```python
import logfire
from src.Ship.Configs import settings

# Конфигурация
logfire.configure(
    token=settings.logfire_token,
    project_name="porto-template",
    environment=settings.app_env,
)

# Auto-instrumentation
logfire.install_auto_tracing(
    modules=["src.Containers", "src.Ship"],
    min_duration=0.01,  # Трейсить функции > 10ms
)

# Использование в коде
class CreateBookAction:
    async def run(self, data: BookDTO) -> Book:
        with logfire.span("create_book", book_title=data.title):
            # Логирование
            logfire.info("Creating new book", data=data.dict())
            
            # Выполнение операций
            book = await self.create_task.run(data)
            
            # Метрики
            logfire.metric("books.created", 1)
            
            # Структурированное логирование
            logfire.info(
                "Book created successfully",
                book_id=book.id,
                title=book.title,
                duration=logfire.duration()
            )
            
            return book
```

### 📊 Трейсинг

```python
# Автоматический трейсинг методов
@logfire.instrument("validate_book_data")
async def validate_book(data: BookDTO) -> None:
    """Валидация данных книги"""
    if not data.isbn:
        logfire.warning("Missing ISBN", book_title=data.title)
        raise ValidationError("ISBN is required")

# Вложенные spans
async def complex_operation():
    with logfire.span("complex_operation") as span:
        with span.span("step_1"):
            await do_step_1()
        
        with span.span("step_2"):
            await do_step_2()
```

### 📚 Документация
- [Официальная документация](https://logfire.pydantic.dev/)
- [GitHub репозиторий](https://github.com/pydantic/logfire)
- [Cookbook](https://logfire.pydantic.dev/docs/cookbook/)

---

## 🐳 Docker & Docker Compose

### 📖 Описание
Контейнеризация приложения для простого развёртывания и масштабирования.

### 📄 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY pyproject.toml .
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY src/ ./src/
COPY piccolo_conf.py .
COPY .env .

# Создание директории для данных
RUN mkdir -p /app/data

# Запуск приложения
CMD ["python", "-m", "src.Bootstrap"]
```

### 🐳 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    container_name: porto-app
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DATABASE_URL=sqlite:///data/app.db
      - LOGFIRE_TOKEN=${LOGFIRE_TOKEN}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - rabbitmq
      - redis
    restart: unless-stopped

  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: porto-rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=admin
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq

  redis:
    image: redis:7-alpine
    container_name: porto-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  rabbitmq_data:
  redis_data:
```

---

## 📦 Дополнительные библиотеки

### 🔐 Безопасность
- **passlib** - хеширование паролей
- **python-jose** - JWT токены
- **cryptography** - шифрование

### ✅ Валидация
- **pydantic** - валидация данных
- **email-validator** - валидация email
- **phonenumbers** - валидация телефонов

### 🧪 Тестирование
- **pytest** - фреймворк тестирования
- **pytest-asyncio** - async тесты
- **httpx** - HTTP клиент для тестов
- **faker** - генерация тестовых данных

### 🛠️ Утилиты
- **python-dotenv** - загрузка .env файлов
- **rich** - красивый вывод в консоль
- **typer** - CLI интерфейс
- **uvloop** - быстрый event loop

## 📊 Сравнение с альтернативами

### Web Frameworks

| Фреймворк | Производительность | Async | Type Hints | DI Support | Porto Ready |
|-----------|-------------------|-------|------------|------------|-------------|
| **Litestar** | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ✅ | ✅ |
| FastAPI | ⭐⭐⭐⭐ | ✅ | ✅ | ⚠️ | ✅ |
| Django | ⭐⭐⭐ | ⚠️ | ⚠️ | ❌ | ⚠️ |
| Flask | ⭐⭐ | ❌ | ⚠️ | ❌ | ⚠️ |

### ORMs

| ORM | Async | Migrations | Type Hints | Performance | Porto Ready |
|-----|-------|------------|------------|-------------|-------------|
| **Piccolo** | ✅ | ✅ | ✅ | ⭐⭐⭐⭐⭐ | ✅ |
| SQLAlchemy | ⚠️ | ✅ | ⚠️ | ⭐⭐⭐⭐ | ✅ |
| Tortoise | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ | ✅ |
| Django ORM | ❌ | ✅ | ⚠️ | ⭐⭐⭐ | ⚠️ |

## 🚀 Установка всех зависимостей

### Через pip

```bash
pip install litestar[standard]
pip install piccolo[sqlite]
pip install dishka
pip install faststream[rabbit]
pip install logfire
pip install pydantic
pip install python-dotenv
```

### Через pyproject.toml

```toml
[project]
name = "porto-template"
version = "0.1.0"
dependencies = [
    "litestar[standard]>=2.0.0",
    "piccolo[sqlite]>=1.0.0",
    "dishka>=1.0.0",
    "faststream[rabbit]>=0.3.0",
    "logfire>=0.1.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
    "faker>=18.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

## 📚 Следующие шаги

1. [**Начало работы**](07-getting-started.md) - установка и запуск проекта
2. [**Best Practices**](08-best-practices.md) - лучшие практики использования
3. [**API Reference**](09-api-reference.md) - справочник по API

---

<div align="center">

**🛠️ Modern Stack for Modern Architecture!**

[← Примеры](05-examples.md) | [Начало работы →](07-getting-started.md)

</div>
