# P1 Beads: CoreSection + ToolSection

> Foundation. Ядро репликатора и базовые инструменты.

---

## CoreSection/SpecModule

### B-CORE-SPEC-001: MissionSpec и связанные модели

- **Компонент:** `Containers/CoreSection/SpecModule/Data/Schemas/`
- **Acceptance:**
  - [ ] `MissionSpec` -- Pydantic frozen model
  - [ ] `IntentType` enum (self_evolve, generate, legacy)
  - [ ] `Priority` enum (critical, high, medium, low)
  - [ ] `Formula`, `FormulaPhase` -- frozen models
  - [ ] `Molecule`, `Bead`, `BeadGraph` -- frozen models
  - [ ] `BeadType` enum (code, test, config, doc, review)
  - [ ] `Complexity` enum (trivial, simple, moderate, complex)
- **Зависимости:** P0 завершен
- **Приоритет:** P1

### B-CORE-SPEC-002: CompileSpecAction

- **Компонент:** `Containers/CoreSection/SpecModule/Actions/CompileSpecAction.py`
- **Acceptance:**
  - [ ] `CompileSpecAction(Action[str, MissionSpec, SpecError])`
  - [ ] Принимает текстовый intent, возвращает MissionSpec
  - [ ] Использует DSPy Signature или LLM API для компиляции
  - [ ] При failure возвращает `SpecCompilationError`
  - [ ] Генерирует событие `SpecCompiled`
- **Зависимости:** B-CORE-SPEC-001
- **Приоритет:** P1

### B-CORE-SPEC-003: ValidateSpecAction

- **Компонент:** `Containers/CoreSection/SpecModule/Actions/ValidateSpecAction.py`
- **Acceptance:**
  - [ ] Валидирует MissionSpec: acceptance_criteria не пусты, target корректен
  - [ ] Возвращает `Result[MissionSpec, SpecError]`
- **Зависимости:** B-CORE-SPEC-001
- **Приоритет:** P1

### B-CORE-SPEC-004: SpecModule Providers + Events + Errors

- **Компонент:** `Containers/CoreSection/SpecModule/{Events,Errors,Providers}.py`
- **Acceptance:**
  - [ ] Events: SpecCompiled, SpecValidated, FormulaInstantiated
  - [ ] Errors: SpecCompilationError, SpecValidationError, FormulaNotFoundError
  - [ ] Providers: DI для Actions, Tasks
- **Зависимости:** B-CORE-SPEC-002, B-CORE-SPEC-003
- **Приоритет:** P1

---

## CoreSection/CellRegistryModule

### B-CORE-REG-001: InMemoryCellRegistry

- **Компонент:** `Containers/CoreSection/CellRegistryModule/Data/Repositories/`
- **Acceptance:**
  - [ ] Реализует `CellRegistryPort` in-memory
  - [ ] Хранит CellSpec-ы в dict
  - [ ] Поддерживает версионирование (get с version)
  - [ ] get_history возвращает цепочку parent_spec_hash
- **Зависимости:** B-SHIP-CELL-001, B-SHIP-CELL-003
- **Приоритет:** P1

### B-CORE-REG-002: RegisterCellAction

- **Компонент:** `Containers/CoreSection/CellRegistryModule/Actions/RegisterCellAction.py`
- **Acceptance:**
  - [ ] Регистрирует CellSpec в реестре
  - [ ] Проверяет уникальность name+version
  - [ ] Вычисляет spec_hash если не задан
  - [ ] Генерирует событие CellRegistered
- **Зависимости:** B-CORE-REG-001
- **Приоритет:** P1

---

## CoreSection/TemplateModule

### B-CORE-TMPL-001: Jinja2 шаблоны Porto-компонентов

- **Компонент:** `Containers/CoreSection/TemplateModule/Data/Templates/`
- **Acceptance:**
  - [ ] Шаблон Action (с Result, type annotations, docstring)
  - [ ] Шаблон Task / SyncTask
  - [ ] Шаблон Query
  - [ ] Шаблон Module (полная структура папок + файлы)
  - [ ] Шаблон Providers.py
  - [ ] Шаблон Events.py + Errors.py
