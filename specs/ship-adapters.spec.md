# Спецификация: Ship/Adapters

> Транспортный слой L0. Protocol-интерфейсы с подменяемыми Web2/Web3 реализациями.

---

## Назначение

Абстрагировать внешнюю инфраструктуру (хранилище, messaging, identity, state, compute) за Protocol-интерфейсами. Позволить переключение Web2 <-> Web3 через DI без изменения бизнес-логики.

## Acceptance Criteria

- [ ] Определены 5 Protocol-ов: StoragePort, StatePort, MessagingPort, IdentityPort, ComputePort
- [ ] Каждый Protocol имеет минимум 1 Web2 реализацию
- [ ] Все Protocol-ы зарегистрированы в Dishka Provider
- [ ] Action-ы зависят от Protocol-ов, а не от конкретных реализаций
- [ ] Переключение окружения (local/production/hybrid) через одну настройку
- [ ] Существующий Ship код (Auth/JWT, Infrastructure/Database) обернут в адаптеры
- [ ] Тесты используют InMemory/Mock адаптеры

## Интерфейсы (Protocols)

### StoragePort

```python
class StoragePort(Protocol):
    async def put(self, data: bytes, metadata: dict | None = None) -> str: ...
    async def get(self, identifier: str) -> bytes: ...
    async def exists(self, identifier: str) -> bool: ...
    async def delete(self, identifier: str) -> None: ...
    async def list_prefix(self, prefix: str) -> list[str]: ...
```

Web2: LocalStorageAdapter (файловая система)
Web3 (будущее): IPFSStorageAdapter

### StatePort

```python
class StatePort(Protocol):
    async def get(self, stream_id: str) -> dict | None: ...
    async def update(self, stream_id: str, patch: dict) -> str: ...
    async def create(self, schema: str, initial_data: dict) -> str: ...
    async def history(self, stream_id: str, limit: int = 100) -> list[dict]: ...
```

Web2: PostgresStateAdapter (Piccolo), SQLiteStateAdapter
Web3 (будущее): CeramicStateAdapter

### MessagingPort

```python
class MessagingPort(Protocol):
    async def publish(self, topic: str, message: bytes, headers: dict | None = None) -> None: ...
    async def subscribe(self, topic: str) -> AsyncIterator[tuple[bytes, dict]]: ...
    async def request(self, topic: str, message: bytes, timeout: float = 5.0) -> bytes: ...
```

Web2: InMemoryMessagingAdapter, LitestarEventsAdapter
Web3 (будущее): LatticaMessagingAdapter (libp2p)

### IdentityPort

```python
class IdentityPort(Protocol):
    async def verify(self, token: str) -> Identity: ...
    async def issue(self, subject: str, capabilities: list[str], ttl_seconds: int = 3600) -> str: ...
    async def delegate(self, parent_token: str, capabilities: list[str]) -> str: ...
    async def revoke(self, token: str) -> None: ...
```

Web2: JWTIdentityAdapter (обертка над Ship/Auth/JWT)
Web3 (будущее): UCANIdentityAdapter

### ComputePort

```python
class ComputePort(Protocol):
    async def execute(self, function_id: str, input_data: bytes, timeout_seconds: float = 60.0) -> ComputeResult: ...
```

Web2: SubprocessComputeAdapter
Web3 (будущее): IPVMComputeAdapter

## Зависимости

- `Ship/Core/Types.py` -- типы Identity, CID, Capability
- `Ship/Configs/Settings.py` -- настройка adapter_mode
- `dishka` -- DI Provider

## Data Models

```python
@dataclass(frozen=True)
class Identity:
    subject: str
    capabilities: list[str]
    metadata: dict

@dataclass(frozen=True)
class ComputeResult:
    output: bytes
    output_id: str
    duration_ms: int
    evidence: dict
```

## Ошибки

```python
class AdapterError(BaseError): ...
class StorageNotFoundError(AdapterError): ...
class StorageWriteError(AdapterError): ...
class MessagingTimeoutError(AdapterError): ...
class IdentityVerificationError(AdapterError): ...
class ComputeTimeoutError(AdapterError): ...
```

## События

Адаптеры не генерируют Domain Events. Они -- чистая инфраструктура.
