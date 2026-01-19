# 💉 Dependency Injection Mistakes

> Ошибки при использовании Dishka DI

---

## 📊 Статистика

- **Всего ошибок:** 0
- **Critical:** 0 | **Major:** 0 | **Minor:** 0

---

## 🚨 Типичные проблемы

### 1. Зависимость не зарегистрирована

```python
# ❌ Забыли зарегистрировать в Provider
class UserModuleProvider(Provider):
    scope = Scope.REQUEST
    # create_user_action = provide(CreateUserAction)  # Забыли!

# Ошибка: DependencyNotProvidedError: CreateUserAction

# ✅ ПРАВИЛЬНО
class UserModuleProvider(Provider):
    scope = Scope.REQUEST
    create_user_action = provide(CreateUserAction)
```

### 2. Неправильный Scope

```python
# ❌ REQUEST scope для stateless компонента
class UserModuleProvider(Provider):
    scope = Scope.REQUEST
    hash_password = provide(HashPasswordTask)  # Создаётся каждый запрос!

# ✅ ПРАВИЛЬНО — APP scope для stateless
class UserModuleProvider(Provider):
    scope = Scope.APP
    hash_password = provide(HashPasswordTask)  # Один экземпляр
```

**Правило выбора Scope:**
| Компонент | Scope | Причина |
|-----------|-------|---------|
| Task (stateless) | APP | Нет состояния |
| Repository | REQUEST | Привязан к сессии БД |
| UnitOfWork | REQUEST | Транзакция per-request |
| Action | REQUEST | Зависит от UoW |

### 3. Циклическая зависимость

```python
# ❌ A зависит от B, B зависит от A
@dataclass
class ActionA:
    action_b: ActionB

@dataclass  
class ActionB:
    action_a: ActionA  # Цикл!

# ✅ Решение: разбить на Task или использовать Events
@dataclass
class ActionA:
    shared_task: SharedTask  # Общая логика в Task
```

### 4. Service Locator вместо DI

```python
# ❌ Service Locator — анти-паттерн
async def run(self):
    container = get_container()
    repo = await container.get(UserRepository)  # Плохо!

# ✅ ПРАВИЛЬНО — инъекция через конструктор
@dataclass
class CreateUserAction:
    repo: UserRepository  # Dishka инжектит автоматически
```

### 5. Забыли FromDishka в Controller

```python
# ❌ Без FromDishka — Litestar не понимает
@post("/users")
async def create_user(action: CreateUserAction):  # Не сработает!
    ...

# ✅ ПРАВИЛЬНО
from dishka.integrations.litestar import FromDishka

@post("/users")
async def create_user(action: FromDishka[CreateUserAction]):
    ...
```

---

## 📝 Записанные ошибки

<!-- AUTO-GENERATED -->

| ID | Название | Серьёзность | Дата | Модуль |
|----|----------|-------------|------|--------|
| — | Нет записей | — | — | — |

---

## 🛡️ Чеклист предотвращения

- [ ] Все зависимости зарегистрированы в `Providers.py`
- [ ] Правильный Scope (APP для stateless, REQUEST для stateful)
- [ ] Нет циклических зависимостей
- [ ] `FromDishka[T]` в Controllers
- [ ] Нет Service Locator паттерна

---

## 🔗 Связи

- [DI Errors Troubleshooting](../../../../troubleshooting/di-errors.md)
- [Dependency Injection Standards](../../../../standards/backend/dependency-injection.md)
- [Dishka Documentation](../../../../../foxdocs/dishka-develop/docs/)
