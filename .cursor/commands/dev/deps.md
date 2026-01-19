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

## Poetry команды

```bash
# Проверить устаревшие
poetry show --outdated

# Обновить все
poetry update

# Обновить конкретный
poetry update litestar

# Добавить
poetry add httpx
poetry add --group dev pytest

# Security scan
pip-audit
safety check
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
