# 🎯 Итоговое видение: Nix CI/CD архитектура

> Консолидированное видение на основе исследований 01–12.
> Финальные решения, компоновка, слои абстракции.

---

## 📐 Общая архитектура — 5 вариантов раннеров

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Nix CI/CD Platform                                  │
│                                                                             │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────────────────────────┐ │
│  │  Вариант A    │ │  Вариант B    │ │  Вариант C                       │ │
│  │  GitHub       │ │  Self-hosted  │ │  Self-hosted + Firecracker       │ │
│  │  Hosted       │ │  NixOS        │ │  microVMs (KVM-изоляция per-job) │ │
│  │  Runner       │ │  Runner       │ │                                  │ │
│  │  Бесплатно    │ │  Persistent   │ │  Изоляция + (гибрид B+C)        │ │
│  │  Zero infra   │ │  /nix/store   │ │  для trusted/untrusted          │ │
│  └───────────────┘ └───────────────┘ └───────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │   ⭐ Вариант E: nspawn + snix overlay-store (рекомендуемый для CI)    ││
│  │                                                                         ││
│  │   systemd-nspawn контейнеры с OverlayFS /nix/store:                    ││
│  │     lower 1: host /nix/store (системные пакеты, read-only)             ││
│  │     lower 2: /srv/snix-store (snix FUSE castore, dedup, read-only)     ││
│  │     upper:   per-runner writable layer (ephemeral или persistent)       ││
│  │                                                                         ││
│  │   + post-build-hook → nix copy в snix castore                          ││
│  │   + nativная производительность overlay (без virtiofs bottleneck)       ││
│  │   + <2s рестарт контейнера, machinectl shell для дебага                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │       🧱 Вариант D: Snix Platform Layer (наслаивается под B, C, E)    ││
│  │                                                                         ││
│  │  ┌─────────────────────────────────────────────────────────────────┐    ││
│  │  │  snix store daemon (shared castore для ВСЕХ раннеров/проектов)  │    ││
│  │  │  gRPC API · content-addressed · BLAKE3 Merkle DAG              │    ││
│  │  └────────┬──────────┬──────────────────┬─────────────────────────┘    ││
│  │           │          │                  │                               ││
│  │     FUSE mount  overlay-store     nar-bridge HTTP                      ││
│  │     (прямой     (snix=lower,      (binary cache                        ││
│  │      доступ)     nix=upper)        для удалённых)                      ││
│  │                                                                         ││
│  │  🧪 Экспериментально: snix-eval (bytecode VM) + snix-build (OCI/gRPC) ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                  🔧 Общий Nix-стек (для всех вариантов)                ││
│  │                                                                         ││
│  │  flake-parts · nix2container · uv2nix/bun2nix · Attic · git-hooks.nix  ││
│  │  queued-build-hook · treefmt · nix-output-monitor                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Вариант A: GitHub Hosted Runner (бесплатный)

> Нулевая инфраструктура. Для open-source, маленьких команд, быстрого старта.

### Стек

| Компонент | Инструмент | Обоснование |
|-----------|-----------|-------------|
| Установка Nix | DeterminateSystems/nix-installer-action | Flakes из коробки, ~30s, open-source |
| Кеш | DeterminateSystems/magic-nix-cache-action | GitHub Actions Cache (10 GB, бесплатно) |
| Публичные кеши | cache.nixos.org + nix-community.cachix.org | Готовые бинарники nixpkgs |
| OCI сборка | nix2container | Инкрементальные push, контроль слоёв |
| Push | skopeo (из push-tools) | Branch tag + SHA tag + :latest |

### Дополнительные публичные кеши

```nix
nixConfig = {
  extra-substituters = [
    "https://cache.nixos.org"
    "https://nix-community.cachix.org"
    "https://numtide.cachix.org"
    "https://devenv.cachix.org"
  ];
  extra-trusted-public-keys = [
    "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
    "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
    "numtide.cachix.org-1:2ps1kLBUWjiaIc8dDaIHLPTJBtQ+vA0hERKcc8BOVZY="
    "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
  ];
};
```

### Когда использовать
- Open-source проекты
- Solo / 1–5 человек
- CI время 3–5 мин приемлемо
- Нет бюджета на серверы
- Store ≤ 10 GB

---

## 🗂️ Вариант B: Self-hosted NixOS Runner

> Персистентный /nix/store. Повторные сборки — секунды.

### Стек

| Компонент | Инструмент | Обоснование |
|-----------|-----------|-------------|
| NixOS модуль | srvos (nix-community) | GitHub App auth, изоляция, масштабирование |
| Runners | services.github-runners (nixpkgs) | Стандартный NixOS модуль, полная кастомизация |
| Кеш-сервер | Attic (приватный) | Multi-tenancy, S3 backend, fine-grained ACL |
| Post-build | queued-build-hook | Async push в Attic, не блокирует сборки |
| Публичные кеши | cache.nixos.org + nix-community | Бинарники для nixpkgs |
| OCI сборка | nix2container | Трёхслойная архитектура |

### Конфигурация runner (через стандартный NixOS)

```nix
{ config, ... }: {
  services.github-runners.ci-runner = {
    enable = true;
    url = "https://github.com/MY-ORG";
    name = "nix-builder-1";
    ephemeral = false;                         # persistent runner
    tokenFile = config.age.secrets.gh-token.path;
    replace = true;
    noDefaultLabels = false;
    extraLabels = [ "nix" "nixos" "self-hosted" ];
    extraPackages = with config.nixpkgs; [
      bash git nix-output-monitor
    ];
    extraEnvironment = {
      NIX_CONFIG = "max-jobs = auto\ncores = 0";
    };
    nodeRuntimes = [ "node20" ];
    serviceOverrides = {
      ProtectHome = false;
    };
  };
}
```

Для `srvos` — дополнительно:
```nix
{ inputs, ... }: {
  imports = [ inputs.srvos.nixosModules.github-actions-runner ];

  roles.github-actions-runner = {
    url = "https://github.com/MY-ORG";
    count = 4;
    name = "nix-builder";
    githubApp = {
      id = "12345";
      login = "MY-ORG";
      privateKeyFile = config.age.secrets.github-runner-key.path;
    };
  };
}
```

### Хуки на сервере

```nix
{
  imports = [ inputs.queued-build-hook.nixosModules.default ];

  services.queued-build-hook = {
    enable = true;
    postBuildScriptContent = ''
      set -eu
      set -f
      export IFS=' '
      exec nix copy --to "http://cache.internal:8080/main" $OUT_PATHS
    '';
  };

  nix.settings = {
    secret-key-files = [ "/etc/nix/cache-priv-key.pem" ];
    auto-optimise-store = true;
    min-free = 5368709120;   # 5 GB — GC если меньше
    max-jobs = "auto";
    cores = 0;
    max-substitution-jobs = 32;
  };
}
```

### Когда использовать
- Приватные проекты, доверенный код
- Скорость <1 мин для повторных сборок
- Большие зависимости (ML, data science)
- Частые push (>50/день)
- Уже есть серверная инфраструктура

