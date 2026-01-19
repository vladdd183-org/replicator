# 🔄 Feedback Loop System

> Автоматический сбор, анализ и применение обратной связи для улучшения агентов

**Версия:** 1.0.0  
**Дата:** 2026-01-19

---

## 🎯 Цель

Замкнутый цикл улучшения:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEEDBACK LOOP                                 │
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│   │  COLLECT │───▶│ ANALYZE  │───▶│  LEARN   │───▶│  APPLY   │ │
│   │          │    │          │    │          │    │          │ │
│   │ Собрать  │    │ Найти    │    │ Создать  │    │ Улучшить │ │
│   │ фидбек   │    │ паттерны │    │ insights │    │ агентов  │ │
│   └──────────┘    └──────────┘    └──────────┘    └──────────┘ │
│        ▲                                                 │      │
│        └─────────────────────────────────────────────────┘      │
│                         Continuous Loop                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура

```
agent-os/feedback/
├── README.md                    # Этот файл
├── config.yml                   # Конфигурация системы
│
├── collection/                  # ═══ Сбор фидбека ═══
│   ├── triggers.yml             # Когда спрашивать
│   ├── questions/               # Шаблоны вопросов
│   │   ├── after-implementation.md
│   │   ├── after-error-fix.md
│   │   ├── after-session.md
│   │   └── weekly-survey.md
│   └── responses/               # Сырые ответы
│       └── YYYY/MM/
│           └── DD-{id}.json
│
├── analysis/                    # ═══ Анализ ═══
│   ├── rules.yml                # Правила анализа
│   ├── reports/                 # Сгенерированные отчёты
│   │   ├── weekly/
│   │   └── monthly/
│   └── insights/                # Извлечённые инсайты
│       └── YYYY-MM-DD-{topic}.md
│
├── actions/                     # ═══ Действия ═══
│   ├── pending/                 # Ожидающие применения
│   │   └── action-{id}.yml
│   ├── applied/                 # Применённые
│   │   └── action-{id}.yml
│   └── rejected/                # Отклонённые
│       └── action-{id}.yml
│
└── metrics/                     # ═══ Метрики ═══
    ├── current.json             # Текущие метрики
    ├── history/                 # История
    │   └── YYYY-MM.json
    └── dashboards/              # Визуализации
        └── overview.md
```

---

## ⚙️ Конфигурация

```yaml
# config.yml
version: "1.0.0"

collection:
  # Когда автоматически запрашивать фидбек
  auto_triggers:
    after_implementation: true      # После реализации задачи
    after_error_fix: true          # После исправления ошибки
    after_session:                 # После сессии
      min_duration_minutes: 15     # Только если сессия > 15 мин
    weekly_survey:
      enabled: true
      day: friday
      time: "17:00"
  
  # Как собирать
  methods:
    inline: true                   # Вопросы в чате
    rating_widget: false           # Виджет с оценкой
    
  # Анонимность
  anonymize_comments: false

analysis:
  # Автоматический анализ
  auto_analyze:
    on_n_responses: 10             # После N ответов
    weekly: true
    
  # Пороги для действий
  thresholds:
    negative_feedback_alert: 3     # Alert после N негативных
    pattern_detection: 5           # Паттерн после N похожих
    
actions:
  # Что делать с результатами
  auto_actions:
    create_mistake_entry: true     # Создавать mistake при негативе
    update_standards: false        # Обновлять стандарты (требует approval)
    notify_user: true              # Уведомлять о трендах
    
  # Требуется ли одобрение
  require_approval:
    update_standards: true
    add_anti_pattern: true
    modify_agents: true

metrics:
  # Что отслеживать
  track:
    - satisfaction_score           # 1-5 rating
    - task_completion_rate         # % успешных задач
    - error_rate                   # % задач с ошибками
    - iteration_count              # Итераций до успеха
    - response_quality             # Качество ответов (1-5)
```

---

## 📝 Триггеры и вопросы

### After Implementation

```yaml
# triggers.yml
after_implementation:
  condition: "task_marked_complete"
  delay: "immediate"
  questions:
    - type: rating
      id: satisfaction
      text: "Насколько вы довольны результатом? (1-5)"
      scale: [1, 5]
      
    - type: binary
      id: correct
      text: "Реализация соответствует требованиям?"
      options: [yes, no]
      
    - type: optional_text
      id: comment
      text: "Комментарий (опционально):"
      
    - type: multiple_choice
      id: issues
      text: "Были ли проблемы?"
      options:
        - none: "Нет проблем"
        - wrong_approach: "Неправильный подход"
        - missing_features: "Не хватает функций"
        - code_quality: "Качество кода"
        - other: "Другое"
```

### After Error Fix

```yaml
after_error_fix:
  condition: "error_resolved"
  delay: "immediate"
  questions:
    - type: binary
      id: fixed
      text: "Ошибка исправлена?"
      
    - type: rating
      id: fix_quality
      text: "Качество исправления (1-5)"
      condition: "fixed == yes"
      
    - type: text
      id: root_cause
      text: "Что было причиной? (для обучения)"
      condition: "fixed == yes"
```

### Weekly Survey

