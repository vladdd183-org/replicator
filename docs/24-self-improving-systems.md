# 24. Self-Improving Systems — Системы самообучения

> Архитектура систем непрерывного обучения и эволюции AI-агента в Hyper-Porto.

---

## Обзор

### Философия Self-Improving

Self-Improving Systems — это набор механизмов, позволяющих AI-агенту:

1. **Учиться на ошибках** — сохранять и анализировать паттерны ошибок
2. **Накапливать знания** — структурировать опыт в переиспользуемую память
3. **Эволюционировать стандарты** — автоматически обновлять правила на основе практики
4. **Интегрировать внешние знания** — подключать актуальные источники (docs, arXiv, web)
5. **Обучаться активно** — симулировать сценарии для закрепления паттернов

### Цикл обучения

```
┌─────────────────────────────────────────────────────────────┐
│                    LEARNING CYCLE                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  ACTION  │───▶│ FEEDBACK │───▶│  MEMORY  │             │
│   └──────────┘    └──────────┘    └──────────┘             │
│        ▲                               │                    │
│        │                               ▼                    │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │ IMPROVE  │◀───│ PATTERNS │◀───│ ANALYZE  │             │
│   └──────────┘    └──────────┘    └──────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Архитектура систем

```
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                │
│                 (Единая точка входа)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   MEMORY    │  │  FEEDBACK   │  │  STANDARDS EVOLUTION    │  │
│  │   SYSTEM    │  │    LOOP     │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  KNOWLEDGE  │  │  TRAINING   │  │   CONTEXT COMPRESSION   │  │
│  │ INTEGRATION │  │    MODE     │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Memory System

Многоуровневая система памяти для накопления и переиспользования опыта.

### 4 уровня памяти

```
agent-os/memory/
├── knowledge/              # Уровень 1: Статические знания
│   ├── architecture/       # Архитектурные решения (ADR)
│   ├── decisions/          # Важные решения
│   └── patterns/           # Проверенные паттерны
│
├── learning/               # Уровень 2: Обучение на ошибках
│   ├── mistakes/           # Записи об ошибках
│   ├── corrections/        # Как исправлялись
│   └── anti-patterns/      # Что НЕ делать
│
├── experience/             # Уровень 3: Накопленный опыт
│   ├── sessions/           # Успешные сессии
│   ├── solutions/          # Решения проблем
│   └── optimizations/      # Найденные оптимизации
│
└── context/                # Уровень 4: Контекст проекта
    ├── project-state.md    # Текущее состояние
    ├── active-tasks.md     # Активные задачи
    └── recent-changes.md   # Недавние изменения
```

### Уровень 1: Knowledge (Знания)

**Что хранит:** Архитектурные решения (ADR), паттерны, стандарты.

**Формат ADR (Architecture Decision Record):**

```markdown
---
id: ADR-001
title: Использование Result[T, E] вместо исключений
status: accepted                    # draft | accepted | deprecated
date: 2025-01-19
context: |
  В бизнес-логике нужна явная обработка ошибок без исключений.
decision: |
  Все Actions возвращают Result[T, E] из библиотеки returns.
consequences:
  positive:
    - Явные типы ошибок в сигнатуре
    - Pattern matching для обработки
    - Композиция через bind/map
  negative:
    - Дополнительный бойлерплейт
    - Кривая обучения для команды
related:
  - docs/04-result-railway.md
  - agent-os/standards/global/error-handling.md
---
```

**Формат Pattern:**

```markdown
---
id: PATTERN-001
name: Repository + UnitOfWork
category: data-access
frequency: high                     # high | medium | low
confidence: 0.95
---

## Проблема
Нужна абстракция над ORM с поддержкой транзакций и events.

## Решение
Repository для доступа к данным + UnitOfWork для транзакций.

## Пример
[code example]

## Когда применять
- Любой CRUD для доменных сущностей
- Когда нужны Domain Events
```