---

## 🗂️ Вариант C: Self-hosted + Firecracker microVMs

> KVM-изоляция каждой job. Эфемерные VM. Максимальная безопасность.

### Что даёт Firecracker

| Параметр | Значение |
|----------|----------|
| Boot time | < 125 мс (Firecracker) → ~1.1 сек end-to-end |
| Snapshot restore | ~176 мс (end-to-end) |
| Memory overhead | < 5 MiB на VM |
| Изоляция | KVM (аппаратная) + Jailer (chroot/cgroups/seccomp) |
| Плотность | до 150 VM/сек на хост |
| Зрелость | Продакшн (AWS Lambda, Fargate, 33K stars) |

### nixos-fireactions — 4-уровневая архитектура

```
Layer 4: Profiles          ─ размеры VM (small/medium/large), окружения (prod/dev)
Layer 3: Runner Orchestrators ─ fireactions(GitHub) / fireteact(Gitea) / fireglab(GitLab)
Layer 2: Registry Cache    ─ Zot OCI cache + Squid HTTP proxy
Layer 1: microvm-base      ─ Network bridges, containerd, DNSmasq, CNI, Firecracker
```

Каждая CI job:
1. Оркестратор создаёт tap-устройство + сеть
2. Firecracker VM стартует с собственным ядром Linux (~1 сек)
3. Runner регистрируется на CI-платформе
4. Job выполняется внутри изолированной VM
5. VM уничтожается → ноль артефактов от предыдущей job

### Конфигурация

```nix
{
  imports = [
    nixos-fireactions.nixosModules.microvm-base
    nixos-fireactions.nixosModules.registry-cache
    nixos-fireactions.nixosModules.fireactions
  ];

  services.microvm-base = {
    enable = true;
    kernel.source = "upstream";
    dns.upstreamServers = [ "8.8.8.8" "8.8.4.4" ];
  };

  services.registry-cache = {
    enable = true;
    useMicrovmBaseBridges = true;
    zot.enable = true;
    zot.mirrors = {
      "docker.io" = {};
      "ghcr.io" = {};
    };
  };

  services.fireactions = {
    enable = true;
    github.appIdFile = "/run/secrets/github-app-id";
    github.appPrivateKeyFile = "/run/secrets/github-app-key";
    pools = [{
      name = "default";
      maxRunners = 5;
      minRunners = 1;
      runner = {
        organization = "your-org";
        labels = [ "self-hosted" "firecracker" "linux" ];
      };
    }];
  };
}
```

### Поддержка CI-платформ

| Платформа | Оркестратор | Auth | Статус |
|-----------|------------|------|--------|
| GitHub Actions | fireactions (Go) | GitHub App | Работает |
| Gitea Actions | fireteact (Go) | API Token | Работает |
| GitLab CI | fireglab (Go) | PAT | Работает |

Все три можно запускать **одновременно** на одном хосте.

### Главный trade-off

```
Firecracker:
  ✅ KVM-изоляция — каждая job в отдельной VM
  ✅ Эфемерность — zero state leaks
  ✅ Multi-tenant безопасность
  ❌ НЕТ персистентного /nix/store → каждая job с нуля
  ❌ Нет 9p/virtiofs в Firecracker → нельзя шарить store хоста напрямую
```

**Обходные пути для /nix/store:**
1. Binary cache (Attic) на хосте — VM скачивает пакеты
2. Pre-built rootfs images — запечь зависимости в container image
3. OverlayFS на хосте — базовый rootfs (ro) + writable overlay per-VM
4. Snapshot restore — ~176 мс, pre-booted runner в warm pool

### Гибридная схема (рекомендация)

```yaml
jobs:
  trusted-build:
    if: github.event_name == 'push'
    runs-on: nix-trusted      # Self-hosted, persistent store, быстрый

  untrusted-build:
    if: github.event_name == 'pull_request'
    runs-on: nix-untrusted    # Firecracker VM, изолированный
```

### Когда использовать
- Open-source (fork PR с чужим кодом)
- Мультитенантные платформы
- Compliance / аудит безопасности
- Несколько CI-платформ (GitHub + Gitea + GitLab)

### Текущая зрелость
- Firecracker — **продакшн** (33K stars, AWS Lambda)
- nixos-fireactions — **ранний проект** (2 stars, solo dev, архитектура продуманная)
- microvm.nix — **зрелая альтернатива** (2.4K stars, 8 гипервизоров, sharing /nix/store)

---

## 🗂️ Вариант D: Snix Platform Layer

> Snix как общесистемный платформенный слой. Shared castore между всеми раннерами.
> Наслаивается под ЛЮБОЙ вариант (B, C, или даже A через nar-bridge).

### Ключевая идея

CI/CD — это частые операции: тесты, линтинг, сборка контейнеров. Контейнер — основной
артефакт, потому что это самый удобный способ запускать что-либо где-либо. При этом
в разных проектах мы часто используем **одни и те же технологии** (Python 3.13, Node.js,
bash, coreutils, ca-certificates, тот же Bun runtime...). Каждый проект тянёт одни и те
же зависимости → огромная дупликация в /nix/store.

Snix с content-defined chunking решает это фундаментально: одинаковые файлы и чанки
между разными версиями пакетов, разными проектами, разными раннерами хранятся
**ровно один раз**. Кейс Replit: 6 ТБ → 1.2 ТБ (80% экономия).

### Трёхуровневая архитектура store

```
┌─────────────────────────────────────────────────────────────────┐
│                     Runner Host (NixOS)                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Уровень 3: Per-Job Upper Layer (эфемерный)                │  │
│  │  Результаты текущей сборки. tmpfs или volume.              │  │
│  │  Уничтожается после job (для Firecracker) или GC.         │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  Уровень 2: Системный /nix/store (стандартный Nix)         │  │
│  │  Обычный persistent Nix store хоста.                       │  │
│  │  Работает как всегда — nix build, nix-env, nixos-rebuild.  │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  Уровень 1: Snix Castore (shared между всеми раннерами)    │  │
│  │  Content-addressed, дедуплицированный, BLAKE3 Merkle DAG.  │  │
│  │  Один systemd daemon обслуживает ВСЕХ.                     │  │
│  │  gRPC API → FUSE mount / virtiofs / nar-bridge.            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Nix видит Уровень 1+2+3 через OverlayFS как единый /nix/store  │
└─────────────────────────────────────────────────────────────────┘
```

