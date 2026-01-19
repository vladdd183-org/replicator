# /test — Запуск тестов

Запуск pytest тестов для модуля или всего проекта.

## Источники

- Skill: `.cursor/skills/setup-tests/SKILL.md`

## Синтаксис

```
/test [<Module>] [--coverage] [--verbose] [--failed]
```

## Примеры

```
/test
/test UserModule
/test UserModule --coverage
/test --failed
/test OrderModule --verbose
```

## Параметры

- `[<Module>]` — Модуль для тестирования (опционально, по умолчанию все)
- `[--coverage]` — Показать coverage report
- `[--verbose]` — Подробный вывод
- `[--failed]` — Запустить только упавшие тесты

## Команды

```bash
# Все тесты
pytest

# Конкретный модуль
pytest tests/unit/Containers/AppSection/UserModule/

# С покрытием
pytest --cov=src --cov-report=term-missing

# Только упавшие
pytest --lf

# Verbose
pytest -v
```

## Структура тестов

```
tests/
├── conftest.py                    # Fixtures
├── unit/                          # Unit тесты
│   └── Containers/
│       └── AppSection/
│           └── UserModule/
│               ├── test_actions.py
│               ├── test_tasks.py
│               └── test_queries.py
├── integration/                   # Integration тесты
└── e2e/                          # E2E API тесты
```

## Минимальное покрытие

- Actions: 80%+
- Tasks: 90%+
- Queries: 70%+
