# 🧠 Agent Memory & Learning System

> Структурированная персистентная память агентов с разделением по типам знаний и автоматической агрегацией.

**Версия:** 2.0.0  
**Дата:** 2026-01-19

---

## 🎯 Философия

Память разделена на **4 уровня** по степени абстракции и долговечности:

```
┌─────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE (Знания)                                              │
│  Долгосрочные, проверенные, переиспользуемые                    │
│  → Архитектурные решения, паттерны, доменные знания             │
├─────────────────────────────────────────────────────────────────┤
│  LEARNING (Обучение)                                             │
│  Извлечённые уроки из опыта                                     │
│  → Ошибки, улучшения, инсайты                                   │
├─────────────────────────────────────────────────────────────────┤
│  EXPERIENCE (Опыт)                                               │
│  Сырые данные о сессиях и имплементациях                        │
│  → Логи сессий, история реализаций, отладка                     │
├─────────────────────────────────────────────────────────────────┤
│  CONTEXT (Контекст)                                              │
│  Текущее состояние проекта и предпочтения                       │
│  → Настройки, предпочтения пользователя, специфика модулей      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура

```
agent-os/memory/
│
├── _meta/                           # ═══ Метаданные системы ═══
│   ├── schema.yml                   # Схема данных и валидация
│   ├── index.json                   # Глобальный поисковый индекс
│   ├── stats.json                   # Агрегированная статистика
│   └── relations.json               # Граф связей между записями
│
├── knowledge/                       # ═══ УРОВЕНЬ 1: Знания ═══
│   │                                # (Долгосрочные, верифицированные)
│   │
│   ├── architecture/                # Архитектурные решения
│   │   ├── _index.md                # Оглавление + навигация
│   │   ├── adr/                     # Architecture Decision Records
│   │   │   └── NNN-title.md         # Формат: номер-название.md
│   │   └── principles/              # Выведенные принципы
│   │       └── principle-name.md
│   │
│   ├── patterns/                    # Паттерны кода
│   │   ├── _index.md                # Каталог паттернов
│   │   ├── verified/                # ✅ Проверенные, рекомендуемые
│   │   │   └── pattern-name.md
│   │   └── experimental/            # 🧪 Экспериментальные
│   │       └── pattern-name.md
│   │
│   └── domain/                      # Доменные знания по модулям
│       ├── _index.md                # Карта модулей
│       └── {Section}/               # По секциям (AppSection, VendorSection)
│           └── {Module}/            # По модулям
│               ├── overview.md      # Обзор модуля
│               ├── decisions.md     # Решения в рамках модуля
│               └── gotchas.md       # Подводные камни
│
├── learning/                        # ═══ УРОВЕНЬ 2: Обучение ═══
│   │                                # (Извлечённые уроки)
│   │
│   ├── mistakes/                    # Ошибки и уроки
│   │   ├── _index.md                # Каталог по категориям
│   │   ├── by-category/             # Группировка по типу
│   │   │   ├── imports.md           # Ошибки импортов
│   │   │   ├── typing.md            # Ошибки типизации
│   │   │   ├── async.md             # Async/await ошибки
│   │   │   ├── di.md                # Dependency Injection
│   │   │   ├── result-pattern.md    # Result[T, E] ошибки
│   │   │   └── architecture.md      # Архитектурные ошибки
│   │   └── by-severity/             # Группировка по важности
│   │       ├── critical.md          # 🔴 Критические
│   │       ├── major.md             # 🟠 Серьёзные
│   │       └── minor.md             # 🟡 Незначительные
│   │
│   ├── improvements/                # Улучшения процессов
│   │   ├── _index.md
│   │   └── YYYY-Q{N}/               # По кварталам
│   │       └── improvement-name.md
│   │
│   └── insights/                    # Инсайты и наблюдения
│       ├── _index.md
│       └── YYYY-MM/                 # По месяцам
│           └── insight-name.md
│
├── experience/                      # ═══ УРОВЕНЬ 3: Опыт ═══
│   │                                # (Сырые данные, история)
│   │
│   ├── sessions/                    # История сессий
│   │   └── YYYY/                    # По годам
│   │       └── MM/                  # По месяцам
│   │           └── DD-{id}.md       # Формат: день-идентификатор.md
│   │
│   ├── implementations/             # История реализаций
│   │   └── YYYY/
│   │       └── MM-DD-{feature}.md   # Что реализовывали
│   │
│   └── debugging/                   # История отладки
│       └── YYYY/
│           └── MM-DD-{issue}.md     # Что отлаживали
│
├── context/                         # ═══ УРОВЕНЬ 4: Контекст ═══
│   │                                # (Текущее состояние)
│   │
│   ├── project/                     # О проекте
│   │   ├── overview.md              # Общая информация
│   │   ├── tech-stack.md            # Технологии (автообновление)
│   │   └── conventions.md           # Конвенции (извлечённые)
│   │
│   ├── user/                        # О пользователе
│   │   ├── preferences.md           # Предпочтения в коде
│   │   ├── communication.md         # Стиль общения
│   │   └── workflows.md             # Предпочитаемые workflow
│   │
│   └── modules/                     # Контекст по модулям
│       └── {Section}/
│           └── {Module}.md          # Текущее состояние модуля
│
└── feedback/                        # ═══ Обратная связь ═══
    │
    ├── ratings/                     # Количественные оценки
    │   └── YYYY.json                # Агрегация по году
    │
    ├── qualitative/                 # Качественный фидбек
    │   └── YYYY-MM/
    │       └── DD-{topic}.md
    │
    └── analytics/                   # Аналитика
        ├── weekly/                  # Еженедельные отчёты
        │   └── YYYY-WNN.md
        ├── monthly/                 # Ежемесячные отчёты
        │   └── YYYY-MM.md
        └── trends.md                # Тренды и паттерны
