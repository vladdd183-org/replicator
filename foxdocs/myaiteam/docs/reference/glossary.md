# 📚 Глоссарий терминов

> **Связанные документы:**
> - [Architecture Overview](../architecture/overview.md)
> - [Relation Types](relation-types.md)

---

## A

### A2A (Agent-to-Agent Protocol)
Протокол от Google + Linux Foundation для коммуникации между AI-агентами. Включает Agent Cards (capability discovery), Context Exchange и разные Communication Modes.

### ACC (Access Control Conditions)
Условия доступа в Lit Protocol. Определяют, кто может расшифровать данные (владельцы NFT, адреса из allowlist, держатели токенов и т.д.).

### Atom
Базовая единица в Knowledge Graph. Типы: Entity (сущность), Claim (утверждение), Chunk (текстовый фрагмент), Event (событие), Concept (абстрактное понятие).

---

## C

### Ceramic
Decentralized data network для мутабельных структурированных данных. Использует Streams (append-only logs) и ComposeDB (GraphQL queries).

### CID (Content Identifier)
Идентификатор контента в IPFS. Вычисляется как хэш содержимого файла. Одинаковый контент = одинаковый CID везде.

### Complementarity
Принцип Human-AI collaboration — понимание того, кто (человек или AI) в чём силён и как лучше распределить задачи.

### ComposeDB
GraphQL layer поверх Ceramic streams. Позволяет определять схемы данных и выполнять структурированные запросы.

### Confidence Score
Уровень уверенности AI в своём ответе (0.0 - 1.0). Используется для калибровки доверия: >85% можно принять, 60-85% требует review, <60% требует human decision.

### Context Graph
Расширение триплетов обязательным контекстом (temporal, provenance, confidence, modality).

### CRDT (Conflict-free Replicated Data Type)
Структуры данных, которые автоматически разрешают конфликты при параллельном редактировании. Используются в OrbitDB.

---

## D

### DID (Decentralized Identifier)
Децентрализованный идентификатор. Формат: `did:method:specific-identifier`. Примеры: `did:key:z6Mk...`, `did:web:example.com`.

### DKG (Decentralized Knowledge Graph)
Децентрализованный граф знаний. OriginTrail DKG — конкретная реализация с public/private assertions.

### DNSLink
Механизм для человекочитаемых URL в IPFS. DNS TXT record указывает на IPNS или CID.

---

## E

### Embedding
Векторное представление текста/сущности в многомерном пространстве. Используется для semantic search и similarity.

### Entity Resolution
Процесс определения, когда два упоминания относятся к одной сущности. Включает coreference, cross-document linking, multimodal matching.

### Escalation
Передача задачи от AI к человеку при низкой уверенности, запросе пользователя или обнаружении проблем.

---

## G

### GraphRAG
RAG-система от Microsoft. Использует Knowledge Graph + Leiden clustering + Community summaries для ответов на вопросы.

---

## H

### Handoff
Передача контекста при эскалации от AI к человеку. Включает summary, actions taken, suggested next steps.

### Hyper-Relational KG
Граф знаний с n-арными отношениями (квинтеты + квалификаторы вместо бинарных триплетов).

### Hypergraph
Граф, в котором гиперребро может соединять произвольное количество узлов (не только 2).

---

## I

### IPFS (InterPlanetary File System)
Децентрализованное хранилище файлов. Content-addressed — файлы идентифицируются по хэшу содержимого (CID).

### IPLD (InterPlanetary Linked Data)
Data model для связанных данных в IPFS. Позволяет ссылаться на объекты по CID.

### IPNS (InterPlanetary Name System)
Система мутабельных указателей в IPFS. IPNS name остаётся постоянным, но может указывать на разные CID.

---

## K

### Knowledge Asset
В OriginTrail DKG — единица знаний с public и private assertions. Имеет NFT для владения и UAL для идентификации.

### Knowledge Graph Embeddings
Векторные представления сущностей и связей графа. Модели: TransE (евклидово), HypHKGE (гиперболическое), ComplEx (комплексное).

---

## L

### Leiden Algorithm
Алгоритм кластеризации графов. Используется в GraphRAG для построения иерархии сообществ.

### LightRAG
RAG-система с dual-level indexing (entities + concepts). 14.6x быстрее GraphRAG в построении.

### Lit Protocol
Децентрализованный протокол для шифрования с контролем доступа. Ключ разделён между нодами, расшифровка требует проверки условий.

---

## M

### MCP (Model Context Protocol)
Протокол для предоставления контекста AI-моделям. Позволяет агентам получать доступ к инструментам и данным.

### Mental Model
Внутреннее понимание человеком того, как что-то работает. В Human-AI — понимание возможностей и ограничений AI.

### MFS (Mutable File System)
Файловая система поверх IPFS. Позволяет работать с путями вместо CID.

---

## O

### OrbitDB
P2P database на основе IPFS с поддержкой CRDTs. Подходит для real-time collaboration.

### OriginTrail DKG
Готовое решение для децентрализованного Knowledge Graph. Public/Private assertions, SPARQL queries, NFT ownership.

---

## P

### PubSub (Publish/Subscribe)
Механизм real-time messaging в IPFS. Подписка на топики, получение сообщений от всех publishers.

---

## R

### RAG (Retrieval-Augmented Generation)
Подход к генерации, при котором LLM получает релевантный контекст из базы знаний перед ответом.

### RAPTOR
RAG-система с древовидной организацией. Рекурсивное суммирование чанков для multi-resolution retrieval.

### Reification
Паттерн моделирования — превращение связи в сущность для добавления метаданных.

---

## S

### Semantic Unit
Альтернатива триплетам — модулярный, семантически осмысленный подграф с контекстом и метаданными.

### Shared Context
Общее информационное пространство для людей и AI-агентов. Включает situational awareness, knowledge base, communication history.

### Stream
В Ceramic — append-only log of events. Каждый event подписан DID автора.

---

## T

### Trust Calibration
Процесс настройки уровня доверия к AI так, чтобы он соответствовал реальной надёжности. Избегание over-trust и under-trust.

### Triplestore
База данных для хранения RDF триплетов (Subject, Predicate, Object).

---

## U

### UAL (Universal Asset Locator)
Идентификатор Knowledge Asset в OriginTrail DKG.

### UCAN (User Controlled Authorization Networks)
Capability-based authorization без центрального сервера. Токены с delegation chain и атенуацией прав.

---

## V

### Vector Search
Поиск по семантической близости с использованием embeddings. Базы: Qdrant, Milvus, ChromaDB.

### Verifiable Credentials (VC)
Криптографически подписанные утверждения о субъекте. Стандарт W3C для децентрализованной идентификации.

---

## Связанные термины

| Термин | См. также |
|--------|-----------|
| Content addressing | CID, IPFS |
| Decentralized identity | DID, UCAN, VC |
| Knowledge representation | Semantic Unit, Triplestore, IPLD |
| Multi-agent | A2A, MCP, CrewAI |
| Privacy | Lit Protocol, ACC, Encryption |
| Real-time | PubSub, OrbitDB, CRDT |

---

*Обновлено: 2 февраля 2026*
