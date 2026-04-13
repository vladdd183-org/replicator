# Replicator

> Самоэволюционирующая модульная система на основе Hyper-Porto.

Может улучшать собственный код, генерировать новые репозитории, работать с существующими legacy-проектами.

## Три режима работы

- **Самоэволюция** -- система модифицирует собственный код через pipeline Intent -> Spec -> Beads -> Execute -> Verify -> Promote
- **Генерация** -- создание нового Porto-проекта с Nix-сборкой, CI/CD и выбранным набором модулей
- **Legacy** -- подключение к существующей кодовой базе и работа в привычном для неё стиле

## Архитектура

```
L0  Транспорт        Ship/Adapters/   (StoragePort, MessagingPort, IdentityPort, StatePort, ComputePort)
L1  Инфраструктура   Ship/            (Core, Parents, Providers, Infrastructure, Auth, CLI)
L2  Рантайм          Ship/Cell/       (CellSpec, Supervisor, Capabilities)
L3  Структура кода   Containers/      (Actions, Tasks, Queries, Events, Result Railway)
L4  Интеллект        AgentSection/    (COMPASS, MAKER, DSPy)
L5  Репликация       CoreSection/     (Spec, Registry, Templates, Evolution)
```

## Стек

- Python 3.13+, Litestar, Dishka (DI), Returns (Result[T,E]), anyio, Pydantic v2
- DSPy, MCP (Model Context Protocol)
- Nix (flakes), nix2container, GitHub Actions с self-hosted NixOS runners

## Документация

- [docs/architecture/](docs/architecture/) -- архитектурные решения (7 документов)
- [docs/patterns/](docs/patterns/) -- паттерны (6 документов)
- [docs/reference/](docs/reference/) -- справочники (глоссарий, стек, карта файлов)
- [specs/](specs/) -- спецификации модулей и beads
- [AGENTS.md](AGENTS.md) -- контекст для AI-агентов

## Быстрый старт

```bash
nix develop    # войти в devshell
just           # доступные команды
```

## Текущий статус

Этап подготовки: документация написана, спецификации созданы, beads декомпозированы.
Следующий шаг: реализация P0 Ship Foundation (Adapters + Cell Engine).
