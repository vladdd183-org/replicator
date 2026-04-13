# 🏭🧬🔥 The Factory — Недостающее звено

> Заметка-диагностика. Зачем нужна фабрика, как она вписывается в экосистему vladOS + sandboxai, и какие требования к ней предъявляются.
>
> 📅 Дата среза: 2026-03-08

---

## 🩺 Диагноз: чего не хватает

```mermaid
flowchart TB
    subgraph HAVE["✅ Что уже есть"]
        direction TB
        V["🏔️ vladOS-v2\n━━━━━━━━━━\nИнфраструктура\nсерверов, хостов,\nсетей, секретов"]
        S["🧬 sandboxai\n━━━━━━━━━━\nМодули-ячейки\nокружений с CID,\ncapabilities, рекурсией"]
    end

    subgraph NEED["❌ Чего не хватает"]
        F["🏭 The Factory\n━━━━━━━━━━\nAI-фабрика, которая\nпорождает, развивает\nи оркестрирует"]
    end

    V -->|"предоставляет\nинфраструктуру"| F
    S -->|"предоставляет\nстроительные блоки"| F
    F -->|"заказывает\nресурсы"| V
    F -->|"порождает\nокружения"| S
    F -->|"развивает\nпроекты"| F

    style HAVE fill:#e8f5e9
    style NEED fill:#ffebee,stroke:#c62828,stroke-width:3px
```

### 🔍 Проблема в одном абзаце

vladOS умеет **управлять инфраструктурой**, sandboxai умеет **описывать и запускать окружения**. Но никто не умеет **автономно принимать задачу, создавать для неё новое окружение, работать внутри него, порождать дочерние, и в результате выдавать готовый проект или улучшение**. Это работа **фабрики**.

---

## 🎯 Что должна уметь The Factory

### 📋 Функциональные требования

```mermaid
mindmap
    root((🏭 Factory\nCore Capabilities))
        📥 Приём задач
            Файл в примонтированной папке
            API-запрос
            WebSocket/gRPC
            Таймер/cron
            MCP-вызов
        🧬 Порождение окружений
            Создать CellSpec из задачи
            Запустить sandboxai-ячейку
            Вложить ячейку в ячейку
            Передать ячейку другому агенту
        🛠️ Работа внутри окружения
            Создать проект с нуля
            Развить существующий
            Запустить тесты
            Собрать артефакты
        🔄 Параллельность и вложенность
            Несколько окружений одновременно
            Вложенные окружения
            Async/await на уровне ячеек
            Pipeline из ячеек
        📦 Выдача результата
            Готовый проект
            OCI-контейнер
            WASM-модуль
            Nix derivation
            Evidence bundle
```

### 🏗️ Нефункциональные требования

| Требование | Почему важно | Приоритет |
|-----------|-------------|-----------|
| 🔌 **Framework-agnostic** | Не быть заложником одного AI-фреймворка | 🔴 Критично |
| ⛓️ **Chain-agnostic** | Не быть заложником одной crypto-цепочки | 🔴 Критично |
| 🧩 **Модульность** | Каждый компонент заменяем | 🔴 Критично |
| 🌐 **Web3-compatible** | Работать и в web2, и в web3 | 🟡 Важно |
| 📦 **Multi-output** | Билдить как окружение, контейнер, и WASM | 🟡 Важно |
| 🔐 **Capability-based security** | Ячейки-агенты ограничены правами | 🟡 Важно |
| 📉 **Monotonic attenuation** | Вложенные агенты не получают больше прав | 🟡 Важно |
| 🧪 **Evidence-driven** | Результат доказуем | 🟢 Желательно |

---

## 🧬 Как Factory вписывается в экосистему

### ⚠️ Важное уточнение: Factory ≠ вшитый CellKind

**Factory — это внешний проект**, который просто **использует sandboxai как шаблон/модуль** и крутит внутри себя AI-фреймворк. Factory **не** вшивается в ядро sandboxai как специальный CellKind.

Пользователи sandboxai сами создают свои CellKind-ы и публикуют их в registry, чтобы другие могли использовать. Factory — это один из таких пользовательских проектов, просто более специализированный.