```yaml
weekly_survey:
  schedule: "friday 17:00"
  questions:
    - type: rating
      id: overall_satisfaction
      text: "Общая удовлетворённость за неделю (1-5)"
      
    - type: multiple_choice
      id: best_aspects
      text: "Что работало лучше всего?"
      allow_multiple: true
      options:
        - code_generation: "Генерация кода"
        - debugging: "Отладка"
        - explanations: "Объяснения"
        - architecture: "Архитектурные решения"
        
    - type: multiple_choice
      id: improvement_areas
      text: "Что улучшить?"
      allow_multiple: true
      options:
        - accuracy: "Точность кода"
        - speed: "Скорость"
        - understanding: "Понимание требований"
        - conventions: "Следование конвенциям"
        
    - type: text
      id: suggestions
      text: "Предложения по улучшению:"
```

---

## 📊 Анализ и метрики

### Формат ответа

```json
{
  "id": "fb-20260119-001",
  "timestamp": "2026-01-19T14:30:00Z",
  "trigger": "after_implementation",
  "session_id": "sess-abc123",
  "task_type": "create_action",
  "module": "UserModule",
  "responses": {
    "satisfaction": 4,
    "correct": "yes",
    "comment": "",
    "issues": "none"
  },
  "context": {
    "duration_minutes": 12,
    "iterations": 1,
    "errors_encountered": 0
  }
}
```

### Метрики

```json
{
  "period": "2026-01",
  "metrics": {
    "total_feedback": 45,
    "avg_satisfaction": 4.2,
    "task_completion_rate": 0.89,
    "error_rate": 0.11,
    "avg_iterations": 1.3,
    "nps_score": 42
  },
  "by_task_type": {
    "create_action": { "avg_satisfaction": 4.5, "count": 12 },
    "debugging": { "avg_satisfaction": 3.8, "count": 8 },
    "create_module": { "avg_satisfaction": 4.1, "count": 5 }
  },
  "trends": {
    "satisfaction": "stable",
    "error_rate": "improving",
    "iterations": "improving"
  }
}
```

---

## 🎬 Действия

### Формат Action

```yaml
# actions/pending/action-001.yml
id: action-001
created: 2026-01-19T15:00:00Z
trigger: pattern_detected
priority: high

observation:
  type: repeated_negative_feedback
  pattern: "Ошибки с относительными импортами"
  occurrences: 5
  affected_modules:
    - UserModule
    - AuditModule

proposed_action:
  type: add_guardrail
  description: "Добавить проверку импортов перед генерацией"
  changes:
    - file: agent-os/guardrails/pre-generation.yml
      action: add_rule
      content: |
        - pattern: "from \\.\\."
          block: true
          message: "Относительные импорты запрещены"

status: pending_approval
approval_required: true
```

### Жизненный цикл Action

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ DETECTED │───▶│ PENDING  │───▶│ APPROVED │───▶ APPLIED
└──────────┘    └──────────┘    └──────────┘
                     │                            │
                     ▼                            ▼
                ┌──────────┐               ┌──────────┐
                │ REJECTED │               │ VERIFIED │
                └──────────┘               └──────────┘
```

---

## 🤖 Интеграция с агентами

### Сбор фидбека

После выполнения задачи агент должен:

```python
# Пример использования
feedback.collect(
    trigger="after_implementation",
    task_type="create_action",
    module="UserModule",
    context={
        "duration_minutes": 12,
        "iterations": 1,
    }
)
```

### Использование инсайтов

Перед выполнением агент проверяет:

```python
# Получить релевантные инсайты
insights = feedback.get_insights(
    task_type="create_action",
    module="UserModule"
)

# Пример инсайта
# {
#   "type": "warning",
#   "message": "В UserModule часто забывают регистрацию в Provider",
#   "recommendation": "Проверить Providers.py после создания Action"
# }
```

---

## 📈 Dashboard

```markdown
# Feedback Dashboard — 2026-01-19

## 📊 Текущие метрики

| Метрика | Значение | Тренд |
|---------|----------|-------|
| Satisfaction | 4.2/5 | ↗️ +0.3 |
| Completion Rate | 89% | ↗️ +5% |
| Error Rate | 11% | ↘️ -3% |
| Avg Iterations | 1.3 | ↘️ -0.2 |

## 🔴 Проблемные области

1. **Debugging** — satisfaction 3.8 (ниже среднего)
   - Action: Улучшить troubleshooting guides

## ✅ Успешные области

1. **Create Action** — satisfaction 4.5
2. **Create Module** — satisfaction 4.1

## 📋 Pending Actions

| ID | Описание | Priority |
|----|----------|----------|
| action-001 | Добавить guardrail для импортов | High |
```

---

## 🔗 Связанные системы

| Система | Интеграция |
|---------|------------|
| **Memory** | Записывает insights в `memory/learning/insights/` |
| **Standards Evolution** | Предлагает изменения в стандарты |
| **Agents** | Обновляет поведение агентов |
| **Training** | Использует фидбек для улучшения tutorials |

---

## 📚 Команды

```bash
# Сбор
/feedback collect              # Запросить фидбек сейчас
/feedback survey               # Запустить недельный опрос

# Просмотр
/feedback stats                # Текущие метрики
/feedback dashboard            # Полный dashboard
/feedback trends               # Тренды за месяц

# Действия
/feedback actions              # Список pending actions
/feedback approve {id}         # Одобрить action
/feedback reject {id}          # Отклонить action

# Анализ
/feedback analyze              # Запустить анализ
/feedback insights             # Показать инсайты
```
