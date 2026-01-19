# /add-event — Создание Domain Event

Создание Domain Event и Listener для межмодульного общения.

## Источники

- **Инструкция:** `agent-os/commands/add-event.md`
- Skill: `.cursor/skills/add-event/SKILL.md`
- Docs: `docs/11-litestar-features.md`

## Синтаксис

```
/add-event <EventName> [в <Module>] [--listener <ListenerName>]
```

## Примеры

```
/add-event UserCreated в UserModule
/add-event OrderPaid в OrderModule --listener on_order_paid_send_receipt
/add-event PaymentFailed в PaymentModule
```

## Параметры

- `<EventName>` — Название Event (PascalCase, например UserCreated)
- `[в <Module>]` — Модуль для размещения
- `[--listener]` — Имя listener функции (опционально)

## Действие

1. Загрузи skill из `.cursor/skills/add-event/SKILL.md`
2. Добавь Event в `Events.py`
3. Создай Listener в `Listeners.py` (если указан)
4. Зарегистрируй listener в `App.py`
5. Добавь `uow.add_event()` в Action

## Event Flow

```
Action.run() 
  → uow.add_event(Event) 
  → uow.commit() 
  → litestar.emit(Event) 
  → Listener(Event)
```

## Naming Convention

| Действие | Event | Listener |
|----------|-------|----------|
| Создание | `{Entity}Created` | `on_{entity}_created_{action}` |
| Обновление | `{Entity}Updated` | `on_{entity}_updated_{action}` |
| Удаление | `{Entity}Deleted` | `on_{entity}_deleted_{action}` |
