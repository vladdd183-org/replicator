# 03. Отладка с агентами

> Как эффективно отлаживать код в Hyper-Porto с помощью AI-агентов

**Уровень:** Intermediate  
**Время:** 40 минут  
**Темы:** Отладка Result, DI ошибки, трейсинг, troubleshooting  
**Пререквизиты:** [01-first-action](./01-first-action.md)

---

## Цель

После этого туториала ты сможешь:

- Эффективно описывать проблемы AI-агенту
- Отлаживать Result/Failure паттерны
- Диагностировать ошибки DI (Dishka)
- Использовать трейсинг и логирование
- Применять команды troubleshooting

---

## Принципы отладки с AI

### 1. Давай контекст

AI не видит весь проект. Чем больше контекста — тем точнее помощь.

```
❌ Плохо:
"Не работает Action"

✅ Хорошо:
"CreateUserAction возвращает Failure вместо Success.
Вход: {"email": "test@test.com", "password": "12345678"}
Ошибка: UserAlreadyExistsError
Ожидание: пользователь должен создаться, email уникален

Файл: src/Containers/AppSection/UserModule/Actions/CreateUserAction.py"
```

### 2. Покажи код и ошибку

```
@debug вот мой код:
{код}

Ошибка:
{traceback или описание}
```

### 3. Опиши что уже пробовал

```
Уже проверил:
- Email уникален в базе
- Валидация проходит
- Repository.add() вызывается
```

---

## Шаг 1: Отладка Result[T, E]

Result — основа Hyper-Porto. Ошибки с ним частые.

### Проблема: Action возвращает Failure, а не Success

```python
# Код
result = await action.run(request)
# result = Failure(SomeError(...))
# Ожидалось: Success(...)
```

### Диагностика

**Команда:**
```
@debug-result проверь CreateUserAction
```

**Что проверит агент:**

1. **Все ветки возвращают Result?**
```python
# ❌ Проблема — return без Result
async def run(self, data):
    if condition:
        return user  # Ошибка! Нужно Success(user)
    return Failure(error)
```

2. **Pattern matching корректен?**
```python
# ❌ Проблема — не все случаи покрыты
match result:
    case Success(value):
        return value
    # Нет case Failure!
```

3. **Тип ошибки совпадает?**
```python
# ❌ Проблема — возвращаем не тот тип ошибки
class MyAction(Action[Input, Output, UserError]):
    async def run(self, data):
        return Failure(OrderError(...))  # Должен быть UserError!
```

### Решение типичных проблем

| Симптом | Причина | Решение |
|---------|---------|---------|
| `Failure` вместо `Success` | Логика возвращает ошибку | Проверь условия |
| `Success(None)` | Забыл передать значение | `Success(actual_value)` |
| Type error в match | Неправильный тип в case | Проверь типы ошибок |
| `unwrap()` падает | Вызов на Failure | Используй pattern matching |

---

## Шаг 2: Отладка DI (Dishka)

Dishka — DI-контейнер. Ошибки инъекции частые.

### Типичная ошибка

```
dishka.exceptions.NoFactoryError: 
Cannot find factory for <class 'CreateUserAction'>. 
Check if this type is registered in any provider.
```

### Диагностика

**Команда:**
```
@debug-di CreateUserAction
```

**Что проверит агент:**

1. **Зарегистрирован ли в Provider?**
```python
# Providers.py
class UserModuleProvider(Provider):
    scope = Scope.REQUEST
    create_user_action = provide(CreateUserAction)  # ← Есть?
```

2. **Provider добавлен в контейнер?**
```python
# AppProvider.py
container = make_container(
    UserModuleProvider(),  # ← Есть?
)
```

3. **Scope правильный?**
```python
# Action требует REQUEST scope
# Task может быть APP scope
```

4. **Зависимости Action зарегистрированы?**
```python
@dataclass
class CreateUserAction:
    user_repository: UserRepository  # ← Зарегистрирован?
    hash_password: HashPasswordTask  # ← Зарегистрирован?
```

### Чек-лист DI

- [ ] Action/Task/Query зарегистрирован в Provider
- [ ] Provider добавлен в `make_container()`
- [ ] Все зависимости также зарегистрированы
- [ ] Scope совместимы (REQUEST не может зависеть от REQUEST другого модуля напрямую)

---

## Шаг 3: Отладка базы данных

### Проблема: данные не сохраняются

```python
async with self.uow:
    await self.uow.users.add(user)
    await self.uow.commit()
    
# Но user не в базе!
```

### Диагностика

**Команда:**
```
@debug-db проверь сохранение User
```

**Что проверит агент:**

1. **Вызван ли `commit()`?**
```python
# ❌ Забыли commit
async with self.uow:
    await self.uow.users.add(user)
    # return Success(user)  # commit не вызван!
```

2. **Исключение в транзакции?**
```python
# Если исключение — rollback автоматически
async with self.uow:
    await self.uow.users.add(user)
    raise SomeException()  # rollback!
    await self.uow.commit()  # не достигнем
```

3. **Правильная база данных?**
```python
# Проверь Settings
# Может быть подключение к test DB?
```

### Команда для проверки базы

```
@db-check users --where "email='test@test.com'"
```

---

## Шаг 4: Трейсинг и логирование

Hyper-Porto использует Logfire для observability.

### Добавление трейсинга

```python
import logfire

class CreateUserAction:
    async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
        with logfire.span("create_user", email=data.email):
            # Логика
            logfire.info("User created", user_id=str(user.id))
            return Success(user)
```

