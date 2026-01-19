# 🎮 Command: /guide

> Интерактивный гайд по Agent OS и Hyper-Porto архитектуре.

---

## Синтаксис

```
/guide [тема]
```

## Доступные темы

| Тема | Описание |
|------|----------|
| `/guide` | Общий обзор системы |
| `/guide start` | С чего начать новичку |
| `/guide architecture` | Архитектура Hyper-Porto |
| `/guide pipelines` | Основные рабочие процессы |
| `/guide spec-driven` | Spec-Driven Development 🆕 |
| `/guide research` | Команды ресерча 🆕 |
| `/guide components` | Компоненты системы |
| `/guide commands` | Все доступные команды |
| `/guide troubleshoot` | Как решать проблемы |

---

# 📖 /guide — Общий обзор

## Что такое Agent OS?

**Agent OS** — это система стандартов, шаблонов и инструкций для AI-assisted разработки в проекте **Hyper-Porto v4.3**.

### 🎯 Назначение

| Для кого | Что даёт |
|----------|----------|
| **AI агент** | Понимание архитектуры, шаблоны кода, правила |
| **Разработчик** | Быстрый старт, чеклисты, troubleshooting |
| **Команда** | Единые стандарты, code review guidelines |

### 📊 Состав Agent OS

```
📋 Specs           — спецификации фич (agent-os/specs/)
📏 Standards (16)  — правила написания кода
📦 Templates (16)  — готовые шаблоны файлов  
📋 Workflows (3)   — пошаговые инструкции
✅ Checklists (3)  — чеклисты проверки
🔧 Troubleshooting — решение проблем
🧩 Snippets (4)    — готовые паттерны кода
🚫 Anti-patterns   — чего НЕ делать
🗣️ Slang           — словарь сленга (можно дополнять!)
```

---

# 🚀 /guide start — С чего начать

## Для новичка в проекте

### Шаг 1: Понять архитектуру (5 мин)
```
Прочитай: agent-os/standards/architecture/constitution.md
```
**Ключевые правила:**
- Actions возвращают `Result[T, E]`
- Импорты только абсолютные от `src.`
- Containers изолированы (общение через Events)

### Шаг 2: Изучить структуру (5 мин)
```
Прочитай: docs/02-project-structure.md
```
```
src/
├── Ship/        # Общая инфраструктура
└── Containers/  # Бизнес-модули
    └── AppSection/
        └── UserModule/  # Пример модуля
```

### Шаг 3: Посмотреть реальный код (10 мин)
```
Открой: src/Containers/AppSection/UserModule/
```
Изучи структуру реального модуля.

### Шаг 4: Начать работу
```
/guide pipelines — узнать рабочие процессы
/guide spec-driven — Spec-Driven Development
```

---

# 🏗️ /guide architecture — Архитектура

## Hyper-Porto v4.3

**Синтез трёх парадигм:**

| Источник | Что берём |
|----------|-----------|
| **Porto** | Container/Ship структура |
| **Cosmic Python** | Repository, UoW, Events |
| **Returns** | Result[T, E], Railway programming |

### Слои архитектуры

```
┌─────────────────────────────────────────┐
│            FRAMEWORK (Litestar)          │
│  HTTP, WebSocket, CLI, GraphQL, TaskIQ   │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│                 SHIP                     │
│  Parents, Core, Providers, Decorators    │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│Container│   │Container│   │Container│
│  User   │   │  Order  │   │ Payment │
└─────────┘   └─────────┘   └─────────┘
```

### Ключевые паттерны

| Паттерн | Где | Зачем |
|---------|-----|-------|
| **Result[T,E]** | Actions | Явная обработка ошибок |
| **CQRS** | Actions/Queries | Разделение чтения/записи |
| **UnitOfWork** | Actions | Транзакции + Events |
| **Repository** | Data | Абстракция над ORM |
| **Domain Events** | UoW → Listeners | Межмодульное общение |

### Подробнее
```
agent-os/standards/architecture/patterns.md
```

---

# 📝 /guide spec-driven — Spec-Driven Development

## Основной workflow: От идеи до кода

