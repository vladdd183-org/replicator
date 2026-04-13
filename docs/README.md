# Документация Replicator

> Самоэволюционирующая модульная система на основе Hyper-Porto.

---

## Архитектура

| # | Документ | Описание |
|---|---|---|
| 00 | [Видение](architecture/00-vision.md) | Три режима работы, слоистая архитектура, принципы |
| 01 | [Слои](architecture/01-layers.md) | L0-L5: от транспорта до репликации |
| 02 | [Модель Cell](architecture/02-cell-model.md) | Cell -> Porto Container, CellSpec, Supervisor, Capabilities |
| 03 | [Адаптерная нейтральность](architecture/03-adapter-neutrality.md) | Protocols, Web2/Web3 адаптеры, DI-переключение |
| 04 | [Расширения Porto](architecture/04-porto-extensions.md) | Ship/Adapters, Ship/Cell, новые Sections |
| 05 | [Pipeline репликации](architecture/05-replication-flow.md) | Intent -> Spec -> Strategy -> Beads -> Execute -> Verify -> Promote |
| 06 | [Модель эволюции](architecture/06-evolution-model.md) | Мутация, fitness test, promotion, governance |

## Паттерны

| Документ | Описание |
|---|---|
| [Result Railway](patterns/result-railway.md) | Result[T, E], явные ошибки, pattern matching |
| [Gateway и Adapter](patterns/gateway-adapter.md) | Межмодульная связь, транспортная абстракция |
| [Event-Driven](patterns/event-driven.md) | Domain Events, подменяемые бэкенды, Outbox |
| [COMPASS-MAKER](patterns/compass-maker.md) | Стратегия + надежность в Porto Container-ах |
| [Spec-Bead Workflow](patterns/spec-bead-workflow.md) | Intent -> MissionSpec -> Formula -> Molecule -> Bead |
| [Вынос в микросервис](patterns/microservice-extraction.md) | Container -> отдельный сервис (механическая операция) |

## Справочники

| Документ | Описание |
|---|---|
| [Глоссарий](reference/glossary.md) | Все термины проекта |
| [Технологический стек](reference/tech-stack.md) | Библиотеки, фреймворки, инструменты |
| [Карта файлов](reference/file-map.md) | Какой файл за что отвечает |

## Спецификации

Формальные спецификации модулей -- в директории `specs/`.

## Быстрый старт

### Для разработчика
1. Прочитай [00-vision.md](architecture/00-vision.md) -- понять что и зачем
2. Прочитай [01-layers.md](architecture/01-layers.md) -- понять архитектуру
3. Посмотри [карту файлов](reference/file-map.md) -- где что лежит

### Для AI-агента
1. Прочитай [00-vision.md](architecture/00-vision.md) -- контекст проекта
2. Прочитай [глоссарий](reference/glossary.md) -- терминология
3. Прочитай паттерн, релевантный задаче
4. Посмотри примеры в `src/Containers/AppSection/UserModule/`

### Для архитектора
1. Вся директория `architecture/` -- от видения до эволюции
2. Все паттерны в `patterns/`
3. Спецификации в `specs/`
