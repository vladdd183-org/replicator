# План очистки Hyper-Porto -> Replicator

> Что удалить, что оставить, что адаптировать.

---

## Принцип

Hyper-Porto содержит demo-модули (UserModule, OrderModule, ...) которые демонстрируют паттерны. В Replicator они не нужны -- их заменят CoreSection, AgentSection, ToolSection, KnowledgeSection.

НО: demo-модули остаются в репозитории `hyper-porto` как showcase.

---

## УДАЛИТЬ

### Containers/AppSection/ (все demo-модули)

| Модуль | Причина удаления |
|---|---|
| `UserModule/` | Demo. Паттерны уже задокументированы. |
| `OrderModule/` | Demo. Saga паттерн задокументирован в docs/patterns. |
| `NotificationModule/` | Demo. Event паттерн задокументирован. |
| `SearchModule/` | Demo. |
| `SettingsModule/` | Demo. |
| `AuditModule/` | Demo. Audit trail будет в EvolutionModule. |

### Containers/VendorSection/ (все vendor-интеграции)

| Модуль | Причина удаления |
|---|---|
| `EmailModule/` | Не нужен для Replicator. |
| `PaymentModule/` | Не нужен для Replicator. |
| `WebhookModule/` | Не нужен для Replicator. |

### Корневые файлы связанные с demo

| Файл | Причина |
|---|---|
| `src/Providers.py` | Будет переписан под новые модули |
| `src/App.py` | Будет переписан под новые модули |
| `piccolo_conf.py` | Будет адаптирован под новые модели |

### Старая документация

| Директория | Причина |
|---|---|
| `docs/` (старые, из Hyper-Porto) | Заменены на новую документацию в docs/architecture, docs/patterns, docs/reference |
| `cursor-boost/` | Не релевантно для Replicator |
| `agent-os/` | Паттерны извлечены в документацию |

---

## ОСТАВИТЬ (без изменений)

### Ship/ -- полностью

| Компонент | Зачем нужен |
|---|---|
| `Ship/Core/` | Базовые типы, ошибки, протоколы -- фундамент |
| `Ship/Parents/` | Action, Task, Query, Repository, UoW -- ядро Porto |
| `Ship/Auth/` | JWT, Guards, Middleware -- используется IdentityPort |
| `Ship/CLI/` | CLI framework, генераторы -- расширяем |
| `Ship/Configs/` | Settings -- расширяем |
| `Ship/Decorators/` | @result_handler -- критический паттерн |
| `Ship/Exceptions/` | Problem Details -- RFC 9457 |
| `Ship/GraphQL/` | GraphQL infra -- опционально, оставляем |
| `Ship/Infrastructure/` | Cache, DB, Telemetry, Events, Workers -- фундамент |
| `Ship/Middleware/` | Idempotency, etc. -- полезно |
| `Ship/Providers/` | AppProvider -- расширяем AdapterProvider |

### Тесты Ship-уровня

Все тесты из `tests/` которые тестируют Ship компоненты -- оставить.

### Конфигурация проекта

| Файл | Зачем |
|---|---|
| `flake.nix` | Nix build -- адаптируем |
| `justfile` | Task runner -- адаптируем |
| `pyproject.toml` / `uv.lock` | Python deps -- обновляем |
| `.gitignore` | Оставляем |
| `.cursor/rules/` | Адаптируем под Replicator |

---

## АДАПТИРОВАТЬ

| Файл | Что изменить |
|---|---|
| `src/App.py` | Переписать: убрать demo роутеры, добавить новые Sections |
| `src/Providers.py` | Переписать: убрать demo providers, добавить новые |
| `Ship/Configs/Settings.py` | Добавить: adapter_mode, agent config, etc. |
| `Ship/Providers/AppProvider.py` | Добавить: AdapterProvider |
| `.cursor/rules/*.mdc` | Обновить правила под Replicator контекст |
| `README.md` | Полностью переписать |

---

## Порядок очистки

1. Удалить `Containers/VendorSection/` полностью
2. Удалить `Containers/AppSection/` полностью
3. Удалить старые `docs/*.md` (Porto docs, они в hyper-porto репо)
4. Удалить `cursor-boost/`, `agent-os/`
5. Обнулить `src/App.py` (минимальная точка входа)
6. Обнулить `src/Providers.py` (только Ship providers)
7. Адаптировать `README.md`
8. Адаптировать `.cursor/rules/`

После очистки проект должен собираться и запускаться (пустой Litestar app с Ship/).
