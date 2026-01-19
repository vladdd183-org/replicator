# Шаги симуляции: Создание модуля User

## Шаг 1: Создание структуры папок

Создай структуру модуля:

```
src/Containers/AppSection/UserModule/
├── __init__.py
├── Models/
│   └── __init__.py
├── Data/
│   └── __init__.py
├── Actions/
│   └── __init__.py
├── UI/
│   └── API/
│       └── __init__.py
├── Errors.py
└── Providers.py
```

**Проверка:** `@training проверь шаг 1`

---

## Шаг 2: Создание модели User

Создай `Models/User.py` с Piccolo Table:

- id (UUID, primary key)
- email (str, unique)
- password_hash (str)
- name (str)
- is_active (bool, default=True)
- created_at (datetime)

**Проверка:** `@training проверь шаг 2`

---

## Шаг 3: Создание ошибок

Создай `Errors.py`:

- `UserError` — базовая ошибка
- `UserNotFoundError` — пользователь не найден (404)
- `UserAlreadyExistsError` — email занят (409)

Используй `ErrorWithTemplate` для автоматического message.

**Проверка:** `@training проверь шаг 3`

---

## Шаг 4: Создание Schemas (DTO)

Создай `Data/Schemas.py`:

- `CreateUserRequest` — email, password, name
- `UpdateUserRequest` — name (optional)
- `UserResponse` — id, email, name, is_active, created_at

**Проверка:** `@training проверь шаг 4`

---

## Шаг 5: Создание Repository

Создай `Data/Repository.py`:

- `UserRepository` наследует `BaseRepository`
- Методы: `get`, `add`, `find_by_email`

**Проверка:** `@training проверь шаг 5`

---

## Шаг 6: Создание UnitOfWork

Создай `Data/UnitOfWork.py`:

- `UserUnitOfWork` наследует `BaseUnitOfWork`
- Содержит `users: UserRepository`

**Проверка:** `@training проверь шаг 6`

---

## Шаг 7: Создание Actions

Создай три Action в `Actions/`:

1. `CreateUserAction` — создание пользователя
2. `GetUserAction` — получение по ID
3. `UpdateUserAction` — обновление имени

Каждый возвращает `Result[T, UserError]`.

**Проверка:** `@training проверь шаг 7`

---

## Шаг 8: Создание Controller

Создай `UI/API/Controllers.py`:

- POST /api/v1/users → CreateUserAction
- GET /api/v1/users/{user_id} → GetUserAction
- PATCH /api/v1/users/{user_id} → UpdateUserAction

Используй `@result_handler` для POST/PATCH.

**Проверка:** `@training проверь шаг 8`

---

## Шаг 9: Регистрация в DI

Создай `Providers.py`:

- Зарегистрируй все компоненты в Dishka
- APP scope для Tasks
- REQUEST scope для Actions, Repository, UoW

**Проверка:** `@training проверь шаг 9`

---

## Шаг 10: Финальная проверка

```
@training проверь всё
```

Поздравляю! Модуль готов.
