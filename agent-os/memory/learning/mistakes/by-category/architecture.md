# Ошибки категории: Архитектура

## Описание

Здесь собраны типичные ошибки связанные с архитектурными решениями: нарушение Porto паттернов, неправильное разделение слоев, циклические зависимости.

## Частые ошибки

### 1. Прямой импорт между Containers

**Симптом:** Циклические зависимости, сильная связанность модулей.
**Причина:** Container A напрямую импортирует код из Container B.
**Решение:** Использовать Domain Events для межмодульного взаимодействия.

```python
# ❌ Плохо — прямой импорт
from src.Containers.AppSection.OrderModule.Actions import CreateOrderAction

# ✅ Хорошо — через Events
# В OrderModule:
self.uow.add_event(OrderCreated(order_id=order.id))

# В NotificationModule — слушатель:
@listener(OrderCreated)
async def on_order_created(event: OrderCreated) -> None:
    ...
```

### 2. Бизнес-логика в Controller

**Симптом:** Толстые контроллеры, дублирование кода, сложно тестировать.
**Причина:** Логика размещена в Controller вместо Action/Task.
**Решение:** Controller только вызывает Action и преобразует результат.

```python
# ❌ Плохо — логика в Controller
@post("/users")
async def create(self, data: CreateUserRequest) -> Response:
    if await self.repo.exists(data.email):
        raise HTTPException(400, "User exists")
    user = User(email=data.email, ...)
    await self.repo.add(user)
    return Response(user)

# ✅ Хорошо — логика в Action
@post("/users")
@result_handler(UserResponse, success_status=201)
async def create(
    self, data: CreateUserRequest, action: FromDishka[CreateUserAction]
) -> Result[User, UserError]:
    return await action.run(data)
```

### 3. Repository в Controller

**Симптом:** Controller напрямую работает с Repository.
**Причина:** Пропущен слой Action/Query.
**Решение:** Controller -> Action/Query -> Repository.

### 4. Смешение Read и Write операций

**Симптом:** Action выполняет и чтение и запись, сложная логика.
**Причина:** Нарушение CQRS принципа.
**Решение:** Разделять на Action (write) и Query (read).

```python
# ❌ Плохо — Action возвращает список для отображения
class GetUsersAction(Action):  # Должно быть Query!
    async def run(self) -> list[User]:
        return await self.repo.list_all()

# ✅ Хорошо — Query для чтения
class ListUsersQuery(Query[ListUsersInput, list[User]]):
    async def execute(self, input: ListUsersInput) -> list[User]:
        return await self.user_repository.list_all()
```

### 5. Отсутствие UnitOfWork для транзакций

**Симптом:** Частичное сохранение данных при ошибке, несогласованность.
**Причина:** Несколько repository.save() без транзакции.
**Решение:** Использовать UnitOfWork для атомарных операций.

```python
# ✅ Правильно — UoW гарантирует транзакцию
async with self.uow:
    await self.uow.orders.add(order)
    await self.uow.items.add_many(items)
    self.uow.add_event(OrderCreated(...))
    await self.uow.commit()  # Всё или ничего
```

---

*Файл будет дополняться по мере обнаружения новых паттернов ошибок.*
