# /extract-service — Выделение микросервиса

Помощь в выделении Porto Container в отдельный микросервис.

## Источники

- Skill: `.cursor/skills/extract-module/SKILL.md`
- Docs: `docs/16-extract-module-to-microservice.md`
- Docs: `docs/17-microservice-extraction-guide.md`

## Синтаксис

```
/extract-service <Module> [--analyze|--plan|--execute]
```

## Примеры

```
/extract-service UserModule --analyze
/extract-service OrderModule --plan
/extract-service PaymentModule --execute
```

## Фазы

### 1. Analyze (--analyze)

Анализ готовности модуля к выделению:
- Зависимости от других модулей
- Зависимости других модулей от него
- Состояние базы данных
- Event flows

### 2. Plan (--plan)

Создание плана выделения:
- Шаги деcouple
- Создание service client
- Event bus настройка
- Data migration план

### 3. Execute (--execute)

Пошаговое выполнение:
- Создание нового сервиса
- Копирование кода
- Настройка коммуникации
- Миграция данных

## Вывод --analyze

```markdown
# Module Extraction Assessment: UserModule

## Readiness Score: 7/10

## Dependencies

### Outgoing (UserModule imports)
- None (clean!)

### Incoming (others import UserModule)
- OrderModule: GetUserQuery (can be replaced with API)
- NotificationModule: UserCreated event (already decoupled)

## Database
- Tables: app_user, user_session
- Foreign keys to: none
- Foreign keys from: order.user_id

## Events
- Published: UserCreated, UserUpdated, UserDeleted
- Consumed: OrderCreated (for stats)

## Recommendation
Module is ready for extraction with minimal changes:
1. Replace GetUserQuery import with HTTP client
2. Set up event bus for cross-service events
```

## Checklist

```
Extraction Checklist:
- [ ] Assessed module boundaries
- [ ] Identified all dependencies
- [ ] Created service client
- [ ] Set up event bus
- [ ] Created new service project
- [ ] Migrated database
- [ ] Updated API gateway
- [ ] Deployed to staging
- [ ] Tested end-to-end
```
