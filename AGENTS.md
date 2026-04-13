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

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd dolt push
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
