# Модель Cell: от теории к Porto

> Cell = f(Spec, Capabilities, State) -- фундаментальный примитив вычислений. Как он маппится на Porto Container.

---

## Теоретическая основа

Из исследования Фрактального Атома:

> **Cell** -- живая единица вычислений с тремя компонентами:
> - **Spec** -- ДНК: что Cell умеет (CID-адресуемая спецификация)
> - **Capabilities** -- мембрана: что Cell ПОЗВОЛЕНО делать
> - **State** -- память: текущее состояние

### Три закона Cell

1. **Закон Content Addressing** -- все есть идентификатор содержимого. Одни и те же входы -> один и тот же выход.
2. **Закон Фрактальности** -- любая Cell может создать внутри себя другую Cell с тем же интерфейсом.
3. **Закон Эволюции** -- система может модифицировать собственный код, тестировать и промоутить успешные мутации.

---

## Маппинг Cell -> Porto Container

| Cell | Porto | Файл |
|---|---|---|
| **Spec** (ДНК) | Actions + Tasks + Models + Events + Errors | `{Module}/Actions/*.py`, `{Module}/Tasks/*.py` |
| **Capabilities** (мембрана) | Providers.py + DI scopes + Auth guards | `{Module}/Providers.py` |
| **State** (память) | UnitOfWork + Repository + Domain Events | `{Module}/Data/UnitOfWork.py` |
| **Interface** (рецепторы) | UI/ (API, CLI, WebSocket, Workers) | `{Module}/UI/` |
| **Identity** (CID) | CellSpec.spec_hash | `Ship/Cell/CellSpec.py` |
| **Spawn** (деление) | Генерация нового Container | `CoreSection/TemplateModule/` |
| **Evolution** (мутация) | Новая версия Spec -> тесты -> promotion | `CoreSection/EvolutionModule/` |

---

## CellSpec -- декларативная спецификация Container

```python
from dataclasses import dataclass, field
from enum import Enum

class CellStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

@dataclass(frozen=True)
class ResourceBudget:
    max_cpu_seconds: float = 60.0
    max_memory_mb: int = 512
    max_storage_mb: int = 1024
    max_network_calls: int = 1000

@dataclass(frozen=True)
class HealthCheckConfig:
    endpoint: str = "/health"
    interval_seconds: int = 30
    timeout_seconds: int = 5
    unhealthy_threshold: int = 3

@dataclass(frozen=True)
class CellSpec:
    name: str
    version: str
    description: str
    section: str
    spec_hash: str                              # sha256 спецификации -> CID в будущем

    # Что Cell умеет
    actions: list[str] = field(default_factory=list)      # список Action-ов
    tasks: list[str] = field(default_factory=list)        # список Task-ов
    queries: list[str] = field(default_factory=list)      # список Query
    events_emitted: list[str] = field(default_factory=list)  # какие события генерирует
    events_consumed: list[str] = field(default_factory=list) # на какие события подписана

    # Что Cell нужно
    capabilities_required: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    adapters_required: list[str] = field(default_factory=list)

    # Ресурсы и здоровье
    resources: ResourceBudget = field(default_factory=ResourceBudget)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)

    # Метаданные
    status: CellStatus = CellStatus.DRAFT
    parent_spec_hash: str | None = None          # от какой версии произошла
    tags: list[str] = field(default_factory=list)
```

---

## Supervisor -- жизненный цикл Cell

```python
class CellSupervisor:
    """Управляет жизненным циклом Cell (Container в runtime)."""

    async def spawn(self, spec: CellSpec) -> CellHandle:
        """Создать и запустить Cell по спецификации."""

    async def health_check(self, handle: CellHandle) -> HealthStatus:
        """Проверить здоровье Cell."""

    async def restart(self, handle: CellHandle) -> CellHandle:
        """Перезапустить Cell."""

    async def shutdown(self, handle: CellHandle) -> None:
        """Остановить Cell."""

    async def evolve(self, handle: CellHandle, new_spec: CellSpec) -> CellHandle:
        """Обновить Cell до новой версии спецификации."""
```

В Web2 реальности `spawn` -- это запуск Container как модуля Litestar или как отдельного процесса. В Web3 -- создание изолированной OCI/WASM Cell.

---

## Capabilities -- что Cell позволено делать

```python
@dataclass(frozen=True)
class Capability:
    resource: str           # к какому ресурсу доступ
    action: str             # какое действие разрешено
    constraints: dict       # ограничения (TTL, scope, атрибуты)

# Примеры
Capability(resource="storage", action="read", constraints={"prefix": "/data/models/"})
Capability(resource="messaging", action="publish", constraints={"topics": ["events.*"]})
Capability(resource="compute", action="execute", constraints={"max_duration_s": 300})
```

В Web2: capabilities -- это просто RBAC-проверки через DI scope.
В Web3: capabilities станут UCAN-токенами с делегированием и атенюацией.

**Принцип атенюации:** Cell может передать дочерней Cell только подмножество своих capabilities, никогда -- расширить.

---

## Фрактальность: Cell содержит Cell-ы

```
Replicator (Root Cell)
  |
  +-- CoreSection (Section Cell)
  |     +-- SpecModule (Module Cell)
  |     |     +-- CompileSpecAction (Action -- листовой уровень)
  |     |     +-- ValidateSpecTask (Task -- листовой уровень)
  |     +-- TemplateModule (Module Cell)
  |     +-- EvolutionModule (Module Cell)
  |
  +-- AgentSection (Section Cell)
  |     +-- CompassModule (Module Cell)
  |     +-- MakerModule (Module Cell)
  |
  +-- ToolSection (Section Cell)
        +-- MCPClientModule (Module Cell)
        +-- GitModule (Module Cell)
```

На каждом уровне -- одинаковый интерфейс: Spec + Capabilities + State.

Section -- это Cell с дочерними Module-Cell-ами.
Module -- это Cell с дочерними Action/Task-Cell-ами.
Action -- это вырожденная Cell (только computation, без вложенности).

---

## Эволюция Cell

```
Версия 1 (spec_hash: abc123)
    |
    |  мутация: добавлен новый Action
    v
Версия 2 (spec_hash: def456, parent: abc123)
    |
    |  fitness test: тесты, метрики, evidence
    |
    |  pass -> promote: версия 2 становится active
    |  fail -> rollback: версия 1 остается active
    v
Версия 2 ACTIVE (или Версия 1 если fail)
```

Старые версии НИКОГДА не удаляются. Они переходят в статус `deprecated` или `archived`. В будущем с CID -- каждая версия навечно адресуема по хешу.
