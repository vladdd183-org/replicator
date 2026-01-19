# 23. Cursor AI Components — Rules, Skills, Subagents, Commands

> Архитектура компонентов Cursor AI для автоматизации разработки в Hyper-Porto.

---

## Обзор компонентов

Cursor AI использует несколько типов компонентов для управления поведением агента:

| Компонент | Расположение | Когда активируется | Изоляция | Назначение |
|-----------|--------------|-------------------|----------|------------|
| **Rules** | `.cursor/rules/*.mdc` | Автоматически | Нет | Стандарты, архитектура |
| **Skills** | `.cursor/skills/*/SKILL.md` | По триггерам | Нет | Специфичные задачи |
| **Subagents** | `.cursor/agents/*.md` | Через Task tool | Да | Комплексные задачи |
| **Commands** | `.cursor/commands/*/*.md` | `/команда` | Нет | Ярлыки для workflow |

---

## 1. Rules (Правила)

**Путь:** `.cursor/rules/*.mdc`

**Что это:** Постоянный контекст, который загружается в системный промпт агента.

### Формат файла

```yaml
---
description: Описание правила
globs: **/*.py        # Опционально: паттерн файлов
alwaysApply: true     # Или false для условных правил
---

# Содержимое правила в Markdown
```

### Конфигурации

| Поле | Тип | Описание |
|------|-----|----------|
| `description` | string | Описание для выбора правил |
| `globs` | string | Паттерн файлов — правило активно при работе с ними |
| `alwaysApply` | boolean | `true` — всегда активно |

### Примеры

**Всегда активное правило:**
```yaml
---
description: Core coding standards for Hyper-Porto
alwaysApply: true
---

# Архитектурные правила
- Все импорты абсолютные от `src.`
- Actions возвращают `Result[T, E]`
```

**Условное правило для Python:**
```yaml
---
description: Python-specific conventions
globs: **/*.py
alwaysApply: false
---

# Python Conventions
- Type hints обязательны
- Docstrings в Google формате
```

### Наш главный Rule

Файл `.cursor/rules/fsad.mdc` содержит всю архитектуру Hyper-Porto:
- Структура Porto Pattern
- Обязательные правила (импорты, Result, DTO)
- Именование компонентов
- Tech stack

---

## 2. Skills (Скиллы)

**Путь:** `.cursor/skills/<skill-name>/SKILL.md`

**Что это:** "Thin interface" файлы, которые направляют агента к детальным инструкциям в `agent-os/`.

### Архитектура Skills

```
┌────────────────────────────────────────────────────────────┐
│  .cursor/skills/add-action/SKILL.md                        │
│  ├─ frontmatter (name, description + триггеры)             │
│  ├─ Quick Reference (краткая таблица)                      │
│  └─ Источники → agent-os/commands/add-action.md            │
│                → agent-os/templates/action.py.template     │
│                → agent-os/checklists/action-implementation │
└────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────┐
│  agent-os/ — Single Source of Truth                        │
│  ├─ commands/     → Полные инструкции                      │
│  ├─ templates/    → Шаблоны кода                           │
│  ├─ checklists/   → Чеклисты                               │
│  └─ standards/    → Стандарты                              │
└────────────────────────────────────────────────────────────┘
```

### Формат SKILL.md (Thin Interface)

```yaml
---
name: skill-name                    # Уникальный идентификатор (a-z, 0-9, -)
description: Описание + триггеры    # Критически важно для активации
---

# Название скилла

## Quick Reference
| Что | Где |
|-----|-----|
| Input | ... |
| Output | ... |

## Источники
- **Инструкция:** `agent-os/commands/...`
- **Template:** `agent-os/templates/...`
- **Checklist:** `agent-os/checklists/...`

## Действие
1. Загрузи инструкцию из `agent-os/commands/...`
2. Следуй шагам...
```

### Локации скиллов

| Тип | Путь | Скоуп |
|-----|------|-------|
| Персональные | `~/.cursor/skills/` | Все проекты пользователя |
| Проектные | `.cursor/skills/` | Только текущий проект |

### Связь с Agent OS

Skills — "thin interface", детальные инструкции в `agent-os/`:

| SKILL.md секция | Ссылается на |
|-----------------|--------------|
| Инструкция | `agent-os/commands/<name>.md` |
| Template | `agent-os/templates/<name>.py.template` |
| Checklist | `agent-os/checklists/<name>.md` |
| Standards | `agent-os/standards/` |