### Уровень 2: Learning (Обучение)

**Что хранит:** Ошибки, их причины, способы исправления.

**Формат Mistake:**

```markdown
---
id: MISTAKE-042
date: 2025-01-19
category: di                        # di | import | result | migration | ...
severity: medium                    # low | medium | high
recurrence: 3                       # Сколько раз повторялась
---

## Симптом
```
DishkaError: Cannot resolve CreateUserAction - HashPasswordTask not provided
```

## Причина
HashPasswordTask не зарегистрирован в Providers.py

## Решение
```python
class UserModuleProvider(Provider):
    scope = Scope.APP
    hash_password = provide(HashPasswordTask)  # ← Добавить
```

## Превентивные меры
- Всегда проверять зависимости Action при создании
- Использовать skill `debug-di` при ошибках DI

## Связанные ресурсы
- agent-os/troubleshooting/di-errors.md
- .cursor/skills/debug-di/SKILL.md
```

### Уровень 3: Experience (Опыт)

**Что хранит:** Успешные сессии, решения, оптимизации.

**Формат Session:**

```markdown
---
id: SESSION-2025-01-19-001
date: 2025-01-19
duration: 45min
task: Создание AuthModule с JWT аутентификацией
outcome: success                    # success | partial | failed
---

## Что сделано
1. Создан AuthModule с Actions: Login, Register, RefreshToken
2. Добавлены Guards для protected routes
3. Интегрированы события: UserLoggedIn, UserRegistered

## Ключевые решения
- JWT хранится в httponly cookie (не localStorage)
- Refresh token в отдельной таблице с device fingerprint

## Что сработало хорошо
- Skill `create-porto-module` ускорил создание структуры
- Template action.py.template избавил от бойлерплейта

## Что можно улучшить
- Добавить skill для auth-specific задач
```

### Уровень 4: Context (Контекст)

**Что хранит:** Текущее состояние проекта, активные задачи.

**Формат project-state.md:**

```markdown
---
updated: 2025-01-19T14:30:00
---

## Модули
| Модуль | Статус | Тесты | Последнее изменение |
|--------|--------|-------|---------------------|
| UserModule | stable | 95% | 2025-01-18 |
| AuthModule | active | 80% | 2025-01-19 |
| OrderModule | planned | 0% | - |

## Активные задачи
- [ ] #123: Добавить 2FA в AuthModule
- [ ] #124: Интеграция с платёжной системой

## Технический долг
- Рефакторинг UserRepository (созданы TODO)
- Обновить зависимости (Litestar 2.x)
```

### Интеграция с агентами

Агенты автоматически обращаются к памяти:

```yaml
# В промпте агента
При выполнении задачи:
1. Проверь agent-os/memory/learning/mistakes/ на похожие ошибки
2. Найди релевантные паттерны в agent-os/memory/knowledge/patterns/
3. После успешного выполнения — обнови agent-os/memory/context/
```

### Команды Memory System

| Команда | Описание |
|---------|----------|
| `/memory/save-mistake` | Сохранить ошибку с анализом |
| `/memory/save-pattern` | Сохранить новый паттерн |
| `/memory/save-decision` | Сохранить ADR |
| `/memory/search` | Поиск в памяти |
| `/memory/recall` | Загрузить релевантный контекст |
| `/memory/summarize` | Сжать и обобщить записи |

---

## Feedback Loop

Система сбора обратной связи для улучшения качества работы агента.

### Триггеры сбора

| Триггер | Когда срабатывает | Тип фидбека |
|---------|-------------------|-------------|
| **После Action** | Завершение любого Action | Быстрая оценка (1-5) |
| **После ошибки** | Агент допустил ошибку | Детальный анализ |
| **После сессии** | Завершение рабочей сессии | Обзор сессии |
| **Периодически** | Каждые N выполненных задач | Агрегированные метрики |
| **По запросу** | Команда `/feedback/collect` | Ручной сбор |

