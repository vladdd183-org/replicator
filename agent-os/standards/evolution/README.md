# 🔄 Adaptive Standards — Self-Evolving Rules

> Система автоматической эволюции стандартов на основе паттернов в коде и обратной связи

**Версия:** 1.0.0  
**Дата:** 2026-01-19

---

## 🎯 Цель

Стандарты должны:
1. **Эволюционировать** — автоматически обновляться на основе практики
2. **Отражать реальность** — примеры из актуального кода
3. **Предотвращать ошибки** — новые правила из повторяющихся mistakes
4. **Улучшаться** — на основе feedback

```
┌─────────────────────────────────────────────────────────────────┐
│                  STANDARDS EVOLUTION CYCLE                       │
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │ OBSERVE  │───▶│ ANALYZE  │───▶│ PROPOSE  │───▶│  APPLY   │ │
│   │          │    │          │    │          │    │          │ │
│   │ Codebase │    │ Patterns │    │ Changes  │    │ Standards│ │
│   │ Feedback │    │ Gaps     │    │ Review   │    │ Update   │ │
│   │ Mistakes │    │ Trends   │    │          │    │          │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│        ▲                                                 │      │
│        └─────────────────────────────────────────────────┘      │
│                       Continuous Evolution                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура

```
agent-os/standards/evolution/
├── README.md                    # Этот файл
├── config.yml                   # Конфигурация эволюции
│
├── observations/                # ═══ Наблюдения ═══
│   ├── patterns/                # Обнаруженные паттерны в коде
│   │   └── YYYY-MM-DD-{name}.md
│   ├── gaps/                    # Разрывы между стандартами и практикой
│   │   └── YYYY-MM-DD-{name}.md
│   └── trends/                  # Тренды изменений
│       └── YYYY-MM-{name}.md
│
├── proposals/                   # ═══ Предложения ═══
│   ├── pending/                 # Ожидающие review
│   │   └── PROP-NNN-{name}.md
│   ├── approved/                # Одобренные
│   │   └── PROP-NNN-{name}.md
│   └── rejected/                # Отклонённые
│       └── PROP-NNN-{name}.md
│
├── history/                     # ═══ История изменений ═══
│   └── YYYY/
│       └── MM-DD-{change}.md
│
└── analytics/                   # ═══ Аналитика ═══
    ├── coverage.md              # Покрытие стандартами
    ├── adherence.md             # Соответствие стандартам
    └── evolution-log.md         # Лог эволюции
```

---

## ⚙️ Конфигурация

```yaml
# config.yml
version: "1.0.0"

observation:
  # Источники для наблюдения
  sources:
    codebase:
      enabled: true
      paths:
        - src/Containers/
        - src/Ship/
      exclude:
        - "**/migrations/**"
        - "**/__pycache__/**"
        
    feedback:
      enabled: true
      path: ../feedback/
      
    memory:
      enabled: true
      path: ../memory/
      
  # Как часто анализировать
  schedule:
    codebase_scan: weekly
    feedback_analysis: daily
    pattern_detection: on_change
    
  # Пороги обнаружения
  thresholds:
    # Паттерн обнаруживается после N появлений
    pattern_min_occurrences: 5
    
    # Gap обнаруживается после N нарушений
    gap_min_violations: 3
    
    # Trend значим после N точек данных
    trend_min_datapoints: 10

proposals:
  # Автоматическое создание предложений
  auto_create:
    from_patterns: true
    from_gaps: true
    from_feedback: true
    
  # Требуется ли одобрение
  require_approval:
    new_rule: true
    modify_rule: true
    deprecate_rule: true
    update_example: false  # Примеры обновляются автоматически
    
  # Уровни изменений
  change_levels:
    minor:  # Обновление примеров, форматирование
      auto_apply: true
    moderate:  # Уточнение правил
      auto_apply: false
      notify: true
    major:  # Новые правила, удаление
      auto_apply: false
      require_explicit_approval: true

updates:
  # Что обновлять автоматически
  auto_update:
    # Примеры кода из codebase
    examples:
      enabled: true
      max_examples_per_rule: 3
      prefer_recent: true
      
    # Статистика использования
    usage_stats:
      enabled: true
      
    # Ссылки на связанные файлы
    cross_references:
      enabled: true
      
  # Валидация изменений
  validation:
    syntax_check: true
    consistency_check: true
    test_examples: false  # Пока не реализовано

notifications:
  # Когда уведомлять
  notify_on:
    new_proposal: true
    proposal_applied: true
    significant_gap: true
    trend_detected: true
    
  # Как уведомлять
  method: inline  # В чате
```

---

## 📝 Типы изменений

### 1. Pattern Discovery (Обнаружение паттерна)

Когда в коде регулярно появляется определённый подход:

```markdown
# Observation: Pattern Discovered

**ID:** OBS-PAT-20260119-001
**Type:** Pattern
**Occurrences:** 7
**First seen:** 2026-01-10
**Last seen:** 2026-01-19

## Паттерн

```python
# Использование anyio.to_thread для sync Tasks
password_hash = await anyio.to_thread.run_sync(
    self.hash_password.run, data.password
)
```

## Где обнаружен
- src/Containers/AppSection/UserModule/Actions/CreateUserAction.py
- src/Containers/AppSection/UserModule/Actions/UpdatePasswordAction.py
- src/Containers/AppSection/AuthModule/Actions/ResetPasswordAction.py
- ... (+4 more)

