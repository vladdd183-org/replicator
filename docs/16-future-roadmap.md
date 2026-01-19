# 🚀 Hyper-Porto Future Roadmap

> Версия: 4.2.0 | Дата: Январь 2026

---

## ✅ Реализовано (v4.2.0)

### Инфраструктура
- [x] **Unified Event Bus** — Protocol + InMemory/Redis/RabbitMQ backends
- [x] **Transactional Outbox** — Гарантированная доставка событий
- [x] **Idempotency Middleware** — X-Idempotency-Key защита от дубликатов
- [x] **Module Gateway Pattern** — Direct/HTTP адаптеры для межмодульных вызовов
- [x] **Temporal Saga** — Durable execution с компенсациями
- [x] **Porto CLI Generator** — `porto make:module`, `make:action`, etc.

### Качество кода
- [x] **Result[T, E]** — Railway-oriented programming
- [x] **Structured Concurrency** — anyio TaskGroups
- [x] **CQRS** — Action/Query разделение

---

## 🔄 В разработке

### Краткосрочно (Q1 2026)
- [ ] **Snapshot Testing** — Тестирование API responses
- [ ] **Contract Testing** — Consumer-driven contracts

### Среднесрочно (Q2 2026)
- [ ] **Specification Pattern** — Композируемые фильтры для сложных queries
- [ ] **Event Sourcing** — Опциональный паттерн для audit-критичных модулей

---

## 🔮 Долгосрочно

### Архитектурные улучшения
- [ ] **AggregateRoot Pattern** — Domain invariants
- [ ] **CQRS с отдельными моделями** — Read/Write разделение на уровне БД

### Производительность
- [ ] **msgspec** — Быстрая сериализация для hot paths
- [ ] **Polars** — Аналитические queries

### Инфраструктура
- [ ] **Istio Ambient Mesh** — Service mesh для микросервисов
- [ ] **Distributed Tracing** — OpenTelemetry интеграция

---

## 📚 Связанные документы

- [13-module-gateway-pattern.md](13-module-gateway-pattern.md) — Gateway Pattern
- [14-microservice-extraction-guide.md](14-microservice-extraction-guide.md) — Вынос в микросервис
- [15-saga-patterns.md](15-saga-patterns.md) — Saga с Temporal
- [17-unified-event-bus.md](17-unified-event-bus.md) — Event Bus

---

**Hyper-Porto v4.2.0** 🚀
