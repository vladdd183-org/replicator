# 🌐 External Knowledge Integration

> Интеграция внешних источников знаний для обогащения контекста агентов

**Версия:** 1.0.0  
**Дата:** 2026-01-19

---

## 🎯 Цель

Агенты должны иметь доступ к:
1. **Внутренним знаниям** — документация проекта, память, стандарты
2. **Внешним знаниям** — документация библиотек, best practices, исследования
3. **Актуальной информации** — свежие версии, изменения API

```
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYERS                              │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  PROJECT KNOWLEDGE (Highest Priority)                     │ │
│   │  docs/, agent-os/, memory/, standards/                    │ │
│   └──────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  LIBRARY KNOWLEDGE (Context7 MCP)                         │ │
│   │  Litestar, Piccolo, Dishka, Returns, anyio...            │ │
│   └──────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  EXTERNAL KNOWLEDGE (Web, Research)                       │ │
│   │  Stack Overflow, GitHub, arXiv, Blogs                     │ │
│   └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура

```
agent-os/knowledge/
├── README.md                    # Этот файл
├── config.yml                   # Конфигурация источников
│
├── sources/                     # ═══ Источники знаний ═══
│   ├── internal.yml             # Внутренние источники
│   ├── libraries.yml            # Документация библиотек
│   └── external.yml             # Внешние источники
│
├── cache/                       # ═══ Кэш знаний ═══
│   ├── libraries/               # Кэш документации библиотек
│   │   └── {library}/
│   │       ├── index.json       # Индекс для поиска
│   │       └── pages/           # Кэшированные страницы
│   └── queries/                 # Кэш запросов
│       └── {hash}.json
│
├── synthesis/                   # ═══ Синтезированные знания ═══
│   ├── comparisons/             # Сравнения библиотек/подходов
│   │   └── {topic}.md
│   ├── guides/                  # Сгенерированные гайды
│   │   └── {topic}.md
│   └── decisions/               # Обоснования решений
│       └── {topic}.md
│
└── retrieval/                   # ═══ Поиск и извлечение ═══
    ├── strategies.yml           # Стратегии поиска
    └── prompts/                 # Промпты для извлечения
        └── {task}.md
```

---

## ⚙️ Конфигурация

```yaml
# config.yml
version: "1.0.0"

# Приоритет источников (выше = приоритетнее)
priority:
  1: internal
  2: libraries
  3: external

# Стратегия поиска
search:
  # Сначала искать внутри, потом снаружи
  strategy: hierarchical
  
  # Максимум результатов на источник
  max_results_per_source: 5
  
  # Кэшировать результаты
  cache_enabled: true
  cache_ttl_hours: 24

# MCP интеграции
mcp:
  context7:
    enabled: true
    use_for:
      - library_docs
      - code_examples
      
  arxiv:
    enabled: true
    use_for:
      - research_papers
      - algorithms
      
  web_search:
    enabled: true
    use_for:
      - recent_updates
      - community_solutions
```

---

## 📚 Источники знаний

### Internal Sources (Внутренние)

```yaml
# sources/internal.yml
sources:
  project_docs:
    path: docs/
    priority: 100
    index: true
    description: "Документация проекта"
    
  agent_os:
    path: agent-os/
    priority: 95
    index: true
    description: "Стандарты и шаблоны"
    
  memory:
    path: agent-os/memory/
    priority: 90
    index: true
    description: "Опыт и решения"
    
  codebase:
    path: src/
    priority: 85
    index: false  # Не индексируем, но можем искать
    description: "Существующий код"
```

### Library Sources (Библиотеки)

```yaml
# sources/libraries.yml
sources:
  litestar:
    mcp: context7
    query: "litestar python web framework"
    topics:
      - routing
      - middleware
      - dependency injection
      - events
      - channels
      - websockets
      
  piccolo:
    mcp: context7
    query: "piccolo orm python"
    topics:
      - tables
      - queries
      - migrations
      - transactions
      
  dishka:
    mcp: context7
    query: "dishka python dependency injection"
    topics:
      - providers
      - scopes
      - integrations
      
  returns:
    mcp: context7
    query: "returns python library"
    topics:
      - result
      - maybe
      - io
      - railway
      
  anyio:
    mcp: context7
    query: "anyio python async"
    topics:
      - task groups
      - cancellation
      - synchronization
      
  strawberry:
    mcp: context7
    query: "strawberry graphql python"
    topics:
      - types
      - resolvers
      - subscriptions
      
  pydantic:
    mcp: context7
    query: "pydantic v2"
    topics:
      - models
      - validation
      - settings
```

### External Sources (Внешние)

```yaml
# sources/external.yml
sources:
  web_search:
    mcp: parrallel
    use_for:
      - error_messages
      - recent_updates
      - community_solutions
    rate_limit: 10/hour
    
  arxiv:
    mcp: arxiv
    use_for:
      - ml_algorithms
      - distributed_systems
      - formal_methods
    categories:
      - cs.SE  # Software Engineering
      - cs.DC  # Distributed Computing
      - cs.AI  # AI
      
  github:
    mcp: web_fetch
    use_for:
      - code_examples
      - issues
      - discussions
```

---

## 🔍 Стратегии поиска

### Hierarchical Search (По умолчанию)

```
Query: "How to implement Result pattern"

1. Search Internal
   ├─ docs/04-result-railway.md ✓
   ├─ agent-os/snippets/result-patterns.md ✓
   └─ memory/patterns/result-*.md

2. If insufficient → Search Libraries
   └─ Context7: "returns library Result"

3. If still insufficient → Search External
   └─ Web: "python returns Result pattern examples"
```

### Targeted Search (Для конкретных вопросов)

```
Query: "Piccolo migration syntax for adding column"

