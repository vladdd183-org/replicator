# 📖 Hyper-Porto Architecture Documentation

> Полная документация по архитектуре Hyper-Porto v4.0

---

## 🗂️ Содержание

| # | Документ | Описание |
|---|----------|----------|
| 00 | [Philosophy](00-philosophy.md) | Философия и ключевые принципы |
| 01 | [Architecture](01-architecture.md) | Слои, компоненты, потоки данных |
| 02 | [Project Structure](02-project-structure.md) | Структура файлов и папок |
| 03 | [Components](03-components.md) | Action, Task, Repository, Controller... |
| 04 | [Result & Railway](04-result-railway.md) | Railway-oriented programming |
| 05 | [Concurrency](05-concurrency.md) | Structured Concurrency с anyio |
| 06 | [Metaprogramming](06-metaprogramming.md) | Декораторы, дженерики, сокращение бойлерплейта |
| 07 | [Spec-Driven](07-spec-driven.md) | Spec-Driven Development workflow |
| 08 | [Libraries](08-libraries.md) | Используемые библиотеки |
| 09 | [Transports](09-transports.md) | HTTP, CLI, WebSocket, GraphQL, TaskIQ |
| 10 | [Registration](10-registration.md) | Explicit Registration (Явная регистрация) |
| 11 | [Litestar Features](11-litestar-features.md) | Channels, Events, Middleware, WebSockets... |
| 12 | [Reducing Boilerplate](12-reducing-boilerplate.md) | Справочник по реализации (EntitySchema, BaseUnitOfWork, etc.) |
| 13 | [Cross-Module Communication](13-cross-module-communication.md) | Event-Driven кросс-модульное взаимодействие |
| 14 | [Future Roadmap](14-future-roadmap-and-patterns.md) | Roadmap развития и будущие паттерны |
| 15 | [Module Gateway](15-module-gateway-pattern.md) | Паттерн Gateway и Репликация данных |
| 16 | [Extract Module to Microservice](16-extract-module-to-microservice.md) | Вынос Container в микросервис (обзорный документ) |
| 17 | [Microservice Extraction Guide](17-microservice-extraction-guide.md) | **Полное практическое руководство** по выносу модуля в микросервис |
| 18 | [Unified Event Bus](18-unified-event-bus.md) | **Единая система событий** с подменяемыми бэкендами (Memory/Redis/RabbitMQ) |
| 19 | [Istio Ambient Mesh](19-istio-ambient-mesh.md) | **Service Mesh без sidecar'ов** — mTLS, traffic management, observability |
| 20 | [Saga Pattern](20-saga-pattern.md) | Распределённые транзакции с TaskIQ и Dishka |
| 21 | [Integration Patterns Guide](21-integration-patterns-guide.md) | **Когда использовать Event Bus vs Gateway vs Temporal vs TaskIQ** |
| 22 | [Temporal Saga Patterns](22-temporal-saga-patterns.md) | **Saga паттерны для Temporal.io** с Railway интеграцией |
| 23 | [Cursor AI Components](23-cursor-ai-components.md) | **Rules, Skills, Subagents, Commands** — автоматизация разработки |
| 24 | [Self-Improving Systems](24-self-improving-systems.md) | **Memory, Feedback, Standards Evolution, Knowledge Integration, Training** |

---

## 📊 Gap Analysis

| Документ | Описание |
|----------|----------|
| [GAP_ANALYSIS_ADVANCED.md](GAP_ANALYSIS_ADVANCED.md) | Event Bus, Outbox, Module Gateway, Idempotency |
| [GAP_ANALYSIS_PATTERNS.md](GAP_ANALYSIS_PATTERNS.md) | **Современные паттерны**: Specification, AggregateRoot, msgspec, Polars, Temporal vs Prefect |

---

## 🎯 Быстрый старт

### Для разработчика

1. Прочитай [00-philosophy.md](00-philosophy.md) — понять принципы
2. Изучи [02-project-structure.md](02-project-structure.md) — где что лежит
3. Посмотри [03-components.md](03-components.md) — как писать код

### Для архитектора

1. [01-architecture.md](01-architecture.md) — общий дизайн
2. [04-result-railway.md](04-result-railway.md) — обработка ошибок
3. [05-concurrency.md](05-concurrency.md) — конкурентность

### Для AI-агента

> 🎯 **Главная команда:** `/agent-os/ask [любой запрос]` — единая точка входа, автоматически роутит к нужному агенту

1. [23-cursor-ai-components.md](23-cursor-ai-components.md) — **Rules, Skills, Subagents, Commands**
2. [24-self-improving-systems.md](24-self-improving-systems.md) — **Memory, Feedback, Standards Evolution, Training, Orchestrator**
3. [07-spec-driven.md](07-spec-driven.md) — workflow разработки
4. [06-metaprogramming.md](06-metaprogramming.md) — паттерны
5. [08-libraries.md](08-libraries.md) — tech stack

### Для интеграции транспортов

1. [09-transports.md](09-transports.md) — HTTP, GraphQL, CLI, WebSocket, TaskIQ
2. [11-litestar-features.md](11-litestar-features.md) — Channels, Events, Middleware, Stores

### Для масштабирования к микросервисам

1. [18-unified-event-bus.md](18-unified-event-bus.md) — **Unified Event Bus** (Memory → Redis → RabbitMQ)
2. [17-microservice-extraction-guide.md](17-microservice-extraction-guide.md) — **Полный пошаговый гайд** по выносу модуля
3. [15-module-gateway-pattern.md](15-module-gateway-pattern.md) — Gateway Pattern для синхронных зависимостей
4. [14-future-roadmap-and-patterns.md](14-future-roadmap-and-patterns.md) — Outbox, Idempotency, SAGA
5. [19-istio-ambient-mesh.md](19-istio-ambient-mesh.md) — **Istio Ambient Mesh** — Service Mesh без sidecar'ов

---

## 🧩 Ключевые концепции

### Porto Architecture

```
Ship (инфраструктура) + Containers (бизнес-модули)
```

### Result[T, E]

```python
Result[User, UserError]  # Success или Failure
```

### Structured Concurrency

```python
async with anyio.create_task_group() as tg:
    tg.start_soon(task1)
    tg.start_soon(task2)
# Все задачи завершены
```

### Pattern Matching

```python
match result:
    case Success(user):
        return Ok(user)
    case Failure(NotFoundError()):
        return NotFound()
```

---

## 📦 Tech Stack

| Категория | Библиотека |
|-----------|------------|
| Web | Litestar |
| GraphQL | Strawberry |
| CLI | Litestar CLIPlugin |
| Background | TaskIQ |
| Functional | returns |
| Async | anyio |
| DI | Dishka |
| ORM | Piccolo |
| Validation | Pydantic |
| Observability | Logfire |

---

## 🔗 Ссылки

- [Porto SAP](https://github.com/Mahmoudz/Porto) — оригинальная спецификация
- [Cosmic Python](https://cosmicpython.com) — паттерны архитектуры
- [Returns](https://returns.readthedocs.io) — функциональные контейнеры
- [anyio](https://anyio.readthedocs.io) — structured concurrency
- [Spec Kit](https://github.com/github/spec-kit) — spec-driven development
- [Litestar](https://litestar.dev) — web framework

---

<div align="center">

**Hyper-Porto v4.0**

*Функциональная архитектура для Python бэкендов*

🚢 Porto + 🐍 Cosmic + 🦀 Returns + ⚡ anyio = 🚀 Production-Ready

</div>