```mermaid
flowchart TB
    subgraph SANDBOXAI["🧬 sandboxai (ядро)"]
        CORE["📦 Core: CellSpec, Supervisor,\nBrokers, Adapters"]
        REGISTRY["📚 Registry: пользователи\nпубликуют свои CellKind-ы"]
    end

    subgraph EXTERNAL["🌍 Внешние проекты"]
        FACTORY["🏭 The Factory\n(отдельный проект)\nиспользует sandboxai preset"]
        OTHER1["📊 Data Pipeline Project\nиспользует sandboxai preset"]
        OTHER2["🤖 Bot Project\nиспользует sandboxai preset"]
    end

    CORE -->|"preset/template"| FACTORY
    CORE -->|"preset/template"| OTHER1
    CORE -->|"preset/template"| OTHER2
    FACTORY -.->|"публикует свой\nCellKind в registry"| REGISTRY
    OTHER1 -.->|"публикует"| REGISTRY

    style SANDBOXAI fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style EXTERNAL fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
```

### 📋 Factory как пользователь sandboxai

```yaml
# Factory просто берёт sandboxai preset и добавляет своё
base: preset/ai-agent  # стандартный sandboxai шаблон

runtime:
  backend: bubblewrap
  resources: { cpu: 8, memory: 16Gi, disk: 50Gi }

packages: [python@3.12, poetry, git, ripgrep]

capabilities:
  requested:
    - child:request-spawn
    - fs:read:/workspace/**
    - fs:write:/workspace/**
    - net:out:443
    - proc:spawn
```

Factory живёт **снаружи** sandboxai, как любой другой проект.

---

## 🔄 Жизненный цикл задачи в Factory

```mermaid
sequenceDiagram
    participant Source as 📥 Источник задачи
    participant Factory as 🏭 Factory Agent
    participant Sup as 🧠 Supervisor
    participant Sandbox as 🧬 sandboxai Cell
    participant Child as 🧬 Дочерняя Cell
    participant Output as 📦 Выход

    Source->>Factory: Задача (файл / API / MCP / timer)
    Factory->>Factory: Анализ задачи
    Factory->>Factory: Генерация CellSpec

    Factory->>Sup: request_spawn(CellSpec)
    Sup->>Sup: Policy check + Grant
    Sup->>Sandbox: Spawn ячейки

    Sandbox->>Sandbox: Работа (создание проекта, код, тесты)

    alt Нужна вложенная ячейка
        Sandbox->>Sup: request_child_spawn(child_spec)
        Sup->>Child: Spawn дочерней ячейки
        Child->>Child: Параллельная работа
        Child-->>Sandbox: Результат + Evidence
    end

    alt Нужно передать другому Factory
        Factory->>Factory: Handoff(task, context)
    end

    Sandbox-->>Factory: Артефакты + Evidence
    Factory->>Output: Build output (container / wasm / derivation)
    Factory->>Output: Evidence bundle
```

---

## 🧩 Архитектура Factory

```mermaid
flowchart TB
    subgraph Intake["📥 Слой приёма задач"]
        FW["📂 File Watcher"]
        API["🌐 HTTP API"]
        WS["🔌 WebSocket"]
        MCP_IN["🔗 MCP Server"]
        TIMER["⏰ Timer/Cron"]
    end

    subgraph Brain["🧠 Мозг Factory"]
        TaskRouter["🧭 Task Router\nАнализ + маршрутизация"]
        SpecGen["🧬 Spec Generator\nЗадача → CellSpec"]
        AgentLayer["🤖 Agent Layer\n(framework-agnostic)"]
    end

    subgraph AgentBackends["🔌 AI Backend Adapters"]
        OAI["OpenAI"]
        ANT["Anthropic"]
        GEM["Google Gemini"]
        OLL["Ollama (local)"]
        CUSTOM["Custom LLM"]
    end

    subgraph Execution["⚙️ Исполнение через sandboxai"]
        SUP["🧠 Supervisor"]
        CELLS["🧬 CellSpec Cells"]
        CHILDREN["🧬🧬 Дочерние Cells"]
    end

    subgraph Output["📦 Выход"]
        NIX["❄️ Nix Derivation"]
        OCI["🐳 OCI Container"]
        WASM["⚡ WASM Module"]
        PROJ["📁 Project Dir"]
        EVID["📦 Evidence Bundle"]
    end

    FW & API & WS & MCP_IN & TIMER --> TaskRouter
    TaskRouter --> SpecGen
    SpecGen --> AgentLayer
    AgentLayer --> OAI & ANT & GEM & OLL & CUSTOM

    AgentLayer --> SUP
    SUP --> CELLS
    CELLS --> CHILDREN

    CELLS --> NIX & OCI & WASM & PROJ & EVID
```

