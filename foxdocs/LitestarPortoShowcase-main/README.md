# 🚢 Porto Architecture Template + Spec Kit

> **Современный шаблон для разработки с Porto архитектурой, Litestar, Piccolo ORM, Dishka DI и Logfire observability + интегрированный Spec-Driven Development workflow**

## 🌟 Особенности

### 🏗️ Porto Architecture
- ✅ **Containers/Ship** структура для масштабируемых приложений
- ✅ **Actions/Tasks/Models/UI** компоненты
- ✅ **AppSection/VendorSection** организация
- ✅ **Четкое разделение** бизнес-логики и инфраструктуры

### 🚀 Modern Tech Stack
- **🌐 Litestar** - Современный ASGI фреймворк
- **🗃️ Piccolo ORM** - Async Python ORM с миграциями
- **🔌 Dishka** - Dependency Injection контейнер
- **📊 Logfire** - Observability и трассировка
- **✨ Pydantic** - Валидация данных

### 🌱 Porto Spec Kit Integration
- **📝 Spec-Driven Development** - от идеи до кода через спецификации
- **🤖 ИИ-агенты поддержка** - Claude, Copilot, Gemini
- **📖 Ручное использование** - работа без ИИ через промпты
- **🎯 Porto-адаптированные шаблоны**

## ⚡ Быстрый старт

### 1. Установка зависимостей
```bash
# Рекомендуемый вариант (uv)
uv venv
source .venv/bin/activate
uv pip install -e .

# Альтернатива (pip)
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Настройка базы данных
```bash
# При первом запуске таблицы создаются автоматически (SQLite в ./data/app.db)
# Для продакшена используйте миграции Piccolo
```

### 3. Запуск приложения
```bash
# Рекомендуемый способ
uv run python run.py

# Альтернативы
python -m src.Bootstrap   # с авто-трейсингом Logfire
python -m src.Main        # dev, reload в коде

# API документация: http://localhost:8000/api/docs
```

### 4. Создание первой фичи с Porto Spec Kit

**С ИИ-агентом:**
```bash
/specify Система управления профилями пользователей с загрузкой аватаров
/plan Использовать Piccolo для Profile модели, Litestar для API, добавить file upload
/tasks
```

**Без ИИ (вручную):**
```bash
# Создание спецификации
./spec-kit/scripts/create-new-feature-porto.sh "Система управления профилями пользователей"

# Заполнение шаблонов
# 1. Откройте specs/001-sistema-upravleniya-profilyami/spec.md
# 2. Заполните по инструкциям в spec-kit/docs/manual-usage.md
```

## 📁 Структура проекта

```
template/
├── 📁 src/                          # Исходный код Porto приложения
│   ├── 📁 Containers/              # Бизнес-логика (Porto Containers)
│   │   ├── 📁 AppSection/         # Основные модули
│   │   │   ├── 📦 Book/           # Управление книгами
│   │   │   └── 📦 User/           # Управление пользователями
│   │   └── 📁 VendorSection/      # Внешние интеграции
│   │       ├── 📦 Payment/        # Платежи
│   │       └── 📦 Notification/   # Уведомления
│   ├── 📁 Ship/                   # Инфраструктура (Porto Ship)
│   │   ├── 📁 Parents/           # Базовые классы
│   │   ├── 📁 Core/              # Ядро системы
│   │   ├── 📁 Providers/         # DI провайдеры
│   │   └── 📁 Configs/           # Конфигурации
│   ├── 📄 Bootstrap.py            # Точка входа с auto-tracing
│   └── 📄 Main.py                # Альтернативная точка входа
├── 📁 spec-kit/                   # Porto Spec Kit
│   ├── 📁 templates/             # Porto-адаптированные шаблоны
│   ├── 📁 scripts/               # Вспомогательные скрипты
│   ├── 📁 docs/                  # Документация Spec Kit
│   ├── 📁 memory/                # Конституция Porto
│   └── 📁 examples/              # Примеры использования
├── 📁 specs/                     # Спецификации фич (создается автоматически)
├── 📁 docs/                      # Документация Porto Architecture
├── 📁 data/                      # SQLite база данных
├── 📄 piccolo_conf.py            # Конфигурация Piccolo ORM
├── 📄 pyproject.toml             # Зависимости и настройки
└── 📄 .cursor/rules/             # Настройки для Cursor IDE
```

## 🎯 Porto Spec Kit - Spec-Driven Development

### 📝 Workflow
```mermaid
graph LR
    A[📝 Specify] --> B[🎯 Plan]  
    B --> C[⚡ Tasks]
    C --> D[🚀 Implement]
    D --> E[✅ Validate]
    
    style A fill:#ffd4a3
    style B fill:#a3d4ff  
    style C fill:#a3ffa3
    style D fill:#ffcccc
    style E fill:#ccffcc
