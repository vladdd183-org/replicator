# /guide — Интерактивный гайд

Навигация по Agent OS и Hyper-Porto архитектуре.

## Источники данных

- Основной гайд: `agent-os/commands/guide.md`
- Стандарты: `agent-os/standards/`
- Workflows: `agent-os/workflows/`
- Troubleshooting: `agent-os/troubleshooting/`
- Сленг: `agent-os/slang/dictionary.md`

## Обработка запроса

| Запрос | Действие |
|--------|----------|
| `/guide` | Общий обзор системы |
| `/guide start` | С чего начать новичку |
| `/guide architecture` | Архитектура Hyper-Porto |
| `/guide pipelines` | Основные рабочие процессы |
| `/guide components` | Компоненты системы |
| `/guide commands` | Все доступные команды |
| `/guide cursor-ai` | **Rules, Skills, Subagents, Commands** — Cursor AI компоненты |
| `/guide troubleshoot` | Как решать проблемы |

## Доступные команды

### Dev команды (`.cursor/commands/dev/`)

| Команда | Описание |
|---------|----------|
| `dev/guide` | Этот гайд |
| `dev/slang` | Словарь сленга разработчика |
| **Создание компонентов** | |
| `dev/create-module` | Создать новый Container (модуль) |
| `dev/add-action` | Создать Action (Use Case) |
| `dev/add-task` | Создать Task (атомарная операция) |
| `dev/add-query` | Создать Query (CQRS Read) |
| `dev/add-endpoint` | Добавить REST endpoint |
| `dev/add-event` | Создать Domain Event + Listener |
| `dev/add-graphql` | Создать GraphQL Types/Resolvers |
| `dev/add-ws` | Создать WebSocket handler |
| `dev/add-worker` | Создать Background Worker Task |
| `dev/generate-crud` | Полный CRUD для сущности |
| **Утилиты** | |
| `dev/migrate` | Piccolo миграции |
| `dev/test` | Запуск тестов |
| `dev/validate` | Валидация кода |

### Agent OS команды (`.cursor/commands/agent-os/`)

| Команда | Описание |
|---------|----------|
| `agent-os/analyze-project` | Анализ проекта |
| `agent-os/plan-product` | Планирование продукта |
| `agent-os/shape-spec` | Формирование спецификации |
| `agent-os/write-spec` | Написание спецификации |
| `agent-os/create-tasks` | Создание задач |
| `agent-os/implement-tasks` | Имплементация задач |
| `agent-os/write-tests` | Написание тестов |

## Быстрый старт

### Новичок в проекте?
```
/guide start
→ Загрузи agent-os/commands/guide.md секцию "С чего начать"
```

### Создать модуль?
```
dev/create-module OrderModule
→ Создаст структуру Container
```

### Не понимаешь сленг?
```
dev/slang экшн
→ Найдёт значение в agent-os/slang/dictionary.md
```

### Проблема с кодом?
```
/guide troubleshoot
→ Покажет troubleshooting гайды
```

## Ресурсы Agent OS

| Ресурс | Путь |
|--------|------|
| Стандарты | `agent-os/standards/` |
| Шаблоны | `agent-os/templates/` |
| Workflows | `agent-os/workflows/` |
| Чеклисты | `agent-os/checklists/` |
| Troubleshooting | `agent-os/troubleshooting/` |
| Сниппеты | `agent-os/snippets/` |
| Сленг | `agent-os/slang/` |
| Глоссарий | `agent-os/glossary.md` |

## Документация проекта

| Ресурс | Путь |
|--------|------|
| Философия | `docs/00-philosophy.md` |
| Архитектура | `docs/01-architecture.md` |
| Структура | `docs/02-project-structure.md` |
| Компоненты | `docs/03-components.md` |
| Result/Railway | `docs/04-result-railway.md` |
| **Cursor AI** | `docs/23-cursor-ai-components.md` |