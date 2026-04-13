# 🔧 Сравнение инструментов и технологий

> **Связанные документы:**
> - [Architecture Overview](../architecture/overview.md)
> - [Decentralized Stack](../architecture/decentralized-stack.md)
> - [Glossary](glossary.md)

---

## 1. Децентрализованное хранилище

### 1.1 IPFS vs Centralized Storage

| Аспект | IPFS | S3/Cloud |
|--------|------|----------|
| **Addressing** | Content (CID) | Location (URL) |
| **Mutability** | Immutable (need IPNS) | Mutable |
| **Redundancy** | Distributed | Provider-managed |
| **Cost** | Self-hosted / Pinning services | Pay-per-use |
| **Control** | Full | Provider-dependent |
| **Latency** | Variable | Low (CDN) |

### 1.2 Ceramic vs OrbitDB

| Аспект | Ceramic | OrbitDB |
|--------|---------|---------|
| **Data model** | Streams (event-sourced) | CRDT stores |
| **Consistency** | Eventually + anchoring | Eventually (CRDT) |
| **Update latency** | Seconds-minutes | Milliseconds |
| **Concurrent edits** | Last-write-wins | Auto-merge |
| **Real-time collab** | ⚠️ Limited | ✅ Native |
| **Global ordering** | ✅ Blockchain anchors | ❌ Causal only |
| **Tamper-proof** | ✅ Anchored | ❌ No proof |
| **GraphQL queries** | ✅ ComposeDB | ❌ Limited |
| **Schema ecosystem** | ✅ Rich | ❌ None |

**Когда что:**
- **Ceramic**: Knowledge base с auditability, cross-app data sharing
- **OrbitDB**: Real-time collaboration, multi-agent parallel writes

### 1.3 Pinning Services

| Service | Free Tier | Pricing | Notes |
|---------|-----------|---------|-------|
| **Pinata** | 1 GB | $0.15/GB/month | Popular, good API |
| **Infura** | 5 GB | Pay-per-request | Reliable infrastructure |
| **Web3.Storage** | 5 GB | Free (Filecoin-backed) | Simple API |
| **Fleek** | Limited | Usage-based | CI/CD integration |

---

## 2. Encryption & Access Control

### 2.1 Lit Protocol vs Alternatives

| Аспект | Lit Protocol | AES + Key Server | Threshold Crypto |
|--------|--------------|------------------|------------------|
| **Decentralization** | ✅ Full | ❌ Centralized | ✅ Partial |
| **Access Conditions** | Rich (token-gated) | Manual | Limited |
| **Setup complexity** | Medium | Low | High |
| **Key recovery** | Threshold | Backup needed | Threshold |

### 2.2 Authorization Comparison

| Аспект | UCAN | JWT + RBAC | OAuth |
|--------|------|------------|-------|
| **Centralization** | ❌ Decentralized | ✅ Centralized | ✅ Provider |
| **Delegation** | ✅ Native chains | ⚠️ Manual | ⚠️ Limited |
| **Offline verify** | ✅ Yes | ❌ Need server | ❌ Need provider |
| **Revocation** | ⚠️ Async | ✅ Instant | ✅ Instant |
| **Attenuation** | ✅ Built-in | ❌ Manual | ❌ No |

---

## 3. Knowledge Graph Databases

### 3.1 Graph Databases

| Database | Type | Query Language | Vectors | Best For |
|----------|------|----------------|---------|----------|
| **Neo4j** | Property Graph | Cypher | ⚠️ Plugin | General graphs |
| **DGraph** | Property Graph | GraphQL/DQL | ⚠️ Limited | High performance |
| **Memgraph** | Property Graph | Cypher | ⚠️ Plugin | Real-time |
| **SurrealDB** | Multi-model | SurrealQL | ✅ Native | Polyglot |
| **Amazon Neptune** | RDF + Property | SPARQL/Gremlin | ❌ No | Enterprise |

### 3.2 Vector Databases

| Database | Type | Indices | Features | Best For |
|----------|------|---------|----------|----------|
| **Qdrant** | Pure vector | HNSW | Filtering, payloads | Production RAG |
| **Milvus** | Pure vector | IVF, HNSW | GPU support, scale | Large scale |
| **ChromaDB** | Embedded | HNSW | Simple API | Prototypes |
| **Pinecone** | Managed | Proprietary | Serverless | No-ops |
| **Weaviate** | Hybrid | HNSW | GraphQL, modules | Semantic search |

### 3.3 OriginTrail DKG

| Aspect | Value |
|--------|-------|
| **Type** | Decentralized Knowledge Graph |
| **Query** | SPARQL |
| **Standards** | W3C (JSON-LD) |
| **Privacy** | Public/Private assertions |
| **Ownership** | NFT-based |
| **Best For** | Verifiable decentralized knowledge |

---

## 4. RAG Systems

### 4.1 Comparison

| System | Knowledge Unit | Hierarchy | Build Cost | Updates | Best For |
|--------|---------------|-----------|------------|---------|----------|
| **GraphRAG** | Entity-Relation | Community (Leiden) | High | Limited | Complex QA |
| **LightRAG** | Entity-Relation | Dual-Level | Low (14.6x faster) | Good | Fast retrieval |
| **RAPTOR** | Text Chunk | Tree | Medium | Limited | Long docs |
| **TagRAG** | Tag Chain | Domain Tags | Low | Good | Domain-specific |
| **HyperGraphRAG** | Hyperedge | N-ary | Medium | Medium | N-ary facts |
| **Deep GraphRAG** | Entity | 3-stage | High | Medium | Precision |

