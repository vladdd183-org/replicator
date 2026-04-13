# 🧠 Decentralized AI Knowledge System
## Документация проекта

---

> **Миссия**: Создать универсальную децентрализованную систему управления знаниями с AI-агентами для human-AI collaboration.

---

## 📋 Оглавление

```
docs/
├── 📐 architecture/           # Архитектурные решения
│   ├── overview.md            # Общий обзор архитектуры
│   ├── knowledge-graph.md     # Дизайн графа знаний
│   ├── decentralized-stack.md # Децентрализованный технологический стек
│   ├── privacy-access.md      # Приватность и контроль доступа
│   └── human-ai-collab.md     # Human-AI взаимодействие
│
├── 💡 concepts/               # Ключевые концепции
│   ├── knowledge-representation.md  # Представление знаний
│   ├── decentralized-tech.md        # Децентрализованные технологии
│   └── ai-integration.md            # Интеграция с AI
│
├── 🔧 implementation/         # Руководства по реализации
│   ├── quickstart.md          # Быстрый старт
│   ├── ipfs-ceramic-setup.md  # Настройка IPFS/Ceramic
│   └── rag-systems.md         # RAG системы
│
├── 📚 reference/              # Справочные материалы
│   ├── glossary.md            # Глоссарий терминов
│   ├── relation-types.md      # Таксономия связей
│   └── tools-comparison.md    # Сравнение инструментов
│
└── 🔬 research/               # Исследования
    └── papers-summary.md      # Обзор научных статей
```

---

## 🎯 Что это за проект?

**Decentralized AI Knowledge System** — это архитектура для построения:

1. **Гетерогенного мультимодального графа знаний** — обработка текстов, аудио, видео, изображений
2. **Децентрализованного хранилища** — IPFS + Ceramic + Lit Protocol
3. **Системы Human-AI Collaboration** — AI-агенты работают вместе с людьми
4. **Приватного контроля доступа** — шифрование + DID + UCAN

---

## 🏗️ Архитектура высокого уровня

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    DECENTRALIZED AI KNOWLEDGE SYSTEM                          ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  👥 HUMAN + 🤖 AI LAYER                                                 │  ║
║  │  ├── UI (Obsidian-like interface)                                       │  ║
║  │  ├── AI Agents (MCP, A2A protocols)                                     │  ║
║  │  └── Human-AI Collaboration patterns                                    │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  🔍 QUERY & RETRIEVAL LAYER                                             │  ║
║  │  ├── Vector Search (Qdrant, ChromaDB)                                   │  ║
║  │  ├── Graph Queries (Neo4j, SPARQL)                                      │  ║
║  │  ├── Full-text Search (MeiliSearch)                                     │  ║
║  │  └── RAG Systems (GraphRAG, LightRAG)                                   │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  🔐 ACCESS CONTROL LAYER                                                │  ║
║  │  ├── UCAN (Authorization)                                               │  ║
║  │  ├── Lit Protocol (Encryption)                                          │  ║
║  │  └── DIDs (Identity)                                                    │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  📊 KNOWLEDGE GRAPH LAYER                                               │  ║
║  │  ├── Semantic Units (not just triples!)                                 │  ║
║  │  ├── Hyper-relational facts                                             │  ║
║  │  ├── Multi-level hierarchy (atoms → clusters → communities → themes)    │  ║
║  │  └── Context-aware relations                                            │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                      │                                        ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  💾 DECENTRALIZED STORAGE LAYER                                         │  ║
║  │  ├── IPFS + IPLD (Content-addressed storage)                            │  ║
║  │  ├── Ceramic + ComposeDB (Structured mutable data)                      │  ║
║  │  ├── IPNS (Mutable pointers)                                            │  ║
║  │  └── OrbitDB (Real-time P2P database)                                   │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🔗 Карта связей документации

