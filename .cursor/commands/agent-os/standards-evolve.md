# Standards Evolve — Эволюция стандартов

Автоматическая эволюция стандартов на основе паттернов в коде и обратной связи.

## Когда использовать

- Для сканирования кодовой базы на паттерны
- Для обнаружения разрывов между стандартами и практикой
- Для обновления примеров в стандартах
- Для применения предложенных изменений

## Синтаксис

```
/agent-os/standards-evolve [действие]
```

## Доступные действия

| Действие | Описание |
|----------|----------|
| `scan` | Сканировать codebase на паттерны |
| `gaps` | Показать разрывы стандарты ↔ практика |
| `proposals` | Список предложений изменений |
| `approve {id}` | Одобрить предложение |
| `reject {id}` | Отклонить предложение |
| `update-examples` | Обновить примеры из реального кода |
| `coverage` | Отчёт о покрытии стандартами |
| `adherence` | Отчёт о соответствии стандартам |
| `history` | История изменений стандартов |

## Примеры использования

### Сканировать кодовую базу

```
/agent-os/standards-evolve scan
```

Выполнит:
1. Поиск паттернов в `src/Containers/` и `src/Ship/`
2. Сравнение с текущими стандартами
3. Обнаружение новых паттернов и анти-паттернов
4. Создание предложений при необходимости

### Показать gaps

```
/agent-os/standards-evolve gaps
```

Покажет:
- Стандарты, которые не соблюдаются
- Количество нарушений по каждому
- Рекомендации по исправлению

### Просмотр предложений

```
/agent-os/standards-evolve proposals
```

Покажет pending proposals с:
- ID и названием
- Типом изменения
- Приоритетом
- Кратким описанием

### Одобрить предложение

```
/agent-os/standards-evolve approve PROP-015
```

Применит изменения:
1. Обновит файл стандарта
2. Запишет в историю
3. Переместит proposal в `approved/`

### Обновить примеры

```
/agent-os/standards-evolve update-examples
```

Автоматически (без одобрения):
1. Найдёт реальные примеры в коде
2. Заменит устаревшие примеры в стандартах
3. Обновит timestamps

## Процесс

Делегируется агенту **standards-evolver**:

```
@.cursor/agents/standards-evolver.md

Выполни эволюцию стандартов:

1. Определи тип действия
2. Сканируй src/ для обнаружения паттернов
3. Сравни с agent-os/standards/
4. Создавай proposals в evolution/proposals/

Справка: @agent-os/standards/evolution/README.md
```

## Структура системы

```
agent-os/standards/evolution/
├── README.md            # Документация
├── config.yml           # Конфигурация
├── observations/        # Наблюдения
│   ├── patterns/        # Обнаруженные паттерны
│   ├── gaps/            # Разрывы
│   └── trends/          # Тренды
├── proposals/           # Предложения
│   ├── pending/         # Ожидающие
│   ├── approved/        # Одобренные
│   └── rejected/        # Отклонённые
├── history/             # История изменений
└── analytics/           # Аналитика
    ├── coverage.md      # Покрытие
    └── adherence.md     # Соответствие
```

## Типы изменений

| Тип | Описание | Требует одобрения |
|-----|----------|-------------------|
| `new_rule` | Новое правило | ✅ Да |
| `modify_rule` | Изменение правила | ✅ Да |
| `deprecate_rule` | Удаление правила | ✅ Да |
| `add_example` | Добавить пример | ❌ Нет |
| `update_example` | Обновить пример | ❌ Нет |
| `add_anti_pattern` | Добавить анти-паттерн | ✅ Да |

## Формат вывода

### После scan

```
📊 Standards Evolution Scan — 2026-01-19

Просканировано:
- 45 файлов в src/Containers/
- 23 файла в src/Ship/

Обнаружено:
- ✨ 2 новых паттерна
- ⚠️ 1 gap (3 нарушения)
- 🚫 0 анти-паттернов

Создано предложений: 2
- PROP-015: Add rule for sync task wrapping (Medium)
- PROP-016: Update Query examples (Low)

Автообновлено:
- 5 примеров в standards/backend/
- Timestamps в 3 файлах
```

### Gaps

```
⚠️ Standards Gaps — 2026-01-19

1. **Missing type hints** (global/coding-style.md)
   Нарушений: 5
   Файлы:
   - src/Containers/.../utils.py:45
   - src/Containers/.../helpers.py:12
   
   Рекомендация: Добавить type hints или обновить стандарт

2. **Relative imports** (CLAUDE.md)
   Нарушений: 2
   Файлы:
   - src/Containers/.../Actions/SomeAction.py:3
   
   Рекомендация: Исправить на абсолютные импорты
```

### Proposals

```
📋 Pending Proposals

| ID | Тип | Название | Priority |
|----|-----|----------|----------|
| PROP-015 | new_rule | Sync Task Wrapping | Medium |
| PROP-016 | update_example | Query Examples | Low |
| PROP-017 | add_anti_pattern | Service Locator | High |

Для одобрения: /agent-os/standards-evolve approve PROP-015
Для отклонения: /agent-os/standards-evolve reject PROP-015
```

### После approve

```
✅ Применено: PROP-015

Файл: standards/backend/actions-tasks.md
Изменение: Добавлено правило "SyncTask в Async"

Diff:
+ ### SyncTask в Async контексте
+ 
+ При вызове SyncTask из Action используйте `anyio.to_thread.run_sync()`:
+ 
+ ```python
+ result = await anyio.to_thread.run_sync(self.sync_task.run, input_data)
+ ```

История: evolution/history/2026/01-19-prop-015.md
```

## Автоматические действия

Без одобрения применяются:
- Обновление примеров из реального кода
- Обновление timestamps
- Обновление cross-references

С одобрением:
- Новые правила
- Изменение существующих правил
- Добавление анти-паттернов
- Удаление правил

## Связанные системы

| Система | Интеграция |
|---------|------------|
| **Memory** | Читает mistakes для обнаружения gaps |
| **Feedback** | Читает негативный feedback для улучшений |
| **Codebase** | Сканирует для обнаружения паттернов |
| **Agents** | Уведомляет об изменениях стандартов |

## Справка

Полная документация: `agent-os/standards/evolution/README.md`
