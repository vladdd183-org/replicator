# Модель эволюции

> Как Replicator модифицирует сам себя: мутация спецификации, fitness test, promotion.

---

## Биологическая аналогия

| Биология | Replicator | Пояснение |
|---|---|---|
| ДНК | CellSpec | Полное описание "что модуль умеет" |
| Мутация | Новая версия CellSpec | Добавление Action, изменение Task, рефакторинг |
| Экспрессия | Code generation / modification | Spec -> реальный код |
| Фенотип | Запущенный Container | Работающий модуль с тестами |
| Fitness test | Verification Lattice | Тесты, линтеры, type check, review |
| Естественный отбор | Promotion / Rollback | Прошел тесты -> merge; не прошел -> откат |
| Видообразование | Fork + Divergence | Новый репозиторий с измененными модулями |

---

## Жизненный цикл версии

```
DRAFT -> CANDIDATE -> TESTING -> VERIFIED -> ACTIVE
                        |                      |
                        |  fail                |  deprecate
                        v                      v
                    REJECTED              DEPRECATED -> ARCHIVED
```

### Статусы

| Статус | Значение |
|---|---|
| `DRAFT` | Спецификация создана, код еще не сгенерирован |
| `CANDIDATE` | Код сгенерирован / модифицирован, готов к тестированию |
| `TESTING` | Проходит verification lattice |
| `VERIFIED` | Прошел все проверки, готов к promotion |
| `ACTIVE` | Текущая рабочая версия |
| `REJECTED` | Не прошел проверки, отклонен |
| `DEPRECATED` | Заменен новой ACTIVE версией |
| `ARCHIVED` | Долго deprecated, перемещен в архив |

---

## Immutable History

Каждая версия CellSpec -- immutable. Создание новой версии не удаляет старую, а порождает новый объект с ссылкой на родителя:

```
v1 (spec_hash: aaa111, status: ARCHIVED)
  |
  +-- v2 (spec_hash: bbb222, parent: aaa111, status: DEPRECATED)
        |
        +-- v3 (spec_hash: ccc333, parent: bbb222, status: ACTIVE)
              |
              +-- v4 (spec_hash: ddd444, parent: ccc333, status: TESTING)
```

Это Merkle-chain: каждая версия хеширует себя + parent_hash. В Web3 это станет CID-chain, аналог Ceramic stream.

---

## Типы мутаций

### 1. Расширение (Extension)

Добавление нового компонента без изменения существующих.

```
v1: SpecModule имеет [CompileSpecAction, ValidateSpecAction]
v2: SpecModule имеет [CompileSpecAction, ValidateSpecAction, OptimizeSpecAction]
```

Низкий риск: существующий код не менялся.

### 2. Модификация (Modification)

Изменение поведения существующего компонента.

```
v1: CompileSpecAction использует simple prompt
v2: CompileSpecAction использует DSPy-оптимизированный prompt
```

Средний риск: нужно проверить, что контракты не нарушены.

### 3. Рефакторинг (Refactoring)

Изменение структуры без изменения поведения.

```
v1: MonolithicAction с 200 строками
v2: Action разбит на 3 Task-а
```

Средний риск: поведение не должно измениться (fitness test проверяет).

### 4. Удаление (Deprecation)

Пометка компонента как deprecated и создание замены.

```
v1: OldGateway (deprecated)
v2: NewGateway (active), OldGateway (compatibility shim)
```

Высокий риск: нужно проверить, что никто не зависит от удаленного.

---

## Fitness Test (Verification Lattice)

Не одна линия CI, а **решетка** разных типов проверок:

```
                    +-- Unit Tests
                    |
                    +-- Integration Tests
                    |
Candidate ------>   +-- Type Checking (pyright)        ----> Evidence Bundle
                    |
                    +-- Linting (ruff)
                    |
                    +-- Architecture Guards
                    |
                    +-- Semantic Review (агент)
                    |
                    +-- Contract Verification
```

### Architecture Guards -- проверки Porto-правил

- Container не импортирует из другого Container
- Все Actions возвращают `Result[T, E]`
- Все Errors наследуют от `BaseError`
- Нет относительных импортов
- Каждый модуль имеет `Providers.py`
- Events pub/sub баланс (все emitted events имеют хотя бы один listener)

### Contract Verification

Проверяет, что контракты (Protocols, type signatures) не нарушены:

- Новые Actions имеют правильные type annotations
- Реализации Protocols полны (все методы реализованы)
- Events имеют правильную структуру (Pydantic frozen models)
- Спецификация (CellSpec) соответствует реальному коду

---

## Promotion Strategy

### Для self_evolve

```
1. Создать feature branch
2. Применить изменения
3. Запустить verification lattice
4. Если pass -> merge в main через merge queue
5. Обновить CellRegistry
6. Пометить старую версию как DEPRECATED
```

### Для generate

```
1. Создать новый репозиторий из шаблона
2. Применить сгенерированный код
3. Запустить базовую верификацию (тесты шаблона + lint)
4. Если pass -> push
5. Зарегистрировать в CellRegistry как новую Cell
```

### Для legacy

```
1. Создать feature branch в legacy репозитории
2. Применить изменения
3. Запустить CI legacy проекта
4. Если pass -> создать PR
5. Дождаться merge (или автоматически через merge queue)
```

---

## Governance: кто решает

| Уровень | Кто решает | Что решает |
|---|---|---|
| Trivial (lint fix, typo) | Автоматически | Merge после прохождения тестов |
| Simple (новый Task, мелкий рефакторинг) | Агент-ревьюер | Проверяет quality, merge при approval |
| Moderate (новый Action, изменение API) | Агент + человек | Агент готовит review, человек одобряет |
| Complex (новый Module, архитектурное изменение) | Человек | Полный human review |
| Critical (изменение Ship, адаптеров, Cell engine) | Человек + ADR | Обязательно Architecture Decision Record |

Уровень определяется автоматически на основе:
- Количество измененных файлов
- Затронутые слои (Ship > Containers)
- Наличие breaking changes в контрактах
- Confidence score от CompassModule
