# 🏛️ Архитектура Porto - Детальное описание

## 📐 Архитектурные слои

Porto организует код в **два основных слоя**, каждый со своей ответственностью:

```mermaid
graph TB
    subgraph "Application Layer"
        subgraph "📦 Containers Layer"
            subgraph "AppSection"
                UC["👤 User Container"]
                BC["📚 Book Container"]
                OC["🛒 Order Container"]
            end
            subgraph "VendorSection"
                PC["💳 Payment Container"]
                NC["📧 Notification Container"]
            end
        end
    end
    
    subgraph "Infrastructure Layer"
        subgraph "🚢 Ship Layer"
            SB["⚓ Ship Base<br/>Parents, Abstracts"]
            SC["⚙️ Ship Core<br/>Database, Logging"]
            SP["🔌 Ship Providers<br/>DI, Registration"]
            SM["🛡️ Ship Middleware<br/>Auth, CORS, etc."]
        end
    end
    
    subgraph "🌊 Framework Layer"
        FL["Litestar, Piccolo, Dishka, Logfire"]
    end
    
    UC --> SB
    BC --> SB
    OC --> SB
    PC --> SB
    NC --> SB
    
    SB --> SC
    SC --> SP
    SP --> SM
    SM --> FL
    
    style UC fill:#ffd4a3,stroke:#333,stroke-width:2px
    style BC fill:#ffd4a3,stroke:#333,stroke-width:2px
    style OC fill:#ffd4a3,stroke:#333,stroke-width:2px
    style PC fill:#ffe4a3,stroke:#333,stroke-width:2px
    style NC fill:#ffe4a3,stroke:#333,stroke-width:2px
    style SB fill:#a3d4ff,stroke:#333,stroke-width:2px
    style SC fill:#a3d4ff,stroke:#333,stroke-width:2px
    style SP fill:#a3d4ff,stroke:#333,stroke-width:2px
    style SM fill:#a3d4ff,stroke:#333,stroke-width:2px
    style FL fill:#a3ffa3,stroke:#333,stroke-width:2px
```

## 📦 Containers Layer (Слой контейнеров)

### 🎯 Назначение
Containers Layer содержит всю **бизнес-логику** приложения. Каждый контейнер - это независимый модуль, инкапсулирующий определённую функциональность.

### 📂 Структура контейнера

```
📦 Book/                        # Контейнер управления книгами
├── 📁 Actions/                 # Бизнес-операции
│   ├── CreateBookAction.py    # Создание книги
│   ├── UpdateBookAction.py    # Обновление книги
│   └── DeleteBookAction.py    # Удаление книги
├── 📁 Tasks/                   # Атомарные задачи
│   ├── CreateBookTask.py      # Задача создания
│   ├── FindBookTask.py        # Задача поиска
│   └── ValidateBookTask.py    # Задача валидации
├── 📁 Models/                  # Модели данных
│   └── Book.py                # Модель книги
├── 📁 UI/                      # Пользовательский интерфейс
│   ├── 📁 API/                # REST API
│   │   ├── Controllers/       # Контроллеры
│   │   ├── Routes/           # Маршруты
│   │   └── Transformers/     # Трансформеры данных
│   ├── 📁 CLI/               # Командная строка
│   └── 📁 Web/               # Веб-интерфейс
├── 📁 Data/                   # DTO и схемы
├── 📁 Exceptions/             # Исключения контейнера
├── 📁 Managers/               # Менеджеры и сервисы
└── Providers.py              # DI провайдеры
```

### 🔄 Sections (Секции)

Контейнеры группируются в **секции** для логической организации:

- **AppSection** - основная бизнес-логика приложения
- **VendorSection** - интеграции с внешними сервисами

```mermaid
graph LR
    subgraph "AppSection"
        A1["User"]
        A2["Book"]
        A3["Order"]
    end
    
    subgraph "VendorSection"
        V1["Payment"]
        V2["Email"]
        V3["SMS"]
    end
    
    A3 --> V1
    A1 --> V2
    A1 --> V3
    
    style A1 fill:#ccffcc,stroke:#333,stroke-width:2px
    style A2 fill:#ccffcc,stroke:#333,stroke-width:2px
    style A3 fill:#ccffcc,stroke:#333,stroke-width:2px
    style V1 fill:#ffcccc,stroke:#333,stroke-width:2px
    style V2 fill:#ffcccc,stroke:#333,stroke-width:2px
    style V3 fill:#ffcccc,stroke:#333,stroke-width:2px
```

## 🚢 Ship Layer (Слой корабля)

### 🎯 Назначение
Ship Layer содержит **инфраструктурный код**, общий для всех контейнеров. Он изолирует бизнес-логику от деталей фреймворка.

### 📂 Структура Ship

