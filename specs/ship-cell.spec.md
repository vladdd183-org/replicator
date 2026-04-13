# Спецификация: Ship/Cell

> Cell Engine (L2). Жизненный цикл Container как исполняемой единицы.

---

## Назначение

Превратить Porto Container из структуры папок в адресуемую, версионируемую, инстанцируемую единицу вычислений. Минимальная реализация для Web2 с заделом на Web3.

## Acceptance Criteria

- [ ] CellSpec -- frozen dataclass с полным описанием Container
- [ ] spec_hash вычисляется автоматически (SHA-256 от сериализованного spec)
- [ ] Supervisor может создавать, проверять health, перезапускать Cell
- [ ] Capabilities -- базовые RBAC-проверки через DI scope
- [ ] ResourceBudget -- конфигурируемые лимиты (CPU, RAM, storage, network)
- [ ] Registry Protocol -- интерфейс реестра спецификаций
- [ ] Каждый Container МОЖЕТ (опционально) экспортировать cell_spec

## Компоненты

### CellSpec

```python
@dataclass(frozen=True)
class CellSpec:
    name: str
    version: str
    description: str
    section: str
    spec_hash: str
    actions: list[str]
    tasks: list[str]
    queries: list[str]
    events_emitted: list[str]
    events_consumed: list[str]
    capabilities_required: list[str]
    dependencies: list[str]
    adapters_required: list[str]
    resources: ResourceBudget
    health_check: HealthCheckConfig
    status: CellStatus
    parent_spec_hash: str | None
    tags: list[str]
```

### CellSupervisor

```python
class CellSupervisor:
    async def spawn(self, spec: CellSpec) -> CellHandle: ...
    async def health_check(self, handle: CellHandle) -> HealthStatus: ...
    async def restart(self, handle: CellHandle) -> CellHandle: ...
    async def shutdown(self, handle: CellHandle) -> None: ...
    async def evolve(self, handle: CellHandle, new_spec: CellSpec) -> CellHandle: ...
```

### Capabilities

```python
@dataclass(frozen=True)
class Capability:
    resource: str
    action: str
    constraints: dict
```

### CellRegistryPort (Protocol)

```python
class CellRegistryPort(Protocol):
    async def register(self, spec: CellSpec) -> None: ...
    async def get(self, name: str, version: str | None = None) -> CellSpec | None: ...
    async def list_all(self) -> list[CellSpec]: ...
    async def list_by_section(self, section: str) -> list[CellSpec]: ...
    async def get_history(self, name: str) -> list[CellSpec]: ...
```

## Зависимости

- `Ship/Core/Types.py` -- базовые типы
- `Ship/Adapters/Protocols.py` -- StoragePort (для хранения specs)
- `hashlib` -- вычисление spec_hash

## Ошибки

```python
class CellError(BaseError): ...
class CellNotFoundError(CellError): ...
class CellAlreadyExistsError(CellError): ...
class CellSpawnError(CellError): ...
class CapabilityDeniedError(CellError): ...
class ResourceExhaustedError(CellError): ...
```

## События

```python
class CellSpawned(DomainEvent): ...
class CellHealthChanged(DomainEvent): ...
class CellEvolved(DomainEvent): ...
class CellShutdown(DomainEvent): ...
```
