# ВИДЕНИЕ ВЛАДЕЛЬЦА

> Заметка о том, как владелец мыслит и что для него важно. Для контекста следующего AI-агента.

---

## Как владелец мыслит

Владелец (vladdd183) -- системный архитектор, который мыслит фрактально и в терминах децентрализации. Он видит все свои проекты как ОДИН стек:

```
L5 Приложения         -- Synesthesia Engine, Dashboard, Agent interfaces
L4 Стратегия          -- COMPASS + MAKER + DSPy
L3 Структура кода     -- Hyper-Porto (Ship + Containers)
L2 Рантайм            -- sandboxai / NixBox (Cell lifecycle)
L1 Инфраструктура     -- nn3w / vladOS (NixOS + Den)
L0 I/O                -- IPFS + Ceramic + Lattica / libp2p
```

Все проекты -- не отдельные, а слои одного целого.

## Ключевые принципы владельца

1. **Централизация -- частный случай децентрализации.** Web2 работает сейчас, но архитектура должна быть готова к Web3 без переписывания.

2. **Модульность важнее всего.** Porto нравится именно потому, что модули можно легко отсоединять и присоединять. "Франкенштейн" -- модульный сборщик.

3. **Spec-first.** Спецификация первична, код вторичен. Любое изменение начинается с описания что и зачем.

4. **AI должен работать НА системе, а не В системе.** Конечная цель -- система, которая не зависит от конкретного IDE (Cursor), а работает автономно.

5. **Nix -- фундамент.** Reproducible builds, декларативность, content-addressing -- это те же принципы что и в Web3 (CID, DAG).

6. **Всё на русском.** Документация, комментарии, коммиты. Код (имена) -- на английском.

## Что владелец хочет в итоге

Систему, которая:
- Принимает задачу на естественном языке
- Формирует стратегию через COMPASS
- Декомпозирует через MAKER
- Исполняет через MCP + Git + Nix
- Верифицирует и промоутит
- Учится на ошибках (Knowledge Graph + Memory)
- Может создать другой такой же проект
- Может улучшить саму себя
- Работает с разными LLM через OpenRouter
- Использует дешевые модели для тривиальных задач, мощные для сложных
- Лучше Cursor, потому что специализирована и самоулучшается

## Проекты-наработки (всё в foxdocs/)

| Проект | Что дает Replicator-у |
|---|---|
| nn3w | Nix aspects, extractable modules, infra patterns |
| factory-ai | 5-слойный стек, DSPy deep dive |
| COMPASS_MAKER | Агентская архитектура (стратегия + надежность) |
| myaiteam | Knowledge Graph, IPFS/UCAN, team processes |
| fd_cicd | Nix CI/CD, runners, nix2container |
| python-uv-nix | Шаблон Python + Nix + OCI |
| research/Fractal Atom | Теория Cell, четыре концепции |
| research/Autonomous Dev Mesh | Recommended stack, beads, NDI |

## OpenRouter config (из opencode.json)

Владелец уже использует OpenRouter. Пример конфигурации:
```json
{
    "$schema": "https://opencode.ai/config.json",
    "model": "openrouter/glm-preset",
    "provider": {
      "openrouter": {
        "models": {
          "glm-preset": {
            "id": "@preset/glm",
            "name": "GLM (OpenRouter preset)"
          }
        }
      }
    }
}
```

То есть инфраструктура OpenRouter уже знакома и используется.