### Типы вопросов

**Quick Feedback (после action):**

```yaml
questions:
  - id: quality
    type: rating
    prompt: "Оцените качество выполнения (1-5)"
    scale: 1-5
  
  - id: issues
    type: multiselect
    prompt: "Были ли проблемы?"
    options:
      - "Неверная структура"
      - "Ошибки в коде"
      - "Неполная реализация"
      - "Лишний бойлерплейт"
      - "Нет проблем"
```

**Detailed Feedback (после ошибки):**

```yaml
questions:
  - id: error_type
    type: select
    prompt: "Тип ошибки"
    options:
      - "DI / Dependency Injection"
      - "Import / Module structure"
      - "Result handling"
      - "Database / Migration"
      - "Type errors"
      - "Logic error"
      - "Other"
  
  - id: root_cause
    type: text
    prompt: "Опишите корневую причину"
  
  - id: should_prevent
    type: boolean
    prompt: "Нужно добавить правило для предотвращения?"
```

### Метрики и аналитика

**Собираемые метрики:**

```yaml
metrics:
  success_rate:
    description: "Процент успешных выполнений"
    calculation: "successful_actions / total_actions"
    target: "> 95%"
  
  error_patterns:
    description: "Частота типов ошибок"
    dimensions:
      - error_type
      - module
      - time_period
  
  feedback_score:
    description: "Средняя оценка качества"
    calculation: "avg(quality_ratings)"
    target: "> 4.0"
  
  time_to_fix:
    description: "Время от ошибки до исправления"
    target: "< 5 min"
  
  learning_effectiveness:
    description: "Снижение повторных ошибок"
    calculation: "1 - (repeat_errors / first_time_errors)"
```

**Дашборд (agent-os/analytics/dashboard.md):**

```markdown
# Agent Performance Dashboard

## Последние 7 дней

| Метрика | Значение | Тренд | Цель |
|---------|----------|-------|------|
| Success Rate | 94.2% | ↑ 2.1% | > 95% |
| Avg. Rating | 4.3 | → 0.0 | > 4.0 |
| Errors Fixed | 12 | ↓ 3 | — |
| New Patterns | 3 | ↑ 1 | — |

## Топ ошибок (за неделю)
1. DI errors (5) — решение: автопроверка Providers.py
2. Import errors (3) — решение: обновлён skill
3. Result handling (2) — решение: добавлен чеклист
```

### Автоматические действия

На основе фидбека система автоматически:

| Триггер | Действие |
|---------|----------|
| Ошибка повторилась 3+ раз | Создать запись в `learning/mistakes/` |
| Низкая оценка skill | Добавить в очередь на улучшение |
| Новый успешный паттерн | Предложить добавить в `knowledge/patterns/` |
| Success rate < 90% | Уведомить и запустить анализ |

---

## Standards Evolution

Система автоматической эволюции стандартов на основе практики.

### Обнаружение паттернов

```
┌─────────────────────────────────────────────────────────────┐
│               PATTERN DETECTION PIPELINE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. COLLECT         2. ANALYZE          3. PROPOSE           │
│  ┌──────────┐       ┌──────────┐       ┌──────────┐         │
│  │ Код      │──────▶│ Частота  │──────▶│ Proposal │         │
│  │ Сессии   │       │ Качество │       │          │         │
│  │ Фидбек   │       │ Консист. │       │          │         │
│  └──────────┘       └──────────┘       └──────────┘         │
│                                              │               │
│                                              ▼               │
│                           4. APPROVE / REJECT                │
│                           ┌──────────────────┐               │
│                           │ Human review     │               │
│                           │ или auto-approve │               │
│                           └──────────────────┘               │
│                                              │               │
│                                              ▼               │
│                           5. INTEGRATE                       │
│                           ┌──────────────────┐               │
│                           │ Обновить         │               │
│                           │ standards/       │               │
│                           │ templates/       │               │
│                           └──────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Proposals и Approval

**Формат Proposal:**

```markdown
---
id: PROPOSAL-2025-01-19-001
type: new_pattern                   # new_pattern | update_standard | deprecate
status: pending                     # pending | approved | rejected
confidence: 0.87
evidence_count: 15
auto_approvable: true               # Если confidence > 0.9 и evidence > 10
---

