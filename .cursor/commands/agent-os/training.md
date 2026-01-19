# Training — Обучение

Интерактивное обучение архитектуре Hyper-Porto через туториалы и симуляции.

## Когда использовать

- Для изучения Hyper-Porto архитектуры
- Для прохождения туториалов по компонентам
- Для симуляции реальных задач
- Для отслеживания прогресса обучения

## Синтаксис

```
/agent-os/training [действие] [параметр]
```

## Доступные действия

| Действие | Описание |
|----------|----------|
| `start` | Начать обучение (интерактивный выбор) |
| `tutorial {name}` | Запустить конкретный туториал |
| `simulation {name}` | Запустить симуляцию задачи |
| `progress` | Показать прогресс обучения |
| `list tutorials` | Список доступных туториалов |
| `list simulations` | Список доступных симуляций |
| `reset` | Сбросить прогресс |

## Примеры использования

### Начать обучение

```
/agent-os/training start
```

Покажет интерактивное меню:
1. Выбор уровня (Beginner / Intermediate / Advanced)
2. Выбор темы
3. Запуск первого урока

### Запустить туториал

```
/agent-os/training tutorial actions
```

Запустит пошаговый туториал по Actions:
1. Теория с примерами
2. Практические задания
3. Проверка понимания

### Запустить симуляцию

```
/agent-os/training simulation create-module
```

Запустит симуляцию реальной задачи:
1. Постановка задачи
2. Подсказки при необходимости
3. Review результата
4. Фидбек и рекомендации

### Показать прогресс

```
/agent-os/training progress
```

Покажет:
- Пройденные туториалы
- Успешные симуляции
- Рекомендации следующих шагов

## Доступные туториалы

### Beginner Level

| ID | Название | Описание |
|----|----------|----------|
| `intro` | Введение в Hyper-Porto | Философия и структура |
| `structure` | Структура проекта | Ship, Containers, Sections |
| `imports` | Правила импортов | Абсолютные импорты |
| `dto` | DTO и Pydantic | Request/Response схемы |

### Intermediate Level

| ID | Название | Описание |
|----|----------|----------|
| `actions` | Actions и Use Cases | Бизнес-логика |
| `result` | Result Pattern | Railway-oriented programming |
| `tasks` | Tasks | Атомарные операции |
| `queries` | Queries (CQRS) | Read-операции |
| `repository` | Repository Pattern | Работа с данными |
| `uow` | Unit of Work | Транзакции и события |
| `di` | Dependency Injection | Dishka DI |

### Advanced Level

| ID | Название | Описание |
|----|----------|----------|
| `events` | Domain Events | События между модулями |
| `graphql` | GraphQL Resolvers | Strawberry интеграция |
| `websocket` | WebSocket | Real-time |
| `workers` | Background Tasks | TaskIQ |
| `testing` | Testing | Pytest + моки |

## Доступные симуляции

| ID | Название | Сложность | Время |
|----|----------|-----------|-------|
| `create-action` | Создать Action | Easy | 10 мин |
| `create-module` | Создать модуль | Medium | 30 мин |
| `add-endpoint` | Добавить endpoint | Easy | 15 мин |
| `implement-feature` | Реализовать фичу | Medium | 45 мин |
| `refactor-to-cqrs` | Рефакторинг в CQRS | Hard | 60 мин |
| `debug-di` | Отладка DI проблем | Medium | 20 мин |
| `add-graphql` | Добавить GraphQL | Medium | 30 мин |

## Формат вывода

### Start

```
🎓 Hyper-Porto Training

Добро пожаловать в обучение!

Выберите уровень:
1. 🌱 Beginner — Основы архитектуры
2. 🌿 Intermediate — Компоненты и паттерны
3. 🌳 Advanced — Продвинутые темы

Ваш текущий прогресс:
- Beginner: 100% ✅
- Intermediate: 60% 🔄
- Advanced: 0%

Рекомендуем: tutorial queries
```

### Tutorial

```
📘 Tutorial: Actions и Use Cases

## Урок 1/5: Что такое Action

Action — это Use Case, точка входа в бизнес-логику.

### Правила:
- ВСЕГДА возвращает `Result[T, E]`
- Может вызывать Tasks, другие Actions, Repository
- Оркестрирует бизнес-логику

### Пример:

```python
@dataclass
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    hash_password: HashPasswordTask
    uow: UserUnitOfWork

    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        ...
        return Success(user)
```

---

[Enter] Далее | [b] Назад | [q] Выход | [p] Практика
```

### Simulation

```
🎮 Simulation: Создать Action

## Задача

Создайте Action `UpdateUserEmailAction`, который:
1. Проверяет, что пользователь существует
2. Проверяет уникальность нового email
3. Обновляет email
4. Публикует событие UserEmailUpdated

## Подсказки

💡 Нажмите [h] для подсказки
📚 Нажмите [d] для документации

## Ваш код

[Начните вводить или используйте skill create-action]

---

Время: 10:00 | Сложность: Easy | Попытка: 1
```

### Progress

```
📊 Training Progress

## Completed

✅ intro — Введение в Hyper-Porto
✅ structure — Структура проекта
✅ imports — Правила импортов
✅ dto — DTO и Pydantic
✅ actions — Actions и Use Cases
✅ result — Result Pattern

## In Progress

🔄 tasks — Tasks (60%)
   Осталось: 2 урока

## Recommended Next

1. Завершить `tasks`
2. Начать `queries`
3. Симуляция `create-action`

## Stats

| Уровень | Прогресс |
|---------|----------|
| Beginner | 100% ✅ |
| Intermediate | 60% 🔄 |
| Advanced | 0% |

Общий прогресс: 47%
```

## Источники материалов

Туториалы используют:
- `docs/` — документация проекта
- `agent-os/standards/` — стандарты
- `agent-os/snippets/` — примеры кода
- `agent-os/templates/` — шаблоны
- `foxdocs/LitestarPortoShowcase-main/` — рабочий пример

## Интеграция с другими системами

| Система | Интеграция |
|---------|------------|
| **Memory** | Сохраняет прогресс и сложные места |
| **Knowledge** | Подгружает документацию |
| **Feedback** | Собирает оценку туториалов |
| **Standards** | Проверяет код на соответствие |

## Настройка

Обучение использует материалы из:
- `agent-os/standards/` — правила
- `agent-os/templates/` — шаблоны
- `agent-os/checklists/` — чеклисты
- `docs/` — теория

## Будущие возможности

- [ ] Интерактивные квизы
- [ ] Gamification (достижения)
- [ ] Адаптивное обучение
- [ ] Pair programming mode
