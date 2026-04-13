# Спецификация: ToolSection

> Инструменты: MCP-клиент, Git, Nix, CI/CD.

---

## Модули

### 1. MCPClientModule -- MCP tool integration

**Назначение:** стандартный интерфейс для подключения инструментов через Model Context Protocol.

**Actions:**
- `CallToolAction(server: str, tool: str, arguments: dict) -> Result[ToolResult, MCPError]`
- `ListToolsAction(server: str) -> Result[list[ToolDescriptor], MCPError]`
- `ConnectServerAction(config: MCPServerConfig) -> Result[MCPConnection, MCPError]`

**Tasks:**
- `SerializeArgumentsTask(args: dict, schema: dict) -> dict` -- валидация и сериализация аргументов
- `ParseToolResultTask(raw: Any) -> ToolResult` -- парсинг результата

**Queries:**
- `GetServerStatusQuery(server: str) -> ServerStatus` -- статус подключения к серверу
- `ListServersQuery() -> list[MCPServerInfo]` -- список подключенных серверов

**Events:** `ToolCalled`, `ToolFailed`, `ServerConnected`, `ServerDisconnected`
**Errors:** `MCPConnectionError`, `ToolNotFoundError`, `ToolExecutionError`, `ArgumentValidationError`

---

### 2. GitModule -- Git operations

**Назначение:** управление Git-операциями для самоэволюции и генерации.

**Actions:**
- `CloneRepoAction(url: str, path: str) -> Result[RepoHandle, GitError]`
- `CreateBranchAction(repo: str, branch: str, base: str) -> Result[str, GitError]`
- `CommitChangesAction(repo: str, message: str, files: list[str]) -> Result[str, GitError]`
- `CreatePRAction(repo: str, title: str, body: str, base: str) -> Result[PRInfo, GitError]`
- `CreateWorktreeAction(repo: str, branch: str) -> Result[str, GitError]`

**Tasks:**
- `StageFilesTask(repo: str, files: list[str]) -> None`
- `CheckDiffTask(repo: str) -> DiffSummary` -- получить summary изменений
- `CleanupWorktreeTask(path: str) -> None`

**Queries:**
- `GetRepoStatusQuery(repo: str) -> RepoStatus`
- `GetBranchesQuery(repo: str) -> list[str]`
- `GetCommitHistoryQuery(repo: str, limit: int) -> list[CommitInfo]`

**Events:** `RepoCloned`, `BranchCreated`, `ChangesCommitted`, `PRCreated`, `WorktreeCreated`
**Errors:** `GitCloneError`, `GitConflictError`, `GitPushError`, `WorktreeError`

---

### 3. NixModule -- Nix build и flake generation

**Назначение:** reproducible builds, OCI-образы, flake-генерация.

**Actions:**
- `BuildAction(flake_ref: str, output: str) -> Result[BuildResult, NixError]`
- `GenerateFlakeAction(config: FlakeConfig) -> Result[str, NixError]` -- сгенерировать flake.nix
- `BuildOCIAction(flake_ref: str) -> Result[OCIImage, NixError]` -- собрать OCI-образ через nix2container

**Tasks:**
- `EvalFlakeTask(flake_ref: str) -> FlakeMetadata` -- evaluate flake без сборки
- `RenderFlakeTemplateTask(config: FlakeConfig) -> str` -- рендер шаблона flake.nix

**Events:** `BuildCompleted`, `BuildFailed`, `FlakeGenerated`, `OCIImageBuilt`
**Errors:** `NixBuildError`, `NixEvalError`, `FlakeGenerationError`

---

### 4. CICDModule -- Pipeline generation

**Назначение:** генерация CI/CD конфигурации (GitHub Actions) для проектов.

**Actions:**
- `GeneratePipelineAction(config: PipelineConfig) -> Result[str, CICDError]` -- сгенерировать workflow
- `ValidatePipelineAction(workflow: str) -> Result[ValidationResult, CICDError]` -- валидировать workflow

**Tasks:**
- `RenderWorkflowTemplateTask(config: PipelineConfig) -> str` -- рендер шаблона
- `DetectRunnerTypeTask(org: str) -> RunnerType` -- определить тип раннера (nix / standard)

**Events:** `PipelineGenerated`, `PipelineValidated`
**Errors:** `PipelineGenerationError`, `PipelineValidationError`, `RunnerDetectionError`

---

## Общие Acceptance Criteria

- [ ] MCP-клиент поддерживает stdio и HTTP транспорт
- [ ] Git-операции работают через subprocess (не Python-библиотека git)
- [ ] Nix build запускается только при наличии Nix в системе (graceful degradation)
- [ ] CI/CD генерация учитывает наличие NixOS self-hosted runners в vladdd183-org
- [ ] Worktree создается и уничтожается атомарно
- [ ] Все Actions возвращают Result[T, E]
