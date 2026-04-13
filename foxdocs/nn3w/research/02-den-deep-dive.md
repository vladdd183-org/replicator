# 🌿 Den — Аспект-ориентированные дендритные Nix-конфигурации

> **Версия:** v0.12.0 (13 марта 2026) | **Автор:** vic (Victor Borja)
> **Репо:** github:vic/den | **Доки:** den.oeiuwq.com
> **Зависимость:** flake-aspects v0.7.0 → flake-parts (опционально)
> **Лицензия:** Apache-2.0

---

## 🧬 Архитектура Den

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DEN FRAMEWORK                                 │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      den.lib (domain-agnostic)                   │  │
│  │                                                                  │  │
│  │  parametric ─── canTake ─── take.exactly ─── take.atLeast       │  │
│  │  statics ────── owned ───── isFn ─────────── __findFile         │  │
│  │  aspects.resolve ──────── aspects.merge ──── aspects.types      │  │
│  │                                                                  │  │
│  │  ⚡ Может использоваться для ЛЮБОГО Nix-домена:                 │  │
│  │     Terranix, NixVim, system-manager, cloud infra и т.д.       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ▲                                         │
│                              │ extends                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               den modules/ (OS-specific framework)               │  │
│  │                                                                  │  │
│  │  den.schema ──── den.hosts ──── den.homes                       │  │
│  │  den.ctx ─────── den.aspects ── den.provides (batteries)        │  │
│  │  config.nix ──── output generation                              │  │
│  │                                                                  │  │
│  │  Поддерживает: NixOS, nix-Darwin, Home-Manager, hjem, nix-maid │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Ключевые концепции

### 1. Аспекты (Aspects) — фича-first организация

Вместо организации по хостам (laptop.nix, server.nix) — организация по фичам:

```
┌─────────────────────────────────────┐
│        den.aspects.bluetooth        │
├─────────────────────────────────────┤
│  nixos:                             │
│    hardware.bluetooth.enable = true │
│                                     │
│  homeManager:                       │
│    services.blueman-applet = true   │
│                                     │
│  darwin:                            │
│    (не применимо — пропускается)    │
│                                     │
│  includes: [ den.aspects.audio ]    │
├─────────────────────────────────────┤
│  Автоматически применяется к:       │
│  laptop ✅  desktop ✅  server ❌   │
│  (через includes хоста/юзера)       │
└─────────────────────────────────────┘
```

**Аспект** — атомарная единица конфигурации, содержащая:
- Конфигурации по классам (`nixos`, `darwin`, `homeManager`, `user`, кастомные)
- Зависимости (`includes` — DAG, `provides` — дерево)
- Контекстно-зависимую логику (параметрический dispatch)

### 2. Контекстный пайплайн (Context Pipeline)

```
den.schema                    den.ctx                        Outputs
────────────                  ───────                        ───────

den.hosts.                    ctx.host                       nixosConfigurations.
  x86_64-linux.               { host }                        laptop
    laptop ──────────────────►  │                              │
      .users.                   │ enumerate users              │
        alice ─────────────►    ▼                              │
                              ctx.user                         │
                               { host, user }                  │
                                │                              │
                                │ check: user.classes          │
                                │ has "homeManager"?           │
                                ▼                              │
                              ctx.hm-user                      │
                               { host, user }                  │
                                │                              │
                                │ resolve aspects              │
                                │ collect classes               │
                                ▼                              │
                              lib.nixosSystem ────────────────►┘
                                { modules = [ resolved ] }
```

**Ключевой принцип: Parse, don't Validate**
- `ctx.host { host }` и `ctx.hm-host { host }` — одна структура, но разная семантика
- `ctx.hm-host` гарантирует: у хоста есть HM-юзеры + inputs.home-manager существует
- Невозможно получить `hm-host` если условия не выполнены

### 3. Параметрический dispatch

```nix
-- Запускается в ЛЮБОМ контексте
{ nixos.networking.firewall.enable = true; }

-- Только когда есть {host}
({ host, ... }: { nixos.networking.hostName = host.hostName; })

-- Только когда есть {host, user}
({ host, user, ... }: {
  nixos.users.users.${user.userName}.extraGroups = [ "wheel" ];
})
```

Den интроспектирует аргументы функций при evaluation time. Функция с `{ host, user }` молча пропускается в контексте только `{ host }`. **Без mkIf, без enable — форма контекста и есть условие.**

### 4. Кастомные классы (Custom Classes)

Механизм `den.provides.forward` — как Den реализует homeManager, hjem, user, WSL:

```
┌─────────────────────────────────────────────────────────┐
│  den.provides.forward {                                 │
│                                                         │
│    each       = (что итерировать)                       │
│    fromClass  = (из какого класса брать конфиг)         │
│    intoClass  = (в какой класс форвардить)              │
│    intoPath   = (по какому пути вложить)                │
│    fromAspect = (из какого аспекта)                     │
│    guard      = (условие активации — опционально)       │
│    adaptArgs  = (трансформация module args — опцион.)   │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
```

**Примеры уже встроенных классов:**
- `user` → forwards в `nixos.users.users.<userName>`
- `os` → forwards в `nixos` И `darwin` одновременно
- `homeManager` → forwards в `home-manager.users.<userName>`
- `hjem`, `maid` — аналогично для альтернативных home-env

**Примеры пользовательских классов:**
- `persist` → forwards в `environment.persistance` (Impermanence) с guard
- `container` → forwards в `virtualisation.oci-containers.containers`
- `role` → role-based конфигурация (host.roles ∩ user.roles)
- `git` → forwards в `homeManager.programs.git`

---

## 📦 Batteries (встроенные аспекты-помощники)

| Battery | Назначение |
|:---|:---|
| `den.provides.hostname` | Автоматический `hostName` из имени хоста в schema |
| `den.provides.primary-user` | Первый юзер хоста → wheel, networkmanager и т.д. |
| `den.provides.user-shell` | Параметрический: `(den.provides.user-shell "fish")` |
| `den.provides.forward` | Создание кастомных forwarding классов |
| `den.provides.mutual-provider` | Взаимная конфигурация host ↔ user |
| `den._.home-manager` | Интеграция Home-Manager (через user.classes) |
| `den._.hjem` | Интеграция hjem |
| `den._.maid` | Интеграция nix-maid |

---

## 🏷️ Namespaces — кросс-flake шаринг аспектов

```
# Flake A экспортирует аспекты под неймспейсом
den.ful.mylib.dev-tools = {
  nixos = { pkgs, ... }: { environment.systemPackages = [ pkgs.git ]; };
};

# Flake B импортирует и использует
den.aspects.my-workstation.includes = [
  den.ful.mylib.dev-tools
];
```

**v0.12.0**: Фикс шаринга параметрических аспектов между flakes — критически важно для Denful/Dendrix.

---

## 🔄 Эволюция релизов

| Версия | Дата | Ключевое |
|:---:|:---:|:---|
| **v0.9.0** | 20 фев 2026 | `den.ctx` — декларативные контекстные типы, forward classes |
| **v0.10.0** | 24 фев 2026 | `user` класс, multi-home (hjem+maid+HM), guarded forwards, WSL |
| **v0.11.0** | 06 мар 2026 | `den.lib` как standalone библиотека, `os` класс, nh apps |
| **v0.12.0** | 13 мар 2026 | Все аспекты parametric по умолчанию, namespaces для ctx/schema, перф x1.52, MicroVM template |

---

## 🎯 Почему Den для nn3w

### Den как библиотека для не-OS доменов

```nix
-- Использование den.lib для cloud/web3 инфраструктуры
den.aspects.ipfs-node = den.lib.parametric {
  terranix.resource.aws_instance.ipfs = { ami = "..."; };
  includes = [
    ({ env, ... }: { terranix.resource.aws_instance.ipfs.tags.Env = env; })
  ];
};

aspect = den.aspects.ipfs-node { env = "production"; };
module = den.lib.aspects.resolve "terranix" [] aspect;
```

### Кастомные классы для анклавов vladOS

```nix
enclaveClass = { host, user }:
  { class, aspect-chain }:
  den._.forward {
    each = host.enclaves or [];
    fromClass = enclave: "enclave-L${toString enclave.level}";
    intoClass = _: host.class;
    fromAspect = enclave: den.aspects.${enclave.aspect};
    guard = { options, ... }: options ? vladOS.enclaves;
  };

den.ctx.user.includes = [ enclaveClass ];
```

### Шаблоны (Templates)

| Шаблон | Описание |
|:---|:---|
| `default` | +flake-file +flake-parts +home-manager |
| `minimal` | +flakes -flake-parts -home-manager |
| `noflake` | -flakes +npins +lib.evalModules +nix-maid |
| `microvm` | MicroVM runnable-pkg + guests, custom ctx-pipeline |
| `example` | Cross-platform (NixOS + Darwin) |

---

## 🌐 Сообщество

- **Matrix:** #den-lib:matrix.org
- **Zulip:** oeiuwq.zulipchat.com
- **Tangled:** tangled.org/oeiuwq.com/den (децентрализованный mirror!)
- **GitHub Discussions:** vic/den/discussions
- **14 контрибьюторов**, растёт
