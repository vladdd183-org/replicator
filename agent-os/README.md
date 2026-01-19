# 🤖 Agent OS — AI Development Standards

> Стандарты, шаблоны и инструкции для AI-assisted разработки в Hyper-Porto проекте.

**Версия:** 4.2.0  
**Проект:** Hyper-Porto v4.0  
**Дата:** 2026-01-19

---

## 🚀 Быстрый старт

### 🎯 Единая точка входа (рекомендуется)

```
/agent-os/ask [любой запрос]   — Главная команда, понимает естественный язык
```

**Примеры:**
```bash
/agent-os/ask создай action для регистрации
/agent-os/ask как в litestar сделать middleware
/agent-os/ask новая фича — система уведомлений
/agent-os/ask ошибка dishka — dependency not provided
/agent-os/ask научи меня Result pattern
```

Orchestrator автоматически:
- Анализирует ваш запрос
- Выбирает нужный агент или skill
- Координирует мультишаговые задачи
- Использует память для контекста

---

### Spec-Driven Development

```
agent-os/plan-product        — 📋 Планирование продукта (mission, roadmap)
agent-os/shape-spec          — 🔍 Сбор требований для фичи
agent-os/write-spec          — 📝 Написание спецификации
agent-os/create-tasks        — ✅ Создание списка задач
agent-os/implement-tasks     — 🚀 Реализация (простой режим)
agent-os/orchestrate-tasks   — 🎭 Реализация (с subagents)
```

### Ресерч

```
agent-os/research            — 📚 Комплексный ресерч (все источники)
agent-os/research-codebase   — 🔍 Ресерч в существующем коде
agent-os/research-online     — 🌐 Ресерч онлайн (документация, статьи)
```

### Быстрые команды разработки

```
dev/guide                    — 📖 Интерактивный гайд
dev/slang                    — 🗣️ Словарь сленга
dev/create-module            — 📦 Создать Container
dev/add-action               — ⚡ Создать Action
dev/add-endpoint             — 🔌 Добавить REST endpoint
dev/generate-crud            — 🔄 Генерация полного CRUD
```

### 🧠 Self-Improving Systems

```
/memory search <query>       — 🔍 Поиск в памяти агента
/memory add <knowledge>      — ➕ Добавить знание в память
/feedback collect            — 📊 Собрать обратную связь
/feedback stats              — 📈 Статистика и метрики
/standards evolve            — 🔄 Запустить эволюцию стандартов
/standards proposals         — 📋 Просмотреть предложения изменений
/knowledge search <topic>    — 🔎 Поиск по всем источникам знаний
/knowledge litestar          — 📚 Документация Litestar
/training start              — 🎓 Начать обучение
/training tutorial <name>    — 📖 Запустить туториал
```

---

## 📁 Структура

```
agent-os/
├── README.md                    # Этот файл
├── config.yml                   # Конфигурация Agent OS
├── glossary.md                  # Словарь терминов
│
├── specs/                       # 📋 Спецификации фич
│   └── YYYY-MM-DD-feature/      # Папка спецификации
│       ├── spec.md              # Формальная спецификация
│       ├── tasks.md             # Список задач
│       └── planning/            # Требования и визуалы
│
├── standards/                   # 📏 Стандарты кода
│   ├── architecture/            # Архитектурные решения
│   ├── backend/                 # Backend стандарты
│   ├── global/                  # Общие стандарты
│   ├── testing/                 # Тестирование
│   └── evolution/               # 🔄 Эволюция стандартов 🆕
│       ├── config.yml           # Настройки эволюции
│       └── README.md            # Документация
│
├── templates/                   # 📦 Шаблоны кода
│   ├── action.py.template
│   ├── task.py.template
│   ├── controller.py.template
│   ├── repository.py.template
│   └── ... (16 шаблонов)
│
├── workflows/                   # 📋 Пошаговые инструкции
│   ├── create-module.md
│   ├── add-api-endpoint.md
│   └── add-domain-event.md
│
├── checklists/                  # ✅ Чеклисты
│   ├── new-module.md
│   ├── code-review.md
│   └── action-implementation.md
│
├── troubleshooting/             # 🔧 Решение проблем
│   ├── di-errors.md
│   ├── result-errors.md
│   └── import-errors.md
│
├── snippets/                    # 🧩 Готовые паттерны кода
│   ├── result-patterns.md
│   ├── uow-patterns.md
│   ├── validation-patterns.md
│   └── query-patterns.md
│
├── anti-patterns/               # 🚫 Чего НЕ делать
│   ├── common-mistakes.md
│   └── bad-async.md
│
├── slang/                       # 🗣️ Словарь сленга
│   └── dictionary.md            # 📖 Можно дополнять!
│
├── commands/                    # 🎮 Справочные команды
│   ├── guide.md
│   ├── slang.md
│   └── ...
│
│── ─────────────────────────────  # 🧠 SELF-IMPROVING SYSTEMS
│
├── memory/                      # 🧠 Персистентная память 🆕
│   ├── README.md                # Документация системы
│   ├── index.json               # Индекс памяти
│   ├── _meta/                   # Метаданные
│   │   ├── schema.yml           # Схема памяти
│   │   ├── index.json           # Индекс
│   │   └── stats.json           # Статистика
│   ├── knowledge/               # Накопленные знания
│   │   ├── architecture/        # Архитектурные паттерны
│   │   ├── domain/              # Доменные знания
│   │   └── patterns/            # Паттерны кода
│   ├── learning/                # Обучение на ошибках
│   │   └── mistakes/            # Документированные ошибки
│   │       └── by-category/     # По категориям (DI, imports, result)
│   └── context/                 # Контекст проекта
│       ├── project/             # Информация о проекте
│       └── user/                # Предпочтения пользователя
│
├── feedback/                    # 📊 Система обратной связи 🆕
│   ├── README.md                # Документация
│   ├── config.yml               # Настройки
│   ├── collection/              # Сбор фидбека
│   │   └── triggers.yml         # Триггеры сбора
│   └── metrics/                 # Метрики
│       ├── current.json         # Текущие метрики
│       └── dashboards/          # Дашборды
│
├── knowledge/                   # 📚 Интеграция знаний 🆕
│   ├── README.md                # Документация
│   ├── config.yml               # Настройки источников
│   └── sources/                 # Конфигурация источников
│       └── libraries.yml        # Библиотеки (Litestar, Piccolo, ...)
│
└── training/                    # 🎓 Режим обучения 🆕
    ├── README.md                # Документация
    ├── tutorials/               # Туториалы
    │   ├── 01-getting-started.md
    │   ├── 02-create-action.md
    │   └── 03-result-pattern.md
    └── sandbox/                 # Песочница для экспериментов
```

