# /write-tests — Автоматическое написание тестов

Запуск test-writer агента для создания тестов.

## Агент

- Agent: `.cursor/agents/test-writer.md`
- Skill: `.cursor/skills/setup-tests/SKILL.md`

## Синтаксис

```
/write-tests <target> [--type unit|integration|e2e]
```

## Примеры

```
/write-tests UserModule
/write-tests UserModule/Actions/CreateUserAction --type unit
/write-tests OrderModule --type integration
/write-tests api --type e2e
```

## Параметры

- `<target>` — Модуль, файл или компонент для тестирования
- `[--type]` — Тип тестов (unit, integration, e2e)

## Действие

1. Запусти test-writer агента
2. Агент анализирует код
3. Создаёт тесты в `tests/` по структуре
4. Проверяет тесты запуском pytest

## Структура вывода

```
tests/
├── unit/
│   └── Containers/AppSection/UserModule/
│       ├── test_actions.py      # Тесты Actions
│       ├── test_tasks.py        # Тесты Tasks
│       └── test_queries.py      # Тесты Queries
├── integration/
│   └── Containers/AppSection/UserModule/
│       └── test_user_flow.py    # Интеграционные тесты
└── e2e/
    └── test_user_api.py         # E2E API тесты
```

## Coverage Target

- Actions: 80%+
- Tasks: 90%+
- Queries: 70%+
- Controllers: 60%+
