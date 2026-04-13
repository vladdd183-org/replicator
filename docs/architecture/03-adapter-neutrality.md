# Адаптерная нейтральность

> Один и тот же бизнес-код. Один и тот же Protocol. Разные адаптеры. Web2 сегодня, Web3 завтра.

---

## Принцип

Бизнес-логика (Actions, Tasks, Queries) **никогда** не зависит от конкретного транспорта, хранилища или системы аутентификации. Она зависит от **Protocol** -- абстрактного контракта.

Конкретная реализация (PostgreSQL, IPFS, JWT, UCAN) подставляется через DI на уровне конфигурации.

```
Action --> Protocol (интерфейс) <-- Adapter (реализация)
```

Замена адаптера = замена одной строки в Provider. Бизнес-код не меняется.

---

## Порты (Protocols)

### StoragePort -- хранение неизменяемых данных

```python
from typing import Protocol

class StoragePort(Protocol):
    """Хранение content-addressed данных (файлы, артефакты, модели)."""

    async def put(self, data: bytes, metadata: dict | None = None) -> str:
        """Сохранить данные, вернуть идентификатор (path или CID)."""
        ...

    async def get(self, identifier: str) -> bytes:
        """Получить данные по идентификатору."""
        ...

    async def exists(self, identifier: str) -> bool:
        """Проверить существование."""
        ...

    async def delete(self, identifier: str) -> None:
        """Удалить данные."""
        ...

    async def list_prefix(self, prefix: str) -> list[str]:
        """Список идентификаторов по префиксу."""
        ...
```

| Реализация | Когда |
|---|---|
| `LocalStorageAdapter` | Разработка, тесты |
| `S3StorageAdapter` | Продакшен Web2 |
| `IPFSStorageAdapter` | Web3 (content-addressed, дедупликация, P2P) |

### StatePort -- мутабельное состояние

```python
class StatePort(Protocol):
    """Мутабельное состояние с историей изменений."""

    async def get(self, stream_id: str) -> dict | None:
        """Получить текущее состояние потока."""
        ...

    async def update(self, stream_id: str, patch: dict) -> str:
        """Обновить состояние, вернуть версию."""
        ...

    async def create(self, schema: str, initial_data: dict) -> str:
        """Создать новый поток, вернуть stream_id."""
        ...

    async def history(self, stream_id: str, limit: int = 100) -> list[dict]:
        """Получить историю изменений."""
        ...
```

| Реализация | Когда |
|---|---|
| `PostgresStateAdapter` | Продакшен Web2 |
| `SQLiteStateAdapter` | Разработка, тесты |
| `CeramicStateAdapter` | Web3 (ComposeDB, верифицируемая история, DID) |

### MessagingPort -- обмен сообщениями

```python
from typing import AsyncIterator

class MessagingPort(Protocol):
    """Pub/Sub обмен сообщениями."""

    async def publish(self, topic: str, message: bytes, headers: dict | None = None) -> None:
        """Опубликовать сообщение в топик."""
        ...

    async def subscribe(self, topic: str) -> AsyncIterator[tuple[bytes, dict]]:
        """Подписаться на топик, получать (message, headers)."""
        ...

    async def request(self, topic: str, message: bytes, timeout: float = 5.0) -> bytes:
        """Request-Reply: отправить запрос и дождаться ответа."""
        ...
```

| Реализация | Когда |
|---|---|
| `InMemoryMessagingAdapter` | Тесты |
| `LitestarEventsAdapter` | Монолит (litestar.events) |
| `NATSMessagingAdapter` | Продакшен Web2 (микросервисы) |
| `LatticaMessagingAdapter` | Web3 (libp2p, P2P, CRDT) |

### IdentityPort -- идентификация и авторизация

