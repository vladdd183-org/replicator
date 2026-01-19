# ✅ Checklist: Action Implementation

> Чеклист реализации нового Action.

---

## 📋 Перед началом

- [ ] Определён Use Case (что делает Action)
- [ ] Определены Input/Output/Error типы
- [ ] Определены зависимости (Tasks, UoW)

## 🏗️ Структура

- [ ] Файл в `Actions/{ActionName}.py`
- [ ] Класс наследует `Action[Input, Output, Error]`
- [ ] Метод `async def run(self, data: Input) -> Result[Output, Error]`

## 📝 Реализация

```python
@audited(action="verb", entity_type="Entity")
class VerbEntityAction(Action[VerbEntityRequest, Entity, ModuleError]):
    def __init__(self, task: SomeTask, uow: ModuleUnitOfWork) -> None:
        self.task = task
        self.uow = uow
    
    async def run(self, data: VerbEntityRequest) -> Result[Entity, ModuleError]:
        # 1. Валидация / проверка условий
        # 2. Выполнение Tasks
        # 3. Работа с UoW
        # 4. Публикация событий
        # 5. Return Success/Failure
```

## ✅ Обязательные элементы

- [ ] `@audited` декоратор
- [ ] Docstring с описанием Use Case
- [ ] Type hints везде
- [ ] Проверка бизнес-правил → `return Failure(Error)`
- [ ] Успешный путь → `return Success(result)`

## 🔄 UoW Pattern

- [ ] `async with self.uow:` для транзакции
- [ ] `self.uow.add_event(Event)` перед commit
- [ ] `await self.uow.commit()` в конце блока

## 💉 DI Registration

- [ ] Импорт в `Providers.py`
- [ ] `action_name = provide(ActionName)` в REQUEST provider

## 🌐 Controller Integration

- [ ] Endpoint в Controller
- [ ] `@result_handler(ResponseDTO, success_status=...)` декоратор
- [ ] `FromDishka[ActionName]` для инъекции

## 🧪 Testing

- [ ] Unit тест для success case
- [ ] Unit тест для failure case(s)
- [ ] Mock для UoW и Tasks

---

## 📐 Шаблон

```python
"""VerbEntityAction - Use case for verbing entity."""

import anyio
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Ship.Decorators import audited
from src.Containers.Section.Module.Data.Schemas.Requests import VerbEntityRequest
from src.Containers.Section.Module.Data.UnitOfWork import ModuleUnitOfWork
from src.Containers.Section.Module.Errors import ModuleError, EntityNotFoundError
from src.Containers.Section.Module.Events import EntityVerbed
from src.Containers.Section.Module.Models.Entity import Entity


@audited(action="verb", entity_type="Entity")
class VerbEntityAction(Action[VerbEntityRequest, Entity, ModuleError]):
    """Use Case: Verb an entity.
    
    Steps:
    1. Validate input
    2. Check business rules
    3. Execute operation
    4. Publish event
    """
    
    def __init__(self, uow: ModuleUnitOfWork) -> None:
        self.uow = uow
    
    async def run(self, data: VerbEntityRequest) -> Result[Entity, ModuleError]:
        # Step 1-2: Validate and check rules
        entity = await self.uow.entities.get(data.entity_id)
        if not entity:
            return Failure(EntityNotFoundError(entity_id=data.entity_id))
        
        # Step 3: Execute operation
        async with self.uow:
            entity.field = data.new_value
            await self.uow.entities.update(entity)
            
            # Step 4: Add event
            self.uow.add_event(EntityVerbed(entity_id=entity.id))
            
            await self.uow.commit()
        
        return Success(entity)
```

---

## 🔗 Связанные

- **Template:** `../templates/action.py.template`
- **Standards:** `../standards/backend/actions-tasks.md`



