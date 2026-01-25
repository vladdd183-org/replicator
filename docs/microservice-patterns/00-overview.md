# Паттерны микросервисной архитектуры

> **Серия заметок** | Январь 2026  
> Полное руководство по паттернам для распределённых систем

---

## Что это за серия?

Эта серия заметок объясняет **34 ключевых паттерна** микросервисной архитектуры:
- Техническим языком — для разработчиков
- Простым языком с аналогиями — для понимания сути

Каждый паттерн содержит:
- Проблему, которую он решает
- Суть решения
- Аналогию из реального мира
- Когда использовать / когда не использовать
- Примеры кода (где применимо)

---

## Навигация по заметкам

### [01. Cross-cutting Concerns](./01-cross-cutting-concerns.md)
Паттерны, пронизывающие всю систему насквозь.
- Externalized Configuration
- Microservice Chassis
- Service Template

### [02. Decomposition (Декомпозиция)](./02-decomposition-patterns.md)
Как разбить монолит на сервисы.
- Decompose by Business Capability
- Decompose by Subdomain
- Database per Service
- Shared Database

### [03. Data Patterns (Работа с данными)](./03-data-patterns.md)
Управление данными в распределённой системе.
- CQRS
- Event Sourcing
- Transactional Outbox
- Saga Pattern

### [04. Communication (Коммуникация)](./04-communication-patterns.md)
Как сервисы общаются друг с другом.
- Messaging
- Remote Procedure Invocation (RPI)
- Event-driven Architecture
- API Composition

### [05. API Patterns](./05-api-patterns.md)
Организация внешнего API системы.
- API Gateway
- Backend for Frontend (BFF)
- GraphQL Gateway

### [06. Service Discovery (Обнаружение)](./06-discovery-patterns.md)
Как сервисы находят друг друга.
- Client-side Discovery
- Server-side Discovery
- Service Registry

### [07. Observability (Наблюдаемость)](./07-observability-patterns.md)
Мониторинг и отладка распределённой системы.
- Distributed Tracing
- Log Aggregation
- Application Metrics
- Health Check API
- Audit Logging
- Exception Tracking

### [08. Resilience (Отказоустойчивость)](./08-resilience-patterns.md)
Как система переживает сбои.
- Circuit Breaker
- Retry with Backoff
- Bulkhead
- Timeout
- Idempotency

### [09. Security (Безопасность)](./09-security-patterns.md)
Защита распределённой системы.
- Access Token (JWT)
- API Key Authentication
- Service-to-Service Auth (mTLS)

### [10. Deployment (Развёртывание)](./10-deployment-patterns.md)
Как деплоить микросервисы.
- Single Service per Host
- Multiple Services per Host
- Serverless Deployment
- Service Mesh (Sidecar)

### [11. Testing (Тестирование)](./11-testing-patterns.md)
Тестирование в микросервисной архитектуре.
- Service Component Test
- Service Integration Contract Test
- End-to-End Test

### [12. UI Patterns](./12-ui-patterns.md)
Паттерны для фронтенда микросервисов.
- Server-side Page Fragment Composition
- Client-side UI Composition
- Micro Frontends

---

## Матрица: Какие паттерны для чего

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ЭТАПЫ ЭВОЛЮЦИИ СИСТЕМЫ                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  МОНОЛИТ              МОДУЛЬНЫЙ МОНОЛИТ         МИКРОСЕРВИСЫ               │
│  ───────              ─────────────────         ─────────────               │
│                                                                             │
│  ┌─────────┐          ┌─────────────────┐       ┌───┐ ┌───┐ ┌───┐         │
│  │         │          │ ┌───┐ ┌───┐     │       │ A │ │ B │ │ C │         │
│  │   ALL   │    →     │ │ A │ │ B │     │   →   └─┬─┘ └─┬─┘ └─┬─┘         │
│  │         │          │ └───┘ └───┘     │         │     │     │            │
│  └─────────┘          │     ┌───┐       │         └─────┼─────┘            │
│                       │     │ C │       │               │                  │
│                       │     └───┘       │         Message Broker           │
│                       └─────────────────┘                                  │
│                                                                             │
│  Паттерны:            Паттерны:                 Паттерны:                   │
│  • Ext. Config        • Ext. Config             • ВСЕ предыдущие           │
│                       • Decomposition           • API Gateway              │
│                       • CQRS                    • Service Discovery        │
│                       • Event-driven            • Circuit Breaker          │
│                       • Module Gateway          • Distributed Tracing      │
│                       • Health Checks           • Contract Tests           │
│                                                 • Saga                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Как читать эти заметки

### Для новичков
1. Начните с [01. Cross-cutting Concerns](./01-cross-cutting-concerns.md)
2. Затем [02. Decomposition](./02-decomposition-patterns.md)
3. Потом [03. Data Patterns](./03-data-patterns.md)

### Для опытных
- Используйте как справочник
- Переходите сразу к нужному паттерну

### Условные обозначения

| Иконка | Значение |
|--------|----------|
| 💡 | Ключевая идея |
| ⚠️ | Важное предупреждение |
| 📝 | Техническое объяснение |
| 🏠 | Аналогия из жизни |
| ✅ | Когда использовать |
| ❌ | Когда НЕ использовать |
| 🔧 | Пример реализации |

