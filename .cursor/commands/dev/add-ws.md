# /add-ws — Создание WebSocket Handler

Создание WebSocket handler для real-time функциональности.

## Источники

- **Инструкция:** `agent-os/commands/add-websocket.md`
- Skill: `.cursor/skills/add-websocket/SKILL.md`
- Docs: `docs/11-litestar-features.md`

## Синтаксис

```
/add-ws <HandlerName> [в <Module>] [--path <path>]
```

## Примеры

```
/add-ws ChatHandler в UserModule --path /ws/chat/{room_id}
/add-ws NotificationsHandler в NotificationModule --path /ws/notifications
/add-ws DashboardStats в SettingsModule --path /ws/dashboard
```

## Параметры

- `<HandlerName>` — Название handler (PascalCase)
- `[в <Module>]` — Модуль для размещения
- `[--path]` — WebSocket path (по умолчанию /ws/{name})

## Действие

1. Загрузи skill из `.cursor/skills/add-websocket/SKILL.md`
2. Создай `UI/WebSocket/Handlers.py`
3. Используй Litestar Channels для pub/sub
4. Зарегистрируй в `App.py`

## WebSocket Template

```python
@websocket("/ws/path")
async def handler(socket: WebSocket, channels: ChannelsPlugin) -> None:
    await socket.accept()
    
    async with channels.start_subscription(["channel"]) as sub:
        try:
            async for message in sub.iter_events():
                await socket.send_json(message)
        finally:
            await socket.close()
```

## Channels Plugin

```python
# В App.py
from litestar.channels import ChannelsPlugin
from litestar.channels.backends.memory import MemoryChannelsBackend

channels = ChannelsPlugin(backend=MemoryChannelsBackend())
```