```

---

## 📋 Форматы записей

### ADR (Architecture Decision Record)

```markdown
# ADR-NNN: [Название решения]

## Статус
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Контекст
[Какую проблему решаем, какие ограничения]

## Решение
[Что выбрали и почему]

## Альтернативы
| Вариант | Плюсы | Минусы |
|---------|-------|--------|
| A       | ...   | ...    |
| B       | ...   | ...    |

## Последствия
[Что это означает для проекта]

## Связи
- Relates: [#tag1, #tag2]
- Supersedes: [ADR-XXX]
- See also: [path/to/related.md]
```

### Mistake Entry

```markdown
# ❌ [Краткое название ошибки]

## Метаданные
- **ID:** MIST-YYYYMMDD-NNN
- **Категория:** [imports | typing | async | di | result | architecture]
- **Серьёзность:** [critical | major | minor]
- **Модуль:** [путь к модулю]
- **Дата:** YYYY-MM-DD

## Что произошло
[Описание ошибки]

## Симптомы
- [Как проявилась ошибка]

## Root Cause
[Почему это произошло]

## Решение
```python
# До (неправильно)
...

# После (правильно)
...
```

## Превентивные меры
- [ ] [Что добавить в чеклист]
- [ ] [Какой guardrail добавить]

## Связи
- Tags: [#tag1, #tag2]
- Related mistakes: [MIST-XXX]
- Related pattern: [path/to/pattern.md]
```

### Pattern Entry

```markdown
# ✅ [Название паттерна]

## Метаданные
- **ID:** PAT-NNN
- **Статус:** [verified | experimental]
- **Использований:** N
- **Последнее использование:** YYYY-MM-DD

## Когда применять
[Контекст и условия]

## Когда НЕ применять
[Антиусловия]

## Реализация

```python
# Шаблон кода
```

## Примеры в проекте
- `src/Containers/.../...`
- `src/Containers/.../...`

## Связи
- Tags: [#tag1, #tag2]
- Supersedes: [PAT-XXX]
- Related: [path/to/related.md]
```

### Session Log

```markdown
# Session: YYYY-MM-DD-{id}

## Метаданные
- **Начало:** HH:MM
- **Длительность:** Xm
- **Тип:** [implementation | debugging | research | review]

## Цель
[Что хотели достичь]

## Результат
[success | partial | failed]

## Ключевые решения
1. [Решение 1] → [результат]
2. [Решение 2] → [результат]

## Извлечённые уроки
- [Урок 1]
- [Урок 2]

## Follow-up
- [ ] [Что нужно сделать потом]

## Оценка пользователя
- Rating: [1-5]
- Comment: [...]
```

---

## 🔍 Поиск и навигация

### Индексация

Каждая категория имеет `_index.md` с:
- Оглавлением всех записей
- Группировкой по тегам
- Ссылками на связанные записи
- Статистикой раздела

### Теги

Стандартные теги:
```
#action #task #query #repository #uow #event
#result #failure #success
#import #typing #async #sync
#di #dishka #provider
#litestar #piccolo #strawberry
#module:{ModuleName}
#severity:{critical|major|minor}
```

### Связи (relations.json)

```json
{
  "nodes": [
    {"id": "ADR-001", "type": "decision", "title": "..."},
    {"id": "MIST-001", "type": "mistake", "title": "..."},
    {"id": "PAT-001", "type": "pattern", "title": "..."}
  ],
  "edges": [
    {"from": "MIST-001", "to": "PAT-001", "relation": "led_to"},
    {"from": "ADR-001", "to": "PAT-001", "relation": "defined"},
    {"from": "MIST-002", "to": "MIST-001", "relation": "similar_to"}
  ]
}
```

---

## 🔄 Жизненный цикл данных

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  EXPERIENCE  │───▶│   LEARNING   │───▶│  KNOWLEDGE   │
│   (сырые)    │    │ (извлечённые)│    │(верифициров.)|
└──────────────┘    └──────────────┘    └──────────────┘
      │                    │                    │
      ▼                    ▼                    ▼
   Sessions            Mistakes              ADRs
   Implementations     Insights              Patterns
   Debugging           Improvements          Principles
```

### Правила продвижения

1. **Experience → Learning**
   - После 3+ похожих ошибок → создать запись в `learning/mistakes/`
   - После успешного паттерна 5+ раз → создать `patterns/experimental/`

2. **Learning → Knowledge**
   - Experimental pattern используется 10+ раз без проблем → `patterns/verified/`
   - Insight подтверждён практикой → `knowledge/principles/`

---

## 🤖 API для агентов

### Чтение памяти

```python
# Поиск релевантных записей
memory.search(
    query="Result pattern error handling",
    types=["mistake", "pattern"],
    limit=5
)

# Получить контекст модуля
memory.get_module_context("UserModule")

# Получить предпочтения пользователя
memory.get_user_preferences()

# Найти похожие ошибки
memory.find_similar_mistakes(error_description)
```

### Запись в память

```python
# Записать ошибку
memory.record_mistake(
    category="imports",
    severity="minor",
    description="...",
    solution="...",
    prevention=["..."]
)

# Записать решение
memory.record_decision(
    title="...",
    context="...",
    decision="...",
    consequences="..."
)

# Обновить контекст
memory.update_context(
    module="UserModule",
    key="last_changes",
    value="..."
)
```

---

## 📊 Автоматическая аналитика

### Еженедельный отчёт (analytics/weekly/)

```markdown
# Week YYYY-WNN Report

## Статистика
- Сессий: N
- Успешных: N (X%)
- С ошибками: N (X%)

## Top ошибки недели
1. [Категория] — N раз
2. [Категория] — N раз

## Новые паттерны
- [Pattern 1]

## Тренды
- ⬆️ Улучшение: [область]
- ⬇️ Проблема: [область]

## Рекомендации
- [ ] [Что улучшить]
```

---

## 🔗 Связанные системы

| Система | Интеграция |
|---------|------------|
| **Feedback Loop** | Записывает оценки в `feedback/` |
| **Standards Evolution** | Читает `learning/` для эволюции стандартов |
| **Training Mode** | Использует `knowledge/` для обучения |
| **Pre-check Agent** | Ищет в `learning/mistakes/` перед реализацией |

---

## 📚 Команды

```bash
# Навигация
/memory browse                    # Интерактивный браузер
/memory browse knowledge          # Только knowledge уровень

# Поиск
/memory search "query"            # Полнотекстовый поиск
/memory search --tag #imports     # По тегу
/memory search --module UserModule # По модулю

# Запись
/memory add mistake               # Добавить ошибку (интерактивно)
/memory add decision              # Добавить решение
/memory add pattern               # Добавить паттерн

# Аналитика
/memory stats                     # Общая статистика
/memory trends                    # Тренды
/memory report weekly             # Сгенерировать недельный отчёт
```