### Правила description

Description определяет КОГДА скилл активируется:

```yaml
# ❌ Плохо — слишком общее
description: Помогает с кодом

# ✅ Хорошо — конкретные триггеры
description: Create new Action (Use Case) for Hyper-Porto architecture. 
  Use when the user wants to add action, create use case, new action, 
  добавить action, новый use case, создать action.
```

### Наши скиллы

| Скилл | Триггеры | Назначение |
|-------|----------|------------|
| **Создание компонентов** | | |
| `add-action` | "создай action", "add action" | Создание Action (Use Case) |
| `add-task` | "создай task", "новый таск" | Создание Task (атомарная операция) |
| `add-query` | "создай query", "cqrs read" | Создание Query (CQRS Read) |
| `add-endpoint` | "добавь endpoint", "new api" | Создание HTTP endpoint |
| `add-event` | "создай event", "домен событие" | Domain Event + Listener |
| `add-graphql` | "добавь graphql", "strawberry" | GraphQL Types/Resolvers |
| `add-websocket` | "добавь websocket", "реалтайм" | WebSocket handlers |
| `add-worker` | "добавь воркер", "фоновая задача" | TaskIQ background tasks |
| **Модули** | | |
| `create-porto-module` | "создай модуль", "new container" | Новый Porto Container |
| `extract-module` | "выдели модуль", "микросервис" | Вынос в микросервис |
| **Миграции** | | |
| `piccolo-migration` | "миграция", "добавить поле" | Создание миграций Piccolo |
| `debug-migration` | "миграция не работает" | Отладка миграций |
| **Тестирование** | | |
| `setup-tests` | "настроить тесты", "pytest" | Настройка pytest |
| **Отладка** | | |
| `debug-result` | "не работает result" | Отладка Result[T, E] |
| `debug-di` | "ошибка dishka", "di не работает" | Отладка DI |
| **Code Review** | | |
| `review-porto` | "проверь код", "code review" | Code review архитектуры |

---

## 3. Subagents (Сабагенты)

**Путь:** `.cursor/agents/*.md`

**Что это:** Специализированные AI-агенты с кастомным системным промптом, запускаемые в изолированном контексте.

### Формат файла

```yaml
---
name: agent-name              # Уникальный идентификатор
description: Когда использовать этого агента
model: inherit                # inherit | fast | default
---

Системный промпт агента...

Ты эксперт в X. При вызове:
1. Делай A
2. Делай B
3. Возвращай результат
```

### Ключевое отличие от Skills

| Аспект | Skills | Subagents |
|--------|--------|-----------|
| Контекст | В текущем чате | Изолированный |
| Запуск | Автоматически | Через Task tool |
| История | Видит всю историю | Только переданный prompt |
| Результат | Продолжает диалог | Возвращает ответ |

### Наши сабагенты (Agent OS)

```
.cursor/agents/
├── spec-initializer.md      # Инициализация спецификации
├── spec-shaper.md           # Сбор требований
├── spec-writer.md           # Написание spec.md
├── spec-verifier.md         # Верификация спеков
├── tasks-list-creator.md    # Создание tasks.md
├── implementer.md           # Имплементация задач
├── implementation-verifier.md # Проверка имплементации
├── product-planner.md       # Планирование продукта
├── project-analyzer.md      # Анализ проекта
│
│   # Self-Improving Agents
├── orchestrator.md          # Единая точка входа для self-improving систем
├── memory-manager.md        # Управление многоуровневой памятью
├── feedback-collector.md    # Сбор и анализ обратной связи
├── standards-evolver.md     # Эволюция стандартов на основе практики
└── knowledge-retriever.md   # Интеграция внешних знаний
```

### Self-Improving Agents (подробно)

| Агент | Описание | Когда использовать |
|-------|----------|-------------------|
| `orchestrator` | Единая точка входа, роутинг к системам | Автоматически при любом запросе |
| `memory-manager` | Сохранение/поиск в памяти (ADR, Mistakes, Patterns) | При ошибках, решениях, паттернах |
| `feedback-collector` | Сбор оценок, анализ метрик | После tasks, по расписанию |
| `standards-evolver` | Обнаружение паттернов, proposals | При повторяющихся паттернах |
| `knowledge-retriever` | Поиск по docs, arXiv, web | При необходимости внешних знаний |