---

## 🔌 Framework-Agnostic Agent Layer

Ключевая архитектурная идея: **Factory не зависит от конкретного AI-фреймворка**. Вместо этого у неё есть **абстрактный Agent Layer** с адаптерами:

```mermaid
classDiagram
    class AgentInterface {
        <<interface>>
        +plan(task: Task) PlanResult
        +execute(plan: Plan, cell: Cell) ExecResult
        +evaluate(result: ExecResult) EvalResult
        +handoff(task: Task, target: Agent) void
    }

    class LangGraphAdapter {
        +plan() PlanResult
        +execute() ExecResult
    }

    class AutoGenAdapter {
        +plan() PlanResult
        +execute() ExecResult
    }

    class CrewAIAdapter {
        +plan() PlanResult
        +execute() ExecResult
    }

    class OpenAIAgentsAdapter {
        +plan() PlanResult
        +execute() ExecResult
    }

    class RawLLMAdapter {
        +plan() PlanResult
        +execute() ExecResult
    }

    class MCPToolsLayer {
        +callTool(name, args) Result
        +listTools() ToolDescriptor[]
    }

    AgentInterface <|.. LangGraphAdapter
    AgentInterface <|.. AutoGenAdapter
    AgentInterface <|.. CrewAIAdapter
    AgentInterface <|.. OpenAIAgentsAdapter
    AgentInterface <|.. RawLLMAdapter

    AgentInterface --> MCPToolsLayer : uses
```

### 🧠 Почему именно так

| Проблема | Решение |
|---------|---------|
| Vendor lock на один AI-фреймворк | Абстрактный `AgentInterface` + адаптеры |
| Vendor lock на одного LLM-провайдера | Адаптеры для каждого провайдера |
| Быстрое старение фреймворков | Фреймворк = адаптер, его можно заменить |
| Разные задачи — разные фреймворки | Router выбирает лучший адаптер по задаче |
| Tools lock-in | MCP как стандарт tool integration |

---

## 🔗 MCP как универсальный tool layer

**MCP (Model Context Protocol)** — идеальный стандарт для framework-agnostic tool integration:

```mermaid
flowchart LR
    subgraph Factory["🏭 Factory Agent"]
        Agent["🤖 Any AI Agent"]
    end

    subgraph MCP_Layer["🔗 MCP Layer"]
        MCP_C["MCP Client"]
    end

    subgraph MCP_Servers["🛠️ MCP Servers"]
        SANDBOX_MCP["🧬 sandboxai MCP\n• spawn\n• build\n• test\n• status"]
        VCS_MCP["📦 VCS MCP\n• commit\n• push\n• PR"]
        FS_MCP["📂 Filesystem MCP\n• read\n• write\n• search"]
        INFRA_MCP["🏔️ vladOS MCP\n• deploy\n• provision\n• status"]
    end

    Agent --> MCP_C
    MCP_C --> SANDBOX_MCP & VCS_MCP & FS_MCP & INFRA_MCP
```

> 💡 **Главное:** любой AI-агент (LangGraph, AutoGen, CrewAI, raw LLM) может использовать одни и те же MCP-серверы. Фабрика не привязана к конкретному фреймворку, потому что **tools живут в MCP**, а не внутри фреймворка.

---

## 🧬 Вложенность и параллельность

