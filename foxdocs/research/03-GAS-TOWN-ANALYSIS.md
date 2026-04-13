# 🏭⛽🔗 GAS TOWN × SOVEREIGN MESH 🔗⛽🏭
### Анализ оркестратора Стива Йегге в контексте нашей архитектуры
### Бонусная заметка — Мост между хаосом и порядком

> 📎 **Контекст:** [00-FRACTAL-ATOM](./00-FRACTAL-ATOM.md) · [01-SYNESTHESIA-ENGINE-V3](./01-SYNESTHESIA-ENGINE-V3.md) · [02-SOVEREIGN-MESH](./02-SOVEREIGN-MESH.md)
> 📅 Дата: 2026-04-13
> 🔬 Статус: Аналитическая заметка
> 🔗 Источник: Steve Yegge, «Встречайте Gas Town» (2026-01-08)

---

## 🗺️ Содержание

```
⛽ Часть 0 — Что такое Gas Town и почему это важно                         [стр.1]
🔬 Часть I — Архитектура MEOW: от Beads к Molecules                       [стр.2]
🪞 Часть II — Зеркало: Gas Town ↔ Sovereign Mesh                          [стр.3]
🧠 Часть III — Gas Town ↔ COMPASS + MAKER                                 [стр.4]
⚡ Часть IV — Gas Town ↔ Synesthesia Engine                               [стр.5]
📊 Часть V — Где Gas Town лучше, где наша архитектура лучше               [стр.6]
🔮 Часть VI — Синтез: что взять для нашей системы                         [стр.7]
```

---

# ⛽ Часть 0 — Что такое Gas Town

## 🎯 Одна строка

> **Gas Town = оркестратор 20-30 параллельных Claude Code, связанных через Git-backed трекер задач (Beads), с ролевой моделью, сервисной сеткой агентов и молекулярным описанием рабочих процессов.**

## 🏗️ Ключевые концепции

| Концепция | Что это | Аналог в нашей архитектуре |
|---|---|---|
| 🏙️ **Town** | Штаб-квартира, корневая директория | 🏰 nn3w (NixOS monorepo) |
| 🏗️ **Rig** | Проект (git repo) под управлением GT | ⚛️ Cell (sandboxai) |
| 🧵 **Bead** | Атомарная единица работы (JSON в Git) | 🔮 CID-addressed task |
| 🧬 **Molecule** | Цепочка Beads = workflow | ⚛️ Cell с Ceramic stream |
| 🧫 **Protomolecule** | Шаблон workflow (как класс) | 🧬 Cell Spec_CID |
| 📋 **Formula** | TOML-описание workflow (компилируется в proto) | 🌿 Den Aspect |
| 🪝 **Hook** | Персональный «крючок» агента с текущей работой | 💾 State_CID |
| 🚚 **Convoy** | Единица доставляемой работы (фича/фикс) | 📋 ReadyPool entry / Ceramic stream |
| ⚡ **GUPP** | «Если работа на крючке — ДЕЛАЙ» | ♾️ Cell lifecycle (Spec_CID → execute) |
| 🔄 **NDI** | Недетерминированная идемпотентность | 🔮 Content-addressed determinism |
| 👻 **Wisp** | Эфемерный Bead (не коммитится в Git) | ⚡ Lattica ephemeral message |

## 👥 7 ролей Gas Town

| Роль GT | Что делает | Аналог в COMPASS/MAKER | Аналог в Synesthesia |
|---|---|---|---|
| 🎩 **Mayor** | Главный консьерж, UI для человека | 🧭 COMPASS Meta-Thinker | 🎬 DirectorCell |
| 😺 **Polecats** | Эфемерные workers, выполняют задачи роями | ⚔️ MAKER micro-agents | 🖌️ ActuatorCells (speculative) |
| 🏭 **Refinery** | Интеллектуальный merge queue | — | 📋 ReadyPool (pick best) |
| 🦉 **Witness** | Patrol agent, следит за workers | 👑 Supervisor | 👑 SupervisorCell |
| 🐺 **Deacon** | Daemon, пингует всех «делай работу» | GUPP heartbeat | 💓 Heartbeat system |
| 🐶 **Dogs** | Помощники Deacon, разное | — | — |
| 👷 **Crew** | Личные агенты человека, долгоживущие | Main Agent (COMPASS) | 🧠 BrainCells |

---

# 🔬 Часть I — Архитектура MEOW

## 📊 Стек MEOW (Molecular Expression of Work)

