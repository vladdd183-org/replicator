# 🤝 Human-AI Collaboration

> **Связанные документы:**
> - [Architecture Overview](overview.md)
> - [Concepts: AI Integration](../concepts/ai-integration.md)
> - [Reference: Tools Comparison](../reference/tools-comparison.md)

---

## 1. Что такое Human-AI Collaboration

### 1.1 Определение

**Human-AI Collaboration** — это не просто "AI помогает человеку". Это **совместная работа**, где:

- Люди и AI имеют **разные сильные стороны**
- Каждый делает то, что **лучше получается**
- Результат **лучше**, чем мог бы достичь каждый в отдельности

### 1.2 Эволюция подходов

```
┌─────────────────────────────────────────────────────────────────┐
│              ЭВОЛЮЦИЯ HUMAN-AI ВЗАИМОДЕЙСТВИЯ                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ЭТАП 1: AI как ИНСТРУМЕНТ (2010-2020)                         │
│  ├── Человек командует, AI выполняет                           │
│  └── Пример: "Найди файлы с ошибками"                          │
│                                                                 │
│  ЭТАП 2: AI как АССИСТЕНТ (2020-2023)                          │
│  ├── AI предлагает, человек решает                             │
│  └── Пример: GitHub Copilot                                     │
│                                                                 │
│  ЭТАП 3: AI как КОЛЛЕГА (2024-2026)                            │
│  ├── Двустороннее взаимодействие                               │
│  └── Пример: CrewAI, Co-Gym                                    │
│                                                                 │
│  ЭТАП 4: AI как TEAMMATE (2026+)                                │
│  ├── Полноценный член команды                                   │
│  ├── Shared mental models                                       │
│  └── Пример: Agentic Organizations                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Ключевая статистика

| Метрика | Результат |
|---------|-----------|
| **Human-AI vs лучший по отдельности** | -0.23 (в среднем хуже!) |
| **Creative tasks** | Значительно лучше с AI |
| **Decision-making tasks** | Хуже с AI |
| **Когда AI > Human изначально** | Collaboration помогает |
| **Когда Human > AI изначально** | Collaboration вредит |

**Вывод:** Коллаборация — не silver bullet. Нужен правильный дизайн под задачи.

---

## 2. Три Mental Models

### 2.1 Что такое Mental Models

**Mental Model** — внутреннее понимание человеком того, как что-то работает. В Human-AI контексте — **как AI думает и работает**.

### 2.2 Три необходимых модели

```
┌─────────────────────────────────────────────────────────────────┐
│              ТРИ MENTAL MODELS                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1️⃣  DOMAIN MENTAL MODEL                                        │
│      "Как работает предметная область"                          │
│      ├── Бизнес-логика задачи                                   │
│      ├── Контекст и ограничения                                 │
│      ├── Критерии успеха                                        │
│      └── Edge cases                                             │
│                                                                 │
│  2️⃣  INFORMATION PROCESSING MODEL                               │
│      "Как AI обрабатывает информацию"                           │
│      ├── Как AI интерпретирует input                            │
│      ├── Какие данные AI использует                             │
│      ├── Где AI может ошибаться                                 │
│      └── Чувствительность к формулировке промпта                │
│                                                                 │
│  3️⃣  COMPLEMENTARITY-AWARENESS MODEL                            │
│      "Кто в чём силён"                                          │
│      ├── В чём AI лучше меня                                    │
│      ├── В чём я лучше AI                                       │
│      ├── Где нужна коллаборация                                 │
│      └── Где лучше работать порознь                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Как развивать Mental Models

| Механизм | Описание |
|----------|----------|
| **Data Contextualization** | AI показывает контекст решения, не только результат |
| **Reasoning Transparency** | AI объясняет КАК пришёл к выводу |
| **Performance Feedback** | Регулярная обратная связь о качестве AI |

---

## 3. Complementarity: Кто что делает лучше

### 3.1 Матрица распределения

