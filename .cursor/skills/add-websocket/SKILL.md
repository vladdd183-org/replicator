---
name: add-websocket
description: Create WebSocket handlers for Hyper-Porto with Litestar. Use when the user wants to add websocket, create ws handler, realtime, добавить websocket, вебсокет, реалтайм.
---

# Add WebSocket Handler

Создание WebSocket handlers с Litestar.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-websocket.md` |
| **Template** | `agent-os/templates/websocket-handler.py.template` |
| **Docs** | `docs/09-transports.md` (WebSocket секция) |
| **Docs** | `docs/11-litestar-features.md` (Channels) |

## Быстрая справка

| Правило | Описание |
|---------|----------|
| **Framework** | Litestar WebSocket |
| **Location** | `UI/WebSocket/Handlers.py` |
| **Channels** | Litestar Channels для pub/sub |
| **Auth** | Через middleware или on_connect |
| **DI** | Через `FromDishka[T]` |

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-websocket.md`
2. **Создай** handler в `UI/WebSocket/Handlers.py`
3. **Настрой** Channels plugin в `App.py` (если нужен pub/sub)
4. **Зарегистрируй** handlers в `route_handlers`
5. **Добавь** authentication если нужно

## Базовая структура

```python
@websocket("/ws/path")
async def handler(socket: WebSocket) -> None:
    await socket.accept()
    try:
        while True:
            data = await socket.receive_json()
            await socket.send_json({"status": "ok"})
    except Exception:
        pass
    finally:
        await socket.close()
```

## Channels (pub/sub)

```python
@websocket("/ws/notifications")
async def notifications(socket: WebSocket, channels: ChannelsPlugin) -> None:
    await socket.accept()
    async with channels.start_subscription(["user:123"]) as subscriber:
        async for message in subscriber.iter_events():
            await socket.send_json(message)
```

## Важно

- ВСЕГДА `await socket.accept()` перед отправкой
- ВСЕГДА `socket.close()` в `finally` блоке
- Проверять auth ПЕРЕД `accept()` если нужно
