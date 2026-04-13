# 🐳 Сборка OCI-образов через Nix — nix2container, nix-oci, dockerTools

> Полный разбор инструментов для сборки контейнерных образов из Nix.
> Без Docker daemon, с инкрементальными push и контролем слоёв.

---

## 📊 Сравнение инструментов

| | `dockerTools.buildImage` | `dockerTools.streamLayeredImage` | **nix2container** | **nix-oci** |
|--|--------------------------|----------------------------------|-------------------|-------------|
| 📦 Tarball в /nix/store | ✅ Да, весь образ | ✅ Стримится | ❌ Нет! JSON-манифест | ❌ Нет (обёртка n2c) |
| ⚡ Rebuild/repush | ~10s | ~7.5s | **~1.8s** 🚀 | ~1.8s (через n2c) |
| 🔄 Пропуск existing layers | ❌ | ❌ | ✅ | ✅ |
| 🔧 Контроль слоёв | ⚠️ Один слой | maxLayers (авто) | Полный ручной + авто | Декларативный |
| 📖 Часть nixpkgs | ✅ | ✅ | ❌ Внешний input | ❌ Внешний input |
| 🔒 Perms без root/VM | ❌ runAsRoot(VM!) | ❌ | ✅ perms attr | ✅ non-root default |
| 🛡️ Security scanning | ❌ | ❌ | ❌ | ✅ Grype + Trivy |
| 🧩 flake-parts | ❌ | ❌ | ❌ | ✅ нативный модуль |
| ⭐ GitHub stars | — (nixpkgs) | — (nixpkgs) | 815 | 89 |

> 💡 **Вердикт**: nix2container — основной инструмент. nix-oci — высокоуровневая обёртка через flake-parts, если хочется декларативности и security scanning.

---

## 🏗️ nix2container — глубокий разбор

### 🔬 Как это работает внутри

```
flake.nix (buildImage)
       │
       ▼
Go binary генерирует JSON:
  - описание слоёв (store paths → layer tarballs)
  - OCI config (entrypoint, env, etc.)
  - НЕ создаёт tarballs!
       │
       ▼
Skopeo с nix-транспортом (patched):
  - читает JSON
  - на лету создаёт layer tarballs из /nix/store
  - пушит только изменённые слои в registry
  - или конвертирует в OCI layout / docker-archive
```

> 🎯 Ключевая идея: tarball слоя НЕ записывается в /nix/store.
> Skopeo создаёт его на лету при push. Это экономит место и время.

### 📦 buildImage — полный API

```nix
nix2container.buildImage {
  name = "myapp";                    # 🏷️ Имя образа
  tag = "v1.0";                      # По умолчанию = хеш содержимого

  # 📁 Корневая файловая система контейнера
  copyToRoot = pkgs.buildEnv {
    name = "root";
    paths = [ pkgs.bashInteractive pkgs.coreutils ];
    pathsToLink = [ "/bin" "/etc" ];
  };

  # 🖼️ Базовый образ (опционально)
  fromImage = nix2container.pullImageFromManifest {
    imageName = "docker.io/library/alpine";
    imageManifest = ./alpine-manifest.json;
  };

  # 📦 Явные слои — САМОЕ ВАЖНОЕ для кеширования!
  layers = [
    (nix2container.buildLayer { deps = [ pkgs.bash pkgs.coreutils ]; })
    (nix2container.buildLayer { deps = [ pythonVenv ]; maxLayers = 1; })
    (nix2container.buildLayer { deps = [ appSource ]; })
  ];

  # 📐 Авто-разбиение оставшихся paths (кроме explicit layers)
  maxLayers = 10;  # default = 1, лимит overlay fs = 128

  # 🐳 OCI config
  config = {
    Entrypoint = [ "${pkgs.bash}/bin/bash" "/app/start.sh" ];
    Cmd = [ "--port" "8080" ];
    Env = [ "PATH=/bin" "LANG=C.UTF-8" ];
    WorkingDir = "/app";
    ExposedPorts = { "8080/tcp" = {}; };
    Labels = { "org.opencontainers.image.source" = "https://github.com/..."; };
    User = "1000:1000";
  };

  # 🔒 Права доступа (БЕЗ root, БЕЗ VM!)
  perms = [{
    path = "/app/scripts";
    regex = ".*\\.sh";
    mode = "0755";
  }];

  # 🗃️ Инициализировать Nix DB (для CI-образов где нужен nix внутри)
  initializeNixDatabase = false;
}
```

