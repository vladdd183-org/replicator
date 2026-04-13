# 🔐 Мульти-трастовая архитектура nn3w

> **Проблема:** Один человек работает с несколькими компаниями/проектами.
> У каждого — свои приватные ресурсы, серверы, секреты.
> Компании выделяют гибкие куски серверов где можно запускать приватное.
> Часть своих вещей можно делать публичными.
> Всё это должно быть декларативно, модульно, суверенно.

---

## 🧭 Модель доменов доверия

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                        ┌──────────────┐                                │
│                        │   PUBLIC     │                                │
│                        │  open-source │                                │
│                        │   configs    │                                │
│                        └──────┬───────┘                                │
│                               │ read-only                              │
│               ┌───────────────┼───────────────┐                       │
│               │               │               │                       │
│      ┌────────▼──────┐  ┌────▼────────┐  ┌───▼─────────┐            │
│      │  COMPANY A    │  │  PERSONAL   │  │  COMPANY B  │            │
│      │  (их серверы, │  │  (мои серв, │  │  (их серв., │            │
│      │   их секреты) │  │   мои секр.)│  │   их секр.) │            │
│      └───────┬───────┘  └──────┬──────┘  └──────┬──────┘            │
│              │                 │                  │                    │
│              │    ┌────────────┼─────────────┐   │                    │
│              │    │            │             │   │                    │
│         ┌────▼────▼──┐   ┌────▼────┐   ┌───▼───▼────┐               │
│         │ EXCLAVE    │   │ MY OWN  │   │ EXCLAVE    │               │
│         │ @CompanyA  │   │ SERVERS │   │ @CompanyB  │               │
│         │            │   │         │   │            │               │
│         │ Мои прив.  │   │ Полный  │   │ Мои прив.  │               │
│         │ сервисы на │   │ контроль│   │ сервисы на │               │
│         │ их железе  │   │         │   │ их железе  │               │
│         └────────────┘   └─────────┘   └────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Матрица доверия

```
                     ┌──────────┬──────────┬──────────┬──────────┐
                     │ Personal │ CompanyA │ CompanyB │  Public  │
┌────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Personal видит:    │   ALL    │ EXCLAVE  │ EXCLAVE  │   ALL    │
│                    │          │ (мой кус)│ (мой кус)│          │
├────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ CompanyA видит:    │ ENCLAVE  │   ALL    │   ---    │   ALL    │
│                    │(мой анкл)│          │          │          │
├────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ CompanyB видит:    │ ENCLAVE  │   ---    │   ALL    │   ALL    │
│                    │(мой анкл)│          │          │          │
├────────────────────┼──────────┼──────────┼──────────┼──────────┤
│ Public видит:      │  public  │  public  │  public  │   ALL    │
│                    │  only    │  only    │  only    │          │
└────────────────────┴──────────┴──────────┴──────────┴──────────┘

ENCLAVE = вид хоста: "чужая территория внутри моего сервера"
EXCLAVE = вид пользователя: "моя территория на чужом сервере"
```

---

## 🏗️ Как это ложится на Den + Clan

### Уровень 1: Den Namespaces — разделение видимости кода

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEN NAMESPACE TOPOLOGY                                │
│                                                                         │
│  ┌─────────────────────────────────────────┐                           │
│  │  den.ful.nn3w.*                         │  ← PUBLIC NAMESPACE       │
│  │                                         │                           │
│  │  Общие аспекты, классы, batteries       │  Кто видит: ВСЕ          │
│  │  enclave-system, mesh-networking        │  Репо: nn3w-framework     │
│  │  sovereign-services, monitoring         │  (open-source)            │
│  └─────────────────────────────────────────┘                           │
│                                                                         │
│  ┌─────────────────────────────────────────┐                           │
│  │  den.ful.vlad.*                         │  ← PERSONAL NAMESPACE    │
│  │                                         │                           │
│  │  Личные аспекты: desktop, dotfiles,     │  Кто видит: только я     │
│  │  personal VPN, home configs             │  Репо: nn3w-personal      │
│  │  Exclave definitions                    │  (private)                │
│  └─────────────────────────────────────────┘                           │
│                                                                         │
│  ┌─────────────────────────────────────────┐                           │
│  │  den.ful.companyA.*                     │  ← COMPANY A NAMESPACE   │
│  │                                         │                           │
│  │  Инфра компании A: их сервисы,          │  Кто видит: я + team A   │
│  │  их хосты, их секреты                   │  Репо: companyA-infra     │
│  │  + мой enclave slot definition          │  (их private repo)        │
│  └─────────────────────────────────────────┘                           │
│                                                                         │
│  ┌─────────────────────────────────────────┐                           │
│  │  den.ful.companyB.*                     │  ← COMPANY B NAMESPACE   │
│  │                                         │                           │
│  │  Инфра компании B: их сервисы,          │  Кто видит: я + team B   │
│  │  их хосты, их секреты                   │  Репо: companyB-infra     │
│  │  + мой enclave slot definition          │  (их private repo)        │
│  └─────────────────────────────────────────┘                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Уровень 2: Den Custom Classes — Enclave/Exclave как Den forward

