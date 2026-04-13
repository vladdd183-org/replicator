# P0 Beads: Ship Foundation

> Critical path. Без этих Beads ничто другое не может начаться.

---

## B-SHIP-CORE-001: Базовые типы для адаптерной нейтральности

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Core/Types.py` (расширение)
- **Acceptance:**
  - [ ] Определен тип `CID` (str alias, с валидацией формата)
  - [ ] Определен тип `Identity` (dataclass: subject, capabilities, metadata)
  - [ ] Определен тип `Capability` (dataclass: resource, action, constraints)
  - [ ] Определен тип `ComputeResult` (dataclass: output, output_id, duration_ms, evidence)
  - [ ] Все типы -- frozen dataclasses или Pydantic frozen models
- **Зависимости:** нет
- **Приоритет:** P0

---

## B-SHIP-ADAPT-001: Protocols (интерфейсы адаптеров)

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Adapters/Protocols.py`
- **Acceptance:**
  - [ ] Определен `StoragePort` (Protocol) с методами put, get, exists, delete, list_prefix
  - [ ] Определен `StatePort` (Protocol) с методами get, update, create, history
  - [ ] Определен `MessagingPort` (Protocol) с методами publish, subscribe, request
  - [ ] Определен `IdentityPort` (Protocol) с методами verify, issue, delegate, revoke
  - [ ] Определен `ComputePort` (Protocol) с методом execute
  - [ ] Все методы async, все type-annotated
- **Зависимости:** B-SHIP-CORE-001
- **Приоритет:** P0

---

## B-SHIP-ADAPT-002: Ошибки адаптеров

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Adapters/Errors.py`
- **Acceptance:**
  - [ ] `AdapterError(BaseError)` -- базовая ошибка адаптеров
  - [ ] `StorageNotFoundError`, `StorageWriteError`
  - [ ] `MessagingTimeoutError`
  - [ ] `IdentityVerificationError`
  - [ ] `ComputeTimeoutError`
  - [ ] Все -- Pydantic frozen, с http_status и code
- **Зависимости:** нет
- **Приоритет:** P0

---

## B-SHIP-ADAPT-003: LocalStorageAdapter

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Adapters/Storage/LocalAdapter.py`
- **Acceptance:**
  - [ ] Реализует `StoragePort`
  - [ ] Хранит файлы в configurable директории
  - [ ] `put` возвращает sha256 hash как идентификатор
  - [ ] `get` бросает `StorageNotFoundError` если файл не найден
  - [ ] `list_prefix` возвращает список файлов по префиксу пути
  - [ ] Тест: put -> get -> roundtrip
- **Зависимости:** B-SHIP-ADAPT-001, B-SHIP-ADAPT-002
- **Приоритет:** P0

---

## B-SHIP-ADAPT-004: InMemoryMessagingAdapter

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Adapters/Messaging/InMemoryAdapter.py`
- **Acceptance:**
  - [ ] Реализует `MessagingPort`
  - [ ] In-memory pub/sub с asyncio.Queue
  - [ ] `subscribe` возвращает AsyncIterator
  - [ ] `request` с timeout
  - [ ] Тест: publish -> subscribe -> receive
- **Зависимости:** B-SHIP-ADAPT-001
- **Приоритет:** P0

---

## B-SHIP-ADAPT-005: JWTIdentityAdapter

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Adapters/Identity/JWTAdapter.py`
- **Acceptance:**
  - [ ] Реализует `IdentityPort`
  - [ ] Обертка над существующим `Ship/Auth/JWT.py`
  - [ ] `verify` -> `Identity`
  - [ ] `issue` -> JWT token string
  - [ ] `delegate` -> новый JWT с подмножеством capabilities
  - [ ] `revoke` -- no-op для JWT (stateless)
- **Зависимости:** B-SHIP-ADAPT-001, B-SHIP-CORE-001
- **Приоритет:** P0

---

## B-SHIP-ADAPT-006: SQLiteStateAdapter

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Adapters/State/SQLiteAdapter.py`
- **Acceptance:**
  - [ ] Реализует `StatePort`
  - [ ] Хранит streams как JSON в SQLite таблице
  - [ ] `create` возвращает UUID stream_id
  - [ ] `update` сохраняет patch + новую запись в history
  - [ ] `history` возвращает хронологический список patches
  - [ ] Тест: create -> update -> get -> history
- **Зависимости:** B-SHIP-ADAPT-001
- **Приоритет:** P0

---

## B-SHIP-ADAPT-007: SubprocessComputeAdapter

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Adapters/Compute/SubprocessAdapter.py`
- **Acceptance:**
  - [ ] Реализует `ComputePort`
  - [ ] Запускает процесс через anyio.run_process
  - [ ] Таймаут через anyio.fail_after
  - [ ] Возвращает ComputeResult с stdout, sha256 output, duration
  - [ ] Тест: execute simple command -> ComputeResult
