# AGENTS.md -- Контекст для AI-агентов

## Проект

**Replicator** -- самоэволюционирующая модульная система. Может улучшать собственный код, генерировать новые репозитории, работать с legacy-проектами.

## Стек

- Python 3.13+, Litestar, Dishka (DI), Returns (Result[T,E]), anyio, Pydantic v2
- Piccolo ORM, DSPy, MCP
- Nix (flakes), nix2container, GitHub Actions с self-hosted NixOS runners

## Архитектура

Porto-паттерн: Ship (инфраструктура) + Containers (бизнес-модули). Расширен:
- `Ship/Adapters/` -- 5 Protocol-портов (Storage, State, Messaging, Identity, Compute)
- `Ship/Cell/` -- CellSpec, Supervisor, Capabilities
- 4 Section-а: CoreSection, AgentSection, ToolSection, KnowledgeSection

## Важные правила

1. Ship НИКОГДА не импортирует из Containers
2. Containers не импортируют друг из друга (только Events / Gateway)
3. Все Actions возвращают `Result[T, E]`
4. Адаптеры за Protocol-ами, переключаются через DI
5. Абсолютные импорты от `src/`
6. Документация и комментарии -- русский, код -- английский

## Навигация

- `docs/` -- архитектура, паттерны, справочники
- `specs/` -- спецификации модулей, beads, планы очистки/добавления
- `foxdocs/` -- копии проектов-наработок для референса
- `src/Ship/` -- инфраструктурное ядро
- `src/Containers/` -- бизнес-модули

## Текущий этап

Этап подготовки: документация написана, спецификации созданы, beads декомпозированы.
Следующий шаг: очистка от demo-модулей, затем реализация P0 Ship Foundation beads.
