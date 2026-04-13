# 🏃 Вариант 1: GitHub Hosted Runner + Nix Action

> Нулевая инфраструктура. GitHub предоставляет runner, мы ставим Nix через action.
> Подходит для начала, open-source, и когда нет своих серверов.

---

## 🎯 Схема

```
┌─────────────────────────────────────────────────────────────┐
│              GitHub-hosted Runner (ubuntu-latest)             │
│                                                              │
│  ┌──────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────┐  │
│  │ checkout  │─▶│ install nix │─▶│ restore  │─▶│nix build│  │
│  │           │  │ (30s)       │  │ cache    │  │ .#oci-* │  │
│  └──────────┘  └─────────────┘  └──────────┘  └────┬────┘  │
│                                                     │        │
│  ┌──────────┐  ┌─────────────┐                      │        │
│  │ save     │◀─│ skopeo push │◀─────────────────────┘        │
│  │ cache    │  │ → GHCR      │                               │
│  └──────────┘  └─────────────┘                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 Ключевые GitHub Actions

### 1️⃣ DeterminateSystems/nix-installer-action ⭐ (рекомендуется)

```yaml
- uses: DeterminateSystems/nix-installer-action@main
  with:
    extra-conf: |
      accept-flake-config = true
      max-jobs = auto
      cores = 0
      # Публичные кеши (всё open-source, бесплатно)
      extra-substituters = https://nix-community.cachix.org
      extra-trusted-public-keys = nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs=
```

- ✅ Установка ~30s
- ✅ Flakes из коробки
- ✅ Корректная деинсталляция
- ✅ Open-source (Determinate Systems, но action бесплатный!)

### 2️⃣ DeterminateSystems/magic-nix-cache-action ⭐ (рекомендуется)

```yaml
- uses: DeterminateSystems/magic-nix-cache-action@main
```

- ✅ Кеширует Nix store через **GitHub Actions Cache** (бесплатно, до 10 GB)
- ✅ Не требует Cachix / внешних сервисов
- ✅ Прозрачно — просто добавь step и всё
- ✅ Open-source
- ⚠️ 10 GB лимит на репо (но для большинства проектов хватит)

### 3️⃣ cachix/install-nix-action (альтернатива)

```yaml
- uses: cachix/install-nix-action@v30
  with:
    extra_nix_config: |
      experimental-features = nix-command flakes
      max-jobs = auto
      cores = 0
```

- ✅ Проверен временем
- ⚠️ Чуть медленнее установка

### ❌ НЕ используем (vendor-lock)

- ~~cachix/cachix-action~~ — требует Cachix аккаунт для push (для публичных проектов есть бесплатный tier, но это vendor-lock)

> 💡 **Наш выбор**: DeterminateSystems/nix-installer-action + magic-nix-cache-action.
> Оба open-source, бесплатные, не требуют внешних сервисов.

---

## 📋 Полный workflow шаблон

```yaml
name: 🐳 Nix Build & Push OCI
on:
  push:
    branches: [main, test, prod]

env:
  REGISTRY: ghcr.io

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      # ❄️ Установка Nix (~30s)
      - uses: DeterminateSystems/nix-installer-action@main
        with:
          extra-conf: |
            max-jobs = auto
            cores = 0
            accept-flake-config = true

      # 💾 Кеш через GitHub Actions Cache (бесплатно, до 10GB)
      - uses: DeterminateSystems/magic-nix-cache-action@main

      # 🔨 Сборка OCI
      - name: Build OCI image
        run: |
          nix build .#oci-prod \
            --log-format internal-json --max-jobs auto --cores 0 \
            2>&1 | nix run nixpkgs#nix-output-monitor -- --json

      # 🚀 Push в GHCR
      - name: Push to GHCR
        env:
          GHCR_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          nix build .#push-tools --out-link .push-tools
          export PATH="$PWD/.push-tools/bin:$PATH"

          OWNER=$(echo "${{ github.repository_owner }}" | tr '[:upper:]' '[:lower:]')
          IMAGE="${{ env.REGISTRY }}/${OWNER}/myapp"
          TAG="${GITHUB_REF_NAME}"
          SHA="${GITHUB_SHA::7}"

          skopeo --insecure-policy copy \
            nix:./result "docker://${IMAGE}:${TAG}" \
            --dest-creds "${{ github.actor }}:${GHCR_TOKEN}"

          skopeo --insecure-policy copy \
            "docker://${IMAGE}:${TAG}" "docker://${IMAGE}:${SHA}" \
            --dest-creds "${{ github.actor }}:${GHCR_TOKEN}"
```

---

## ⏱️ Ожидаемые тайминги

| Этап | 🥶 Первый раз (cold) | 🔥 Повторно (с кешем) |
|------|-------------------|-----------------------|
| ❄️ Install Nix | ~30s | ~30s |
| 💾 Restore cache | — | ~20-40s |
| 🔨 nix build (Python app, ~20 deps) | 5-10 мин | 30s-2 мин |
| 🔨 nix build (JS app, ~50 deps) | 3-7 мин | 20s-1 мин |
| 🚀 Push to GHCR | 30s-1 мин | ~10s (только app слой) |
| 💾 Save cache | ~30s | ~10s |
| **ИТОГО** | **7-12 мин** | **1.5-4 мин** |

---

## 📦 Ресурсы GitHub Hosted Runners

| Runner | vCPU | RAM | Диск | Цена |
|--------|------|-----|------|------|
| `ubuntu-latest` | 4 | 16 GB | 14 GB | Бесплатно (2000 мин/мес) |
| `ubuntu-latest-4-cores` | 4 | 16 GB | 150 GB | $0.008/мин |
| `ubuntu-latest-8-cores` | 8 | 32 GB | 300 GB | $0.016/мин |
| `ubuntu-latest-16-cores` | 16 | 64 GB | 600 GB | $0.032/мин |

> 💡 14 GB диска на бесплатном runner — может быть мало для больших Nix store.
> magic-nix-cache помогает, но если зависимостей очень много — нужен Вариант 2.

---

## ✅ Когда выбирать

- 🌐 Open-source проекты
- 👤 Маленькие команды (1-5 человек)
- 📦 Проекты с умеренным количеством зависимостей
- 🧪 CI время 3-5 мин — приемлемо
- 💰 Нет бюджета на инфраструктуру
- 🔄 Быстрый старт без настройки серверов

## ❌ Когда НЕ подходит

- 🏗️ Тяжёлые сборки (ML, CUDA, огромные зависимости)
- ⚡ Нужна скорость <1 мин
- 📦 Store > 10 GB (лимит кеша)
- 🔒 Строгие требования к приватности (код собирается на GitHub серверах)
- 🔄 Очень частые push (>50/день) — лимит минут