### 📦 buildLayer — контроль слоёв

```nix
nix2container.buildLayer {
  deps = [ pkgs.python3 myVenv ];     # Store paths для включения

  # Или скопировать в корень (без /nix/store/ префикса)
  copyToRoot = pkgs.buildEnv { ... };

  # Для не-reproducible зависимостей (tarball в store)
  reproducible = true;

  maxLayers = 1;  # Не дробить этот слой

  layers = [ ... ];  # Вложенные слои для дедупликации

  # Исключить path (например, OCI config)
  ignore = someDerivation;
}
```

### 🖼️ pullImage vs pullImageFromManifest

```nix
# ❌ pullImage — весь образ в одном store path, нужен narhash
fromImage = nix2container.pullImage {
  imageName = "docker.io/library/alpine";
  imageDigest = "sha256:abc123...";
  sha256 = "sha256-xxxxx...";  # narhash — нужно вычислить вручную!
};

# ✅ pullImageFromManifest — ЛУЧШЕ
# - Каждый слой = отдельный store path (дедупликация!)
# - manifest.json как lockfile в git
# - Обновление = только перекачать manifest.json
fromImage = nix2container.pullImageFromManifest {
  imageName = "docker.io/library/alpine";
  imageManifest = ./alpine-manifest.json;
  imageTag = "3.19";
};

# Обновить manifest:
# nix run .#myimage.fromImage.getManifest > alpine-manifest.json
```

---

## 🎯 Паттерн слоёв для наших проектов

### 🐍 Python (uv) — 3 слоя

```nix
layers = [
  # 🟢 Слой 1: System runtime — меняется КРАЙНЕ редко
  # bash, coreutils, cacert, tzdata, libxml2...
  (n2c.buildLayer { deps = runtimeDeps; })

  # 🟡 Слой 2: Python venv — меняется при uv add/remove
  # Все pip-зависимости в одном слое
  (n2c.buildLayer { deps = [ venv ]; maxLayers = 1; })

  # 🔴 Слой 3: App source — меняется каждый коммит
  # src/, scripts/, pyproject.toml, piccolo_conf.py
  (n2c.buildLayer { deps = [ appSrc ]; })
];
```

### 🟢 JS (Bun) — 3 слоя

```nix
layers = [
  # 🟢 Слой 1: Bun runtime + system deps
  (n2c.buildLayer { deps = [ pkgs.bun pkgs.cacert pkgs.bash ]; })

  # 🟡 Слой 2: node_modules (из bun2nix)
  (n2c.buildLayer { deps = [ nodeModules ]; maxLayers = 1; })

  # 🔴 Слой 3: App source
  (n2c.buildLayer { deps = [ appSrc ]; })
];
```

### 🟢 JS (Node.js) — 3 слоя

```nix
layers = [
  # 🟢 Слой 1: Node.js runtime + system deps
  (n2c.buildLayer { deps = [ pkgs.nodejs pkgs.cacert pkgs.bash ]; })

  # 🟡 Слой 2: node_modules (из dream2nix / node2nix)
  (n2c.buildLayer { deps = [ nodeModules ]; maxLayers = 1; })

  # 🔴 Слой 3: App source
  (n2c.buildLayer { deps = [ appSrc ]; })
];
```

### ⚠️ Борьба с дупликатами в слоях

Проблема: если pkgs.bash есть и в Слое 1, и в Слое 2 (через зависимости venv),
он будет включён дважды → ~40% waste вместо 100% efficiency.