---

## Связь с Hyper-Porto

Эта серия заметок создана в контексте **Hyper-Porto** архитектуры.

### Cross-cutting Concerns

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Externalized Configuration | ✅ Реализован | Pydantic Settings, .env |
| Microservice Chassis | ✅ Реализован | Ship Layer |
| Service Template | ✅ Реализован | Porto CLI Generator |

### Decomposition

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Decompose by Business Capability | ✅ Реализован | Containers структура |
| Decompose by Subdomain | ✅ Реализован | AppSection/VendorSection |
| Database per Service | ⚠️ Подготовлено | Сейчас shared DB, готово к разделению |
| Shared Database | ✅ Текущий режим | Piccolo ORM + ownership rules |

### Data Patterns

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| CQRS | ✅ Реализован | Actions (write) + Queries (read) |
| Event Sourcing | ❌ Не реализован | Можно добавить при необходимости |
| Transactional Outbox | ✅ Реализован | OutboxEvent + OutboxPublisher |
| Saga (Orchestration) | ✅ Реализован | Temporal.io workflows |
| Saga (Simple) | ✅ Реализован | TaskIQ tasks |

### Communication

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| REST API (RPI) | ✅ Реализован | Litestar Controllers |
| gRPC | ❌ Не реализован | Можно добавить |
| Messaging | ✅ Реализован | Unified Event Bus |
| Event-driven | ✅ Реализован | UoW + litestar.events |
| API Composition | ⚠️ Подготовлено | Через BFF/Gateway |

### API Patterns

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| API Gateway | ⚠️ Подготовлено | Module Gateway Pattern |
| Backend for Frontend (BFF) | ⚠️ Архитектура готова | Можно создать отдельный сервис |
| GraphQL Gateway | ✅ Реализован | Strawberry + Federation ready |

### Service Discovery

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Client-side Discovery | ❌ Для микросервисов | При выносе — Consul/etcd |
| Server-side Discovery | ⚠️ Подготовлено | Kubernetes Service DNS |
| Service Registry | ⚠️ Подготовлено | При выносе — Consul |

### Observability

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Distributed Tracing | ✅ Реализован | Logfire + OpenTelemetry |
| Log Aggregation | ✅ Реализован | Logfire structured logging |
| Application Metrics | ⚠️ Подготовлено | Logfire metrics, можно Prometheus |
| Health Check API | ✅ Реализован | /health, /health/ready |
| Audit Logging | ✅ Реализован | @audited decorator |
| Exception Tracking | ⚠️ Подготовлено | Logfire, можно Sentry |

### Resilience

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Circuit Breaker | ❌ Нужно добавить | Рекомендуется circuitbreaker lib |
| Retry with Backoff | ✅ Реализован | tenacity |
| Bulkhead | ⚠️ Можно добавить | asyncio.Semaphore |
| Timeout | ✅ Реализован | httpx timeout, anyio.fail_after |
| Idempotency | ✅ Реализован | IdempotencyMiddleware |

### Security

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Access Token (JWT) | ✅ Реализован | JWTService, Guards |
| API Key Authentication | ⚠️ Легко добавить | Middleware готов |
| mTLS | ❌ Для микросервисов | При выносе — Istio |
| Secrets Management | ⚠️ Частично | Env vars, можно Vault |

### Deployment

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Single Service per Host | ✅ Реализован | Docker, Kubernetes |
| Multiple Services per Host | ❌ Не рекомендуется | — |
| Serverless | ⚠️ Можно адаптировать | Litestar + AWS Lambda |
| Service Mesh | ⚠️ Документировано | Istio Ambient Mesh guide |

### Testing

| Паттерн | Статус | Реализация |
|---------|--------|------------|
| Service Component Test | ✅ Реализован | pytest + testcontainers |
| Service Integration Contract Test | ⚠️ Можно добавить | Pact |
| End-to-End Test | ⚠️ Подготовлено | pytest + httpx |

### UI Patterns

| Паттерн | Статус | Примечание |
|---------|--------|------------|
| Micro Frontends | ➖ N/A | Backend framework |
| Client-side Composition | ➖ N/A | Backend framework |
| Server-side Composition | ➖ N/A | Backend framework |

### Легенда

| Статус | Значение |
|--------|----------|
| ✅ Реализован | Полностью работает в проекте |
| ⚠️ Подготовлено | Архитектура готова, требуется минимум работы |
| ❌ Не реализован | Нужно добавить при необходимости |
| ➖ N/A | Не применимо к backend framework |

---

## Источники

- [microservices.io](https://microservices.io/patterns/) — Chris Richardson
- [Designing Data-Intensive Applications](https://dataintensive.net/) — Martin Kleppmann
- [Building Microservices](https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/) — Sam Newman
- [Release It!](https://pragprog.com/titles/mnee2/release-it-second-edition/) — Michael Nygard

---

<div align="center">

**Следующая заметка:** [01. Cross-cutting Concerns →](./01-cross-cutting-concerns.md)

</div>
