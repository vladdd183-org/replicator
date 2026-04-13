# 🏛️🧬🔥 The Grand Architecture — Финальный синтез

> **Всё, что было исследовано, спроектировано и прототипировано — собрано в единую архитектурную визию.**
>
> Это не новый проект. Это **карта того, как все существующие наработки складываются в одно целое**.
>
> 📅 Дата: 2026-03-08

---

## 🧠 Понимание замысла

### Что на самом деле происходит

Ты не делаешь пять отдельных проектов. Ты строишь **одну систему** на пяти уровнях:

```mermaid
flowchart TB
    subgraph L5["🏔️ Уровень 5 — ИНФРАСТРУКТУРА"]
        VLADOS["vladOS-v2\n❄️ Декларативная NixOS конфигурация\nХосты, сети, секреты, деплой"]
    end

    subgraph L4["🧬 Уровень 4 — ОКРУЖЕНИЕ"]
        SANDBOX["sandboxai / NixBox\n🫧 CID-адресуемые рекурсивные ячейки\nSupervisor, Capabilities, Adapters"]
    end

    subgraph L3["⚓ Уровень 3 — КАРКАС ПРОЕКТА"]
        PORTO["Hyper-Porto\n📦 Ship + Containers + Actions + Tasks\nResult Railway, DI, Domain Events"]
    end

    subgraph L2["🧠 Уровень 2 — ИНТЕЛЛЕКТ"]
        INTEL["COMPASS + MAKER + DSPy\n🧭 Стратегия + 🏗️ Надёжность + 🧪 Оптимизация\nMeta-Thinker, MAD, K-Voting, MIPROv2"]
    end

    subgraph L1["🔗 Уровень 1 — ИНСТРУМЕНТЫ"]
        TOOLS["MCP Servers\n🔌 Стандартный протокол tool integration\nframework-agnostic, chain-agnostic"]
    end

    L5 -->|"предоставляет хосты"| L4
    L4 -->|"предоставляет\nизолированное окружение"| L3
    L3 -->|"предоставляет\nструктуру проекта"| L2
    L2 -->|"использует"| L1
    L1 -->|"воздействует на"| L4

    style L5 fill:#e3f2fd,stroke:#1565c0
    style L4 fill:#e8f5e9,stroke:#2e7d32
    style L3 fill:#fff3e0,stroke:#e65100
    style L2 fill:#fce4ec,stroke:#c62828
    style L1 fill:#f3e5f5,stroke:#7b1fa2
```

### 📝 В одном абзаце

> **vladOS** разворачивает серверы. На серверах живут **sandboxai-ячейки** — изолированные CID-адресуемые окружения. Внутри каждой ячейки — **Hyper-Porto проект**: модульная архитектура с Ship/Containers/Actions/Tasks. Логику проекта движет **COMPASS** (стратегия) + **MAKER** (надёжность), реализованные как **DSPy-модули** (self-improvement). Все инструменты подключены через **MCP** (framework-agnostic). Всё это работает сейчас в web2, но каждый слой **архитектурно готов** к web3 через adapter families.

---

## 🔬 Каждый слой — зачем и что именно

### 🏔️ Уровень 5: vladOS — «Земля под ногами»

```text
Роль:     Декларативное управление ФИЗИЧЕСКОЙ инфраструктурой
Что:      NixOS + Snowfall Lib + SOPS + deploy-rs
Аналогия: Фундамент здания. Стены, электричество, водоснабжение.
```

vladOS **не знает** про AI, агентов и фабрики. Он знает про хосты, профили, секреты и деплой. И это правильно — чистое разделение ответственности.

**Web3 readiness:** vladOS уже декларативен и воспроизводим (Nix). Для web3 нужно добавить: DID-ы вместо SSH-ключей, UCAN вместо SOPS, P2P discovery вместо статических IP. Всё это — adapter-level изменения, не перестройка.

---

### 🧬 Уровень 4: sandboxai — «Стены комнаты»

```text
Роль:     Изолированное ОКРУЖЕНИЕ для любой нагрузки
Что:      CellSpec + Supervisor + Brokers + Capabilities + Adapters
Аналогия: Комната в здании. Стены, дверь, замок, вентиляция.
```