### Пример: implementer

```yaml
---
name: implementer
description: Use proactively to implement a feature by following tasks.md
model: inherit
---

You are a full stack software developer...
Your role is to implement tasks from tasks.md, spec.md.

## Implementation process:
1. Analyze spec.md and requirements.md
2. Analyze patterns in codebase
3. Implement the assigned task group
4. Update tasks.md to mark tasks as done
```

### Когда использовать Subagent vs Skill

**Используй Skill когда:**
- Задача простая и атомарная
- Нужен доступ к истории диалога
- Результат сразу в чат

**Используй Subagent когда:**
- Комплексная многошаговая задача
- Нужна изоляция контекста
- Параллельное выполнение нескольких задач

---

## 4. Commands (Команды)

**Путь:** `.cursor/commands/<category>/<command>.md`

**Что это:** Слэш-команды для быстрого запуска workflow.

### Формат использования

```
/команда [аргументы]
```

### Наши команды

#### Development (`/dev/`)

| Команда | Описание |
|---------|----------|
| `/dev/guide` | Интерактивный гайд |
| `/dev/slang` | Словарь сленга |
| **Создание компонентов** | |
| `/dev/create-module` | Создать Porto Container |
| `/dev/add-action` | Создать Action (Use Case) |
| `/dev/add-task` | Создать Task (атомарная операция) |
| `/dev/add-query` | Создать Query (CQRS Read) |
| `/dev/add-endpoint` | Добавить HTTP endpoint |
| `/dev/add-event` | Создать Domain Event + Listener |
| `/dev/add-graphql` | Создать GraphQL Types/Resolvers |
| `/dev/add-ws` | Создать WebSocket handler |
| `/dev/add-worker` | Создать Background Worker |
| `/dev/generate-crud` | Полный CRUD для сущности |
| **Утилиты** | |
| `/dev/migrate` | Piccolo миграции |
| `/dev/test` | Запуск тестов |
| `/dev/validate` | Валидация кода |

#### Agent OS (`/agent-os/`)

| Команда | Описание |
|---------|----------|
| **Единая точка входа** | |
| `/agent-os/ask [запрос]` | 🎯 **Главная команда** — принимает любой запрос, автоматически роутит к нужному агенту |
| **Spec-Driven Workflow** | |
| `/agent-os/analyze-project` | Анализ проекта |
| `/agent-os/plan-product` | Планирование продукта |
| `/agent-os/shape-spec` | Сбор требований |
| `/agent-os/write-spec` | Написание спецификации |
| `/agent-os/create-tasks` | Создание списка задач |
| `/agent-os/implement-tasks` | Запуск имплементации |
| `/agent-os/write-tests` | Написание тестов |

#### Примеры `/agent-os/ask`

```bash
/agent-os/ask создай action для регистрации пользователя
/agent-os/ask как в litestar сделать middleware
/agent-os/ask новая фича — система уведомлений
/agent-os/ask ошибка dishka — dependency not provided
/agent-os/ask научи меня Result pattern
```

#### Self-Improving (`/memory/`, `/feedback/`, `/standards/`, `/knowledge/`, `/training/`)

| Команда | Описание |
|---------|----------|
| **Memory System** | |
| `/memory/save-mistake` | Сохранить ошибку с анализом |
| `/memory/save-pattern` | Сохранить новый паттерн |
| `/memory/save-decision` | Сохранить ADR (Architecture Decision) |
| `/memory/search <query>` | Поиск в памяти |
| `/memory/recall` | Загрузить релевантный контекст |
| `/memory/summarize` | Сжать и обобщить записи |
| **Feedback Loop** | |
| `/feedback/collect` | Ручной сбор обратной связи |
| `/feedback/dashboard` | Показать метрики и аналитику |
| `/feedback/analyze` | Анализ трендов |
| **Standards Evolution** | |
| `/standards/propose` | Предложить новый стандарт/паттерн |
| `/standards/review` | Просмотреть pending proposals |
| `/standards/approve <id>` | Одобрить proposal |
| `/standards/reject <id>` | Отклонить proposal |
| `/standards/analyze` | Запустить анализ паттернов |
| **Knowledge Integration** | |
| `/knowledge/search <query>` | Поиск по всем источникам |
| `/knowledge/docs <library>` | Получить docs библиотеки (Context7) |
| `/knowledge/research <topic>` | Найти научные статьи (arXiv) |
| `/knowledge/sync` | Обновить локальный кэш |
| **Training Mode** | |
| `/training/start <tutorial>` | Начать туториал |
| `/training/simulate <scenario>` | Запустить симуляцию |
| `/training/sandbox` | Открыть sandbox |
| `/training/progress` | Показать прогресс обучения |
| `/training/recommend` | Получить рекомендации |

