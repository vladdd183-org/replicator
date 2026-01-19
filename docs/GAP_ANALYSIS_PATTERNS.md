# 📋 Gap Analysis: Современные паттерны и библиотеки

> **Статус:** Анализ расхождений между текущей реализацией и рекомендациями  
> **Дата:** Январь 2026  
> **Источник:** Исследование современных научных паттернов

---

## 🔴 Отсутствует в текущей реализации

### 1. Specification Pattern для сложных запросов

**Что это:** Инкапсуляция критериев фильтрации в переиспользуемые объекты (Fowler, Evans DDD).

**Зачем нужно:**
- Улучшает читаемость сложных queries
- Композируемые фильтры (`spec.and_(other_spec)`)
- Переиспользование логики фильтрации между Repository и бизнес-кодом

**Реализация:**

```python
# src/Ship/Parents/Specification.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")

class Specification(ABC, Generic[T]):
    """Base specification for domain queries."""
    
    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """Check if entity satisfies specification (in-memory)."""
        ...
    
    @abstractmethod
    def to_query(self) -> "QueryExpression":
        """Convert to ORM query expression (Piccolo)."""
        ...
    
    def and_(self, other: "Specification[T]") -> "Specification[T]":
        return AndSpecification(self, other)
    
    def or_(self, other: "Specification[T]") -> "Specification[T]":
        return OrSpecification(self, other)
    
    def not_(self) -> "Specification[T]":
        return NotSpecification(self)


# Пример использования в UserModule
class ActiveUserSpec(Specification[AppUser]):
    def is_satisfied_by(self, user: AppUser) -> bool:
        return user.is_active
    
    def to_query(self):
        return AppUser.is_active == True

class EmailDomainSpec(Specification[AppUser]):
    def __init__(self, domain: str):
        self.domain = domain
    
    def is_satisfied_by(self, user: AppUser) -> bool:
        return user.email.endswith(f"@{self.domain}")
    
    def to_query(self):
        return AppUser.email.like(f"%@{self.domain}")

# В Repository
async def find_by_spec(self, spec: Specification[AppUser]) -> list[AppUser]:
    return await AppUser.select().where(spec.to_query())

# Композиция
active_corp_users = await repo.find_by_spec(
    ActiveUserSpec().and_(EmailDomainSpec("corp.com"))
)
```

**Effort:** Medium  
**Priority:** 🟡 Medium

---

### 2. AggregateRoot с Domain Invariants

**Что это:** Базовый класс для Aggregate Roots с автоматической валидацией бизнес-правил.

**Зачем нужно:**
- Бизнес-правила встроены в доменные объекты
- Невозможно создать невалидный Aggregate
- Domain Events из Aggregate

**Реализация:**

```python
# src/Ship/Parents/AggregateRoot.py
from pydantic import BaseModel, model_validator
from typing import Self
from src.Ship.Parents.Event import DomainEvent

class AggregateRoot(BaseModel):
    """Base class for Aggregate Roots with invariant validation."""
    
    model_config = {"validate_assignment": True}  # Валидация при изменении
    
    _domain_events: list[DomainEvent] = []
    
    def add_domain_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> list[DomainEvent]:
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events


# Пример: Order Aggregate
class Order(AggregateRoot):
    items: list[OrderItem]
    status: OrderStatus
    total: Decimal
    paid_amount: Decimal = Decimal("0")
    
    @model_validator(mode="after")
    def validate_invariants(self) -> Self:
        # Инвариант 1: Заказ не может быть пустым
        if not self.items:
            raise ValueError("Order must have at least one item")
        
        # Инвариант 2: Total должен соответствовать items
        calculated = sum(i.price * i.quantity for i in self.items)
        if self.total != calculated:
            raise ValueError("Total mismatch")
        
        return self
    
    def can_be_shipped(self) -> bool:
        """Business rule: можно отправить только оплаченный заказ."""
        return self.paid_amount >= self.total
```

**Effort:** Medium  
**Priority:** 🟡 Medium

---

### 3. msgspec для высокопроизводительной сериализации

**Что это:** Библиотека сериализации от разработчика uvicorn, **5-10x быстрее Pydantic v2**.

