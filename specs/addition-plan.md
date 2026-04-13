# План добавления: от чистого Ship к полному Replicator

> Порядок добавления новых компонентов с приоритетами.

---

## Принцип

Добавляем послойно, снизу вверх. Каждый шаг -- компилируемый, тестируемый промежуточный результат.

---

## Этап 1: Ship Extensions (P0)

**Цель:** адаптерная нейтральность и Cell engine.

| # | Компонент | Beads | Что получаем |
|---|---|---|---|
| 1.1 | `Ship/Core/Types.py` (расширение) | B-SHIP-CORE-001 | Базовые типы для адаптеров |
| 1.2 | `Ship/Adapters/Protocols.py` | B-SHIP-ADAPT-001 | 5 Protocol-ов |
| 1.3 | `Ship/Adapters/Errors.py` | B-SHIP-ADAPT-002 | Ошибки адаптеров |
| 1.4 | `Ship/Adapters/Storage/LocalAdapter.py` | B-SHIP-ADAPT-003 | Файловое хранилище |
| 1.5 | `Ship/Adapters/Messaging/InMemoryAdapter.py` | B-SHIP-ADAPT-004 | In-memory pub/sub |
| 1.6 | `Ship/Adapters/Identity/JWTAdapter.py` | B-SHIP-ADAPT-005 | JWT обертка |
| 1.7 | `Ship/Adapters/State/SQLiteAdapter.py` | B-SHIP-ADAPT-006 | SQLite state |
| 1.8 | `Ship/Adapters/Compute/SubprocessAdapter.py` | B-SHIP-ADAPT-007 | Subprocess compute |
| 1.9 | `Ship/Providers/AdapterProvider.py` | B-SHIP-ADAPT-008 | DI для адаптеров |
| 1.10 | `Ship/Cell/CellSpec.py` | B-SHIP-CELL-001 | Спецификация Cell |
| 1.11 | `Ship/Cell/Capabilities.py` | B-SHIP-CELL-002 | Capabilities |
| 1.12 | `Ship/Cell/Registry.py` | B-SHIP-CELL-003 | Registry Protocol |

**Результат:** Ship имеет полную адаптерную абстракцию и Cell engine. Можно подставлять любые реализации через DI.

---

## Этап 2: CoreSection (P1)

**Цель:** ядро репликатора -- компиляция спецификаций, реестр, шаблоны.

| # | Компонент | Beads | Что получаем |
|---|---|---|---|
| 2.1 | `CoreSection/SpecModule/Data/Schemas/` | B-CORE-SPEC-001 | Модели: MissionSpec, Bead, Formula |
| 2.2 | `CoreSection/SpecModule/Actions/CompileSpecAction.py` | B-CORE-SPEC-002 | Компиляция intent |
| 2.3 | `CoreSection/SpecModule/Actions/ValidateSpecAction.py` | B-CORE-SPEC-003 | Валидация spec |
| 2.4 | `CoreSection/SpecModule/{Events,Errors,Providers}.py` | B-CORE-SPEC-004 | Инфра модуля |
| 2.5 | `CoreSection/CellRegistryModule/` | B-CORE-REG-001,002 | Реестр Cell |
| 2.6 | `CoreSection/TemplateModule/` | B-CORE-TMPL-001,002 | Генерация кода |

**Результат:** можно скомпилировать intent в spec, зарегистрировать Cell, сгенерировать Porto-скелет.

---

## Этап 3: ToolSection (P1, параллельно с Этапом 2)

**Цель:** инструменты для исполнения.

| # | Компонент | Beads | Что получаем |
|---|---|---|---|
| 3.1 | `ToolSection/MCPClientModule/` | B-TOOL-MCP-001 | MCP tool integration |
| 3.2 | `ToolSection/GitModule/` | B-TOOL-GIT-001,002 | Git operations + PR |
| 3.3 | `ToolSection/NixModule/` | B-TOOL-NIX-001 | Nix build |

**Результат:** можно вызывать MCP-инструменты, работать с Git, строить через Nix.

---

## Этап 4: AgentSection (P2)

**Цель:** интеллект -- стратегия, декомпозиция, исполнение.

| # | Компонент | Beads | Что получаем |
|---|---|---|---|
| 4.1 | `AgentSection/CompassModule/` | B-AGENT-COMP-001,002 | Стратегия (COMPASS) |
| 4.2 | `AgentSection/MakerModule/` | B-AGENT-MAKER-001,002 | Декомпозиция + K-Voting (MAKER) |
| 4.3 | `AgentSection/OrchestratorModule/` | B-AGENT-ORCH-001 | BeadGraph Executor |

**Результат:** полный pipeline: intent -> strategy -> beads -> execute.

---

## Этап 5: EvolutionModule + Knowledge (P2)

**Цель:** верификация, promotion, знания.

| # | Компонент | Beads | Что получаем |
|---|---|---|---|
| 5.1 | `CoreSection/EvolutionModule/` | B-CORE-EVOL-001,002 | Verify + Promote |
| 5.2 | `KnowledgeSection/MemoryModule/` | B-KNOW-MEM-001 | Agent memory |
| 5.3 | `KnowledgeSection/KnowledgeGraphModule/` | B-KNOW-KG-001 | Knowledge Graph |

**Результат:** полный замкнутый pipeline: intent -> ... -> verify -> promote. Агенты имеют память и знания.

---

## Этап 6: Интеграция и CLI (P3)

**Цель:** собрать всё воедино, CLI команды.

| # | Компонент | Что получаем |
|---|---|---|
| 6.1 | Обновленный `App.py` | Все Sections подключены |
| 6.2 | CLI: `replicator spec:compile` | Компиляция intent |
| 6.3 | CLI: `replicator evolve` | Полный pipeline самоэволюции |
| 6.4 | CLI: `replicator generate` | Генерация нового проекта |
| 6.5 | CLI: `replicator cell:list/inspect` | Работа с реестром |
| 6.6 | `ToolSection/CICDModule/` | Генерация CI |
| 6.7 | `KnowledgeSection/SpecLibraryModule/` | Библиотека Formula |

**Результат:** работающий Replicator с CLI.

---

## Зависимости между этапами

```
Этап 1 (Ship) ─────────────────────┐
    |                                |
    +──> Этап 2 (CoreSection)  ──────+──> Этап 4 (AgentSection) ──> Этап 5 (Evolution+Knowledge)
    |                                |                                    |
    +──> Этап 3 (ToolSection)  ──────+                                    v
                                                                     Этап 6 (Integration)
```

Этапы 2 и 3 -- параллельны.
Этап 4 зависит от 2 и 3.
Этап 5 зависит от 4.
Этап 6 зависит от 5.
