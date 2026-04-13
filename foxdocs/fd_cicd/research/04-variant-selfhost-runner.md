# 🖥️ Вариант 2: Self-hosted NixOS GitHub Runner

> Свой сервер с NixOS, на нём крутится GitHub Actions runner.
> Nix store персистентный, сборки быстрые, полный контроль.
> **Это то, что уже работает в автопостере** (но криво).

---

## 🎯 Схема

```
┌─── Ваш сервер (NixOS) ──────────────────────────────────────┐
│                                                               │
│  ┌─────────────────────────┐    ┌─────────────────────────┐   │
│  │  GitHub Actions Runner  │    │  Nix Binary Cache        │   │
│  │  (srvos / github-nix-ci)│    │  (Attic / Harmonia)     │   │
│  │  ├── runner-1           │    │  ├── /nix/store → HTTP   │   │
│  │  ├── runner-2           │    │  └── post-build-hook     │   │
│  │  └── runner-N           │    │      auto-push           │   │
│  └─────────┬───────────────┘    └─────────────────────────┘   │
│            │                                                   │
│  ┌─────────▼───────────────────────────────────────────────┐   │
│  │              Persistent /nix/store                       │   │
│  │  ✅ Все деривейшны кешируются между сборками            │   │
│  │  ✅ Повторная сборка = ~секунды                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
  GitHub Actions UI    Container Registry (GHCR)
  (логи, статусы)      (OCI-образы)
```

---

## 🔧 NixOS модули для GitHub runners

### 1️⃣ srvos (nix-community) ⭐ рекомендуется