```
Level 4:  📋 FORMULA (TOML)
          Декларативное описание workflow
          Компоненты: шаги, циклы, шлюзы, переменные
          ↓ "cook" (compile)

Level 3:  🧫 PROTOMOLECULE
          Шаблон из реальных Beads
          Как класс: инстанцируется в конкретный workflow
          ↓ "instantiate" (variable substitution)

Level 2:  🧬 MOLECULE
          Цепочка связанных Beads = живой workflow
          Агент идёт по цепочке, отмечая шаг за шагом
          Переживает crashes, перезапуски, смену сессий

Level 1:  🧵 BEAD
          Атомарная задача (JSON строка в .jsonl файле)
          ID, описание, статус, исполнитель
          Живёт в Git → переживает всё

Level 0:  🐙 GIT
          Единый источник истины
          Все Beads, Molecules, состояния агентов — в Git
```

### 💡 Ключевые инсайты MEOW

**1. Работа = данные в Git**
Не внешняя БД, не SaaS-трекер. Beads = JSON строки в `.jsonl` файлах, коммитятся в Git. Это даёт:
- 🔄 Версионирование всей истории задач
- 🔀 Branching/merging работы как кода
- 🔍 Полный аудит через `git log`
- 📡 Распределённость через `git push/pull`

**2. Молекулы = workflows с гарантией завершения**
Молекула — цепочка Beads с зависимостями. Агент проходит шаг за шагом. Если агент упал:
- Молекула в Git → переживает crash
- Новый агент продолжает с текущего шага
- Результат: **NDI** — недетерминированный путь, но гарантированное завершение

**3. Формулы = декларативные workflows (как Nix для задач)**
TOML → компилируется в protomolecule → инстанцируется в molecule. Это **Nix-подобный подход**: декларативно описать workflow → детерминированно «построить» его.

**4. Wisps = эфемерные Beads**
Для оркестрации: не коммитятся в Git, живут в runtime. Аналог Lattica ephemeral messages в нашей архитектуре.

---

# 🪞 Часть II — Зеркало: Gas Town ↔ Sovereign Mesh

## 📊 Глубокий маппинг

| Паттерн | ⛽ Gas Town | 🌐 Sovereign Mesh | 💡 Инсайт |
|---|---|---|---|
| **Единица работы** | 🧵 Bead (JSON в Git) | 🔮 CID (content-addressed) | GT: location-based (файл в repo). SM: content-based (hash). **SM масштабируется лучше** |
| **Workflow** | 🧬 Molecule (цепочка Beads) | ⚛️ Cell pipeline (Ceramic stream) | GT: линейная цепочка. SM: DAG (нелинейная). **SM более гибкий** |
| **Шаблон** | 🧫 Protomolecule → instantiate | 🧬 Spec_CID → deploy | GT: JSON copy + var substitution. SM: CID-addressed, immutable. **SM = точнее** |
| **Декларация** | 📋 Formula (TOML) | 🌿 Aspect (Nix) | GT: TOML. SM: Nix. **Nix мощнее** (типы, composition, derivations) |
| **Хранилище** | 🐙 Git | 🪨 IPFS + 🌊 Ceramic | GT: централизованный Git. SM: децентрализованный P2P. **SM: sovereignty** |
| **Identity** | Agent Bead (JSON в Git) | 🆔 DID + UCAN | GT: имя в файле. SM: криптографическая идентичность. **SM: zero-trust** |
| **Heartbeat** | Deacon → GUPP nudge (tmux send-keys) | ⚡ Lattica heartbeat | GT: tmux hack. SM: P2P protocol. **SM: native** |
| **Merge** | Refinery (git merge agent) | 🌊 Ceramic CRDT | GT: Git merge conflicts. SM: CRDT auto-resolve. **SM: conflict-free** |
| **Ephemerality** | Wisps (in-memory, burned) | ⚡ Lattica ephemeral | GT: custom. SM: protocol-level. **SM: standard** |
| **Supervision** | Witness patrol | 👑 SupervisorCell | GT: periodic patrol. SM: continuous monitoring. **Comparable** |
| **Swarming** | Polecats (spawn N workers) | ♾️ cell.spawn() | GT: tmux sessions. SM: Cell lifecycle. **SM: isolated + CID-tracked** |
| **Resilience** | NDI (restart agent → continue molecule) | Content-addressed replay | GT: agent reads Git state. SM: agent reads Ceramic stream. **Equivalent** |

## 💡 Главный инсайт

