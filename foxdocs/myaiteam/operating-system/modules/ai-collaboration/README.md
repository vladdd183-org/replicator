# Модуль: AI Collaboration

**Версия:** 0.1  
**Дата:** 2026-02-09  
**DRI:** CEO / Архитектор

---

## Назначение

Модуль определяет **как команда FatData работает совместно с AI**. Не как с инструментом, а как с цифровым коллегой — с чёткими ролями, границами и правилами доверия.

Это наш **ключевой дифференциатор**. Большинство команд просто «используют ChatGPT». Мы строим системный подход к Human-AI коллаборации, который масштабируется вместе с командой.

## Статус компонентов

| Компонент | Статус | Описание |
|-----------|--------|----------|
| `hit-framework-light.md` | 🧪 Experiment | HIT Framework Light — AI-роли, границы, гайдлайны для текущего уровня |
| `human-ai-boundaries.md` | 🧪 Experiment | Матрица автономии AI: кто что решает, red lines |
| `hit-framework-full.md` | 📋 Planned | Полный HIT Framework — Diamond Model, multi-agent orchestration |

## Две версии

- **HIT Light** (сейчас) — минимальный фреймворк для 14 человек. AI как персональный ассистент каждого участника. Фокус: правила использования, границы доверия, реестр агентов.
- **HIT Full** (будущее, Level 3) — полноценная AI-native архитектура. Diamond Model, multi-agent системы (CrewAI, LangGraph), автоматические workflow. Активируется по [триггерам масштабирования](../../MANIFEST.md#триггеры-масштабирования).

## Зависимости

- **`core/principles.md`** — принцип #1 (Async-first + AI-native) — фундамент этого модуля
- **`core/roles-and-tiers.md`** — AI-навыки как обязательный skill на каждом уровне (раздел 3)

## Связанные исследования

Для глубокого погружения — исследовательские документы в корне `myaiteam/`:

| Документ | Что внутри |
|----------|-----------|
| [AI-Native-Startup-Framework.md](../../../AI-Native-Startup-Framework.md) | HIT Framework, COMPASS+MAKER, Agentic Workflows |
| [Human-AI-Collaboration-Guide.md](../../../Human-AI-Collaboration-Guide.md) | Trust Calibration, Mental Models, паттерны взаимодействия |
| [SOTA-AI-Native-Team-Architecture.md](../../../SOTA-AI-Native-Team-Architecture.md) | Diamond Model, Human-in-the-Loop, Multi-Agent Orchestration |

## История изменений

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| 0.1 | 2026-02-09 | AI + CEO | Первая версия. HIT Light + Human-AI Boundaries как эксперимент |
