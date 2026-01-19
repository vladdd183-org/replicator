# Generate CRUD Skill

Generate full CRUD operations for Hyper-Porto module.

## Trigger Words
- "generate crud"
- "создай crud"
- "full crud"
- "полный crud"

## Sources
| **Command** | `agent-os/commands/generate-crud.md` |
| **Templates** | `agent-os/templates/` |
| **Checklist** | `agent-os/checklists/new-module.md` |
| **Docs** | `docs/03-components.md` |

## Steps

1. **Identify Module** — определить модуль и entity
2. **Generate Components**:
   - Model (если не существует)
   - Repository
   - UnitOfWork
   - Actions: Create, Update, Delete
   - Queries: Get, List
   - Controller с endpoints
   - Schemas: Requests, Responses
   - Errors
3. **Register in Providers.py**
4. **Update App.py** если нужно

## Output
- Полный набор CRUD компонентов
- Регистрация в DI
- Готовые endpoints