> **Gas Town — это Sovereign Mesh, реализованный в Web2 с Git + tmux. Наша архитектура — то же самое, но на Web3 с IPFS + Ceramic + libp2p.**

Gas Town **доказывает**, что паттерны Sovereign Mesh **работают на практике**:
- Persistent worker identity (Bead → DID)
- Workflow-as-data (Molecule → Ceramic stream)
- Declarative templates (Formula → Aspect)
- Swarm execution (Polecats → Cell.spawn)
- Guaranteed completion (NDI → CID replay)

Йегге пришёл к тем же выводам **эмпирически**, через 4 итерации оркестратора. Мы пришли **теоретически**, через content-addressing и Cell abstraction. **Конвергенция подтверждает правильность обеих архитектур.**

---

# 🧠 Часть III — Gas Town ↔ COMPASS + MAKER

## ⚔️ MAKER в Gas Town

Йегге **прямо ссылается** на MAKER (arXiv:2511.09030). Его Polecats реализуют MAD (Maximal Agentic Decomposition):

| MAKER concept | Gas Town implementation | Наш AIOBSH design |
|---|---|---|
| **MAD** (decompose to micro-steps) | Formula → Molecule → one step per Polecat | MAD → CellSpec → one Cell per step |
| **K-Voting** | Swarm of Polecats → Refinery picks winner | K-Voting in MAKER module → ReadyPool pick_best |
| **Red-Flagging** | Witness patrol checks quality | Red-Flag filter before voting |
| **Minimal context** | Each Polecat gets one Bead + current state | Each micro-agent gets episode brief (COMPASS Context Manager) |
| **Pipeline** | Molecule: step → step → step | Ceramic stream: event → event → event |

💡 **Gas Town = MAKER на стероидах.** Йегге решил проблему Ханойской башни (20 дисков, миллион шагов) просто сгенерировав молекулу на миллион шагов и пропустив через Polecats. Это **валидация MAD** — декомпозиция до атомарных шагов + эфемерные агенты работает.

## 🧭 COMPASS в Gas Town

| COMPASS concept | Gas Town equivalent |
|---|---|
| **Meta-Thinker** (strategy) | 🎩 Mayor (talks to human, sets strategy) |
| **Context Manager** (slim briefs) | 🪝 Hook system (each agent sees only current Bead) |
| **Main Agent** (tactical) | 😺 Polecat (executes one step) |
| **Signals** (CONTINUE/REVISE/STOP) | Witness patrol → nudge / restart / escalate |
| **Episode loop** | Patrol cycle: evaluate → assign → execute → check |

💡 **Gas Town разделяет COMPASS-роли на 3 отдельных агента** (Mayor, Witness, Deacon) вместо одного мульти-модульного COMPASS. Это **более отказоустойчиво** — если один упал, другие продолжают.

---

# ⚡ Часть IV — Gas Town ↔ Synesthesia Engine

## 🖌️ Speculative Parallel Pipeline = Swarming

| Synesthesia concept | Gas Town equivalent | Что общего |
|---|---|---|
| **ActuatorCells работают параллельно** | Polecats swarm | N workers делают параллельную работу |
| **ReadyPool** (готовые результаты) | Merge Queue | Буфер результатов от workers |
| **Director picks best** | Refinery picks best merge | Куратор выбирает из готовых |
| **Hints** (warm/hot/fire) | gt sling (швыряет работу) | Приоритизация задач |
| **Speculative → cache** | Unused work → Git history | Неиспользованная работа не теряется |
| **Context broadcast** | Bead updates → all workers see Git | Все видят общий контекст |

💡 **Swarming — общий паттерн.** И Gas Town, и Synesthesia Engine пришли к одному: запусти N workers параллельно, пусть делают спекулятивно, выбирай лучшее. **Разница:** GT для кода, SE для визуализаций.

---

# 📊 Часть V — Где кто лучше

## 🟢 Gas Town лучше

| Аспект | Почему GT лучше | Урок для нас |
|---|---|---|
| 🚀 **Работает сейчас** | 4-я итерация, 75K LOC, используется автором | Наша архитектура — research. Нужен MVP |
| 🔧 **Практичность** | tmux + Git = работает на любой машине | Не нужен IPFS/Ceramic для первой версии |
| 📝 **MEOW stack** | Beads → Molecules → Formulas: элегантный стек | Нам нужен аналог Formulas для декларативных workflows |
| 🔄 **NDI** | Гарантия завершения через Git persistence | Ceramic streams дадут то же, но нужно реализовать |
| 🐛 **Chaos tolerance** | «Рыба выпадает из бочки. Придёт ещё рыба.» | Не бояться потерь; фокус на throughput |
| 👷 **Crew** | Долгоживущие личные агенты с историей | Наши Cells — ephemeral. Нужны persistent Cells для dev |

