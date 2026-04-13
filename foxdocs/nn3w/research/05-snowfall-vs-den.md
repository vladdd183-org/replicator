# ❄️ vs 🌿 Snowfall Lib vs Den — Финальный вердикт

> **Вопрос:** Можно ли полностью заменить Snowfall на Den, или Snowfall всё ещё даёт что-то уникальное?
> **Контекст:** vladOS-v2 построен на Snowfall Lib. Планируется nn3w на новом стеке.

---

## 📋 Сравнительная таблица

| Критерий | Snowfall Lib v3 | Den v0.12.0 | Победитель |
|:---|:---|:---|:---:|
| **Организация** | По папкам (convention) | По аспектам (feature-first) | 🌿 Den |
| **Автозагрузка** | Да, по структуре папок | Через flake-parts modules | ≈ Ничья |
| **Multi-platform** | NixOS + Darwin + HM | NixOS + Darwin + HM + hjem + maid + WSL + custom | 🌿 Den |
| **Модульность** | flake-utils-plus (НЕ flake-parts) | flake-parts (де-факто стандарт) | 🌿 Den |
| **Кросс-flake шаринг** | Нет нативного | Namespaces, Dendrix, Denful | 🌿 Den |
| **Кастомные классы** | Нет | `den.provides.forward` + guard | 🌿 Den |
| **Контекстный dispatch** | Нет | `den.ctx` — параметрический | 🌿 Den |
| **Порог входа** | Низкий (кинул файл — работает) | Выше (нужно понять аспекты, ctx) | ❄️ Snowfall |
| **Boilerplate** | Минимальный | Минимальный (с v0.12.0 parametric by default) | ≈ Ничья |
| **Документация** | Хорошая, стабильная | Активно развивается, docs в репо | ≈ Ничья |
| **Зрелость** | 3+ года, v3, стабильный | <1 года в текущем виде, быстрые релизы | ❄️ Snowfall |
| **Сообщество** | ~611 ⭐, широкое | ~171 ⭐, но растёт быстро | ❄️ Snowfall |
| **Без flakes** | Нет | Да (noflake template, npins) | 🌿 Den |
| **Библиотечный режим** | Нет | `den.lib` — для любого Nix-домена | 🌿 Den |
| **Breaking changes** | v2→v3 были болезненными | Частые, но документированные | ≈ Ничья |

---

## 🔍 Что Snowfall даёт уникально

### 1. Zero-config автозагрузка по папкам

```
systems/x86_64-linux/laptop/default.nix  → nixosConfigurations.laptop
homes/x86_64-linux/user@laptop/default.nix → homeConfigurations."user@laptop"
packages/my-app/default.nix → packages.x86_64-linux.my-app
modules/nixos/my-module/default.nix → применяется ко всем NixOS хостам
overlays/my-overlay/default.nix → применяется ко всем
```

Кинул файл в папку — всё работает. Без импортов, без деклараций.

### 2. Автоматический merge библиотек

```nix
-- Snowfall автоматически мержит lib из всех inputs:
lib.flake-utils-plus.mkApp  -- доступно
lib.home-manager.mkHome     -- доступно
lib.vladOS.myHelper         -- доступно (из lib/)
```

### 3. Стабильность и предсказуемость

Snowfall работает уже 3+ года. Шаблон известен, проблемы задокументированы, community большое.

---

## 🔍 Что Den даёт уникально (и Snowfall НЕ может)

### 1. Аспект-ориентированная организация

```
Snowfall:                              Den:
─────────                              ────
modules/nixos/bluetooth.nix            den.aspects.bluetooth = {
modules/home/bluetooth.nix               nixos = { hardware.bluetooth... };
  ← два файла для одной фичи             homeManager = { services.blueman... };
  ← нужно синхронизировать               includes = [ den.aspects.audio ];
                                        };
                                         ← один аспект = одна фича, все классы
```

### 2. Параметрический dispatch без mkIf

```
Snowfall:                              Den:
─────────                              ────
mkIf config.services.x.enable {        ({ host, user, ... }: {
  ...                                    ...
}                                      })
  ← ручные условия везде                ← автоматически пропускается
                                          если контекста нет
```

### 3. Кастомные forwarding классы

В Snowfall невозможно создать класс `enclave` который автоматически forward-ится в правильный backend (systemd-nspawn, microvm, QEMU). В Den — это core feature.

### 4. Кросс-flake аспекты