```
┌─────────────────────────────────────────────────────────────────┐
│              КОМУ КАКИЕ ЗАДАЧИ                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  👤 ЧЕЛОВЕК ЛУЧШЕ:                                              │
│  ├── 🎨 Creative ideation (начальная генерация идей)           │
│  ├── 🤔 Ethical judgment (этические решения)                   │
│  ├── 😊 Emotional intelligence                                 │
│  ├── 🔮 Novel situations (принципиально новые)                 │
│  ├── 🎯 Strategic thinking (долгосрочная стратегия)            │
│  └── 🧩 Context integration (неявный контекст)                 │
│                                                                 │
│  🤖 AI ЛУЧШЕ:                                                   │
│  ├── 📊 Pattern recognition (паттерны в данных)                │
│  ├── 🔄 Repetitive tasks (повторяющиеся операции)              │
│  ├── 📈 Data processing (большие объёмы)                       │
│  ├── ⚡ Speed-critical tasks (скорость важна)                  │
│  ├── 🔍 Consistency checking                                   │
│  └── 📝 Summarization                                          │
│                                                                 │
│  🤝 ЛУЧШЕ ВМЕСТЕ:                                               │
│  ├── Content creation (AI draft → Human refine)                │
│  ├── Bug hunting (AI finds → Human verifies)                   │
│  ├── Code review (AI checks → Human approves)                  │
│  ├── Research (AI gathers → Human synthesizes)                 │
│  └── Analysis (AI processes → Human interprets)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Quick Reference

| Тип задачи | AI | Human | Together | Почему |
|------------|:---:|:------:|:--------:|--------|
| **Поиск информации** | ✅ | | | AI быстрее |
| **Summarization** | ✅ | | | AI справится |
| **Boilerplate code** | ✅ | | | Рутина |
| **Creative ideation** | | ✅ | | Human лучше в novelty |
| **Ethical decisions** | | ✅ | | Values & judgment |
| **Strategic planning** | | ✅ | | Context & vision |
| **Content creation** | | | ✅ | AI draft + Human polish |
| **Code review** | | | ✅ | AI finds + Human verifies |

---

## 4. Компоненты системы

### 4.1 Shared Context

**Shared Context** — общее информационное пространство для людей и AI.

```yaml
# Пример структуры
project:
  name: "MyApp Backend"
  current_sprint: "Sprint-42"
  deadline: "2026-02-15"

active_work:
  - issue: "API-123"
    title: "Implement user search"
    assignee: "@alice"
    status: "In Review"
    blockers: []

recent_decisions:
  - id: "ADR-045"
    title: "Use Redis for caching"
    rationale: "Performance requirements exceed PostgreSQL capabilities"

team_availability:
  alice: "Online, focused work until 14:00"
  bob: "In meeting until 11:00"
  ai_agent_1: "Available, 3 tasks in queue"
```

### 4.2 Dynamic Task Allocation

**Факторы распределения:**

```
1️⃣  TASK CHARACTERISTICS
    ├── Тип: creative / analytical / routine
    ├── Complexity: low / medium / high
    ├── Risk: reversible / irreversible
    └── Context needed: low / high

2️⃣  AGENT CAPABILITIES
    ├── Human: expertise, availability, workload
    ├── AI: accuracy on this task type, speed
    └── Historical performance data

3️⃣  CURRENT STATE
    ├── Urgency: deadline pressure
    ├── Dependencies: blocked by something?
    └── Resource availability
```

### 4.3 Decision Tree

```
Новая задача
     │
     ▼
┌─────────────────┐
│ Требует этики?  │─── ДА ──→ 👤 HUMAN
└────────┬────────┘
         │ НЕТ
         ▼
┌─────────────────┐
│ Новая ситуация? │─── ДА ──→ 👤 HUMAN
└────────┬────────┘
         │ НЕТ
         ▼
┌─────────────────┐
│ High risk +     │─── ДА ──→ 👤 HUMAN (или 🤝 с review)
│ irreversible?   │
└────────┬────────┘
         │ НЕТ
         ▼
┌─────────────────┐
│ AI accuracy     │─── >90% ──→ 🤖 AI
│ на этом типе?   │
└────────┬────────┘
         │ <90%
         ▼
     🤝 COLLABORATIVE
```

---

## 5. Trust Calibration

### 5.1 Спектр доверия

| Тип | Описание | Проблема |
|-----|----------|----------|
| **Under-trust** | Игнорирование AI suggestions | Потеря value от AI |
| **Over-trust** | Слепое принятие всего от AI | Пропущенные ошибки |
| **Calibrated** | Доверие соответствует надёжности | Оптимально |

### 5.2 Confidence Scores

```python
class AIResponse:
    content: str           # Основной ответ
    confidence: float      # 0.0 - 1.0
    reasoning: list[str]   # Шаги рассуждения
    sources: list[str]     # Источники данных
    uncertainties: list[str]  # Области неуверенности
    suggested_verification: str | None  # Что проверить
```

### 5.3 Правила по confidence

| Confidence | Визуал | Действие |
|------------|--------|----------|
| **95-100%** | 🟢🟢🟢 | Можно принять сразу |
| **85-95%** | 🟢🟢 | Quick review |
| **70-85%** | 🟡🟡 | Review рекомендуется |
| **50-70%** | 🟡 | Review обязателен |
| **<50%** | 🔴 | Human decision |

---

## 6. Паттерны взаимодействия

### 6.1 AI Draft → Human Refine

**Когда:** Создание контента, кода, документации

```
1. Human: Задаёт направление
   "Напиши функцию для валидации email..."

2. AI: Генерирует черновик
   [Код + тесты + документация]

3. Human: Ревьюит и уточняет
   "Добавь кеширование MX lookups"

