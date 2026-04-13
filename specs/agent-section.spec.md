# Спецификация: AgentSection

> Интеллект: COMPASS (стратегия), MAKER (надежность), Orchestrator (координация).

---

## Модули

### 1. CompassModule -- стратегическое мышление

**Назначение:** формировать стратегию, мониторить прогресс, управлять контекстом агентов.

**Actions:**
- `StrategizeAction(spec: MissionSpec, context: ContextBundle) -> Result[StrategyPlan, CompassError]`
- `MonitorProgressAction(bead_results: list[BeadResult]) -> Result[ProgressReport, CompassError]`
- `DetectAnomalyAction(context: ContextBundle, progress: ProgressReport) -> Result[AnomalyReport | None, CompassError]`

**Tasks:**
- `BuildContextBriefTask(context: ContextBundle, target_bead: Bead) -> Brief` -- формирует краткий brief для агента-исполнителя
- `ExtractNotesTask(results: list[BeadResult]) -> list[Note]` -- извлекает долгосрочные заметки
- `ScoreConfidenceTask(plan: StrategyPlan) -> float` -- оценивает confidence стратегии

**Queries:**
- `GetContextQuery(mission_id: str) -> ContextBundle` -- получить контекст для миссии
- `GetNotesQuery(mission_id: str) -> list[Note]` -- получить заметки

**DSPy Signatures:**
- `StrategizeSignature` -- mission_spec + context + history -> approach + phases + risks + confidence
- `MonitorSignature` -- progress + plan + anomalies -> status + recommendations + adjustments
- `AnomalySignature` -- context + progress + expected -> anomaly_detected + description + severity

**Events:** `StrategyFormed`, `ProgressUpdated`, `AnomalyDetected`, `StrategyAdjusted`
**Errors:** `LowConfidenceError`, `ContextOverflowError`, `StrategyFormationError`

---

### 2. MakerModule -- надежное исполнение

**Назначение:** декомпозировать задачи, обеспечивать статистическую надежность, фильтровать ненадежные ответы.

**Actions:**
- `DecomposeAction(plan: StrategyPlan) -> Result[BeadGraph, MakerError]` -- MAD декомпозиция
- `VoteAction(bead: Bead, k: int, min_confidence: float) -> Result[VoteResult, MakerError]` -- K-Voting
- `FilterAction(results: list[BeadResult]) -> Result[list[BeadResult], MakerError]` -- Red-Flagging

**Tasks:**
- `SplitIntoBeadsTask(phase: StrategyPhase) -> list[Bead]` -- атомарная декомпозиция
- `BuildDependencyGraphTask(beads: list[Bead]) -> list[tuple[str, str]]` -- построить граф зависимостей
- `MajorityVoteTask(results: list[Any]) -> VoteResult` -- подсчет голосов
- `ConsistencyCheckTask(results: list[Any]) -> float` -- проверка согласованности
- `ConfidenceScoreTask(result: Any) -> float` -- оценка уверенности

**DSPy Signatures:**
- `DecomposeSignature` -- phase + context + constraints -> beads_json
- `VoteEvaluationSignature` -- bead + results_k -> best_result + confidence + reasoning

**Events:** `BeadsCreated`, `VoteCompleted`, `ResultRedFlagged`, `ConsensusReached`
**Errors:** `DecompositionError`, `NoConsensusError`, `AllResultsRedFlaggedError`

---

### 3. OrchestratorModule -- координация агентов

**Назначение:** исполнять BeadGraph, координировать агентов, управлять workcell-ами.

**Actions:**
- `ExecuteBeadGraphAction(graph: BeadGraph) -> Result[ExecutionResult, OrchestratorError]` -- исполнить граф
- `ExecuteBeadAction(bead: Bead, brief: Brief) -> Result[BeadResult, OrchestratorError]` -- исполнить один bead
- `RetryBeadAction(bead: Bead, previous_result: BeadResult) -> Result[BeadResult, OrchestratorError]` -- повторить с учетом ошибки

**Tasks:**
- `TopologicalSortTask(graph: BeadGraph) -> list[list[Bead]]` -- тополог. сортировка (группы для параллелизма)
- `SelectAgentTask(bead: Bead) -> AgentConfig` -- выбрать агента для bead
- `CreateWorkcellTask(bead: Bead) -> WorkcellHandle` -- создать изолированную среду
- `CleanupWorkcellTask(handle: WorkcellHandle) -> None` -- очистить среду
- `CollectEvidenceTask(bead: Bead, result: Any) -> dict` -- собрать evidence

**Events:** `BeadStarted`, `BeadCompleted`, `BeadFailed`, `GraphExecutionStarted`, `GraphExecutionCompleted`
**Errors:** `BeadExecutionError`, `WorkcellCreationError`, `AgentUnavailableError`, `TimeoutError`

---

## Общие Acceptance Criteria

- [ ] COMPASS использует DSPy Signatures, не хардкод-промпты
- [ ] MAKER K-Voting использует anyio TaskGroup для параллелизма
- [ ] Orchestrator корректно обрабатывает граф зависимостей (DAG)
- [ ] Workcell-ы изолированы (git worktree минимум)
- [ ] Evidence собирается для каждого Bead
- [ ] Все модули общаются через Events
- [ ] Retry с exponential backoff + max_retries
