# 🛠️ Справочник команд Hyper-Porto

> **КРИТИЧЕСКИ ВАЖНО**: Этот проект использует **UV** для управления зависимостями и виртуальным окружением.
> **НИКОГДА** не используй `pip` напрямую. **ВСЕГДА** запускай Python через `uv run`.

---

## 📦 Package Management (UV, НЕ pip!)

### Добавление зависимостей

```bash
# ✅ ПРАВИЛЬНО — используй uv
uv add package-name                    # Добавить зависимость
uv add "package-name>=1.0"             # С версией
uv add --dev pytest                    # Dev зависимость
uv add --dev pytest pytest-asyncio     # Несколько dev зависимостей
uv add --group lint ruff mypy          # Группа зависимостей

# ❌ ЗАПРЕЩЕНО — НЕ используй pip!
pip install package-name               # НЕТ!
pip install -r requirements.txt        # НЕТ!
pip install -e .                       # НЕТ!
```

### Удаление зависимостей

```bash
# ✅ ПРАВИЛЬНО
uv remove package-name                 # Удалить зависимость
uv remove --dev pytest                 # Удалить dev зависимость

# ❌ ЗАПРЕЩЕНО
pip uninstall package-name             # НЕТ!
```

### Синхронизация окружения

```bash
# ✅ ПРАВИЛЬНО
uv sync                                # Синхронизировать все зависимости
uv sync --frozen                       # Без обновления lock файла
uv lock                                # Обновить uv.lock файл
uv lock --upgrade                      # Обновить все зависимости до последних

# ❌ ЗАПРЕЩЕНО
pip freeze > requirements.txt          # НЕТ! uv.lock создаётся автоматически
pip install -r requirements.txt        # НЕТ! Используй uv sync
```

---

## 🐍 Запуск Python (ТОЛЬКО через UV!)

### Запуск скриптов

```bash
# ✅ ПРАВИЛЬНО — uv автоматически активирует окружение
uv run python script.py                # Запуск скрипта
uv run python -m module_name           # Запуск модуля
uv run python -c "print('hello')"      # Inline код

# ❌ ЗАПРЕЩЕНО — НЕ активируй venv вручную!
python script.py                       # НЕТ! Используй uv run
python3 script.py                      # НЕТ!
source .venv/bin/activate              # НЕТ! UV активирует автоматически
. .venv/bin/activate                   # НЕТ!
.venv/bin/python script.py             # НЕТ!
```

### Запуск инструментов

```bash
# ✅ ПРАВИЛЬНО
uv run pytest                          # Тесты
uv run ruff check .                    # Линтер
uv run mypy src/                       # Type checker
uv run black .                         # Форматтер

# ❌ ЗАПРЕЩЕНО
pytest                                 # НЕТ! uv run pytest
ruff check .                           # НЕТ! uv run ruff check .
```

---

## 🏭 Porto CLI Generator

### Создание модулей

```bash
# Базовый модуль
uv run porto make:module Blog

# С GraphQL поддержкой
uv run porto make:module Order --with-graphql

# С WebSocket
uv run porto make:module Chat --with-websocket

# Полный модуль (все транспорты)
uv run porto make:module Payment --with-graphql --with-websocket
```

### Создание компонентов

```bash
# Action (Use Case)
uv run porto make:action CreatePost --module=Blog
uv run porto make:action UpdatePost --module=Blog

# Task (атомарная операция)
uv run porto make:task SendEmail --module=Notification
uv run porto make:task ValidatePayment --module=Payment

# Query (CQRS Read)
uv run porto make:query GetPost --module=Blog
uv run porto make:query ListPosts --module=Blog

# Controller (HTTP API)
uv run porto make:controller Admin --module=User
uv run porto make:controller Public --module=Blog

# Event (Domain Event)
uv run porto make:event PostPublished --module=Blog
uv run porto make:event OrderCompleted --module=Order

# Listener (Event Handler)
uv run porto make:listener SendWelcomeEmail --module=User --event=UserCreated
```

### Справка по Porto CLI

```bash
# Показать все доступные команды
uv run porto --help

# Справка по конкретной команде
uv run porto make:module --help
uv run porto make:action --help
```

---

## 🗄️ Piccolo ORM Migrations

### Создание миграций

```bash
# Автоматическая миграция (анализирует изменения в Models)
uv run piccolo migrations new UserModule --auto

# Пустая миграция (для ручного редактирования)
uv run piccolo migrations new UserModule

# Проверка pending миграций
uv run piccolo migrations check
```

### Применение миграций

```bash
# Применить все миграции
uv run piccolo migrations forwards all

# Применить миграции конкретного модуля
uv run piccolo migrations forwards UserModule

# Применить до конкретной миграции
uv run piccolo migrations forwards UserModule 2024_01_15_migration_name
```

### Откат миграций

