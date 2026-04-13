# Спецификация: CoreSection

> Ядро репликатора: компиляция спецификаций, реестр Cell, шаблоны, эволюция.

---

## Модули

### 1. SpecModule -- компиляция Intent -> MissionSpec -> Formula

**Назначение:** принять высокоуровневый intent и преобразовать его в структурированную спецификацию.

**Actions:**
- `CompileSpecAction(intent: str) -> Result[MissionSpec, SpecError]` -- компиляция intent в MissionSpec
- `ValidateSpecAction(spec: MissionSpec) -> Result[MissionSpec, SpecError]` -- валидация спецификации
- `InstantiateFormulaAction(spec: MissionSpec, formula: Formula) -> Result[Molecule, SpecError]` -- создание Molecule из Formula

**Tasks:**
- `ParseIntentTask(text: str) -> ParsedIntent` -- парсинг текстового intent
- `EnrichContextTask(parsed: ParsedIntent) -> EnrichedIntent` -- обогащение контекстом из KG
- `SelectFormulaTask(spec: MissionSpec) -> Formula` -- выбор подходящей Formula из библиотеки

**Queries:**
- `ListFormulasQuery() -> list[FormulaSummary]` -- список доступных Formula
- `GetFormulaQuery(name: str) -> Formula | None` -- получить Formula по имени

**Events:** `SpecCompiled`, `SpecValidated`, `FormulaInstantiated`
**Errors:** `SpecCompilationError`, `SpecValidationError`, `FormulaNotFoundError`

---

### 2. CellRegistryModule -- реестр спецификаций

**Назначение:** хранить и управлять всеми CellSpec-ами системы.

**Actions:**
- `RegisterCellAction(spec: CellSpec) -> Result[CellSpec, RegistryError]` -- зарегистрировать новую Cell
- `UpdateCellStatusAction(name: str, status: CellStatus) -> Result[CellSpec, RegistryError]` -- обновить статус
- `DeprecateCellAction(name: str, replacement: str | None) -> Result[CellSpec, RegistryError]` -- пометить как deprecated

**Queries:**
- `GetCellQuery(name: str, version: str | None) -> CellSpec | None` -- получить Cell spec
- `ListCellsQuery(section: str | None, status: CellStatus | None) -> list[CellSpec]` -- список Cell
- `GetCellHistoryQuery(name: str) -> list[CellSpec]` -- история версий

**Events:** `CellRegistered`, `CellStatusUpdated`, `CellDeprecated`
**Errors:** `CellNotFoundError`, `CellAlreadyExistsError`, `InvalidCellSpecError`

---

### 3. TemplateModule -- генерация Porto-скелетов

**Назначение:** генерировать структуру Porto-проекта или отдельного модуля из шаблонов.

**Actions:**
- `GenerateModuleAction(config: ModuleConfig) -> Result[GeneratedModule, TemplateError]` -- генерировать модуль
- `GenerateProjectAction(config: ProjectConfig) -> Result[GeneratedProject, TemplateError]` -- генерировать проект
- `GenerateComponentAction(config: ComponentConfig) -> Result[GeneratedComponent, TemplateError]` -- генерировать компонент (Action/Task/Query)

**Tasks:**
- `RenderTemplateTask(template: str, context: dict) -> str` -- рендер Jinja2 шаблона
- `ValidateStructureTask(path: str) -> ValidationResult` -- проверить Porto-структуру
- `GenerateFlakeTask(config: ProjectConfig) -> str` -- сгенерировать flake.nix
- `GenerateCITask(config: ProjectConfig) -> str` -- сгенерировать CI workflow

**Events:** `ModuleGenerated`, `ProjectGenerated`, `ComponentGenerated`
**Errors:** `TemplateNotFoundError`, `TemplateRenderError`, `InvalidConfigError`

---

### 4. EvolutionModule -- мутация, fitness test, promotion

**Назначение:** управлять жизненным циклом версий: мутация -> тестирование -> promotion/rollback.

**Actions:**
- `MutateAction(current_spec: CellSpec, changes: ChangeSet) -> Result[CellSpec, EvolutionError]` -- создать новую версию spec
- `VerifyAction(execution_result: ExecutionResult) -> Result[EvidenceBundle, EvolutionError]` -- верификация результатов
- `PromoteAction(evidence: EvidenceBundle) -> Result[PromotionResult, EvolutionError]` -- промоутить verified версию
- `RollbackAction(name: str) -> Result[CellSpec, EvolutionError]` -- откатить к предыдущей ACTIVE версии

**Tasks:**
- `RunTestsTask(path: str) -> TestResults` -- запуск тестов
- `RunLintTask(path: str) -> LintResults` -- запуск линтера
- `RunTypeCheckTask(path: str) -> TypeCheckResults` -- проверка типов
- `CheckArchitectureGuardsTask(path: str) -> GuardResults` -- проверка Porto-правил
- `DetermineGovernanceLevelTask(changes: ChangeSet) -> GovernanceLevel` -- определить уровень governance

**Events:** `VersionMutated`, `VerificationPassed`, `VerificationFailed`, `VersionPromoted`, `VersionRolledBack`
**Errors:** `VerificationFailedError`, `PromotionDeniedError`, `RollbackError`, `GovernanceEscalationError`

---

## Общие Acceptance Criteria для CoreSection

- [ ] Все Actions возвращают Result[T, E]
- [ ] Все модели -- Pydantic frozen
- [ ] Все модули имеют Providers.py с Dishka
- [ ] Межмодульное общение -- только через Events
- [ ] Нет прямых импортов между модулями CoreSection
- [ ] Каждый модуль имеет cell_spec.py с CellSpec