### Просмотр логов

```
@logs показать CreateUserAction последние 10
```

### Настройка уровня логирования

```python
# Settings.py
class Settings(BaseSettings):
    log_level: str = "DEBUG"  # Для отладки
```

---

## Шаг 5: Команды troubleshooting

### Общие команды отладки

| Команда | Описание |
|---------|----------|
| `@debug <file>` | Анализ файла на ошибки |
| `@debug-result <action>` | Проверка Result-паттернов |
| `@debug-di <component>` | Проверка DI регистрации |
| `@debug-db <query>` | Проверка запросов к БД |
| `@trace <action>` | Трейсинг выполнения |
| `@logs <filter>` | Просмотр логов |

### Специфичные для Hyper-Porto

| Команда | Описание |
|---------|----------|
| `@check-imports <module>` | Проверка импортов (абсолютные?) |
| `@check-types <file>` | Проверка типизации |
| `@check-uow <action>` | Проверка использования UoW |
| `@check-events <module>` | Проверка публикации событий |

---

## Шаг 6: Практика — отладка реального бага

### Сценарий

У тебя есть Action, который должен обновлять пользователя, но изменения не сохраняются.

### Код с багом

```python
@dataclass
class UpdateUserAction(Action[UpdateUserRequest, User, UserError]):
    uow: UserUnitOfWork
    
    async def run(self, data: UpdateUserRequest) -> Result[User, UserError]:
        user = await self.uow.users.get(data.user_id)
        
        if not user:
            return Failure(UserNotFoundError(user_id=data.user_id))
        
        # Обновляем
        if data.name:
            user.name = data.name
        if data.email:
            user.email = data.email
        
        return Success(user)
```

### Найди баг

Скажи агенту:

```
@debug вот мой UpdateUserAction:
{код выше}

Проблема: после вызова action.run() пользователь не обновляется в базе.
Тесты показывают, что Success возвращается, но при повторном запросе — старые данные.
```

### Решение

```python
async def run(self, data: UpdateUserRequest) -> Result[User, UserError]:
    async with self.uow:  # ← Добавили контекст
        user = await self.uow.users.get(data.user_id)
        
        if not user:
            return Failure(UserNotFoundError(user_id=data.user_id))
        
        if data.name:
            user.name = data.name
        if data.email:
            user.email = data.email
        
        await self.uow.commit()  # ← Добавили commit
    
    return Success(user)
```

**Баги:**
1. Не использовался `async with self.uow`
2. Не вызывался `commit()`

---

## Шаг 7: Анти-паттерны отладки

### ❌ Не делай так

1. **Игнорирование Failure**
```python
result = await action.run(data)
user = result.unwrap()  # Упадёт если Failure!
```

2. **Пустые except**
```python
try:
    await action.run(data)
except:  # Ловим всё и молчим
    pass
```

3. **Print вместо логов**
```python
print(f"Debug: {user}")  # Не делай так!
logfire.debug("User data", user=user)  # Делай так
```

4. **Отладка в production**
```python
# ❌ Не добавляй debug-код в production
if settings.DEBUG:
    import pdb; pdb.set_trace()
```

### ✅ Делай так

1. **Pattern matching для Result**
```python
match await action.run(data):
    case Success(user):
        return user
    case Failure(error):
        logfire.error("Action failed", error=str(error))
        raise
```

2. **Структурированное логирование**
```python
logfire.info(
    "User created",
    user_id=str(user.id),
    email=user.email,
    action="CreateUserAction",
)
```

---

## Итоговое задание

Тебе дан код с 3 багами. Найди и исправь их.

### Код

```python
from dataclasses import dataclass
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from ....Data.Schemas import TransferRequest
from src.Containers.AppSection.WalletModule.Errors import WalletError


@dataclass
class TransferMoneyAction(Action[TransferRequest, bool, WalletError]):
    uow: WalletUnitOfWork
    
    async def run(self, data: TransferRequest):
        from_wallet = await self.uow.wallets.get(data.from_wallet_id)
        to_wallet = await self.uow.wallets.get(data.to_wallet_id)
        
        if from_wallet.balance < data.amount:
            return Failure(InsufficientFundsError())
        
        from_wallet.balance -= data.amount
        to_wallet.balance += data.amount
        
        return True
```

### Найди баги

Скажи:

```
@training проверь итоговое задание
```

---

## Что дальше?

### Следующие шаги

1. Попробуй отладить реальный баг в проекте
2. Изучи [Troubleshooting Guide](../../troubleshooting/)
3. Настрой Logfire для своего проекта

### Полезные ресурсы

- [Troubleshooting: DI ошибки](../../troubleshooting/di-errors.md)
- [Troubleshooting: Result ошибки](../../troubleshooting/result-errors.md)
- [Skill: debug-result](../../../.cursor/skills/debug-result/)
- [Skill: debug-di](../../../.cursor/skills/debug-di/)

---

## Резюме

| Тип проблемы | Команда | Что проверить |
|--------------|---------|---------------|
| Result | `@debug-result` | Типы, pattern matching, все ветки |
| DI | `@debug-di` | Provider, scope, зависимости |
| Database | `@debug-db` | commit, транзакции, подключение |
| General | `@debug` | Контекст + traceback |

### Ключевые принципы

- **Давай контекст** — AI не видит весь проект
- **Показывай код и ошибку** — конкретика помогает
- **Используй команды** — они ускоряют диагностику
- **Логируй структурировано** — будущий ты скажет спасибо