---

## 🎯 Workflow: От идеи до кода

```
┌─────────────────────────────────────────────────────────────┐
│  1. ПЛАНИРОВАНИЕ                                             │
│     agent-os/plan-product → mission.md, roadmap.md           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. РЕСЕРЧ (опционально)                                     │
│     agent-os/research → research.md                          │
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

---

## 📂 Где создаются файлы

### Спецификации → `agent-os/specs/`

```
agent-os/specs/2026-01-18-user-management/
├── planning/
│   ├── requirements.md      # Собранные требования
│   ├── research.md          # Результаты ресерча
│   └── visuals/             # Макеты, скриншоты
├── implementation/          # Отчёты реализации
├── verifications/           # Верификация
├── spec.md                  # Спецификация
├── tasks.md                 # Задачи
└── orchestration.yml        # Настройки оркестрации
```

### Код → `src/Containers/`

```
src/Containers/AppSection/UserModule/
├── Actions/
├── Tasks/
├── Queries/
├── Data/
├── Models/
├── UI/
├── Events.py
├── Errors.py
└── Providers.py
```

### Продукт → `agent-os/product/`

```
agent-os/product/
├── mission.md               # Видение продукта
├── roadmap.md               # Фазы разработки
└── tech-stack.md            # Технологический стек
```

---

## 🔍 Команды ресерча

| Команда | Где ищет | Когда использовать |
|---------|----------|-------------------|
| `agent-os/research` | Везде | Комплексный ресерч перед фичей |
| `agent-os/research-codebase` | `src/`, `foxdocs/` | Найти примеры в существующем коде |
| `agent-os/research-online` | Web, Context7, arXiv | Документация, best practices |

### Примеры

```bash
# Найти как реализованы Actions в проекте
agent-os/research-codebase Actions

# Найти документацию по Litestar middleware
agent-os/research-online Litestar middleware