4. AI: Итерирует
   [Обновлённый код]

5. Human: Финализирует
   [Edge cases из опыта]

РЕЗУЛЬТАТ:
├── AI: 70% работы (boilerplate)
├── Human: 30% работы (judgment)
└── Качество: Выше чем каждый по отдельности
```

### 6.2 AI Monitor → Human Decide

**Когда:** Мониторинг, alerting, anomaly detection

```
AI Agent (24/7 мониторинг)
         │
         │ Anomaly detected
         ▼
ALERT to Human:
"Обнаружена аномалия:
 - Что: Error rate вырос с 0.1% до 5%
 - Когда: Последние 15 минут
 - Возможные причины:
   1. Deploy 30 мин назад
   2. Spike в трафике (+200%)
 - Confidence: 78%
 - Suggested actions:
   □ Rollback deploy
   □ Scale up instances"
         │
         ▼
Human: Принимает решение
```

### 6.3 Human Lead → AI Execute

**Когда:** Стратегические задачи с рутинным исполнением

```
1. Human (Strategy):
   "Переименовать UserService в UserRepository во всём проекте"

2. AI (Execution):
   ├── Находит все 47 файлов
   ├── Генерирует план изменений
   ├── Показывает Human для approval
   ├── Выполняет изменения
   ├── Запускает тесты
   └── Создаёт PR

3. Human (Review):
   ├── Проверяет ключевые изменения
   └── Approves & Merge

РЕЗУЛЬТАТ:
├── Human time: 15 мин (strategy + review)
├── Без AI: 2-3 часа manual work
└── Экономия: ~90%
```

---

## 7. Escalation & Handoff

### 7.1 Триггеры эскалации

| Категория | Триггер |
|-----------|---------|
| **🔴 Немедленная** | Customer requests human, negative sentiment, security/compliance |
| **🟡 По confidence** | Confidence < 60%, нет данных, conflicting sources |
| **🟠 По pattern** | Loop >3 попыток, customer повторяет вопрос, timeout |

### 7.2 Формат handoff

```
При передаче Human'у AI предоставляет:

1. CONTEXT SUMMARY
   "User @alice спрашивает о проблеме с billing..."

2. ACTIONS TAKEN
   "Я проверил: ✓ Payment history, ✓ Subscription status"

3. SUGGESTED NEXT STEPS
   "Рекомендации: □ Проверить Stripe logs..."

4. ESCALATION REASON
   "Причина: Financial decision требует human approval"

5. CUSTOMER EXPECTATION
   "Клиент ожидает: Решение в течение 24 часов"
```

---

## 8. Cognitive Load Management

### 8.1 Проблема overload

**AI генерирует информацию быстрее, чем человек может обработать.**

Симптомы:
- Перестаёт читать внимательно
- "Принимаю всё не глядя"
- Усталость от уведомлений
- Атрофия критического мышления

### 8.2 Стратегии снижения

| Стратегия | Описание |
|-----------|----------|
| **Progressive Disclosure** | Показывать уровнями: Summary → Details → Deep dive |
| **Smart Notifications** | Группировать и приоритизировать |
| **Actionable Outputs** | Предлагать действия, не просто информацию |
| **Context-Aware Interruptions** | Прерывать только когда важно |
| **Focus Protection** | Режимы: Deep Work / Collaboration / Review |

### 8.3 Preventing skill atrophy

- **Deliberate Practice** — иногда делать без AI
- **Understanding over Accepting** — требовать объяснений
- **Verification Habit** — spot-check даже high confidence
- **Teaching AI** — формулировать почему исправляешь
- **Novel Challenges** — браться за задачи где AI плох

---

## 9. Рекомендации по внедрению

### 9.1 Фазы внедрения

| Фаза | Действия |
|------|----------|
| **Подготовка (1-2 нед)** | Выбрать use cases, инструменты, метрики |
| **Пилот (3-6 нед)** | Запустить, собирать feedback, итерировать |
| **Масштабирование (7-12 нед)** | Расширить use cases, внедрить feedback loops |
| **Ongoing** | Weekly reviews, monthly trends, quarterly improvements |

### 9.2 Метрики

| Метрика | Цель | Как измерять |
|---------|------|--------------|
| Time savings | -30% на routine | Before/after |
| AI accuracy | >85% delegated tasks | Acceptance rate |
| Human satisfaction | >8/10 | Weekly survey |
| Error rate | ≤ baseline | Bug tracking |
| Skill retention | Stable | Periodic assessments |

---

## 10. Навигация

| Следующий документ | Тема |
|--------------------|------|
| → [../concepts/ai-integration.md](../concepts/ai-integration.md) | Детали AI интеграции |
| → [../reference/tools-comparison.md](../reference/tools-comparison.md) | Сравнение инструментов |

---

*Источник: Human-AI-Collaboration-Guide.md*