sandboxai **не знает** какой проект внутри него живёт. Он знает про изоляцию (bubblewrap/OCI/WASM), права (Capabilities + Grants), ресурсы (Budgets), и доказательства (Evidence + Ledgers).

**Ключевой инсайт:** sandboxai — это **runtime**, а не проект. Factory — это **проект**, который живёт внутри sandboxai-ячейки, используя preset `ai-agent`.

**Web3 readiness:** уже спроектировано. Adapter families (Local → IPFS → Filecoin), progressive decentralization (Stage 0-3), CID-addressable specs, UCAN capabilities. Ядро protocol-neutral.

---

### ⚓ Уровень 3: Hyper-Porto — «Мебель и планировка»

```text
Роль:     КАРКАС ПРОЕКТА, живущего внутри ячейки
Что:      Ship + Containers + Actions + Tasks + Result Railway + DI + Events
Аналогия: Планировка квартиры. Кухня, спальня, коридор, мебель.
```

Hyper-Porto — это **как организован код** внутри проекта. Factory — это Hyper-Porto проект. Любой другой проект тоже может быть Hyper-Porto. Это архитектурный паттерн, не конкретное приложение.

```mermaid
flowchart TB
    subgraph PORTO_IN_FACTORY["⚓ Hyper-Porto внутри Factory"]
        SHIP["🚢 Ship\n━━━━━━━━\nAuth, Configs, Core,\nDecorators, Events,\nInfrastructure, Parents"]

        subgraph STRATEGIC["🧭 Strategic Section"]
            META["MetaThinkerModule\n(COMPASS)"]
            CTX["ContextManagerModule\n(COMPASS + AgentFold)"]
        end

        subgraph EXECUTION["🏗️ Execution Section"]
            DECOMP["DecomposerModule\n(MAKER MAD)"]
            VOTER["VoterModule\n(MAKER K-Voting)"]
            FILTER["FilterModule\n(MAKER Red-Flagging)"]
        end

        subgraph AGENT["🤖 Agent Section"]
            DSPY_MOD["DSPyAgentModule\n(ReAct + Optimizers)"]
            MCP_MOD["MCPClientModule\n(Tool integration)"]
        end

        subgraph CORE["📦 Core Section"]
            TASK_MOD["TaskRouterModule\n(intake channels)"]
            SPEC_MOD["SpecGeneratorModule\n(task → CellSpec)"]
            EVIDENCE["EvidenceModule\n(results + learnings)"]
        end
    end

    SHIP --> STRATEGIC & EXECUTION & AGENT & CORE
```

**Web3 readiness:** Hyper-Porto уже готов:
- **Gateway Pattern** = port/adapter = adapter family в web3. Монолит → микросервис = заменить DirectAdapter на HTTPAdapter. Монолит → web3 = заменить на Web3Adapter.
- **Saga Pattern** = distributed transactions = аналог cross-chain sagas
- **Domain Events** = event sourcing = append-only ledger = blockchain-compatible
- **Result[T, E]** = явные ошибки = deterministic execution = WASM-compatible

---

### 🧠 Уровень 2: COMPASS + MAKER + DSPy — «Обитатели»

```text
Роль:     ИНТЕЛЛЕКТ, который живёт внутри проекта
Что:      Стратегия + Надёжность + Самоулучшение
Аналогия: Жители квартиры. Их навыки, привычки, способ мышления.
```

Это **не фреймворк**, а **набор паттернов**, реализованных как DSPy-модули внутри Hyper-Porto Containers:

```mermaid
flowchart LR
    subgraph COMPASS_IMPL["🧭 COMPASS → DSPy Modules"]
        MT["dspy.ChainOfThought\nMeta-Thinker:\nstrategy, monitoring,\nanomaly detection"]
        CM["dspy.Module\nContext Manager:\nfolding, notes, briefs\n(AgentFold-inspired)"]
    end

    subgraph MAKER_IMPL["🏗️ MAKER → sandboxai primitives"]
        MAD["Task → list[CellSpec]\nMAD decomposition:\nодна Cell = один шаг"]
        VOTE["Parallel Cells\nK-Voting:\nK ячеек голосуют"]
        RED["EvidenceBundle check\nRed-Flagging:\nфильтрация ненадёжных"]
    end

    subgraph DSPY_IMPL["🧪 DSPy → Self-improvement"]
        OPT["MIPROv2 Optimizer\nAuto-optimize промптов\nпо реальным метрикам"]
        SIG["Signatures\nДекларативные контракты\nне промпты"]
    end
```

