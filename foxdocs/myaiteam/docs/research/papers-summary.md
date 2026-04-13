# 📄 Обзор научных источников

> **Связанные документы:**
> - [Architecture: Knowledge Graph](../architecture/knowledge-graph.md)
> - [Concepts: Knowledge Representation](../concepts/knowledge-representation.md)

---

## 1. Knowledge Representation

### 1.1 Критика триплетов

| Paper | Key Insight |
|-------|-------------|
| **arXiv:2406.11160** (Context Graph) | "Triple-based KGs lack contextual information of relational knowledge, like temporal dynamics and provenance details" |
| **arXiv:2301.01227** (Semantic Units) | "Triple-based representations have limited expressiveness for complex propositions" |
| **arXiv:2503.21322** (HyperGraphRAG) | "Existing graph-based RAG approaches are constrained by binary relations, limiting ability to represent n-ary relations" |

### 1.2 Альтернативные представления

| Approach | Paper | Description |
|----------|-------|-------------|
| **Semantic Units** | arXiv:2301.01227, arXiv:2407.10720 | Modular, semantically meaningful subgraphs |
| **Context Graphs** | arXiv:2406.11160 | Triples with mandatory context |
| **Hyper-Relational KG** | StarE, HyNT, GRAN | Quintuples with qualifiers |
| **PAGER** | arXiv:2601.09402 | Cognitive pages with slots |
| **KERAIA** | arXiv:2505.04313 | Clouds of Knowledge, Dynamic Relations |

---

## 2. RAG Systems

### 2.1 GraphRAG

| Paper | System | Key Innovation |
|-------|--------|----------------|
| **arXiv:2501.00309** | GraphRAG (Microsoft) | Leiden clustering + community summaries |
| **arXiv:2410.05779** | LightRAG | Dual-level indexing, 14.6x faster |
| **arXiv:2401.18059** | RAPTOR | Tree-organized retrieval |
| **arXiv:2601.05254** | TagRAG | Hierarchical tag chains |
| **arXiv:2503.21322** | HyperGraphRAG | Hyperedges for n-ary relations |
| **arXiv:2601.11144** | Deep GraphRAG | 3-stage hierarchical retrieval |

### 2.2 Comparison Results

| System | Win Rate vs Baselines | Build Speed |
|--------|----------------------|-------------|
| **LightRAG** | — | 14.6x faster than GraphRAG |
| **TagRAG** | 78.36% | Efficient incremental updates |
| **RAPTOR** | +20% on QuALITY | — |

---

## 3. Knowledge Graph Embeddings

### 3.1 Geometric Spaces

| Paper | Model | Space | Best For |
|-------|-------|-------|----------|
| **arXiv:2204.13704** | HypHKGE | Hyperbolic | Deep hierarchies |
| **arXiv:2206.00449** | UltraE | Ultrahyperbolic | Mixed topology |
| **ACL 2022** | SimKGC | Contrastive | Sparse entities |
| **arXiv:2210.04870** | SMiLE | Multi-level | Schema-aware |
| **TACL 2021** | KEPLER | Joint text-KG | Text + graph |
| **arXiv:2410.11235** | GT2Vec | LLM-based | Multimodal |

### 3.2 Results

| Model | Improvement | Dataset |
|-------|-------------|---------|
| **SimKGC** | +19% MRR | WN18RR |
| **SimKGC** | +22% MRR | Wikidata5M (inductive) |

---

## 4. Entity Resolution

### 4.1 Key Papers

| Paper | System | Key Innovation |
|-------|--------|----------------|
| **2023** | UniversalNER | Targeted distillation, 43 datasets |
| **2024** | LinkNER | Uncertainty-based linking |
| **ACL 2024** | DocLLM | Layout-aware without image encoders |
| **ACL 2024** | MUIE | First unified multimodal framework |

### 4.2 Results

| System | Improvement |
|--------|-------------|
| **UniversalNER** | +30 F1 points over instruction-tuned models |
| **Pixel-Level VEL** | +5 accuracy points |