```

### 🤖 Команды для ИИ-агентов
- **`/specify [описание]`** - Создание спецификации фичи
- **`/plan [технические детали]`** - Планирование реализации
- **`/tasks`** - Генерация списка задач

### 📖 Ручное использование
Полное руководство: [spec-kit/docs/manual-usage.md](spec-kit/docs/manual-usage.md)

## 🏗️ Porto Architecture

### 📦 Containers (Бизнес-логика)
```python
# Пример Action
class CreateBookAction(Action[BookCreateDTO, BookDTO]):
    def __init__(self, create_task: CreateBookTask, transformer: BookTransformer):
        self.create_task = create_task
        self.transformer = transformer
    
    async def run(self, data: BookCreateDTO) -> BookDTO:
        book = await self.create_task.run(data)
        return self.transformer.transform(book)

# Пример Task
class CreateBookTask(Task[BookCreateDTO, Book]):
    def __init__(self, repository: BookRepository):
        self.repository = repository
    
    async def run(self, data: BookCreateDTO) -> Book:
        return await self.repository.create(data.model_dump())
```

### 🚢 Ship (Инфраструктура)
```python
# Базовые классы в Ship/Parents/
class Action(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    async def run(self, data: InputT) -> OutputT: ...

class Task(ABC, Generic[InputT, OutputT]):
    @abstractmethod
    async def run(self, data: InputT) -> OutputT: ...
```

### 🔌 Dependency Injection с Dishka
```python
# Container/Providers.py
class BookProvider(Provider):
    scope = Scope.REQUEST
    
    repository = provide(BookRepository)
    create_task = provide(CreateBookTask)
    create_action = provide(CreateBookAction)
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты
pytest

# С покрытием
pytest --cov=src

# Только интеграционные
pytest tests/integration/

# Только unit тесты
pytest tests/unit/
```

### TDD с Porto Spec Kit
```python
# Сначала тесты
def test_create_book_action():
    action = CreateBookAction(create_task, transformer)
    result = await action.run(book_data)
    assert result.title == "Test Book"

# Потом реализация
class CreateBookAction(Action[BookCreateDTO, BookDTO]):
    async def run(self, data: BookCreateDTO) -> BookDTO:
        # Реализация после написания тестов
        pass
```

## 📊 Observability с Logfire

### Автоматическая трассировка
```python
# Actions автоматически трассируются
with logfire.span("🚀 CreateBookAction"):
    result = await action.run(data)
```

### Просмотр логов
```bash
# Логи в консоли и Logfire dashboard
python src/Bootstrap.py
# Откройте https://logfire.pydantic.dev для просмотра трейсов
```

## 🚀 Production Deployment

### Docker
```bash
# Сборка образа
docker build -t porto-app .

# Запуск docker-compose
docker-compose up -d
```

### Environment Variables
```bash
# .env
APP_NAME="Porto Application"
APP_DEBUG=false
DATABASE_URL="postgresql://user:pass@localhost/db"
LOGFIRE_TOKEN="your-token"
```

## 📚 Документация

### Porto Architecture
- [🚀 Введение](docs/01-introduction.md)
- [🏛️ Архитектура](docs/02-architecture.md)  
- [📁 Структура проекта](docs/03-project-structure.md)
- [🧩 Компоненты](docs/04-components.md)

### Porto Spec Kit
- [🚀 Начало работы](spec-kit/docs/getting-started.md)
- [📖 Работа без ИИ](spec-kit/docs/manual-usage.md)
- [📋 Конституция Porto](spec-kit/memory/constitution-porto.md)
- [📦 Пример Order Management](spec-kit/examples/order-management/)

## 🤝 Примеры использования

### Создание Container'а
```bash
# 1. Спецификация
/specify Система отзывов на книги с рейтингами

# 2. Планирование  
/plan Создать Review Container в AppSection, связать с Book и User

# 3. Генерация задач
/tasks

# 4. Реализация по задачам из specs/###-reviews/tasks.md
```

### Интеграция с внешними сервисами
```bash
# VendorSection для внешних интеграций
/specify Интеграция с Stripe для обработки платежей

# Результат: VendorSection.Payment Container
```

## 🔧 Настройка IDE

### Cursor IDE
Правила автоматически настроены в `.cursor/rules/porto-spec-kit.md`

### VS Code
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.ruffEnabled": true,
  "files.associations": {
    "*.md": "markdown"
  }
}
```

## 📈 Преимущества

### 🚀 Скорость разработки
- **Spec-Driven**: От идеи до кода за минуты
- **Готовые шаблоны**: Porto компоненты из коробки
- **ИИ-интеграция**: Автоматизация рутинных задач

### 🏗️ Архитектурная чистота
- **Четкие границы**: Containers vs Ship
- **Переиспользование**: Tasks между Actions
- **Тестируемость**: Каждый компонент изолирован

### 📊 Observability
- **Автоматическая трассировка**: Logfire из коробки
- **Structured logging**: Контекстные логи
- **Performance monitoring**: Метрики производительности

## 🆘 Поддержка

- 📖 **Документация**: `docs/` и `spec-kit/docs/`
- 🎯 **Примеры**: `spec-kit/examples/`
- 🏗️ **Шаблоны**: `spec-kit/templates/`
- 📜 **Конституция**: `spec-kit/memory/constitution-porto.md`

## 📄 Лицензия

MIT License

---

<div align="center">

**🚢 Porto Architecture + 🌱 Spec Kit = 🚀 Productive Development**

*Создано для эффективной разработки с ИИ и без него*

</div>