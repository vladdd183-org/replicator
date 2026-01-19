# Memory — Управление памятью агентов

Управление персистентной памятью агентов: поиск, добавление записей, просмотр статистики.

## Когда использовать

- Для поиска прошлых решений и ошибок
- Для записи архитектурных решений (ADR)
- Для фиксации ошибок и их решений
- Для добавления проверенных паттернов
- Для анализа накопленного опыта

## Синтаксис

```
/agent-os/memory [действие] [параметры]
```

## Доступные действия

| Действие | Описание |
|----------|----------|
| `search "query"` | Поиск по всей памяти |
| `add decision` | Добавить архитектурное решение (ADR) |
| `add mistake` | Записать ошибку с решением |
| `add pattern` | Добавить паттерн кода |
| `add insight` | Добавить наблюдение/инсайт |
| `stats` | Показать статистику памяти |
| `recent` | Последние записи |
| `related [id]` | Найти связанные записи |

## Примеры использования

### Поиск в памяти

```
/agent-os/memory search "Result pattern"
```

Ищет во всех уровнях памяти:
- `knowledge/` — знания, ADR, паттерны
- `learning/` — ошибки, инсайты
- `experience/` — сессии, реализации

### Добавить архитектурное решение

```
/agent-os/memory add decision
```

Агент интерактивно запросит:
1. Название решения
2. Контекст и причины
3. Рассмотренные альтернативы
4. Последствия

Создаст файл в `agent-os/memory/knowledge/architecture/adr/NNN-title.md`

### Записать ошибку

```
/agent-os/memory add mistake
```

Агент запросит:
1. Категорию (imports, typing, async, di, result-pattern, architecture)
2. Серьёзность (critical, major, minor)
3. Что произошло
4. Root cause
5. Решение
6. Превентивные меры

### Добавить паттерн

```
/agent-os/memory add pattern
```

Создаст паттерн в:
- `knowledge/patterns/experimental/` — новый паттерн
- `knowledge/patterns/verified/` — проверенный паттерн (10+ использований)

### Статистика

```
/agent-os/memory stats
```

Покажет:
- Количество записей по уровням
- Топ категорий ошибок
- Последние изменения
- Тренды

### Последние записи

```
/agent-os/memory recent
```

Покажет последние добавленные записи из всех уровней.

## Процесс

Делегируется агенту **memory-manager**:

```
@.cursor/agents/memory-manager.md

Выполни действие с памятью:

1. Определи тип действия (search/add/stats)
2. Используй структуру agent-os/memory/
3. Обновляй индексы (_meta/index.json)
4. Поддерживай связи между записями

Справка по структуре: @agent-os/memory/README.md
```

## Структура памяти

```
agent-os/memory/
├── _meta/           # Индексы и статистика
├── knowledge/       # Долгосрочные знания
│   ├── architecture/  # ADRs, принципы
│   ├── patterns/      # Паттерны кода
│   └── domain/        # Доменные знания
├── learning/        # Извлечённые уроки
│   ├── mistakes/      # Ошибки
│   ├── insights/      # Наблюдения
│   └── improvements/  # Улучшения
├── experience/      # История сессий
└── context/         # Текущий контекст
```

## Формат вывода

### После поиска

```
🔍 Поиск: "Result pattern"

Найдено 4 записи:

1. 📘 PAT-003: Result Pattern Best Practices
   Relevance: ⭐⭐⭐⭐⭐
   → knowledge/patterns/verified/result-best-practices.md

2. ❌ MIST-20260115-002: Forgotten Failure case
   Relevance: ⭐⭐⭐⭐
   → learning/mistakes/by-category/result-pattern.md

3. 📘 ADR-002: Railway-Oriented Programming
   Relevance: ⭐⭐⭐
   → knowledge/architecture/adr/002-railway-oriented.md

4. 💡 INS-202601: Result vs Exceptions analysis
   Relevance: ⭐⭐
   → learning/insights/2026-01/result-vs-exceptions.md
```

### После добавления

```
✅ Записано: ADR-005 "Выбор Temporal для Saga"

Добавлено в: knowledge/architecture/adr/005-temporal-for-saga.md
Tags: #temporal, #saga, #architecture
Связи: ADR-003, PAT-012

Индексы обновлены.
```

## Связанные системы

| Система | Интеграция |
|---------|------------|
| **Feedback** | Записывает insights из фидбека |
| **Standards Evolution** | Читает ошибки для эволюции стандартов |
| **Training** | Использует знания для обучения |
| **Pre-check Agent** | Ищет похожие ошибки перед реализацией |

## Справка

Полная документация: `agent-os/memory/README.md`