### 4.2 When to Use

| Scenario | Recommended |
|----------|-------------|
| General QA over documents | GraphRAG |
| Fast retrieval, frequent updates | LightRAG |
| Very long documents | RAPTOR |
| Specialized domain | TagRAG |
| Complex multi-entity relations | HyperGraphRAG |

---

## 5. AI Agent Frameworks

### 5.1 Multi-Agent Orchestration

| Framework | Architecture | Complexity | Best For |
|-----------|-------------|------------|----------|
| **LangGraph** | Graph-based | Medium | Flexible workflows |
| **CrewAI** | Role-based teams | Low | Collaborative agents |
| **AutoGen** | Conversational | Medium | Multi-turn dialogues |
| **Swarms** | Enterprise | High | Large scale |

### 5.2 Code Assistance

| Tool | Integration | Agent Mode | Best For |
|------|-------------|------------|----------|
| **Cursor** | IDE-native | ✅ Yes | Full-stack dev |
| **GitHub Copilot** | VS Code/JetBrains | ❌ Limited | Code completion |
| **Cody** | Enterprise | ✅ Yes | Codebase context |
| **aider** | CLI | ✅ Yes | Git integration |

### 5.3 Agent Protocols

| Protocol | Organization | Status | Use Case |
|----------|--------------|--------|----------|
| **MCP** | Anthropic | Production | Tool access |
| **A2A** | Google/Linux F. | Production | Agent-to-agent |

---

## 6. Embedding Models

### 6.1 Text Embeddings

| Model | Dimensions | Quality | Speed | Cost |
|-------|------------|---------|-------|------|
| **OpenAI text-embedding-3-large** | 3072 | Excellent | Fast | $0.13/1M |
| **OpenAI text-embedding-3-small** | 1536 | Good | Faster | $0.02/1M |
| **Cohere embed-v3** | 1024 | Excellent | Fast | $0.10/1M |
| **sentence-transformers/all-MiniLM** | 384 | Good | Local/Fast | Free |
| **BAAI/bge-large** | 1024 | Excellent | Local | Free |

### 6.2 KG Embeddings

| Model | Space | Patterns | Best For |
|-------|-------|----------|----------|
| **TransE** | Euclidean | Translation | Simple graphs |
| **RotatE** | Complex | Rotation | Symmetric/antisymmetric |
| **HypHKGE** | Hyperbolic | Hierarchical | Deep hierarchies |
| **SimKGC** | Contrastive | Textual | Sparse entities |

---

## 7. Full-Text Search

| Engine | Type | Features | Best For |
|--------|------|----------|----------|
| **MeiliSearch** | Embedded | Typo-tolerance, instant | User-facing |
| **Typesense** | Hosted/Self | Geo, facets | E-commerce |
| **Elasticsearch** | Distributed | Scale, analytics | Enterprise |

---

## 8. Decision Matrix by Use Case

### 8.1 Personal Knowledge Base

| Component | Recommendation |
|-----------|---------------|
| Storage | IPFS + IPNS |
| Database | SQLite / SurrealDB (local) |
| Vectors | ChromaDB |
| Privacy | Lit Protocol (optional) |

### 8.2 Team Collaboration

| Component | Recommendation |
|-----------|---------------|
| Storage | IPFS + Ceramic |
| Database | SurrealDB / Neo4j |
| Vectors | Qdrant |
| Privacy | Lit Protocol + UCAN |
| Real-time | OrbitDB / PubSub |

### 8.3 Enterprise Platform

| Component | Recommendation |
|-----------|---------------|
| Storage | IPFS Cluster + Ceramic |
| Database | Neo4j / DGraph |
| Vectors | Milvus / Pinecone |
| Privacy | Lit Protocol + UCAN |
| RAG | GraphRAG / LightRAG |
| Search | Elasticsearch |

---

## 9. Quick Reference

### 9.1 Technology Stack Tiers

```
TIER 1 (Essential):
├── IPFS (storage)
├── IPLD (linking)
├── Vector DB (Qdrant/ChromaDB)
└── LLM API (OpenAI/Claude)

TIER 2 (Team Features):
├── Ceramic (structured data)
├── Lit Protocol (encryption)
├── UCAN (authorization)
└── PubSub (real-time)

TIER 3 (Advanced):
├── Graph DB (Neo4j)
├── RAG System (GraphRAG)
├── Agent Framework (LangGraph)
└── Full-text (MeiliSearch)
```

### 9.2 Alternatives Without Web3

| Web3 Stack | Alternative | Trade-off |
|------------|-------------|-----------|
| IPFS | S3 + content hash | Centralized |
| Ceramic | PostgreSQL + events | Centralized |
| Lit Protocol | AES + key server | Need own server |
| UCAN | JWT + RBAC | Centralized auth |
| PubSub | WebSocket server | Single point of failure |

---

*Источники: Все оригинальные руководства*
