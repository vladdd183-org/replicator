# 🚀 Начало работы с Porto Template

## 📋 Требования

### Системные требования
- **Python** 3.11 или выше
- **SQLite** 3.35+ (обычно уже установлен)
- **Git** для клонирования репозитория
- **Docker** (опционально) для контейнеризации

### Рекомендуемое окружение
- **OS**: Linux, macOS, Windows (WSL2)
- **RAM**: минимум 2GB
- **IDE**: VS Code, PyCharm, Cursor

## 🎯 Быстрый старт

### 1️⃣ Клонирование репозитория

```bash
# Клонирование репозитория
git clone https://github.com/your-org/porto-template.git
cd porto-template

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2️⃣ Установка зависимостей

В проекте используется `uv` (быстрый менеджер пакетов) и `pyproject.toml`.

```bash
# Вариант A: uv (рекомендуется)
uv venv
source .venv/bin/activate
uv pip install -e .

# Вариант B: стандартный venv + pip
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 3️⃣ Настройка окружения

```bash
# Копирование примера конфигурации
cp env.example .env

# Редактирование .env файла
nano .env  # или используйте любой редактор
```

#### 📝 Пример .env файла

```env
# Application Settings
APP_NAME="Porto Template"
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# Database
DATABASE_URL=sqlite:///data/app.db

# Logfire (Optional)
LOGFIRE_TOKEN=your-token-here
LOGFIRE_PROJECT_NAME=porto-template

# RabbitMQ (Optional)
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=3600

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

### 4️⃣ Инициализация базы данных

```bash
# Создание директории для данных
mkdir -p data

# Таблицы создаются автоматически при первом запуске
# (см. src/Main.py и src/Bootstrap.py → setup_database)
# Для прод-окружений используйте полноценные миграции Piccolo
uv run python -m src.Main  # создаст директорию data и базу, затем можно остановить
```

### 5️⃣ Запуск приложения

#### Вариант 1: Через uv (рекомендуется)

```bash
# Основной старт (горячая перезагрузка в development конфигурации)
uv run python run.py
```

#### Вариант 2: Прямой запуск модулей

```bash
# С авто-трейсингом Logfire
python -m src.Bootstrap

# Без авто-трейсинга (dev-режим с reload в коде src/Main.py)
python -m src.Main
```

#### Вариант 3: Через Makefile

```bash
# Запуск в режиме разработки
make dev

# Запуск в production
make run

# Запуск тестов
make test
```

### 6️⃣ Проверка работы

```bash
# OpenAPI доступна по пути, заданному в фабрике приложения
# (см. src/Ship/App.py → OpenAPIConfig.path = "/api/docs")

# Открыть документацию (Scalar UI)
xdg-open http://localhost:8000/api/docs || true
```

## 🐳 Docker запуск

### Использование Docker Compose

```bash
# Сборка и запуск приложения
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d

# Просмотр логов
docker-compose logs -f app

# Остановка сервисов
docker-compose down
```

### Только приложение в Docker (без compose)

```bash
# Сборка образа
docker build -t porto-litestar .

# Запуск контейнера
docker run -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  -e APP_ENV=development \
  porto-litestar
```

## 📁 Структура проекта после установки

```
porto-template/
├── 📁 src/                    # Исходный код
│   ├── 📁 Containers/         # Бизнес-логика
│   │   ├── 📁 AppSection/    # Основные модули
│   │   └── 📁 VendorSection/ # Внешние интеграции
│   ├── 📁 Ship/              # Инфраструктура
│   ├── 📄 Bootstrap.py       # Точка входа с трейсингом
│   └── 📄 Main.py           # Альтернативная точка входа
├── 📁 data/                  # База данных SQLite
│   └── 📄 app.db            # Файл БД (создаётся автоматически)
├── 📁 docs/                  # Документация
├── 📁 tests/                 # Тесты
├── 📄 .env                   # Конфигурация (создать из .env.example)
├── 📄 docker-compose.yml     # Docker конфигурация
├── 📄 Makefile              # Команды автоматизации
└── 📄 pyproject.toml        # Зависимости проекта
```

## 🧪 Запуск тестов

```bash
# Запуск всех тестов
pytest

# Запуск с покрытием
pytest --cov=src --cov-report=html

# Запуск конкретного теста
pytest tests/Containers/Book/test_actions.py

# Запуск с подробным выводом
pytest -v -s

# Запуск только unit тестов
pytest -m unit