В vladOS-v2 анклавы реализованы как кастомный lib. В nn3w они становятся
**нативными Den forwarding классами** с guard и parametric dispatch:

```nix
-- nn3w-framework: modules/classes/enclave.nix

enclaveClass = { host }:
  { class, aspect-chain }:
  den._.forward {
    each = lib.attrValues (host.enclaves or {});

    fromClass = enclave:
      "enclave-L${toString enclave.isolationLevel}";

    intoClass = _: host.class;

    intoPath = enclave: [
      "vladOS" "enclaves" enclave.name
    ];

    fromAspect = enclave:
      den.aspects.${enclave.aspect};

    -- Активируется ТОЛЬКО если модуль анклавов импортирован
    guard = { options, ... }:
      options ? vladOS.enclaves;
  };

den.ctx.host.includes = [ enclaveClass ];
```

```nix
-- nn3w-framework: modules/classes/exclave.nix

exclaveClass = { user }:
  { class, aspect-chain }:
  den._.forward {
    each = lib.attrValues (user.exclaves or {});

    fromClass = exclave:
      "exclave-${exclave.host}";

    intoClass = _: "homeManager";

    intoPath = exclave: [
      "programs" "exclave-${exclave.name}"
    ];

    fromAspect = exclave:
      den.aspects.${exclave.aspect};
  };

den.ctx.user.includes = [ exclaveClass ];
```

### Уровень 3: Den Schema — расширение для мульти-тенантности

```nix
-- nn3w-framework: modules/schema/trust.nix

den.schema.host = { host, lib, ... }: {
  options = {
    trustDomain = lib.mkOption {
      type = lib.types.enum [ "personal" "company" "public" ];
      default = "personal";
    };

    enclaves = lib.mkOption {
      type = lib.types.attrsOf (lib.types.submodule {
        options = {
          isolation = lib.mkOption {
            type = lib.types.enum [
              "namespace" "microvm" "vm" "confidential" "sovereign"
            ];
          };
          owner = lib.mkOption { type = lib.types.str; };
          resources = lib.mkOption { type = lib.types.attrs; default = {}; };
          elastic = lib.mkOption { type = lib.types.bool; default = false; };
          deployKeys = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [];
          };
        };
      });
      default = {};
    };
  };
};

den.schema.user = { user, lib, ... }: {
  options = {
    exclaves = lib.mkOption {
      type = lib.types.attrsOf (lib.types.submodule {
        options = {
          host = lib.mkOption { type = lib.types.str; };
          isolation = lib.mkOption { type = lib.types.str; };
          trustDomain = lib.mkOption { type = lib.types.str; };
          deployTarget = lib.mkOption { type = lib.types.str; };
        };
      });
      default = {};
    };
  };
};
```

