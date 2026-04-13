# РУКОВОДСТВО ПО РЕАЛИЗАЦИИ

> Конкретные инструкции для AI-агента. Как реализовать каждый следующий шаг.

---

## Стиль кода проекта

### Абсолютные импорты ВСЕГДА
```python
# Правильно
from src.Ship.Parents.Action import Action
from src.Ship.Core.Errors import BaseError
from src.Ship.Adapters.Protocols import StoragePort

# Неправильно
from ....Parents.Action import Action
```

### Result Railway
```python
from returns.result import Result, Success, Failure

class MyAction(Action[InputType, OutputType, ErrorType]):
    async def run(self, data: InputType) -> Result[OutputType, ErrorType]:
        if something_wrong:
            return Failure(MyError(detail="..."))
        return Success(result)
```

### Ошибки -- Pydantic frozen
```python
from pydantic import BaseModel
from src.Ship.Core.Errors import BaseError

class MyModuleError(BaseError):
    """Базовая ошибка модуля."""
    pass

class SpecificError(MyModuleError):
    code: str = "SPECIFIC_ERROR"
    http_status: int = 400
    detail: str
```

### Events -- Pydantic frozen
```python
from src.Ship.Parents.Event import DomainEvent

class SomethingHappened(DomainEvent):
    entity_id: str
    detail: str
```

### Providers -- Dishka
```python
from dishka import Provider, Scope, provide

class MyModuleProvider(Provider):
    scope = Scope.REQUEST
    my_action = provide(MyAction)
    my_task = provide(MyTask)
```

### Structured Concurrency
```python
import anyio

async with anyio.create_task_group() as tg:
    tg.start_soon(task1)
    tg.start_soon(task2)
# Обе задачи завершены или обе отменены
```

---

## Как реализовать P0 Bead

### Пример: B-SHIP-ADAPT-003 (LocalStorageAdapter)

1. Прочитать спецификацию: `specs/ship-adapters.spec.md`
2. Прочитать bead: `specs/beads/p0-ship-foundation.md` (секция B-SHIP-ADAPT-003)
3. Проверить зависимости: B-SHIP-ADAPT-001 (Protocols) и B-SHIP-ADAPT-002 (Errors) должны быть готовы
4. Создать файл: `src/Ship/Adapters/Storage/__init__.py` и `src/Ship/Adapters/Storage/LocalAdapter.py`
5. Реализовать все методы StoragePort
6. Проверить acceptance criteria:
   - [ ] Реализует StoragePort
   - [ ] Хранит файлы в configurable директории
   - [ ] put возвращает sha256 hash
   - [ ] get бросает StorageNotFoundError если не найден
   - [ ] list_prefix работает
   - [ ] Тест roundtrip
7. Написать тест в `tests/unit/adapters/test_local_storage.py`

---

## Как интегрировать OpenRouter

```python
# В Ship/Configs/Settings.py добавить:
class AISettings(BaseModel):
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "anthropic/claude-sonnet-4"
    fast_model: str = "openai/gpt-4o-mini"
    reasoning_model: str = "anthropic/claude-sonnet-4"

# Использовать через стандартный OpenAI SDK:
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url=settings.ai.openrouter_base_url,
    api_key=settings.ai.openrouter_api_key,
)
response = await client.chat.completions.create(
    model=settings.ai.default_model,
    messages=[...],
)
```

---

## Как интегрировать LangGraph

```python
# AgentSection/OrchestratorModule/ использует LangGraph для BeadGraph execution
from langgraph.graph import StateGraph, END

class BeadGraphState(TypedDict):
    beads: list[Bead]
    results: list[BeadResult]
    current_bead_idx: int

graph = StateGraph(BeadGraphState)
graph.add_node("execute_bead", execute_bead_node)
graph.add_node("verify_bead", verify_bead_node)
graph.add_conditional_edges("verify_bead", check_result, {"pass": "execute_bead", "fail": "retry_or_end"})
```

---

## Как интегрировать MCP

```python
# ToolSection/MCPClientModule/ -- MCP-клиент
import mcp

async def call_tool(server_config: MCPServerConfig, tool_name: str, args: dict):
    async with mcp.ClientSession(server_config.command, server_config.args) as session:
        result = await session.call_tool(tool_name, args)
        return result
```

---

## Как интегрировать DSPy

```python
import dspy

# Настройка LLM через OpenRouter
lm = dspy.LM(
    model="openrouter/anthropic/claude-sonnet-4",
    api_key=settings.ai.openrouter_api_key,
    api_base=settings.ai.openrouter_base_url,
)
dspy.configure(lm=lm)

# Signature для COMPASS Meta-Thinker
class StrategizeSignature(dspy.Signature):
    """Сформировать стратегию исполнения задачи."""
    mission_spec: str = dspy.InputField(desc="Структурированная спецификация задачи")
    context: str = dspy.InputField(desc="Контекст из базы знаний")
    approach: str = dspy.OutputField(desc="Подход к решению")
    phases: str = dspy.OutputField(desc="Фазы исполнения (JSON)")
    confidence: float = dspy.OutputField(desc="Уверенность 0-1")

# Module
class MetaThinker(dspy.Module):
    def __init__(self):
        self.strategize = dspy.ChainOfThought(StrategizeSignature)

    def forward(self, mission_spec, context):
        return self.strategize(mission_spec=mission_spec, context=context)
```

---

## Структура нового модуля (шаблон)

```
Containers/{Section}/{Module}/
  __init__.py
  Actions/
    __init__.py
    {Verb}{Noun}Action.py
  Tasks/
    __init__.py
    {Verb}{Noun}Task.py
  Queries/
    __init__.py
    {Get|List}{Noun}Query.py
  Data/
    __init__.py
    Schemas/
      __init__.py
      Requests.py
      Responses.py
  Events.py
  Errors.py
  Providers.py
  cell_spec.py          # опционально
```
