# Глубокое исследование snix-eval и snix-build

> Детальный технический анализ двух ключевых компонентов Snix (бывш. Tvix):
> evaluator (snix-eval) и builder (snix-build).
> Включает архитектуру, оптимизации, текущий статус, бенчмарки и сценарии ускорения CI/CD.

---

## 1. snix-eval — Bytecode VM Evaluator

### 1.1 Архитектура

snix-eval — bytecode-интерпретатор языка Nix, написанный на Rust (~4000 строк).
Построен по архитектуре из книги [Crafting Interpreters](https://craftinginterpreters.com/):
вместо прямого обхода AST (как в C++ Nix) используется двухфазный подход.

```
┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐
│  Nix source  │───▶│    Compiler      │───▶│   Snix VM         │
│  (.nix file) │    │  (rnix AST →     │    │  (frame-based     │
│              │    │   Snix bytecode)  │    │   execution loop) │
└──────────────┘    └──────────────────┘    └───────────────────┘
       ▲                    │                        │
       │              ┌─────┘                        │
  rnix-parser         ▼                              ▼
  (Rowan-based)  ┌─────────┐                  ┌──────────┐
                 │ Opcodes  │                  │ Values   │
                 │ set      │                  │ (NixAttrs│
                 └─────────┘                  │  NixList │
                                              │  Thunks) │
                                              └──────────┘
```

#### Фазы работы

1. **Парсинг** — `rnix-parser` (Rowan-based) генерирует concrete syntax tree (CST), сохраняющее
   полную информацию о позициях в исходном коде. Это позволяет использовать snix-eval
   как основу для dev tooling (LSP, форматтеры).

2. **Компиляция** — обходит AST от rnix и генерирует Snix-специфический bytecode:
   - Глубокий анализ scopes: компилятор знает, какие идентификаторы доступны, и генерирует
     эффективный bytecode для доступа к переменным
   - Предупреждения и ошибки **без раннего fail** — может продолжать компиляцию после ошибок
   - Подходит для IDE-интеграции

3. **Выполнение** — VM с frame-based execution loop:
   - Stack of `Frame` (CallFrame или Generator)
   - Каждый фрейм обрабатывается в основном цикле VM
   - `ImportCache` — кеширование результатов `import` по canonical path (аналогично C++ Nix)
   - `PathImportCache` — маппинг абсолютных путей файлов в store paths

### 1.2 Система опкодов (Instruction Set)

Snix использует **Nix-специфический набор инструкций**, не general-purpose bytecode.

#### Примитивные операции

- `OP_CONSTANT` — загрузить константу на стек
- `OP_ADD`, `OP_SUB`, `OP_MUL`, `OP_DIV` — арифметика
- `OP_NEGATE`, `OP_INVERT` — унарные операции

#### Операции с атрибутами (ключевая оптимизация)

Специализированные опкоды для attribute sets — наиболее частая операция в Nix:

```
# Простой attrset: { foo = 42; }
0000 OP_CONSTANT(0)  # key "foo"
0001 OP_CONSTANT(1)  # value 42
0002 OP_ATTR_SET(1)  # construct attrset from 1 pair

# Вложенные ключи: { a.b = 15; }
0000 OP_CONSTANT(0)  # key "a"
0001 OP_CONSTANT(1)  # key "b"
0002 OP_ATTR_PATH(2) # construct attrpath from 2 fragments
0003 OP_CONSTANT(2)  # value 15
0004 OP_ATTRS(1)     # construct attrset from one pair

# Динамические ключи: { "${k}" = 42; }
0000..000n <operations leaving key value on stack>
000n+1     OP_CONSTANT(1)  # value 42
000n+2     OP_ATTR_SET(1)  # construct attrset
```

`OP_ATTR_PATH` — позволяет выражать произвольно вложенные ключи. VM самостоятельно
создаёт nested maps при обработке `OP_ATTRS`, проверяя дубликаты ключей.

#### Рекурсивные attribute sets (rec { ... })

Компилятор разбивает `rec { ... }` на три фазы scoping:

1. `inherit` значения из внешнего scope
2. Новый scope для статически известных рекурсивных ключей
3. Третий scope для динамических ключей (которые не могут рекурсировать в `self`)

Это преобразуется в эквивалент вложенных `let`-привязок, переиспользуя
существующую оптимизированную обработку let-binding.

### 1.3 Оптимизации

#### Lazy Evaluation (Thunks)

```
┌─────────────┐     force      ┌──────────────┐
│   Thunk     │ ─────────────▶ │   Value      │
│ (delayed    │                │ (evaluated   │
│  computation│                │  result)     │
│  + upvalues)│                │              │
└─────────────┘                └──────────────┘
```

- **Thunks** — отложенные вычисления, которые выполняются только при необходимости
- **Upvalues** — захват переменных из окружающего scope (для thunks и closures)
- Бинарные операции и select-выражения могут быть thunk-ированы компилятором
  (откладывая вычисление до фактического использования результата)
- `final_deep_force` — генератор для глубокого форсирования финального значения

#### Tail-Call Optimization (TCO)

- VM поддерживает tail-call optimization для рекурсивных выражений
- Позволяет вычислять рекурсию в **постоянном stack space**
- Работает для многих (но ещё не для всех) случаев

#### Оптимизированные представления значений

Один и тот же Nix тип имеет **разные backing representations** в зависимости от содержимого:

| Тип | Пустой | Маленький | Большой |
|-----|--------|-----------|---------|
| `NixAttrs` | Empty variant | KV (1 пара, без hashmap) | Full BTreeMap |
| `NixString` | — | Small (inline) | Heap-allocated |

Это оптимизирует частые паттерны (пустые attrsets, name/value пары)
без влияния на общий случай.

#### Строки как byte strings

В отличие от ранних версий (Rust `String`, UTF-8), сейчас snix-eval
использует `Vec<u8>` как backing store для строк — полная совместимость
с C++ Nix, который использует C-style zero-terminated строки.

#### String Contexts

Полная поддержка string contexts (контексты Nix-строк), включая:
- `builtins.unsafeDiscardStringContext`
- `builtins.getContext` / `builtins.appendContext`
- Корректное распространение контекстов через конкатенацию и интерполяцию

Это необходимо для bit-to-bit совместимости с C++ Nix из-за
[бага в Nix](https://github.com/NixOS/nix/issues/4629), который обходится
в `stdenv.mkDerivation`.

#### Catchable Errors (tryEval)

Специальный тип значения `CatchableErrorKind` для обработки `builtins.tryEval`:
- В C++ Nix используются C++ exceptions (стек вызовов = AST дерево)
- В Snix exceptions хранятся как специальный тип значения в VM

### 1.4 Pluggable I/O (`EvalIO` trait)

```rust
trait EvalIO {
    fn path_exists(&self, path: &Path) -> Result<bool>;
    fn read_to_end(&self, path: &Path) -> Result<Vec<u8>>;
    fn read_dir(&self, path: &Path) -> Result<Vec<(SmallVec<...>, FileType)>>;
    // ... etc
}
```

- **`StdIO`** — стандартная реализация, работает с локальной FS
- **`DummyIO`** — заглушка для контекстов без IO (WASM, тесты)
- **Custom** — позволяет подключать remote store, mock FS, snix-castore

Это критически важно: snix-eval **не привязан к конкретному store**.
evaluator не знает о `/nix/store`, FUSE, или gRPC — всё это инжектируется
через `EvalIO`.

### 1.5 Pluggable Builtins

```
┌──────────────────────────────────────────────────────────┐
│  snix-eval core builtins (в crate snix-eval)            │
│  map, filter, foldl, length, elemAt, attrNames, ...     │
├──────────────────────────────────────────────────────────┤
│  snix-glue builtins (в crate snix-glue)                 │
│  derivation, fetchurl, fetchTarball, path, filterSource  │
│  + import builtins + SnixStoreIO                        │
├──────────────────────────────────────────────────────────┤
│  User builtins (в вашем коде)                           │
│  Можно добавить свои builtins через API                 │
└──────────────────────────────────────────────────────────┘
```

`builtins.derivation` (точнее `derivationStrict`) живёт в `snix-glue`,
а не в `snix-eval` — это сознательное решение для модульности.
Как и в C++ Nix, `builtins.derivation` — это Nix-код, вызывающий `derivationStrict`.

### 1.6 Совместимость с nixpkgs

#### Текущий статус (апрель 2026)

| Что | Статус |
|-----|--------|
| Парсинг Nix language | ✅ Полный (через rnix-parser) |
| Основные builtins | ✅ Большинство реализовано |
| String contexts | ✅ Полная поддержка |
| `builtins.tryEval` / Catchable | ✅ Реализовано |
| `builtins.derivation` / derivationStrict | ✅ Реализовано |
| `builtins.fetchurl` / fetchTarball | ✅ Реализовано |
| `builtins.path` / `filterSource` | ✅ Реализовано |
| `builtins.fetchTree` (flakes) | 🟡 В разработке (WIP) |
| `toJSON`, `fromJSON`, `toXML`, `fromTOML` | ✅ Реализовано |
| Оценка nixpkgs hello | ✅ Корректный output path |
| Оценка nixpkgs firefox | ✅ Корректный output path (тест cross-compilation) |
| Regression testing vs C++ Nix в CI | ✅ Работает |
| Полная оценка всего nixpkgs | 🟡 Большая часть, но не 100% |
| Flakes поддержка | 🔴 Нет (fetchTree WIP) |
| Замена `nix eval` в production | 🔴 Не готово |

#### Регрессионное тестирование

- CI регулярно проверяет, что snix-eval генерирует **те же output paths**, что и C++ Nix
- Тестируется на сложных выражениях (Firefox, cross-compilation)
- Интеграция с [Windtunnel](https://staging.windtunnel.ci/tvl/tvix) для
  мониторинга производительности между коммитами

### 1.7 Бенчмарки

#### Ранние бенчмарки (сент. 2022)

Из блога TVL:
> "In most cases Tvix evaluation is an **order of magnitude faster**" на изолированных
> языковых фичах (не nixpkgs).

Это касалось чисто языковых операций: арифметика, manipulations с attrsets,
рекурсия — всё, что полностью внутри VM без IO.

#### Бенчмарк Mic92 (май 2023, Tvix vs Nix 2.19.2)

| Выражение | Tvix | C++ Nix | Ratio |
|-----------|------|---------|-------|
| `toString hello` | 2.055s | 0.358s | **5.73x медленнее** |
| `toString firefox` | 22.415s | 1.962s | **11.42x медленнее** |

> **AMD EPYC 7713P, 64 cores, NixOS**

**Важно**: на тот момент Tvix **не имел собственного store** и вызывал `nix-store`
для каждой файловой операции. Основное время тратилось на IO, а не на evaluation.
Это бенчмарк "evaluator + наихудший IO backend", а не чистый eval.

#### Текущая ситуация (2025-2026)

- Store реализован полностью (redb, objectstore, grpc)
- Continuous benchmarking через Windtunnel
- Конкретных публичных чисел нового замера пока нет
- Фокус на **корректности** перед оптимизацией производительности
- devenv (от Cachix) [объявил о переходе на Tvix evaluator](https://devenv.sh/blog/2024/10/22/devenv-is-switching-its-nix-implementation-to-tvix) (окт. 2024)

#### Потенциал для ускорения

Bytecode VM по природе даёт преимущества:

| Аспект | C++ Nix (AST walk) | Snix (Bytecode VM) |
|--------|--------------------|--------------------|
| Dispatch overhead | Рекурсивный обход узлов AST, virtual dispatch | Flat loop + switch на opcodes, предсказуемый CPU pipeline |
| Memory layout | AST nodes разбросаны в heap | Bytecode — компактный плоский массив, cache-friendly |
| Кеширование bytecode | Нет (eval с нуля каждый раз) | Можно кешировать скомпилированный bytecode |
| Инкрементальная eval | Нет | Потенциально — кеш bytecode + ImportCache |
| Параллелизм | Однопоточный | Архитектура допускает параллельную eval (планируется) |

### 1.8 Можно ли использовать snix-eval вместо `nix eval` в CI?

**Сейчас: НЕТ**, по следующим причинам:

1. **Нет поддержки flakes** — `builtins.fetchTree` в разработке
2. **CLI нестабилен** — `snix-cli` является "vehicle для тестирования", не production tool
3. **Не все builtins реализованы** — могут быть edge cases
4. **Нет гарантии bit-to-bit совместимости** для всех nixpkgs выражений

**Можно экспериментировать** с:
- Evaluation простых Nix выражений (без flakes)
- Использование snix-eval как **библиотеки** в Rust-приложении
- Snixbolt (WASM bytecode explorer) для отладки и обучения

**В перспективе (по мере дозревания)**:
- Кеширование bytecode между CI runs → быстрая re-evaluation
- Parallel evaluation (обсуждается в проекте)
- devenv уже планирует использовать как production evaluator

---

## 2. snix-build — Pluggable Builder

### 2.1 Архитектура

```
┌────────────────────────────────────────────────────────────────┐
│                        snix-glue                                │
│   Derivation → BuildRequest трансляция                         │
│   (Nix derivation ⟶ content-addressed BuildRequest)           │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│   Fetch/Build Realization Strategies                           │
│   (стратегии: когда строить, когда fetch-ить)                  │
└────────────────────────┬───────────────────────────────────────┘
                         │ BuildRequest (protobuf)
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                      snix-build                                 │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ Builder Trait     │  │ gRPC Server      │                    │
│  │ (pluggable)      │  │ Adapter          │                    │
│  └────────┬─────────┘  └────────┬─────────┘                    │
│           │                     │                               │
│  ┌────────┴─────────────────────┴─────────┐                    │
│  │            Implementations              │                    │
│  │                                         │                    │
│  │  ✅ OCI Runner (runc)                   │                    │
│  │  ✅ gRPC Client (remote builds)         │                    │
│  │  🔮 MicroVM Executor (firecracker)      │                    │
│  │  🔮 Kubernetes Executor                 │                    │
│  │  🔮 gVisor Executor                     │                    │
│  │  🔮 bwrap (bubblewrap)                  │                    │
│  │  🔮 Cloud Hypervisor                    │                    │
│  └─────────────────────────────────────────┘                    │
└────────────────────────────────────────────────────────────────┘

✅ = реализовано   🔮 = планируется / в component overview diagram
```

### 2.2 Builder Protocol (BuildRequest)

Протокол определён в `build/protos/build.proto` (protobuf) и сознательно
**не привязан к Nix internals**.

#### Структура BuildRequest

```protobuf
message BuildRequest {
  repeated castore.Node inputs = 1;        // castore root nodes как входы
  string inputs_dir = 2;                    // куда монтировать inputs
  repeated string command_args = 3;         // команда для выполнения
  string working_dir = 4;                   // рабочая директория
  repeated bytes scratch_paths = 5;         // writable paths
  repeated EnvVar environment_vars = 6;     // переменные окружения
  repeated string expected_outputs = 7;     // ожидаемые output paths
  bool provide_bin_sh = 8;                  // статический /bin/sh
  bool network_access = 9;                  // доступ к сети
}
```

#### Ключевые принципы протокола

| Принцип | Описание |
|---------|----------|
| **Nix-agnostic** | Протокол не знает о store paths, derivations, NAR. Только generic: env vars, paths, commands |
| **Content-addressed inputs** | Входы передаются как castore root nodes с BLAKE3 хешами содержимого |
| **Hermetic** | Нет зависимости от состояния remote builder (в отличие от Nix remote builds) |
| **Streaming logs** | Планируется переход на stream of events для логов/телеметрии |

#### Трансляция Derivation → BuildRequest

Происходит в `snix-glue` (`glue/src/tvix_build.rs`):

1. Nix Derivation (ATerm) разбирается на компоненты
2. Каждый input store path заменяется на **castore root node** (content-addressed)
3. Environment variables из derivation переносятся в BuildRequest
4. `$out` и другие output paths становятся `expected_outputs`

### 2.3 OCI Builder — как работает

```
┌──────────────────────────────────────────────────────────────────┐
│                        OCI Builder                                │
│                                                                   │
│  1. Получает BuildRequest                                        │
│                    │                                              │
│  2. Создаёт OCI Runtime Specification                            │
│     ┌─────────────┴──────────────────┐                           │
│     │  config.json (OCI spec)        │                           │
│     │  - rootfs (overlay)            │                           │
│     │  - mounts (inputs из castore)  │                           │
│     │  - process (command_args)      │                           │
│     │  - env (environment_vars)      │                           │
│     └────────────────────────────────┘                           │
│                    │                                              │
│  3. Монтирует inputs из snix-castore                             │
│     ┌─────────────┴──────────────────┐                           │
│     │  Каждый castore root node      │                           │
│     │  монтируется в inputs_dir      │                           │
│     │  (FUSE или virtiofs)           │                           │
│     │                                │                           │
│     │  НЕ копируется на диск!        │                           │
│     │  Read-on-demand из castore     │                           │
│     └────────────────────────────────┘                           │
│                    │                                              │
│  4. Вызывает runc для выполнения                                 │
│     ┌─────────────┴──────────────────┐                           │
│     │  runc create + runc start      │                           │
│     │  (OCI-compliant container      │                           │
│     │   runtime)                     │                           │
│     └────────────────────────────────┘                           │
│                    │                                              │
│  5. Собирает outputs и загружает в castore                       │
│     ┌─────────────┴──────────────────┐                           │
│     │  expected_outputs → BlobService │                           │
│     │  + DirectoryService            │                           │
│     │  + PathInfoService             │                           │
│     └────────────────────────────────┘                           │
└──────────────────────────────────────────────────────────────────┘
```

### 2.4 Монтирование build inputs через castore (без копирования)

Это **ключевое архитектурное преимущество** snix-build.

#### Проблема в стандартном Nix

```
Стандартный Nix build:
1. Все dependencies → /nix/store (полные copies)
2. Sandbox видит полный /nix/store (или bind-mounts конкретных путей)
3. Даже если build использует 1 файл из 10000 — все 10000 на диске

→ Огромное время на substitution и disk I/O
```

#### Решение в Snix

```
Snix build:
1. Build inputs описаны как castore root nodes (Merkle DAG)
2. OCI builder монтирует их через FUSE/virtiofs
3. Файлы читаются ON DEMAND из castore (lazy)
4. Чанки, которые уже есть локально, не скачиваются
5. Одинаковые чанки между разными inputs — хранятся один раз

→ Минимальный IO, максимальная дедупликация
```

#### Детально: как FUSE mount работает для build inputs

1. snix-castore предоставляет FUSE adapter
2. При mount: в ядро регистрируется virtual filesystem
3. При первом `open(path)`:
   - FUSE handler получает запрос
   - Ищет Directory node по пути (PathInfoService → DirectoryService)
   - Находит file blob hash
   - Запрашивает blob из BlobService (может быть remote!)
4. Последующие чтения: FUSE caching / kernel page cache
5. Файлы, которые build **не открывает** — **никогда не скачиваются**

### 2.5 Remote Build через gRPC

```
┌─────────────────┐     gRPC BuildRequest     ┌─────────────────────┐
│  Orchestrator   │ ──────────────────────────▶│  Remote Builder     │
│  (snix-cli /    │                            │                     │
│   snix-glue)    │     gRPC BuildResponse     │  OCI Runner (runc)  │
│                 │ ◀──────────────────────────│  или другой backend │
└─────────────────┘                            └─────────────────────┘
        │                                               │
        │ gRPC                                          │ gRPC
        ▼                                               ▼
┌─────────────────┐                            ┌─────────────────────┐
│ snix-store      │     sync blobs/dirs        │ snix-store          │
│ (local)         │ ◀─────────────────────────▶│ (remote)            │
└─────────────────┘                            └─────────────────────┘
```

#### Преимущества gRPC remote build vs Nix remote build

| Аспект | Nix remote build | Snix gRPC build |
|--------|-----------------|-----------------|
| Передача inputs | NAR (целые store paths) | Content-addressed chunks (только delta) |
| Верификация | По store path (input-addressed) | По BLAKE3 hash содержимого |
| Frankenbuilds | Возможны (другое содержимое по тому же path) | Невозможны (content-addressed) |
| Granularity | Целый store path или ничего | Отдельные файлы и чанки |
| Протокол | Nix daemon protocol (custom, undocumented) | gRPC (стандарт, tooling, observability) |

#### Можно ли распределять сборки?

**Да**, gRPC протокол позволяет:
- Один orchestrator → несколько builders
- Builder может быть на другой машине, в другом DC
- OpenTelemetry tracing пропагируется через gRPC (trace IDs в headers)
- Можно построить scheduler/queue перед пулом builders

**НО**: scheduler/queue пока не реализован в самом Snix.
Это инфраструктура, которую нужно строить поверх gRPC API.

### 2.6 Планируемые builder backends

Из component overview diagram на snix.dev:

| Backend | Статус | Описание |
|---------|--------|----------|
| **OCI Runner (runc)** | ✅ Реализован | Создаёт OCI spec, запускает runc |
| **gRPC Server/Client** | ✅ Реализован | Локальные и удалённые сборки |
| **MicroVM Executor** | 🔮 В диаграмме | Firecracker/Cloud Hypervisor |
| **Kubernetes Executor** | 🔮 В диаграмме | Запуск сборок как K8s Jobs/Pods |
| **gVisor Executor** | 🔮 В диаграмме | Sandbox на базе gVisor |
| **bwrap** | 🔮 Упоминается в docs | Bubblewrap sandbox (как в Flatpak) |

Из документации протокола:
> "With a well-defined builder abstraction, it's also easy to imagine other backends
> such as a Kubernetes-based / bwrap / gVisor / Cloud Hypervisor in the future."

Также обсуждался переход на [REAPI](https://discourse.nixos.org/t/a-proposal-for-replacing-the-nix-worker-protocol/20926/22)
(Remote Execution API, используемый в Bazel), что открыло бы интеграцию
с существующей экосистемой remote execution.

### 2.7 Текущий статус: можно ли собирать реальные пакеты?

| Вопрос | Ответ |
|--------|-------|
| Простые пакеты (hello) | ✅ Работает (с августа 2024) |
| Сложные пакеты (firefox) | 🟡 Evaluation работает, build — не полностью |
| Reference scanning | 🟡 В процессе реализации (критически нужно) |
| IFD (Import From Derivation) | ✅ Архитектурно поддерживается нативно |
| Полный nixpkgs build | 🔴 Не готово |
| Production использование builder | 🔴 Не готово |

Из блога Tvix (август 2024):
> "We were already able to build some first few store paths with Tvix
> and our runc-based builder 🎉!"

> "We didn't get too far though, as we still need to implement reference
> scanning, so that's next on our TODO list."

---

## 3. Ускорение сборки контейнеров — конкретный сценарий

### 3.1 Текущий pipeline: nix2container

```
flake.nix → nix eval → nix build → nix2container → OCI image → push
    │           │           │              │
    │      ~2-5s eval   ~30s-5min      ~5-30s
    │     (каждый раз     build       (layer skip
    │      с нуля)     (full rebuild    если есть)
    │                   без delta)
```

### 3.2 Как Snix может ускорить каждый этап

#### Этап 1: snix-eval → быстрая evaluation flake.nix

**Сейчас (не готово)**: нет flake-поддержки.

**В перспективе**, преимущества snix-eval для CI:

| Оптимизация | Механизм | Потенциальный выигрыш |
|-------------|----------|----------------------|
| Bytecode caching | Кеш скомпилированного bytecode между CI runs | ~50-80% ускорение re-evaluation (не нужно re-parse + re-compile nixpkgs) |
| Lazy evaluation | Thunks: оцениваем только то, что реально нужно | Уже есть и в Nix, но bytecode VM делает это эффективнее |
| ImportCache | Кеш результатов `import` по canonical path | Избегаем re-evaluation одних и тех же файлов |
| Parallel eval | Планируется: оценка независимых derivations параллельно | Потенциально 2-4x на multi-core |
| IFD без блокировки | Graph-based scheduling вместо двух фаз | IFD не блокирует остальную evaluation |

#### Этап 2: snix-build → быстрые derivation builds

| Оптимизация | Механизм | Потенциальный выигрыш |
|-------------|----------|----------------------|
| Lazy input mount | FUSE/virtiofs: файлы читаются on-demand | Не нужно копировать/скачивать неиспользуемые dependencies |
| Content-addressed dedup | Одинаковые файлы/чанки хранятся один раз | Меньше disk space, меньше network transfer |
| Granular substitution | Скачиваем только изменённые чанки, не целый NAR | 10-100x меньше transfer для minor updates |
| Remote build | gRPC → мощный build server | Offload тяжёлых сборок |

#### Этап 3: snix-castore → dedup и lazy fetch

```
Стандартный Nix CI:
  Download hello-2.12.1.nar.xz (32 MB)    # полный NAR
  Download hello-2.12.2.nar.xz (32 MB)    # другая версия — снова полный NAR
  Total: 64 MB

Snix castore CI:
  Download hello-2.12.1 chunks (32 MB)     # первый раз — все чанки
  Download hello-2.12.2 delta (0.5 MB)     # только изменённые чанки!
  Total: 32.5 MB

+ Если build не открывает файл — он вообще не скачивается
```

### 3.3 Комбинирование: snix-eval → nix-build? snix-eval → snix-build?

#### Вариант A: snix-eval → стандартный nix-build

**Теоретически возможно, но практически сложно:**

- snix-eval генерирует те же derivation hashes, что и C++ Nix
- Можно сохранить `.drv` файлы и передать в `nix-build`
- Но: нет стабильного CLI для этого, нет flake-поддержки

#### Вариант B: snix-eval → snix-build (полный Snix stack)

**Архитектурно поддерживается через snix-glue:**

```
snix-eval
    │ evaluates Nix, produces Derivation values
    ▼
snix-glue
    │ converts Derivation → BuildRequest
    │ manages KnownPaths, FetchRealizationStrategy
    ▼
snix-build
    │ executes BuildRequest via OCI/gRPC
    ▼
snix-castore
    │ stores results content-addressed
    ▼
nar-bridge
    │ exposes as Nix HTTP Binary Cache
    ▼
nix / другие потребители
```

**Это основной планируемый путь.** snix-cli уже работает именно так.

#### Вариант C: стандартный Nix + snix-castore overlay (РЕКОМЕНДУЕМЫЙ СЕЙЧАС)

**Работает уже сегодня:**

```
┌───────────────────────────────┐
│  nix-daemon (standard Nix)    │
│  uses Local Overlay Store     │
│  upper = /nix/store (local)   │
│  lower = snix nix-daemon      │
│              │                │
│              ▼                │
│     snix store daemon         │
│     + snix store mount (FUSE) │
│     + snix nix-daemon         │
│              │                │
│              ▼                │
│     snix-castore              │
│     (content-addressed,       │
│      deduplicated data)       │
└───────────────────────────────┘
```

Это позволяет:
- Использовать **стандартный Nix** для eval и build
- Но backing store — это **snix-castore** с дедупликацией
- Local builds идут в верхний слой (обычный /nix/store)
- Substitutions идут в нижний слой (snix-castore, 80-90% экономия)

---

## 4. Shared castore для нескольких раннеров

### 4.1 Архитектура: один snix daemon → несколько runners

```
┌──────────────────────────────────────────────────────────────────┐
│                          Host Machine                             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              snix store daemon                               │ │
│  │  gRPC listener: [::1]:8000                                  │ │
│  │  BlobService:      objectstore file:///var/lib/snix/blobs   │ │
│  │  DirectoryService: redb /var/lib/snix/directories.redb      │ │
│  │  PathInfoService:  redb /var/lib/snix/pathinfo.redb         │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                              │ gRPC                               │
│          ┌───────────────────┼───────────────────┐               │
│          │                   │                   │               │
│          ▼                   ▼                   ▼               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   Runner 1   │   │   Runner 2   │   │   Runner 3   │        │
│  │              │   │              │   │              │        │
│  │ snix store   │   │ snix store   │   │ snix store   │        │
│  │ mount /nix   │   │ mount /nix   │   │ mount /nix   │        │
│  │ (FUSE)       │   │ (FUSE)       │   │ (FUSE)       │        │
│  │              │   │              │   │              │        │
│  │ OR: overlay  │   │ OR: overlay  │   │ OR: overlay  │        │
│  │ store lower  │   │ store lower  │   │ store lower  │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              nar-bridge (HTTP Binary Cache)                  │ │
│  │  http://localhost:9000                                       │ │
│  │  Exposes snix-castore as Nix HTTP Binary Cache              │ │
│  │  (read-write)                                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 gRPC API для shared доступа

Три gRPC-сервиса, все могут обслуживать множество клиентов одновременно:

```protobuf
service BlobService {
  rpc Stat(StatBlobRequest) returns (StatBlobResponse);
  rpc Read(ReadBlobRequest) returns (stream BlobChunk);
  rpc Put(stream BlobChunk) returns (PutBlobResponse);
}

service DirectoryService {
  rpc Get(GetDirectoryRequest) returns (stream Directory);
  rpc Put(stream Directory) returns (PutDirectoryResponse);
}

service PathInfoService {
  rpc Get(GetPathInfoRequest) returns (PathInfo);
  rpc Put(PathInfo) returns (PathInfo);
  rpc List(ListPathInfoRequest) returns (stream PathInfo);
  rpc CalculateNAR(Node) returns (CalculateNARResponse);
}
```

#### Клиенты, которые могут подключаться:

1. **snix store mount** — FUSE mount, подключается к daemon по gRPC
2. **snix nix-daemon** — эмулирует nix-daemon протокол, подключается к daemon по gRPC
3. **nar-bridge** — HTTP binary cache, подключается к daemon по gRPC
4. **snix-build** — builder подключается к store по gRPC для получения inputs и сохранения outputs
5. **Любой custom клиент** — gRPC API открыт и документирован

### 4.3 Store Composition — тонкая настройка

Можно описать иерархию stores в TOML для сложных сценариев:

#### Пример: fetch-through cache с cache.nixos.org

```toml
[blobservices.root]
type = "objectstore"
object_store_url = "file:///var/lib/snix-castore/blobs"
object_store_options = {}

[directoryservices.root]
type = "redb"
path = "/var/lib/snix-castore/directories.redb"

[pathinfoservices.root]
type = "cache"
near = "&redb"
far = "&cache-nixos-org"

[pathinfoservices.redb]
type = "redb"
path = "/var/lib/snix-store/pathinfo.redb"

[pathinfoservices.cache-nixos-org]
type = "nix"
base_url = "https://cache.nixos.org"
trusted_public_keys = ["cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="]
blob_service = "&root"
directory_service = "&root"
```

Эта конфигурация:
1. Проверяет локальную redb базу (near)
2. Если нет — скачивает из cache.nixos.org (far)
3. Ингестит NAR в content-addressed blobs/directories
4. Кеширует PathInfo в redb для следующих запросов

#### Пример: LRU + gRPC remote

```toml
[blobservices.root]
type = "combined"
near = "&local"
far = "&remote"

[blobservices.local]
type = "objectstore"
object_store_url = "file:///var/lib/snix-castore/blobs"
object_store_options = {}

[blobservices.remote]
type = "grpc"
url = "grpc+http://store-server:8000"

[pathinfoservices.root]
type = "cache"
near = "&lru"
far = "&remote"

[pathinfoservices.lru]
type = "lru"
capacity = 5000

[pathinfoservices.remote]
type = "grpc"
url = "grpc+http://store-server:8000"
```

### 4.4 Сетевой доступ через nar-bridge

nar-bridge — HTTP Binary Cache сервер (read-write), использующий snix-castore.

```
Runner A (любая машина)                 Host с snix-castore
┌──────────────────┐                   ┌──────────────────────┐
│  nix-daemon      │  HTTP             │  nar-bridge          │
│  substituters =  │ ────────────────▶ │  http://host:9000    │
│  http://host:9000│                   │                      │
│                  │  GET /nar/...     │  ┌────────────────┐  │
│                  │  GET /nix-cache-  │  │ snix-store     │  │
│                  │      info         │  │ + snix-castore │  │
└──────────────────┘                   │  └────────────────┘  │
                                       └──────────────────────┘
```

Это позволяет:
- **Любому Nix клиенту** (стандартный Nix!) использовать snix-castore как binary cache
- Не нужна модификация клиента — стандартный HTTP Binary Cache протокол
- Read-write: runners могут и скачивать, и загружать build results
- nar-bridge автоматически ингестит NAR в content-addressed формат

### 4.5 NixOS systemd service (рекомендуемая конфигурация)

Snix пока не поставляет готовый NixOS module, но systemd services
описываются прямолинейно. Рекомендуемая конфигурация:

```nix
# /etc/nixos/snix-services.nix — концептуальный пример
{ config, pkgs, ... }:
let
  snixPkg = /* snix binary */;
in {
  # 1. snix store daemon — центральное хранилище
  systemd.services.snix-store-daemon = {
    description = "Snix Store gRPC Daemon";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "${snixPkg}/bin/snix store daemon";
      StateDirectory = "snix-castore snix-store";
      DynamicUser = true;
      Restart = "always";
    };
  };

  # 2. snix store mount — FUSE mount для /nix/store доступа
  systemd.services.snix-store-mount = {
    description = "Snix FUSE Store Mount";
    after = [ "snix-store-daemon.service" ];
    requires = [ "snix-store-daemon.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "${snixPkg}/bin/snix store mount /srv/snix-store";
      Restart = "always";
    };
  };

  # 3. snix nix-daemon — для overlay store интеграции
  systemd.services.snix-nix-daemon = {
    description = "Snix Nix Daemon (overlay store lower layer)";
    after = [ "snix-store-daemon.service" ];
    requires = [ "snix-store-daemon.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = ''
        ${snixPkg}/bin/snix nix-daemon \
          -l /run/snix-daemon.sock \
          --unix-listen-unlink
      '';
      Restart = "always";
    };
  };

  # 4. nar-bridge — HTTP binary cache
  systemd.services.snix-nar-bridge = {
    description = "Snix NAR Bridge (HTTP Binary Cache)";
    after = [ "snix-store-daemon.service" ];
    requires = [ "snix-store-daemon.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "${snixPkg}/bin/snix nar-bridge --listen [::]:9000";
      Restart = "always";
    };
  };

  # 5. Настройка Nix для overlay store
  nix.settings = {
    experimental-features = [ "local-overlay-store" ];
  };

  nix.extraOptions = ''
    store = local-overlay://?upper-layer=/nix/store&lower-store=unix%3A%2F%2F%2Frun%2Fsnix-daemon.sock&check-mount=false
  '';
}
```

> **Внимание**: это концептуальный пример. Реальная конфигурация зависит от
> версии Snix и может требовать дополнительных настроек (RequiresMountsFor и др.).
> В `ops/` директории репозитория Snix есть конфигурации для их собственных серверов.

### 4.6 Схема для CI: shared castore + N раннеров

```
                     ┌─────────────────────────────────────┐
                     │        GitHub / Gitea / etc.        │
                     │            CI Server                 │
                     └───────────────┬─────────────────────┘
                                     │ triggers
                     ┌───────────────┴─────────────────────┐
                     │          Runner Host                  │
                     │                                       │
                     │  ┌─────────────────────────────────┐ │
                     │  │     snix store daemon            │ │
                     │  │  /var/lib/snix-{castore,store}   │ │
                     │  │  gRPC :8000                      │ │
                     │  └────────┬──────┬─────┬───────────┘ │
                     │           │      │     │              │
                     │     ┌─────┘  ┌───┘     └────┐        │
                     │     │        │              │        │
                     │  ┌──▼───┐ ┌──▼───┐     ┌───▼──┐    │
                     │  │Job 1 │ │Job 2 │ ... │Job N │    │
                     │  │      │ │      │     │      │    │
                     │  │ nix  │ │ nix  │     │ nix  │    │
                     │  │+over-│ │+over-│     │+over-│    │
                     │  │ lay  │ │ lay  │     │ lay  │    │
                     │  └──────┘ └──────┘     └──────┘    │
                     │                                       │
                     │  ┌─────────────────────────────────┐ │
                     │  │     nar-bridge :9000             │ │
                     │  │  (HTTP Binary Cache для          │ │
                     │  │   внешних runners)               │ │
                     │  └─────────────────────────────────┘ │
                     └───────────────────────────────────────┘
```

**Преимущества**:
- **Дедупликация** — все runners делят один castore, одни и те же чанки хранятся один раз
- **Instant substitution** — если Runner 1 уже скачал/собрал пакет, Runner 2 получает его мгновенно из общего castore
- **Экономия диска** — 80-90% экономия vs отдельный /nix/store на каждый runner (кейс Replit: 6TB → 1.2TB)
- **Lazy fetch** — через FUSE mount файлы скачиваются только при обращении
- **Network cache** — nar-bridge позволяет обслуживать runners на других машинах

---

## 5. Сводная таблица готовности

| Компонент | Что делает | Можно использовать в prod? | Рекомендация |
|-----------|-----------|---------------------------|--------------|
| **snix-castore** | Content-addressed storage | ✅ Да (Replit в prod) | Использовать для dedup store |
| **snix-store daemon** | gRPC сервер для castore + store | ✅ Да | Центральный daemon на хосте |
| **snix store mount** | FUSE mount store | ✅ Да | Для overlay store lower layer |
| **snix nix-daemon** | Nix daemon протокол | ✅ Да (subset) | Для Local Overlay Store |
| **nar-bridge** | HTTP Binary Cache | ✅ Да | Для external binary cache |
| **snix-eval** | Nix evaluator | 🟡 Экспериментально | Не для замены `nix eval` в CI |
| **snix-build** | Pluggable builder | 🟡 Ранняя стадия | Не для production builds |
| **snix-cli** | REPL + eval | 🟡 Для тестирования | Не замена nix CLI |
| **Store Composition** | Тиерированные stores | 🟡 Experimental flag | Для продвинутых настроек |

---

## 6. Конкретные рекомендации для CI/CD

### Этап 1 (сейчас): snix-castore + overlay store

```
Выигрыш: 80-90% экономия disk space, дедупликация между runners
Усилие: среднее (настройка systemd services)
Риск: низкий (стандартный Nix для eval/build)
```

### Этап 2 (середина 2026): + nar-bridge для сетевого кеша

```
Выигрыш: shared binary cache между всеми runners без Attic/Cachix
Усилие: низкое (один дополнительный service)
Риск: низкий
```

### Этап 3 (по готовности snix-eval): bytecode caching

```
Выигрыш: ~50-80% ускорение evaluation через кеш bytecode
Усилие: зависит от зрелости API
Риск: средний (зависит от совместимости с flakes)
```

### Этап 4 (долгосрочно): полный Snix stack

```
Выигрыш: parallel eval, lazy build inputs, granular substitution
Усилие: высокое (migration от стандартного Nix)
Риск: высокий (зависит от зрелости проекта)
```

---

## Источники

| Источник | URL |
|----------|-----|
| Snix website | https://snix.dev/ |
| Snix repository | https://git.snix.dev/snix/snix |
| Component Overview | https://snix.dev/docs/components/overview/ |
| Architecture | https://snix.dev/docs/components/architecture/ |
| Build Protocol | https://snix.dev/docs/components/build/protocol/ |
| OCI Builder | https://snix.dev/docs/components/build/oci/ |
| Castore API | https://snix.dev/docs/reference/snix-castore-api/ |
| Store Composition | https://snix.dev/docs/guides/store-configuration-composition/ |
| Local Overlay Guide | https://snix.dev/docs/guides/local-overlay/ |
| Announcing Snix | https://snix.dev/blog/announcing-snix/ |
| Overlay Store Blog | https://snix.dev/blog/snix-as-lower-nix-overlay-store/ |
| snix-eval rustdoc | https://snix.dev/rustdoc |
| snix-eval VM module | https://snix.dev/rustdoc/snix_eval/vm/index.html |
| Attrset Opcodes | https://snix.dev/docs/components/eval/attrset-opcodes/ |
| Tvix Status Sept '22 | https://tvl.fyi/blog/tvix-status-september-22 |
| Tvix Status Feb '24 | https://tvl.fyi/blog/tvix-update-february-24 |
| Tvix Status Aug '24 | https://tvl.fyi/blog/tvix-update-august-24 |
| Replit tvix-store blog | https://blog.replit.com/tvix-store |
| devenv → Tvix | https://devenv.sh/blog/2024/10/22/devenv-is-switching-its-nix-implementation-to-tvix |
| NLnet project | https://nlnet.nl/project/Snix-Store_Builder |
| Benchmark gist (Mic92) | https://gist.github.com/Mic92/2edb7d1afa861dffd2f601f1de78cb87 |