## Предложение
Добавить паттерн "Validation Task" для выделения валидации в отдельный Task.

## Доказательства
- Использовано в 15 Actions
- Средняя оценка качества: 4.6
- Уменьшает дублирование на ~30%

## Предлагаемое изменение

### В standards/backend/validation.md добавить:
```python
class ValidateUserDataTask(SyncTask[UserData, ValidationResult]):
    def run(self, data: UserData) -> ValidationResult:
        errors = []
        if not data.email:
            errors.append("Email required")
        return ValidationResult(valid=len(errors) == 0, errors=errors)
```

### В templates/ добавить:
- `validation-task.py.template`

## Риски
- Низкий: может увеличить количество файлов
```

### Автоматический Approval

```yaml
auto_approval_rules:
  - condition: "confidence >= 0.9 AND evidence_count >= 10"
    action: auto_approve
    notify: true
  
  - condition: "confidence >= 0.8 AND evidence_count >= 20"
    action: auto_approve
    notify: true
  
  - condition: "type == 'deprecate'"
    action: require_human_review
  
  - condition: "affects_core_standards"
    action: require_human_review
```

### Автообновление примеров

При approval, система автоматически:

1. **Обновляет standards/** — добавляет/изменяет правила
2. **Обновляет templates/** — создаёт/обновляет шаблоны
3. **Обновляет skills/** — модифицирует SKILL.md
4. **Обновляет checklists/** — добавляет новые пункты
5. **Создаёт migration guide** — если breaking change

### Команды Standards Evolution

| Команда | Описание |
|---------|----------|
| `/standards/propose` | Предложить новый стандарт |
| `/standards/review` | Просмотреть pending proposals |
| `/standards/approve <id>` | Одобрить proposal |
| `/standards/reject <id>` | Отклонить proposal |
| `/standards/analyze` | Запустить анализ паттернов |

---

## Knowledge Integration

Система интеграции внешних источников знаний.

### Иерархия источников

```
┌─────────────────────────────────────────────────────────────┐
│                 KNOWLEDGE HIERARCHY                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Priority 1: PROJECT-SPECIFIC                                │
│  ├─ agent-os/standards/                                      │
│  ├─ agent-os/memory/knowledge/                               │
│  └─ docs/                                                    │
│                                                              │
│  Priority 2: LIBRARY DOCUMENTATION                           │
│  ├─ Context7 MCP (актуальные docs)                          │
│  ├─ foxdocs/ (локальные копии)                              │
│  └─ Official docs (web)                                      │
│                                                              │
│  Priority 3: RESEARCH & ARTICLES                             │
│  ├─ arXiv MCP (научные статьи)                              │
│  └─ Web Search (блоги, tutorials)                           │
│                                                              │
│  Priority 4: COMMUNITY KNOWLEDGE                             │
│  ├─ GitHub Issues/Discussions                                │
│  └─ StackOverflow                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### MCP интеграции

**Context7 — Актуальная документация библиотек:**

```yaml
# Использование
query: "Как использовать Litestar channels?"
source: context7
result:
  library: litestar
  version: 2.15.0
  content: |
    # Channels in Litestar
    Channels provide pub/sub functionality...
```

**arXiv — Научные статьи:**

```yaml
# Использование для исследования паттернов
query: "Railway Oriented Programming error handling"
source: arxiv
result:
  papers:
    - title: "Error Handling in Functional Languages"
      arxiv_id: "2301.12345"
      relevance: 0.89
```

