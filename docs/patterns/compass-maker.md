# Паттерн: COMPASS-MAKER в Porto

> Как стратегическое мышление (COMPASS) и надежное исполнение (MAKER) живут в Porto Container-ах.

---

## Две проблемы LLM-агентов

1. **Потеря контекста** -- по мере роста истории агент теряет фокус, забывает цель, галлюцинирует
2. **Накопление ошибок** -- даже при 99% точности на шаг, после 100 шагов общая точность ~37%

**COMPASS** решает проблему 1 (контекст). **MAKER** решает проблему 2 (ошибки).

---

## COMPASS в Porto: AgentSection/CompassModule

### Компоненты

| COMPASS | Porto-компонент | Ответственность |
|---|---|---|
| Meta-Thinker | `StrategizeAction` | Формирует стратегию, мониторит прогресс, обнаруживает тупики |
| Context Manager | `ManageContextAction` | Поддерживает долгосрочные Notes, формирует Briefs для агентов |
| Signal System | `Events.py` | Сигналы: progress, anomaly, stuck, completed |

### Структура модуля

```
AgentSection/CompassModule/
  Actions/
    StrategizeAction.py         # MissionSpec -> StrategyPlan
    MonitorProgressAction.py    # BeadResults -> ProgressReport
    DetectAnomalyAction.py      # Контекст -> AnomalySignal
  Tasks/
    BuildContextBriefTask.py    # Формирует Brief для агента-исполнителя
    ExtractNotesTask.py         # Извлекает долгосрочные Notes из результатов
    ScoreConfidenceTask.py      # Оценивает confidence стратегии
  Data/
    Schemas/
      Requests.py               # StrategizeRequest, MonitorRequest
      Responses.py              # StrategyPlan, ProgressReport
  Events.py                     # StrategyFormed, AnomalyDetected, StuckSignal
  Errors.py                     # LowConfidenceError, ContextOverflowError
  Providers.py                  # DI: DSPy modules, LLM clients
```

### DSPy интеграция

COMPASS не использует хардкод-промпты. Вместо этого -- DSPy Signatures:

```python
class StrategizeSignature(dspy.Signature):
    """Сформировать стратегию исполнения MissionSpec."""

    mission_spec: str = dspy.InputField(desc="Структурированная спецификация задачи")
    context: str = dspy.InputField(desc="Релевантный контекст из KnowledgeGraph")
    history: str = dspy.InputField(desc="История предыдущих попыток, если есть")

    approach: str = dspy.OutputField(desc="Общий подход к решению")
    phases: str = dspy.OutputField(desc="JSON список фаз исполнения")
    risks: str = dspy.OutputField(desc="Идентифицированные риски")
    confidence: float = dspy.OutputField(desc="Уверенность 0-1")
```

MIPROv2 optimizer подбирает оптимальные промпты автоматически по метрикам.

---

## MAKER в Porto: AgentSection/MakerModule

### Компоненты

| MAKER | Porto-компонент | Ответственность |
|---|---|---|
| MAD Decomposition | `DecomposeAction` | Разбивает задачу на микро-beads |
| K-Voting | `VoteAction` | Запускает K агентов, голосует за лучший результат |
| Red-Flagging | `FilterAction` | Фильтрует ненадежные ответы |

### Структура модуля

```
AgentSection/MakerModule/
  Actions/
    DecomposeAction.py          # StrategyPlan -> BeadGraph (MAD)
    VoteAction.py               # Запуск K агентов, голосование
    FilterAction.py             # Фильтрация ненадежных результатов
  Tasks/
    SplitIntoBeadsTask.py       # Атомарная декомпозиция
    MajorityVoteTask.py         # Подсчет голосов
    ConsistencyCheckTask.py     # Проверка согласованности ответов
    ConfidenceScoreTask.py      # Оценка уверенности ответа
  Data/
    Schemas/
      Requests.py               # DecomposeRequest, VoteRequest
      Responses.py              # BeadGraph, VoteResult
  Events.py                     # BeadsCreated, VoteCompleted, RedFlagged
  Errors.py                     # DecompositionError, NoConsensusError
  Providers.py                  # DI: DSPy modules, parallel execution config
```

### K-Voting в Porto

```python
class VoteAction(Action[VoteRequest, VoteResult, MakerError]):
    async def run(self, data: VoteRequest) -> Result[VoteResult, MakerError]:
        # Запускаем K агентов параллельно
        results = []
        async with anyio.create_task_group() as tg:
            for i in range(data.k):
                tg.start_soon(self._execute_agent, data.bead, i, results)

        # Голосуем
        vote_result = self.majority_vote.run(results)

        # Red-flag проверка
        if vote_result.confidence < data.min_confidence:
            return Failure(NoConsensusError(bead_id=data.bead.id))

        return Success(vote_result)
```

---

## Взаимодействие COMPASS и MAKER

```
COMPASS (стратегия)                     MAKER (исполнение)
    |                                       |
    |  StrategizeAction                     |
    |  -> StrategyPlan              DecomposeAction
    |                               -> BeadGraph
    |  MonitorProgressAction                |
    |  <- BeadResults               VoteAction (для каждого Bead)
    |                               -> VoteResult
    |  DetectAnomalyAction                  |
    |  -> AnomalySignal?            FilterAction
    |                               -> FilteredResult
    |  (если anomaly)                       |
    |  -> корректировка стратегии           |
```

COMPASS отвечает за **ЧТО** и **ЗАЧЕМ**. MAKER отвечает за **КАК** и **НАСКОЛЬКО НАДЕЖНО**.

---

## Для Replicator

- COMPASS + MAKER живут в обычных Porto Container-ах (Actions, Tasks, Events)
- Они используют DSPy вместо хардкод-промптов
- K-Voting обеспечивает надежность для критических операций
- Meta-Thinker мониторит весь pipeline и корректирует стратегию
- Всё это работает через стандартный Porto flow: DI, Result Railway, Events