```python
@dataclass(frozen=True)
class Identity:
    subject: str                    # кто (user_id или DID)
    capabilities: list[str]         # что разрешено
    metadata: dict                  # дополнительные данные

class IdentityPort(Protocol):
    """Идентификация и авторизация."""

    async def verify(self, token: str) -> Identity:
        """Верифицировать токен, вернуть Identity."""
        ...

    async def issue(self, subject: str, capabilities: list[str], ttl_seconds: int = 3600) -> str:
        """Выдать токен."""
        ...

    async def delegate(self, parent_token: str, capabilities: list[str]) -> str:
        """Делегировать подмножество capabilities дочернему токену."""
        ...

    async def revoke(self, token: str) -> None:
        """Отозвать токен."""
        ...
```

| Реализация | Когда |
|---|---|
| `JWTIdentityAdapter` | Web2 (стандартный JWT) |
| `UCANIdentityAdapter` | Web3 (DID + UCAN с делегированием и атенюацией) |

### ComputePort -- исполнение вычислений

```python
@dataclass(frozen=True)
class ComputeResult:
    output: bytes
    output_id: str                  # hash или CID результата
    duration_ms: int
    evidence: dict                  # proof of execution

class ComputePort(Protocol):
    """Исполнение изолированных вычислений."""

    async def execute(
        self,
        function_id: str,           # идентификатор функции/модуля
        input_data: bytes,
        timeout_seconds: float = 60.0,
    ) -> ComputeResult:
        """Исполнить функцию над данными."""
        ...
```

| Реализация | Когда |
|---|---|
| `SubprocessComputeAdapter` | Разработка |
| `DockerComputeAdapter` | Продакшен Web2 |
| `IPVMComputeAdapter` | Web3 (WASM на IPFS, глобальная мемоизация) |

---

## DI-связывание адаптеров

```python
# Ship/Providers/AdapterProvider.py

from dishka import Provider, Scope, provide

class LocalAdapterProvider(Provider):
    """Адаптеры для локальной разработки."""
    scope = Scope.APP

    storage = provide(LocalStorageAdapter, provides=StoragePort)
    state = provide(SQLiteStateAdapter, provides=StatePort)
    messaging = provide(InMemoryMessagingAdapter, provides=MessagingPort)
    identity = provide(JWTIdentityAdapter, provides=IdentityPort)
    compute = provide(SubprocessComputeAdapter, provides=ComputePort)


class ProductionAdapterProvider(Provider):
    """Адаптеры для продакшена (Web2)."""
    scope = Scope.APP

    storage = provide(S3StorageAdapter, provides=StoragePort)
    state = provide(PostgresStateAdapter, provides=StatePort)
    messaging = provide(NATSMessagingAdapter, provides=MessagingPort)
    identity = provide(JWTIdentityAdapter, provides=IdentityPort)
    compute = provide(DockerComputeAdapter, provides=ComputePort)


class HybridAdapterProvider(Provider):
    """Гибридные адаптеры (Web2 + первые Web3)."""
    scope = Scope.APP

    storage = provide(IPFSStorageAdapter, provides=StoragePort)    # Web3
    state = provide(PostgresStateAdapter, provides=StatePort)       # Web2
    messaging = provide(NATSMessagingAdapter, provides=MessagingPort) # Web2
    identity = provide(JWTIdentityAdapter, provides=IdentityPort)   # Web2
    compute = provide(DockerComputeAdapter, provides=ComputePort)   # Web2
```

Выбор Provider -- одна строка в `create_app()`:

```python
def get_adapter_provider() -> Provider:
    settings = get_settings()
    match settings.adapter_mode:
        case "local":
            return LocalAdapterProvider()
        case "production":
            return ProductionAdapterProvider()
        case "hybrid":
            return HybridAdapterProvider()
```

---

## Использование в бизнес-логике

Action не знает про конкретный адаптер. Он зависит от Protocol:

```python
class SaveArtifactAction(Action[SaveArtifactRequest, str, ArtifactError]):
    def __init__(self, storage: StoragePort) -> None:
        self.storage = storage

    async def run(self, data: SaveArtifactRequest) -> Result[str, ArtifactError]:
        identifier = await self.storage.put(data.content, {"name": data.name})
        return Success(identifier)
```

Этот код работает одинаково с LocalFS, S3 и IPFS. Замена -- через DI.
