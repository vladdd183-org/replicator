---
name: piccolo-migration
description: Create and manage Piccolo ORM database migrations in Hyper-Porto architecture. Use when adding fields to models, creating new tables, running migrations, or when the user mentions "миграция", "изменить модель", "piccolo migration", "добавить поле", "новая таблица".
---

# Piccolo ORM Migrations

Создание и управление миграциями БД.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Standard** | `agent-os/standards/backend/migrations.md` |
| **Template** | `agent-os/templates/model.py.template` |
| **Library docs** | <https://piccolo-orm.com/docs/> |

## Quick Reference

```bash
# Create migration (auto-detect changes)
piccolo migrations new {app_name} --auto

# Apply migrations
piccolo migrations forwards {app_name}

# Rollback
piccolo migrations backwards {app_name}

# Check status
piccolo migrations check
```

## Workflow: Change Model

1. **Измени** model в `Models/{Entity}.py`
2. **Создай** migration: `piccolo migrations new {app_name} --auto`
3. **Проверь** generated file в `Models/migrations/`
4. **Применяй**: `piccolo migrations forwards {app_name}`

## Действие

1. **Загрузи** полный гайд из `agent-os/standards/backend/migrations.md`
2. **Выполни** нужную операцию

## Column Types

| Type | Usage | Example |
|------|-------|---------|
| `UUID` | Primary keys | `id = UUID(primary_key=True, default=uuid.uuid4)` |
| `Varchar` | Short strings | `name = Varchar(length=255)` |
| `Text` | Long text | `description = Text()` |
| `Boolean` | True/False | `is_active = Boolean(default=True)` |
| `Timestamptz` | Datetime | `created_at = Timestamptz(default=TimestamptzNow())` |
| `ForeignKey` | Relations | `user = ForeignKey(references=AppUser)` |
| `JSON/JSONB` | JSON data | `metadata = JSONB()` |

## New Module Checklist

```
- [ ] Models/ directory created
- [ ] Model file Models/{Entity}.py
- [ ] Models/PiccoloApp.py created
- [ ] Registered in piccolo_conf.py
- [ ] piccolo migrations new --auto
- [ ] piccolo migrations forwards
```
