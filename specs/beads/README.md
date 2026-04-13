# Декомпозиция на Beads

> Атомарные единицы работы с acceptance criteria, зависимостями и приоритетами.

---

## Формат Bead

| Поле | Описание |
|---|---|
| ID | Уникальный идентификатор (формат: `B-{section}-{module}-{number}`) |
| Spec | Родительская спецификация |
| Компонент | Что создается (Action, Task, Protocol, Model, ...) |
| Acceptance | Конкретные, проверяемые критерии |
| Зависимости | Beads, которые должны быть завершены раньше |
| Приоритет | P0 (critical path) / P1 (foundation) / P2 (feature) / P3 (enhancement) |

## Critical Path (порядок реализации)

```
P0: Ship Core Types + Adapter Protocols
  -> P0: Ship Adapter Web2 implementations
    -> P0: Ship Cell (CellSpec + Supervisor)
      -> P1: CoreSection/SpecModule
        -> P1: CoreSection/CellRegistryModule
          -> P1: CoreSection/TemplateModule
            -> P2: AgentSection/CompassModule
              -> P2: AgentSection/MakerModule
                -> P2: AgentSection/OrchestratorModule
                  -> P2: CoreSection/EvolutionModule
      -> P1: ToolSection/MCPClientModule (параллельно с SpecModule)
        -> P1: ToolSection/GitModule
          -> P1: ToolSection/NixModule
            -> P3: ToolSection/CICDModule
      -> P2: KnowledgeSection/MemoryModule (параллельно с AgentSection)
        -> P2: KnowledgeSection/KnowledgeGraphModule
          -> P3: KnowledgeSection/SpecLibraryModule
```