```
                              ┌─────────────────┐
                              │   README.md     │
                              │   (вы здесь)    │
                              └────────┬────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  architecture/  │         │   concepts/     │         │ implementation/ │
│                 │         │                 │         │                 │
│ • overview      │◄───────►│ • knowledge-    │◄───────►│ • quickstart    │
│ • knowledge-    │         │   representation│         │ • ipfs-ceramic  │
│   graph         │         │ • decentral-    │         │ • rag-systems   │
│ • decentral-    │         │   ized-tech     │         │                 │
│   ized-stack    │         │ • ai-integration│         │                 │
│ • privacy-      │         │                 │         │                 │
│   access        │         │                 │         │                 │
│ • human-ai-     │         │                 │         │                 │
│   collab        │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
          │                            │                            │
          └────────────────────────────┼────────────────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   reference/    │         │   research/     │         │ Original Guides │
│                 │         │                 │         │                 │
│ • glossary      │         │ • papers-       │         │ • Ultimate-KG   │
│ • relation-     │         │   summary       │         │ • Decentral-    │
│   types         │         │                 │         │   Stack         │
│ • tools-        │         │                 │         │ • Privacy-      │
│   comparison    │         │                 │         │   Access        │
│                 │         │                 │         │ • Human-AI-     │
│                 │         │                 │         │   Collab        │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

---

## 🚀 Быстрый старт

### Навигация по документации

| Цель | Куда смотреть |
|------|---------------|
| **Понять общую картину** | [architecture/overview.md](architecture/overview.md) |
| **Изучить дизайн графа знаний** | [architecture/knowledge-graph.md](architecture/knowledge-graph.md) |
| **Разобраться в децентрализованном стеке** | [architecture/decentralized-stack.md](architecture/decentralized-stack.md) |
| **Настроить приватность и доступ** | [architecture/privacy-access.md](architecture/privacy-access.md) |
| **Организовать работу с AI** | [architecture/human-ai-collab.md](architecture/human-ai-collab.md) |
| **Найти определение термина** | [reference/glossary.md](reference/glossary.md) |
| **Выбрать инструменты** | [reference/tools-comparison.md](reference/tools-comparison.md) |
| **Изучить научную базу** | [research/papers-summary.md](research/papers-summary.md) |

---

## 📖 Оригинальные исследовательские материалы

Эта документация синтезирована из следующих детальных руководств:

| Документ | Описание | Строк |
|----------|----------|-------|
| `Ultimate-Knowledge-Graph-Architecture-Guide.md` | Критика триплетов, Semantic Units, RAG-системы, KG Embeddings | ~4900 |
| `Decentralized-Knowledge-Stack-Guide.md` | IPFS, Ceramic, Lit Protocol, UCAN, OrbitDB | ~3700 |
| `Decentralized-Private-Access-Control.md` | Шифрование, DID, OriginTrail DKG | ~1200 |
| `Decentralized-Graph-Architecture.md` | Графы + векторы + теги в децентрализованной системе | ~1000 |
| `Human-AI-Collaboration-Guide.md` | Mental Models, Trust Calibration, паттерны | ~1700 |

**Всего**: ~12,500 строк исследовательского материала

---

## 🏷️ Ключевые технологии

### Децентрализованное хранилище
- **IPFS** — Content-addressed storage
- **IPLD** — Linked data model
- **Ceramic** — Mutable structured data
- **OrbitDB** — P2P database с CRDTs

### Приватность и авторизация
- **Lit Protocol** — Decentralized encryption
- **UCAN** — Capability-based authorization
- **DIDs** — Decentralized identifiers

### Knowledge Graph
- **Semantic Units** — Альтернатива триплетам
- **Hyper-relational KG** — N-арные отношения
- **GraphRAG/LightRAG** — Retrieval-Augmented Generation

### AI Integration
- **MCP** — Model Context Protocol
- **A2A** — Agent-to-Agent protocol
- **Multi-agent orchestration** — LangGraph, CrewAI

---

## 📅 Статус проекта

| Компонент | Статус | Документация |
|-----------|--------|--------------|
| Knowledge Graph Design | ✅ Исследован | Полная |
| Decentralized Stack | ✅ Исследован | Полная |
| Privacy & Access | ✅ Исследован | Полная |
| Human-AI Collaboration | ✅ Исследован | Полная |
| Implementation | 🔄 В планах | Частичная |

---

*Документация создана: 2 февраля 2026*  
*Версия: 1.0*
