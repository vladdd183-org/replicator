---
name: add-event
description: Create Domain Event and Listener for Hyper-Porto architecture. Events enable loose coupling between modules. Use when the user wants to add event, create event, домен событие, добавить event, listener, слушатель.
---

# Add Domain Event + Listener

Создание Domain Event и Listener.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-event.md` |
| **Template** | `agent-os/templates/event.py.template` |
| **Workflow** | `agent-os/workflows/add-domain-event.md` |
| **Docs** | `docs/11-litestar-features.md` |

## Быстрая справка

| Правило | Описание |
|---------|----------|
| **Event** | Pydantic frozen model в `Events.py` |
| **Listener** | Async функция в `Listeners.py` |
| **Publishing** | Через `uow.add_event()` перед commit |
| **Cross-module** | Events — ЕДИНСТВЕННЫЙ способ коммуникации |
| **Registration** | В `App.py` через Litestar events |

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-event.md`
2. **Создай** Event class в `Events.py` (наследник `DomainEvent`)
3. **Создай** Listener(s) в `Listeners.py`
4. **Зарегистрируй** listeners в `App.py`
5. **Публикуй** через `uow.add_event()` в Action

## Именование

### Events
| Действие | Паттерн | Пример |
|----------|---------|--------|
| Created | `{Entity}Created` | `UserCreated` |
| Updated | `{Entity}Updated` | `UserUpdated` |
| Deleted | `{Entity}Deleted` | `UserDeleted` |
| Status | `{Entity}{Status}` | `OrderPaid` |

### Listeners
| Паттерн | Пример |
|---------|--------|
| `on_{event}_{action}` | `on_user_created_send_welcome_email` |

## Cross-Module правило

```
❌ ЗАПРЕЩЕНО: UserModule импортирует OrderModule
✅ ПРАВИЛЬНО: OrderModule emits Event → UserModule listens
```
