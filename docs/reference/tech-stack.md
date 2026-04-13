# Технологический стек Replicator

> Полный перечень технологий с обоснованием выбора.

---

## Ядро (обязательное)

| Категория | Технология | Версия | Обоснование |
|---|---|---|---|
| Язык | Python | >=3.13 | Экосистема AI/ML, типизация, async |
| Web framework | Litestar | latest | ASGI, каналы, middleware, CLI plugin, OpenAPI |
| DI | Dishka | latest | Scoped providers, auto-resolution, type-safe |
| Функциональность | Returns | latest | Result[T, E], Maybe, Railway-oriented programming |
| Async | anyio | latest | Structured concurrency, backend-agnostic |
| Валидация | Pydantic | v2 | Модели, сериализация, settings |
| ORM | Piccolo | latest | Async, PostgreSQL/SQLite, миграции |
| Телеметрия | Logfire | latest | Observability, tracing, auto-instrumentation |
| Package manager | uv | latest | Быстрый, lockfile, workspace support |

## Агенты и AI

| Категория | Технология | Обоснование |
|---|---|---|
| Prompt framework | DSPy | Сигнатуры вместо промптов, автооптимизация MIPROv2 |
| Tool integration | MCP (Model Context Protocol) | Стандартный протокол, framework-agnostic |
| Agent memory | Mem0 (или аналог) | Прагматичный memory layer |
| Knowledge graph | Graphiti (или аналог) | Temporal durable knowledge layer |
| Orchestration | Temporal (будущее) | Durable outer loop для длинных workflows |

## Сборка и деплой

| Категория | Технология | Обоснование |
|---|---|---|
| Build system | Nix (flakes) | Reproducible builds, декларативность |
| OCI images | nix2container | Инкрементальные push, минимальные слои |
| Task runner | just | Простой, кроссплатформенный, Makefile-альтернатива |
| CI/CD | GitHub Actions | Self-hosted NixOS runners в vladdd183-org |
| Linting | ruff | Быстрый, всё-в-одном |
| Formatting | ruff format + nixfmt | Python + Nix |
| Type checking | pyright | Строгий, хорошая интеграция |

## Messaging и State (Web2)

| Категория | Технология | Когда |
|---|---|---|
| Events (монолит) | litestar.events | По умолчанию |
| Events (distributed) | NATS JetStream | При выносе в микросервисы |
| Cache | Redis / Cashews | Кеширование, rate limiting |
| Queue | TaskIQ | Фоновые задачи |
| Database | PostgreSQL | Продакшен |
| Database (dev) | SQLite | Локальная разработка |

## Messaging и State (Web3, будущее)

| Категория | Технология | Когда |
|---|---|---|
| Storage | IPFS | Content-addressed хранилище |
| Mutable state | Ceramic (ComposeDB) | Мутабельные потоки с историей |
| Messaging | libp2p (Lattica-подобный) | P2P real-time |
| Identity | DID + UCAN | Самосуверенная авторизация |
| Compute | IPVM (Homestar) | WASM execution на IPFS данных |

---

## Рекомендуемый стек для Autonomous Dev Mesh

Из исследования 10-autonomous-dev-mesh/12-comparison-matrix:

| Слой | Рекомендация |
|---|---|
| Interaction mode | vibe coding как intake, не как truth |
| Repo context | AGENTS.md (минимальный) |
| Standards memory | Agent OS-подобный слой |
| Spec layer | OpenSpec |
| Task truth | Beads |
| Tool plane | MCP |
| Runtime/orchestration | Temporal + pragmatic agent runner |
| Agent framework | LangGraph или thin custom orchestrator |
| Agent memory | Mem0 |
| Durable knowledge | Graphiti |
| Verification | tests + evals + traces + evidence bundles |
| Integration rail | merge queue + Refinery-lite + preview env |
