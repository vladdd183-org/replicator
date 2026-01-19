# /validate — Валидация модуля

Проверка структуры и соответствия модуля архитектуре Hyper-Porto.

## Источники

- Skill: `.cursor/skills/review-porto/SKILL.md`
- Docs: `docs/02-project-structure.md`

## Синтаксис

```
/validate <Module> [--fix]
```

## Примеры

```
/validate UserModule
/validate OrderModule --fix
/validate всё
```

## Параметры

- `<Module>` — Название модуля или "всё" для всех модулей
- `[--fix]` — Автоматически исправить найденные проблемы

## Проверки

### Структура

- [ ] Все обязательные папки существуют
- [ ] `Models/PiccoloApp.py` существует
- [ ] `Providers.py` существует
- [ ] `Errors.py` существует

### Импорты

- [ ] Все импорты абсолютные (`from src.`)
- [ ] Нет относительных импортов (`from ....`)
- [ ] Нет кросс-модульных импортов (кроме Events)

### Компоненты

- [ ] Actions возвращают `Result[T, E]`
- [ ] DTOs наследуют Pydantic `BaseModel`
- [ ] Errors наследуют `BaseError`
- [ ] Tasks зарегистрированы в APP scope
- [ ] Actions/Queries в REQUEST scope

### Naming

- [ ] Actions: `{Verb}{Noun}Action`
- [ ] Tasks: `{Verb}{Noun}Task`
- [ ] Queries: `{Get/List}{Entity}Query`
- [ ] Errors: `{Entity/Action}Error`

## Выходной отчёт

```markdown
# Validation Report: UserModule

## ✅ Passed
- Structure: OK
- Imports: OK
- Providers: OK

## ⚠️ Warnings
- Missing docstring in CreateUserAction

## ❌ Errors
- Relative import in Tasks/HashPasswordTask.py:5

## Summary
- Passed: 15
- Warnings: 1
- Errors: 1
```