1. Direct to Library
   └─ Context7: "piccolo orm add column migration"
   
2. Supplement with Internal
   └─ agent-os/standards/backend/migrations.md
```

### Research Search (Для исследований)

```
Query: "Best practices for saga pattern in Python"

1. Internal Theory
   └─ docs/15-saga-patterns.md

2. External Papers
   └─ arXiv: "saga pattern distributed transactions"
   
3. Community Practices
   └─ Web: "python saga pattern implementation 2025 2026"
```

---

## 🤖 Knowledge Retriever Agent

### Когда вызывается

- Вопросы о библиотеках: "Как в Litestar сделать..."
- Исследовательские запросы: "Best practices для..."
- Ошибки: "Error: XYZ" → поиск решения
- Сравнения: "X vs Y"

### Процесс

```
┌──────────────┐
│    Query     │
└──────┬───────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐
│   Classify   │───▶│   Strategy   │
│   Intent     │    │   Selection  │
└──────────────┘    └──────┬───────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Internal   │    │   Library    │    │   External   │
│   Search     │    │   Search     │    │   Search     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                    ┌──────────────┐
                    │   Synthesize │
                    │   & Rank     │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Response   │
                    └──────────────┘
```

---

## 💾 Кэширование

### Что кэшируется

| Тип | TTL | Причина |
|-----|-----|---------|
| Library docs | 7 days | Редко меняются |
| Web searches | 24 hours | Могут устареть |
| arXiv papers | 30 days | Статичны |
| Internal | No cache | Всегда актуально |

### Формат кэша

```json
// cache/queries/{hash}.json
{
  "query": "litestar middleware example",
  "hash": "abc123...",
  "timestamp": "2026-01-19T12:00:00Z",
  "expires": "2026-01-20T12:00:00Z",
  "sources_used": ["context7", "internal"],
  "results": [
    {
      "source": "context7",
      "title": "Litestar Middleware Guide",
      "content": "...",
      "relevance": 0.95
    }
  ]
}
```

---

## 📝 Синтез знаний

### Comparison (Сравнение)

```markdown
# synthesis/comparisons/taskiq-vs-temporal.md

# TaskIQ vs Temporal для Background Tasks

## Comparison

| Аспект | TaskIQ | Temporal |
|--------|--------|----------|
| Complexity | Low | High |
| Durability | Redis/RabbitMQ | Event Sourcing |
| Saga Support | Manual | Built-in |
| Learning Curve | 1-2 days | 2-4 weeks |

## Recommendation

Используйте **TaskIQ** для:
- Простых background tasks
- Не-критичных процессов

Используйте **Temporal** для:
- Mission-critical workflows
- Сложных Saga с компенсациями

## Sources

- Internal: docs/15-saga-patterns.md
- Context7: Temporal Python SDK
- arXiv: Saga pattern formal analysis
```

### Decision (Обоснование)

```markdown
# synthesis/decisions/why-litestar.md

# Почему Litestar?

## Контекст

Выбор web-фреймворка для проекта.

## Рассмотренные альтернативы

1. **FastAPI** — популярный, но...
2. **Litestar** — выбран
3. **Django** — слишком тяжёлый

## Обоснование

[Extracted and synthesized from multiple sources]

## Sources

- Internal: docs/08-libraries.md
- Context7: Litestar documentation
- Web: "Litestar vs FastAPI 2025"
```

---

## 📚 Команды

```bash
# Поиск
/knowledge search "query"            # Поиск по всем источникам
/knowledge search --internal "query" # Только внутренние
/knowledge search --library "query"  # Только документация библиотек
/knowledge search --external "query" # Только внешние

# Конкретные источники
/knowledge litestar "middleware"     # Документация Litestar
/knowledge piccolo "migrations"      # Документация Piccolo

# Исследование
/knowledge research "topic"          # Глубокое исследование
/knowledge compare "X" "Y"           # Сравнение

# Кэш
/knowledge cache clear               # Очистить кэш
/knowledge cache stats               # Статистика кэша

# Синтез
/knowledge synthesize "topic"        # Создать synthesis документ
```

---

## 🔗 MCP Интеграция

### Context7 (Документация библиотек)

```yaml
server: user-context7
tool: resolve-library-id  # Найти библиотеку
tool: get-library-docs    # Получить документацию
```

Использование:
- Для вопросов о Litestar, Piccolo, Dishka, etc.
- Для примеров кода из официальной документации

### arXiv (Научные статьи)

```yaml
server: user-arxiv-mcp-server
tool: search_papers       # Поиск статей
tool: get_paper_details   # Детали статьи
```

Использование:
- Для исследования алгоритмов
- Для формального обоснования решений

### Web Search (Паррallel)

```yaml
server: user-parrallel
tool: web_search          # Поиск в интернете
tool: web_fetch           # Получить страницу
```

Использование:
- Для свежих решений ошибок
- Для community best practices

---

## 🔒 Приоритеты и конфликты

### При конфликте информации

1. **Internal** (docs/, agent-os/) — высший приоритет
2. **Project decisions** (memory/knowledge/) — второй
3. **Library official docs** — третий
4. **External** — самый низкий

### Пример разрешения

```
Вопрос: "Как обрабатывать ошибки?"

Internal docs/04-result-railway.md: "Use Result[T, E]"
External blog: "Just raise exceptions"

→ Ответ: "Use Result[T, E]" (приоритет internal)
```

---

## 🔗 Связанные системы

| Система | Интеграция |
|---------|------------|
| **Memory** | Сохраняет synthesis в knowledge |
| **Standards** | Обогащает примерами из библиотек |
| **Training** | Использует для обучающих материалов |