### Как раннеры используют Snix

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Runner Host                                  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │         snix store daemon (systemd, единственный)               │ │
│  │  gRPC :8000 · /var/lib/snix-{castore,store}                     │ │
│  │  Content-addressed blobs (objectstore) + PathInfo (redb)        │ │
│  │                                                                  │ │
│  │  Store Composition:                                              │ │
│  │    PathInfo: local redb → cache.nixos.org → nix-community       │ │
│  │    Blobs: local objectstore (дедуплицированные чанки)           │ │
│  └────────────┬──────────┬──────────┬──────────┬───────────────────┘ │
│               │          │          │          │                      │
│          gRPC │     gRPC │     gRPC │    gRPC  │                     │
│               │          │          │          │                      │
│  ┌────────────▼┐  ┌──────▼─────┐  ┌▼────────┐ ┌▼──────────────────┐ │
│  │ snix FUSE   │  │ snix       │  │ nar-    │ │ snix nix-daemon   │ │
│  │ mount       │  │ nix-daemon │  │ bridge  │ │ (overlay lower)   │ │
│  │ /srv/snix   │  │ .sock      │  │ :9000   │ │ /run/snix.sock    │ │
│  └──────┬──────┘  └──────┬─────┘  └────┬────┘ └──────┬────────────┘ │
│         │                │              │             │              │
│    ┌────▼────┐     ┌─────▼─────┐  ┌─────▼────┐  ┌────▼──────────┐  │
│    │Runner 1 │     │ Runner 2  │  │ Remote   │  │ Runner 3      │  │
│    │(direct  │     │(overlay   │  │ runners  │  │(Firecracker   │  │
│    │ Nix +   │     │ store:    │  │(standard │  │ VM + virtiofs │  │
│    │ FUSE)   │     │ snix=low  │  │ Nix HTTP │  │ → snix lower) │  │
│    │         │     │ local=up) │  │ subst.)  │  │               │  │
│    └─────────┘     └───────────┘  └──────────┘  └───────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

**Три способа подключения раннера к shared castore:**

1. **Overlay-store (рекомендуемый)** — snix nix-daemon как lower layer, локальный /nix/store как upper.
   Nix работает как обычно, но substitutions идут через snix (с дедупликацией).

2. **FUSE mount** — прямое монтирование snix store. Проще, но медленнее для write.

3. **nar-bridge (HTTP)** — для удалённых раннеров. Стандартный Nix substituter.
   Любой Nix клиент на любой машине подключается как `substituters = http://host:9000`.

### Что даёт Snix

| Механизм | Эффект | Влияние на CI |
|----------|--------|---------------|
| Content-defined chunking | 70–90% дедупликация (Replit: 6 ТБ → 1.2 ТБ) | Компактный shared store для всех проектов |
| OverlayFS overlay-store | Мгновенное подключение store | 0 сек на восстановление кеша |
| Lazy FUSE mount | On-demand подгрузка файлов | Build открывает 1 файл из 10000 → скачивается 1 |
| Granular substitution | Только изменённые чанки | python-3.11.8→3.11.9: ~10MB вместо 200MB |
| Verified streaming (BLAKE3) | Параллельная загрузка | Быстрее substitution |
| nar-bridge | Read-write HTTP binary cache | Заменяет или дополняет Attic |
| Shared castore | Один store на все проекты | Runner 1 собрал numpy → Runner 2 получает мгновенно |

### Почему это критично для CI/CD контейнеров

```
Проект A (Python бот):      python3.13, requests, aiohttp, pillow, cacert, bash
Проект B (Python API):      python3.13, fastapi, pydantic, pillow, cacert, bash
Проект C (Bun сайт):        bun, cacert, bash, coreutils
Проект D (Python ML):       python3.13, numpy, torch, cacert, bash

Обычный /nix/store (отдельно на каждом runner):
  python3.13 × 4 копии = 400 MB waste
  cacert × 4 = 4 MB waste
  pillow × 2 = 60 MB waste
  ...

Shared snix-castore:
  python3.13 = одна копия чанков (shared)
  cacert = одна копия (shared)
  pillow = одна копия (shared)
  Все четыре проекта на одном хосте: ~70-90% экономия

+ nix2container: при сборке OCI-образа, runtime layer (python, bash, cacert)
  одинаков для проектов A, B, D → skopeo пропускает при push!
```

### Сценарий: Snix + Firecracker (идеальная комбинация)

```
1. На хосте работает snix store daemon (persistent, дедуплицированный)
2. CI job приходит → Firecracker VM стартует за ~125ms
3. virtiofs экспортирует snix-store в VM как /nix/store (lower layer)
4. tmpfs — upper layer для результатов текущей сборки
5. OverlayFS объединяет → Nix внутри VM видит полный store
6. nix build .#oci-prod → собирает только то, чего нет в lower
7. Новые артефакты (upper) сохраняются обратно в snix-castore на хосте
8. VM уничтожается — чистая KVM-изоляция, zero state leaks
9. Следующая VM мгновенно видит всё, что было собрано ранее

Итого: изоляция Firecracker + persistent deduplicated store = лучшее из обоих миров
```

### Конфигурация shared snix daemon (NixOS)

```nix
{ config, pkgs, ... }:
let snixPkg = /* snix binary from flake */;
in {
  # 1. Центральный snix store daemon
  systemd.services.snix-store-daemon = {
    description = "Snix Store gRPC Daemon (shared castore)";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "${snixPkg}/bin/snix store daemon";
      StateDirectory = "snix-castore snix-store";
      Restart = "always";
    };
  };

  # 2. FUSE mount для overlay-store lower layer
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

  # 3. nix-daemon протокол для overlay-store lower
  systemd.services.snix-nix-daemon = {
    description = "Snix Nix Daemon (overlay store lower layer)";
    after = [ "snix-store-daemon.service" ];
    requires = [ "snix-store-daemon.service" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = "${snixPkg}/bin/snix nix-daemon -l /run/snix-daemon.sock --unix-listen-unlink";
      Restart = "always";
    };
  };

  # 4. nar-bridge — HTTP binary cache для удалённых runners
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

  # 5. Nix использует overlay-store с snix lower layer
  nix.settings.experimental-features = [ "local-overlay-store" ];
  nix.extraOptions = ''
    store = local-overlay://?upper-layer=/nix/store&lower-store=unix%3A%2F%2F%2Frun%2Fsnix-daemon.sock&check-mount=false
  '';
}
```

### Store Composition — тиерированный кеш

```toml
# /etc/snix/store-config.toml
# Snix castore ищет PathInfo: local → cache.nixos.org → nix-community
[pathinfoservices.root]
type = "cache"
near = "&local-redb"
far = "&nixos-cache"

[pathinfoservices.local-redb]
type = "redb"
path = "/var/lib/snix-store/pathinfo.redb"

[pathinfoservices.nixos-cache]
type = "nix"
base_url = "https://cache.nixos.org"
trusted_public_keys = ["cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="]
blob_service = "&root"
directory_service = "&root"
```

### snix-eval и snix-build — экспериментальное ускорение

Помимо castore (уже production-ready), Snix имеет два компонента для
ускорения самого процесса evaluation и build. Они ещё не stable, но
представляют интерес для экспериментов.

#### snix-eval — Bytecode VM Evaluator