```
┌─────────────────────────────────────────────────────────────┐
│  1. ПЛАНИРОВАНИЕ                                             │
│     agent-os/plan-product → mission.md, roadmap.md           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. РЕСЕРЧ (опционально)                                     │
│     agent-os/research → комплексный                          │
│     agent-os/research-codebase → примеры в коде              │
│     agent-os/research-online → документация, статьи          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. СПЕЦИФИКАЦИЯ                                             │
│     agent-os/shape-spec → requirements.md                    │
│     agent-os/write-spec → spec.md                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. ЗАДАЧИ                                                   │
│     agent-os/create-tasks → tasks.md                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  5. РЕАЛИЗАЦИЯ                                               │
│     agent-os/implement-tasks → код в src/Containers/         │
└─────────────────────────────────────────────────────────────┘
```

## Где создаются файлы

### Спецификации → `agent-os/specs/`

```
agent-os/specs/2026-01-18-user-management/
├── planning/
│   ├── requirements.md      # Собранные требования
│   ├── research.md          # Результаты ресерча
│   └── visuals/             # Макеты, скриншоты
├── spec.md                  # Спецификация
├── tasks.md                 # Задачи
└── verifications/           # Верификация
```

### Код → `src/Containers/`

```
src/Containers/AppSection/[Module]/
├── Actions/
├── Tasks/
├── Data/
├── Models/
├── UI/
└── ...
```

## Команды Spec-Driven

| Шаг | Команда | Результат |
|-----|---------|-----------|
| 1 | `agent-os/plan-product` | mission.md, roadmap.md |
| 2 | `agent-os/shape-spec` | requirements.md, visuals/ |
| 3 | `agent-os/write-spec` | spec.md |
| 4 | `agent-os/create-tasks` | tasks.md |
| 5 | `agent-os/implement-tasks` | Код |

📖 **Подробнее:** `docs/07-spec-driven.md`

---

# 🔍 /guide research — Команды ресерча

## Три режима ресерча

| Команда | Где ищет | Когда использовать |
|---------|----------|-------------------|
| `agent-os/research` | Везде | Комплексный ресерч перед фичей |
| `agent-os/research-codebase` | `src/`, `docs/`, внешние ссылки | Найти примеры в коде |
| `agent-os/research-online` | Web, Context7 | Документация, best practices |

## Примеры использования

### Ресерч в кодовой базе
```bash
agent-os/research-codebase Actions
# Найти все примеры Actions в проекте

agent-os/research-codebase Repository pattern
# Как реализованы Repositories

agent-os/research-codebase GraphQL resolvers
# Примеры GraphQL кода
```

### Ресерч онлайн
```bash
agent-os/research-online Litestar middleware
# Документация по middleware

agent-os/research-online Piccolo migrations
# Как делать миграции

agent-os/research-online Dishka scopes
# Объяснение scopes в DI
```

### Комплексный ресерч
```bash
agent-os/research WebSocket handlers
# Ищет везде: код, docs, онлайн
```

## Результаты ресерча

Сохраняются в спецификацию:
```
agent-os/specs/[текущая-спека]/planning/research.md
```

---

# 🔄 /guide pipelines — Рабочие процессы

## Pipeline 0: Spec-Driven Development (рекомендуется) 🆕

```
📋 Задача: Разработка новой фичи от идеи до кода

🎮 Команды:
   1. agent-os/plan-product    → Планирование (один раз)
   2. agent-os/research        → Ресерч (опционально)
   3. agent-os/shape-spec      → Сбор требований
   4. agent-os/write-spec      → Спецификация
   5. agent-os/create-tasks    → Задачи
   6. agent-os/implement-tasks → Реализация

📁 Результат:
   agent-os/specs/YYYY-MM-DD-feature/
   └── spec.md, tasks.md, planning/

📖 Подробнее: docs/07-spec-driven.md
```

---

## Pipeline 1: Создание нового модуля

```
📋 Задача: Создать новый бизнес-модуль (Container)

🎮 Команда: dev/create-module OrderModule

📁 Результат:
   Containers/AppSection/OrderModule/
   ├── Actions/
   ├── Queries/
   ├── Data/
   ├── Models/
   ├── UI/
   ├── Events.py
   ├── Errors.py
   └── Providers.py

✅ Чеклист: agent-os/checklists/new-module.md
📋 Workflow: agent-os/workflows/create-module.md
```

---

## Pipeline 2: Добавление API endpoint