### Пример команды

```markdown
# /add-action — Создание Action

## Синтаксис
/add-action <ActionName> [в <Module>] [с событием <EventName>]

## Примеры
/add-action ActivateUser в UserModule
/add-action ApproveOrder в OrderModule с событием OrderApproved

## Действие
1. Загрузи инструкцию из `agent-os/commands/add-action.md`
2. Используй template из `agent-os/templates/action.py.template`
3. Создай Action, Event, Listener
4. Зарегистрируй в Providers.py
```

---

## 5. Agent OS — Система оркестрации

**Путь:** `agent-os/`

**Что это:** Кастомная система для Spec-Driven Development.

### Структура

```
agent-os/
├── specs/                    # Спецификации фич
│   └── [feature-name]/
│       ├── planning/
│       │   ├── requirements.md   # Требования от spec-shaper
│       │   └── visuals/          # Mockups, screenshots
│       ├── spec.md               # Спецификация от spec-writer
│       ├── tasks.md              # Задачи от tasks-list-creator
│       ├── orchestration.yml     # Распределение по агентам
│       └── verification/
│           └── screenshots/      # Скриншоты тестирования
│
├── standards/                # Стандарты кодирования
│   ├── backend/
│   │   ├── api.md
│   │   ├── migrations.md
│   │   ├── models.md
│   │   └── queries.md
│   ├── frontend/
│   │   ├── accessibility.md
│   │   ├── components.md
│   │   ├── css.md
│   │   └── responsive.md
│   ├── global/
│   │   ├── coding-style.md
│   │   ├── commenting.md
│   │   ├── conventions.md
│   │   ├── error-handling.md
│   │   ├── tech-stack.md
│   │   └── validation.md
│   └── testing/
│       └── test-writing.md
│
├── templates/                # Шаблоны кода
│   ├── action.py.template
│   ├── task.py.template
│   ├── query.py.template
│   ├── controller.py.template
│   └── ...
│
├── checklists/               # Чеклисты
│   ├── action-implementation.md
│   ├── module-creation.md
│   └── ...
│
├── troubleshooting/          # Гайды по отладке
│   ├── di-errors.md
│   ├── result-errors.md
│   ├── migration-errors.md
│   └── ...
│
├── workflows/                # Пошаговые workflow
│   ├── add-api-endpoint.md
│   └── ...
│
└── commands/                 # Инструкции для команд
    ├── add-action.md
    ├── add-task.md
    ├── add-query.md
    ├── add-endpoint.md
    ├── add-event.md
    ├── add-graphql.md
    ├── add-websocket.md
    ├── add-worker.md
    ├── create-module.md
    └── ...
```

### Workflow разработки фичи

```
┌─────────────────────────────────────────────────────────────┐
│  1. /shape-spec                                             │
│     └─ spec-shaper → requirements.md                        │
├─────────────────────────────────────────────────────────────┤
│  2. /write-spec                                             │
│     └─ spec-writer → spec.md                                │
├─────────────────────────────────────────────────────────────┤
│  3. /create-tasks                                           │
│     └─ tasks-list-creator → tasks.md                        │
├─────────────────────────────────────────────────────────────┤
│  4. /orchestrate-tasks                                      │
│     └─ orchestration.yml + распределение по агентам         │
├─────────────────────────────────────────────────────────────┤
│  5. implementer (для каждой task group)                     │
│     └─ Имплементация + отметка выполненных задач            │
├─────────────────────────────────────────────────────────────┤
│  6. implementation-verifier                                 │
│     └─ Проверка результата                                  │
└─────────────────────────────────────────────────────────────┘
```

### orchestration.yml

```yaml
task_groups:
  - name: authentication-system
    claude_code_subagent: implementer
    standards:
      - all
  - name: user-dashboard
    claude_code_subagent: implementer
    standards:
      - global/*
      - frontend/components.md
      - frontend/css.md
  - name: api-endpoints
    claude_code_subagent: implementer
    standards:
      - backend/*
      - global/error-handling.md
```