| Оптимизация | Механизм | Потенциальный выигрыш |
|-------------|----------|----------------------|
| Bytecode VM | Flat opcode loop вместо AST walk (C++ Nix) | Cache-friendly, предсказуемый CPU pipeline |
| Bytecode caching | Кеш скомпилированного bytecode между CI runs | ~50-80% ускорение re-evaluation |
| Specialized opcodes | `OP_ATTR_SET`, `OP_ATTR_PATH` для attrsets | Оптимизация самой частой Nix операции |
| Lazy thunks | Отложенные вычисления, force-on-demand | Evaluate только то, что реально нужно |
| Parallel eval | Планируется: оценка независимых derivations параллельно | 2-4x на multi-core |
| Pluggable I/O | `EvalIO` trait — evaluator не привязан к конкретному store | Подключение к snix-castore, remote store |

**Текущий статус**: evaluation nixpkgs hello/firefox даёт корректные output paths.
Flakes пока не поддерживаются (fetchTree WIP). devenv от Cachix планирует переход
на snix-eval. CLI нестабилен — для экспериментов, не для production.

#### snix-build — Pluggable Builder

| Оптимизация | Механизм | Потенциальный выигрыш |
|-------------|----------|----------------------|
| Lazy input mount | FUSE/virtiofs: файлы читаются on-demand | Build открывает 1 из 10000 → скачивается 1 |
| Content-addressed inputs | BuildRequest с BLAKE3 хешами | Нет frankenbuilds, точечная дельта |
| gRPC remote builds | Распределение сборок на мощные серверы | Offload тяжёлых derivations |
| OCI builder | runc container для каждой сборки | Изоляция без Nix sandbox overhead |
| Планируемые backends | Kubernetes, bwrap, gVisor, Firecracker | Выбор execution environment |

**Текущий статус**: OCI builder собирает простые пакеты (hello). Reference scanning
в процессе. Полный nixpkgs build — не готов. Для production — рано.

#### Комбинирование: что можно попробовать

```
Вариант A (стабильный, рекомендуемый СЕЙЧАС):
  Стандартный Nix eval + build + snix-castore overlay
  Nix не знает про Snix — просто видит overlay-store
  100% совместимость, 80-90% экономия хранения

Вариант B (экспериментальный):
  snix-eval → .drv файлы → стандартный nix-build
  Теоретически: bytecode caching ускоряет evaluation
  Практически: нет flake-поддержки, нет стабильного CLI

Вариант C (будущее):
  snix-eval → snix-glue → snix-build (полный Snix stack)
  Lazy inputs, parallel eval, content-addressed everything
  Ждём зрелости проекта
```

### Дорожная карта Snix-интеграции

```
Этап 1 (СЕЙЧАС):
  snix-castore + overlay-store + nar-bridge
  Стандартный Nix для eval/build
  Выигрыш: 80-90% dedup, shared store, HTTP cache
  Риск: низкий

Этап 2 (эксперименты):
  Попробовать snix-eval для evaluation простых Nix выражений
  Попробовать snix-build OCI builder на простых пакетах
  Написать NixOS модуль для удобной настройки snix daemon
  Риск: средний (experimental)

Этап 3 (по готовности flakes в snix):
  snix-eval с bytecode caching для ускорения evaluation
  Parallel evaluation на multi-core
  Риск: зависит от зрелости API

Этап 4 (долгосрочно):
  Полный Snix stack: eval → build → castore
  Lazy build inputs, granular substitution, gRPC remote builds
  MicroVM executor (Firecracker backend для snix-build)
  Риск: высокий, но потенциал огромный
```

### Текущая зрелость

| Компонент | Статус | Можно в prod? |
|-----------|--------|--------------|
| snix-castore (хранение, dedup) | ✅ Готово | Да (Replit в prod) |
| snix store daemon (gRPC) | ✅ Готово | Да |
| snix FUSE mount | ✅ Готово | Да |
| snix nix-daemon (overlay lower) | ✅ Готово (subset) | Да |
| nar-bridge (HTTP cache) | ✅ Готово | Да |
| Store Composition (тиеры) | ⚠️ Experimental | Для экспериментов |
| snix-eval (bytecode VM) | ⚠️ В разработке | Для экспериментов |
| snix-build (OCI builder) | ⚠️ Ранняя стадия | Для экспериментов |
| overlay-store (Nix feature) | ⚠️ Experimental | Для экспериментов |
| Полная замена nix CLI | ❌ Не готово | Нет |

---

## 🗂️ Вариант E: nspawn-runners + snix overlay-store

> Рекомендуемый вариант для trusted internal CI.
> Заменяет Вариант C (microVM) на systemd-nspawn контейнеры с нативным OverlayFS.
> Наслаивается поверх Варианта D (Snix Platform Layer).

### Архитектура

```
Host:
  snix-store-daemon → FUSE mount /srv/snix-store (ro)
  Host /nix/store (системный, 54+ GB)

Per-runner nspawn container:
  /nix/store = OverlayFS:
    lower 1: host /nix/store (bind-mount, ro)
    lower 2: /srv/snix-store (snix FUSE, ro, dedup)
    upper:   /var/lib/runner-stores/<name>/upper (rw, ephemeral)

  nix-daemon (local-overlay-store)
    lower = unix:///run/snix-daemon.sock (snix nix-daemon)
    upper = per-runner writable layer

  github-runner → nix build → overlay lookup → post-build-hook → snix castore
```

### Почему не microVM (Вариант C)

| Проблема microVM | Решение в nspawn |
|-----------------|------------------|
| virtiofs sandbox=none (workaround) | OverlayFS нативный в ядре |
| VM overhead: hypervisor + kernel boot | Container: namespace isolation, <1s start |
| microvm.nix input → +30s flake eval | Нулевой overhead на eval (systemd built-in) |
| Дебаг: ssh root@vm, serial console | `machinectl shell runner-*` |
| ~200-400MB RAM per VM | ~20-50MB per container |

### Стек

| Компонент | Инструмент | Роль |
|-----------|-----------|------|
| Container runtime | systemd-nspawn | NixOS native containers, veth isolation |
| Store sharing | Linux OverlayFS | Multi-lower: host + snix, per-runner upper |
| Dedup backend | snix castore | Content-addressed, BLAKE3 Merkle DAG |
| Store protocol | local-overlay-store (Nix experimental) | Nix daemon знает о snix lower |
| Post-build push | nix copy --to snix socket | Результаты билдов попадают в castore |

### Что генерирует модуль

Для каждого runner из `organizations.*.runners.*`:
- `containers.runner-<org>-<type>-<idx>` — NixOS nspawn контейнер
- OverlayFS setup через ExecStartPre
- Внутри: github-runner, docker, nix с overlay-store, post-build-hook
- Изолированная сеть (veth + bridge + NAT)

### Готовность компонентов

| Компонент | Статус | Production-ready? |
|-----------|--------|-------------------|
| systemd-nspawn containers | ✅ Stable | Да (NixOS native) |
| Linux OverlayFS multi-lower | ✅ Stable | Да (kernel 4.0+) |
| snix FUSE mount | ✅ Готово | Да |
| snix nix-daemon socket | ✅ Готово | Да |
| local-overlay-store (Nix) | ⚠️ Experimental | Для CI — да, с check-mount=false |
| post-build-hook → snix | ✅ Готово | Да |