```
🚢 Ship/
├── 📁 Parents/              # Базовые классы
│   ├── Action.py           # Базовый Action
│   ├── Task.py            # Базовый Task
│   ├── Model.py           # Базовая Model
│   ├── Controller.py      # Базовый Controller
│   └── Repository.py      # Базовый Repository
├── 📁 Core/                # Ядро системы
│   ├── Database.py        # Подключение к БД
│   ├── Logging.py         # Логирование
│   └── Cache.py          # Кеширование
├── 📁 Configs/            # Конфигурации
│   └── App.py            # Настройки приложения
├── 📁 Providers/          # DI провайдеры
│   └── App.py            # Главный провайдер
├── 📁 Middleware/         # Middleware
│   ├── Auth.py           # Аутентификация
│   └── CORS.py           # CORS
├── 📁 Exceptions/         # Обработчики исключений
├── 📁 Commands/           # CLI команды
└── App.py                 # Фабрика приложения
```

### 🔧 Компоненты Ship Layer

```mermaid
graph TD
    subgraph "Ship Components"
        P["📋 Parents<br/>Base Classes"]
        C["⚙️ Core<br/>Infrastructure"]
        PR["🔌 Providers<br/>DI Container"]
        M["🛡️ Middleware<br/>Request Pipeline"]
        E["⚠️ Exceptions<br/>Error Handling"]
        CM["🖥️ Commands<br/>CLI Tools"]
    end
    
    P --> C
    C --> PR
    PR --> M
    M --> E
    E --> CM
    
    style P fill:#e6f2ff,stroke:#333,stroke-width:2px
    style C fill:#e6f2ff,stroke:#333,stroke-width:2px
    style PR fill:#e6f2ff,stroke:#333,stroke-width:2px
    style M fill:#e6f2ff,stroke:#333,stroke-width:2px
    style E fill:#e6f2ff,stroke:#333,stroke-width:2px
    style CM fill:#e6f2ff,stroke:#333,stroke-width:2px
```

## 🔄 Поток данных (Data Flow)

### 📥 Входящий запрос

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant M as Middleware
    participant CT as Controller
    participant A as Action
    participant T as Task
    participant DB as Database
    
    C->>R: HTTP Request
    R->>M: Route Match
    M->>M: Auth, CORS, etc.
    M->>CT: Validated Request
    CT->>A: Call Action
    A->>T: Execute Tasks
    T->>DB: Query/Update
    DB-->>T: Result
    T-->>A: Task Result
    A-->>CT: Action Result
    CT-->>C: HTTP Response
```

### 🎯 Action-Task взаимодействие

```mermaid
graph TD
    subgraph "CreateOrderAction"
        A["🎯 Action Entry"]
        T1["✅ ValidateOrderTask"]
        T2["💰 CalculatePriceTask"]
        T3["📦 CreateOrderTask"]
        T4["💳 ProcessPaymentTask"]
        T5["📧 SendEmailTask"]
        
        A --> T1
        T1 --> T2
        T2 --> T3
        T3 --> T4
        T4 --> T5
    end
    
    style A fill:#ffcccc,stroke:#333,stroke-width:3px
    style T1 fill:#ccffcc,stroke:#333,stroke-width:2px
    style T2 fill:#ccffcc,stroke:#333,stroke-width:2px
    style T3 fill:#ccffcc,stroke:#333,stroke-width:2px
    style T4 fill:#ccffcc,stroke:#333,stroke-width:2px
    style T5 fill:#ccffcc,stroke:#333,stroke-width:2px
```

## 🎨 Компоненты Porto

### 🎯 Main Components (Основные компоненты)

#### 1. Actions
**Назначение**: Orchestration слой, координирует выполнение Tasks

```python
class CreateBookAction(Action):
    """Создание новой книги"""
    
    def __init__(self, 
                 validate_task: ValidateBookTask,
                 create_task: CreateBookTask,
                 notify_task: NotifyTask):
        self.validate = validate_task
        self.create = create_task
        self.notify = notify_task
    
    async def run(self, data: BookDTO) -> Book:
        # 1. Валидация
        await self.validate.run(data)
        # 2. Создание
        book = await self.create.run(data)
        # 3. Уведомление
        await self.notify.run(book)
        return book
```

#### 2. Tasks
**Назначение**: Атомарные операции с единой ответственностью

```python
class CreateBookTask(Task):
    """Создание книги в БД"""
    
    async def run(self, data: BookDTO) -> Book:
        return await Book.insert(
            title=data.title,
            author=data.author,
            isbn=data.isbn
        )
```

#### 3. Models
**Назначение**: Представление данных и бизнес-правил

```python
class Book(Model, table=True):
    """Модель книги"""
    
    id: int = Integer(primary_key=True)
    title: str = Varchar(length=255)
    author: str = Varchar(length=100)
    isbn: str = Varchar(length=13, unique=True)
    created_at: datetime = Timestamp()
    
    def is_available(self) -> bool:
        """Бизнес-логика проверки доступности"""
        return not self.is_borrowed
```

#### 4. Controllers
**Назначение**: Обработка HTTP запросов

```python
class BookController(Controller):
    """Контроллер книг"""
    
    @post("/books")
    async def create(self, 
                     data: BookDTO,
                     action: CreateBookAction) -> Book:
        """Создание книги"""
        return await action.run(data)
