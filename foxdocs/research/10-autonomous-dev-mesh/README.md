# Autonomous Development Mesh

### От Huly-задачи к самодвижущемуся циклу разработки
### Серия meta-research заметок про intent-driven delivery, NDI, swarm execution и knowledge plane

> 📅 Дата: 2026-04-13
> 🔬 Статус: Рабочая исследовательская серия
> 📎 Контекст: [07-SNS3-FOUNDATIONS](../07-SNS3-FOUNDATIONS.md) · [08-SNS3-TOOLKIT](../08-SNS3-TOOLKIT.md) · [09-SNS3-PROMPT](../09-SNS3-PROMPT.md)
> 📎 Мосты: [02-SOVEREIGN-MESH](../02-SOVEREIGN-MESH.md) · [03-GAS-TOWN-ANALYSIS](../03-GAS-TOWN-ANALYSIS.md) · [04-ORCHESTRATOR-EVOLUTION](../04-ORCHESTRATOR-EVOLUTION.md)

---

## 🎯 Зачем эта серия

> Эта серия переопределяет software delivery как оркестрацию молекул работы, а не как ручную бюрократическую цепочку из issue, branch, PR и статусов.

Исходная боль проста: сейчас цикл разработки слишком длинный, слишком человекоцентричный и слишком хрупкий. Даже если в нём уже есть хорошие практики, они живут как несвязанные ритуалы:

- Huly как вход
- ручное исследование
- ручная декомпозиция
- ветки и PR
- локальное тестирование
- stage / prod
- ручные комментарии, статусы и отчёты

Вместо этого мы хотим построить систему, где:

- человек или агент формулирует **intent**
- intent компилируется в **workflow graph**
- swarm агентов исполняет beads в изолированных workcells
- verification lattice выдаёт evidence bundle
- Refinery интегрирует и продвигает изменения по окружениям
- knowledge plane сам публикует всё нужное в Huly, GitHub и базе знаний

---

## 🗺️ Карта серии

| # | Заметка | Суть |
|---|---|---|
| 00 | [why-the-current-loop-breaks](./00-why-the-current-loop-breaks.md) | Почему текущий dev-loop ломается и почему issue не должен быть центром системы |
| 01 | [ndi-for-software-delivery](./01-ndi-for-software-delivery.md) | NDI как базовый принцип автономной разработки |
| 02 | [formulas-molecules-beads-for-dev-work](./02-formulas-molecules-beads-for-dev-work.md) | Новая единица работы: mission spec -> formula -> molecule -> bead |
| 03 | [agent-roles-a2a-and-mcp](./03-agent-roles-a2a-and-mcp.md) | Роли агентов, A2A control plane и MCP tool plane |
| 03.5 | [mission-spec-patterns](./03.5-mission-spec-patterns.md) | Мини-шаблон того, как формулировать mission spec для компиляции |
| 04 | [dynamic-simulacra-and-ephemeral-envs](./04-dynamic-simulacra-and-ephemeral-envs.md) | Изолированные динамические среды для исполнения и проверки |
| 05 | [verification-lattice-property-stateful-load-chaos](./05-verification-lattice-property-stateful-load-chaos.md) | Решётка верификации вместо линейного CI |
| 06 | [refinery-intelligent-merge-and-architecture-guard](./06-refinery-intelligent-merge-and-architecture-guard.md) | Интеллектуальный merge, архитектурные guardrails и promotion |
| 07 | [knowledge-plane-huly-github-dashboards-kb](./07-knowledge-plane-huly-github-dashboards-kb.md) | Автоматическая эмиссия знаний, статусов и evidence-артефактов |
| 08 | [web2-first-mvp-roadmap](./08-web2-first-mvp-roadmap.md) | Практический MVP без прыжка сразу в полный sovereign mesh |
| 09 | [stage9-sovereign-dev-mesh](./09-stage9-sovereign-dev-mesh.md) | Дальний горизонт: decentralized autonomous swarm для разработки |
| 10 | [sota-methods-and-agent-stacks](./10-sota-methods-and-agent-stacks.md) | Внешний frontier-скан: методы разработки, spec-подходы, orchestration runtimes и protocol layer |
| 11 | [memory-context-and-task-ledgers](./11-memory-context-and-task-ledgers.md) | Разведение `AGENTS.md`, `Agent OS`, `Beads`, `Letta`, `Mem0`, `Graphiti` по разным типам памяти и истины |
| 12 | [comparison-matrix-and-recommended-stack](./12-comparison-matrix-and-recommended-stack.md) | Жёсткая comparison matrix и recommended stack для Autonomous Development Mesh |

