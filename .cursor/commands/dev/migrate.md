# /migrate — Управление миграциями

Работа с Piccolo ORM миграциями.

## Источники

- Skill: `.cursor/skills/piccolo-migration/SKILL.md`
- Docs: <https://piccolo-orm.com/docs/>

## Синтаксис

```
/migrate <command> [<app>] [options]
```

## Команды

### Создание миграции

```
/migrate new <app> [--auto]
```

Примеры:
```
/migrate new user --auto      # Автоматическая миграция
/migrate new user             # Пустая миграция
```

### Применение миграций

```
/migrate run [<app>]
```

Примеры:
```
/migrate run              # Все миграции
/migrate run user         # Только user app
```

### Статус миграций

```
/migrate status
```

### Откат миграции

```
/migrate rollback <app>
```

## Piccolo команды

```bash
# Создать автомиграцию
piccolo migrations new user --auto

# Применить миграции
piccolo migrations forwards all
piccolo migrations forwards user

# Проверить статус
piccolo migrations check

# Откатить
piccolo migrations backwards user
```

## Workflow изменения модели

1. Измени Model в `Models/<Entity>.py`
2. `/migrate new <app> --auto`
3. Проверь сгенерированную миграцию
4. `/migrate run <app>`
5. Проверь БД

## Важно

- Всегда проверяй автосгенерированные миграции
- Для rename column используй ручную миграцию
- Делай бэкап перед production миграциями
