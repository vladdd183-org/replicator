# 🤖 Интеграция с AI

> **Связанные документы:**
> - [Architecture: Human-AI Collaboration](../architecture/human-ai-collab.md)
> - [Reference: Tools Comparison](../reference/tools-comparison.md)

---

## 1. AI в Knowledge Systems

### 1.1 Роли AI

| Роль | Описание | Примеры |
|------|----------|---------|
| **Extractor** | Извлечение сущностей и связей | NER, Relation Extraction |
| **Embedder** | Векторизация для поиска | Text embeddings, KG embeddings |
| **Reasoner** | Вывод новых знаний | RAG, Chain-of-Thought |
| **Generator** | Создание контента | Summarization, Q&A |
| **Agent** | Автономное выполнение задач | Research, Analysis |

### 1.2 Архитектурные паттерны

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI INTEGRATION PATTERNS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PATTERN 1: LLM as Orchestrator                                 │
│  ┌─────────┐                                                    │
│  │   LLM   │ → decides what to do → calls tools → synthesizes   │
│  └─────────┘                                                    │
│                                                                 │
│  PATTERN 2: LLM as Processor                                    │
│  Data → LLM (extract/transform) → Structured output             │
│                                                                 │
│  PATTERN 3: LLM + RAG                                           │
│  Query → Retriever → Context → LLM → Answer                     │
│                                                                 │
│  PATTERN 4: Multi-Agent                                         │
│  Agents collaborate → each has role → orchestrator coordinates  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. RAG (Retrieval-Augmented Generation)

### 2.1 Базовый RAG

```
1. Query → Embed
2. Vector Search → Top-K chunks
3. Context = chunks
4. LLM(query + context) → Answer
```

### 2.2 GraphRAG

```
1. Indexing:
   Text → Chunks → Entities → KG → Communities → Summaries

2. Query:
   ├── Global Search: use community summaries
   └── Local Search: entity fan-out + neighbors

3. Generation:
   Context from graph + LLM → Answer
```

### 2.3 Сравнение RAG подходов

| Подход | Когда использовать |
|--------|-------------------|
| **Vector RAG** | Простые вопросы, конкретные факты |
| **GraphRAG** | Сложные вопросы, need context |
| **Hybrid** | Best of both worlds |

---

## 3. Entity Extraction

### 3.1 Подходы

| Подход | Плюсы | Минусы |
|--------|-------|--------|
| **NER models** (GLiNER, spaCy) | Быстро, предсказуемо | Ограниченные типы |
| **LLM extraction** | Гибко, понимает контекст | Медленнее, дороже |
| **Hybrid** | Лучшее из обоих | Сложнее |

### 3.2 LLM Extraction Prompt

```
Extract entities and relations from the following text.

Text: {text}

Output JSON:
{
  "entities": [
    {"name": "...", "type": "...", "description": "..."}
  ],
  "relations": [
    {"source": "...", "target": "...", "type": "...", "description": "..."}
  ]
}
```

### 3.3 Entity Resolution

```
1. Mention Detection → найти упоминания
2. Candidate Generation → найти похожие в KB
3. Candidate Ranking → оценить по контексту
4. Linking Decision → связать или создать новую
5. Entity Consolidation → объединить атрибуты
```

---

## 4. Knowledge Graph Embeddings

### 4.1 Зачем нужны

- **Similarity search** — найти похожие сущности
- **Link prediction** — предсказать отсутствующие связи
- **Clustering** — группировка
- **Downstream ML** — features для моделей

### 4.2 Выбор модели

| Структура графа | Модель | Пространство |
|-----------------|--------|--------------|
| Плоский | TransE, DistMult | Евклидово |
| Глубокие иерархии | HypHKGE | Гиперболическое |
| Текст + граф | KEPLER | Joint |

---

## 5. Agent Protocols

### 5.1 MCP (Model Context Protocol)

**Назначение**: Предоставление контекста и инструментов AI-моделям.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    LLM      │ ←→  │  MCP Server │ ←→  │   Tools     │
│             │     │             │     │  (APIs, DB) │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 5.2 A2A (Agent-to-Agent)

**Назначение**: Коммуникация между AI-агентами.