```mermaid
flowchart TB
    subgraph F0["🏭 Root Factory"]
        TASK["📥 Задача: 'Сделай микросервис на Go'"]
    end

    subgraph F1["🧬 Cell: Project Scaffolding"]
        C1["Создание структуры проекта"]
    end

    subgraph F2["🧬 Cell: Backend Dev"]
        C2["Написание Go-кода"]
        subgraph F2_1["🧬 Cell: Tests"]
            C2_1["Unit-тесты"]
        end
        subgraph F2_2["🧬 Cell: Integration"]
            C2_2["Integration-тесты"]
        end
    end

    subgraph F3["🧬 Cell: Build"]
        C3["Сборка OCI-контейнера"]
    end

    subgraph F4["🧬 Cell: Deploy Preview"]
        C4["Деплой в preview-окружение"]
    end

    F0 --> F1
    F1 --> F2
    F2 --> F2_1 & F2_2
    F2_1 & F2_2 --> F3
    F3 --> F4

    style F0 fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style F2_1 fill:#e8f5e9
    style F2_2 fill:#e8f5e9
```

### 🔑 Ключевые свойства

- 🪆 **Вложенность**: Factory порождает Cell, Cell порождает дочерние Cell
- ⚡ **Параллельность**: F2_1 и F2_2 работают параллельно
- 🔐 **Attenuation**: каждый уровень вложенности получает меньше прав
- 📦 **Изоляция**: каждая Cell в своём sandbox (bubblewrap/OCI/WASM)
- 🔄 **Handoff**: Factory может передать задачу другому Factory

---

## 🎯 Минимальный MVP Factory

Что нужно для первого рабочего прототипа:

```mermaid
graph TD
    subgraph MVP["🎯 MVP Factory"]
        direction TB
        M1["📥 File Watcher\nфайл появился → задача"]
        M2["🧠 Task → CellSpec\nразбор задачи в спецификацию"]
        M3["🤖 Single Agent\n(один LLM-адаптер)"]
        M4["🧬 sandboxai spawn\nсоздание окружения"]
        M5["🛠️ Работа внутри\n(через MCP tools)"]
        M6["📦 Результат\n(project dir + evidence)"]
    end

    M1 --> M2 --> M3 --> M4 --> M5 --> M6
```

### ❌ Что НЕ в MVP

- Multi-framework routing
- Web3 adapters
- WASM output
- Distributed execution
- GUI/Dashboard

### ✅ Что в MVP

| Компонент | Реализация |
|-----------|-----------|
| Приём задачи | File watcher (inotify) |
| AI Agent | Один адаптер (OpenAI или Anthropic) |
| Tool layer | MCP (sandboxai MCP + filesystem MCP) |
| Окружение | sandboxai Cell (bubblewrap) |
| Результат | Project directory + JSON evidence |

---

## 🧩 Связь с sandboxai

Factory — это **внешний проект**, который использует sandboxai как базу:

```mermaid
flowchart LR
    subgraph SANDBOXAI["🧬 sandboxai"]
        PRESETS["📦 Presets\n(ai-agent, python,\ncontainer, etc.)"]
        REGISTRY["📚 Registry\n(пользовательские\nCellKind-ы)"]
    end

    subgraph FACTORY["🏭 Factory Project"]
        FP["Берёт preset/ai-agent\n+ добавляет AI framework\n+ добавляет task routing\n+ добавляет spawn logic"]
    end

    PRESETS -->|"использует\nкак базу"| FP
    FP -.->|"может опубликовать\nсвой шаблон обратно"| REGISTRY

    style FACTORY fill:#fff3e0,stroke:#e65100,stroke-width:2px
```

> Factory — это **пользователь sandboxai**, который берёт preset, оборачивает AI-фреймворком и получает фабрику. Точно так же любой другой пользователь может создать свой CellKind и опубликовать в registry.

---

## ❤️ Главный вывод

**The Factory** — это:

1. 🏭 **Недостающее звено** между vladOS (инфраструктура) и sandboxai (модули)
2. 🤖 **AI-оркестратор**, который принимает задачи и создаёт окружения для их решения
3. 🔌 **Framework-agnostic** — через абстрактный Agent Layer с адаптерами
4. 🔗 **MCP-native** — tools живут в MCP-серверах, а не внутри фреймворка
5. 🧬 **Ещё одна Cell** в экосистеме sandboxai — kind: factory
6. 🪆 **Рекурсивная** — factory может породить factory

**Следующая заметка — конкретный выбор AI-фреймворков и стратегия framework-agnostic подхода.**
