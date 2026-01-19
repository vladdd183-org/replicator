# 🧩 Snippets: UnitOfWork Patterns

> Готовые паттерны работы с UnitOfWork.

---

## Базовый паттерн

### Create с событием
```python
async with self.uow:
    entity = Entity(field=data.field)
    await self.uow.entities.add(entity)
    
    self.uow.add_event(EntityCreated(entity_id=entity.id))
    
    await self.uow.commit()

return Success(entity)
```

### Update с событием
```python
async with self.uow:
    entity = await self.uow.entities.get(entity_id)
    if not entity:
        return Failure(EntityNotFoundError(entity_id=entity_id))
    
    entity.field = data.new_value
    await self.uow.entities.update(entity)
    
    self.uow.add_event(EntityUpdated(
        entity_id=entity.id,
        updated_fields=["field"],
    ))
    
    await self.uow.commit()

return Success(entity)
```

### Delete с событием
```python
async with self.uow:
    entity = await self.uow.entities.get(entity_id)
    if not entity:
        return Failure(EntityNotFoundError(entity_id=entity_id))
    
    await self.uow.entities.delete(entity)
    
    self.uow.add_event(EntityDeleted(entity_id=entity.id))
    
    await self.uow.commit()

return Success(None)
```

---

## Множественные операции

### Несколько сущностей в одной транзакции
```python
async with self.uow:
    # Создать заказ
    order = Order(user_id=data.user_id)
    await self.uow.orders.add(order)
    
    # Создать позиции заказа
    for item_data in data.items:
        item = OrderItem(order_id=order.id, product_id=item_data.product_id)
        await self.uow.order_items.add(item)
    
    # Обновить баланс пользователя
    user = await self.uow.users.get(data.user_id)
    user.balance -= data.total
    await self.uow.users.update(user)
    
    # Одно событие на всю операцию
    self.uow.add_event(OrderCreated(order_id=order.id, total=data.total))
    
    await self.uow.commit()
```

---

## Проверки ДО транзакции

### Валидация вне UoW блока
```python
async def run(self, data) -> Result[Order, OrderError]:
    # Проверки ДО транзакции (read-only)
    user = await self.uow.users.get(data.user_id)
    if not user:
        return Failure(UserNotFoundError(user_id=data.user_id))
    
    if user.balance < data.total:
        return Failure(InsufficientBalanceError(
            required=data.total,
            available=user.balance,
        ))
    
    # Транзакция ТОЛЬКО для изменений
    async with self.uow:
        order = Order(...)
        await self.uow.orders.add(order)
        
        user.balance -= data.total
        await self.uow.users.update(user)
        
        self.uow.add_event(OrderCreated(order_id=order.id))
        await self.uow.commit()
    
    return Success(order)
```

---

## Множественные события

### Несколько событий
```python
async with self.uow:
    user = User(...)
    await self.uow.users.add(user)
    
    # Несколько событий
    self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
    self.uow.add_event(WelcomeEmailRequested(user_id=user.id))
    self.uow.add_event(UserStatsUpdated(action="user_created"))
    
    await self.uow.commit()
# Все события публикуются после commit
```

---

## Условные события

### Событие по условию
```python
async with self.uow:
    user.status = new_status
    await self.uow.users.update(user)
    
    # Разные события в зависимости от статуса
    if new_status == "active":
        self.uow.add_event(UserActivated(user_id=user.id))
    elif new_status == "suspended":
        self.uow.add_event(UserSuspended(user_id=user.id, reason=data.reason))
    
    await self.uow.commit()
```

---

## Без событий (CLI/тесты)

### UoW без event emitter
```python
# В CLI Provider
@provide
def uow(self) -> ModuleUnitOfWork:
    return ModuleUnitOfWork(_emit=None, _app=None)

# События не будут публиковаться
async with self.uow:
    await self.uow.entities.add(entity)
    self.uow.add_event(...)  # Будет проигнорировано
    await self.uow.commit()
```

---

## Rollback

### Автоматический rollback при exception
```python
async with self.uow:
    await self.uow.entities.add(entity)
    
    if some_condition:
        raise ValueError("Something wrong")  # → rollback
    
    await self.uow.commit()
# Если exception → rollback, события НЕ публикуются
```

### Явный rollback (не commit)
```python
async with self.uow:
    await self.uow.entities.add(entity)
    
    if validation_failed:
        # Просто не вызываем commit → rollback
        return Failure(ValidationError())
    
    await self.uow.commit()
```