**Почему DSPy, а не промпты:**

```text
Nix   : «Не пиши конфигурации руками — опиши декларативно, nix соберёт»
DSPy  : «Не пиши промпты руками — опиши сигнатуру, optimizer подберёт»
Porto : «Не мешай бизнес-логику с инфраструктурой — раздели на Actions и Ship»
```

Все три — **декларативны**, **компилируемы**, **самоулучшаемы**.

**Web3 readiness:**
- DSPy-оптимизированные промпты = immutable artifacts = CID-addressable
- Метрики = evidence = on-chain verifiable
- MAKER K-Voting = consensus mechanism = blockchain-native pattern
- COMPASS strategy = governance = DAO-compatible decision-making

---

### 🔗 Уровень 1: MCP — «Руки и инструменты»

```text
Роль:     СТАНДАРТНЫЙ ПРОТОКОЛ для tool integration
Что:      JSON-RPC 2.0, stdio/HTTP transport, Tool/Resource/Prompt
Аналогия: Руки, которыми жители делают работу. Универсальные, не привязаны к телу.
```

MCP — это **framework-agnostic** и **chain-agnostic** tool layer:

```mermaid
flowchart LR
    subgraph ANY_AGENT["🤖 Любой агент"]
        DSPY_A["DSPy ReAct"]
        LG_A["LangGraph"]
        RAW_A["Raw LLM"]
    end

    subgraph MCP_LAYER["🔗 MCP Protocol"]
        MCP_C["MCP Client"]
    end

    subgraph MCP_SERVERS["🛠️ MCP Servers"]
        S1["🧬 sandboxai-mcp\nspawn, build, test, status"]
        S2["📂 filesystem-mcp\nread, write, search"]
        S3["📦 git-mcp\ncommit, push, PR"]
        S4["🏔️ vladOS-mcp\ndeploy, provision"]
        S5["🌐 web3-mcp\nIPFS, UCAN, DID"]
    end

    DSPY_A & LG_A & RAW_A --> MCP_C
    MCP_C --> S1 & S2 & S3 & S4 & S5
```

**Web3 readiness:** MCP уже protocol-neutral. Добавить web3-mcp server = подключить IPFS/UCAN/DID tools без изменения агентов.

---

## 🏭 The Factory: как всё собирается

### Factory = Hyper-Porto проект внутри sandboxai-ячейки

```mermaid
flowchart TB
    subgraph VLADOS["🏔️ vladOS Infrastructure"]
        HOST["Server host"]
    end

    subgraph SANDBOX_CELL["🧬 sandboxai Cell (preset: ai-agent)"]
        subgraph FACTORY_PROJECT["🏭 Factory (Hyper-Porto project)"]

            subgraph SHIP_L["🚢 Ship"]
                CONFIGS["Configs"]
                AUTH["Auth"]
                INFRA["Infrastructure\n(MCP Client, DSPy LM)"]
            end

            subgraph STRATEGIC_S["🧭 Strategic Section"]
                META_M["MetaThinkerModule\n(DSPy ChainOfThought)"]
                CTX_M["ContextManagerModule\n(DSPy + AgentFold)"]
            end

            subgraph EXECUTION_S["🏗️ Execution Section"]
                DECOMP_M["DecomposerModule\n(MAKER MAD → CellSpecs)"]
                VOTER_M["VoterModule\n(Parallel Cells → Vote)"]
                FILTER_M["FilterModule\n(Red-Flag → Evidence)"]
            end

            subgraph AGENT_S["🤖 Agent Section"]
                DSPY_M["DSPyAgentModule\n(ReAct + MCP tools)"]
                OPTIM["OptimizerModule\n(MIPROv2 auto-improve)"]
            end

            subgraph INTAKE_S["📥 Intake Section"]
                FW_M["FileWatcherModule"]
                API_M["APIModule"]
                MCP_INTAKE["MCPServerModule"]
            end
        end
    end

    HOST --> SANDBOX_CELL
```

### Поток задачи через Factory