### Конфигурация (целевое состояние perturabo)

```nix
vladOS.services.nspawn-runners = {
  enable = true;
  organizations.fatdata = {
    url = "https://github.com/FatDataProduct";
    tokenFile = "/secrets/github-tokens/fatdata";
    runners = {
      nix-build = { count = 2; ephemeral = true; };
      deploy = { count = 1; ephemeral = false; };
    };
  };
};
```

> Детальная архитектура: `fd_cicd/research/14-nspawn-runners-architecture.md`

---

## 🐳 Сборка OCI-образов: nix2container (без nix-oci)

### Решение по nix-oci

**nix-oci НЕ подходит** для нашей архитектуры:
- Нет управления слоями (`layers` не передаётся в `buildImage`)
- Нет escape hatch к nix2container API
- Захардкоженный `Env`, `PATH=/bin`, `pathsToLink`
- Спроектирован для single-binary контейнеров

**Решение**: прямой nix2container + собственные flake-parts обёртки.

### Заимствуем из nix-oci

| Идея | Реализация |
|------|-----------|
| Auto shadow setup | Утилита `mkNonRootShadowSetup` для /etc/passwd |
| Security scanning | Trivy + Grype как `nix flake check` |
| Debug-образы | Вариант с bash/curl/strace для отладки |
| SBOM | Syft для Software Bill of Materials |
| perContainer pattern | Deferred modules для monorepo |

### Трёхслойная архитектура (финальная)

```nix
runtimeLayer = n2c.buildLayer { deps = runtimeDeps; };

depsLayer = n2c.buildLayer {
  deps = [ venv ];  # или nodeModules
  layers = [ runtimeLayer ];  # дедупликация: вычитаем paths из runtime
};

appLayer = n2c.buildLayer {
  deps = [ appSrc ];
  layers = [ runtimeLayer depsLayer ];  # вычитаем всё предыдущее
};

image = n2c.buildImage {
  name = "myapp";
  tag = commitSha;
  layers = [ runtimeLayer depsLayer appLayer ];
  config = {
    Entrypoint = [ ... ];
    WorkingDir = "/app";
    Env = [ "PATH=/bin" "LANG=C.UTF-8" ... ];
    User = "1000:1000";
  };
  perms = [{
    path = appSrc;
    regex = ".*\\.sh";
    mode = "0755";
  }];
};
```

### Ответ про гранулярность слоёв (Nix vs Docker)

**Вопрос**: если я в слое зависимостей изменил одну зависимость — нужно ли пересобирать весь слой?

**Ответ**: зависит от стратегии.

**Docker (классика)**: изменение одного пакета → пересборка ВСЕГО слоя и всех последующих.

**Nix + nix2container**: гранулярнее! Несколько подходов:

1. **`maxLayers` (автоматическое разбиение)** — nix2container разбивает зависимости на подслои:
```nix
(n2c.buildLayer {
  deps = [ venv ];
  maxLayers = 10;  # разбить venv на 10 подслоёв
})
```
При изменении одной зависимости — пересобирается только подслой, содержащий её store path. Остальные подслои идентичны → skopeo их пропускает при push.

2. **Ручное разделение** — вынести тяжёлые зависимости в отдельные слои:
```nix
layers = [
  (n2c.buildLayer { deps = [ pkgs.python3 ]; })        # Python runtime
  (n2c.buildLayer { deps = heavyDeps; maxLayers = 5; }) # numpy, torch...
  (n2c.buildLayer { deps = lightDeps; maxLayers = 5; }) # requests, pyyaml...
  (n2c.buildLayer { deps = [ appSrc ]; })               # код
];
```

3. **Nix store granularity** — каждый пакет = отдельный store path:
```
/nix/store/abc-requests-2.31.0   # 500 KB — НЕ меняется
/nix/store/def-numpy-1.26.0      # 30 MB — НЕ меняется
/nix/store/ghi-pyyaml-6.0.2      # ИЗМЕНИЛСЯ → только этот path обновляется
```
nix2container при push проверяет каждый store path по хешу. skopeo пропускает существующие слои в registry. **Даже если весь слой deps пересобирается, при push отправляется только diff**.

4. **На уровне Nix store (не Docker)** — overlay-store + snix:
```
Lower store: все предыдущие зависимости (read-only, дедуплицированные)
Upper store: только изменённый пакет (copy-on-write)
```
При сборке Nix не пересобирает то, что уже есть в store — берёт из кеша. Пересобирается **только** изменённый пакет и то, что от него зависит. Это быстрее Docker, где `pip install` запускается с нуля.

### Стратегии использования maxLayers

#### Стратегия 1: "Просто maxLayers" (для простых проектов)

Для небольших сервисов и случаев, где управление слоями не критично — можно не думать
о семантике слоёв вообще. Достаточно одного `buildLayer` с `maxLayers`:

```nix
image = n2c.buildImage {
  name = "myapp";
  tag = commitSha;
  layers = [
    (n2c.buildLayer {
      deps = allDeps ++ [ appSrc ];
      maxLayers = 20;
    })
  ];
  config = { Entrypoint = [ ... ]; };
};
```

nix2container автоматически разобьёт все store paths на ~20 подслоёв, группируя
по popularity/size. При изменении любого пакета или кода — пересобирается
только подслой, содержащий изменённый store path. Остальные подслои сохраняют
свой digest → skopeo их пропускает при push, Docker/containerd не перетягивает при pull.

**Когда подходит**:
- Маленькие проекты, 1–3 сервиса
- Не нужен контроль над тем, что именно попадает в какой слой
- Быстрый старт без оверинжиниринга

**Ограничение**: nix2container не знает семантику пакетов — runtime, deps и app-код
могут оказаться в одном подслое. Это снижает эффективность cross-image sharing
между разными сервисами (подробнее — ниже в "Как maxLayers группирует store paths").

#### Стратегия 2: Семантические слои + maxLayers (рекомендуемая)

Комбинация ручных семантических слоёв и автоматического `maxLayers` внутри каждого
даёт максимальную эффективность. Ты контролируешь *что* группируется вместе
(по частоте изменений и переиспользуемости), а nix2container дробит *как* это хранится
на подслои для минимального diff при push/pull:

```nix
layers = [
  # Runtime: Python, bash, coreutils, ca-certificates
  # Меняется раз в месяц. Общий для всех Python-сервисов.
  (n2c.buildLayer { deps = runtimeDeps; maxLayers = 5; })

  # Dependencies: venv с pip-пакетами
  # Меняется раз в неделю. maxLayers дробит на подслои —
  # при обновлении одного пакета пересобирается один подслой.
  (n2c.buildLayer {
    deps = [ venv ];
    layers = [ runtimeLayer ];
    maxLayers = 10;
  })

  # App: исходный код
  # Меняется каждый коммит. Маленький, maxLayers не нужен.
  (n2c.buildLayer {
    deps = [ appSrc ];
    layers = [ runtimeLayer depsLayer ];
  })
];
```