**GitHub**: [nix-community/srvos](https://github.com/nix-community/srvos)

Полноценный NixOS модуль от numtide с безопасными дефолтами:

```nix
# configuration.nix
{ inputs, ... }: {
  imports = [ inputs.srvos.nixosModules.github-actions-runner ];

  roles.github-actions-runner = {
    url = "https://github.com/MY-ORG";
    count = 4;  # 4 параллельных runner'а
    name = "nix-builder";

    # 🔐 GitHub App (безопаснее чем PAT!)
    githubApp = {
      id = "12345";
      login = "MY-ORG";
      privateKeyFile = config.age.secrets.github-runner-key.path;
    };

    # 💾 Опционально: Cachix для push
    # cachix.cacheName = "my-cache";
    # cachix.tokenFile = config.age.secrets.cachix-token.path;
  };
}
```

**Плюсы:**
- ✅ GitHub App auth (рекомендуемый способ)
- ✅ Секреты через sops-nix / agenix
- ✅ Изоляция между runners
- ✅ Масштабирование: N runners на одной машине
- ✅ Документация + поддержка numtide

**Требования:**
- ⚠️ Nested virtualization (KVM) если нужны NixOS VM тесты
- ⚠️ Bare-metal или VPS с KVM

### 2️⃣ github-nix-ci (juspay) — упрощённый

**GitHub**: [juspay/github-nix-ci](https://github.com/juspay/github-nix-ci)

Обёртка над стандартными nixpkgs/nix-darwin runner сервисами:

```nix
{
  services.github-nix-ci = {
    age.secretsDir = ./secrets;

    # Runners для конкретных репо
    personalRunners = {
      "myorg/myrepo".num = 2;
      "myorg/another-repo".num = 1;
    };

    # Runners для всей организации
    orgRunners = {
      "myorg".num = 4;
    };
  };
}
```

**Плюсы:**
- ✅ ~20 строк конфига вместо 200+
- ✅ Поддержка agenix
- ✅ Авто-labels (hostname + nix systems)
- ✅ Включает omnix (om ci) по умолчанию

**Минусы:**
- ⚠️ Меньше контроля чем srvos
- ⚠️ Менее активная поддержка

### 3️⃣ nixos-fireactions — изоляция через Firecracker 🔒

**GitHub**: [thpham/nixos-fireactions](https://github.com/thpham/nixos-fireactions)

Каждый job запускается в эфемерной Firecracker microVM:

```
Job → Firecracker microVM → выполнение → уничтожение
```

- ✅ Максимальная изоляция между jobs
- ✅ Поддержка GitHub Actions, Gitea Actions, GitLab CI
- ✅ 4-уровневая модульная архитектура
- ⚠️ Ещё молодой (1 ⭐, v0.3.0)
- ⚠️ Нужен bare-metal с KVM

---

## 📋 Workflow шаблон для self-hosted

```yaml
name: 🐳 Nix Build & Push OCI
on:
  push:
    branches: [main, test, prod]

jobs:
  build-and-push:
    runs-on: nix-builder  # 🏷️ label вашего self-hosted runner
    steps:
      - uses: actions/checkout@v4

      # ❌ НЕ нужен install-nix — Nix уже есть на NixOS!
      # ❌ НЕ нужен cache restore — /nix/store персистентный!

      # 🔨 Сборка
      - name: Build OCI image
        run: |
          nix build .#oci-prod \
            --log-format internal-json --max-jobs auto --cores 0 \
            2>&1 | nix run nixpkgs#nix-output-monitor -- --json

      # 🚀 Push
      - name: Push to GHCR
        env:
          GHCR_TOKEN: ${{ secrets.GHCR_TOKEN }}
        run: |
          nix build .#push-tools --out-link .push-tools
          export PATH="$PWD/.push-tools/bin:$PATH"
          # ... skopeo push logic
```

> 💡 На self-hosted runner НЕ нужны install-nix и cache actions!
> Nix уже установлен, store персистентный.

---

## 💾 Интеграция с кеш-сервером

### 🔄 post-build-hook → Attic / Harmonia

Каждый build автоматически пушится в кеш:

```bash
#!/bin/sh
# /etc/nix/post-build-hook.sh
set -eu
export IFS=' '
exec nix copy --to "http://cache.internal:5000" $OUT_PATHS
```

```nix
# nix.conf
post-build-hook = /etc/nix/post-build-hook.sh
```

> ⚠️ Проблема: hook блокирует build loop! Пока upload идёт — Nix ждёт.

### 🔄 Лучше: nix-post-build-hook-queue

```nix
# Фоновый daemon, не блокирует сборки
services.nix-post-build-hook-queue = {
  enable = true;
  # подписывает и пушит в фоне
};
```

**GitHub**: [newAM/nix-post-build-hook-queue](https://github.com/newAM/nix-post-build-hook-queue)

---

## ⏱️ Ожидаемые тайминги

| Этап | 🥶 Первая сборка | 🔥 Повторная (store есть) | 📦 Только код |
|------|-----------------|--------------------------|---------------|
| checkout | ~2s | ~2s | ~2s |
| nix build | 3-8 мин | 10-30s | **5-15s** |
| skopeo push | 30s-1 мин | 10-20s | **~5s** |
| **ИТОГО** | **4-10 мин** | **30s-1 мин** | **15-25s** 🚀 |

> 🔥 С персистентным store повторные сборки — **секунды**.
> Это главное преимущество self-hosted.

---

## 🖥️ Рекомендации по серверу

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| CPU | 4 cores | 8-16 cores |
| RAM | 8 GB | 16-32 GB |
| Диск | 50 GB SSD | 200+ GB NVMe |
| ОС | NixOS (любая) | NixOS unstable |
| Сеть | 100 Mbit | 1 Gbit+ |

> 💡 `/nix/store` на NVMe — ключевой фактор скорости.
> Nix делает ОЧЕНЬ много мелкого I/O.

---

## 🔒 Безопасность self-hosted runners

| Угроза | Mitigation |
|--------|-----------|
| Утечка secrets | GitHub App auth (не PAT), secrets через sops-nix/agenix |
| Вредоносный PR | Ограничить runs-on label, не запускать на fork PR |
| Shared /nix/store | Runners изолированы (srvos), store read-only для runner |
| Сетевой доступ | Firewall, только GitHub API + registry |
| Незачищенный workspace | Runner auto-cleanup после job |

---

## ✅ Когда выбирать

- 🏢 Приватные проекты (код не уходит на GitHub servers)
- ⚡ Нужна скорость (<1 мин для повторных сборок)
- 📦 Большие зависимости (ML, data science)
- 🔄 Частые push (>50/день)
- 💾 Нужен приватный binary cache
- 🖥️ Уже есть серверная инфраструктура

## ❌ Когда НЕ подходит

- 💰 Нет бюджета на сервер
- 👤 Solo-разработчик с маленьким проектом
- 🌐 Open-source (GitHub hosted бесплатный и проще)