---

## 🌐 Внешний SOTA-слой

Первый блок серии строил собственную архитектурную гипотезу.

Новый слой `10 -> 12` делает другое:

- прошивает эту гипотезу через внешний landscape
- разводит методологии, runtimes, протоколы и memory systems по слоям
- убирает ложные сравнения между `spec`, `task truth`, `agent memory` и `knowledge plane`
- заканчивает всё не обзором, а concrete recommended stack

Именно этот слой отвечает на вопросы:

- что реально frontier, а что просто популярно
- что practical уже сейчас
- какой стек лучше всего подходит именно для brownfield-heavy autonomous delivery

---

## 📚 Базовый словарь

| Термин | Короткое определение |
|---|---|
| `intent` | Высокоуровневое намерение: что нужно изменить и зачем |
| `mission spec` | Структурированная формулировка intent с рисками, границами и acceptance gates |
| `formula` | Декларативный шаблон workflow, из которого можно инстанцировать molecule |
| `molecule` | Связанный граф шагов разработки, проверки, интеграции и публикации |
| `bead` | Атомарная единица работы с чётким acceptance criteria |
| `workcell` | Изолированная среда исполнения bead: worktree, container, preview env или sandbox |
| `simulacrum` | Динамический двойник среды или системы, создаваемый под конкретную задачу |
| `verification lattice` | Не одна линия CI, а сеть разных типов проверок и инвариантов |
| `evidence bundle` | Пакет доказательств: тесты, логи, метрики, diff, traces, screenshots, review verdicts |
| `Refinery` | Интеграционный агент, отвечающий за merge, совместимость и promotion |
| `knowledge plane` | Слой автоматических артефактов: Huly, GitHub, KB, dashboards, ADR, summaries |
| `context engineering` | Дисциплина управления тем, какие именно high-signal токены, документы, заметки и tool results попадают в контекст агента |
| `repo context` | Минимальный repository-level контекст для агента: команды, локальные ограничения, важные gotchas |
| `standards memory` | Долгоживущий слой инженерных норм и паттернов кодовой базы |
| `spec layer` | Артефакты, которые фиксируют what/why/how конкретного change и служат truth layer для исполнения |
| `task truth` | Структурированный operational state задач: ownership, blockers, dependencies, handoff, progress |
| `agent memory` | Слой памяти самого агента: наблюдения, preferences, session carry-over, learned context |
| `durable knowledge graph` | Долгоживущий temporal слой знаний о решениях, ограничениях, фактах и их происхождении |

---

## 🔗 Knowledge Graph Links

- [03-GAS-TOWN-ANALYSIS](../03-GAS-TOWN-ANALYSIS.md) --validates--> [NDI for software delivery]
- [02-SOVEREIGN-MESH](../02-SOVEREIGN-MESH.md) --extends--> [Autonomous Development Mesh]
- [04-ORCHESTRATOR-EVOLUTION](../04-ORCHESTRATOR-EVOLUTION.md) --enables--> [Role taxonomy for agent orchestration]
- [07-SNS3-FOUNDATIONS](../07-SNS3-FOUNDATIONS.md) --is_style_foundation_for--> [This series]
- [10-SOTA-Methods-And-Agent-Stacks](./10-sota-methods-and-agent-stacks.md) --extends--> [This series]
- [11-Memory-Context-And-Task-Ledgers](./11-memory-context-and-task-ledgers.md) --clarifies--> [Layered memory architecture]
- [12-Comparison-Matrix-And-Recommended-Stack](./12-comparison-matrix-and-recommended-stack.md) --operationalizes--> [Recommended stack]