```bash
# Откатить последнюю миграцию
uv run piccolo migrations backwards UserModule 1

# Откатить несколько миграций
uv run piccolo migrations backwards UserModule 3

# Откатить до конкретной (не включая)
uv run piccolo migrations backwards UserModule 2024_01_10_migration_name
```

### Просмотр статуса

```bash
# Показать статус всех миграций
uv run piccolo migrations list

# Показать миграции конкретного модуля
uv run piccolo migrations list UserModule
```

---

## 📤 Outbox CLI (Domain Events)

```bash
# Статистика очереди событий
uv run python -m src.Ship.CLI.Main outbox stats

# Обработать pending события
uv run python -m src.Ship.CLI.Main outbox process

# Обработать с лимитом
uv run python -m src.Ship.CLI.Main outbox process --limit=100

# Очистка старых обработанных событий
uv run python -m src.Ship.CLI.Main outbox cleanup

# Очистка событий старше N дней
uv run python -m src.Ship.CLI.Main outbox cleanup --days=30

# Retry failed события
uv run python -m src.Ship.CLI.Main outbox retry
```

---

## 🚀 Сервер разработки

### Запуск

```bash
# Основной способ (через entry point)
uv run python -m src.Main

# С hot reload (для разработки)
uv run uvicorn src.App:create_app --reload --host 0.0.0.0 --port 8000

# С кастомным портом
uv run uvicorn src.App:create_app --reload --port 3000

# Production режим
uv run uvicorn src.App:create_app --workers 4 --host 0.0.0.0 --port 8000
```

### Litestar CLI

```bash
# Показать все роуты
uv run litestar routes

# Показать схему OpenAPI
uv run litestar schema openapi
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
uv run pytest

# С verbose output
uv run pytest -v

# Unit тесты
uv run pytest tests/unit/

# Integration тесты
uv run pytest tests/integration/

# Конкретный файл
uv run pytest tests/unit/test_user_action.py

# Конкретный тест
uv run pytest tests/unit/test_user_action.py::test_create_user_success

# По имени (pattern matching)
uv run pytest -k "test_user"
uv run pytest -k "test_create and not test_delete"
```

### Coverage

```bash
# С отчётом coverage
uv run pytest --cov=src

# HTML отчёт
uv run pytest --cov=src --cov-report=html

# С минимальным порогом
uv run pytest --cov=src --cov-fail-under=80
```

### Параллельный запуск

```bash
# Параллельно на всех ядрах
uv run pytest -n auto

# На конкретном количестве ядер
uv run pytest -n 4
```

---

## 🔍 Линтинг и форматирование

```bash
# Ruff (линтер + форматтер)
uv run ruff check .                    # Проверка
uv run ruff check . --fix              # Автофикс
uv run ruff format .                   # Форматирование

# MyPy (type checking)
uv run mypy src/

# Black (если используется)
uv run black .
uv run black --check .                 # Только проверка
```

---

## 🚫 ТАБЛИЦА ЗАПРЕЩЁННЫХ КОМАНД

| ❌ **ЗАПРЕЩЕНО**                     | ✅ **Используй вместо**                |
|--------------------------------------|----------------------------------------|
| `pip install X`                      | `uv add X`                             |
| `pip install -r requirements.txt`    | `uv sync`                              |
| `pip install -e .`                   | `uv sync` (editable по умолчанию)      |
| `pip uninstall X`                    | `uv remove X`                          |
| `pip freeze > requirements.txt`      | `uv lock` (автоматически)              |
| `python script.py`                   | `uv run python script.py`              |
| `python3 script.py`                  | `uv run python script.py`              |
| `python -m pytest`                   | `uv run pytest`                        |
| `python -m module`                   | `uv run python -m module`              |
| `pytest`                             | `uv run pytest`                        |
| `source .venv/bin/activate`          | **Не нужно!** UV активирует сам        |
| `. .venv/bin/activate`               | **Не нужно!** UV активирует сам        |
| `.venv/bin/python`                   | `uv run python`                        |
| `deactivate`                         | **Не нужно!**                          |

---

## 💡 Почему UV?

1. **Скорость**: UV в 10-100x быстрее pip
2. **Детерминизм**: `uv.lock` гарантирует одинаковые версии везде
3. **Простота**: Не нужно активировать venv — `uv run` делает всё сам
4. **Совместимость**: Работает с pyproject.toml, понимает pip синтаксис
5. **Единый инструмент**: Заменяет pip, pip-tools, virtualenv, pyenv

---

## 📚 Дополнительные ресурсы

- [UV Documentation](https://docs.astral.sh/uv/)
- [Piccolo ORM Docs](https://piccolo-orm.readthedocs.io/)
- [Litestar Docs](https://docs.litestar.dev/)

---

**Hyper-Porto v4.1** — Используй правильные инструменты! 🚀
