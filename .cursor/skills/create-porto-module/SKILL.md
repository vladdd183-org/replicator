---
name: create-porto-module
description: Create new Porto Container (module) with full structure including Actions, Tasks, Queries, Repository, UoW, Controller, Events. Use when user asks to create module, create container, new module, new container, создай модуль, новый контейнер, добавь модуль, create porto module.
---

# Create Porto Module

Создание нового Container (модуля) по архитектуре Hyper-Porto.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Workflow** | `agent-os/workflows/create-module.md` |
| **Checklist** | `agent-os/checklists/new-module.md` |
| **Templates** | `agent-os/templates/` (все шаблоны) |
| **Standard** | `agent-os/standards/backend/` |
| **Docs** | `docs/02-project-structure.md` |

## Параметры

| Параметр | Пример | Описание |
|----------|--------|----------|
| Section | `AppSection` | Parent section folder |
| Module | `OrderModule` | Module name (PascalCase + Module) |
| Entity | `Order` | Main entity name (PascalCase) |

## Структура модуля

```
src/Containers/{Section}/{Module}/
├── __init__.py
├── Actions/           # Use Cases (CQRS Commands)
├── Tasks/             # Atomic operations
├── Queries/           # CQRS Read operations
├── Data/
│   ├── Repositories/  # Data access
│   ├── Schemas/       # Request/Response DTOs
│   └── UnitOfWork.py  # Transaction management
├── Models/            # Piccolo Tables + migrations
├── UI/API/            # Controllers + Routes
├── Events.py          # Domain Events
├── Listeners.py       # Event handlers
├── Errors.py          # Module errors
└── Providers.py       # DI registration
```

## Действие

1. **Загрузи** полный workflow из `agent-os/workflows/create-module.md`
2. **Создай** структуру папок
3. **Создай** компоненты по шаблонам из `agent-os/templates/`:
   - `model.py.template` → Model
   - `error.py.template` → Errors
   - `schemas.py.template` → Schemas
   - `repository.py.template` → Repository
   - `unit-of-work.py.template` → UnitOfWork
   - `query.py.template` → Queries
   - `action.py.template` → Actions
   - `event.py.template` → Events
   - `controller.py.template` → Controller
   - `providers.py.template` → Providers
4. **Зарегистрируй** PiccoloApp в `piccolo_conf.py`
5. **Создай** и применяй миграции
6. **Добавь** Providers в container
7. **Добавь** Router и Listeners в `App.py`
8. **Проверь** по checklist из `agent-os/checklists/new-module.md`

## Checklist

```
- [ ] 1. Folder structure created
- [ ] 2. Model (Piccolo Table)
- [ ] 3. PiccoloApp.py
- [ ] 4. Errors.py
- [ ] 5. Schemas (Requests + Responses)
- [ ] 6. Repository
- [ ] 7. UnitOfWork
- [ ] 8. Queries (Get, List)
- [ ] 9. Actions (Create, Update, Delete)
- [ ] 10. Events + Listeners
- [ ] 11. Controller
- [ ] 12. Providers.py
- [ ] 13. Registered in piccolo_conf.py
- [ ] 14. Migration created and applied
- [ ] 15. Added to App.py
```
