# 14. DAG — унифицирующая структура данных будущей сети

> DAG (Directed Acyclic Graph) — это не просто структура данных. Это
> фундаментальный паттерн, который лежит в основе IPFS, блокчейнов нового
> поколения, Git, Nix store, Ceramic, и по сути является «скелетом» всей
> децентрализованной инфраструктуры.

## Оглавление

1. [Что такое DAG и почему он везде](#1-что-такое-dag)
2. [Merkle-DAG — DAG с криптографической верификацией](#2-merkle-dag)
3. [IPFS: Merkle-DAG как ядро](#3-ipfs)
4. [IPLD — InterPlanetary Linked Data](#4-ipld)
5. [GHOST/PHANTOM/GHOSTDAG — DAG-консенсус Сомполинского](#5-ghost)
6. [Kaspa и DAGKnight — блокDAG нового поколения](#6-kaspa)
7. [Avalanche — Snow-протоколы и DAG-консенсус](#7-avalanche)
8. [BECP — Epidemic-консенсус для extreme-scale блокчейна](#8-becp)
9. [Nix Store — content-addressed DAG для софта](#9-nix)
10. [Ceramic — event streams как DAG](#10-ceramic)
11. [Merkle-CRDT — DAG для eventual consistency](#11-merkle-crdt)
12. [Сводная таблица: DAG everywhere](#12-сводная)
13. [Что это значит для nn3w](#13-nn3w)
14. [Библиография](#14-библиография)

---

## 1. Что такое DAG

**Directed Acyclic Graph** — ориентированный ациклический граф.

```
     ┌───┐
     │ A │
     └─┬─┘
    ┌──┴──┐
  ┌─┴─┐ ┌─┴─┐
  │ B │ │ C │
  └─┬─┘ └─┬─┘
    │   ┌──┘
  ┌─┴─┐ │
  │ D ├─┘
  └─┬─┘
  ┌─┴─┐
  │ E │
  └───┘
```

Три свойства:
1. **Directed** — рёбра имеют направление (от родителя к потомку)
2. **Acyclic** — нет циклов (невозможно вернуться к себе по рёбрам)
3. **Graph** — узлы могут иметь несколько родителей (в отличие от дерева)

### Почему DAG а не дерево

Дерево — частный случай DAG, где у каждого узла ровно один родитель.
DAG позволяет **ветвям сходиться** (конвергенция), что критически важно для:
- Параллельной обработки (блокчейн)
- Дедупликации (IPFS, Git, Nix)
- Конфликт-резолюции (CRDT)
- Слияния веток (Git merge)

---

## 2. Merkle-DAG

**Merkle-DAG** = DAG + криптографические хеши.

Каждый узел идентифицируется **хешем своего содержимого + хешей потомков**.

```
CID(A) = hash(payload_A + CID(B) + CID(C))
CID(B) = hash(payload_B + CID(D))
CID(C) = hash(payload_C + CID(D))
CID(D) = hash(payload_D + CID(E))
CID(E) = hash(payload_E)
```

### Ключевые свойства

| Свойство | Описание |
|----------|----------|
| **Иммутабельность** | Любое изменение узла меняет его CID → меняются CID всех предков |
| **Самоверификация** | Два узла с одинаковым CID = гарантированно идентичные поддеревья |
| **Content addressing** | Идентификация по содержимому, а не по расположению |
| **Строятся снизу вверх** | Сначала листья, потом родители (CID потомков нужны для родителя) |
| **Конвергенция** | Один узел может иметь нескольких родителей → дедупликация |

### Где используется

- **Git** — коммиты, деревья, блобы = Merkle-DAG
- **IPFS** — всё хранилище = Merkle-DAG
- **Nix** — store paths = content-addressed Merkle-DAG
- **Bitcoin/Ethereum** — Merkle tree транзакций (упрощённая версия)
- **Ceramic** — event streams = Merkle-DAG

---

## 3. IPFS

### Архитектура IPFS построена вокруг Merkle-DAG

```
┌──────────────────────────────────────┐
│           IPFS Protocol Stack        │
├──────────────────────────────────────┤
│  IPNS    — мутабельные указатели     │
├──────────────────────────────────────┤
│  MerkleDAG — ядро всего хранилища   │ ◄── DAG
├──────────────────────────────────────┤
│  Exchange — Bitswap (обмен блоками)  │
├──────────────────────────────────────┤
│  Routing  — DHT (Kademlia)           │
├──────────────────────────────────────┤
│  Network  — libp2p (транспорт)       │
└──────────────────────────────────────┘
```

### Как файл хранится в IPFS

Файл разбивается на **чанки** (по ~256KB), каждый получает свой CID.
Дальше строится Merkle-DAG:

```
         ┌─────────────────────┐
         │  Root CID           │
         │  (всего файла)      │
         └──┬────────┬─────┬───┘
       ┌────┘    ┌───┘     └────┐
  ┌────┴───┐ ┌──┴────┐  ┌──────┴──┐
  │ Chunk1 │ │ Chunk2│  │ Chunk3  │
  │ CID_1  │ │ CID_2 │  │ CID_3   │
  └────────┘ └───────┘  └─────────┘
```

Root CID = `hash(CID_1 + CID_2 + CID_3)` → один хеш = весь файл.

### CID (Content Identifier)

CID — это не просто хеш. Это самоописывающий идентификатор:

```
CID = <version><codec><multihash>
       │         │      │
       v1        │      sha2-256 + digest
                 │
                 dag-pb / dag-cbor / raw / ...
```

CID содержит:
- **Версию** (v0 или v1)
- **Кодек** — как интерпретировать данные (dag-pb, dag-cbor, raw...)
- **Мультихеш** — какой алгоритм хеширования + сам хеш

---

## 4. IPLD

> **IPLD (InterPlanetary Linked Data)** — это «тонкая талия» между форматами
> данных и их Merkle-DAG представлением. Это единый Data Model для ВСЕХ
> content-addressed данных.

### Ключевая идея

IPLD определяет **универсальную модель данных** (как AST, но без синтаксиса),
которая абстрагирует:

```
┌────────────────────────────────────────────────┐
│              APPLICATION                        │
│  (работает с Data Model, не знает о формате)    │
├────────────────────────────────────────────────┤
│        IPLD DATA MODEL                          │
│  maps, lists, strings, bytes, links, ...        │
├──────┬──────────┬──────────┬──────────┬─────────┤
│ JSON │  CBOR    │ dag-pb   │ dag-cbor │ git ... │
│ codec│  codec   │ codec    │ codec    │ codec   │
└──────┴──────────┴──────────┴──────────┴─────────┘
```

### Компоненты IPLD

| Компонент | Назначение |
|-----------|-----------|
| **Data Model** | JSON-подобный AST: maps, lists, strings, bytes, booleans, ints, floats, **links** |
| **Codecs** | Плагины сериализации: JSON, CBOR, dag-pb, dag-cbor, git... |
| **Blocks** | Единица сериализованных данных. Блок = то, что хешируется |
| **Links** | Ссылки через CID — кросс-блоковое связывание |
| **Pathing** | Unix-style пути по DAG: `/ipfs/Qm.../a/b/c` |
| **Selectors** | Декларативный формат для обхода DAG (какие узлы посетить) |
| **Schemas** | Типизация данных (struct, union, enum) с repr-стратегиями |
| **ADLs** | Advanced Data Layouts — encrypted data, HAMT, FBL (large files) |

### Schemas — типизация без Тьюринг-полноты

IPLD Schemas описывают два уровня:
- **Type information** — семантика (struct, union, enum)
- **Representation** — как данные выглядят на уровне Data Model

```
type Document struct {
  title   String
  chunks  [&Chunk]    # список ссылок на другие блоки
  author  &Identity   # ссылка на блок identity
} representation map
```

Schemas **не Тьюринг-полные** — проверка «подходит ли Schema к данным»
ограничена по вычислительной стоимости. Это позволяет делать
**feature detection** — пробовать несколько Schema подряд.

### ADLs — Advanced Data Layouts

ADL трансформирует одну Data Model структуру в другую:
- **HAMT** — огромные maps, разбитые на многие блоки
  (как B+ дерево, но выглядит как один map)
- **FBL** — огромные byte sequences через multi-block split
- **Encryption** — шифрование данных как Data Model трансформация

### Graphsync

Протокол обмена блоками, использующий Selectors:
- Описание «какие части DAG нужны» → минимум round-trips
- Эффективнее чем Bitswap для связанных блоков

### Тезис IPLD

> Используя IPLD, можно создать систему «как Git» (content-addressed,
> decentralized, excellent) **на порядок быстрее**, чем без неё.
> — ipld.io

---

## 5. GHOST

### Исследователи

**Йонатан Сомполинский** и **Авив Зоар** — Еврейский университет
в Иерусалиме. Создали семейство протоколов:

```
GHOST (2013) → PHANTOM (2018) → GHOSTDAG (2018/2021) → DAGKnight (2025)
```

### Проблема линейного блокчейна

```
Bitcoin: A → B → C → D → E     (линейная цепь)
              └→ C' (orphan!)   ← выброшен

Проблема: при ускорении создания блоков растёт число orphans
→ хешрейт дробится → безопасность падает
```

### GHOST (Greedy Heaviest Observed SubTree)

**Идея**: вместо «самая длинная цепь» → «самое тяжёлое поддерево».

```
                A
              / | \
            B   C   D
          / |     / | \
         E  F    G  H  I
         |       |
         J       K
```

GHOST учитывает ВСЕ блоки при выборе каноничной цепи.
Виталик Бутерин взял модификацию GHOST для Ethereum →
**uncle (ommer) blocks** получают частичные награды.

### PHANTOM / GHOSTDAG

**Эволюция**: от дерева к полноценному blockDAG.

```
Традиционный        BlockDAG
блокчейн:            (PHANTOM/GHOSTDAG):

A → B → C           A ──→ B ──→ D
                     │     ↑     ↑
                     └→ C ─┘     │
                          └──────┘
```

**PHANTOM** — оптимальный, но NP-hard алгоритм.
**GHOSTDAG** — жадная аппроксимация PHANTOM, работающая за O(k·n).

Ключевое свойство: GHOSTDAG разделяет блоки на:
- **Blue blocks** — честные (в основном DAG)
- **Red blocks** — потенциально атакующие (выпадающие из нормы)

Линейный порядок восстанавливается из DAG через **topological sort**
с приоритетом blue blocks.

### Формальные результаты

Из оригинальной статьи [ePrint 2018/104]:

> PHANTOM is the first protocol to achieve scalability without
> compromising security. It generalizes Nakamoto consensus to DAGs
> while maintaining the 50% honest majority threshold.

---

## 6. Kaspa

### BlockDAG в продакшене

**Kaspa** — первый блокчейн, реализующий GHOSTDAG в продакшене.

| Параметр | Bitcoin | Ethereum | Kaspa (Crescendo) |
|----------|---------|----------|-------------------|
| Блоков/сек | 1/600 | 1/12 | **10/sec** |
| TPS | ~7 | ~30 | **сотни** |
| Finality | ~60 мин | ~12 мин | **< 10 сек** |
| Структура | цепь | цепь + PoS | **blockDAG** |

### Crescendo (май 2025)

Hard fork, увеличивший скорость с 1 до **10 блоков в секунду**.
Sub-second confirmation times.

### DAGKnight (2025-2026)

Следующая эволюция от Michael Sutton и Yonatan Sompolinsky:

- **Адаптивный параметр k** (в GHOSTDAG k фиксирован) →
  автоматическая подстройка под условия сети
- **ZK Layer 1 ↔ Layer 2 bridge** — zero-knowledge мосты
  между L1 (DAG) и L2 (smart contracts)
- **MEV-resistance** — защита от front-running
- **Oracle-voting** — децентрализованные оракулы

### Архитектурная значимость

Kaspa доказывает, что **DAG-консенсус работает в реальных условиях**
и решает фундаментальную трилемму масштабируемости:

```
    Security ─────── Decentralization
         \             /
          \           /
           \         /
         Scalability

Traditional blockchain: выбери 2 из 3
BlockDAG (Kaspa):       все 3 одновременно
```

---

## 7. Avalanche

### Snow Protocol Family

**Emin Gün Sirer** (Cornell → Ava Labs) — создатель Snow протоколов.

| Протокол | Назначение |
|----------|-----------|
| **Snowball** | Бинарный консенсус (да/нет) |
| **Snowflake** | Промежуточный вариант |
| **Snowman** | Линейный блок-консенсус (текущий основной) |
| **Avalanche** | Исторический DAG-консенсус (заменён Snowman) |

### Как работает Snow-консенсус

В отличие от PBFT (all-to-all коммуникация, O(n²)):

```
Snow: Repeated Random Subsampled Voting

Раунд 1: Нода опрашивает k случайных нод
          → собирает ответы
          → обновляет свой preference

Раунд 2: Повторяет
          → preference усиливается или меняется

...

Раунд β: Консенсус достигнут с вероятностью 1-ε
```

**Сложность**: O(k·log(n)) вместо O(n²)
**Финализация**: ~1-2 секунды

### Subnet-архитектура

```
┌────────────────────────────────┐
│       PRIMARY NETWORK          │
│  ┌──────┬────────┬──────────┐  │
│  │P-Chain│C-Chain │ X-Chain  │  │
│  │(stake)│(EVM)   │(exchange)│  │
│  └──────┴────────┴──────────┘  │
├────────────────────────────────┤
│  SUBNET 1     SUBNET 2    ... │
│  (custom      (custom         │
│   blockchain)  blockchain)    │
└────────────────────────────────┘
```

Каждый Subnet — собственный набор валидаторов,
валидирующих один или несколько блокчейнов.

### Связь с Ethereum

Avalanche не связан с Ethereum напрямую. **Виталик Бутерин**
взял идеи из GHOST (Сомполинского), а не из Avalanche (Сирера).
Avalanche появился позже Ethereum.

---

## 8. BECP

> **"Blockchain Epidemic Consensus Protocol"**
> Abdi et al., Aug 2025 — [arXiv:2508.02595](https://arxiv.org/abs/2508.02595)

### Epidemic (Gossip) консенсус

BECP — полностью децентрализованный консенсус на основе эпидемических
протоколов:

- **Нет фиксированных ролей** (валидаторов, лидеров)
- **Вероятностная сходимость** — эпидемическое распространение
- **Толерантность к задержкам** и отказам узлов

### Результаты vs другие протоколы

| Метрика | BECP vs Avalanche |
|---------|-------------------|
| Throughput | **1.2x выше** |
| Consensus latency | **4.8x лучше** |
| Messages | **значительно меньше** |

BECP также превосходит PAXOS, RAFT, PBFT по масштабируемости.

### Применимость к nn3w

Epidemic/gossip протоколы — те же принципы, что используются в:
- **libp2p GossipSub** (IPFS, Ceramic, Lattica)
- **Ceramic Recon protocol** (event stream синхронизация)

---

## 9. Nix

### Content-Addressed Store

Nix store — это по сути **Merkle-DAG для софта**:

```
/nix/store/<hash>-package-name/
     │
     └── hash = f(source code, dependencies, build script, ...)
```

### Сходство с IPFS

| Аспект | IPFS | Nix Store |
|--------|------|-----------|
| Идентификация | CID = hash(content) | path = hash(inputs) |
| Иммутабельность | Блоки не изменяемы | Store paths не изменяемы |
| Дедупликация | По CID | По хешу |
| DAG | Merkle-DAG блоков | DAG зависимостей |
| Воспроизводимость | Один CID = один blob | Один derivation = один output |

### Nix + IPFS интеграция

**PR #3727** (Trustful IPFS Store):
- Nix store graph нативно представляется через **IPLD**
- Поддержка upload/download через IPFS
- Замена centralized binary caches на децентрализованный IPFS

**PR #8918 + RFC 133** (Git hashing):
- Nix принял **Git object hashing** как альтернативу NAR
- Каждый subdirectory → свой хеш → **Merkle-DAG** автоматически
- Совместимость с Git-репозиториями
- Дедупликация на уровне директорий

### Философская связь

```
IPFS:  content-addressed DATA
Nix:   content-addressed SOFTWARE
Git:   content-addressed CODE

Все три используют Merkle-DAG как фундамент.
Все три обеспечивают:
  → воспроизводимость
  → верифицируемость
  → дедупликацию
  → децентрализуемость
```

---

## 10. Ceramic

### Event Streams как DAG

Ceramic Network хранит данные как **event streams** — по сути,
это Merkle-DAG событий:

```
Stream:  init_event ──→ update_1 ──→ update_2 ──→ ...
              │              │             │
              ▼              ▼             ▼
         IPFS (CID)    IPFS (CID)    IPFS (CID)

Anchoring:
         update_1 ──→ time_event (Ethereum anchor)
```

- Каждое событие = IPFS CID (content-addressed)
- Время события подтверждается Ethereum anchor (Merkle proof)
- Stream tip = последний CID = текущее состояние

### ComposeDB как DAG-индекс

ComposeDB поверх Ceramic = **GraphQL-интерфейс** к Merkle-DAG:
- Модели определяют структуру данных
- Relations = ссылки между streams
- Запросы = обход DAG через SQL/GraphQL

---

## 11. Merkle-CRDT

> Merkle-CRDT = Merkle-DAG + CRDT (Conflict-free Replicated Data Types)

### Проблема

Как синхронизировать данные между узлами без центрального сервера,
когда оба узла могут параллельно менять данные?

### Решение

```
Node A:  init ──→ A1 ──→ A2
                          │
Node B:  init ──→ B1 ─────┤
                          │
Merged:  init ──→ A1 ──→ merge(A2, B1)
                  │
              B1 ─┘
```

Merkle-DAG позволяет:
1. Быстро определить **общего предка** (по CID)
2. Передать только **дельту** (новые блоки)
3. **Детерминистически смержить** ветки (CRDT-правила)

### Где используется

- **IPFS Cluster** — синхронизация pinset между нодами
- **OrbitDB** — P2P база данных на IPFS
- **Ceramic Recon** — event stream синхронизация
- **SHIMI** — семантическая память агентов (Merkle-DAG summaries)

---

## 12. Сводная таблица

### DAG Everywhere

```
┌──────────────────────────────────────────────────────────────┐
│                    DAG — УНИВЕРСАЛЬНЫЙ ПАТТЕРН               │
├───────────┬──────────────────┬───────────────────────────────┤
│ Система   │ Тип DAG          │ Что хранится                 │
├───────────┼──────────────────┼───────────────────────────────┤
│ IPFS      │ Merkle-DAG       │ Файлы, данные                │
│ IPLD      │ Data Model DAG   │ Любые linked data            │
│ Git       │ Merkle-DAG       │ Код, коммиты, деревья        │
│ Nix       │ Derivation DAG   │ Пакеты, зависимости          │
│ Ceramic   │ Event Stream DAG │ Мутабельные данные + anchors  │
│ Kaspa     │ BlockDAG         │ Транзакции (GHOSTDAG)         │
│ Avalanche │ Tx DAG (ист.)    │ Транзакции (Snow)             │
│ OrbitDB   │ Merkle-CRDT DAG  │ P2P база данных              │
│ Bitcoin   │ Merkle Tree      │ Tx в блоке (упрощённый DAG)   │
│ Ethereum  │ Patricia Trie    │ State (специфический DAG)     │
└───────────┴──────────────────┴───────────────────────────────┘
```

### DAG как «тонкая талия» архитектуры

Подобно тому как IP-протокол стал «тонкой талией» интернета,
**Merkle-DAG / IPLD** становится «тонкой талией» для данных:

```
Applications:  Knowledge Graph | Agent Memory | Smart Contracts
                          ↓           ↓             ↓
                   ┌──────────────────────────────┐
                   │     IPLD Data Model           │
                   │     (Merkle-DAG)               │
                   └──────────────────────────────┘
                          ↓           ↓             ↓
Storage:          IPFS        Filecoin        Local FS
Transport:        libp2p      HTTP            Lattica
Consensus:        GHOSTDAG    Avalanche       Ceramic anchors
```

---

## 13. Что это значит для nn3w

### Единый фундамент

Все компоненты nn3w уже используют DAG:

```
nn3w Layer          DAG technology
──────────────────────────────────────────
Nix infra           Derivation DAG (store paths)
Code versioning     Git Merkle-DAG (commits)
Immutable storage   IPFS Merkle-DAG (blocks, CIDs)
Mutable data        Ceramic Event Stream DAG
Knowledge Graph     ComposeDB → IPLD DAG
Agent memory        SHIMI → Merkle-DAG + CRDT
P2P transport       libp2p (DHT = distributed DAG routing)
Consensus           GHOSTDAG/Avalanche/BECP (blockDAG)
```

### IPLD как универсальный Data Model для Meta-Graph

Наш «гетерогенный-темпоральный-децентрализованный-мета-граф»
может быть полностью представлен через IPLD:

```graphql
# Proposition как IPLD Node
type Proposition struct {
  text        String
  confidence  Float
  entityIDs   [&Entity]       # IPLD Links!
  sourceChunk &Chunk          # IPLD Link!
  embedding   Bytes           # IPLD Bytes
  temporal    optional String
} representation map
```

Каждый Proposition, Entity, Relation — это IPLD Block с CID.
Связи между ними — IPLD Links.
Весь Meta-Graph = один гигантский Merkle-DAG.

### Convergence: Nix + IPFS + Ceramic

С PR #3727 и Git-hashing, Nix store может нативно
**публиковать store paths как IPLD блоки через IPFS**.

Это означает:

```
Nix build    →  content-addressed derivation output
             →  IPLD block (dag-cbor)
             →  IPFS CID
             →  доступно любому IPFS-ноду

Ceramic      →  event stream с IPFS anchoring
             →  тот же CID namespace
             →  тот же libp2p transport

Knowledge    →  Propositions/Entities as IPLD blocks
             →  ComposeDB indexes them
             →  IPFS хранит immutable history
```

**Единый CID namespace** для кода, данных, знаний и инфраструктуры.

### BlockDAG для Knowledge Contracts

Консенсус-протоколы типа GHOSTDAG / Avalanche / BECP
могут использоваться для:

1. **Knowledge Validation** — достижение консенсуса о корректности
   Propositions через DAG-голосование
2. **Settlement** — микроплатежи за Knowledge Exchange через
   blockDAG (как Kaspa — быстро и дёшево)
3. **Reputation DAG** — trust graph агентов как blockDAG
   с GHOSTDAG-упорядочиванием

### Формула будущего

```
FUTURE INTERNET =
  IPLD (universal data model)
  + Merkle-DAG (verification & dedup)
  + libp2p (transport)
  + Content Addressing (identity)
  + DAG Consensus (agreement)
  + CRDT (eventual consistency)
  + Declarative Config (Nix)
  + AI Agents (autonomy)
  + Knowledge Contracts (programmability)
```

---

## 14. Библиография

### Оригинальные исследования DAG-консенсуса

| ID | Название | Авторы | Дата |
|----|----------|--------|------|
| [ePrint 2018/104](https://eprint.iacr.org/2018/104) | PHANTOM and GHOSTDAG: A Scalable Generalization of Nakamoto Consensus | Sompolinsky, Wyborski, Zohar | 2018/2021 |
| [2109.01102](https://arxiv.org/abs/2109.01102) | DAG-Oriented Protocols PHANTOM and GHOSTDAG under Incentive Attack | Perešíni et al. | 2021 |
| [2012.06128](https://arxiv.org/abs/2012.06128) | SoK: Diving into DAG-based Blockchain Systems | Wang et al. | 2020 |
| [2312.09816](https://arxiv.org/abs/2312.09816) | Directed Acyclic Graph Based Blockchain Systems | Devarajan & Karabulut | 2023 |
| [2508.02595](https://arxiv.org/abs/2508.02595) | BECP: Fully Decentralised Consensus for Extreme-scale Blockchain | Abdi et al. | Aug 2025 |

### IPFS & IPLD

| Ресурс | Описание |
|--------|----------|
| [docs.ipfs.io/concepts/merkle-dag](https://docs.ipfs.io/concepts/merkle-dag/) | IPFS Merkle-DAG документация |
| [ipld.io/docs/intro/primer](https://ipld.io/docs/intro/primer/) | IPLD Primer — ключевой документ |
| [ipld.io/docs/data-model](https://ipld.io/docs/data-model/) | IPLD Data Model спецификация |
| [github.com/ipfs/specs](https://github.com/ipfs/specs/blob/main/ARCHITECTURE.md) | IPFS Architecture |

### Nix + IPFS

| Ресурс | Описание |
|--------|----------|
| [NixOS/nix#3727](https://github.com/NixOS/nix/pull/3727) | Trustful IPFS Store — IPLD для Nix |
| [NixOS/nix#8918](https://github.com/NixOS/nix/pull/8918) | Git object hashing in libstore |
| [NixOS/rfcs#133](https://github.com/NixOS/rfcs/pull/133) | RFC: Git hashing and Git-hashing-based remote stores |
| [nix.dev/manual](https://nix.dev/manual/nix/2.28/store/derivation/outputs/content-address) | Content-addressing derivation outputs |

### Kaspa

| Ресурс | Описание |
|--------|----------|
| [kaspa.org/publications](https://kaspa.org/publications/) | Научные публикации Kaspa |
| [kaspa.org/milestones-2025](https://kaspa.org/kaspa-development-milestones-revealed-2025) | Roadmap 2025-2026 (DAGKnight, ZK bridge) |

---

> **Главный вывод**: DAG — это не одна из технологий, которые мы используем.
> DAG — это **фундаментальная парадигма**, на которой построено всё:
> от хранения данных (IPFS) до консенсуса (GHOSTDAG) и управления пакетами (Nix).
> Понимание этого единства позволяет видеть nn3w не как набор разрозненных
> технологий, а как **одну согласованную архитектуру**, объединённую
> content-addressed Merkle-DAG структурами.

---

> **Дополнительно — Chimera Linux и DAG-мышление**:
> Chimera Linux, упомянутый в обсуждении — интересный проект, но он решает
> другую задачу (alternative userspace). Для nn3w подход Nix/NixOS принципиально
> лучше, потому что Nix store — это уже content-addressed DAG для пакетов,
> а Chimera использует традиционный APK (binary packaging), который не даёт
> криптографической верификации зависимостей. Nix + IPFS (PR #3727) =
> единый content-addressed namespace для кода и данных, чего APK не может.