**Почему это лучше обоих подходов по отдельности:**

```
Только семантические слои (без maxLayers):
  deps слой = 200 MB, один пакет обновился
  → весь 200 MB layer blob получает новый digest
  → push/pull 200 MB

Только maxLayers (без семантики):
  runtime + deps + app перемешаны в подслоях
  → cross-image sharing между сервисами не работает
  → разные сервисы не переиспользуют общий runtime-подслой

Семантические слои + maxLayers:
  deps слой разбит на 10 подслоёв по ~20 MB
  → обновился один пакет → один подслой ~20 MB
  → push/pull 20 MB вместо 200 MB
  + runtime слой идентичен для всех Python-сервисов
  → registry хранит один раз, pull один раз
```

**Когда подходит**:
- Несколько сервисов на одном стеке (общий runtime layer)
- Частые деплои (>5/день) — каждый MB на push/pull имеет значение
- Тяжёлые deps (ML, data science) — maxLayers на deps-слое критичен

### Как maxLayers группирует store paths

`maxLayers` **не раскладывает** каждую зависимость в отдельный подслой.
Алгоритм берёт всю closure (набор store paths) слоя и распределяет их
в N бакетов по popularity (количество ссылок из других paths) и размеру.

```
Пример: deps-слой содержит 80 store paths, maxLayers = 10
→ каждый подслой ≈ 8 store paths (не 1 path = 1 подслой)

Подслой 1: [ glibc, gcc-libs, zlib, bzip2, ... ]        # высокая popularity
Подслой 2: [ openssl, libffi, ncurses, readline, ... ]   # средняя
...
Подслой 9: [ requests, urllib3, charset-normalizer, ... ] # низкая
Подслой 10: [ my-rare-lib, ... ]                          # минимальная
```

Группировка **детерминирована** для данного набора store paths — одинаковые deps
всегда дают одинаковые подслои с одинаковыми digest.

#### Два уровня sharing, которые из этого следуют

**1. Cross-VERSION sharing (один сервис, разные версии) — работает отлично.**
Обновил `requests 2.31→2.32` → изменился один подслой из 10. Остальные 9 сохраняют
digest → skopeo пропускает при push, Docker не перетягивает при pull.

**2. Cross-IMAGE sharing (разные сервисы) — зависит от уровня.**

```
Runtime-слой (семантический):
  Service A: deps = [ python3 bash cacert coreutils ]
  Service B: deps = [ python3 bash cacert coreutils ]
  → ОДИНАКОВАЯ closure → ОДИНАКОВЫЕ подслои → ОДИНАКОВЫЕ digest
  → Registry хранит ОДИН раз. Pull ОДИН раз.
  ✅ Идеальная дедупликация.

Deps-слой (maxLayers):
  Service A: venv = [ requests, numpy, torch ]     → closure из 60 paths
  Service B: venv = [ requests, flask, pydantic ]   → closure из 45 paths
  → РАЗНАЯ closure → РАЗНАЯ группировка popularity
  → `requests` может попасть в разные подслои у A и B
  → digest подслоёв РАЗНЫЕ, даже если пакет один и тот же
  ⚠️ Cross-image дедупликация НЕ гарантирована.
```

Это фундаментальное ограничение: `maxLayers` группирует по popularity-графу
всей closure. Разный набор deps → разный граф → один и тот же пакет попадает
в разные бакеты. Registry видит разные digest → хранит отдельно.

#### Почему семантические слои всё равно критичны

Семантический runtime-слой — единственный способ гарантировать cross-image sharing:

```
5 Python-сервисов в monorepo, все используют один runtimeDeps:

Без семантики (1 слой + maxLayers на всё):
  Каждый сервис: уникальная closure (runtime + deps + app)
  → 5 × уникальные подслои → 0% shared в registry
  → registry: 5 × 400 MB = 2 GB

С семантикой (runtime + deps + app):
  Runtime (одинаковый для всех):  150 MB × 1 = 150 MB (shared)
  Deps (у каждого свои, maxLayers): 5 × 200 MB = 1 GB
  App:                              5 × 5 MB = 25 MB
  → registry: 1.175 GB вместо 2 GB

  + при pull на новую ноду:
    runtime уже есть → тянутся только deps + app
```

Общие deps между сервисами (вроде `requests`, который используется повсюду)
дедуплицируются **не на уровне OCI-слоёв**, а на уровне **Nix store** и **snix castore**
(content-defined chunking). Это два разных механизма дедупликации:

```
OCI registry:  дедупликация по layer digest (целый tar-blob)
Nix store:     дедупликация по store path hash (отдельный пакет)
Snix castore:  дедупликация по content chunks (части файлов)

maxLayers помогает с cross-version diff (один сервис, разные коммиты).
Семантические слои помогают с cross-image sharing (разные сервисы, общий runtime).
Snix помогает с cross-everything dedup (любые совпадения на уровне файлов/чанков).
```

**Итого**: Nix значительно гранулярнее Docker. Изменение одного пакета → пересборка
только его store path → при push отправляется только diff подслоя. Семантические слои
обеспечивают cross-image sharing на уровне registry. `maxLayers` внутри семантических
слоёв обеспечивает cross-version diff. Snix castore обеспечивает дедупликацию на уровне
файлов/чанков — там, где OCI-слои уже не помогают.

### Дедупликация на уровне Kubernetes-нод

Вопрос: когда k8s тянет образы на ноды, как дедуплицируются слои?

#### Уровень 1: containerd (автоматически, из коробки)

containerd (и CRI-O) хранит OCI-слои в content store, индексируя по digest (sha256).
Если два образа содержат слой с одинаковым digest — он хранится **один раз** на ноде.
Это работает автоматически, без настройки:

```
Node A:  10 Python-сервисов запущено
         runtime layer (sha256:abc123) — хранится 1 раз, ~150 MB
         10 разных deps layers — по ~200 MB каждый
         10 app layers — по ~5 MB каждый

Без семантических слоёв (1 монолитный слой на сервис):
  Хранение на ноде: 10 × 400 MB = 4 GB
  Pull при деплое нового сервиса: ~400 MB

С семантическими слоями (общий runtime):
  Хранение на ноде: 150 MB (shared) + 10 × 205 MB = 2.2 GB
  Pull при деплое нового сервиса: ~205 MB (runtime уже есть)
```

Именно поэтому `mkOCIImage` с общим `runtimeDeps` важен — он гарантирует,
что containerd на каждой ноде хранит runtime слой ровно один раз.

#### Уровень 2: Spegel — P2P sharing между нодами

Spegel (stateless cluster-level OCI registry mirror) позволяет нодам тянуть слои
друг у друга, а не из внешнего registry:

```
Без Spegel:
  Node 1: pull runtime layer ← registry (150 MB, через интернет)
  Node 2: pull runtime layer ← registry (150 MB, через интернет)
  Node 3: pull runtime layer ← registry (150 MB, через интернет)

С Spegel:
  Node 1: pull runtime layer ← registry (150 MB, через интернет)
  Node 2: pull runtime layer ← Node 1 (150 MB, LAN, ~10 Gbit/s)
  Node 3: pull runtime layer ← Node 1 или 2 (LAN)
```

Особенно эффективно при rolling update на 50+ нод — registry не становится
бутылочным горлышком, ноды обмениваются слоями по LAN.

#### Уровень 3: nix-snapshotter — store-path-level dedup на нодах (experimental)

nix-snapshotter — containerd snapshotter, который **вообще убирает OCI-слои**
из уравнения. Вместо pull tar-blob'ов containerd разрешает образ в набор
Nix store paths и тянет их из binary cache (Attic, cache.nixos.org, snix nar-bridge).

```
Обычный containerd:
  Image → [ layer1.tar.gz, layer2.tar.gz, layer3.tar.gz ]
  Дедупликация: по layer digest (целый tar)

nix-snapshotter:
  Image → [ /nix/store/abc-python3, /nix/store/def-requests, /nix/store/ghi-app ]
  Дедупликация: по store path (отдельный пакет)
```

Это даёт store-path-level дедупликацию прямо на k8s-ноде:

```
Service A: python3 + requests + numpy + app-a    (40 store paths)
Service B: python3 + requests + flask + app-b    (35 store paths)

Обычный containerd:
  runtime layer shared (одинаковый) ✅
  deps layer A ≠ deps layer B (разный digest) → хранятся отдельно ❌
  requests хранится 2 раза (внутри разных layer tar'ов)

nix-snapshotter:
  /nix/store/abc-python3   — 1 копия (shared) ✅
  /nix/store/def-requests  — 1 копия (shared) ✅  ← вот тут выигрыш
  /nix/store/xyz-numpy     — 1 копия (только A)
  /nix/store/qwe-flask     — 1 копия (только B)
  Каждый store path ровно один раз на ноде.
```

nix-snapshotter решает именно ту проблему, которую OCI-слои не могут:
общие зависимости между сервисами с разным набором deps.

#### Сводка: дедупликация на каждом уровне

```
Уровень             │ Единица dedup  │ Автоматически? │ Что помогает
────────────────────┼────────────────┼────────────────┼──────────────────────────
OCI registry        │ layer digest   │ ✅ да          │ семантические слои + maxLayers
containerd на ноде  │ layer digest   │ ✅ да          │ семантические слои (общий runtime)
Spegel (P2P)        │ layer digest   │ ✅ после setup │ снижает нагрузку на registry
nix-snapshotter     │ store path     │ ✅ после setup │ dedup общих deps между сервисами
Nix store (builder) │ store path     │ ✅ да          │ пересборка только изменённого
Snix castore        │ content chunk  │ ✅ да          │ dedup на уровне файлов/чанков
```

---

## 🧩 Структура flake.nix (flake-parts)

### Выбранный стек

| Инструмент | Роль | Приоритет |
|------------|------|-----------|
| **flake-parts** | Модульность flake | Обязательно |
| **nix2container** | Сборка OCI | Обязательно |
| **uv2nix** | Python packaging | Для Python шаблона |
| **bun2nix** | Bun packaging | Для Bun шаблона |
| **dream2nix** | Node.js packaging | Опциональный (отдельные примеры) |
| **git-hooks.nix** | Pre-commit hooks | Обязательно |
| **treefmt-nix** | Форматирование | Обязательно |

### Модульная структура

```
flake.nix
├── nix/
│   ├── oci.nix          # OCI-образы (nix2container)
│   ├── python.nix       # Python env (uv2nix) — или js.nix для Bun
│   ├── devshell.nix     # Dev shell с инструментами
│   ├── hooks.nix         # git-hooks.nix конфигурация
│   ├── checks.nix       # Тесты, линтинг, security scan
│   └── push.nix         # Push-инструменты (skopeo, curl, jq)
```

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    nix2container.url = "github:nlewo/nix2container";
    git-hooks-nix.url = "github:cachix/git-hooks.nix";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    # + uv2nix / bun2nix / pyproject-nix...
  };

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } {
    systems = [ "x86_64-linux" "aarch64-linux" ];
    imports = [
      inputs.git-hooks-nix.flakeModule
      inputs.treefmt-nix.flakeModule
      ./nix/oci.nix
      ./nix/python.nix      # или ./nix/js.nix
      ./nix/devshell.nix
      ./nix/checks.nix
    ];
  };
}
```

---

## 🪝 Хуки — полная стратегия

```
┌─────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1️⃣ Pre-commit (git-hooks.nix через flake-parts)            │
│     ├── Nix: nixfmt-rfc-style, deadnix, statix              │
│     ├── Python: ruff, ruff-format, mypy                      │
│     ├── JS: eslint, prettier                                 │
│     ├── Security: trufflehog, detect-private-keys            │
│     ├── General: check-merge-conflicts, actionlint, typos    │
│     └── Запуск: nix develop -c pre-commit run --all-files    │
│                                                              │
│  2️⃣ Build                                                    │
│     ├── pre-build-hook (опц. — кастомизация sandbox)         │
│     ├── nix build .#oci-prod                                 │
│     └── nix-output-monitor для наблюдения                    │
│                                                              │
│  3️⃣ Post-build (загрузка в кеш)                              │
│     ├── Self-hosted: queued-build-hook → Attic (async)       │
│     └── GitHub-hosted: magic-nix-cache-action                │
│                                                              │
│  4️⃣ Reproducibility (опционально)                            │
│     └── diff-hook + nix build --check                        │
│                                                              │
│  5️⃣ Security scan (опционально)                              │
│     ├── Trivy (CVE) как nix flake check                      │
│     ├── Grype (CVE) как nix flake check                      │
│     └── Syft (SBOM генерация)                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 Кеширование — многоуровневая архитектура

```
🔴 Уровень 0: /nix/store на runner (самый быстрый)
   ├── Self-hosted: персистентный → мгновенные повторные сборки
   ├── + overlay-store (Snix/Nix experimental): COW, деdup
   └── GitHub-hosted: эфемерный → magic-nix-cache спасает

🟡 Уровень 1: Приватный кеш (Attic)
   ├── Multi-tenancy, S3/local/Minio/R2 backend
   ├── LRU eviction, fine-grained JWT access
   ├── queued-build-hook → async auto-push
   └── Harmonia — проще, для одного сервера/проекта

🟢 Уровень 2: Публичные кеши (бесплатно)
   ├── cache.nixos.org — всё из nixpkgs
   ├── nix-community.cachix.org — community пакеты
   └── numtide.cachix.org, devenv.cachix.org...

🔵 Уровень 3: GitHub Actions Cache (для Варианта A)
   └── magic-nix-cache-action: 10 GB, бесплатно
```

---

## ⚡ Оптимизация nix.conf для CI