**Web Search — Актуальные решения:**

```yaml
# Использование для поиска решений
query: "Litestar Dishka integration 2025"
source: web_search
result:
  sources:
    - url: "https://..."
      snippet: "..."
```

### Кэширование

```yaml
cache_config:
  context7:
    ttl: 7d                         # Документация обновляется редко
    storage: agent-os/cache/docs/
  
  arxiv:
    ttl: 30d                        # Статьи не меняются
    storage: agent-os/cache/research/
  
  web:
    ttl: 1d                         # Web контент актуален
    storage: agent-os/cache/web/
```

### Синтез знаний

Система объединяет знания из разных источников:

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Project    │   │   Library    │   │   Research   │
│   Standards  │   │     Docs     │   │   Articles   │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └─────────────┬────┴─────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │   SYNTHESIS    │
            │   ──────────   │
            │ Контекст проекта │
            │ + Best practices │
            │ + Latest APIs   │
            └────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ ACTIONABLE     │
            │ KNOWLEDGE      │
            └────────────────┘
```

**Пример синтеза:**

```markdown
# Вопрос: "Как реализовать WebSocket с аутентификацией?"

## Источники:
1. **Project standards** (agent-os/standards/):
   - Использовать JWT Guards
   - Events через UoW
   
2. **Litestar docs** (Context7):
   - WebSocket handlers syntax
   - on_accept, on_disconnect hooks
   
3. **Best practices** (web search):
   - Token validation в on_accept
   - Heartbeat для keepalive

## Синтезированный ответ:
[Конкретная реализация с учётом всех источников]
```

### Команды Knowledge Integration

| Команда | Описание |
|---------|----------|
| `/knowledge/search <query>` | Поиск по всем источникам |
| `/knowledge/docs <library>` | Получить docs библиотеки |
| `/knowledge/research <topic>` | Найти научные статьи |
| `/knowledge/sync` | Обновить локальный кэш |

---

## Training Mode

Режим активного обучения агента через симуляции и туториалы.

### Туториалы

**Интерактивные tutorials в agent-os/training/tutorials/:**

```markdown
# Tutorial: Создание Porto Module

## Уровень: Beginner
## Время: 15 минут
## Пререквизиты: Понимание Porto Pattern

---

## Шаг 1: Структура модуля

> Создайте базовую структуру для OrderModule

### Задание:
Создайте папки:
```
src/Containers/AppSection/OrderModule/
├── Actions/
├── Data/
├── Models/
├── UI/API/
├── Errors.py
└── Providers.py
```

### Проверка:
- [ ] Все папки созданы
- [ ] __init__.py в каждой папке

---

## Шаг 2: Модель Order
[...]
```

### Симуляции

**Сценарии для практики в agent-os/training/simulations/:**

```yaml
simulation:
  id: SIM-001
  name: "Debug DI Error"
  difficulty: medium
  
  setup:
    description: |
      Пользователь получает ошибку DI при вызове CreateOrderAction.
      Нужно найти и исправить проблему.
    
    files_to_create:
      - path: src/Containers/AppSection/OrderModule/Actions/CreateOrderAction.py
        content: |
          # Action с отсутствующей зависимостью
          @dataclass
          class CreateOrderAction(Action):
              validate_order: ValidateOrderTask  # Не зарегистрирован!
              ...
    
    error_to_show: |
      DishkaError: Cannot resolve CreateOrderAction - ValidateOrderTask not provided
  
  expected_solution:
    - Найти ValidateOrderTask
    - Добавить в Providers.py
    - Проверить работоспособность
  
  hints:
    - "Проверь Providers.py модуля"
    - "Skill debug-di может помочь"
    - "ValidateOrderTask должен быть в scope APP"