**Зачем нужно:**
- Hot paths (высоконагруженные endpoints)
- Kafka/Redis сообщения
- Response serialization

**Когда использовать:**

| Сценарий | Pydantic | msgspec |
|----------|----------|---------|
| Request DTOs (валидация) | ✅ Лучше | ❌ Нет валидации |
| Response serialization | Хорошо | ✅ 10x быстрее |
| Internal data transfer | Хорошо | ✅ Быстрее |
| Kafka/Redis messages | Хорошо | ✅ Намного быстрее |

**Реализация:**

```python
import msgspec

# Для высоконагруженных Response
class UserResponseFast(msgspec.Struct):
    id: str
    email: str
    name: str
    created_at: str

# В Controller для hot paths
@get("/users/{user_id}/fast")
async def get_user_fast(user_id: UUID, repo: FromDishka[UserRepository]) -> Response:
    user = await repo.get(user_id)
    response = UserResponseFast(
        id=str(user.id),
        email=user.email,
        name=user.name,
        created_at=user.created_at.isoformat(),
    )
    return Response(
        content=msgspec.json.encode(response),
        media_type="application/json",
    )
```

**Добавить в pyproject.toml:**
```toml
"msgspec>=0.18",
```

**Effort:** Low  
**Priority:** 🟡 Medium (для hot paths)

---

### 4. Polars для аналитических Queries

**Что это:** DataFrame библиотека на Rust, **10-100x быстрее pandas**.

**Зачем нужно:**
- Аналитические Queries в CQRS
- SearchModule, AuditModule
- Отчёты и дашборды

**Реализация:**

```python
import polars as pl
from src.Ship.Parents.Query import Query

class AnalyticsQuery(Query[AnalyticsInput, AnalyticsResult]):
    """CQRS Query для аналитики с Polars."""
    
    async def execute(self, input: AnalyticsInput) -> AnalyticsResult:
        # Загружаем данные напрямую из БД
        df = pl.read_database(
            "SELECT * FROM orders WHERE created_at > ?",
            connection=self.db_url,
            execute_options={"parameters": [input.start_date]},
        )
        
        # Быстрая аналитика на Polars
        result = (
            df
            .group_by("user_id")
            .agg([
                pl.count("id").alias("order_count"),
                pl.sum("total").alias("total_spent"),
                pl.mean("total").alias("avg_order"),
            ])
            .sort("total_spent", descending=True)
            .head(100)
        )
        
        return AnalyticsResult(data=result.to_dicts())
```

**Добавить в pyproject.toml:**
```toml
"polars>=1.0",
```

**Effort:** Medium  
**Priority:** 🟢 Low (когда понадобится аналитика)

---

### 5. beartype для Runtime Type Checking

**Что это:** Самая быстрая библиотека runtime type checking (O(1) сложность).

**Зачем нужно:**
- Раннее обнаружение type errors в development
- Защита на границах модулей

**Реализация:**

```python
from beartype import beartype

@beartype
class UserRepository:
    async def find_by_ids(self, ids: list[UUID]) -> list[AppUser]:
        # Если передать неправильный тип — немедленная ошибка
        ...

# Или глобально через BeartypeConf
```

**Добавить в pyproject.toml:**
```toml
"beartype>=0.18",
```

**Effort:** Low  
**Priority:** 🟡 Medium (для development)

---

### 6. Property-Based Testing с Hypothesis

**Статус:** ✅ Уже есть в dev dependencies (`hypothesis>=6.0`)

**Что нужно:** Активно использовать!

```python
# tests/property/test_user_properties.py
from hypothesis import given, strategies as st, settings
from hypothesis.strategies import composite

@composite
def user_requests(draw):
    """Strategy для генерации CreateUserRequest."""
    return CreateUserRequest(
        email=draw(st.emails()),
        password=draw(st.text(min_size=8, max_size=128)),
        name=draw(st.text(min_size=2, max_size=100)),
    )

@given(request=user_requests())
@settings(max_examples=100)
async def test_create_user_never_crashes(request: CreateUserRequest):
    """Property: создание пользователя никогда не падает с unhandled exception."""
    action = CreateUserAction(...)
    result = await action.run(request)
    
    # Result всегда Success или Failure, никогда не exception
    assert isinstance(result, (Success, Failure))


@given(email=st.emails())
def test_email_normalization_is_idempotent(email: str):
    """Property: нормализация email идемпотентна."""
    normalized_once = normalize_email(email)
    normalized_twice = normalize_email(normalized_once)
    assert normalized_once == normalized_twice
```