## 🟢 Наша архитектура лучше

| Аспект | Почему мы лучше | Почему GT не может это |
|---|---|---|
| 🔮 **Content-addressing** | CID = вечная идентичность, zero-trust verification | Git hash != content hash (разные семантики) |
| 🌐 **Decentralization** | IPFS + Ceramic + Lattica = no SPOF | Git = один repo = SPOF |
| 🔑 **UCAN** | Cryptographic capabilities, delegation, attenuation | GT: «just trust tmux sessions» |
| ♾️ **Fractal scaling** | Cell → Cell → Cell, бесконечная вложенность | GT: 2 уровня (Town → Rig), плоская структура |
| 📦 **WASM portability** | Cell runs anywhere: browser, IPVM, edge, cloud | GT: только tmux на одной машине (скоро federation) |
| 🌿 **Dendritic composition** | Aspects compose → infinite configurations | Formulas: менее мощная композиция |
| 🌊 **CRDT state** | Ceramic = conflict-free, multi-writer, verifiable | Git merge = конфликты, Refinery нужен |
| 🛡️ **Isolation** | bubblewrap / OCI / microVM per Cell | GT: Claude Code в tmux pane, zero isolation |
| 💰 **Economy** | IPVM: pay for compute with crypto | GT: «чертовски дорог», нужно N аккаунтов |

---

# 🔮 Часть VI — Синтез: что взять для нашей системы

## 🏆 7 паттернов из Gas Town, которые усилят Sovereign Mesh

### 1. 🧵 Bead-like атомарные единицы работы

> **Урок:** Каждая задача = один JSON-объект с ID, статусом, исполнителем. Просто и эффективно.

**Как интегрировать:** CID-addressed Bead in Ceramic:
```jsonc
{
  "bead_cid": "bafy2bz...",
  "type": "task",
  "status": "in_progress",    // open | in_progress | done | blocked
  "assignee_did": "did:key:zPolecat3",
  "parent_cid": "bafy2bz...", // molecule/epic
  "description": "Generate physics diagram for binary tree",
  "acceptance": "SVG with >5 nodes, animated entrance"
}
```

### 2. 🧬 Molecule-like workflows с гарантией завершения

> **Урок:** Цепочка задач в persistent storage. Агент падает → новый продолжает.

**Как интегрировать:** Ceramic stream of linked Beads:
```
Molecule Stream:
  Event 0: {step: "design", bead_cid: "bafy...", status: "done"}
  Event 1: {step: "implement", bead_cid: "bafy...", status: "in_progress"}
  Event 2: {step: "review", bead_cid: "bafy...", status: "open"}
  ...
```
Cell crash → new Cell reads stream → finds `in_progress` step → continues.

### 3. 🪝 Hook pattern (одна задача на агенте)

> **Урок:** У каждого агента — один «крючок» с текущей работой. Просто и надёжно.

**Как интегрировать:** Each Cell's `state_stream` includes a `current_hook` field:
```jsonc
{
  "cell_did": "did:key:zDirectorCell",
  "current_hook": {
    "molecule_stream_id": "ceramic://k2t6wz...",
    "current_step_cid": "bafy2bz..."
  }
}
```

### 4. 📋 Formula-like декларативные workflows

> **Урок:** TOML → compile → workflow. Декларативное описание сложных процессов.

**Как интегрировать:** Nix-based Formula (мощнее TOML):
```nix
# formulas/lecture-post-process.nix
{ lib, ... }: {
  steps = [
    { name = "extract-transcript"; cell = "TranscriptCell"; input = "audio_cid"; }
    { name = "extract-entities"; cell = "NERCell"; input = "transcript_cid"; depends = ["extract-transcript"]; }
    { name = "build-kg"; cell = "KGCell"; input = "entities_cid"; depends = ["extract-entities"]; }
    { name = "generate-pdf"; cell = "TypstCell"; input = "kg_cid"; depends = ["build-kg"]; }
    { name = "generate-html"; cell = "HTMLCell"; input = "kg_cid"; depends = ["build-kg"]; parallel = true; }
  ];
}
```
Nix compile → Ceramic molecule stream → Cells execute step by step.

### 5. 🐺 Deacon-like daemon heartbeat