# Запуск только integration тестов
pytest -m integration
```

## 🔧 Настройка IDE

### VS Code

```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    "venv": true
  }
}
```

### PyCharm

1. Откройте проект в PyCharm
2. Настройте интерпретатор: `Settings → Project → Python Interpreter`
3. Выберите виртуальное окружение `venv`
4. Настройте пути: `Settings → Project → Project Structure`
5. Добавьте `src` как Source Root

## 📊 Мониторинг с Logfire

### Настройка Logfire

1. Зарегистрируйтесь на [logfire.pydantic.dev](https://logfire.pydantic.dev)
2. Создайте проект
3. Получите токен
4. Добавьте в `.env`:

```env
LOGFIRE_TOKEN=your-logfire-token
LOGFIRE_PROJECT_NAME=your-project-name
```

### Просмотр метрик

```python
# Автоматический трейсинг включён в Bootstrap.py
# Все вызовы Actions и Tasks автоматически логируются

# Ручное логирование
import logfire

logfire.info("Application started", version="1.0.0")
logfire.metric("requests_total", 1)
```

## 🚦 Первые шаги после установки

### 1. Создайте первый Container

```bash
# Используйте шаблон или создайте вручную
mkdir -p src/Containers/AppSection/Product/{Actions,Tasks,Models,UI/API/Controllers}
```

### 2. Создайте Model

```python
# src/Containers/AppSection/Product/Models/Product.py
from piccolo.table import Table
from piccolo.columns import Varchar, Numeric, Boolean
from src.Ship.Parents.Model import Model

class Product(Model, table=True):
    name = Varchar(length=100)
    price = Numeric(digits=(10, 2))
    is_active = Boolean(default=True)
```

### 3. Создайте Task

```python
# src/Containers/AppSection/Product/Tasks/CreateProductTask.py
from src.Ship.Parents.Task import Task
from src.Containers.AppSection.Product.Models import Product

class CreateProductTask(Task):
    async def run(self, name: str, price: float) -> Product:
        product = Product(name=name, price=price)
        await product.save()
        return product
```

### 4. Создайте Action

```python
# src/Containers/AppSection/Product/Actions/CreateProductAction.py
from src.Ship.Parents.Action import Action
from src.Containers.AppSection.Product.Tasks import CreateProductTask

class CreateProductAction(Action):
    def __init__(self, create_task: CreateProductTask):
        self.create_task = create_task
    
    async def run(self, name: str, price: float) -> Product:
        return await self.create_task.run(name, price)
```

### 5. Создайте Controller

```python
# src/Containers/AppSection/Product/UI/API/Controllers/ProductController.py
from litestar import Controller, post
from src.Ship.Parents.Controller import Controller as BaseController

class ProductController(BaseController):
    path = "/products"
    
    @post("/")
    async def create(self, data: ProductDTO, action: CreateProductAction):
        return await action.run(data.name, data.price)
```

## 🐛 Решение проблем

### Проблема: ModuleNotFoundError

```bash
# Убедитесь, что вы в виртуальном окружении
which python  # должен показать путь к venv

# Переустановите зависимости
pip install -r requirements.txt
```

### Проблема: База данных не создаётся

```bash
# Создайте директорию вручную
mkdir -p data

# Проверьте права доступа
chmod 755 data

# Запустите миграции
piccolo migrations forwards app_section
```

### Проблема: Порт занят

```bash
# Найдите процесс на порту 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Убейте процесс или измените порт в .env
APP_PORT=8001
```

## 📚 Полезные команды

```bash
# Форматирование кода
black src/
ruff check src/ --fix

# Проверка типов
mypy src/

# Генерация requirements.txt из pyproject.toml
pip-compile pyproject.toml

# Обновление зависимостей
pip-compile --upgrade

# Очистка кеша Python
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Создание дампа БД
sqlite3 data/app.db .dump > backup.sql

# Восстановление БД
sqlite3 data/app.db < backup.sql
```

## 🎓 Что дальше?

1. 📖 Изучите [Архитектуру Porto](02-architecture.md)
2. 🧩 Познакомьтесь с [Компонентами](04-components.md)
3. 💡 Посмотрите [Примеры кода](05-examples.md)
4. 🤖 Изучите [AI Development Guide](11-ai-development.md)
5. ✨ Следуйте [Best Practices](08-best-practices.md)

## 🆘 Получение помощи

- 📚 [Документация проекта](README.md)
- 💬 [GitHub Discussions](https://github.com/your-org/porto-template/discussions)
- 🐛 [Issue Tracker](https://github.com/your-org/porto-template/issues)
- 📧 Email: support@porto-template.dev

---

<div align="center">

**🚀 Welcome aboard the Porto ship!**

[← Технологии](06-technologies.md) | [Best Practices →](08-best-practices.md)

</div>
