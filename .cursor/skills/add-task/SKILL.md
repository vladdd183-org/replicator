---
name: add-task
description: Create new Task (atomic operation) for Hyper-Porto architecture. Tasks are stateless reusable operations. Use when the user wants to add task, create task, новый таск, добавить task, атомарная операция.
---

# Add Task (Atomic Operation)

Создание Task по архитектуре Hyper-Porto.

## Источники (ОБЯЗАТЕЛЬНО загрузи перед выполнением)

| Тип | Путь |
|-----|------|
| **Инструкция** | `agent-os/commands/add-task.md` |
| **Template** | `agent-os/templates/task.py.template` |
| **Standard** | `agent-os/standards/backend/actions-tasks.md` |

## Быстрая справка

| Правило | Описание |
|---------|----------|
| **Types** | `Task[I, O]` (async) или `SyncTask[I, O]` (CPU-bound) |
| **Stateless** | Без внутреннего состояния, чистые функции |
| **Reusable** | Может использоваться в нескольких Actions |
| **Imports** | ТОЛЬКО абсолютные от `src.` |
| **DI** | Регистрация в `Providers.py` (APP scope) |

## Типы Task

| Тип | Когда использовать | Вызов |
|-----|-------------------|-------|
| `Task[I, O]` | I/O операции (сеть, БД) | `await task.run(data)` |
| `SyncTask[I, O]` | CPU-bound (хеш, парсинг) | `await anyio.to_thread.run_sync(task.run, data)` |

## Действие

1. **Загрузи** полную инструкцию из `agent-os/commands/add-task.md`
2. **Используй** template из `agent-os/templates/task.py.template`
3. **Создай** Task файл в `Tasks/[TaskName].py`
4. **Зарегистрируй** в `Providers.py` (APP scope — stateless)

## Именование

| Операция | Паттерн | Пример |
|----------|---------|--------|
| Transform | `{Verb}{Noun}Task` | `HashPasswordTask` |
| Generate | `Generate{Noun}Task` | `GenerateTokenTask` |
| Send | `Send{Noun}Task` | `SendEmailTask` |
| Validate | `Validate{Noun}Task` | `ValidateAddressTask` |
