# 💾 Кеширование в Nix CI/CD

> Кеширование — **самое важное** для скорости Nix CI.
> Без кеша каждая сборка скачивает/собирает всё с нуля.
> С кешем — повторная сборка за секунды.

---

## 🏗️ Архитектура кеширования

```
┌─────────────────────────────────────────────────────────────────┐
│                    Уровни кеширования                            │
│                                                                  │
│  🔴 Уровень 0: /nix/store на runner (самый быстрый)             │
│  ├── Self-hosted: ПЕРСИСТЕНТНЫЙ → повторные сборки мгновенные   │
│  └── GitHub-hosted: ЭФЕМЕРНЫЙ → magic-nix-cache спасает         │
│                                                                  │
│  🟡 Уровень 1: Свой binary cache (Attic / Harmonia)             │
│  ├── Для приватного кода                                        │
│  ├── post-build-hook: автоматический push после каждой сборки   │
│  └── В локальной сети → быстрый доступ                          │
│                                                                  │
│  🟢 Уровень 2: Публичные кеши                                   │
│  ├── cache.nixos.org — всё из nixpkgs                           │
│  ├── nix-community.cachix.org — nix-community пакеты            │
│  └── Другие публичные Cachix кеши                               │
│                                                                  │
│  🔵 Уровень 3: GitHub Actions Cache (для Варианта 1)             │
│  └── magic-nix-cache-action: 10 GB, бесплатно                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Публичные кеши (бесплатные, open-source зависимости)

### Настройка в flake.nix

```nix
{
  nixConfig = {
    extra-substituters = [
      "https://cache.nixos.org"
      "https://nix-community.cachix.org"
    ];
    extra-trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
    ];
  };
}
```

### Или в nix.conf на сервере

```
substituters = https://cache.nixos.org https://nix-community.cachix.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs=
```

> 💡 Большинство зависимостей из nixpkgs уже закешированы на cache.nixos.org.
> Это значит что `pkgs.python3`, `pkgs.nodejs`, `pkgs.bash` и т.д. скачиваются
> как готовые бинарники, а не собираются из исходников!

---

## 🏠 Self-hosted Binary Cache

### ⚖️ Attic vs Harmonia

| | **Attic** ⭐ | **Harmonia** |
|-|------------|-------------|
| ⭐ GitHub stars | 1796 | 444 |
| 🏗️ Архитектура | S3-backed (или local), отдельный сервер | Сервит /nix/store напрямую |
| 👥 Multi-tenancy | ✅ Да! Изолированные кеши | ❌ Нет |
| 🔄 Дедупликация | ✅ Глобальная между кешами | ❌ (store-level) |
| 🔐 Signing | ✅ Managed (сервер подписывает) | ✅ Ручная настройка |
| 🗑️ Garbage collection | ✅ LRU eviction | ❌ Через nix-collect-garbage |
| 📦 Storage backend | S3 / Minio / R2 / Backblaze / local | Локальный /nix/store |
| 🔧 Сложность | 🟡 Средняя (нужен PostgreSQL + S3) | 🟢 Простая (один binary) |
| 🖥️ Минимум для старта | PostgreSQL + Attic + (опц. S3) | NixOS + Harmonia модуль |
| 📡 Масштабируемость | ✅ Горизонтальная (S3 + replicas) | ⚠️ Один сервер |
| 🔗 Доступ | JWT tokens (fine-grained) | ✅ Открытый / basic auth |
| 📊 Статус | «early prototype» но 1800 ⭐ | v3.0.0 (stable) |

### 🎯 Когда что выбирать

**Attic** → если:
- Несколько команд/проектов с разными уровнями доступа
- Нужна S3-совместимая storage (Minio, Cloudflare R2)
- Хочется fine-grained access control
- Планируется масштабирование

**Harmonia** → если:
- Один сервер, один проект
- Нужна максимальная простота
- /nix/store уже есть на сервере (self-hosted runner = кеш автоматически)
- Не нужна S3

### 🔧 Настройка Attic на NixOS

```nix
# Через Docker Compose (проще для старта)
services.atticd = {
  enable = true;
  settings = {
    listen = "[::]:8080";
    database.url = "postgresql://attic@localhost/attic";
    storage = {
      type = "local";
      path = "/var/lib/atticd/storage";
    };
    # Или S3:
    # storage = {
    #   type = "s3";
    #   region = "us-east-1";
    #   bucket = "nix-cache";
    #   endpoint = "https://minio.internal:9000";
    # };
  };
};
```

```bash
# Создать кеш
attic login myserver https://cache.internal:8080 <TOKEN>
attic cache create main