- **Зависимости:** B-SHIP-ADAPT-001, B-SHIP-CORE-001
- **Приоритет:** P0

---

## B-SHIP-ADAPT-008: AdapterProvider

- **Spec:** ship-adapters.spec.md
- **Компонент:** `Ship/Providers/AdapterProvider.py`
- **Acceptance:**
  - [ ] `LocalAdapterProvider` -- все Web2 локальные адаптеры
  - [ ] Каждый адаптер provide-ится с `provides=XxxPort`
  - [ ] `get_adapter_provider(settings)` выбирает Provider по adapter_mode
  - [ ] Интеграция в `get_all_providers()`
- **Зависимости:** B-SHIP-ADAPT-003 .. B-SHIP-ADAPT-007
- **Приоритет:** P0

---

## B-SHIP-CELL-001: CellSpec dataclass

- **Spec:** ship-cell.spec.md
- **Компонент:** `Ship/Cell/CellSpec.py`
- **Acceptance:**
  - [ ] `CellSpec` -- frozen dataclass со всеми полями из спецификации
  - [ ] `CellStatus` -- enum (DRAFT, ACTIVE, DEPRECATED, ARCHIVED)
  - [ ] `ResourceBudget` -- frozen dataclass
  - [ ] `HealthCheckConfig` -- frozen dataclass
  - [ ] `compute_spec_hash()` -- SHA-256 от JSON-сериализации spec (без spec_hash поля)
  - [ ] Тест: создание CellSpec, проверка immutability, проверка hash стабильности
- **Зависимости:** B-SHIP-CORE-001
- **Приоритет:** P0

---

## B-SHIP-CELL-002: Capabilities

- **Spec:** ship-cell.spec.md
- **Компонент:** `Ship/Cell/Capabilities.py`
- **Acceptance:**
  - [ ] `Capability` dataclass (resource, action, constraints)
  - [ ] `check_capability(required, granted) -> bool` -- проверка
  - [ ] `attenuate(parent_caps, child_caps) -> list[Capability]` -- атенюация (сужение)
  - [ ] Тест: check разрешает, check отказывает, attenuate сужает
- **Зависимости:** B-SHIP-CORE-001
- **Приоритет:** P0

---

## B-SHIP-CELL-003: CellRegistryPort

- **Spec:** ship-cell.spec.md
- **Компонент:** `Ship/Cell/Registry.py`
- **Acceptance:**
  - [ ] `CellRegistryPort` (Protocol) с методами register, get, list_all, list_by_section, get_history
  - [ ] Все методы async, type-annotated
- **Зависимости:** B-SHIP-CELL-001
- **Приоритет:** P0

---

## Сводка P0

| Bead | Компонент | Зависит от |
|---|---|---|
| B-SHIP-CORE-001 | Core/Types.py | -- |
| B-SHIP-ADAPT-001 | Adapters/Protocols.py | CORE-001 |
| B-SHIP-ADAPT-002 | Adapters/Errors.py | -- |
| B-SHIP-ADAPT-003 | Storage/LocalAdapter.py | ADAPT-001, ADAPT-002 |
| B-SHIP-ADAPT-004 | Messaging/InMemoryAdapter.py | ADAPT-001 |
| B-SHIP-ADAPT-005 | Identity/JWTAdapter.py | ADAPT-001, CORE-001 |
| B-SHIP-ADAPT-006 | State/SQLiteAdapter.py | ADAPT-001 |
| B-SHIP-ADAPT-007 | Compute/SubprocessAdapter.py | ADAPT-001, CORE-001 |
| B-SHIP-ADAPT-008 | Providers/AdapterProvider.py | ADAPT-003..007 |
| B-SHIP-CELL-001 | Cell/CellSpec.py | CORE-001 |
| B-SHIP-CELL-002 | Cell/Capabilities.py | CORE-001 |
| B-SHIP-CELL-003 | Cell/Registry.py | CELL-001 |

**Итого: 12 Beads, P0 critical path.**