```
Agent Cards (capability discovery):
{
  "name": "CodeReviewAgent",
  "capabilities": ["review_code", "find_bugs"],
  "supported_languages": ["python", "javascript"]
}

Communication Modes:
├── Synchronous: Request → Response
├── Streaming: Real-time updates (SSE)
└── Async: Push notifications
```

---

## 6. Multi-Agent Orchestration

### 6.1 Frameworks

| Framework | Архитектура | Best For |
|-----------|------------|----------|
| **LangGraph** | Graph-based | Flexible workflows |
| **CrewAI** | Role-based teams | Collaborative tasks |
| **AutoGen** | Conversational | Multi-turn dialogues |

### 6.2 CrewAI Example

```python
from crewai import Agent, Task, Crew

# Agents
researcher = Agent(
    role='Researcher',
    goal='Find relevant information',
    backstory='Expert at finding information'
)

analyst = Agent(
    role='Analyst',
    goal='Analyze and synthesize findings',
    backstory='Expert at analysis'
)

# Tasks
research_task = Task(
    description='Research the topic: {topic}',
    agent=researcher
)

analysis_task = Task(
    description='Analyze the research findings',
    agent=analyst
)

# Crew
crew = Crew(
    agents=[researcher, analyst],
    tasks=[research_task, analysis_task]
)

result = crew.kickoff(inputs={'topic': 'Decentralized Knowledge Graphs'})
```

---

## 7. Human-AI Task Allocation

### 7.1 Принцип Complementarity

```
👤 ЧЕЛОВЕК ЛУЧШЕ:
├── Creative ideation
├── Ethical judgment
├── Novel situations
├── Strategic thinking
└── Context integration

🤖 AI ЛУЧШЕ:
├── Pattern recognition
├── Repetitive tasks
├── Data processing
├── Speed-critical tasks
└── Consistency checking

🤝 ЛУЧШЕ ВМЕСТЕ:
├── Content creation (AI draft → Human refine)
├── Code review (AI finds → Human verifies)
├── Research (AI gathers → Human synthesizes)
└── Analysis (AI processes → Human interprets)
```

### 7.2 Decision Tree

```
Новая задача
     │
     ├── Требует этики? → Human
     │
     ├── Новая ситуация? → Human
     │
     ├── High risk + irreversible? → Human (или review)
     │
     ├── AI accuracy > 90%? → AI
     │
     └── Иначе → Collaborative
```

---

## 8. Trust Calibration

### 8.1 Confidence Scores

```python
class AIResponse:
    content: str           # Ответ
    confidence: float      # 0.0 - 1.0
    reasoning: list[str]   # Шаги рассуждения
    uncertainties: list[str]  # Области неуверенности
```

### 8.2 Правила по confidence

| Confidence | Действие |
|------------|----------|
| **95-100%** | Можно принять сразу |
| **85-95%** | Quick review |
| **70-85%** | Review рекомендуется |
| **50-70%** | Review обязателен |
| **<50%** | Human decision |

---

## 9. Practical Recommendations

### 9.1 Начните с простого

```
1. LLM API для extraction
2. Vector DB для search
3. RAG для Q&A
```

### 9.2 Добавляйте сложность постепенно

```
1. Simple RAG → GraphRAG
2. Single LLM → Multi-agent
3. Manual triggers → Autonomous agents
```

### 9.3 Мониторинг и feedback

```
1. Log all AI interactions
2. Track acceptance/rejection rate
3. Measure confidence vs actual accuracy
4. Iterate on prompts and models
```

---

## 10. Инструменты

### 10.1 LLM Providers

| Provider | Models | Best For |
|----------|--------|----------|
| **OpenAI** | GPT-4, GPT-3.5 | General, coding |
| **Anthropic** | Claude 3 | Reasoning, safety |
| **Google** | Gemini | Multimodal |
| **Local** | Llama, Mistral | Privacy, cost |

### 10.2 Embedding Models

| Model | Dimensions | Use Case |
|-------|------------|----------|
| **text-embedding-3-large** | 3072 | Best quality |
| **text-embedding-3-small** | 1536 | Balance |
| **all-MiniLM** | 384 | Fast, local |

### 10.3 Observability

| Tool | Purpose |
|------|---------|
| **LangSmith** | Tracing, debugging |
| **Weights & Biases** | MLOps |
| **TruLens** | Observability |

---

*Источники: Human-AI-Collaboration-Guide.md, Ultimate-Knowledge-Graph-Architecture-Guide.md*