---

## 5. Heterogeneous Data Processing

### 5.1 Multimodal KG

| Paper | Framework | Approach |
|-------|-----------|----------|
| **arXiv:2406.02962** | Docs2KG | Unified pipeline for documents |
| **arXiv:2503.12972** | VaLiK | VLM cascade for cross-modal |
| **arXiv:2509.10467** | DSRAG | Conceptual + Instance layers |

### 5.2 Key Finding

> "80% of enterprise data exists in unstructured files" (Docs2KG)

---

## 6. Ontology Patterns

### 6.1 Key Resources

| Resource | Type | Content |
|----------|------|---------|
| **ontologydesignpatterns.org** | Catalog | Content, Structural, Logical ODPs |
| **arXiv:1808.08433** | MOMo | Modular Ontology Design |
| **MODL** | Library | 100+ reusable patterns |

### 6.2 Pattern Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **Content ODPs** | Conceptual modeling | AgentRole, PartOf, Participation |
| **Structural ODPs** | Logical organization | N-ary Relation, Reification |
| **Logical ODPs** | Reasoning | Closure Axiom |
| **Alignment ODPs** | Inter-ontology | Bridge Patterns |

---

## 7. Human-AI Collaboration

### 7.1 Key Research

| Source | Framework | Key Insight |
|--------|-----------|-------------|
| **MIT/Stanford** | Co-Gym | Benchmark for collaborative tasks |
| **CU Boulder** | HAT Framework | Trust calibration mechanisms |
| **ICIS 2025** | Mental Models | Three models for effective collaboration |
| **Google/Linux F.** | A2A Protocol | Agent-to-agent communication |

### 7.2 Meta-Analysis Results

| Finding | Statistic |
|---------|-----------|
| Human-AI vs best individual | -0.23 (worse on average!) |
| Creative tasks | Significantly better with AI |
| Decision-making | Worse with AI |

**Key Insight**: Collaboration is not a silver bullet. Requires proper design.

---

## 8. Decentralized Systems

### 8.1 Key Technologies

| Technology | Paper/Source | Purpose |
|------------|--------------|---------|
| **Ceramic** | Technical Docs | Mutable decentralized data |
| **Lit Protocol** | Technical Docs | Decentralized encryption |
| **UCAN** | UCAN.xyz | Capability-based auth |
| **OrbitDB** | GitHub | P2P database with CRDTs |

### 8.2 Scale (Ceramic 2024)

- 350M events
- 10M streams
- 1.5M accounts
- 400 apps

---

## 9. Recommended Reading Order

### 9.1 Fundamentals

1. **Semantic Units** (arXiv:2301.01227) — альтернатива триплетам
2. **Context Graphs** (arXiv:2406.11160) — контекст в KG
3. **GraphRAG** (arXiv:2501.00309) — RAG с графами

### 9.2 Advanced

1. **HyperGraphRAG** (arXiv:2503.21322) — гиперграфы
2. **HypHKGE** (arXiv:2204.13704) — гиперболические embeddings
3. **Mental Models** (ICIS 2025) — Human-AI collaboration

### 9.3 Practical

1. **LightRAG** (arXiv:2410.05779) — эффективная реализация
2. **Docs2KG** (arXiv:2406.02962) — обработка документов
3. **UniversalNER** (2023) — entity extraction

---

## 10. Key Takeaways

### 10.1 Knowledge Representation

> Триплеты ограничены. Используйте Semantic Units или Context Graphs для сохранения контекста.

### 10.2 RAG

> GraphRAG лучше для complex QA, LightRAG — для скорости и обновлений.

### 10.3 Embeddings

> Выбирайте геометрию под структуру данных: гиперболическое для иерархий.

### 10.4 Human-AI

> Collaboration работает не всегда. Правильное распределение задач критично.

### 10.5 Decentralization

> Ceramic для auditability, OrbitDB для real-time collaboration.

---

*Источники: Ultimate-Knowledge-Graph-Architecture-Guide.md, Human-AI-Collaboration-Guide.md*