### Уровень 4: Clan — сетевая связность между доменами

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CLAN NETWORK TOPOLOGY                                 │
│                                                                         │
│  ┌───────────────────────────┐                                         │
│  │   CLAN: personal          │   Мои серверы + десктоп                 │
│  │                           │                                         │
│  │  vladOS ◄──mesh──► angron │                                         │
│  │     │               │     │                                         │
│  │     └──mesh──► perturabo  │                                         │
│  │                           │                                         │
│  │  Secrets: sops (personal) │                                         │
│  │  VPN: WireGuard mesh      │                                         │
│  └─────────────┬─────────────┘                                         │
│                │                                                        │
│                │ EXCLAVE tunnels                                        │
│                │ (per-company isolated VPN)                             │
│                │                                                        │
│  ┌─────────────▼─────────────┐  ┌──────────────────────────┐          │
│  │  COMPANY A NETWORK        │  │  COMPANY B NETWORK       │          │
│  │                           │  │                          │          │
│  │  compA-srv1 ── compA-srv2 │  │  compB-srv1 ── compB-gw │          │
│  │       │                   │  │       │                  │          │
│  │  ┌────▼────────────┐     │  │  ┌────▼────────────┐    │          │
│  │  │ MY EXCLAVE @A   │     │  │  │ MY EXCLAVE @B   │    │          │
│  │  │ (L2/L3 VM)      │     │  │  │ (L3 confid.)    │    │          │
│  │  │                 │     │  │  │                 │    │          │
│  │  │ Мои приватные   │     │  │  │ Мои приватные   │    │          │
│  │  │ сервисы. CompA  │     │  │  │ сервисы. CompB  │    │          │
│  │  │ видит только    │     │  │  │ НЕ видит ничего │    │          │
│  │  │ образ диска     │     │  │  │ (шифрование)    │    │          │
│  │  └─────────────────┘     │  │  └─────────────────┘    │          │
│  │                           │  │                          │          │
│  │  Secrets: compA sops      │  │  Secrets: compB sops     │          │
│  │  VPN: их ZeroTier/WG     │  │  VPN: их overlay          │          │
│  └───────────────────────────┘  └──────────────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Расширенная multi-repo архитектура

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  REPO: nn3w-framework (PUBLIC / open-source)                           │
│  ════════════════════════════════════════════                           │
│  Общая платформа, не привязанная ни к кому                             │
│                                                                         │
│  Экспортирует:                                                          │
│    den.ful.nn3w.enclave-system     → L0-L4, elastic, presets           │
│    den.ful.nn3w.exclave-system     → deploy, tunnel, image build       │
│    den.ful.nn3w.mesh-networking    → WireGuard/ZeroTier/Tor helpers    │
│    den.ful.nn3w.sovereign-services → self-hosted service templates     │
│    den.ful.nn3w.trust-domains      → trust schema + visibility         │
│                                                                         │
│  Классы:                                                                │
│    enclaveClass, exclaveClass, trustBoundaryClass                      │
│                                                                         │
│  Может использовать кто угодно.                                        │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  REPO: nn3w-personal (PRIVATE / encrypted)                             │
│  ═════════════════════════════════════════                              │
│  Личная инфраструктура. Только мои глаза.                              │
│                                                                         │
│  inputs: nn3w-framework, den, clan                                     │
│                                                                         │
│  den.hosts:                                                             │
│    vladOS     = { trustDomain = "personal"; ... };                     │
│    angron     = { trustDomain = "personal"; enclaves = {...}; };       │
│    perturabo  = { trustDomain = "personal"; enclaves = {...}; };       │
│                                                                         │
│  den.aspects.vladdd183 = {                                             │
│    exclaves = {                                                         │
│      dev-at-companyA = {                                               │
│        host = "compA-srv1";                                            │
│        isolation = "vm";                                               │
│        trustDomain = "companyA";                                       │
│        deployTarget = "root@compA-srv1.vpn";                           │
│      };                                                                 │
│      workspace-at-companyB = {                                         │
│        host = "compB-srv1";                                            │
│        isolation = "confidential";                                     │
│        trustDomain = "companyB";                                       │
│        deployTarget = "root@compB-srv1.onion";                         │
│      };                                                                 │
│    };                                                                   │
│  };                                                                     │
│                                                                         │
│  clan: personal fleet config                                           │
│  secrets/: sops (personal keys only)                                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  REPO: companyA-infra (COMPANY A PRIVATE)                              │
│  ════════════════════════════════════════                               │
│  Инфра компании A. Доступ: я + team A.                                 │
│                                                                         │
│  inputs: nn3w-framework, den, clan (или их собственный стек)           │
│                                                                         │
│  den.hosts:                                                             │
│    compA-srv1 = {                                                       │
│      trustDomain = "company";                                          │
│      enclaves.vladdd183-dev = {                                        │
│        isolation = "vm";                                               │
│        owner = "vladdd183";                                            │
│        resources = { cpu.cores = 4; memory = "8G"; elastic = true; };  │
│      };                                                                 │
│    };                                                                   │
│                                                                         │
│  den.aspects.companyA-services = { nixos = {...}; };                   │
│  secrets/: sops (company A keys)                                       │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  REPO: companyB-infra (COMPANY B PRIVATE)                              │
│  ════════════════════════════════════════                               │
│  Аналогично, но с бОльшей изоляцией.                                   │
│                                                                         │
│  den.hosts:                                                             │
│    compB-srv1 = {                                                       │
│      trustDomain = "company";                                          │
│      enclaves.vladdd183-workspace = {                                  │
│        isolation = "confidential";  ← L3, CompB НЕ видит содержимое   │
│        owner = "vladdd183";                                            │
│        deployKeys = [ "ssh-ed25519 AAAA..." ];                         │
│        resources = { ... };                                            │
│      };                                                                 │
│    };                                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Жизненный цикл Exclave (мой сервис на чужом железе)