```
📋 Задача: Добавить новый REST endpoint

🎮 Команда: dev/add-endpoint POST /orders для CreateOrderAction

📝 Создаётся:
   1. Request DTO (Pydantic)
   2. Action (Use Case)
   3. Endpoint в Controller
   4. Регистрация в Providers

📦 Шаблоны:
   - templates/action.py.template
   - templates/controller.py.template

📋 Workflow: agent-os/workflows/add-api-endpoint.md
```

---

## Pipeline 3: Добавление Domain Event

```
📋 Задача: Добавить событие для межмодульного общения

🎮 Команда: dev/add-action ProcessPayment с событием PaymentProcessed

📝 Создаётся:
   1. Event (dataclass)
   2. Публикация в Action через UoW
   3. Listener (@listener)
   4. Регистрация в App.py

📦 Шаблон: templates/event.py.template
📋 Workflow: agent-os/workflows/add-domain-event.md
```

---

## Pipeline 4: Генерация полного CRUD

```
📋 Задача: Быстро создать CRUD для сущности

🎮 Команда: dev/generate-crud Product в ShopModule

📝 Создаётся всё:
   - Model (Piccolo)
   - Repository
   - UnitOfWork
   - Errors + Events
   - Queries (Get, List)
   - Actions (Create, Update, Delete)
   - Controller (REST API)
   - Listeners
   - Providers

📦 Все шаблоны из templates/
```

---

## Pipeline 5: Исправление ошибки

```
📋 Задача: Понять и исправить ошибку

🔧 Шаги:
   1. Определи тип ошибки
   2. Найди в troubleshooting/
   3. Примени решение

📁 Гайды:
   - troubleshooting/di-errors.md      — DI проблемы
   - troubleshooting/result-errors.md  — Result проблемы
   - troubleshooting/import-errors.md  — Импорты
```

---

## Pipeline 6: Code Review

```
📋 Задача: Проверить код перед merge

✅ Чеклист: agent-os/checklists/code-review.md

🔴 Критичные проверки:
   - Импорты абсолютные от src.
   - Actions возвращают Result
   - Нет импортов между Containers
   - События через UoW

🚫 Анти-паттерны: agent-os/anti-patterns/common-mistakes.md
```

---

# 🧩 /guide components — Компоненты

## Компоненты Hyper-Porto

| Компонент | Файл | Назначение | Return |
|-----------|------|------------|--------|
| **Action** | `Actions/*.py` | Use Case (write) | `Result[T, E]` |
| **Task** | `Tasks/*.py` | Атомарная операция | `T` |
| **Query** | `Queries/*.py` | CQRS Read | `T \| None` |
| **Repository** | `Data/Repositories/*.py` | CRUD + domain queries | — |
| **UnitOfWork** | `Data/UnitOfWork.py` | Транзакции + Events | — |
| **Controller** | `UI/API/Controllers/*.py` | HTTP endpoints | Response |
| **Event** | `Events.py` | Domain Event | — |
| **Listener** | `Listeners.py` | Event handler | — |
| **Error** | `Errors.py` | Бизнес-ошибки | — |

## Правила вызовов

```
Controller → Action (write) или Query (read)
     │
     ▼
Action → Tasks + UoW (Repository + Events)
     │
     ▼
Result[T, E] → @result_handler → Response
```

## Подробнее
```
agent-os/standards/backend/actions-tasks.md
agent-os/standards/backend/queries.md
```

---

# 🎮 /guide commands — Все команды

## Spec-Driven команды (`.claude/commands/agent-os/`)

| Команда | Описание |
|---------|----------|
| `agent-os/plan-product` | 📋 Планирование продукта |
| `agent-os/shape-spec` | 🔍 Сбор требований |
| `agent-os/write-spec` | 📝 Написание спецификации |
| `agent-os/create-tasks` | ✅ Создание задач |
| `agent-os/implement-tasks` | 🚀 Реализация (простой) |
| `agent-os/orchestrate-tasks` | 🎭 Реализация (с subagents) |

## Команды ресерча (`.claude/commands/agent-os/`) 🆕

| Команда | Описание |
|---------|----------|
| `agent-os/research` | 📚 Комплексный ресерч |
| `agent-os/research-codebase` | 🔍 Ресерч в коде |
| `agent-os/research-online` | 🌐 Ресерч онлайн |