```

### Sandbox

Изолированная среда для экспериментов:

```yaml
sandbox:
  location: agent-os/training/sandbox/
  
  features:
    - Изолированная копия проекта
    - Можно ломать без последствий
    - Автоматический reset
    - Сравнение с эталоном
  
  use_cases:
    - Тестирование новых подходов
    - Эксперименты с архитектурой
    - Обучение на ошибках
```

### Tracking прогресса

```markdown
# agent-os/training/progress.md

## Общий прогресс

| Категория | Пройдено | Всего | Уровень |
|-----------|----------|-------|---------|
| Porto Basics | 5/5 | 100% | ⭐⭐⭐ Master |
| Result Handling | 3/4 | 75% | ⭐⭐ Advanced |
| DI & Providers | 2/3 | 67% | ⭐⭐ Advanced |
| Events & Listeners | 1/2 | 50% | ⭐ Intermediate |
| Testing | 0/3 | 0% | 🔒 Locked |

## Последние достижения
- ✅ 2025-01-19: Completed "Debug DI Error" simulation
- ✅ 2025-01-18: Completed "Create Action" tutorial
- ✅ 2025-01-17: Completed "Porto Structure" tutorial

## Рекомендации
- Пройти tutorial "Events & Listeners" для разблокировки Testing
- Повторить simulation "Result Handling Edge Cases"
```

### Команды Training Mode

| Команда | Описание |
|---------|----------|
| `/training/start <tutorial>` | Начать туториал |
| `/training/simulate <scenario>` | Запустить симуляцию |
| `/training/sandbox` | Открыть sandbox |
| `/training/progress` | Показать прогресс |
| `/training/recommend` | Рекомендации по обучению |

---

## Orchestrator

Единая точка входа для всех self-improving систем.

### Команда `/agent-os/ask`

**Главная команда для работы с AI-системой:**

```
/agent-os/ask [любой запрос на русском или английском]
```

**Примеры:**

```bash
# Разработка
/agent-os/ask создай action для регистрации пользователя
/agent-os/ask добавь endpoint для получения профиля

# Spec-Driven
/agent-os/ask новая фича — система уведомлений

# Исследование
/agent-os/ask как в litestar сделать middleware
/agent-os/ask документация piccolo миграций

# Отладка
/agent-os/ask ошибка dishka — dependency not provided

# Self-Improving
/agent-os/ask запомни: используем UUID v4
/agent-os/ask что я делал неправильно с импортами

# Обучение
/agent-os/ask научи меня Result pattern
```

**Преимущества `/ask`:**
- Не нужно знать конкретные команды
- Автоматический выбор нужного агента/skill
- Координация сложных мультишаговых задач
- Использование памяти для контекста

### Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│                  .cursor/agents/orchestrator.md                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT                                                           │
│  ├─ User request                                                 │
│  ├─ Error occurred                                               │
│  ├─ Task completed                                               │
│  └─ Scheduled trigger                                            │
│                                                                  │
│  ROUTING                                                         │
│  ├─ Анализ intent                                                │
│  ├─ Выбор системы/агента                                         │
│  ├─ Подготовка контекста                                         │
│  └─ Делегация                                                    │
│                                                                  │
│  COORDINATION                                                    │
│  ├─ Параллельный запуск агентов                                  │
│  ├─ Сбор результатов                                             │
│  ├─ Разрешение конфликтов                                        │
│  └─ Финальный ответ                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Роутинг к агентам

| Intent | Агент/Система | Действие |
|--------|---------------|----------|
| "Ошибка в коде" | `debug-*` skills | Диагностика и исправление |
| "Создай компонент" | `add-*` skills | Создание по шаблону |
| "Запомни это" | Memory System | Сохранение в память |
| "Что я делал вчера?" | Memory System | Recall из experience |
| "Как улучшить?" | Feedback Loop | Сбор и анализ |
| "Обнови стандарты" | Standards Evolution | Analyze + propose |
| "Найди в документации" | Knowledge Integration | Multi-source search |
| "Потренируй меня" | Training Mode | Tutorial/Simulation |

### Координация между системами

**Пример: Обработка ошибки**

```
1. USER: "Получаю ошибку DI при вызове CreateUserAction"
   