```
                    nn3w-personal                    companyA-infra
                    (мой private repo)               (их private repo)

1. ДОГОВОРЁННОСТЬ
   "Мне нужно 4 CPU,     ──────────►    Создают enclave slot:
    8GB RAM, elastic"                    den.hosts.srv1.enclaves.
                                           vladdd183-dev = {
                                             isolation = "vm";
                                             resources = { ... };
                                             elastic = true;
                                         };

2. КОНФИГУРАЦИЯ
   den.aspects.vladdd183.               nixos-rebuild switch
     exclaves.dev-at-compA = {              ↓
       host = "compA-srv1";             VM slot создан,
       isolation = "vm";                ждёт деплоя
     };

3. ДЕПЛОЙ (зависит от уровня изоляции)

   L0-L2 (Declarative):
   ┌─────────────────────────────────────────────────┐
   │ compA-infra импортирует мой flake как input      │
   │ → nixos-rebuild switch включает мой конфиг      │
   │ → Хост видит мои NixOS modules                  │
   └─────────────────────────────────────────────────┘

   L3-L4 (Sovereign):
   ┌─────────────────────────────────────────────────┐
   │ Я собираю образ локально:                       │
   │   nix build .#exclave-images.dev-at-compA       │
   │                                                  │
   │ Деплою через deploy-rs/scp:                     │
   │   deploy-exclave dev-at-compA ./result/image     │
   │                                                  │
   │ Хост НЕ видит содержимое (LUKS2 + vTPM)        │
   └─────────────────────────────────────────────────┘

4. NETWORKING
   ┌──────────────┐     WireGuard tunnel     ┌──────────────┐
   │   vladOS     │◄────────────────────────►│  Exclave     │
   │  (мой десктоп)│     (point-to-point)     │  @compA      │
   └──────────────┘                          └──────────────┘
   IP: 10.0.0.1                              IP: 10.250.X.2

   CompA видит: VM существует, потребляет ресурсы
   CompA НЕ видит: что внутри VM (L3+), мой VPN трафик
```

---

## 🧩 Аспекты с разной видимостью

Ключевое преимущество Den для этой модели — **один аспект может содержать части с разной видимостью**, и это работает через namespace + parametric dispatch:

```nix
-- nn3w-framework (PUBLIC): общий аспект мониторинга
den.ful.nn3w.monitoring = {
  nixos = { pkgs, ... }: {
    services.prometheus.exporters.node.enable = true;
  };
  homeManager = { ... }: {
    programs.grafana-agent.enable = true;
  };
};

-- nn3w-personal (PRIVATE): мой личный overlay поверх
den.aspects.monitoring-personal = {
  includes = [ den.ful.nn3w.monitoring ];
  nixos = { ... }: {
    services.prometheus.exporters.node.extraFlags = [
      "--collector.wifi"  -- только на моём десктопе
    ];
  };
};

-- companyA-infra (COMPANY): их overlay
den.aspects.monitoring-compA = {
  includes = [ den.ful.nn3w.monitoring ];
  nixos = { ... }: {
    services.prometheus.remoteWrite = [{
      url = "https://compA-prometheus.internal/api/v1/write";
    }];
  };
};
```

**Каждый домен видит только свой репо + public framework.** Нет утечки между компаниями.

---

## 🔒 Секреты: мульти-уровневая sops модель

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SECRETS TOPOLOGY                                     │
│                                                                         │
│  nn3w-personal/secrets/                                                │
│  ├── hosts/                                                             │
│  │   ├── vladOS.yaml          ← AGE key: vladOS host key              │
│  │   ├── angron.yaml          ← AGE key: angron host key              │
│  │   └── perturabo.yaml       ← AGE key: perturabo host key           │
│  ├── users/                                                             │
│  │   └── vladdd183.yaml       ← AGE key: personal user key            │
│  ├── exclaves/                                                          │
│  │   ├── dev-at-compA.yaml    ← AGE key: exclave-specific key         │
│  │   │                           (НЕ company key! Только мой)          │
│  │   └── ws-at-compB.yaml     ← AGE key: exclave-specific key         │
│  └── .sops.yaml               ← creation rules по path                │
│                                                                         │
│  companyA-infra/secrets/                                               │
│  ├── hosts/                                                             │
│  │   └── compA-srv1.yaml      ← AGE key: compA host key               │
│  ├── services/                                                          │
│  │   └── compA-db.yaml        ← AGE key: compA team keys              │
│  └── .sops.yaml                                                        │
│                                                                         │
│  ПРАВИЛО: Exclave-секреты НИКОГДА не шифруются ключами компании.       │
│  Они шифруются ТОЛЬКО ключом exclave-VM (который внутри LUKS).         │
│  Компания физически не может прочитать exclave-секреты.                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Полная модель: что где живёт