## Рекомендация

Добавить в стандарт `backend/actions-tasks.md`:

> При использовании SyncTask из Action, оборачивать вызов в 
> `anyio.to_thread.run_sync()` для избежания блокировки event loop.
```

### 2. Gap Detection (Обнаружение разрыва)

Когда практика расходится со стандартом:

```markdown
# Observation: Gap Detected

**ID:** OBS-GAP-20260119-001
**Type:** Gap
**Standard:** global/coding-style.md
**Violations:** 5

## Стандарт говорит

> Все функции должны иметь type hints

## Реальность

Найдено 5 функций без type hints:
- src/Containers/.../utils.py:45 - `def format_date(d)`
- src/Containers/.../helpers.py:12 - `def calculate_total(items)`
- ...

## Рекомендация

1. Исправить нарушения
2. Добавить проверку в pre-commit hook
3. Добавить в anti-patterns с примером
```

### 3. Trend Detection (Обнаружение тренда)

Когда наблюдается систематическое изменение:

```markdown
# Observation: Trend Detected

**ID:** OBS-TRD-202601-001
**Type:** Trend
**Period:** 2026-01-01 to 2026-01-19
**Direction:** Increasing

## Тренд

Увеличение использования `Query` классов вместо прямых запросов в Controllers.

## Данные

| Неделя | Query usage | Direct ORM |
|--------|-------------|------------|
| W1     | 15%         | 85%        |
| W2     | 40%         | 60%        |
| W3     | 70%         | 30%        |

## Рекомендация

Обновить стандарт `backend/queries.md`:
- Сделать Query обязательным для всех read операций
- Добавить migration guide для существующего кода
```

---

## 📋 Формат предложения

```markdown
# Proposal: [Title]

**ID:** PROP-NNN
**Type:** [new_rule | modify_rule | deprecate_rule | add_example | update_example]
**Priority:** [low | medium | high]
**Status:** [pending | approved | rejected | applied]

## Основание

[Почему это изменение нужно]

Based on:
- Observation: OBS-XXX
- Feedback: FB-XXX
- Mistakes: MIST-XXX

## Предлагаемое изменение

### Файл: `standards/backend/actions-tasks.md`

```diff
- Старый текст или отсутствие
+ Новый текст или добавление
```

## Влияние

- **Затрагивает:** [список файлов/модулей]
- **Обратная совместимость:** [да/нет]
- **Требует миграции:** [да/нет]

## Checklist

- [ ] Согласовано с существующими правилами
- [ ] Примеры актуальны
- [ ] Нет конфликтов с другими стандартами

## Approval

- [ ] Одобрено пользователем
- [ ] Применено
```

---

## 🔄 Процесс эволюции

### Автоматический (без одобрения)

```
Обнаружен паттерн ──▶ Обновить примеры в стандарте
                      (если примеры устарели)
```

### С одобрением

```
Обнаружен паттерн
      │
      ▼
Создать Proposal ──▶ PENDING
      │
      ▼
Уведомить пользователя
      │
      ├──▶ Одобрено ──▶ Применить ──▶ APPLIED
      │
      └──▶ Отклонено ──▶ REJECTED
```

---

## 🤖 Subagent: standards-evolver

```yaml
name: standards-evolver
triggers:
  - weekly_scan
  - on_feedback_pattern
  - on_mistake_repeat
  - manual_request
  
responsibilities:
  - Scan codebase for patterns
  - Compare with standards
  - Detect gaps
  - Create proposals
  - Update examples
```

---

## 📊 Аналитика

### Coverage Report

```markdown
# Standards Coverage Report

## Покрытие по категориям

| Категория | Файлов | Правил | Примеров | Coverage |
|-----------|--------|--------|----------|----------|
| Backend   | 6      | 42     | 38       | 90%      |
| Global    | 6      | 35     | 30       | 86%      |
| Testing   | 1      | 15     | 12       | 80%      |

## Непокрытые области

- GraphQL mutations (нет примеров)
- WebSocket error handling (нет правил)
- CLI testing (нет правил)
```

### Adherence Report

```markdown
# Standards Adherence Report

## Соответствие по модулям

| Модуль | Adherence | Violations | Top Issue |
|--------|-----------|------------|-----------|
| UserModule | 95% | 2 | Missing docstrings |
| AuditModule | 88% | 5 | Import style |
| SearchModule | 92% | 3 | Type hints |

## Trend

- Улучшение: +5% за месяц
- Главная проблема: Import style (15 violations)
```

---

## 📚 Команды

```bash
# Анализ
/standards scan                  # Сканировать codebase
/standards gaps                  # Показать gaps
/standards coverage              # Отчёт о покрытии

# Предложения
/standards proposals             # Список pending proposals
/standards approve {id}          # Одобрить proposal
/standards reject {id}           # Отклонить proposal

# Обновления
/standards update-examples       # Обновить примеры из кода
/standards sync                  # Синхронизировать все

# История
/standards history               # История изменений
/standards diff                  # Изменения с последнего sync
```

---

## 🔗 Интеграция

| Система | Как интегрируется |
|---------|-------------------|
| **Memory** | Читает mistakes для обнаружения gaps |
| **Feedback** | Читает негативный feedback для улучшений |
| **Codebase** | Сканирует для обнаружения паттернов |
| **Agents** | Уведомляет об изменениях стандартов |
