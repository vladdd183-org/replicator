# /deps — Управление зависимостями

Проверка и управление Python зависимостями проекта.

## Источники

- Agent: `.cursor/agents/dependency-updater.md`

## Синтаксис

```
/deps <command> [options]
```

## Команды

### Проверка устаревших

```
/deps check
```

Выводит список устаревших пакетов.

### Проверка безопасности

```
/deps security
```

Сканирует на уязвимости (pip-audit, safety).

### Обновление

```
/deps update [<package>]
```

Примеры:
```
/deps update              # Все пакеты
/deps update litestar     # Конкретный пакет
```

### Добавление

```
/deps add <package> [--dev]
```

Примеры:
```
/deps add httpx
/deps add pytest --dev
```

## UV команды

```bash
# Проверить устаревшие
# UV не имеет встроенного --outdated, используй pip-audit или вручную:
uv pip list  # Показать установленные версии
uv run pip list --outdated  # Через pip внутри venv

# Обновить все зависимости
uv lock --upgrade && uv sync

# Обновить конкретный пакет
uv lock --upgrade-package litestar && uv sync

# Добавить зависимость
uv add httpx

# Добавить dev зависимость
uv add --dev pytest

# Security scan
uv run pip-audit
uv run safety check
```

## Hyper-Porto Core Dependencies

| Пакет | Назначение | Версия |
|-------|------------|--------|
| litestar | Web framework | ^2.6 |
| piccolo | ORM | ^1.0 |
| dishka | DI | ^1.0 |
| returns | Result type | ^0.22 |
| anyio | Async | ^4.0 |
| pydantic | Validation | ^2.5 |
| strawberry-graphql | GraphQL | ^0.220 |
| taskiq | Background jobs | ^0.11 |

## Безопасные обновления

1. Patch версии (x.x.PATCH) — безопасно
2. Minor версии (x.MINOR.x) — проверь changelog
3. Major версии (MAJOR.x.x) — читай migration guide