```
┌────────────────┬────────────────┬─────────────┬────────────────┬──────────┐
│                │ nn3w-framework │ nn3w-personal│ companyX-infra │  exclave │
│                │   (public)     │  (private)   │ (company priv.)│ (in-VM)  │
├────────────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ Den classes    │      ✅        │      ─      │      ─         │    ─     │
│ Den schema ext │      ✅        │      ─      │      ─         │    ─     │
│ Generic aspects│      ✅        │      ─      │      ─         │    ─     │
├────────────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ My hosts       │      ─        │      ✅      │      ─         │    ─     │
│ My users       │      ─        │      ✅      │      ─         │    ─     │
│ My exclave defs│      ─        │      ✅      │      ─         │    ─     │
│ My secrets     │      ─        │      ✅      │      ─         │    ─     │
│ My Clan fleet  │      ─        │      ✅      │      ─         │    ─     │
│ My dotfiles    │      ─        │      ✅      │      ─         │    ─     │
├────────────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ Co. hosts      │      ─        │      ─      │      ✅         │    ─     │
│ Co. services   │      ─        │      ─      │      ✅         │    ─     │
│ Co. secrets    │      ─        │      ─      │      ✅         │    ─     │
│ Enclave slot   │      ─        │      ─      │      ✅         │    ─     │
├────────────────┼────────────────┼─────────────┼────────────────┼──────────┤
│ Exclave OS     │      ─        │  builds ──────────────────────► runs   │
│ Exclave secrets│      ─        │  encrypts ─────────────────────► decr. │
│ Exclave tunnel │      ─        │  initiates ────────────────────► term. │
└────────────────┴────────────────┴─────────────┴────────────────┴──────────┘
```

---

## 💡 Сценарии использования

### Сценарий 1: Работаю на компанию A — нужна dev-среда

```
1. CompanyA создаёт enclave slot (L2 VM, elastic, 4CPU/8GB)
2. Я описываю exclave в nn3w-personal
3. Собираю image: nix build .#exclave-images.dev-at-compA
4. Деплою через VPN: deploy-exclave dev-at-compA
5. Подключаюсь через WireGuard tunnel напрямую с vladOS
6. Внутри VM: мой NixOS, мои инструменты, мои секреты
7. CompA видит: VM потребляет ресурсы
8. CompA НЕ видит: что внутри VM
```

### Сценарий 2: Делаю публичный open-source сервис

```
1. Описываю аспект в nn3w-framework (public repo)
2. Любой может использовать: includes = [ den.ful.nn3w.my-service ]
3. Деплою на своём сервере через Clan
4. Другие могут деплоить на своих через тот же аспект
```

### Сценарий 3: Компания B хочет максимальную изоляцию

```
1. CompB создаёт enclave slot (L3 Confidential, LUKS2 + vTPM)
2. Slot имеет deployKeys (мой SSH pubkey)
3. Я собираю encrypted image
4. Деплою через Tor hidden service
5. CompB физически НЕ МОЖЕТ прочитать содержимое (LUKS2)
6. Даже RAM зашифрована (L4 = AMD SEV-SNP)
```

### Сценарий 4: Нужно расшарить аспект между компаниями

```
1. Создаю аспект в nn3w-framework (public)
2. CompA и CompB обе могут: includes = [ den.ful.nn3w.shared-aspect ]
3. Каждая компания добавляет свой overlay поверх
4. Нет утечки между CompA и CompB
```

---

## ⚡ Ключевые архитектурные принципы

1. **Код разделён по доменам доверия** — каждый домен = отдельный repo + Den namespace
2. **Общее = public framework** — enclave/exclave классы, generic аспекты
3. **Приватное = отдельный repo** — secrets, host configs, exclave definitions
4. **Компания не видит exclave содержимое** — L3+ шифрование обеспечивает это аппаратно
5. **Exclave-секреты шифруются только моим ключом** — никогда ключами компании
6. **Сеть через VPN tunnels** — каждый exclave имеет point-to-point WireGuard к моей сети
7. **Elastic ресурсы** — exclave может burst-ить используя свободные ресурсы хоста
8. **Декларативность всего** — и хост-side (slot), и user-side (exclave) описаны в Nix
9. **Den parametric dispatch** — аспекты автоматически применяются к правильному контексту
10. **Clan для fleet** — мои личные серверы в одном Clan, exclaves подключены через tunnels