2. ORCHESTRATOR:
   ├─ [Memory] Поиск похожих ошибок
   ├─ [Knowledge] Получение docs по Dishka
   └─ [Skill] Активация debug-di
   
3. PARALLEL EXECUTION:
   ├─ Memory → Найдено 2 похожих случая
   ├─ Knowledge → Документация по provide()
   └─ Skill → Диагностика проблемы
   
4. SYNTHESIS:
   - Объединение результатов
   - Формирование решения
   
5. ACTION:
   - Исправление кода
   - [Feedback] Запрос оценки
   - [Memory] Сохранение, если новый паттерн
```

### Расписание автоматических задач

```yaml
scheduled_tasks:
  daily:
    - time: "00:00"
      task: "memory/compress-context"
      description: "Сжатие дневного контекста"
    
    - time: "23:00"
      task: "feedback/daily-summary"
      description: "Дневной отчёт по метрикам"
  
  weekly:
    - day: "sunday"
      task: "standards/analyze-patterns"
      description: "Анализ новых паттернов"
    
    - day: "sunday"
      task: "knowledge/sync-cache"
      description: "Обновление кэша знаний"
  
  on_event:
    - event: "error_occurred"
      task: "memory/save-mistake"
      condition: "severity >= medium"
    
    - event: "task_completed"
      task: "feedback/quick"
      condition: "task_type == 'implementation'"
```

---

## Subagents для Self-Improving

| Агент | Файл | Назначение |
|-------|------|------------|
| `orchestrator` | `.cursor/agents/orchestrator.md` | Единая точка входа, роутинг |
| `memory-manager` | `.cursor/agents/memory-manager.md` | Управление памятью, recall |
| `feedback-collector` | `.cursor/agents/feedback-collector.md` | Сбор и анализ фидбека |
| `standards-evolver` | `.cursor/agents/standards-evolver.md` | Эволюция стандартов |
| `knowledge-retriever` | `.cursor/agents/knowledge-retriever.md` | Интеграция внешних знаний |

### Примеры агентов

**orchestrator.md:**

```yaml
---
name: orchestrator
description: Единая точка входа для self-improving систем. Роутит запросы к нужным агентам.
model: inherit
---

Ты — Orchestrator для self-improving систем Hyper-Porto.

## Твоя роль
1. Анализировать входящие запросы
2. Определять какая система/агент нужна
3. Координировать параллельное выполнение
4. Синтезировать результаты

## Доступные системы
- Memory System: agent-os/memory/
- Feedback Loop: agent-os/analytics/
- Standards Evolution: agent-os/standards/
- Knowledge Integration: MCP (Context7, arXiv, Web)
- Training Mode: agent-os/training/

## Workflow
[детальное описание]
```

**memory-manager.md:**

```yaml
---
name: memory-manager
description: Управляет многоуровневой памятью. Сохранение, поиск, recall.
model: inherit
---

Ты — Memory Manager для Hyper-Porto.

## Твоя роль
1. Сохранять новые записи в правильный уровень памяти
2. Искать релевантные записи по запросу
3. Сжимать и обобщать старые записи
4. Обновлять контекст проекта

## Структура памяти
- knowledge/ — ADR, Patterns
- learning/ — Mistakes, Anti-patterns
- experience/ — Sessions, Solutions
- context/ — Current state