# Полный ресерч перед реализацией WebSocket
agent-os/research WebSocket handlers
```

---

## 🗣️ Словарь сленга

Agent OS понимает сленг разработчиков!

**Примеры:**
- "накидай экшн" → Создать Action
- "запили эндпоинт" → Создать REST endpoint
- "пульни евент" → Опубликовать Event

**Файл:** `agent-os/slang/dictionary.md`

> 💡 **Совет:** Словарь можно дополнять своими терминами!

---

## 🧠 Self-Improving Systems

Agent OS включает системы самообучения и адаптации, которые позволяют AI-агенту накапливать опыт и улучшаться со временем.

### 1. Memory System (`memory/`)

Персистентная память агента с иерархией уровней:

| Уровень | Назначение | Пример |
|---------|------------|--------|
| **knowledge/** | Накопленные знания | Архитектурные паттерны, доменные правила |
| **learning/** | Обучение на ошибках | Документированные ошибки и их решения |
| **context/** | Контекст проекта | Предпочтения пользователя, состояние проекта |

**Команды:**
```
/memory search <query>    — Поиск в базе знаний
/memory add <knowledge>   — Добавить новое знание
/memory mistakes          — Просмотреть документированные ошибки
```

### 2. Feedback Loop (`feedback/`)

Автоматический сбор и анализ обратной связи:

- **Триггеры сбора** — после завершения задач, при ошибках
- **Метрики** — время выполнения, качество кода, количество итераций
- **Автоматические действия** — обновление памяти, корректировка подходов

**Команды:**
```
/feedback collect         — Запросить фидбек по последней задаче
/feedback stats           — Показать статистику и метрики
/feedback dashboard       — Открыть дашборд метрик
```

### 3. Standards Evolution (`standards/evolution/`)

Автоматическая эволюция стандартов на основе анализа кода:

- **Обнаружение паттернов** — анализ повторяющихся решений в коде
- **Proposals** — предложения по изменению стандартов
- **Версионирование** — история изменений стандартов

**Команды:**
```
/standards evolve         — Запустить анализ и предложить изменения
/standards proposals      — Просмотреть pending proposals
/standards apply <id>     — Применить предложение
```

### 4. Knowledge Integration (`knowledge/`)

Интеграция с внешними источниками знаний через MCP:

| Источник | Приоритет | Содержимое |
|----------|-----------|------------|
| **internal** | 1 (высший) | agent-os/, docs/, foxdocs/ |
| **libraries** | 2 | Context7 (Litestar, Piccolo, Dishka, ...) |
| **external** | 3 | Web Search, arXiv |

**Команды:**
```
/knowledge search <topic>     — Поиск по всем источникам
/knowledge litestar <query>   — Документация Litestar
/knowledge piccolo <query>    — Документация Piccolo ORM
/knowledge dishka <query>     — Документация Dishka DI
```

### 5. Training Mode (`training/`)

Обучающий режим для онбординга и экспериментов:

- **Туториалы** — пошаговые инструкции для изучения архитектуры
- **Симуляции** — интерактивные сценарии разработки
- **Sandbox** — безопасная среда для экспериментов

**Команды:**
```
/training start               — Начать обучающий режим
/training tutorial <name>     — Запустить конкретный туториал
/training sandbox             — Открыть песочницу
/training list                — Список доступных туториалов
```

---

## 📊 Статистика

| Категория | Количество |
|-----------|------------|
| Standards | 17 файлов |
| Templates | 16 шаблонов |
| Workflows | 3 инструкции |
| Checklists | 3 чеклиста |
| Troubleshooting | 3 гайда |
| Snippets | 4 паттерна |
| Anti-patterns | 2 гайда |
| Commands (справочные) | 13 файлов |
| Slang | 1 словарь |
| **Self-Improving Systems** | **5 систем** |
| Memory | ~15 файлов |
| Feedback | ~5 файлов |
| Knowledge | ~4 файла |
| Standards Evolution | ~3 файла |
| Training | ~5 файлов |
| **Итого** | **~95 файлов** |

---

## 🔗 Связь с `.cursor/`

Рабочие команды находятся в `.cursor/commands/`:

```
.cursor/
├── commands/
│   ├── agent-os/            # Spec-Driven workflow + Research
│   │   ├── plan-product.md
│   │   ├── shape-spec.md
│   │   ├── write-spec.md
│   │   ├── create-tasks.md
│   │   ├── implement-tasks.md
│   │   ├── orchestrate-tasks.md
│   │   ├── research.md           # 🆕
│   │   ├── research-codebase.md  # 🆕
│   │   └── research-online.md    # 🆕
│   └── dev/                 # Быстрые команды разработки
│       ├── guide.md
│       ├── slang.md
│       └── ...
└── agents/
    └── agent-os/            # Subagents
```

---

## 📚 Основные принципы

1. **Result[T, E]** — не exceptions для бизнес-ошибок
2. **Абсолютные импорты** — от `src.`
3. **Containers изолированы** — общение через Events
4. **Явная регистрация** — никакой магии
5. **Типизация везде** — mypy strict

---

---

## 🔮 Архитектура Self-Improving Agent

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT OS v4.2                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │
│  │   Memory    │◄──│  Feedback   │──►│  Standards  │                │
│  │   System    │   │    Loop     │   │  Evolution  │                │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                │
│         │                 │                 │                        │
│         ▼                 ▼                 ▼                        │
│  ┌──────────────────────────────────────────────────────┐           │
│  │              Knowledge Integration                    │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │           │
│  │  │ Internal │  │Libraries │  │ External │            │           │
│  │  │ (docs/)  │  │(Context7)│  │(Web/arXiv)│           │           │
│  │  └──────────┘  └──────────┘  └──────────┘            │           │
│  └──────────────────────────────────────────────────────┘           │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────┐           │
│  │                  Training Mode                        │           │
│  │         Tutorials │ Simulations │ Sandbox             │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Цикл самообучения:**
1. **Выполнение задачи** → Агент решает задачу
2. **Feedback** → Сбор обратной связи (автоматический + от пользователя)
3. **Memory** → Сохранение опыта (успехи, ошибки, паттерны)
4. **Evolution** → Анализ и обновление стандартов
5. **Knowledge** → Обогащение внешними знаниями
6. **Training** → Применение новых знаний в следующих задачах

---

**Hyper-Porto v4.0** — AI-First Self-Improving Architecture 🚀