```ini
max-jobs = auto
cores = 0
max-substitution-jobs = 32
auto-optimise-store = true
min-free = 5368709120       # 5 GB
log-lines = 500
show-trace = true

# Публичные кеши
substituters = https://cache.nixos.org https://nix-community.cachix.org
trusted-public-keys = cache.nixos.org-1:... nix-community.cachix.org-1:...

# Приватный кеш (self-hosted)
extra-substituters = http://cache.internal:8080/main
extra-trusted-public-keys = cache.internal:...

# Signing для post-build-hook
secret-key-files = /etc/nix/cache-priv-key.pem
```

---

## 📊 Матрица: что берём, что нет

### ✅ Берём (core)

| Инструмент | Роль | Статус |
|------------|------|--------|
| nix2container | OCI сборка | Основной |
| flake-parts | Модульность | Основной |
| DeterminateSystems/nix-installer-action | Nix на GitHub runner | Основной |
| DeterminateSystems/magic-nix-cache-action | Кеш для GitHub runner | Основной |
| srvos + services.github-runners | Self-hosted runner | Основной |
| Attic | Приватный binary cache | Основной |
| queued-build-hook | Async push в кеш | Основной |
| git-hooks.nix | Pre-commit hooks | Основной |
| treefmt-nix | Форматирование | Основной |
| uv2nix | Python packaging | Для Python |
| bun2nix | Bun packaging | Для Bun |
| nix-output-monitor | Наблюдение за сборкой | Утилита |

### 🟡 Берём (advanced / experimental)

| Инструмент | Роль | Статус |
|------------|------|--------|
| nixos-fireactions | Firecracker CI runners | Перспективный |
| Snix / overlay-store | Платформенный слой | Стратегический |
| buildbot-nix | Full Nix CI | Для больших команд |
| diff-hook | Reproducibility | Опциональный |

### ❌ Не берём

| Инструмент | Причина |
|------------|---------|
| nix-oci | Нет контроля слоёв, нет escape hatch |
| github-nix-ci (juspay) | Обрубок, мало контроля |
| cachix/cachix-action (push) | Vendor-lock |
| dockerTools.buildImage | Медленнее, нет инкрементальности |
| om ci (omnix) | CLI-helper для CI; не решает задач, которые не решаются стандартным Nix CLI |
| std (divnix) | Другой домен: организация flake-output'ов в "cells". См. разбор ниже |
| node2nix | Legacy, для новых проектов bun2nix/dream2nix |

### 🔵 Отдельные примеры (опциональные)

| Инструмент | Роль |
|------------|------|
| dream2nix | Node.js packaging (альтернатива bun2nix) |
| nixidy | K8s GitOps (будущее) |
| nix-snapshotter | containerd + Nix (будущее) |
| Trivy / Grype | Security scan (CVE), интеграция как `nix flake check` |
| Syft | SBOM (Software Bill of Materials) генерация |

---

## 🗺️ Дорожная карта

```
СЕЙЧАС (MVP):
  ┌── Вариант A: GitHub runner + magic-nix-cache
  └── Вариант B: Self-hosted NixOS + srvos + Attic
  Общее: nix2container · flake-parts · queued-build-hook · git-hooks.nix

СЛЕДУЮЩИЙ ШАГ:
  ┌── Вариант C: Firecracker (nixos-fireactions) — изоляция jobs
  ├── Гибрид B+C: persistent runner для push, Firecracker для PR
  └── overlay-store (Nix experimental) — COW /nix/store

БУДУЩЕЕ:
  ┌── Snix как платформенный слой (castore + FUSE + virtiofs)
  ├── Snix + Firecracker = изоляция + persistent deduplicated store
  ├── nixidy → ArgoCD (GitOps для K8s)
  └── nix-snapshotter (containerd без OCI registry)
```

---

## 🏗️ Итоговая компоновка шаблонов

### Шаблон 1: Python (uv) + GitHub Runner
```
uv2nix → nix2container (3 слоя) → skopeo → GHCR
Actions: nix-installer-action + magic-nix-cache
Хуки: ruff, ruff-format, mypy, nixfmt, trufflehog
```

### Шаблон 2: Python (uv) + Self-hosted Runner
```
uv2nix → nix2container (3 слоя) → skopeo → GHCR
Сервер: srvos + Attic + queued-build-hook
Хуки: те же + diff-hook для reproducibility
```

### Шаблон 3: Bun + GitHub Runner
```
bun2nix → nix2container (3 слоя) → skopeo → GHCR
Actions: nix-installer-action + magic-nix-cache
Хуки: eslint, prettier, nixfmt, trufflehog
```

### Шаблон 4: Bun + Self-hosted Runner
```
bun2nix → nix2container (3 слоя) → skopeo → GHCR
Сервер: srvos + Attic + queued-build-hook
```

### Шаблон 5: Self-hosted + Firecracker (advanced)
```
Любой стек + nixos-fireactions
Конфигурация: microvm-base + registry-cache + fireactions
Гибрид: nix-trusted (persistent) + nix-untrusted (Firecracker)
```

### Шаблон 6: Snix Overlay-Store (experimental)
```
Любой стек + overlay-store (Nix/Snix)
Lower: snix FUSE mount (или host /nix/store)
Upper: per-job writable layer
Можно наслоить на Варианты B, C, D
```

### Шаблон 7: dream2nix (Node.js, отдельно)
```
dream2nix → nix2container → GHCR
Отдельные примеры для Node.js + npm/yarn
```

---

## 🗂️ Структура репозитория

Репозиторий организован в три слоя: **research** (исследования), **templates** (scaffold для `nix flake init`), **examples** (рабочие мини-приложения с CI).

### Обоснование

1. **research/** — showcase всей исследовательской работы. Не содержит исполняемого кода, только документацию.
2. **templates/** — минимальные scaffold'ы, которые пользователь получает через `nix flake init -t github:owner/repo#python-uv`. Содержат заглушки (`src/__init__.py`), нет `flake.lock`. Пользователь заполняет своим кодом.
3. **examples/** — работающие мини-приложения с `flake.lock`, реальным (минимальным) кодом, и CI. Проверяются CI этого репозитория. Пользователь может скопировать как более полный стартер.

### GitHub Actions: двухуровневые workflow

GitHub Actions читает workflow-файлы только из `.github/workflows/` в корне репозитория. Поэтому:

- Каждый пример содержит "свой" CI-файл как контент примера (то, что пользователь скопирует)
- В корне репо — тонкие wrapper-workflow, которые триггерятся по path-filter и запускают `nix flake check` в директории примера

### Каноническая структура flake-parts модулей

Каждый шаблон/пример использует `nix/` директорию с отдельными файлами-модулями:
- `oci.nix` — OCI-образы (nix2container, слои, push)
- `python.nix` / `bun.nix` — языковой стек
- `devshell.nix` — dev shell
- `checks.nix` — тесты, линтинг

Это exactly how flake-parts designed to be used: явные импорты, каждый файл — модуль.