Решение из [блога Peter Kolloch](https://blog.eigenvalue.net/2023-nix2container-everything-once/):
```nix
# Слой 2 знает о Слое 1 → пропускает общие paths
(n2c.buildLayer {
  deps = [ venv ];
  layers = [ layer1 ];  # ← "вычесть" paths из Слоя 1
})
```

---

## 📤 Паттерны push

| Метод | Команда | Когда использовать |
|-------|---------|-------------------|
| Прямой push | `nix run .#img.copyToRegistry` | Простые случаи |
| Docker daemon | `nix run .#img.copyToDockerDaemon` | Локальная разработка |
| Podman | `nix run .#img.copyToPodman` | Без Docker |
| Skopeo nix→docker | `skopeo copy nix:./result docker://...` | CI с auth |
| Двухэтапный (OCI layout) | `nix:→oci: → docker://` | Multi-tag, retag |

---

## 🧩 nix-oci (flake-parts модуль)

Высокоуровневая абстракция над nix2container + security scanning.

```nix
# flake.nix с flake-parts + nix-oci
{
  inputs.nix-oci.url = "github:Dauliac/nix-oci";

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } {
    imports = [ inputs.nix-oci.flakeModules.default ];

    perSystem = { pkgs, ... }: {
      oci.containers = {
        myapp = {
          package = myAppDerivation;
          # Автоматически:
          # - non-root user
          # - минимальная ФС
          # - CVE scan (Grype)
          # - credential leak detection (Trivy)
        };
      };
    };
  };
}
```

**Плюсы:**
- ✅ Декларативно и компактно
- ✅ Security scanning из коробки
- ✅ non-root по умолчанию
- ✅ Debug-варианты образов

**Минусы:**
- ⚠️ Ещё молодой проект (89 ⭐)
- ⚠️ Меньше контроля чем прямой nix2container

---

## 🔐 Аутентификация для pull приватных base images

```bash
# На CI-сервере (self-hosted runner):
sudo mkdir -p /etc/nix/skopeo
sudo cp ~/.docker/config.json /etc/nix/skopeo/auth.json
sudo chmod -R g+rx /etc/nix/skopeo
sudo chgrp -R nixbld /etc/nix/skopeo

# В nix.conf:
extra-sandbox-paths = /etc/skopeo/auth.json=/etc/nix/skopeo/auth.json
```

---

## 📊 Сравнение с Docker + Habr бенчмарк (Сбер)

По данным [статьи Сбера на Habr](https://habr.com/ru/companies/sber/articles/896190/):

| Тест | Docker | Nix | Nix/Docker ratio |
|------|--------|-----|-----------------|
| Конфигурация cmd | 0.6s | 7.2s | **12x медленнее** ⚠️ |
| Установка пакетов | 37.4s | **33.2s** | **0.9x быстрее** ✅ |
| Копирование больших файлов | 12.6s | 45.2s | **3.6x медленнее** ⚠️ |
| Копирование мелких файлов | 4.1s | 12.9s | **3.1x медленнее** ⚠️ |
| Произвольная команда (runAsRoot) | 1.2s | 173s | **147x!** ☠️ |
| Произвольная команда (extraCommands) | 1.1s | 7.8s | **7x медленнее** ⚠️ |

> ⚠️ **Важно**: это бенчмарки `dockerTools`, а НЕ `nix2container`!
> nix2container гораздо быстрее за счёт отсутствия tarball и инкрементальности.
> Но общий вывод: Nix-сборка медленнее Docker для "грязных" операций (runAsRoot, COPY).
> Зато быстрее для установки пакетов и великолепен для инкрементальных push.

### 🎯 Когда Nix выигрывает у Docker:

1. ✅ **Инкрементальные push** — только изменённые слои (nix2container)
2. ✅ **Воспроизводимость** — тот же flake.lock = тот же образ
3. ✅ **Установка пакетов** — свой пакетный менеджер без overhead контейнера
4. ✅ **Нет Docker daemon** — можно собирать в любом sandbox
5. ✅ **Гранулярные слои** — ручной контроль что в каком слое

### 🎯 Когда Docker выигрывает:

1. ✅ **Произвольные команды** — `RUN apt-get install ...` быстрее
2. ✅ **COPY** — копирование файлов быстрее
3. ✅ **Простота** — порог входа ниже
4. ✅ **Экосистема** — больше готовых образов и инструментов