```mermaid
sequenceDiagram
    participant SRC as 📥 Источник
    participant INTAKE as 📥 Intake Section
    participant META as 🧭 MetaThinker
    participant CTX as 📋 ContextManager
    participant DECOMP as ✂️ Decomposer
    participant AGENT as 🤖 DSPy Agent
    participant SANDBOX as 🧬 sandboxai
    participant VOTER as 🗳️ Voter
    participant FILTER as 🚩 Filter
    participant EVIDENCE as 📦 Evidence

    SRC->>INTAKE: Задача (файл / API / MCP)

    INTAKE->>META: Анализ задачи
    META->>META: Стратегический план
    META->>CTX: Сформировать контекст
    CTX->>DECOMP: Brief + план

    DECOMP->>DECOMP: MAD: задача → микрозадачи
    DECOMP->>SANDBOX: Spawn K ячеек на микрозадачу

    loop Для каждой микрозадачи
        SANDBOX->>AGENT: Запустить DSPy ReAct в ячейке
        AGENT->>AGENT: Работа (через MCP tools)
        AGENT-->>SANDBOX: Результат
    end

    SANDBOX-->>VOTER: K результатов
    VOTER->>VOTER: Голосование
    VOTER->>FILTER: Победитель
    FILTER->>FILTER: Red-Flag проверка

    alt Passed
        FILTER->>EVIDENCE: ✅ Evidence Bundle
    else Failed
        FILTER->>META: 🚩 Пересмотреть стратегию
        META->>DECOMP: Новый план
    end

    META->>CTX: Обновить контекст (fold)
    EVIDENCE->>SRC: 📦 Результат + доказательства
```

---

## 🌐 Web3 Readiness: почему архитектура готова

### Каждый слой = adapter swap, не перестройка

```mermaid
flowchart LR
    subgraph WEB2["🌐 Web2 (сейчас)"]
        W2_INFRA["SSH + SOPS + deploy-rs"]
        W2_STORE["Local FS + Git + S3"]
        W2_COMPUTE["Local process + Docker"]
        W2_AUTH["JWT + API keys"]
        W2_EVENTS["PostgreSQL + Redis"]
    end

    subgraph WEB3["🌐 Web3 (потом)"]
        W3_INFRA["DID + UCAN + P2P"]
        W3_STORE["IPFS + Filecoin + Arweave"]
        W3_COMPUTE["Bacalhau + IPVM + ICP"]
        W3_AUTH["UCAN + Internet Identity"]
        W3_EVENTS["Ceramic + OrbitDB"]
    end

    W2_INFRA -.->|"adapter swap"| W3_INFRA
    W2_STORE -.->|"adapter swap"| W3_STORE
    W2_COMPUTE -.->|"adapter swap"| W3_COMPUTE
    W2_AUTH -.->|"adapter swap"| W3_AUTH
    W2_EVENTS -.->|"adapter swap"| W3_EVENTS
```

### Почему каждый паттерн web3-compatible

| Паттерн | Web2 реализация | Web3 аналог | Почему совместимо |
|---------|----------------|-------------|-------------------|
| **CellSpec (CID)** | SHA256 hash | IPFS CID | Контент-адресация = один механизм |
| **Capabilities** | RBAC/JWT | UCAN tokens | Capability-based = native web3 |
| **Event Sourcing** | PostgreSQL append-only | Blockchain ledger | Append-only = blockchain по определению |
| **Result[T, E]** | Python returns lib | Deterministic execution | Детерминизм = WASM-compatible |
| **K-Voting** | Parallel processes | Consensus mechanism | Голосование = BFT consensus |
| **Evidence Bundle** | JSON + hashes | Merkle proof | Доказуемость = zero-knowledge ready |
| **Porto Containers** | Python modules | Smart contracts | Модульная изоляция = contract boundaries |
| **Gateway Pattern** | Direct/HTTP adapter | On-chain/off-chain adapter | Adapter pattern = protocol-neutral |
| **Saga Pattern** | Temporal workflow | Cross-chain transaction | Компенсации = atomic swaps |
| **DSPy Signatures** | Prompt compilation | On-chain verified prompts | CID-addressable artifacts |

---

## 🧬 Связь с AIOBSH

В `COMPASS_MAKER_LITESTAR_PORTO/AIOBSH_ARCHITECTURE_RU.md` ты уже однажды сводил всё это вместе:

```text
AIOBSH = COMPASS × MAKER × Litestar × PORTO × Nix
```