- **Зависимости:** P0 завершен
- **Приоритет:** P1

### B-CORE-TMPL-002: GenerateModuleAction

- **Компонент:** `Containers/CoreSection/TemplateModule/Actions/GenerateModuleAction.py`
- **Acceptance:**
  - [ ] Принимает ModuleConfig (name, section, actions, tasks, queries)
  - [ ] Генерирует полную структуру Porto-модуля
  - [ ] Возвращает Result[GeneratedModule, TemplateError]
- **Зависимости:** B-CORE-TMPL-001
- **Приоритет:** P1

---

## ToolSection/MCPClientModule

### B-TOOL-MCP-001: MCP Client базовый

- **Компонент:** `Containers/ToolSection/MCPClientModule/`
- **Acceptance:**
  - [ ] Подключение к MCP-серверу через stdio
  - [ ] `CallToolAction` -- вызов инструмента с аргументами
  - [ ] `ListToolsAction` -- список доступных инструментов
  - [ ] Обработка ошибок: таймаут, невалидные аргументы, сервер недоступен
- **Зависимости:** P0 завершен
- **Приоритет:** P1

---

## ToolSection/GitModule

### B-TOOL-GIT-001: Git базовые операции

- **Компонент:** `Containers/ToolSection/GitModule/`
- **Acceptance:**
  - [ ] `CloneRepoAction` через subprocess (git clone)
  - [ ] `CreateBranchAction` (git checkout -b)
  - [ ] `CommitChangesAction` (git add + git commit)
  - [ ] `CreateWorktreeAction` (git worktree add)
  - [ ] `CheckDiffTask` (git diff --stat)
  - [ ] Все через anyio.run_process, не Python git-библиотеки
- **Зависимости:** P0 завершен
- **Приоритет:** P1

### B-TOOL-GIT-002: Git PR операции

- **Компонент:** `Containers/ToolSection/GitModule/Actions/CreatePRAction.py`
- **Acceptance:**
  - [ ] Создание PR через `gh pr create`
  - [ ] Push через `git push`
  - [ ] Возвращает PRInfo (url, number, title)
- **Зависимости:** B-TOOL-GIT-001
- **Приоритет:** P1

---

## ToolSection/NixModule

### B-TOOL-NIX-001: Nix build базовый

- **Компонент:** `Containers/ToolSection/NixModule/`
- **Acceptance:**
  - [ ] `BuildAction` -- `nix build .#output` через subprocess
  - [ ] Graceful degradation если Nix не установлен
  - [ ] BuildResult с path, duration, success/failure
  - [ ] `EvalFlakeTask` -- `nix flake show` для метаданных
- **Зависимости:** P0 завершен
- **Приоритет:** P1

---

## Сводка P1

| Bead | Компонент | Зависит от |
|---|---|---|
| B-CORE-SPEC-001 | SpecModule/Schemas | P0 |
| B-CORE-SPEC-002 | CompileSpecAction | SPEC-001 |
| B-CORE-SPEC-003 | ValidateSpecAction | SPEC-001 |
| B-CORE-SPEC-004 | SpecModule Events/Errors/Providers | SPEC-002, SPEC-003 |
| B-CORE-REG-001 | InMemoryCellRegistry | B-SHIP-CELL-001, CELL-003 |
| B-CORE-REG-002 | RegisterCellAction | REG-001 |
| B-CORE-TMPL-001 | Jinja2 Templates | P0 |
| B-CORE-TMPL-002 | GenerateModuleAction | TMPL-001 |
| B-TOOL-MCP-001 | MCP Client | P0 |
| B-TOOL-GIT-001 | Git базовые | P0 |
| B-TOOL-GIT-002 | Git PR | GIT-001 |
| B-TOOL-NIX-001 | Nix build | P0 |

**Итого: 12 Beads, P1 foundation. Параллелизм: CoreSection и ToolSection могут идти параллельно.**