**Effort:** Low  
**Priority:** 🔴 High (уже есть, нужно использовать!)

---

## 🟡 Расходится с текущей реализацией

### 7. Temporal.io vs TaskIQ для Saga Pattern

**Текущее:** TaskIQ + custom Saga (docs/20-saga-pattern.md)

**Альтернатива:** Temporal.io

| Аспект | TaskIQ + Custom | Temporal.io |
|--------|-----------------|-------------|
| **Лицензия** | MIT | ✅ MIT (100% open source) |
| **Vendor lock-in** | ❌ Нет | ❌ Нет (self-hosted или cloud) |
| **Retry логика** | Ручная | Автоматическая |
| **Состояние процесса** | В Redis/DB (ручное) | Встроенное (Event Sourcing) |
| **Компенсации** | Ручной код | Декларативные |
| **Replay/Debug** | Сложно | UI + Replay |
| **Learning curve** | Низкая | Высокая (1+ месяц) |
| **Self-hosted** | ✅ | ✅ (Postgres/MySQL/Cassandra) |

**Рекомендация:**
- Для **простых Saga** — оставить TaskIQ
- Для **mission-critical** (PaymentModule, OrderModule) — рассмотреть Temporal

```bash
uv add temporalio
```

**Effort:** High  
**Priority:** 🟢 Long-term (6-12 месяцев)

---

### 8. Prefect vs TaskIQ для Data Pipelines

**Текущее:** TaskIQ для всех background tasks

**Альтернатива:** Prefect для ML/Data pipelines

| Аспект | TaskIQ | Prefect |
|--------|--------|---------|
| **Фокус** | General background tasks | Data/ML pipelines |
| **UI** | Нет | ✅ Отличный |
| **Scheduling** | Cron | Cron + Events + Triggers |
| **Python-native** | ✅ | ✅ |
| **Learning curve** | Низкая | Низкая |

**Рекомендация:** 
- TaskIQ — для обычных background tasks
- Prefect — если будут ML/Data pipelines

**Effort:** Medium  
**Priority:** 🟢 Low (если появятся ML pipelines)

---

## ❌ НЕ добавлять (решено не использовать)

### Логирование / Observability

**Решение:** Использовать **Logfire** с стандартным экспортом или возможностью замены на кастомный.

Дополнительные logging библиотеки НЕ нужны.

---

## 📊 Итоговый приоритет

### 🔴 High Priority (добавить в ближайшее время)

| Паттерн | Effort | Причина |
|---------|--------|---------|
| Hypothesis property testing | Low | Уже есть, нужно активировать |
| beartype | Low | Runtime type safety |

### 🟡 Medium Priority (3-6 месяцев)

| Паттерн | Effort | Причина |
|---------|--------|---------|
| Specification Pattern | Medium | Улучшает queries |
| AggregateRoot | Medium | DDD correctness |
| msgspec для hot paths | Low | Performance |

### 🟢 Long-term (6-12 месяцев)

| Паттерн | Effort | Причина |
|---------|--------|---------|
| Temporal.io для Saga | High | Mission-critical workflows |
| Polars для аналитики | Medium | Fast analytics |

---

## 📚 Добавить в pyproject.toml

```toml
# High Priority
"beartype>=0.18",

# Medium Priority  
"msgspec>=0.18",

# Long-term
"polars>=1.0",
# "temporalio>=1.7",  # Когда понадобится
```

---

## 🔗 Связанные документы

- [20-saga-pattern.md](20-saga-pattern.md) — Текущая Saga реализация
- [14-future-roadmap-and-patterns.md](14-future-roadmap-and-patterns.md) — Roadmap
- [GAP_ANALYSIS_ADVANCED.md](GAP_ANALYSIS_ADVANCED.md) — Event Bus, Outbox