> **Урок:** Периодический heartbeat, который «пинает» застрявших агентов.

**Как интегрировать:** DeaconCell в Synesthesia Engine:
- Каждые 30с проверяет все Cells через Lattica heartbeat
- Если Cell не ответила >60с → SupervisorCell restart
- Если Cell stuck на одном шаге >5мин → escalate / fallback

### 6. 😺 Polecat-like ephemeral swarming

> **Урок:** Эфемерные workers, запускаемые по требованию, живущие одну задачу.

**Уже реализовано:** ActuatorCells в Speculative Parallel Pipeline. Каждый ActuatorCell — это «Polecat», который работает спекулятивно и публикует в ReadyPool.

### 7. 🔄 NDI через Ceramic persistence

> **Урок:** Workflow переживает crash агента, потому что состояние в persistent storage.

**Как работает:**
1. Molecule stream в Ceramic = persistent
2. Cell crash → SupervisorCell spawn new Cell
3. New Cell reads molecule stream → finds current step → continues
4. Output = same CID regardless of which Cell instance computed it (content-addressing)

**NDI в нашей архитектуре = stronger** чем в Gas Town, потому что CID гарантирует что один и тот же input всегда даёт один и тот же output CID (deterministic). Git не даёт этой гарантии.

---

## 📊 Итоговая таблица синтеза

| GT Pattern | Наш эквивалент | Нужно реализовать? | Приоритет |
|---|---|---|---|
| Beads (task tracking) | Ceramic Beads | ✅ Да, в P2 | 🔥 Высокий |
| Molecules (workflows) | Ceramic molecule streams | ✅ Да, в P2 | 🔥 Высокий |
| Formulas (templates) | Nix formulas | ✅ Да, в P1 | 🟡 Средний |
| GUPP (hook → execute) | Cell lifecycle | ✅ Уже в дизайне | ✅ Готово |
| NDI (crash recovery) | Ceramic persistence + Cell restart | ✅ Да, в P2 | 🔥 Высокий |
| Swarming (Polecats) | Speculative Parallel Pipeline | ✅ Уже в дизайне | ✅ Готово |
| Patrols (Deacon) | DeaconCell + heartbeat | ✅ Да, в P0 | 🔥 Высокий |
| Merge Queue (Refinery) | ReadyPool pick_best | ✅ Уже в дизайне | ✅ Готово |
| Wisps (ephemeral) | Lattica ephemeral messages | ✅ Уже в дизайне | ✅ Готово |
| Convoy (deliverable unit) | Lecture CID / Artifact CID | ✅ Уже в дизайне | ✅ Готово |
| Crew (personal agents) | Persistent BrainCells | 🆕 Добавить | 🟡 Средний |
| Seance (talk to past self) | Ceramic stream history replay | ✅ Бесплатно (Ceramic) | ✅ Готово |
| tmux UI | Web UI / nixvimde integration | ❌ Другой подход | — |
| Federation | libp2p mesh (native) | ✅ Уже в дизайне | ✅ Готово |

---

## 🏛️ Финальный вердикт

> **Gas Town — это MVP Sovereign Mesh, построенный одним человеком за 17 дней на Git + tmux.**
>
> **Sovereign Mesh — это то, чем Gas Town СТАНЕТ, когда Git → IPFS, tmux → Cells, JSON → CID, централизованный → P2P.**

Gas Town доказывает:
1. ⚛️ **Cell pattern works** — persistent agents with ephemeral sessions
2. 🧬 **Molecules work** — workflow-as-data with crash recovery
3. 😺 **Swarming works** — parallel speculative execution
4. 🔄 **NDI works** — guaranteed completion through persistent state
5. 📋 **Formulas work** — declarative workflow templates

Наша архитектура делает всё это, но:
- 🔮 **Content-addressed** (not location-addressed)
- 🌐 **Decentralized** (not single-machine)
- 🔑 **Cryptographically authorized** (not tmux-trust)
- ♾️ **Fractally scalable** (not 2-level flat)
- 📦 **WASM-portable** (not tmux-locked)

**Gas Town = колесо, которое отлично крутится. Sovereign Mesh = тот же паттерн вращения, но как варп-двигатель.**

---

> 📎 **Главная серия:**
> [00-FRACTAL-ATOM](./00-FRACTAL-ATOM.md) · [01-SYNESTHESIA-ENGINE-V3](./01-SYNESTHESIA-ENGINE-V3.md) · [02-SOVEREIGN-MESH](./02-SOVEREIGN-MESH.md)