```nix
-- Flake A (vladOS-framework):
den.ful.vladOS.enclave-system = { ... };

-- Flake B (company-infra):
den.aspects.prod-server.includes = [
  den.ful.vladOS.enclave-system
];
```

В Snowfall для этого нужны костыли с overlays и модулями.

### 5. den.lib для не-OS доменов

Den может управлять Terranix, NixVim, system-manager, и любым другим Nix module system. Snowfall только OS-конфигурации.

---

## 🎯 Проблемы Snowfall которые Den решает

| Проблема Snowfall | Как решает Den |
|:---|:---|
| Жёсткая структура папок — нельзя организовать иначе | Свободная организация, аспекты — это attrsets |
| External overlay packages не работают (#61) | flake-parts экосистема, нет этой проблемы |
| HM standalone rebuild без system rebuild (#138) | Отдельные `den.homes` с `intoPath` |
| v2→v3 миграция болезненная (namespace, HM, overlays) | Breaking changes документированы, есть migration guides |
| Не совместим с flake-parts | Den на flake-parts (или без него) |
| Нет шаринга модулей между репо | Namespaces |

---

## 📊 Диаграмма: Миграция vladOS-v2 → nn3w

```
vladOS-v2 (Snowfall)                    nn3w (Den)
──────────────────                      ──────────

systems/x86_64-linux/                   den.hosts.x86_64-linux.
  vladOS/                     ──────►     vladOS.users.vladdd183 = {};
  angron-node0/               ──────►     angron.users.kubeadmin = {};
  perturabo-gpu4gb-node0/     ──────►     perturabo.users.kubeadmin = {};

homes/x86_64-linux/                     den.homes.x86_64-linux.
  vladdd183@vladOS/           ──────►     vladdd183 = {};

modules/nixos/suites/                   den.aspects.
  common.nix                  ──────►     common = { os = {...}; };
  desktop.nix                 ──────►     desktop = { nixos = {...}; homeManager = {...}; };
  development.nix             ──────►     development = { includes = [...]; };
  server.nix                  ──────►     server = { nixos = {...}; };

modules/nixos/services/                 den.aspects.
  docker.nix                  ──────►     docker = { nixos = {...}; };
  k3s.nix                    ──────►     k3s = { nixos = {...}; };
  wireguard.nix              ──────►     wireguard = { os = {...}; };

modules/nixos/enclaves/                 Custom Den class:
  default.nix                ──────►     enclaveClass = { host }: ...
  security/                  ──────►     den.aspects.*.enclave-L3 = {...};
  network/                   ──────►     den.aspects.*.enclave-net = {...};

lib/profiles/                           den.aspects + includes:
  desktop/developer          ──────►     den.aspects.developer.includes = [
                                           den.aspects.workstation
                                           den.aspects.dev-tools
                                         ];
  server/k3s-agent           ──────►     den.aspects.k3s-agent.includes = [
                                           den.aspects.server-base
                                           den.aspects.k3s
                                         ];

lib/enclave/                            den.lib (custom domain):
  flake-import.nix           ──────►     den.ctx.enclave-host pipeline
  mkExternalEnclave          ──────►     Den forward class + guard
  mkEnclaveSlot              ──────►     Den forward class + guard (L3+)
```

---

## 🏆 Финальный вердикт

### Snowfall всё ещё полезен для:

1. **Быстрого старта** — если нужна конфигурация за 15 минут без изучения аспектов
2. **Простых сетапов** — один десктоп, один юзер, мало кастомизации
3. **Стабильности** — проверен годами, меньше edge cases

### Snowfall НЕ нужен в nn3w потому что:

1. **Den покрывает 100% функциональности Snowfall** и добавляет:
   - Кастомные классы (критично для анклавов)
   - Параметрический dispatch (критично для multi-host)
   - Кросс-flake шаринг (критично для 3-repo архитектуры)
   - den.lib для не-OS доменов (критично для web3/Terranix/etc.)
2. **Snowfall не совместим с flake-parts** — а flake-parts это фундамент Den, std, и всей новой экосистемы
3. **Разделение на 3 репо** — в Snowfall потребует костылей, в Den это native через namespaces
4. **Система анклавов** — невозможна в Snowfall без огромного количества кастомного кода, в Den это несколько `forward` классов

### Решение: 🌿 **Den заменяет Snowfall полностью для nn3w**

Snowfall остаётся хорошим фреймворком для простых конфигов. Но для суверенной, децентрализованной, multi-repo инфраструктуры — Den объективно превосходит по всем критическим параметрам.
