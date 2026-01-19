---
name: add-action
description: Create new Action (Use Case) for Hyper-Porto architecture. Actions always return Result[T, E] from returns library. Use when the user wants to add action, create use case, new action, добавить action, новый use case, создать action.
---

# Add Action (Use Case)

Создание Action по архитектуре Hyper-Porto.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-action.md` |
| **Template** | `agent-os/templates/action.py.template` |
| **Checklist** | `agent-os/checklists/action-implementation.md` |
| **Standard** | `agent-os/standards/backend/actions-tasks.md` |
| **Anti-patterns** | `agent-os/anti-patterns/common-mistakes.md` |

## Быстрая справка

| Правило | Описание |
|---------|----------|
| **Return type** | ВСЕГДА `Result[OutputT, ErrorT]` |
| **Imports** | ТОЛЬКО абсолютные от `src.` |
| **Transactions** | Через `UnitOfWork` context manager |
| **Events** | Через `uow.add_event()` перед commit |
| **Auditing** | Декоратор `@audited` для логирования |
| **DI** | Регистрация в `Providers.py` (REQUEST scope) |

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-action.md`
2. **Используй** template из `agent-os/templates/action.py.template`
3. **Создай** Action файл в `Actions/[ActionName].py`
4. **Создай** Error классы в `Errors.py` (если нужны)
5. **Создай** Event в `Events.py` (если меняется state)
6. **Зарегистрируй** в `Providers.py` (REQUEST scope)
7. **Проверь** по checklist из `agent-os/checklists/action-implementation.md`

## Именование

| Операция | Паттерн | Пример |
|----------|---------|--------|
| Create | `Create{Entity}Action` | `CreateUserAction` |
| Update | `Update{Entity}Action` | `UpdateUserAction` |
| Delete | `Delete{Entity}Action` | `DeleteUserAction` |
| Get/List | Используй **Query** вместо | `GetUserQuery` |
| Custom | `{Verb}{Entity}Action` | `ActivateUserAction` |