## Форматы записей
[шаблоны для каждого типа]
```

---

## Команды (Сводная таблица)

### Memory System

| Команда | Описание |
|---------|----------|
| `/memory/save-mistake` | Сохранить ошибку с анализом |
| `/memory/save-pattern` | Сохранить новый паттерн |
| `/memory/save-decision` | Сохранить ADR |
| `/memory/search <query>` | Поиск в памяти |
| `/memory/recall` | Загрузить релевантный контекст |
| `/memory/summarize` | Сжать записи |

### Feedback Loop

| Команда | Описание |
|---------|----------|
| `/feedback/collect` | Ручной сбор фидбека |
| `/feedback/dashboard` | Показать метрики |
| `/feedback/analyze` | Анализ трендов |

### Standards Evolution

| Команда | Описание |
|---------|----------|
| `/standards/propose` | Предложить стандарт |
| `/standards/review` | Просмотр proposals |
| `/standards/approve <id>` | Одобрить |
| `/standards/reject <id>` | Отклонить |
| `/standards/analyze` | Анализ паттернов |

### Knowledge Integration

| Команда | Описание |
|---------|----------|
| `/knowledge/search <query>` | Поиск по источникам |
| `/knowledge/docs <library>` | Docs библиотеки |
| `/knowledge/research <topic>` | Научные статьи |
| `/knowledge/sync` | Обновить кэш |

### Training Mode

| Команда | Описание |
|---------|----------|
| `/training/start <tutorial>` | Начать туториал |
| `/training/simulate <scenario>` | Симуляция |
| `/training/sandbox` | Sandbox |
| `/training/progress` | Прогресс |
| `/training/recommend` | Рекомендации |

---

## Интеграция с Agent OS

```
┌─────────────────────────────────────────────────────────────────┐
│                         AGENT OS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EXISTING                          NEW (Self-Improving)         │
│  ─────────                         ────────────────────         │
│  ├─ specs/                         ├─ memory/                   │
│  ├─ standards/                     │   ├─ knowledge/            │
│  ├─ templates/                     │   ├─ learning/             │
│  ├─ checklists/                    │   ├─ experience/           │
│  ├─ troubleshooting/               │   └─ context/              │
│  ├─ workflows/                     │                            │
│  └─ commands/                      ├─ analytics/                │
│                                    │   ├─ metrics.yaml          │
│                                    │   └─ dashboard.md          │
│                                    │                            │
│                                    ├─ training/                 │
│                                    │   ├─ tutorials/            │
│                                    │   ├─ simulations/          │
│                                    │   ├─ sandbox/              │
│                                    │   └─ progress.md           │
│                                    │                            │
│                                    ├─ proposals/                │
│                                    │   └─ pending/              │
│                                    │                            │
│                                    └─ cache/                    │
│                                        ├─ docs/                 │
│                                        ├─ research/             │
│                                        └─ web/                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### Memory System

1. **Не перегружай память** — храни только ценное
2. **Регулярная компрессия** — сжимай старые записи
3. **Правильный уровень** — ошибки в learning, решения в experience
4. **Связывай записи** — используй related fields

### Feedback Loop

1. **Не злоупотребляй** — не спрашивай слишком часто
2. **Конкретные вопросы** — избегай размытых формулировок
3. **Действуй на данных** — фидбек бесполезен без action

### Standards Evolution

1. **Высокий порог** — не добавляй каждый паттерн
2. **Evidence-based** — только с доказательствами
3. **Backward compatibility** — не ломай существующий код

### Knowledge Integration

1. **Project-first** — сначала локальные стандарты
2. **Верифицируй** — внешние источники могут устареть
3. **Кэшируй** — не делай лишних запросов

### Training Mode

1. **Практика важнее теории** — симуляции эффективнее tutorials
2. **Инкрементальность** — от простого к сложному
3. **Регулярность** — лучше по 10 минут ежедневно

---

## См. также

- [23-cursor-ai-components.md](23-cursor-ai-components.md) — Rules, Skills, Subagents, Commands
- [07-spec-driven.md](07-spec-driven.md) — Spec-Driven Development
- [04-result-railway.md](04-result-railway.md) — Error handling patterns
- [CLAUDE.md](../CLAUDE.md) — Quick Reference для AI
