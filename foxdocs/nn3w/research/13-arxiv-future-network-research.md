# 13. Научные концепции будущей сети — обзор arXiv 2024–2026

> Обзор ключевых исследований с arXiv о том, какой учёные видят архитектуру
> будущего интернета: Agentic Web, децентрализованные протоколы, AI-native
> сети, программируемые знания и Web3 × AI.

## Оглавление

1. [Общий тренд: от Интернета информации к Интернету агентов](#1-общий-тренд)
2. [Agentic Web — ткань нового интернета](#2-agentic-web)
3. [Agent-OSI — эталонный стек для децентрализованной сети агентов](#3-agent-osi)
4. [Agent Network Protocol (ANP) — коммуникационный протокол Agentic Web](#4-anp)
5. [Модели доверия между агентами — A2A, AP2, ERC-8004](#5-модели-доверия)
6. [Web3 × AI Agents — ландшафт и интеграции](#6-web3-x-ai)
7. [ETHOS — децентрализованное управление автономными AI-агентами](#7-ethos)
8. [Децентрализованная идентичность агентов — DIAP и ZKP](#8-diap)
9. [Архитектуры надёжного агентного AI](#9-архитектуры)
10. [Semantic Web: прошлое, настоящее и будущее](#10-semantic-web)
11. [Верифицируемые вычисления и zkVC](#11-zkvc)
12. [Децентрализованные графы знаний — Pistis и SHIMI](#12-dkg)
13. [Сводная карта: как это соотносится с nn3w](#13-карта)
14. [Библиография](#14-библиография)

---

## 1. Общий тренд

Научное сообщество фиксирует фундаментальный сдвиг: **Интернет трансформируется
из сети документов (Web 1.0 → 2.0 → 3.0) в сеть автономных агентов (Agentic Web)**.

Четыре ключевых тренда, выделяемых исследователями [ANP, 2508.00007]:

| # | Тренд | Суть |
|---|-------|------|
| 1 | Агенты заменяют софт | AI-ассистенты → основной интерфейс пользователя с интернетом |
| 2 | Универсальное соединение | Любой агент может найти и связаться с любым другим |
| 3 | Нативные протоколы | Не HTTP/HTML для людей, а AI-native структурированные данные |
| 4 | Самоорганизация | Агенты автономно формируют коллаборации через переговоры |

**Ключевая проблема**: существующая инфраструктура интернета спроектирована
для людей — GUI, HTML, centralized auth. Это создаёт:
- **Дата-силосы** — данные заперты в платформах
- **Недружественные интерфейсы** — агентам приходится «симулировать человека»
- **Высокая стоимость коллаборации** — нет стандартного протокола agent↔agent

---

## 2. Agentic Web

> **"Agentic Web: Weaving the Next Web with AI Agents"**
> Yang et al., Jul 2025 — [arXiv:2507.21206](https://arxiv.org/abs/2507.21206)
> Авторы: Pieter Abbeel, Dawn Song, Jun Wang et al.

### Концепция

Agentic Web — **новая фаза интернета**, определяемая автономными, целеуправляемыми
взаимодействиями. Агенты взаимодействуют напрямую друг с другом для планирования,
координации и выполнения задач от имени пользователей.

### Три измерения фреймворка

```
┌─────────────────────────────────────────────┐
│            AGENTIC WEB FRAMEWORK            │
├───────────────┬──────────────┬──────────────┤
│  INTELLIGENCE │ INTERACTION  │  ECONOMICS   │
├───────────────┼──────────────┼──────────────┤
│ • Retrieval   │ • A2A proto  │ • Agent      │
│ • Recommend   │ • Orchestr   │   Attention  │
│ • Planning    │ • Communic   │   Economy    │
│ • Collaborat  │ • Discovery  │ • Incentives │
└───────────────┴──────────────┴──────────────┘
```

### Agent Attention Economy

Новая парадигма экономики: **внимание агентов** как ресурс. Аналогично тому, как
в Web 2.0 ценилось внимание пользователей, в Agentic Web ценится:
- **Вычислительное время** агентов
- **Качество обработки запросов**
- **Репутация и trust score** агента в сети

### Эволюция эпох

```
PC Web (1990s)          → документы, гиперссылки
Mobile Web (2010s)      → приложения, API, платформы
Agentic Web (2025+)     → агенты, протоколы, самоорганизация
```

---

## 3. Agent-OSI

> **"Agent-OSI: A Layered Protocol Stack Toward a Decentralized Internet of Agents"**
> Xu et al., Feb 2026 — [arXiv:2602.13795](https://arxiv.org/abs/2602.13795)

### Самая свежая работа (февраль 2026)

Agent-OSI предлагает **шестислойный эталонный стек** для децентрализованной
сети агентов, построенный поверх существующего интернета:

```
┌──────────────────────────────────────────────┐
│  Layer 6: SEMANTIC INTEROPERABILITY          │
│  → оркестрация, семантическое понимание      │
├──────────────────────────────────────────────┤
│  Layer 5: VERIFIABLE EXECUTION & PROVENANCE  │
│  → доказуемость вычислений, происхождение    │
├──────────────────────────────────────────────┤
│  Layer 4: SETTLEMENT & METERING             │
│  → оплата, учёт ресурсов, HTTP 402          │
├──────────────────────────────────────────────┤
│  Layer 3: IDENTITY & AUTHORIZATION          │
│  → DID, decentralized auth, ZKP             │
├──────────────────────────────────────────────┤
│  Layer 2: A2A MESSAGING                     │
│  → agent-to-agent обмен сообщениями          │
├──────────────────────────────────────────────┤
│  Layer 1: SECURE CONNECTIVITY               │
│  → TLS, QUIC, существующий транспорт         │
└──────────────────────────────────────────────┘
```

### Ключевые инновации

- **HTTP 402 как payment challenge**: аналогично HTTP 401 для аутентификации,
  HTTP 402 триггерит escrow-based settlement через блокчейн
- **Off-chain negotiation**: переговоры и доставка off-chain, только settlement
  on-chain → **снижение стоимости on-chain сессий на ~51%**
- **Verifiable receipts**: криптографические квитанции для доказательства выполнения
- Совместимость с существующей инфраструктурой интернета

### Пересечение с nn3w

Agent-OSI подтверждает архитектурный подход nn3w — слоистая система,
где каждый уровень отвечает за свою функцию (identity, transport, settlement,
execution), и где верифицируемость — core principle.

---

## 4. ANP

> **"Agent Network Protocol Technical White Paper"**
> Chang et al., Jul 2025 — [arXiv:2508.00007](https://arxiv.org/abs/2508.00007)

### Трёхслойная архитектура протокола

```
┌──────────────────────────────────────────┐
│  APPLICATION PROTOCOL LAYER              │
│  ┌────────────────┬────────────────┐     │
│  │ ADP (Agent     │ Agent          │     │
│  │ Description    │ Discovery      │     │
│  │ Protocol)      │ Protocol       │     │
│  └────────────────┴────────────────┘     │
├──────────────────────────────────────────┤
│  META-PROTOCOL LAYER                     │
│  → динамическая NL-переговорная          │
│    адаптация протоколов                  │
├──────────────────────────────────────────┤
│  IDENTITY & ENCRYPTED COMMUNICATION      │
│  → W3C DID (did:wba), ECDHE E2E         │
└──────────────────────────────────────────┘
```

### Мета-протокольный уровень

Революционная идея: агенты **на естественном языке** договариваются о формате
коммуникации. Процесс:

1. **Agent A → Agent B**: мета-протокольный запрос (NL-описание потребностей +
   кандидатные протоколы)
2. **Agent B**: AI анализирует запрос, предлагает свои варианты
3. **Negotiation**: итеративный процесс до консенсуса
4. **Code generation**: обе стороны генерируют обработчик протокола
5. **Joint testing**: совместное тестирование
6. **Formal communication**: переход к продакшену

### AI-Native Data Network

ANP предлагает полностью новую **сеть данных для AI** (а не для людей):
- Каждый узел — описываемый, обнаруживаемый, вызываемый агент
- Каждая связь — семантически ясное, структурно единообразное соединение
- Агенты читают JSON-LD description documents вместо HTML-страниц

### Agent Description Protocol (ADP)

Каждый агент публикует свою «визитку» в формате JSON-LD:
- Базовая информация (имя, ID, принадлежность)
- Capabilities (что умеет)
- Interfaces (API endpoints, поддерживаемые протоколы)
- Security (DID, public key)
- Contact (для fallback к человеку)

### Agent Discovery Protocol

Два механизма обнаружения:
- **Active**: `/.well-known/agent-descriptions` — аналог `robots.txt` для агентов
- **Passive**: регистрация в поисковых агентах через API

### Безопасность

- **Human Authorization vs Agent Authorization**: разделение на low-risk (агент
  решает автономно) и high-risk (требуется подтверждение человека)
- **Multi-DID strategy**: разные DID для разных контекстов
- **Minimal Information Disclosure**: передача только необходимых полей
- **E2E encryption**: ECDHE между DID-парами ключей

---

## 5. Модели доверия

> **"Inter-Agent Trust Models: Brief, Claim, Proof, Stake, Reputation, Constraint"**
> Hu & Rong, Nov 2025 — [arXiv:2511.03434](https://arxiv.org/abs/2511.03434)

### Шесть моделей доверия для Agentic Web

| Модель | Описание | Сила | Слабость |
|--------|----------|------|----------|
| **Brief** | Верифицируемые заявления (self или 3rd party) | Быстрая идентификация | Не гарантирует поведение |
| **Claim** | Самозаявленные capabilities (AgentCard) | Простота | Легко фальсифицировать |
| **Proof** | Криптографическая верификация (ZKP, TEE) | Математическая гарантия | Вычислительно дорого |
| **Stake** | Залоговое обеспечение + slashing | Экономический стимул | Барьер входа |
| **Reputation** | Crowd feedback, graph-based trust | Социальная адаптивность | Sybil attacks, gaming |
| **Constraint** | Sandboxing, capability bounding | Ограничение ущерба | Снижает функциональность |

### Конкретные протоколы

- **Google A2A (Agent-to-Agent)** — claim-based с AgentCard
- **AP2 (Agent Payments Protocol)** — stake + proof для финансовых транзакций
- **ERC-8004 "Trustless Agents"** — Ethereum standard для trustless операций

### Главный вывод

> **Ни одна модель доверия не достаточна сама по себе.** Необходимы гибридные
> архитектуры: **Proof + Stake** для high-impact действий, **Brief** для
> идентификации, **Reputation** как overlay для гибкости.

### LLM-специфические уязвимости

Работа особо выделяет проблемы LLM-агентов:
- Prompt injection → agent manipulation
- Sycophancy / nudge-susceptibility → social engineering
- Hallucination → false claims
- Deception → misaligned behaviour
- Misalignment → goal divergence

Эти уязвимости делают **claim-only и reputation-only подходы хрупкими** —
нужна криптографическая основа (Proof) как фундамент.

---

## 6. Web3 × AI

> **"Web3 x AI Agents: Landscape, Integrations, and Foundational Challenges"**
> Shen et al., Aug 2025 — [arXiv:2508.02773](https://arxiv.org/abs/2508.02773)

### Масштаб исследования

Первый comprehensive анализ пересечения Web3 и AI agents:
**133 проекта**, 5 измерений.

### Пять измерений анализа

```
┌─────────────────────────────────────────────────┐
│              WEB3 × AI AGENTS                   │
├──────────┬───────────┬──────────┬───────┬───────┤
│ LANDSCAPE│ ECONOMICS │GOVERNANCE│SECURITY│ TRUST │
├──────────┼───────────┼──────────┼───────┼───────┤
│ Taxonomy │ DeFi      │ DAOs     │ Vuln  │ Trust │
│ 133 proj │ optimiz   │ enhanced │ detect│ infra │
│ Market   │ Agent     │ by AI    │ Smart │ for   │
│ mapping  │ trading   │ agents   │ audit │ agents│
└──────────┴───────────┴──────────┴───────┴───────┘
```

### Ключевые интеграции

1. **AI → DeFi**: агенты участвуют в и оптимизируют децентрализованные финансы
2. **AI → Governance**: агенты улучшают DAO-управление
3. **AI → Security**: интеллектуальный аудит смарт-контрактов, обнаружение уязвимостей
4. **Web3 → AI Trust**: инфраструктура доверия Web3 как reliability framework
   для AI-агентов

### Основные вызовы

- **Scalability**: блокчейн-подтверждения → latency bottleneck
- **Security**: новые attack vectors на стыке AI и Web3
- **Ethics**: автономные агенты с доступом к финансам и governance

---

## 7. ETHOS

> **"Decentralized Governance of Autonomous AI Agents"**
> Chaffer et al., Dec 2024 — [arXiv:2412.17114](https://arxiv.org/abs/2412.17114)

### ETHOS Framework

**Ethical Technology and Holistic Oversight System** — модель
децентрализованного управления через Web3:

```
┌─────────────────────────────────────────────┐
│              ETHOS FRAMEWORK                │
├─────────────────────────────────────────────┤
│  Global AI Agent Registry                   │
│  → DID-based, decentralized                 │
├─────────────────────────────────────────────┤
│  Dynamic Risk Classification                │
│  → автоматическая оценка рисков             │
├─────────────────────────────────────────────┤
│  Soulbound Tokens (SBTs)                    │
│  → non-transferable identity + compliance   │
├─────────────────────────────────────────────┤
│  Zero-Knowledge Proofs                      │
│  → compliance monitoring без раскрытия данных│
├─────────────────────────────────────────────┤
│  Decentralized Justice System               │
│  → dispute resolution через DAO             │
├─────────────────────────────────────────────┤
│  AI Legal Entities + Insurance              │
│  → limited liability + accountability       │
└─────────────────────────────────────────────┘
```

### Применимость к nn3w

ETHOS предлагает именно тот тип governance, который нужен для
«программируемого интернета знаний»:
- Реестр агентов с DID → наша модель identity
- SBTs → non-transferable credentials для Knowledge Contracts
- ZKP → privacy-preserving verification
- DAO → decentralized dispute resolution для Knowledge Exchange Contracts

---

## 8. DIAP

> **"DIAP: A Decentralized Agent Identity Protocol with ZKP and Hybrid P2P Stack"**
> Nov 2025 — [arXiv:2511.11619](https://arxiv.org/abs/2511.11619)

### Архитектура

DIAP — протокол идентичности для агентов, комбинирующий:

- **IPFS/IPNS content identifiers** — адресация агентов через content-addressed ID
- **Zero-Knowledge Proofs** — доказательство владения identity без раскрытия
  приватных данных и без обновления записей
- **Libp2p GossipSub** — P2P discovery агентов
- **Iroh** — высокопроизводительный QUIC-based обмен данными

### Связь с нашим стеком

DIAP напрямую использует **IPFS + libp2p** — те же технологии, что в основе nn3w.
Это подтверждает, что наш выбор IPFS + Ceramic + libp2p как фундамента —
в мейнстриме исследований.

---

## 9. Архитектуры

> **"Architectures for Building Agentic AI"**
> Nowaczyk, Dec 2025 — [arXiv:2512.09458](https://arxiv.org/abs/2512.09458)

### Таксономия агентных архитектур

| Тип | Описание |
|-----|----------|
| Tool-using agents | Агенты с доступом к внешним инструментам |
| Memory-augmented agents | + persistent memory с provenance |
| Planning & self-improvement | + планирование и саморефлексия |
| Multi-agent systems | Координация нескольких агентов |
| Embodied / Web agents | Физическое или веб-воплощение |

### Компоненты надёжной агентной системы

```
┌────────────────────────────────────────────────┐
│          RELIABLE AGENT ARCHITECTURE           │
├────────────────┬───────────────────────────────┤
│ Goal Manager   │ определение и декомпозиция    │
│ Planner        │ генерация планов действий     │
│ Tool Router    │ маршрутизация к инструментам  │
│ Executor       │ выполнение с контролем        │
│ Memory         │ persistent + provenance       │
│ Verifiers      │ проверка результатов          │
│ Safety Monitor │ guardrails + budget control   │
│ Telemetry      │ мониторинг + observability    │
└────────────────┴───────────────────────────────┘
```

### Принципы проектирования

- **Typed schemas** — строгая типизация всех интерфейсов
- **Idempotency** — повторные вызовы безопасны
- **Least-privilege** — минимальные permissions
- **Transactional semantics** — атомарность операций
- **Memory provenance** — отслеживание происхождения данных
- **Simulate-before-actuate** — тестирование перед действием
- **Budget + termination** — контроль ресурсов

---

## 10. Semantic Web

> **"Semantic Web: Past, Present, and Future"**
> Scherp et al., Dec 2024 — [arXiv:2412.17159](https://arxiv.org/abs/2412.17159)

### Эволюция Semantic Web Layer Cake

Классическая архитектура Semantic Web обновлена с учётом:
- **Provenance** — откуда данные, кто их создал
- **Security & Trust** — верификация источников
- **Industry-led contributions** — практические решения из индустрии

### ML + Knowledge Graphs

- **Shallow ML** (embedding, link prediction) → расширение KG
- **Deep ML** (GNN, transformers) → reasoning по графу
- **LLMs + KG** — LLM как интерфейс к Knowledge Graphs:
  - KG → grounding для LLM (уменьшение hallucinations)
  - LLM → генерация/расширение KG
  - Гибридные RAG-системы

### Связь с nn3w Meta-Graph

Наш «гетерогенный-темпоральный-децентрализованный-мета-граф» —
это по сути **следующий шаг после Semantic Web**, где:
- Propositions вместо RDF-триплетов → сохранение контекста
- Temporal context → временная семантика
- Decentralized storage (Ceramic) → не centralized triple store
- LLM-native format → естественный язык как first-class citizen

---

## 11. zkVC

> **"zkVC: Fast Zero-Knowledge Proof for Private and Verifiable Computing"**
> Zhang et al., Apr 2025 — [arXiv:2504.12217](https://arxiv.org/abs/2504.12217)

### Верифицируемые вычисления

zkVC оптимизирует ZKP для матричных операций:
- **12x ускорение** proof generation по сравнению с предыдущими методами
- Применение к **верифицируемому ML** — клиент может проверить,
  что сервер честно выполнил inference
- **CRPC** (Constraint-reduced Polynomial Circuit) — уменьшение
  числа ограничений для матричного умножения

### Зачем это nn3w

Верифицируемые вычисления — ключевой компонент для
**Knowledge Computation Contracts**: доказательство того, что
AI-агент действительно выполнил обещанное вычисление
(embedding generation, RAG retrieval, inference) без доверия к нему.

---

## 12. DKG

### Pistis — Decentralized Knowledge Graph Platform

> VLDB 2025 — первая платформа для DKG с ownership-preserving SPARQL

- **Owner-managed E2E encryption**: каждый владелец шифрует свои данные
- **VO-SPARQL**: верифицируемые запросы по зашифрованным данным
- **Cross-owner queries**: запросы через данные нескольких владельцев
  с сохранением приватности

### SHIMI — Semantic Hierarchical Memory Index

> 2025 — иерархическая семантическая память для децентрализованных агентов

- **Динамическая иерархия концептов** вместо плоского vector store
- **Merkle-DAG summaries** — content-addressed синхронизация
- **CRDT-style conflict resolution** — eventual consistency
  для децентрализованного хранения
- Спроектирован для **decentralized agent collaboration**

### AGNTCY Agent Directory Service (ADS)

> 2025 — распределённое обнаружение AI-агентов

- **Content-addressed storage** для capability descriptions
- **Kademlia DHT** — распределённая хеш-таблица для обнаружения
- **OCI registry semantics** — интеграция с container ecosystem
- **Two-level mapping**: capability taxonomy → content location

---

## 13. Сводная карта

### Как научные концепции соотносятся с nn3w

```
┌──────────────────────────────────────────────────────────────┐
│                    НАУЧНАЯ КОНЦЕПЦИЯ                         │
│                         ↕                                    │
│                   КОМПОНЕНТ nn3w                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Agentic Web [2507.21206]                                    │
│    ↕ Наш AI Factory + oblakagent + Knowledge Contracts       │
│                                                              │
│  Agent-OSI 6-layer stack [2602.13795]                        │
│    ↕ nn3w sovereign stack layers                             │
│    ↕ (Identity → Transport → Settlement → Execution →       │
│       Verification → Semantic)                               │
│                                                              │
│  ANP Protocol [2508.00007]                                   │
│    ↕ Lattica (libp2p) + DID + Agent Description              │
│    ↕ Meta-protocol = наши Knowledge Exchange Contracts       │
│                                                              │
│  Trust Models [2511.03434]                                   │
│    ↕ UCAN (Brief) + Lit Protocol (Proof) +                   │
│       Ceramic anchoring (Stake) + Reputation overlay         │
│                                                              │
│  Web3 × AI [2508.02773]                                      │
│    ↕ Весь nn3w стек: IPFS + Ceramic + AI Agents              │
│                                                              │
│  ETHOS Governance [2412.17114]                               │
│    ↕ DAO governance для Knowledge Contracts                  │
│    ↕ SBTs + ZKP compliance monitoring                        │
│                                                              │
│  DIAP Identity [2511.11619]                                  │
│    ↕ IPFS/IPNS + libp2p + ZKP → наша identity layer          │
│                                                              │
│  Agentic AI Architecture [2512.09458]                        │
│    ↕ oblakagent + factory-ai-framework архитектура            │
│                                                              │
│  Semantic Web Evolution [2412.17159]                          │
│    ↕ Meta-Graph = next-gen Semantic Web                       │
│    ↕ Propositions > Triples = наш подход                     │
│                                                              │
│  zkVC Verifiable Compute [2504.12217]                        │
│    ↕ Knowledge Computation Contracts verification             │
│                                                              │
│  Pistis DKG [VLDB 2025]                                      │
│    ↕ Decentralized Knowledge Graph =                         │
│       ComposeDB + encrypted queries                          │
│                                                              │
│  SHIMI Memory [2025]                                         │
│    ↕ Hierarchical semantic memory для наших агентов           │
│    ↕ Merkle-DAG + CRDT = наш Ceramic/IPFS подход             │
│                                                              │
│  AGNTCY ADS [2025]                                           │
│    ↕ Agent Discovery через DHT =                             │
│       наш Agent Discovery Protocol                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Что nn3w делает, чего нет в отдельных работах

| Аспект | Отдельные работы | nn3w (наш стек) |
|--------|------------------|-----------------|
| Knowledge representation | RDF triples, vector stores | Meta-Graph с Propositions, temporal context, multimodal |
| Agent communication | A2A, MCP, ANP — каждый отдельно | Unified stack: Lattica (real-time) + Ceramic (mutable) + IPFS (immutable) |
| Identity | DID alone или blockchain alone | DID + UCAN + Lit Protocol + multi-layer |
| Infrastructure | Cloud-dependent или full blockchain | Nix-declarative, reproducible, sovereign |
| Build system | Docker, ad-hoc | Content-addressed Nix store (аналог IPFS для кода) |
| Programmability | Smart contracts (financial) | Knowledge Contracts (data, exchange, computation, composition) |
| Web2/Web3 bimodality | Обычно одно или другое | Dual-mode transport adapter на каждом уровне |

### Научное обоснование nn3w vision

Каждый ключевой компонент nn3w подтверждён независимым научным исследованием:

1. **Agentic Web** — подтверждает переход к agent-first интернету
2. **Agent-OSI** — подтверждает слоистую архитектуру с settlement + verification
3. **ANP** — подтверждает AI-native протоколы, DID, meta-protocol negotiation
4. **Trust Models** — подтверждают гибридный подход (Proof + Stake + Reputation)
5. **DIAP** — подтверждает IPFS + libp2p + ZKP как identity stack
6. **Pistis** — подтверждает decentralized KG с privacy-preserving queries
7. **SHIMI** — подтверждает Merkle-DAG + CRDT для agent memory
8. **zkVC** — подтверждает verifiable computation для trustless AI inference

---

## 14. Библиография

### Tier 1 — Архитектура будущей сети

| ID | Название | Авторы | Дата |
|----|----------|--------|------|
| [2602.13795](https://arxiv.org/abs/2602.13795) | Agent-OSI: A Layered Protocol Stack Toward a Decentralized Internet of Agents | Xu et al. | Feb 2026 |
| [2507.21206](https://arxiv.org/abs/2507.21206) | Agentic Web: Weaving the Next Web with AI Agents | Yang, Abbeel, Song et al. | Jul 2025 |
| [2508.00007](https://arxiv.org/abs/2508.00007) | Agent Network Protocol Technical White Paper | Chang et al. | Jul 2025 |
| [2304.06111](https://arxiv.org/abs/2304.06111) | Web3: The Next Internet Revolution | Wan et al. | Mar 2023 |

### Tier 2 — Доверие и управление

| ID | Название | Авторы | Дата |
|----|----------|--------|------|
| [2511.03434](https://arxiv.org/abs/2511.03434) | Inter-Agent Trust Models: Brief, Claim, Proof, Stake, Reputation, Constraint | Hu & Rong | Nov 2025 |
| [2508.02773](https://arxiv.org/abs/2508.02773) | Web3 × AI Agents: Landscape, Integrations, Challenges | Shen et al. | Aug 2025 |
| [2412.17114](https://arxiv.org/abs/2412.17114) | Decentralized Governance of Autonomous AI Agents (ETHOS) | Chaffer et al. | Dec 2024 |
| [2509.07131](https://arxiv.org/abs/2509.07131) | SoK: Security and Privacy of AI Agents for Blockchain | Romandini et al. | Sep 2025 |
| [2602.21012](https://arxiv.org/abs/2602.21012) | International AI Safety Report 2026 | Bengio et al. | Feb 2026 |

### Tier 3 — Идентичность и криптография

| ID | Название | Авторы | Дата |
|----|----------|--------|------|
| [2511.11619](https://arxiv.org/abs/2511.11619) | DIAP: Decentralized Agent Identity Protocol with ZKP | — | Nov 2025 |
| [2504.12217](https://arxiv.org/abs/2504.12217) | zkVC: Fast Zero-Knowledge Proof for Verifiable Computing | Zhang et al. | Apr 2025 |

### Tier 4 — Знания и семантика

| ID | Название | Авторы | Дата |
|----|----------|--------|------|
| [2412.17159](https://arxiv.org/abs/2412.17159) | Semantic Web: Past, Present, and Future | Scherp et al. | Dec 2024 |
| [2512.09458](https://arxiv.org/abs/2512.09458) | Architectures for Building Agentic AI | Nowaczyk | Dec 2025 |
| VLDB 2025 | Pistis: First Decentralized Knowledge Graph Platform | Zhou et al. | 2025 |

### Tier 5 — Инфраструктура и RAG

| ID | Название | Авторы | Дата |
|----|----------|--------|------|
| [2601.05264](https://arxiv.org/abs/2601.05264) | Engineering the RAG Stack | Wampler et al. | Nov 2025 |
| [2511.06455](https://arxiv.org/abs/2511.06455) | Multi-Agent System for Semantic Mapping to Knowledge Graphs | Trajanoska et al. | Nov 2025 |
| [2511.11017](https://arxiv.org/abs/2511.11017) | AI Agent-Driven Framework for Automated Product KG Construction | Peshevski et al. | Nov 2025 |

---

> **Вывод**: научное сообщество движется точно в том направлении, которое мы
> закладываем в nn3w. Термин **Agentic Web** стал общепринятым для обозначения
> следующей фазы интернета. Ключевые компоненты — DID identity, AI-native
> протоколы, verifiable computation, decentralized knowledge graphs, hybrid
> trust models — напрямую соответствуют архитектуре nn3w. Наше уникальное
> преимущество: **Nix-based declarative infrastructure** + **Meta-Graph с
> Propositions** + **Knowledge Contracts** + **Web2/Web3 bimodality** —
> эта комбинация не встречается ни в одной из рассмотренных работ.
