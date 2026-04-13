# 15. Микрофронтенды и дендритный паттерн — аспект-ориентированная UI-архитектура

> Микрофронтенды (MFE) — это frontend-аналог микросервисов: разбиение
> монолитного UI на независимо разрабатываемые, деплоимые и композируемые
> модули. Это тот же паттерн, что Den (dendric) применяет к Nix-конфигурациям.
> В контексте nn3w микрофронтенды + IPFS + Module Federation = 
> content-addressed, decentralized, composable UI.

## Оглавление

1. [Микрофронтенды — суть](#1-суть)
2. [Module Federation 2.0 — runtime-композиция](#2-module-federation)
3. [Дендритный паттерн для UI](#3-dendric-ui)
4. [IPFS + MFE = content-addressed UI delivery](#4-ipfs-mfe)
5. [BIMF — bundler-independent Module Federation](#5-bimf)
6. [Архитектура для nn3w](#6-nn3w-архитектура)
7. [Библиография](#7-библиография)

---

## 1. Суть

### Что такое микрофронтенды

```
МОНОЛИТ                          МИКРОФРОНТЕНДЫ
┌──────────────────┐            ┌─────┐ ┌─────┐ ┌─────┐
│                  │            │Auth │ │Chat │ │Dash │
│    Один SPA      │     →     │ MFE │ │ MFE │ │ MFE │
│    (React App)   │            └──┬──┘ └──┬──┘ └──┬──┘
│                  │               │       │       │
└──────────────────┘            ┌──┴───────┴───────┴──┐
                                │     Host / Shell     │
                                └──────────────────────┘
```

Каждый MFE:
- **Независимо разрабатывается** (своя команда, свой репо)
- **Независимо деплоится** (свой CI/CD pipeline)
- **Runtime-композируется** (загружается в host при необходимости)
- **Свой tech stack** (React, Vue, Svelte — в одном приложении)

### Три подхода к композиции

| Подход | Описание | Пример |
|--------|----------|--------|
| **Build-time** | MFE как npm-пакет, вставляется при сборке | Lerna monorepo |
| **Server-side** | Сервер собирает HTML из фрагментов | Tailor, Podium |
| **Runtime** | MFE загружается в браузере динамически | **Module Federation**, Web Components |

Runtime-композиция — самый мощный подход и прямая аналогия
с тем, как агенты в Agentic Web динамически обнаруживают и
подключают сервисы.

---

## 2. Module Federation

### Module Federation 2.0 (2024-2026)

Module Federation — механизм в Webpack/Rspack, позволяющий
приложениям **в runtime** загружать модули из других приложений.

```
┌─────────────────────────────────────────────────┐
│                   HOST APP                       │
│                                                  │
│  import AuthModule from "auth_remote/Login"      │
│  import ChatWidget from "chat_remote/Widget"     │
│                                                  │
│  ┌───────────┐  ┌───────────┐  ┌──────────────┐ │
│  │ AuthModule│  │ ChatWidget│  │ DashboardMFE │ │
│  │ (remote)  │  │ (remote)  │  │ (remote)     │ │
│  └─────┬─────┘  └─────┬─────┘  └──────┬───────┘ │
│        │              │               │          │
└────────┼──────────────┼───────────────┼──────────┘
         │              │               │
    ┌────┴────┐   ┌─────┴────┐   ┌─────┴─────┐
    │auth.app │   │chat.app  │   │dash.app   │
    │CDN/IPFS │   │CDN/IPFS  │   │CDN/IPFS   │
    └─────────┘   └──────────┘   └───────────┘
```

### Ключевые фичи MF 2.0

| Фича | Описание |
|------|----------|
| **TypeScript sharing** | `dts: true` → автоматическая генерация типов между MFE |
| **Manifest discovery** | JSON-manifest вместо hardcoded URL → динамическое обнаружение |
| **Shared deps** | React, Router и т.д. грузятся один раз, шарятся между MFE |
| **Bundler-agnostic** | `@module-federation/enhanced` для Webpack + Rspack |
| **Vite support** | `@module-federation/vite` для Vite-проектов |

### Rspack / Rsbuild

**Rspack** — Rust-based bundler, совместимый с Webpack:
- **5-10x быстрее** Webpack 5 на сборке
- Полная совместимость с Module Federation
- **Rsbuild** — build tool поверх Rspack (аналог Vite/CRA)

```javascript
// rsbuild.config.ts (Host)
import { pluginModuleFederation } from '@module-federation/rsbuild-plugin';

export default {
  plugins: [
    pluginModuleFederation({
      name: 'host',
      remotes: {
        auth: 'auth@https://auth.example.com/mf-manifest.json',
        dashboard: 'dashboard@https://dash.example.com/mf-manifest.json',
      },
      shared: ['react', 'react-dom'],
    }),
  ],
};
```

```javascript
// rsbuild.config.ts (Auth Remote)
import { pluginModuleFederation } from '@module-federation/rsbuild-plugin';

export default {
  plugins: [
    pluginModuleFederation({
      name: 'auth',
      exposes: {
        './Login': './src/components/Login.tsx',
        './Profile': './src/components/Profile.tsx',
      },
      shared: ['react', 'react-dom'],
    }),
  ],
};
```

---

## 3. Дендритный паттерн для UI

### Den = аспект-ориентированная Nix → MFE = аспект-ориентированный UI

Прямая структурная аналогия:

```
DEN ASPECTS (Nix)              MFE ASPECTS (UI)
─────────────────              ────────────────────
aspects/                       micro-frontends/
├── bluetooth/                 ├── auth/
│   ├── nixos.nix             │   ├── Login.tsx
│   └── homeManager.nix       │   ├── Profile.tsx
├── development/               │   └── mf-manifest.json
│   ├── nixos.nix             ├── knowledge-graph/
│   ├── homeManager.nix       │   ├── GraphView.tsx
│   └── nixvim.nix            │   ├── PropositionCard.tsx
├── ssh/                       │   └── mf-manifest.json
│   ├── nixos.nix             ├── agent-dashboard/
│   └── homeManager.nix       │   ├── AgentList.tsx
│                              │   ├── TaskMonitor.tsx
│                              │   └── mf-manifest.json
│                              └── settings/
│                                  ├── SettingsPanel.tsx
│                                  └── mf-manifest.json

Host = den.hosts.laptop        Host = shell-app
Aspects = den.aspects.*        MFE = remote modules
Composition = take/canTake     Composition = Module Federation
```

### Принципы Den, применённые к MFE

| Den-принцип | MFE-аналог |
|-------------|-----------|
| **Feature-first** (не host-first) | **Domain-first** (не page-first) |
| **Аспект** объединяет все классы (nixos, hm, darwin) | **MFE** объединяет все слои (UI, state, API) |
| **canTake** — параметрическая гибкость | **shared deps** — version negotiation |
| **Аспекты composable** — take.exactly, take.atLeast | **MFE composable** — expose/consume |
| **Аспект platform-agnostic** (nixos + darwin + hm) | **MFE framework-agnostic** (React + Vue + Svelte) |
| **den.lib domain-agnostic** | **BIMF bundler-independent** |

### Dendric MFE Architecture

Объединяем Den-паттерн с MFE → **Dendric MFE**:

```
┌──────────────────────────────────────────────────────┐
│              DENDRIC MFE ARCHITECTURE                │
├──────────────────────────────────────────────────────┤
│                                                      │
│  aspects/                                            │
│  ├── auth/                   # Аспект: аутентификация│
│  │   ├── ui/                 # React components      │
│  │   ├── state/              # Zustand/Redux slice   │
│  │   ├── api/                # API client            │
│  │   ├── nix/                # Nix build derivation  │
│  │   └── manifest.json       # MF manifest           │
│  │                                                   │
│  ├── knowledge-graph/        # Аспект: граф знаний   │
│  │   ├── ui/                 # D3/Three.js viz       │
│  │   ├── state/              # GraphQL client        │
│  │   ├── api/                # ComposeDB queries     │
│  │   ├── nix/                # Nix build derivation  │
│  │   └── manifest.json       # MF manifest           │
│  │                                                   │
│  ├── agent-panel/            # Аспект: панель агентов│
│  │   ├── ui/                 # Agent monitoring      │
│  │   ├── state/              # WebSocket state       │
│  │   ├── api/                # Lattica P2P client    │
│  │   ├── nix/                # Nix build derivation  │
│  │   └── manifest.json       # MF manifest           │
│  │                                                   │
│  shells/                     # Host-приложения       │
│  ├── desktop/                # Full desktop shell    │
│  ├── mobile/                 # Mobile shell          │
│  └── agent-ui/               # AI agent interface    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

Каждый **аспект** = полноценный MFE с собственной:
- UI-частью (компоненты)
- State management
- API-клиентом
- **Nix derivation** для воспроизводимой сборки
- **Module Federation manifest** для runtime-обнаружения

---

## 4. IPFS + MFE

### Content-Addressed Module Delivery

Вместо традиционного CDN (Cloudflare, AWS):

```
ТРАДИЦИОННЫЙ                    DECENTRALIZED
CDN delivery:                   IPFS delivery:

auth.example.com/bundle.js      /ipfs/Qm...auth.../bundle.js
  → S3 bucket                     → любой IPFS-нод
  → Cloudflare edge               → P2P сеть
  → vendor lock-in                → content-verified
  → mutable (!)                   → immutable (!)
```

### Преимущества IPFS для MFE

| Аспект | Традиционный CDN | IPFS |
|--------|-------------------|------|
| Идентификация | URL (location-based) | CID (content-based) |
| Верификация | TLS (доверие CA) | Hash (криптографическая) |
| Доступность | Зависит от провайдера | P2P, censorship-resistant |
| Версионирование | Semver, mutable URLs | CID = version, immutable |
| Lock-in | AWS/GCP/Cloudflare | Нет lock-in |

### Manifest через IPFS

```json
{
  "name": "knowledge-graph",
  "version": "1.0.0",
  "cid": "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
  "exposes": {
    "./GraphView": {
      "cid": "bafybeih...graphview",
      "types": "bafybeih...types"
    },
    "./PropositionCard": {
      "cid": "bafybeih...propcard",
      "types": "bafybeih...types"
    }
  },
  "shared": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  }
}
```

Manifest сам хранится в IPFS → CID manifest = identity MFE.
**Nix** собирает MFE → output = CID → публикуется в IPFS.

### Nix + IPFS + MFE Pipeline

```
Source code (Git)
    │
    ▼
Nix derivation (deterministic build)
    │
    ▼
Content-addressed output (/nix/store/<hash>-mfe-auth)
    │
    ▼
IPFS add → CID (bafybeih...)
    │
    ▼
mf-manifest.json updated with CID
    │
    ▼
Manifest pinned to IPFS/IPNS
    │
    ▼
Host resolves manifest → loads MFE from IPFS
```

Весь пайплайн **воспроизводим и верифицируем**:
- Nix → одинаковые inputs = одинаковый output
- IPFS → один CID = один blob (immutable)
- Host → проверяет CID при загрузке (content-verified)

---

## 5. BIMF

> **"Toward Bundler-Independent Module Federations"**
> Lando & Hasselbring, Jan 2025 — [arXiv:2501.18225](https://arxiv.org/abs/2501.18225)

### Идея

BIMF (Bundler-Independent Module Federation) — модульная
федерация **без привязки к конкретному бандлеру**:

```
СЕЙЧАС:                          BIMF:
Webpack → MF plugin              Любой бандлер
Rspack → MF plugin               → стандартный протокол
Vite → MF Vite plugin            → runtime loader
                                  → manifest standard
```

### Параллель с ANP

| BIMF | ANP (Agent Network Protocol) |
|------|------------------------------|
| Manifest = описание модуля | ADP = Agent Description Protocol |
| Discovery = как найти модуль | Agent Discovery = /.well-known/ |
| Shared deps = согласование | Meta-protocol = NL-negotiation |
| Runtime loading = композиция | Agent collaboration = runtime |

**BIMF для UI = ANP для агентов**. Тот же паттерн:
описание → обнаружение → согласование → runtime-композиция.

### Проблемы и решения

| Проблема | Решение (из статьи) |
|----------|---------------------|
| Debugging across MFE | Distributed tracing |
| Performance | Server-side rendering + prefetching |
| Observability | Centralized logging + monitoring |
| Type safety | Shared type declarations |

---

## 6. Архитектура для nn3w

### Полный стек: Dendric MFE + Nix + IPFS

```
┌─────────────────────────────────────────────────────────┐
│                    nn3w UI ARCHITECTURE                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Layer 1: SHELL (Host Application)                       │
│  ├── Desktop Shell (Electron/Tauri)                      │
│  ├── Web Shell (SPA)                                     │
│  └── Agent Shell (headless, API-only)                    │
│                                                          │
│  Layer 2: DENDRIC MFE ASPECTS                            │
│  ├── auth-aspect/          → DID login, UCAN tokens      │
│  ├── knowledge-aspect/     → Meta-Graph viz, queries      │
│  ├── agent-aspect/         → Agent dashboard, monitoring  │
│  ├── editor-aspect/        → Knowledge editor, markdown   │
│  ├── search-aspect/        → Semantic search, RAG         │
│  ├── contracts-aspect/     → Knowledge Contract mgmt      │
│  └── settings-aspect/      → User preferences, keys       │
│                                                          │
│  Layer 3: SHARED INFRASTRUCTURE                          │
│  ├── @nn3w/ceramic-client  → ComposeDB GraphQL           │
│  ├── @nn3w/ipfs-client     → IPFS file operations         │
│  ├── @nn3w/lattica-client  → P2P real-time                │
│  ├── @nn3w/did-auth        → DID authentication           │
│  └── @nn3w/ucan-store      → UCAN token management        │
│                                                          │
│  Layer 4: BUILD & DEPLOY                                 │
│  ├── Nix flake             → reproducible builds          │
│  ├── IPFS publish          → content-addressed delivery   │
│  ├── IPNS update           → mutable pointers to CIDs     │
│  └── MF manifest           → runtime discovery            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Web2 ↔ Web3 Bimodality для UI

```
WEB2 MODE:                       WEB3 MODE:
─────────────                    ──────────────
MFE served from CDN              MFE served from IPFS
Manifest from API server         Manifest from IPNS
Auth via OAuth2/JWT              Auth via DID/UCAN
State in PostgreSQL              State in Ceramic/ComposeDB
Search via Elasticsearch         Search via IPLD selectors
                                 
       ↕ Transport Adapter ↕
       (тот же MFE код работает в обоих режимах)
```

### Dendric MFE as Nix Flake

```nix
# flake.nix для nn3w UI
{
  inputs.den.url = "github:vic/den";

  outputs = { den, ... }: den.lib.aspects {
    # UI aspects (MFE)
    auth = {
      ui = ./aspects/auth/ui;
      build = pkgs: pkgs.buildNpmPackage { ... };
      manifest = ./aspects/auth/mf-manifest.json;
    };

    knowledge-graph = {
      ui = ./aspects/knowledge-graph/ui;
      build = pkgs: pkgs.buildNpmPackage { ... };
      manifest = ./aspects/knowledge-graph/mf-manifest.json;
    };

    agent-panel = {
      ui = ./aspects/agent-panel/ui;
      build = pkgs: pkgs.buildNpmPackage { ... };
      manifest = ./aspects/agent-panel/mf-manifest.json;
    };
  };
}
```

### Связь с Agentic Web

Каждый MFE-аспект = потенциальный **Agent UI**:

```
Agent A (oblakagent)
  ↕ Lattica P2P
Agent B (knowledge-worker)
  ↕ Ceramic events
Knowledge Graph MFE
  → визуализирует данные от обоих агентов
  → загружается по CID из IPFS
  → host обнаруживает его через MF manifest
  → manifest = ADP (Agent Description Protocol) для UI

MFE в nn3w = UI-агент, который:
  1. Имеет CID-идентичность (content-addressed)
  2. Описывает свои capabilities (manifest)
  3. Обнаруживается runtime (Module Federation)
  4. Композируется с другими MFE (как агенты в ANP)
  5. Собирается воспроизводимо (Nix)
```

### OpenComponents как альтернатива

[OpenComponents](https://opencomponents.github.io/) — другой подход к MFE:
- **Versioned, immutable** деплои через registry
- **Language-agnostic** — consumption через HTTP
- **Semantic versioning** для safe updates
- **Registry-based** — аналогично IPFS + manifest

OpenComponents ближе к nn3w-философии:
- Immutable = content-addressed
- Registry = IPFS + discovery
- HTTP consumption = protocol-based, bundler-independent

---

## 7. Библиография

### Научные работы

| ID | Название | Авторы | Дата |
|----|----------|--------|------|
| [2501.18225](https://arxiv.org/abs/2501.18225) | Toward Bundler-Independent Module Federations (BIMF) | Lando & Hasselbring | Jan 2025 |
| [2407.15829](https://arxiv.org/abs/2407.15829) | Investigating Benefits and Limitations of Migrating to MFE | Antunes et al. | Jul 2024 |
| [2506.21297](https://arxiv.org/abs/2506.21297) | Exploring Micro Frontends: Case Study in E-Commerce | Kojo et al. | Jun 2025 |

### Инструменты и фреймворки

| Инструмент | Описание |
|-----------|----------|
| [Module Federation 2.0](https://module-federation.io/) | Runtime module sharing |
| [Rspack](https://rspack.rs/) | Rust-based Webpack-compatible bundler |
| [Rsbuild](https://rsbuild.dev/) | Build tool on top of Rspack |
| [OpenComponents](https://opencomponents.github.io/) | Registry-based MFE framework |
| [ipfs-cdn](https://github.com/vrde/ipfs-cdn) | IPFS as CDN for static assets |

### Видео и практика

| Ресурс | Описание |
|--------|----------|
| [АйТи Синяк — МФЕ базовый минимум](https://www.youtube.com/@it-sin9k) | Основы MFE |
| [АйТи Синяк — Строим первое МФЕ](https://github.com/Sin9k/host) | Rsbuild + MF2 практика |

---

> **Главный вывод**: Микрофронтенды — это **UI-проекция дендритного паттерна**.
> Den организует Nix-конфигурации по аспектам (фичам), MFE организуют UI
> по аспектам (доменам). В контексте nn3w:
>
> - **Den aspects** → infrastructure configuration
> - **MFE aspects** → user interface composition
> - **Nix** → reproducible builds для обоих
> - **IPFS** → content-addressed delivery для обоих
> - **Module Federation manifest ≈ ADP** → runtime discovery
> - **BIMF** → protocol-first, bundler-agnostic (как ANP)
>
> Это не «отдельная технология» — это **один и тот же паттерн
> (аспект-ориентированная композиция)** применённый к разным доменам.
