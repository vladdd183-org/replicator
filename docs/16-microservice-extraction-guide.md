# 🚀 Практическое руководство: Вынос Container в микросервис

> **Версия:** 4.3  
> **Дата:** Январь 2026  
> **Назначение:** Полное пошаговое руководство по выделению модуля (Container) из Hyper-Porto монолита в самостоятельный микросервис — максимально безопасно и с минимальным переписыванием бизнес-логики

---

## 📋 Содержание

1. [Философия и ключевые принципы](#1-философия-и-ключевые-принципы)
2. [Оценка готовности модуля](#2-оценка-готовности-модуля)
3. [Три уровня архитектурной зрелости](#3-три-уровня-архитектурной-зрелости)
4. [Подготовка модуля к выносу](#4-подготовка-модуля-к-выносу)
5. [Матрица контрактов](#5-матрица-контрактов)
6. [Общий Ship в мире микросервисов](#6-общий-ship-в-мире-микросервисов)
7. [Коммуникация между сервисами](#7-коммуникация-между-сервисами)
8. [Структура нового микросервиса](#8-структура-нового-микросервиса)
9. [Пошаговый процесс выноса (Strangler Fig)](#9-пошаговый-процесс-выноса-strangler-fig)
10. [Событийная система: от litestar.events к брокеру](#10-событийная-система-от-litestarevents-к-брокеру)
11. [Конфигурация и инфраструктура](#11-конфигурация-и-инфраструктура)
12. [Миграция данных](#12-миграция-данных)
13. [Module Gateway: синхронные зависимости](#13-module-gateway-синхронные-зависимости)
14. [Транспорты при выносе](#14-транспорты-при-выносе)
15. [Практический пример: SearchModule → SearchService](#15-практический-пример-searchmodule--searchservice)
16. [Типичные ошибки и как их избежать](#16-типичные-ошибки-и-как-их-избежать)
17. [Чеклисты](#17-чеклисты)
18. [Шаблоны файлов](#18-шаблоны-файлов)
19. [Troubleshooting](#19-troubleshooting)

---

## 1. Философия и ключевые принципы

### 1.1 Почему вынос в Hyper-Porto — это просто

В Hyper-Porto **Container уже является границей будущего сервиса**. Архитектура изначально спроектирована так, что вынос модуля — это механическая операция, а не рефакторинг бизнес-логики:

| Аспект | Как реализовано | Что это даёт при выносе |
|--------|-----------------|-------------------------|
| **Явная сборка** | `src/App.py` вручную подключает роутеры/listeners | Просто убрать из списка |
| **Явная DI-регистрация** | `AppProvider.py` перечисляет провайдеры | Просто убрать импорт |
| **Модульные миграции** | `PiccoloApp.py` в каждом модуле | Просто перенести |
| **События через UoW** | `uow.add_event()` + `litestar.events` | Заменить на брокер |
| **Изоляция данных** | Каждый модуль владеет своими таблицами | Просто вынести БД |

### 1.2 Ключевой принцип

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Вынос модуля = Перенос папки + Создание точки входа + Замена транспорта   │
│                                                                             │
│  Бизнес-логика (Actions, Tasks, Repositories) остаётся БЕЗ ИЗМЕНЕНИЙ       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Что такое "вынести модуль в микросервис"

В этом репозитории **Container** — папка вида:

```
src/Containers/{Section}/{ModuleName}/
```

Под "микросервисом" понимаем:

- **Отдельный процесс/деплой** (свой `uvicorn`, свой Docker образ)
- **Свой контекст конфигурации** (`Settings`, env vars)
- **Своя БД и ownership данных** (идеально: отдельная БД; минимум: отдельная схема с жёстким владением)
- **Коммуникация с другими сервисами** через:
  - асинхронные события (предпочтительно)
  - синхронные вызовы через Gateway/HTTP
  - репликацию данных по событиям
  - RPC через очередь (как компромисс)

> **Важное уточнение:** "микросервис" — не обязательно маленький. Важно, что он **самостоятельно разворачивается** и **сам владеет своими данными**.

---

## 2. Оценка готовности модуля

### 2.1 Матрица готовности

Оцените модуль по следующим критериям (0-3 балла за каждый):

| Критерий | 0 | 1 | 2 | 3 |
|----------|---|---|---|---|
| **Изоляция кода** | Много импортов из других Containers | Есть импорты, но можно заменить | Минимум импортов, через Events | Полная изоляция |
| **Изоляция данных** | Читает/пишет чужие таблицы | Только читает чужие | Только через Events/API | Полная изоляция |
| **Событийный контракт** | События не определены | Частично определены | Определены, но не версионированы | Полный контракт + версии |
| **Идемпотентность** | Нет | Частичная | Для критичных операций | Полная |

**Интерпретация:**
- **10-12**: Готов к выносу немедленно
- **7-9**: Требуется небольшая подготовка
- **4-6**: Требуется серьёзная подготовка
- **0-3**: Не готов, нужен рефакторинг

### 2.2 Хорошие кандидаты для выноса

Из текущего проекта:

| Модуль | Оценка | Причина |
|--------|--------|---------|
| **SearchModule** | ⭐⭐⭐ | Только слушает события, своя таблица, независим |
| **WebhookModule** | ⭐⭐⭐ | Fire-and-forget, внешние доставки |
| **AuditModule** | ⭐⭐ | Слушает события, но зависит от Ship декоратора |
| **NotificationModule** | ⭐⭐ | Может потребовать Gateway для чтения |
| **UserModule** | ⭐ | Центральный, много зависимостей от него |

### 2.3 Когда выносить — критерии принятия решения

**Выносить стоит когда:**

- 📈 **Масштабирование**: модуль требует отдельного scaling (CPU/RAM)
- 🔒 **Безопасность**: модуль обрабатывает чувствительные данные
- 🚀 **Деплой**: модуль меняется независимо и чаще других
- 👥 **Команды**: отдельная команда владеет модулем
- 💰 **Стоимость**: модуль потребляет дорогие ресурсы (GPU, внешние API)

**НЕ выносить если:**

- ❌ Модуль тесно связан с другими через прямые импорты
- ❌ Нет чёткого владения данными
- ❌ Команда не готова поддерживать отдельный сервис
- ❌ Преждевременная оптимизация без реальной необходимости

---

## 3. Три уровня архитектурной зрелости

### Уровень 1: Модульный монолит (текущее состояние)

```
┌─────────────────────────────────────────────────────────────┐
│                    Единый процесс                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  App.py                                              │    │
│  │  ├── UserModule (роутер + listeners)                │    │
│  │  ├── SearchModule (роутер + listeners)              │    │
│  │  └── WebhookModule (роутер + listeners)             │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                   │
│                    litestar.events                           │
│                      (in-process)                            │
└─────────────────────────────────────────────────────────────┘
```

**Характеристики:**
- Все Containers живут в одном процессе
- События распространяются через `litestar.events` (in-process)
- Общая БД (с модульным владением таблицами)

### Уровень 2: Distributed Monolith (промежуточный шаг)

```
┌─────────────────────────────────────────────────────────────┐
│                    Один репозиторий                          │
│                                                              │
│  ┌────────────────────┐     ┌────────────────────┐          │
│  │  Process 1         │     │  Process 2         │          │
│  │  App.py (Main)     │     │  SearchApp.py      │          │
│  │  ├── UserModule    │     │  └── SearchModule  │          │
│  │  └── WebhookModule │     │                    │          │
│  └─────────┬──────────┘     └────────┬───────────┘          │
│            │                         │                       │
│            └───────── Redis ─────────┘                       │
│                   (Pub/Sub или Streams)                      │
└─────────────────────────────────────────────────────────────┘
```

**Характеристики:**
- Несколько приложений/процессов в одном репозитории
- Redis используется как:
  - брокер для TaskIQ (уже есть)
  - backend для Channels (WebSocket multi-instance)
  - транспорт для событий (временно без Outbox)

**Почему этот уровень полезен:**
- Снижает риск "big bang" миграции
- Позволяет протестировать разделение без полного выноса
- Упрощает debugging (общий код)

### Уровень 3: Микросервисы (целевое состояние)

```
┌────────────────────┐     ┌────────────────────┐
│  user-service      │     │  search-service    │
│  Repo: user-svc    │     │  Repo: search-svc  │
│  DB: PostgreSQL    │     │  DB: PostgreSQL    │
└─────────┬──────────┘     └────────┬───────────┘
          │                         │
          └───── Kafka/RabbitMQ ────┘
                   + Outbox
```

**Характеристики:**
- Каждый Container — отдельный репозиторий и сервис
- События через внешний брокер + Transactional Outbox
- Синхронные запросы через HTTP/gRPC Gateway

---

## 4. Подготовка модуля к выносу

### 4.1 Границы кода: устранение прямых импортов

**Проверка:**

```bash
# Найти прямые импорты между контейнерами
grep -r "from src.Containers.AppSection" src/Containers/AppSection/SearchModule/ | \
  grep -v "SearchModule"
```

**Если найдены — заменить на:**

```python
# ❌ БЫЛО: прямой импорт
from src.Containers.AppSection.UserModule.Actions.GetUserAction import GetUserAction

# ✅ СТАЛО: через Events (если ответ не нужен)
# Action публикует событие, другой модуль подписан

# ✅ СТАЛО: через Gateway (если нужен синхронный ответ)
from src.Containers.AppSection.SearchModule.Gateways.UserGateway import UserGateway

# ✅ СТАЛО: через Replication (если нужен быстрый read-доступ)
# Храним копию данных, обновляем по событиям
```

### 4.2 Границы данных: владение таблицами

**Правило:** только модуль-владелец пишет в свои таблицы.

Если другому модулю нужны данные:
- **Для read** — репликация (event-carried state transfer) или API вызов
- **Для write** — команда/запрос в сервис-владелец (HTTP/Gateway/RPC)

### 4.3 Определение событийного контракта

Создайте файл `EventContracts.md` в модуле:

```markdown
# SearchModule Event Contracts

## Потребляемые события (Subscribed)

| Событие | Producer | Версия | Обязательные поля | Опциональные |
|---------|----------|--------|-------------------|--------------|
| UserCreated | UserModule | v1 | user_id, email, name | occurred_at |
| UserUpdated | UserModule | v1 | user_id | email, name |
| UserDeleted | UserModule | v1 | user_id | - |
| PaymentCreated | PaymentModule | v1 | payment_id, amount | currency |

## Публикуемые события (Published)

| Событие | Версия | Поля | Consumers |
|---------|--------|------|-----------|
| EntityIndexed | v1 | entity_type, entity_id | AuditModule |

## Гарантии доставки

- **Consumer idempotency**: Обязательно (по entity_type + entity_id)
- **Ordering**: Не требуется
- **At-least-once**: Допускаем дубли
```

### 4.4 Добавление версионирования событий

```python
# src/Containers/AppSection/SearchModule/Events.py

from src.Ship.Parents.Event import DomainEvent

class EntityIndexed(DomainEvent):
    """Событие успешной индексации сущности."""
    
    event_version: str = "v1"  # <-- Версия обязательна
    
    entity_type: str
    entity_id: str
    indexed_at: str  # ISO datetime
```

### 4.5 Идемпотентность и надёжность доставки

Как только модуль становится сервисом, коммуникация становится **ненадёжной по умолчанию**:

- сообщения могут дублироваться
- могут приходить не по порядку
- могут потеряться (если нет Outbox)
- сервис может временно быть недоступен

**Перед выносом включайте:**

- **Idempotency Keys** на критичных командах
- **Transactional Outbox** для публикации событий
- **Retry + backoff** (через `tenacity`)

---

## 5. Матрица контрактов

Договорённости при микросервисах ломаются чаще всего не в бизнес-логике, а в "межсервисных" контрактах.

### 5.1 Шаблон матрицы

| Producer (Service/Module) | Тип контракта | Имя | Версия | Схема/поля | Consumers | Гарантии/заметки |
|---------------------------|---------------|-----|--------|------------|-----------|------------------|
| `UserService` | Event | `UserCreated` | `v1` | `user_id, email, name, occurred_at` | `SearchService`, `WebhookService` | at-least-once, consumer idempotency |
| `UserService` | Event | `UserUpdated` | `v1` | `user_id, email?, name?` | `SearchService` | at-least-once |
| `SearchService` | HTTP | `GET /api/v1/search` | `v1` | query params + response schema | `API Gateway` | SLA 200ms, ретраи на 5xx |
| `PaymentService` | Event | `PaymentCompleted` | `v1` | `payment_id, amount, currency` | `NotificationService`, `AuditService` | exactly-once через Outbox |

### 5.2 Рекомендации

- **Версии фиксируйте явно** (`v1`, `v2`), даже если пока одна
- **Для событий фиксируйте:** какие поля обязательны, какие optional
- **Для каждого consumer:** идемпотентность, порядок, обработка дублей
- **HTTP контракт:** уже генерируется Litestar (OpenAPI)

### 5.3 Контракт события (envelope)

Чтобы события пережили разделение на сервисы, договоритесь о формате:

```python
{
    "event_name": "UserCreated",        # Имя события
    "event_version": "v1",              # Версия схемы
    "event_id": "uuid-...",             # Уникальный ID (для идемпотентности)
    "occurred_at": "2026-01-19T...",    # ISO datetime
    "producer": "user-service",         # Имя сервиса-продьюсера
    "correlation_id": "req-uuid-...",   # Для трассировки
    "payload": {                        # Данные события
        "user_id": "...",
        "email": "...",
        "name": "..."
    }
}
```

---

## 6. Общий Ship в мире микросервисов

В Hyper-Porto `Ship/` — это инфраструктура (Parents/Core/Decorators/Providers/Auth/Infra). При разделении на сервисы возникает вопрос: как переиспользовать Ship?

### Вариант A: Копировать Ship в каждый сервис

```
✅ Плюсы: минимальный порог входа, быстрый старт
❌ Минусы: расхождение версий, сложные массовые апдейты

📌 Подходит для: прототипа или первых 1-2 сервисов
```

### Вариант B: Вынести Ship в общий Python-пакет (рекомендуется)

```bash
# Отдельный репозиторий
hyper-porto-ship/
├── hyper_porto_ship/
│   ├── parents/
│   ├── core/
│   ├── decorators/
│   └── infrastructure/
├── pyproject.toml
└── README.md
```

```toml
# pyproject.toml сервиса
[project]
dependencies = [
    "hyper-porto-ship>=0.1.0",  # Общий пакет
]
```

**Рекомендации:**
- В общий пакет выносить инфраструктуру, но не "бизнес-домен"
- Контракты событий/HTTP можно выносить отдельно ("contracts" пакет)

### Вариант C: Монорепозиторий с несколькими сервисами

```
new_porto/
├── services/
│   ├── user-service/
│   │   ├── src/
│   │   └── Dockerfile
│   ├── search-service/
│   │   ├── src/
│   │   └── Dockerfile
│   └── shared/
│       └── Ship/
├── docker-compose.yml
└── pyproject.toml
```

```
✅ Плюсы: код общий, деплой раздельный
❌ Минусы: релизы и команды сильнее связаны

📌 Подходит для: distributed monolith
```

---

## 7. Коммуникация между сервисами

### 7.1 Сравнение подходов

| Подход | Когда использовать | Плюсы | Минусы |
|--------|-------------------|-------|--------|
| **Events** | Уведомления, eventual consistency | Loose coupling, масштабируемость | Нет мгновенного ответа |
| **Gateway (HTTP)** | Нужен синхронный ответ | Простота, привычность | Coupling, latency |
| **Replication** | Частый read, сервис может быть offline | Быстрый доступ, resilience | Eventual consistency |
| **RPC (TaskIQ)** | Синхронно, но через очередь | Разгрузка сервиса | Сложнее трассировка |

### 7.2 Events (асинхронно, fire-and-forget)

**Используйте когда:**
- Модулю-потребителю не нужен синхронный ответ
- Допустима eventual consistency
- Действие похоже на "уведомить", "проиндексировать", "отправить webhook"

**В этом репозитории это уже основной стиль:**
- `UserModule` публикует `UserCreated/UserUpdated/UserDeleted`
- `SearchModule` слушает события и индексирует
- `WebhookModule` слушает события и делает доставки
- `AuditModule` слушает `ActionExecuted` через `@audited`

### 7.3 Module Gateway (синхронно, нужен ответ)

**Используйте когда:**
- Нужно "спросить соседа" и получить ответ прямо сейчас
- Невозможно/неудобно реплицировать данные
- Операция критична для UX (проверка лимита/баланса)

**Паттерн:** модуль-потребитель определяет порт (Protocol) и DTO, а DI решает реализацию:
- **В монолите** → прямой адаптер
- **В микросервисе** → HTTP-адаптер

### 7.4 Data Replication (event-carried state transfer)

**Используйте когда:**
- Потребителю нужны данные часто и быстро
- Сервис-владелец может быть недоступен, но потребитель должен работать
- Допустима eventual consistency

```python
# SearchService хранит копию нужных данных
class UserReplica(Table):
    user_id = UUID(primary_key=True)
    email = Varchar()
    name = Varchar()

# Обновляется по событиям UserCreated/UserUpdated
```

### 7.5 RPC через очередь (TaskIQ как транспорт)

**Компромисс:** "синхронно, но через очередь"

```
✅ Плюсы: проще, чем HTTP-клиент с ретраями, разгрузка сервиса
❌ Минусы: хуже трассировка, сложнее broadcast
```

---

## 8. Структура нового микросервиса

### 8.1 Рекомендуемая структура репозитория

```
hyper-porto-search/                  # Новый репозиторий
├── docs/
│   ├── README.md
│   └── event-contracts.md           # Контракты событий
│
├── src/
│   ├── __init__.py
│   ├── App.py                       # Litestar App (только этот модуль)
│   ├── Main.py                      # uvicorn entry point
│   │
│   ├── Ship/                        # Копия или зависимость
│   │   ├── Parents/
│   │   │   ├── Action.py
│   │   │   ├── Task.py
│   │   │   ├── Query.py
│   │   │   ├── Repository.py
│   │   │   ├── Event.py
│   │   │   └── UnitOfWork.py
│   │   ├── Core/
│   │   │   ├── BaseSchema.py
│   │   │   └── Errors.py
│   │   ├── Configs/
│   │   │   └── Settings.py          # Своя конфигурация
│   │   ├── Decorators/
│   │   │   └── result_handler.py
│   │   └── Infrastructure/
│   │       ├── HealthCheck.py
│   │       └── EventConsumer/       # НОВОЕ: консьюмер событий
│   │           ├── __init__.py
│   │           └── BrokerConsumer.py
│   │
│   └── Containers/
│       └── AppSection/
│           └── SearchModule/        # Переносим модуль целиком
│               ├── __init__.py
│               ├── Actions/
│               ├── Tasks/
│               ├── Queries/
│               ├── Data/
│               ├── Models/
│               │   ├── PiccoloApp.py
│               │   └── migrations/
│               ├── UI/
│               │   └── API/
│               ├── Events.py
│               ├── Errors.py
│               ├── Providers.py
│               ├── Listeners.py     # Переделать на Consumers.py
│               └── Consumers.py     # НОВОЕ: для брокера
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/                    # Consumer-driven contract tests
│
├── piccolo_conf.py                  # Только SearchModule PiccoloApp
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
└── env.example
```

### 8.2 Что переносится без изменений

| Компонент | Изменения |
|-----------|-----------|
| `Actions/` | ✅ Без изменений |
| `Tasks/` | ✅ Без изменений |
| `Queries/` | ✅ Без изменений |
| `Data/` | ✅ Без изменений |
| `Models/` | ✅ Без изменений (+ новый piccolo_conf.py) |
| `UI/API/` | ✅ Без изменений |
| `Events.py` | 🔄 Добавить версии |
| `Listeners.py` | 🔄 Переделать в Consumers.py |
| `Providers.py` | 🔄 Адаптировать под микросервис |

---

## 9. Пошаговый процесс выноса (Strangler Fig)

### Шаг 0: Выбор кандидата

**Хорошие кандидаты:**
- `SearchModule`: консьюмит события, имеет свою таблицу индекса
- `WebhookModule`: консьюмит события, делает внешние доставки
- `AuditModule`: консьюмит события `ActionExecuted`

**Сложные кандидаты:**
- `UserModule`: связан с auth/websocket/профилем, потребует решения "где живёт аутентификация"

### Шаг 1: Зафиксировать контракты (до выноса)

- [ ] Список HTTP endpoints
- [ ] Список Domain Events, которые сервис публикует/слушает
- [ ] Матрица потребителей (кто слушает что)
- [ ] Версионирование (`event_version`, `api/v1`)

### Шаг 2: Убрать скрытые зависимости

- [ ] Прямые импорты между контейнерами → Events или Gateway
- [ ] Чтения чужих таблиц → репликация/HTTP

### Шаг 3: Вынести модуль в отдельное приложение (в том же репо)

Создаём новый `App.py` только для этого модуля:

```python
# src/SearchApp.py (временно в том же репо)
"""Isolated SearchModule application for testing extraction."""

from litestar import Litestar
from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka, LitestarProvider

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.HealthCheck import health_controller
from src.Containers.AppSection.SearchModule import search_router
from src.Containers.AppSection.SearchModule.Providers import (
    SearchModuleProvider,
    SearchRequestProvider,
)
from src.Ship.Providers.AppProvider import AppProvider


def create_search_app() -> Litestar:
    """Create isolated SearchModule application."""
    settings = get_settings()
    
    # Только провайдеры SearchModule
    container = make_async_container(
        AppProvider(),
        LitestarProvider(),
        SearchModuleProvider(),
        SearchRequestProvider(),
    )
    
    app = Litestar(
        route_handlers=[
            health_controller,
            search_router,
        ],
        listeners=[],  # События пойдут через брокер
        debug=settings.app_debug,
    )
    
    setup_dishka(container, app)
    return app


# Для uvicorn
app = create_search_app()
```

**Тестирование:**

```bash
# Запуск изолированного сервиса
uv run uvicorn src.SearchApp:app --port 8001

# Проверка
curl http://localhost:8001/health
curl http://localhost:8001/api/v1/search?q=test
```

### Шаг 4: Создать отдельный репозиторий сервиса

```bash
# Создаём новый репозиторий
mkdir hyper-porto-search
cd hyper-porto-search

# Инициализируем проект
uv init
uv add litestar dishka piccolo returns anyio pydantic logfire redis

# Копируем модуль
cp -r ../new_porto/src/Containers/AppSection/SearchModule src/Containers/AppSection/

# Копируем необходимые части Ship
cp -r ../new_porto/src/Ship/Parents src/Ship/
cp -r ../new_porto/src/Ship/Core src/Ship/
cp -r ../new_porto/src/Ship/Decorators src/Ship/
cp -r ../new_porto/src/Ship/Configs src/Ship/
```

### Шаг 5: Переключить трафик

- [ ] HTTP: переключить роутинг на новый сервис (DNS/Ingress)
- [ ] Синхронные вызовы: переключить DI-биндинг Gateway на HTTP-адаптер
- [ ] События: включить публикацию/подписку через брокер

### Шаг 6: Мигрировать данные

- [ ] Выбрать стратегию (см. раздел 12)
- [ ] Перенести таблицы или построить из событий
- [ ] Включить идемпотентность консьюмеров

### Шаг 7: Удалить старый код из монолита

```python
# src/App.py — убрать:
# - Импорт роутера: from src.Containers.AppSection.SearchModule import search_router
# - Из route_handlers: search_router
# - Listeners: on_user_created_index, ...

# src/Ship/Providers/AppProvider.py — убрать:
# - Импорты провайдеров SearchModule
# - Из get_all_providers(): SearchModuleProvider(), SearchRequestProvider()

# piccolo_conf.py — убрать:
# - "src.Containers.AppSection.SearchModule.Models.PiccoloApp"
```

---

## 10. Событийная система: от litestar.events к брокеру

### 10.1 Текущая схема (монолит)

```
Action → uow.add_event() → uow.commit() → __aexit__() → app.emit()
                                                            │
                                                     litestar.events
                                                      (in-process)
                                                            │
                                                      @listener()
```

**Важно:** семантика уже совместима с Outbox — события "выходят" только после реального commit.

### 10.2 Целевая схема (микросервисы)

```
┌─ Сервис-продьюсер ─────────────────────────────────────────────────┐
│                                                                     │
│  Action → uow.add_event() → uow.commit()                           │
│                                 │                                   │
│                                 ▼                                   │
│                          Outbox Table (в той же транзакции)        │
│                                 │                                   │
└─────────────────────────────────│───────────────────────────────────┘
                                  │
                           Outbox Worker                               
                                  │
                                  ▼
                         Redis Streams / Kafka
                                  │
                                  ▼
┌─ Сервис-консьюмер ─────────────────────────────────────────────────┐
│                                                                     │
│                          BrokerConsumer                            │
│                                 │                                   │
│                                 ▼                                   │
│                          Event Handlers                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 10.3 BrokerConsumer (реализация)

```python
# src/Ship/Infrastructure/EventConsumer/BrokerConsumer.py
"""Event consumer for microservice architecture."""

import asyncio
import json
from typing import Callable, Awaitable
from dataclasses import dataclass, field

import logfire
from redis.asyncio import Redis


@dataclass
class EventHandler:
    """Handler for a specific event type."""
    event_name: str
    handler: Callable[..., Awaitable[None]]
    version: str = "v1"


@dataclass
class BrokerConsumer:
    """Consumes events from Redis Streams."""
    
    redis_url: str
    consumer_group: str
    consumer_name: str
    handlers: list[EventHandler] = field(default_factory=list)
    _redis: Redis | None = field(default=None, init=False)
    
    async def start(self) -> None:
        """Start consuming events."""
        self._redis = Redis.from_url(self.redis_url)
        
        # Создаём consumer group для каждого типа события
        for handler in self.handlers:
            stream_name = f"events:{handler.event_name}"
            try:
                await self._redis.xgroup_create(
                    stream_name, 
                    self.consumer_group, 
                    id="0", 
                    mkstream=True
                )
            except Exception:
                pass  # Группа уже существует
        
        logfire.info(
            "🎧 Event consumer started",
            consumer_group=self.consumer_group,
            events=[h.event_name for h in self.handlers],
        )
        
        while True:
            await self._consume_batch()
    
    async def _consume_batch(self) -> None:
        """Consume a batch of events."""
        streams = {f"events:{h.event_name}": ">" for h in self.handlers}
        
        try:
            results = await self._redis.xreadgroup(
                groupname=self.consumer_group,
                consumername=self.consumer_name,
                streams=streams,
                count=10,
                block=5000,  # 5 секунд
            )
            
            for stream_name, messages in results:
                event_name = stream_name.decode().split(":")[1]
                handler = next(
                    (h for h in self.handlers if h.event_name == event_name),
                    None,
                )
                
                if handler:
                    for message_id, data in messages:
                        await self._process_message(
                            stream_name, message_id, data, handler
                        )
        except Exception as e:
            logfire.error("Failed to consume events", error=str(e))
            await asyncio.sleep(1)
    
    async def _process_message(
        self,
        stream_name: bytes,
        message_id: bytes,
        data: dict,
        handler: EventHandler,
    ) -> None:
        """Process a single message."""
        try:
            # Декодируем данные
            payload_raw = data.get(b"payload", b"{}")
            event_data = json.loads(payload_raw.decode())
            
            logfire.info(
                f"📥 Processing {handler.event_name}",
                message_id=message_id.decode(),
            )
            
            # Вызываем хендлер
            await handler.handler(**event_data)
            
            # ACK сообщения
            await self._redis.xack(stream_name, self.consumer_group, message_id)
            
        except Exception as e:
            logfire.error(
                f"Failed to process {handler.event_name}",
                error=str(e),
                message_id=message_id.decode(),
            )
            # Не делаем ACK — сообщение будет переобработано
```

### 10.4 Адаптация Listeners → Consumers

**До (Listeners.py):**

```python
@listener("UserCreated")
async def on_user_created_index(user_id: str, email: str, name: str, **kwargs):
    task = IndexEntityTask()
    await task.run(...)
```

**После (Consumers.py):**

```python
# src/Containers/AppSection/SearchModule/Consumers.py
"""SearchModule event consumers for microservice mode."""

from src.Ship.Infrastructure.EventConsumer.BrokerConsumer import EventHandler
from src.Containers.AppSection.SearchModule.Tasks.IndexEntityTask import (
    IndexEntityTask,
    IndexableEntity,
    RemoveFromIndexTask,
)
import logfire


async def handle_user_created(
    user_id: str,
    email: str,
    name: str,
    **kwargs,
) -> None:
    """Index newly created user."""
    logfire.info("🔍 Indexing new user", user_id=user_id)
    
    task = IndexEntityTask()
    await task.run(IndexableEntity(
        entity_type="User",
        entity_id=user_id,
        title=name,
        content=f"{name} ({email})",
        tags=["user", "active"],
        metadata={"email": email},
    ))


async def handle_user_deleted(user_id: str, **kwargs) -> None:
    """Remove deleted user from index."""
    logfire.info("🗑️ Removing user from index", user_id=user_id)
    
    task = RemoveFromIndexTask()
    await task.run(("User", user_id))


# Регистрация хендлеров
EVENT_HANDLERS = [
    EventHandler(event_name="UserCreated", handler=handle_user_created),
    EventHandler(event_name="UserDeleted", handler=handle_user_deleted),
]
```

### 10.5 Transactional Outbox (рекомендуется для production)

```python
# src/Ship/Core/OutboxEvent.py
from piccolo.table import Table
from piccolo.columns import UUID, Varchar, Text, Timestamptz, Boolean
from piccolo.columns.defaults import UUID4, TimestamptzNow


class OutboxEvent(Table, tablename="outbox_events"):
    """Transactional Outbox for reliable event publishing."""
    
    id = UUID(primary_key=True, default=UUID4())
    event_name = Varchar(length=255, index=True)
    event_version = Varchar(length=10, default="v1")
    payload = Text()  # JSON
    occurred_at = Timestamptz(default=TimestamptzNow())
    published = Boolean(default=False, index=True)
    published_at = Timestamptz(null=True, default=None)
```

```python
# src/Ship/Infrastructure/Workers/OutboxPublisher.py
"""Background worker that publishes Outbox events to broker."""

import asyncio
from datetime import datetime, timezone
import json

import logfire
from redis.asyncio import Redis

from src.Ship.Core.OutboxEvent import OutboxEvent


async def publish_outbox_events(redis_url: str, batch_size: int = 100) -> None:
    """Publish pending outbox events to broker."""
    redis = Redis.from_url(redis_url)
    
    while True:
        # Получаем неопубликованные события
        events = await OutboxEvent.select().where(
            OutboxEvent.published == False
        ).limit(batch_size).run()
        
        for event in events:
            try:
                stream_name = f"events:{event['event_name']}"
                await redis.xadd(
                    stream_name,
                    {
                        "payload": event["payload"],
                        "version": event["event_version"],
                        "event_id": str(event["id"]),
                    },
                )
                
                # Помечаем как опубликованное
                await OutboxEvent.update({
                    OutboxEvent.published: True,
                    OutboxEvent.published_at: datetime.now(timezone.utc),
                }).where(
                    OutboxEvent.id == event["id"]
                ).run()
                
                logfire.info(
                    "📤 Published outbox event",
                    event_name=event["event_name"],
                    event_id=str(event["id"]),
                )
                
            except Exception as e:
                logfire.error(
                    "Failed to publish outbox event",
                    event_id=str(event["id"]),
                    error=str(e),
                )
        
        # Пауза между итерациями
        await asyncio.sleep(1)
```

---

## 11. Конфигурация и инфраструктура

### 11.1 Важные env vars (по текущему Settings)

| Переменная | Описание | Пример |
|------------|----------|--------|
| `SERVICE_NAME` | Имя сервиса для телеметрии | `search-service` |
| `APP_PORT` | Порт сервиса | `8001` |
| `APP_DEBUG` | Debug mode | `false` |
| `APP_ENV` | Окружение | `production` |
| `DB_URL` | URL базы данных | `postgresql://...` |
| `BROKER_URL` | URL брокера событий | `redis://localhost:6379/0` |
| `CONSUMER_GROUP` | Consumer group для событий | `search-service-group` |
| `LOGFIRE_TOKEN` | Токен Logfire | `...` |

### 11.2 Важное про APP_ENV

В текущем коде `APP_ENV` влияет на инфраструктуру:

- **TaskIQ broker:**
  - `production` → Redis broker
  - иначе → InMemory broker

- **cashews cache:**
  - `production` → Redis
  - иначе → memory cache

### 11.3 Settings для микросервиса

```python
# src/Ship/Configs/Settings.py
"""SearchService configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SearchService settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Service identity
    service_name: str = Field(default="search-service")
    service_version: str = Field(default="1.0.0")
    
    # Server
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8001)
    app_debug: bool = Field(default=False)
    app_env: str = Field(default="production")
    
    # Database (own database!)
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_user: str = Field(default="search")
    db_password: str = Field(default="secret")
    db_name: str = Field(default="search_db")
    
    # Message broker
    broker_url: str = Field(default="redis://localhost:6379/0")
    consumer_group: str = Field(default="search-service-group")
    
    # External services (if needed via Gateway)
    user_service_url: str = Field(default="http://user-service:8000")
    
    # Observability
    logfire_token: str | None = Field(default=None)
    
    @property
    def db_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
```

### 11.4 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the service
EXPOSE 8001
CMD ["uv", "run", "uvicorn", "src.App:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 11.5 docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  search-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: search-service
    ports:
      - "8001:8001"
    environment:
      - SERVICE_NAME=search-service
      - APP_DEBUG=false
      - APP_ENV=production
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=search
      - DB_PASSWORD=secret
      - DB_NAME=search_db
      - BROKER_URL=redis://redis:6379/0
      - CONSUMER_GROUP=search-service-group
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - microservices-network
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: search-postgres
    environment:
      POSTGRES_USER: search
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: search_db
    volumes:
      - search-postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U search -d search_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - microservices-network

  redis:
    image: redis:7-alpine
    container_name: shared-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - microservices-network

volumes:
  search-postgres-data:

networks:
  microservices-network:
    driver: bridge
```

### 11.6 piccolo_conf.py для нового сервиса

```python
# piccolo_conf.py
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine
import os

DB = PostgresEngine(
    config={
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "user": os.getenv("DB_USER", "search"),
        "password": os.getenv("DB_PASSWORD", "secret"),
        "database": os.getenv("DB_NAME", "search_db"),
    }
)

APP_REGISTRY = AppRegistry(
    apps=[
        # Только SearchModule
        "src.Containers.AppSection.SearchModule.Models.PiccoloApp",
    ]
)
```

---

## 12. Миграция данных

### 12.1 Стратегии миграции

| Стратегия | Даунтайм | Сложность | Когда использовать |
|-----------|----------|-----------|-------------------|
| **Freeze & Move** | Есть | Низкая | Небольшой объём, допустим даунтайм |
| **Dual Write** | Нет | Высокая | Критичные данные, zero-downtime |
| **Event Replay** | Нет | Средняя | Read-модели (SearchModule) |

### 12.2 Freeze & Move (простая, с даунтаймом)

```bash
# 1. Остановить запись (feature flag или maintenance mode)
curl -X POST http://api/admin/maintenance/enable

# 2. Экспорт таблицы
pg_dump -t search_index old_db > search_index.sql

# 3. Импорт в новую БД
psql -d search_db < search_index.sql

# 4. Запустить новый сервис
docker-compose up -d search-service

# 5. Переключить трафик (nginx/ingress)
# 6. Включить запись обратно
```

### 12.3 Event Replay (рекомендуется для read-моделей)

```python
# scripts/replay_events.py
"""Replay historical events to rebuild search index."""

import asyncio
from src.Containers.AppSection.SearchModule.Consumers import EVENT_HANDLERS


async def replay_from_main_db():
    """Replay all entities from main database."""
    from piccolo.engine.postgres import PostgresEngine
    
    # Подключаемся к БД монолита (read-only)
    main_db = PostgresEngine(config={
        "host": "main-db-host",
        "database": "main_db",
        "user": "readonly_user",
        "password": "...",
    })
    
    # Получаем всех пользователей
    users = await main_db.run(
        "SELECT id, email, name, created_at FROM app_users"
    )
    
    # Эмулируем события
    handler = next(h for h in EVENT_HANDLERS if h.event_name == "UserCreated")
    
    for user in users:
        await handler.handler(
            user_id=str(user["id"]),
            email=user["email"],
            name=user["name"],
        )
        print(f"Indexed user {user['id']}")


if __name__ == "__main__":
    asyncio.run(replay_from_main_db())
```

### 12.4 Dual Write (сложная, zero-downtime)

```
⚠️ Осторожно: сложно гарантировать консистентность без SAGA/Outbox

1. Включить запись в обе БД (через feature flag)
2. Сначала писать в старую, потом в новую
3. Мониторить расхождения
4. Переключить основную запись на новую
5. Отключить старую
```

---

## 13. Module Gateway: синхронные зависимости

### 13.1 Создание Gateway Interface

```python
# src/Containers/AppSection/SearchModule/Gateways/UserGateway.py
from typing import Protocol
from dataclasses import dataclass
from returns.result import Result


@dataclass(frozen=True)
class UserInfo:
    """Minimal user info needed by SearchModule."""
    user_id: str
    email: str
    name: str
    is_active: bool


class UserGateway(Protocol):
    """Port for getting user information."""
    
    async def get_user(self, user_id: str) -> Result[UserInfo, Exception]:
        """Get user by ID."""
        ...
    
    async def get_users_batch(
        self, user_ids: list[str]
    ) -> dict[str, UserInfo | None]:
        """Get multiple users by IDs."""
        ...
```

### 13.2 Local Adapter (для монолита)

```python
# src/Containers/AppSection/SearchModule/Gateways/Adapters/LocalUserAdapter.py
from dataclasses import dataclass
from returns.result import Result, Success, Failure

from src.Containers.AppSection.UserModule.Data.Repository import UserRepository
from src.Containers.AppSection.SearchModule.Gateways.UserGateway import (
    UserGateway, UserInfo
)


@dataclass
class LocalUserAdapter:
    """Direct adapter for monolith mode."""
    
    user_repository: UserRepository
    
    async def get_user(self, user_id: str) -> Result[UserInfo, Exception]:
        try:
            user = await self.user_repository.get(user_id)
            if not user:
                return Failure(ValueError(f"User {user_id} not found"))
            
            return Success(UserInfo(
                user_id=str(user.id),
                email=user.email,
                name=user.name,
                is_active=user.is_active,
            ))
        except Exception as e:
            return Failure(e)
```

### 13.3 HTTP Adapter (для микросервиса)

```python
# src/Containers/AppSection/SearchModule/Gateways/Adapters/HttpUserAdapter.py
from dataclasses import dataclass
import httpx
from returns.result import Result, Success, Failure

from src.Containers.AppSection.SearchModule.Gateways.UserGateway import (
    UserGateway, UserInfo
)


@dataclass
class HttpUserAdapter:
    """HTTP adapter for microservice mode."""
    
    base_url: str
    timeout: float = 5.0
    
    async def get_user(self, user_id: str) -> Result[UserInfo, Exception]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}"
                )
                response.raise_for_status()
                
                data = response.json()
                return Success(UserInfo(
                    user_id=data["id"],
                    email=data["email"],
                    name=data["name"],
                    is_active=data["is_active"],
                ))
        except httpx.HTTPStatusError as e:
            return Failure(e)
        except Exception as e:
            return Failure(e)
    
    async def get_users_batch(
        self, user_ids: list[str]
    ) -> dict[str, UserInfo | None]:
        result = {}
        # В реальности — batch endpoint или параллельные запросы
        for user_id in user_ids:
            user_result = await self.get_user(user_id)
            result[user_id] = user_result.value_or(None)
        return result
```

### 13.4 Регистрация в DI

```python
# src/Containers/AppSection/SearchModule/Providers.py
from dishka import Provider, Scope, provide
import os

from src.Ship.Configs import get_settings
from src.Containers.AppSection.SearchModule.Gateways.UserGateway import UserGateway


class SearchModuleProvider(Provider):
    """Provider for SearchModule."""
    
    scope = Scope.APP
    
    @provide
    def user_gateway(self) -> UserGateway:
        settings = get_settings()
        
        # Выбор адаптера в зависимости от режима
        if os.getenv("MICROSERVICE_MODE", "false") == "true":
            from src.Containers.AppSection.SearchModule.Gateways.Adapters.HttpUserAdapter import HttpUserAdapter
            return HttpUserAdapter(base_url=settings.user_service_url)
        else:
            # В монолите используем прямой адаптер
            # (требует UserRepository в DI)
            from src.Containers.AppSection.SearchModule.Gateways.Adapters.LocalUserAdapter import LocalUserAdapter
            # ... получить UserRepository из DI
            raise NotImplementedError("Local adapter requires UserRepository setup")
```

---

## 14. Транспорты при выносе

### 14.1 HTTP (REST)

Обычно самый простой слой для выноса:

- Роутер модуля (`UI/API/Routes.py`) переезжает в сервис
- `src/App.py` в сервисе регистрирует только свои роуты
- Клиенты переключаются по DNS/Ingress

### 14.2 GraphQL

**Варианты:**

| Подход | Описание | Когда использовать |
|--------|----------|-------------------|
| **Gateway с резолверами** | GraphQL в API Gateway, резолверы вызывают HTTP | Простой старт |
| **Federation/Stitching** | Каждый сервис — свой subgraph | Масштабирование |
| **GraphQL на сервис** | Отдельный GraphQL endpoint | Редко удобно |

**Практика:** чаще всего GraphQL остаётся в gateway.

### 14.3 WebSocket + Channels

**В монолите:**

```python
app.plugins.get(ChannelsPlugin)
```

**После выноса:**

| Сценарий | Решение |
|----------|---------|
| WebSocket в одном сервисе (gateway) | Другие сервисы публикуют через брокер/HTTP |
| WebSocket распределён | Backend Channels = Redis (не memory), общие имена каналов |

**Практика:** "Realtime Gateway" как отдельный сервис часто проще.

### 14.4 CLI

**Два пути:**

1. CLI становится **клиентом API** (HTTP вызовы в сервис)
2. CLI остаётся **внутри сервиса** (для администрирования в приватной сети)

### 14.5 Workers (TaskIQ)

**Рекомендация:**

- У каждого сервиса свои воркеры
- Воркеры оперируют только данными своего сервиса
- Межсервисные действия — через события/команды (SAGA)

---

## 15. Практический пример: SearchModule → SearchService

### 15.1 Почему SearchModule — хороший кандидат

- ✅ Модуль в основном асинхронный (индексация)
- ✅ Уже слушает события других модулей
- ✅ Имеет свою таблицу `SearchIndex` и миграции
- ✅ Его ошибки/консистентность не критичны для "write" потоков

### 15.2 Что переносим "как есть"

| Компонент | Изменения |
|-----------|-----------|
| `src/Containers/AppSection/SearchModule/` целиком | — |
| `Models/PiccoloApp.py` и `migrations/` | — |
| `UI/API/Routes.py` | — |

### 15.3 Что меняем

**Listeners.py → Consumers.py:**

```python
# Было (litestar.events):
@listener("UserCreated")
async def on_user_created_index(user_id: str, email: str, name: str, **kwargs):
    ...

# Стало (BrokerConsumer):
EVENT_HANDLERS = [
    EventHandler(event_name="UserCreated", handler=handle_user_created),
]
```

### 15.4 Что НЕ меняем

```python
# Actions остаются без изменений
class IndexEntityAction(Action[IndexRequest, IndexResult, SearchError]):
    async def run(self, data: IndexRequest) -> Result[IndexResult, SearchError]:
        # Та же логика
        ...

# Tasks остаются без изменений
class IndexEntityTask(Task[IndexableEntity, None]):
    async def run(self, entity: IndexableEntity) -> None:
        # Та же логика
        ...

# Queries остаются без изменений
class FullTextSearchQuery(Query[SearchParams, list[SearchResult]]):
    async def execute(self, params: SearchParams) -> list[SearchResult]:
        # Та же логика
        ...
```

### 15.5 Контракты событий для SearchService

**Зафиксировать перед выносом:**

| Событие | Producer | Версия | Обязательные поля |
|---------|----------|--------|-------------------|
| `UserCreated` | UserService | v1 | user_id, email, name |
| `UserUpdated` | UserService | v1 | user_id |
| `UserDeleted` | UserService | v1 | user_id |
| `PaymentCreated` | PaymentService | v1 | payment_id, amount |

### 15.6 Переключение чтения

**До:** `/api/v1/search` из `src/App.py`

**После:**
- API gateway проксирует на SearchService
- или клиент ходит напрямую (редко)

---

## 16. Типичные ошибки и как их избежать

### 16.1 Потеря событий (Dual Write Problem)

**❌ Проблема:**

```python
# Событие отправляется ДО коммита
async with uow:
    await uow.users.add(user)
    await publish_to_broker(UserCreated(...))  # ← Опасно!
    await uow.commit()  # Может упасть
```

**✅ Решение: Outbox**

```python
# Событие записывается в ту же транзакцию
async with uow:
    await uow.users.add(user)
    await uow.outbox.add(UserCreated(...))  # В ту же БД
    await uow.commit()
# Отдельный worker публикует из Outbox
```

### 16.2 Отсутствие идемпотентности

**❌ Проблема:**

```python
async def handle_payment_created(payment_id: str, amount: float, **kwargs):
    # При повторной доставке — дублирование
    await create_invoice(payment_id, amount)
```

**✅ Решение:**

```python
async def handle_payment_created(payment_id: str, amount: float, **kwargs):
    # Проверяем, обрабатывали ли уже
    if await redis.get(f"processed:payment:{payment_id}"):
        return  # Уже обработали
    
    await create_invoice(payment_id, amount)
    
    # Помечаем как обработанное (TTL 7 дней)
    await redis.set(f"processed:payment:{payment_id}", "1", ex=86400 * 7)
```

### 16.3 Нет версионирования событий

**❌ Проблема:**

```python
# Продьюсер добавил новое поле
class UserCreated(DomainEvent):
    user_id: str
    email: str
    name: str
    phone: str  # НОВОЕ — сломает старых консьюмеров
```

**✅ Решение:**

```python
class UserCreatedV2(DomainEvent):
    event_name: str = "UserCreated"
    event_version: str = "v2"  # Версия!
    
    user_id: str
    email: str
    name: str
    phone: str | None = None  # Optional для совместимости
```

### 16.4 Циклические зависимости

**❌ Проблема:**

```
SearchService → UserService (для получения данных)
UserService → SearchService (для поиска)
```

**✅ Решение: Event-Carried State Transfer**

```python
# SearchService хранит копию нужных данных
class UserReplica(Table):
    user_id = UUID(primary_key=True)
    email = Varchar()
    name = Varchar()

# Обновляется по событиям UserCreated/UserUpdated
```

### 16.5 "Событие есть, но никто не гарантирует поля"

**❌ Проблема:**

Событие публикуется как dict, слушатели завязаны на имена полей.

**✅ Решение:**

- Envelope + версионирование
- Валидация payload при публикации и потреблении
- Contract tests

---

## 17. Чеклисты

### 17.1 Чеклист "модуль готов к выносу"

```markdown
## Подготовка к выносу: [ModuleName]

### Изоляция кода
- [ ] Нет прямых импортов из других Containers
- [ ] Зависимости через Events или Gateway
- [ ] Ship-компоненты выделены или копируемы

### Изоляция данных
- [ ] Модуль владеет своими таблицами
- [ ] Нет чужих write-операций в наши таблицы
- [ ] Нет наших write-операций в чужие таблицы

### Событийный контракт
- [ ] Все потребляемые события задокументированы
- [ ] Все публикуемые события задокументированы
- [ ] События имеют версии (event_version)
- [ ] Обязательные и опциональные поля определены

### Идемпотентность
- [ ] Consumer handlers идемпотентны
- [ ] Критичные операции имеют idempotency keys
- [ ] Логика устойчива к дублированию сообщений
```

### 17.2 Чеклист выноса

```markdown
## Вынос модуля: [ModuleName]

### Шаг 1: Изолированный запуск (в том же репо)
- [ ] Создан отдельный App.py для модуля
- [ ] Модуль запускается на отдельном порту
- [ ] HTTP endpoints работают
- [ ] Health check проходит

### Шаг 2: Новый репозиторий
- [ ] Создан репозиторий
- [ ] Скопирован код модуля
- [ ] Скопированы/добавлены зависимости Ship
- [ ] pyproject.toml настроен
- [ ] piccolo_conf.py настроен

### Шаг 3: Событийная система
- [ ] Listeners переделаны в Consumers
- [ ] BrokerConsumer настроен
- [ ] События читаются из брокера
- [ ] Продьюсер публикует в брокер

### Шаг 4: Инфраструктура
- [ ] Dockerfile создан
- [ ] docker-compose.yml создан
- [ ] CI/CD настроен
- [ ] Мониторинг настроен (Logfire)

### Шаг 5: Миграция данных
- [ ] Стратегия миграции выбрана
- [ ] Данные мигрированы
- [ ] Данные верифицированы

### Шаг 6: Переключение
- [ ] Трафик переключён на новый сервис
- [ ] Модуль удалён из монолита
- [ ] Старые listeners удалены
- [ ] Старые providers удалены
- [ ] PiccoloApp удалён из piccolo_conf.py

### Шаг 7: Верификация
- [ ] Все endpoints работают
- [ ] События обрабатываются
- [ ] Логи и метрики собираются
- [ ] Алерты настроены
```

### 17.3 Чеклист "сервис запущен"

```markdown
## Сервис запущен: [ServiceName]

### Конфигурация
- [ ] Отдельный src/App.py собирает только нужные роуты/listeners
- [ ] piccolo_conf.py содержит только нужные PiccoloApp
- [ ] DB_URL, BROKER_URL, APP_ENV настроены корректно

### Health & Readiness
- [ ] Есть /health endpoint
- [ ] Есть /health/ready endpoint (если БД)

### Observability
- [ ] Логи маркируются service_name (Logfire)
- [ ] Трейсы настроены
- [ ] Метрики собираются
```

---

## 18. Шаблоны файлов

### 18.1 Шаблон App.py для микросервиса

```python
# src/App.py
"""${ServiceName} main application."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import anyio
import socket

from litestar import Litestar
from dishka import make_async_container
from dishka.integrations.litestar import setup_dishka, LitestarProvider

from src.Ship.Configs import get_settings
from src.Ship.Infrastructure.HealthCheck import health_controller
from src.Ship.Infrastructure.EventConsumer.BrokerConsumer import BrokerConsumer
from src.Containers.AppSection.${ModuleName} import ${module}_router
from src.Containers.AppSection.${ModuleName}.Providers import (
    ${ModuleName}Provider,
    ${ModuleName}RequestProvider,
)
from src.Containers.AppSection.${ModuleName}.Consumers import EVENT_HANDLERS


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan with event consumer."""
    settings = get_settings()
    
    consumer = BrokerConsumer(
        redis_url=settings.broker_url,
        consumer_group=settings.consumer_group,
        consumer_name=f"{settings.service_name}-{socket.gethostname()}",
        handlers=EVENT_HANDLERS,
    )
    
    async with anyio.create_task_group() as tg:
        tg.start_soon(consumer.start)
        try:
            yield
        finally:
            tg.cancel_scope.cancel()


def create_app() -> Litestar:
    """Create ${ServiceName} application."""
    settings = get_settings()
    
    container = make_async_container(
        ${ModuleName}Provider(),
        ${ModuleName}RequestProvider(),
        LitestarProvider(),
    )
    
    app = Litestar(
        route_handlers=[
            health_controller,
            ${module}_router,
        ],
        lifespan=[lifespan],
        debug=settings.app_debug,
    )
    
    setup_dishka(container, app)
    return app


app = create_app()
```

### 18.2 Шаблон Consumers.py

```python
# src/Containers/AppSection/${ModuleName}/Consumers.py
"""${ModuleName} event consumers for microservice mode."""

import logfire
from src.Ship.Infrastructure.EventConsumer.BrokerConsumer import EventHandler

# Import tasks/actions needed for handling events
# from src.Containers.AppSection.${ModuleName}.Tasks.SomeTask import SomeTask


async def handle_some_event(
    entity_id: str,
    **kwargs,
) -> None:
    """Handle SomeEvent."""
    logfire.info("📥 Processing SomeEvent", entity_id=entity_id)
    
    # Idempotency check (example)
    # if await redis.get(f"processed:{entity_id}"):
    #     return
    
    # Your handling logic here
    # task = SomeTask()
    # await task.run(...)
    
    # Mark as processed
    # await redis.set(f"processed:{entity_id}", "1", ex=86400 * 7)


# Register all event handlers
EVENT_HANDLERS = [
    EventHandler(event_name="SomeEvent", handler=handle_some_event),
    # Add more handlers as needed
]
```

### 18.3 Шаблон env.example

```bash
# env.example

# Service Identity
SERVICE_NAME=search-service
SERVICE_VERSION=1.0.0

# Server
APP_HOST=0.0.0.0
APP_PORT=8001
APP_DEBUG=false
APP_ENV=production

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=search
DB_PASSWORD=change-me-in-production
DB_NAME=search_db

# Message Broker
BROKER_URL=redis://localhost:6379/0
CONSUMER_GROUP=search-service-group

# External Services (if using Gateway)
USER_SERVICE_URL=http://user-service:8000

# Observability
LOGFIRE_TOKEN=
```

---

## 19. Troubleshooting

### 19.1 События не приходят в консьюмер

**Симптомы:**
- Consumer запущен, но не получает сообщения
- В логах нет ошибок

**Проверить:**

```bash
# Проверить, есть ли сообщения в stream
redis-cli XLEN events:UserCreated

# Проверить consumer group
redis-cli XINFO GROUPS events:UserCreated

# Проверить pending messages
redis-cli XPENDING events:UserCreated search-service-group
```

**Решения:**
- Убедиться, что продьюсер публикует в тот же stream
- Проверить, что consumer_group создан
- Проверить, что читаем с `>` (новые сообщения), а не с `0` (все)

### 19.2 Дублирование обработки событий

**Симптомы:**
- Одно событие обрабатывается несколько раз
- Данные дублируются

**Проверить:**
- Есть ли idempotency check в handler
- Делается ли ACK после обработки

**Решения:**

```python
async def handle_event(event_id: str, **kwargs):
    # Idempotency check
    if await redis.get(f"processed:{event_id}"):
        logfire.info("Event already processed", event_id=event_id)
        return
    
    # Process event
    ...
    
    # Mark as processed
    await redis.set(f"processed:{event_id}", "1", ex=86400 * 7)
```

### 19.3 Outbox не публикует события

**Симптомы:**
- События накапливаются в outbox_events
- published = False

**Проверить:**
- Запущен ли OutboxPublisher worker
- Есть ли подключение к Redis
- Есть ли ошибки в логах worker'а

**Решения:**

```bash
# Проверить количество непубликованных
psql -c "SELECT COUNT(*) FROM outbox_events WHERE published = false"

# Посмотреть последние события
psql -c "SELECT * FROM outbox_events ORDER BY occurred_at DESC LIMIT 10"

# Запустить worker вручную для debug
uv run python -c "
import asyncio
from src.Ship.Infrastructure.Workers.OutboxPublisher import publish_outbox_events
asyncio.run(publish_outbox_events('redis://localhost:6379/0'))
"
```

### 19.4 Gateway timeout / connection refused

**Симптомы:**
- HTTP запросы к другому сервису падают
- Connection refused / timeout

**Проверить:**
- Доступен ли целевой сервис
- Правильный ли URL в настройках
- Есть ли сетевая связность (docker networks)

**Решения:**

```bash
# Проверить доступность
curl http://user-service:8000/health

# Проверить DNS (в docker)
docker exec search-service nslookup user-service

# Проверить переменные окружения
docker exec search-service env | grep USER_SERVICE
```

### 19.5 Миграции не применяются

**Симптомы:**
- Таблицы не создаются
- "relation does not exist" ошибки

**Проверить:**
- Правильный ли piccolo_conf.py
- Подключение к БД работает
- APP_REGISTRY содержит нужные модули

**Решения:**

```bash
# Проверить статус миграций
uv run piccolo migrations check

# Применить миграции
uv run piccolo migrations forwards all

# Проверить таблицы
psql -c "\dt"
```

---

## 📚 Связанная документация

- [00-philosophy.md](00-philosophy.md) — Философия и стратегия "монолит → distributed monolith → микросервисы"
- [01-architecture.md](01-architecture.md) — Архитектурные слои
- [10-registration.md](10-registration.md) — Явная регистрация компонентов
- [13-cross-module-communication.md](13-cross-module-communication.md) — Межмодульное взаимодействие (Events, Gateway)
- [14-module-gateway-pattern.md](14-module-gateway-pattern.md) — Module Gateway Pattern (подробно)
- [15-saga-patterns.md](15-saga-patterns.md) — Distributed transactions и SAGA

---

<div align="center">

**Hyper-Porto v4.3**

*От модульного монолита к микросервисам — шаг за шагом*

🏢 Monolith → 🔀 Distributed → 🚀 Microservice

</div>