**The Factory = AIOBSH v2**, но с тремя ключевыми отличиями:

| Аспект | AIOBSH (v1) | Factory (v2) |
|--------|-------------|--------------|
| **AI layer** | Свой orchestration | **DSPy** (auto-optimization, MCP native) |
| **Environment** | Nix shells | **sandboxai** (CID, Supervisor, Capabilities) |
| **Tool integration** | Кастомные интеграции | **MCP** (стандарт, framework-agnostic) |
| **Web3** | Упоминание | **Adapter families** (спроектировано) |
| **Self-improvement** | Задумка | **DSPy Optimizers** (реализовано в DSPy) |

---

## 📐 Единая формула

```text
The Grand Architecture =

  vladOS(Infrastructure)
    └── sandboxai(Environment: CellSpec + Supervisor + Capabilities + Adapters)
          └── Hyper-Porto(Project: Ship + Containers + Actions + Tasks + Events)
                ├── COMPASS(Strategy: MetaThinker + ContextManager)
                ├── MAKER(Reliability: MAD + K-Voting + Red-Flagging)
                ├── DSPy(Intelligence: Signatures + Modules + Optimizers)
                └── MCP(Tools: framework-agnostic protocol)
```

### Каждый слой отвечает на свой вопрос

| Вопрос | Слой | Ответ |
|--------|------|-------|
| **ГДЕ** физически? | vladOS | На этом хосте, в этой сети, с этими секретами |
| **В ЧЁМ** изолированно? | sandboxai | В этой ячейке, с этими правами, с этим бюджетом |
| **КАК** организован код? | Hyper-Porto | Ship + Containers, Actions, Result Railway |
| **КУДА** двигаться? | COMPASS | Стратегия, мониторинг, корректировка курса |
| **НАСКОЛЬКО** надёжно? | MAKER | MAD, голосование, фильтрация ненадёжных |
| **КАК** улучшаться? | DSPy | Оптимизация промптов и весов по метрикам |
| **ЧЕМ** работать? | MCP | Стандартные tools, framework-agnostic |

---

## 🔮 Вектор

```mermaid
timeline
    title 🔮 Путь от web2 к web3
    section Сейчас (web2)
        vladOS + sandboxai local : Инфраструктура и окружения работают
        Hyper-Porto + DSPy : Первый Factory проект внутри ячейки
        MCP tools : sandboxai-mcp + filesystem-mcp + git-mcp
    section Скоро (hybrid)
        IPFS для артефактов : Content-addressable storage
        DID для идентичности : Decentralized identity
        Bacalhau для compute : Distributed batch execution
    section Потом (web3-native)
        UCAN для capabilities : Token-based authorization
        ICP для sovereign runtime : On-chain execution
        Filecoin для durability : Permanent storage
        P2P для discovery : Decentralized networking
```

### 🔑 Почему путь не требует перестройки

Каждый шаг — это **adapter swap**, не рефакторинг:

```python
# Сейчас (web2)
artifact_store = LocalFSAdapter()

# Скоро (hybrid)
artifact_store = IPFSAdapter(fallback=LocalFSAdapter())

# Потом (web3)
artifact_store = FilecoinAdapter(cache=IPFSAdapter())
```

Код Factory, COMPASS-модулей, MAKER-логики, DSPy-программ — **не меняется**. Меняются только адаптеры.

---

## ❤️ Финальная мысль

Ты не строишь «AI-фреймворк». Ты строишь **операционную систему для суверенных вычислений**, где:

- **vladOS** = kernel (управление железом)
- **sandboxai** = process isolation (контейнеры и права)
- **Hyper-Porto** = application framework (как писать приложения)
- **COMPASS+MAKER** = cognitive architecture (как думать и действовать надёжно)
- **DSPy** = learning subsystem (как становиться лучше)
- **MCP** = syscall interface (как общаться с миром)

И всё это **с первого дня архитектурно готово** к web3, потому что каждый паттерн (CID, Capabilities, Event Sourcing, Result Railway, Adapter Families, K-Voting, Evidence) — это **web3-native паттерн**, который пока работает на web2-инфраструктуре.

```text
Web2 — это не ограничение. Это начальные адаптеры.
Web3 — это не миграция. Это замена адаптеров.
Архитектура — одна и та же.
```