---

## Взаимодействие компонентов

```
┌─────────────────────────────────────────────────────────────────┐
│                      CURSOR AI AGENT                            │
├─────────────────────────────────────────────────────────────────┤
│  RULES (.cursor/rules/)                                         │
│  ├─ alwaysApply: true → ВСЕГДА в контексте                     │
│  └─ globs: **/*.py → При работе с Python файлами               │
├─────────────────────────────────────────────────────────────────┤
│  SKILLS (.cursor/skills/) — Thin Interface                      │
│  └─ Активируются по триггерам в description                     │
│     "создай action" → читает add-action/SKILL.md               │
│     SKILL.md ссылается → agent-os/commands/add-action.md       │
├─────────────────────────────────────────────────────────────────┤
│  COMMANDS (.cursor/commands/)                                   │
│  ├─ /dev/* → Ссылаются на agent-os/commands/*                  │
│  └─ /agent-os/* → Spec-Driven workflow                         │
├─────────────────────────────────────────────────────────────────┤
│  SUBAGENTS (.cursor/agents/)                                    │
│  └─ Task tool → запуск изолированного агента                   │
│     spec-writer, implementer, verifier                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              AGENT OS — Single Source of Truth                  │
├─────────────────────────────────────────────────────────────────┤
│  agent-os/commands/          ← Полные инструкции               │
│  agent-os/templates/         ← Шаблоны кода                    │
│  agent-os/checklists/        ← Чеклисты                        │
│  agent-os/standards/         ← Стандарты                       │
│  agent-os/troubleshooting/   ← Отладка                         │
│  agent-os/workflows/         ← Пошаговые процессы              │
├─────────────────────────────────────────────────────────────────┤
│  agent-os/specs/[feature]/   ← Spec-Driven артефакты           │
│  ├─ requirements.md          ← spec-shaper создаёт             │
│  ├─ spec.md                  ← spec-writer создаёт             │
│  ├─ tasks.md                 ← tasks-list-creator создаёт      │
│  └─ orchestration.yml        ← /orchestrate-tasks создаёт      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### Rules

1. Держи правила краткими (до 50 строк на правило)
2. Одно правило — одна тема
3. Используй конкретные примеры кода

### Skills (Thin Interface)

1. Description — критически важен для обнаружения
2. SKILL.md до 100 строк — "thin interface" со ссылками на `agent-os/`
3. Включай триггерные слова на разных языках (рус + eng)
4. Детальные инструкции храни в `agent-os/commands/`
5. Templates — в `agent-os/templates/`

### Subagents

1. Один агент — одна специализация
2. "Use proactively" в description для автозапуска
3. Ссылайся на standards в промпте

### Commands

1. Понятный синтаксис с примерами
2. Ссылки на templates и checklists
3. Документируй каждый шаг

---

## Чеклист: создание нового компонента

### Новый Skill (Thin Interface)

```markdown
- [ ] Создать детальную инструкцию в `agent-os/commands/<name>.md`
- [ ] Создать template в `agent-os/templates/<name>.py.template` (опционально)
- [ ] Создать checklist в `agent-os/checklists/<name>.md` (опционально)
- [ ] Создать `.cursor/skills/<name>/SKILL.md` как thin interface:
      - frontmatter (name, description с триггерами)
      - Quick Reference таблица
      - Секция "Источники" со ссылками на agent-os/
      - Краткие шаги в секции "Действие"
- [ ] Skill до 100 строк — детали в agent-os/
```

### Новый Subagent

```markdown
- [ ] Создать `.cursor/agents/<name>.md`
- [ ] Заполнить frontmatter (name, description, model)
- [ ] Написать системный промпт
- [ ] Указать workflow/checklist
- [ ] Добавить ссылки на @standards
```

### Новая Command

```markdown
- [ ] Создать `.cursor/commands/<category>/<name>.md`
- [ ] Описать синтаксис и примеры
- [ ] Указать источники (templates, checklists)
- [ ] Описать шаги выполнения
```

---

## См. также

- [02-project-structure.md](02-project-structure.md) — Структура проекта
- [07-spec-driven.md](07-spec-driven.md) — Spec-Driven Development
- [24-self-improving-systems.md](24-self-improving-systems.md) — **Memory, Feedback, Standards Evolution, Training**
- [CLAUDE.md](../CLAUDE.md) — Quick Reference для AI