```

### 🔧 Optional Components (Опциональные компоненты)

- **Repositories** - абстракция доступа к данным
- **Transformers** - преобразование данных для API
- **Validators** - валидация данных
- **Services** - внешние сервисы
- **Events** - обработка событий
- **Jobs** - фоновые задачи

## 🏗️ Принципы проектирования

### 1. Single Responsibility Principle (SRP)
Каждый компонент имеет одну причину для изменения:

```mermaid
graph LR
    subgraph "❌ Нарушение SRP"
        B1["UserService<br/>• Create User<br/>• Send Email<br/>• Log Activity<br/>• Validate Data"]
    end
    
    subgraph "✅ Следование SRP"
        G1["CreateUserTask"]
        G2["SendEmailTask"]
        G3["LogActivityTask"]
        G4["ValidateTask"]
    end
    
    style B1 fill:#ffcccc,stroke:#333,stroke-width:2px
    style G1 fill:#ccffcc,stroke:#333,stroke-width:2px
    style G2 fill:#ccffcc,stroke:#333,stroke-width:2px
    style G3 fill:#ccffcc,stroke:#333,stroke-width:2px
    style G4 fill:#ccffcc,stroke:#333,stroke-width:2px
```

### 2. Dependency Inversion Principle (DIP)
Зависимость от абстракций, а не от конкретных реализаций:

```python
# Ship/Parents/Repository.py
class Repository(ABC):
    @abstractmethod
    async def find(self, id: int): ...
    
    @abstractmethod
    async def save(self, entity): ...

# Containers/Book/Repositories/BookRepository.py
class BookRepository(Repository):
    async def find(self, id: int) -> Book:
        return await Book.objects.get(id=id)
    
    async def save(self, book: Book) -> Book:
        return await book.save()
```

### 3. Don't Repeat Yourself (DRY)
Переиспользование кода через наследование и композицию:

```python
# Ship/Parents/Action.py
class Action(ABC):
    """Базовый класс для всех Actions"""
    
    @abstractmethod
    async def run(self, *args, **kwargs):
        """Главный метод выполнения"""
        pass
    
    async def log(self, message: str):
        """Общий метод логирования"""
        logfire.info(message)
```

## 🔐 Безопасность и изоляция

### Изоляция слоёв
```mermaid
graph TB
    subgraph "External World"
        EW["🌍 Internet"]
    end
    
    subgraph "API Gateway"
        AG["🔒 Security Layer<br/>Rate Limiting, Auth"]
    end
    
    subgraph "Application"
        C["📦 Containers"]
        S["🚢 Ship"]
    end
    
    subgraph "Database"
        DB["💾 Data Layer"]
    end
    
    EW --> AG
    AG --> C
    C --> S
    S --> DB
    
    style EW fill:#ffcccc,stroke:#333,stroke-width:2px
    style AG fill:#ffffcc,stroke:#333,stroke-width:2px
    style C fill:#ccffcc,stroke:#333,stroke-width:2px
    style S fill:#ccccff,stroke:#333,stroke-width:2px
    style DB fill:#ffccff,stroke:#333,stroke-width:2px
```

## 📊 Масштабирование

### От монолита к микросервисам

```mermaid
graph TD
    subgraph "Phase 1: Monolith"
        M["All Containers<br/>in One App"]
    end
    
    subgraph "Phase 2: Service Separation"
        S1["User Service"]
        S2["Book Service"]
        S3["Order Service"]
        MQ["Message Queue"]
        
        S1 <--> MQ
        S2 <--> MQ
        S3 <--> MQ
    end
    
    subgraph "Phase 3: Full Microservices"
        MS1["User μService<br/>+ DB"]
        MS2["Book μService<br/>+ DB"]
        MS3["Order μService<br/>+ DB"]
        GW["API Gateway"]
        
        GW --> MS1
        GW --> MS2
        GW --> MS3
    end
    
    M --> S1
    M --> S2
    M --> S3
    
    S1 --> MS1
    S2 --> MS2
    S3 --> MS3
```

## 🎯 Преимущества архитектуры

### 📈 Масштабируемость
- Легко добавлять новые контейнеры
- Простое разделение на микросервисы
- Горизонтальное масштабирование

### 🧪 Тестируемость
- Изолированное тестирование компонентов
- Моки и стабы через DI
- Чёткие границы тестирования

### 🔧 Поддерживаемость
- Понятная структура кода
- Легко находить и исправлять баги
- Простое добавление новых функций

### 🚀 Производительность
- Асинхронное выполнение
- Оптимизация на уровне Tasks
- Кеширование результатов

## 📚 Следующие шаги

Изучите детали реализации:

1. [**Структура проекта**](03-project-structure.md) - файловая организация
2. [**Компоненты**](04-components.md) - детали каждого компонента
3. [**Примеры кода**](05-examples.md) - практическая реализация

---

<div align="center">

**🏛️ Porto Architecture - Build Clean, Scale Smart!**

[← Введение](01-introduction.md) | [Структура проекта →](03-project-structure.md)

</div>
