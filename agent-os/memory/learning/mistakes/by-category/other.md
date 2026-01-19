# Ошибки категории: Прочие

## Описание

Здесь собраны типичные ошибки, которые не попадают в другие категории: конфигурация, окружение, инструменты, документация.

## Частые ошибки

### 1. Использование pip вместо uv

**Симптом:** Зависимости не синхронизированы, конфликты версий.
**Причина:** Проект использует uv, но вызывается pip напрямую.
**Решение:** Всегда использовать uv для управления зависимостями.

```bash
# ❌ Запрещено
pip install package
python script.py

# ✅ Правильно
uv add package
uv run python script.py
```

### 2. Хардкод конфигурации

**Симптом:** Разные значения нужны для dev/prod, приходится менять код.
**Причина:** Конфигурация захардкожена в коде.
**Решение:** Использовать Settings (Pydantic BaseSettings) и .env файлы.

```python
# ❌ Плохо
DATABASE_URL = "postgresql://localhost/mydb"

# ✅ Хорошо
from src.Ship.Configs.Settings import Settings
settings = Settings()  # Читает из .env
```

### 3. Секреты в git репозитории

**Симптом:** Утечка API ключей, паролей.
**Причина:** Файлы с секретами (.env, credentials.json) закоммичены.
**Решение:** Добавить в .gitignore, использовать secrets management.

```gitignore
# .gitignore
.env
.env.local
*.pem
credentials.json
```

### 4. Отсутствие миграций при изменении модели

**Симптом:** Модель изменена, но база данных не соответствует.
**Причина:** Забыли создать и применить миграцию Piccolo.
**Решение:** После изменения модели всегда создавать миграцию.

```bash
# После изменения Model
uv run piccolo migrations new ModuleName --auto
uv run piccolo migrations forwards all
```

### 5. Неправильные права доступа к файлам

**Симптом:** Permission denied при запуске.
**Причина:** Скрипты без executable флага, неправильный owner.
**Решение:** Проверять права доступа.

```bash
chmod +x script.sh
```

### 6. Игнорирование .cursorignore

**Симптом:** AI агент читает ненужные файлы (node_modules, .venv).
**Причина:** Не настроен .cursorignore.
**Решение:** Добавить паттерны игнорирования.

```gitignore
# .cursorignore
.venv/
node_modules/
*.pyc
__pycache__/
```

### 7. Отсутствие docstrings

**Симптом:** Сложно понять назначение функции/класса.
**Причина:** Код без документации.
**Решение:** Добавлять docstrings к публичным API.

```python
# ✅ Хорошо
class CreateUserAction(Action[CreateUserRequest, User, UserError]):
    """Use Case: Create new user.
    
    Creates a new user account with hashed password.
    Publishes UserCreated event on success.
    """
```

---

*Файл будет дополняться по мере обнаружения новых паттернов ошибок.*