## Dev команды (`.claude/commands/dev/`)

| Команда | Описание |
|---------|----------|
| `dev/slang` | 🗣️ Словарь сленга |
| `dev/guide` | 📖 Этот гайд |
| `dev/create-module` | 📦 Создать Container |
| `dev/add-action` | ⚡ Создать Action |
| `dev/add-endpoint` | 🔌 Добавить endpoint |
| `dev/generate-crud` | 🔄 Полный CRUD |

## Примеры использования

```bash
# Spec-Driven
agent-os/plan-product
agent-os/shape-spec Система оплаты
agent-os/research-codebase Repository

# Dev
dev/create-module PaymentModule в VendorSection
dev/add-endpoint POST /payments/process для ProcessPaymentAction
dev/generate-crud Invoice в BillingModule
dev/slang экшн
```

---

# 🔧 /guide troubleshoot — Решение проблем

## Быстрая диагностика

| Симптом | Смотри |
|---------|--------|
| `NoFactoryError` | `troubleshooting/di-errors.md` |
| Result не конвертируется | `troubleshooting/result-errors.md` |
| `ImportError` | `troubleshooting/import-errors.md` |
| Код работает неправильно | `anti-patterns/common-mistakes.md` |
| Async проблемы | `anti-patterns/bad-async.md` |

## Топ-3 ошибки новичков

### 1. Забыл `FromDishka`
```python
# ❌ Плохо
async def create(self, action: CreateAction): ...

# ✅ Хорошо  
async def create(self, action: FromDishka[CreateAction]): ...
```

### 2. Относительные импорты
```python
# ❌ Плохо
from ....Actions import X

# ✅ Хорошо
from src.Containers.Section.Module.Actions import X
```

### 3. Exception вместо Result
```python
# ❌ Плохо
raise UserNotFoundError()

# ✅ Хорошо
return Failure(UserNotFoundError(user_id=id))
```

---

# 📚 /guide resources — Ресурсы

## Agent OS

| Ресурс | Путь |
|--------|------|
| **Спецификации** | `agent-os/specs/` |
| Стандарты | `agent-os/standards/` |
| Шаблоны | `agent-os/templates/` |
| Workflows | `agent-os/workflows/` |
| Чеклисты | `agent-os/checklists/` |
| Troubleshooting | `agent-os/troubleshooting/` |
| Сниппеты | `agent-os/snippets/` |
| **Сленг** | `agent-os/slang/dictionary.md` |
| Глоссарий | `agent-os/glossary.md` |

## Документация проекта

| Ресурс | Путь |
|--------|------|
| Философия | `docs/00-philosophy.md` |
| Архитектура | `docs/01-architecture.md` |
| Структура | `docs/02-project-structure.md` |
| Компоненты | `docs/03-components.md` |
| Result/Railway | `docs/04-result-railway.md` |
| **Spec-Driven** | `docs/07-spec-driven.md` |

## Документация библиотек

| Библиотека | Путь |
|------------|------|
| Litestar | <https://docs.litestar.dev/> |
| Piccolo | <https://piccolo-orm.com/docs/> |
| Dishka | <https://dishka.dev/> |
| Returns | <https://returns.readthedocs.io/> |
| Strawberry | <https://strawberry.rocks/docs/> |

---

# 🎯 Quick Reference

## Разработка фичи (Spec-Driven)
```
agent-os/plan-product    → mission, roadmap
agent-os/research        → ресерч
agent-os/shape-spec      → requirements
agent-os/write-spec      → spec.md
agent-os/create-tasks    → tasks.md
agent-os/implement-tasks → код
```

## Быстрые действия
```
dev/create-module OrderModule
→ workflows/create-module.md

dev/add-endpoint POST /orders
→ workflows/add-api-endpoint.md

dev/generate-crud Invoice
→ templates/*.template
```

## Ресерч
```
agent-os/research WebSocket
→ комплексный (код + онлайн)

agent-os/research-codebase Actions
→ примеры в src/

agent-os/research-online Litestar events
→ документация, статьи
```

## Troubleshooting
```
→ troubleshooting/*.md
→ anti-patterns/*.md
```

## Не понимаю сленг
```
dev/slang <слово>
→ slang/dictionary.md (можно дополнять!)
```

---

**Agent OS v4.3** — Your AI Development Companion 🚀