# Использовать кеш
attic use main

# Push paths
attic push main /nix/store/xxx-mypackage
# или
nix build .#myapp | attic push main -
```

### 🔧 Настройка Harmonia на NixOS

```nix
services.harmonia = {
  enable = true;
  signKeyPath = "/etc/nix/cache-priv-key.pem";
  settings.bind = "[::]:5000";
};

services.nginx.virtualHosts."cache.internal" = {
  locations."/".proxyPass = "http://[::1]:5000";
};
```

```bash
# Генерация ключей
nix-store --generate-binary-cache-key cache.internal cache-priv-key.pem cache-pub-key.pem

# На клиентах:
# nix.conf
substituters = https://cache.internal https://cache.nixos.org
trusted-public-keys = cache.internal:<PUBLIC_KEY> cache.nixos.org-1:...
```

---

## 🔄 Автоматический push в кеш

### post-build-hook (простой, но блокирующий)

```bash
#!/bin/sh
# /etc/nix/upload-to-cache.sh
set -eu
set -f
export IFS=' '
echo "Uploading $OUT_PATHS"
exec nix copy --to "http://cache.internal:5000" $OUT_PATHS
```

```nix
# nix.conf
post-build-hook = /etc/nix/upload-to-cache.sh
secret-key-files = /etc/nix/cache-priv-key.pem
```

> ⚠️ **Проблема**: hook блокирует build loop! Медленный upload = медленный build.

### nix-post-build-hook-queue (лучше!) ⭐

**GitHub**: [newAM/nix-post-build-hook-queue](https://github.com/newAM/nix-post-build-hook-queue)

Фоновый daemon: paths передаются через systemd socket, upload в фоне:

```nix
services.nix-post-build-hook-queue = {
  enable = true;
  cache = "http://cache.internal:5000";
  signingKeyFile = "/etc/nix/cache-priv-key.pem";
};
```

- ✅ Не блокирует сборку
- ✅ Подписывает и пушит в фоне
- ✅ systemd socket activation

---

## 🔵 magic-nix-cache-action (для Варианта 1)

```yaml
- uses: DeterminateSystems/magic-nix-cache-action@main
```

Что делает под капотом:
1. Запускает локальный HTTP-сервер как Nix substituter
2. Перехватывает store paths
3. Сохраняет в GitHub Actions Cache (до 10 GB)
4. При следующем run — восстанавливает из кеша

- ✅ Бесплатно, open-source
- ✅ Не нужен внешний сервис
- ⚠️ 10 GB лимит на репо
- ⚠️ Только для GitHub-hosted runners

---

## 🧮 Что кешировать, а что нет

### ✅ Кешировать в ПУБЛИЧНЫЙ кеш:
- Всё из nixpkgs (Python, Node.js, bash, coreutils...) — уже закешировано на cache.nixos.org
- nix-community пакеты — закешированы на nix-community.cachix.org

### ✅ Кешировать в ПРИВАТНЫЙ кеш (Attic/Harmonia):
- Наш собранный Python venv (из uv.lock)
- Наши node_modules (из bun.lockb)
- OCI-образы (JSON манифесты nix2container)
- Кастомные деривейшны

### ❌ НЕ кешировать в публичный кеш:
- Наш исходный код (app source)
- Конфиги с секретами
- Приватные зависимости

---

## 📊 Влияние кеширования на время сборки

| Сценарий | Без кеша | С публичным | + приватный | + store |
|----------|----------|-------------|-------------|---------|
| Python app (20 deps) | 8-12 мин | 3-5 мин | 1-2 мин | **10-30s** |
| JS app (Bun, 50 deps) | 5-8 мин | 2-4 мин | 30s-1 мин | **5-15s** |
| Только код изменён | 3-5 мин | 1-2 мин | 20-40s | **5-10s** |

> 🔥 Персистентный /nix/store (self-hosted) + приватный кеш = **секунды**.
