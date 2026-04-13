# 🔍 Анализ CI/CD AutoPosterMonolith — текущее состояние

> Разбор существующей реализации CI/CD через Nix в боевом проекте.
> Что работает, что костыли, что взять за основу для шаблона.

---

## 📋 Паспорт проекта

| Параметр | Значение |
|----------|----------|
| 📂 Путь | `../AutoPosterMonolith/` |
| 🐍 Язык / Runtime | Python 3.14 |
| 📦 Package manager | uv (lockfile: `uv.lock`) |
| 🔧 Nix интеграция | uv2nix (pyproject-nix) → nix2container |
| 🐳 Регистр | GHCR (`ghcr.io`) |
| 🚀 Деплой | Kubernetes (SSH → kubectl) |
| 🏃 Runner | Self-hosted (`Linux` label) |
| 🔀 Ветки | `test` → stage-образ, `prod` → prod-образ |

---

## 🏗️ Как устроен flake.nix

### 📥 Граф зависимостей

```
inputs:
  nixpkgs (unstable)
  ├── pyproject-nix       → базовый Python build framework
  │   └── uv2nix          → парсит uv.lock → Nix деривейшны
  │       └── pyproject-build-systems → wheel build systems
  └── nix2container        → сборка OCI без Docker
```

> 💡 **Ключевое**: uv2nix читает `uv.lock` и генерирует Python-деривейшны.
> nix2container собирает из них OCI-образ.

### 🐍 Python venv через uv2nix

```nix
workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

# Два варианта virtualenv:
venvProd  = pythonSet.mkVirtualEnv "autoposter-prod-env"
  (workspace.deps.default // { autopost-bot = [ "prod" ]; });

venvStage = pythonSet.mkVirtualEnv "autoposter-stage-env"
  workspace.deps.all;
```

- `sourcePreference = "wheel"` — предпочитает бинарные wheel (меньше оверрайдов)
- Два окружения из одного `uv.lock`: prod (PostgreSQL) и stage (все extras)

### 🔧 Кастомные оверрайды пакетов

| Пакет | Проблема | Решение |
|-------|----------|---------|
| `pillow` | Нужны системные библиотеки (libjpeg, zlib...) | `buildInputs += [libjpeg zlib freetype lcms2 libtiff libwebp]` |
| `pyaes` | Нет pyproject.toml, legacy setup.py | `nativeBuildInputs += [setuptools]` |
| `autopost-bot` (наш пакет) | Изменение кода → пересборка всего venv | Decoupled: только pyproject.toml metadata в venv, код через PYTHONPATH |
| `piccolo-admin/api` | Конфликт директорий `e2e/` между пакетами | `rm -rf $out/lib/python*/site-packages/e2e` в postInstall |

> ⚠️ Это **главная боль uv2nix**: каждый пакет с C-зависимостями или legacy build system
> требует ручного оверрайда. Выбор `sourcePreference = "wheel"` минимизирует это,
> но не устраняет полностью. Для шаблона нужна коллекция типовых оверрайдов.

### 🐳 Сборка OCI-образа — трёхслойная архитектура

```nix
layers = [
  (n2c.buildLayer { deps = runtimeDeps; })           # 📦 runtime: bash, coreutils, cacert, tzdata
  (n2c.buildLayer { deps = [ venv ]; maxLayers = 1; })# 📦 Python venv: все pip-зависимости
  (n2c.buildLayer { deps = [ appSrc ]; })             # 📦 App source: src/, scripts/, pyproject.toml
];
```

**Почему это хорошо:**
```
┌───────────────────────────────────────────────┐
│ Слой 3: appSrc (~5 MB)              🔴 часто │ ← push ~10s
├───────────────────────────────────────────────┤
│ Слой 2: Python venv (~200 MB)        🟡 редко│ ← push только при pip add/remove
├───────────────────────────────────────────────┤
│ Слой 1: runtime deps (~50 MB)        🟢 почти│ ← push почти никогда
│                                       никогда │
└───────────────────────────────────────────────┘
```

При изменении только кода приложения → пересобирается и пушится ТОЛЬКО слой 3.
skopeo проверяет наличие слоёв в registry и пропускает уже загруженные.

### 📤 Хитрый push в GHCR

```bash
# 1️⃣ nix: → oci: (локальный OCI layout с кешем блобов)
skopeo copy nix:./result "oci:${OCI_DIR}:${TAG}"

# 2️⃣ oci: → docker:// (push ветка-тег, только новые слои)
skopeo copy "oci:${OCI_DIR}:${TAG}" "docker://${IMAGE}:${TAG}"

# 3️⃣ Тот же образ → SHA-тег (manifest-only, 0 трафика)
skopeo copy "oci:${OCI_DIR}:${TAG}" "docker://${IMAGE}:${SHA}"

# 4️⃣ Re-tag :latest через GHCR REST API (manifest-only, 0 трафика)
curl -X PUT ... "https://ghcr.io/v2/.../manifests/latest"
```

> 💡 SHA-теги дают immutable деплои: `imagePullPolicy: IfNotPresent` в K8s
> означает что containerd скачает только изменённые слои.

---

## 🔄 Workflow: nix-build.yaml

### 📊 Полная схема пайплайна

```
git push (test|prod)
        │
        ▼
┌─ Job: build-and-push ──────────────────────┐
│  1. checkout                                │
│  2. Determine variant (prod/stage)          │
│  3. nix build .#oci-{variant}               │
│     --max-jobs auto --cores 0               │
│     | nix-output-monitor                    │
│  4. nix build .#push-tools                  │
│  5. skopeo push → GHCR                      │
│     (branch tag + SHA tag + :latest)        │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌─ Job: deploy ───────────────────────────────┐
│  SSH → kubectl set image (test)             │
│  SSH → kubectl rollout restart (prod)       │
│  - Phase 1: userbot + publisher (parallel)  │
│  - Phase 2: backend                         │
│  - Phase 3: bot                             │
└─────────────────────────────────────────────┘
```

### 🏃 Runner

- `runs-on: Linux` — self-hosted runner с NixOS
- Nix store **персистентный** → повторные сборки быстрые
- ⚠️ Нет явного кеш-сервера (Attic/Harmonia) — только локальный store

### 🛠️ Ещё в проекте

| Workflow | Что делает | Runner |
|----------|-----------|--------|
| `ruff.yml` | Линтер Python (через `nix shell nixpkgs#ruff`) | Self-hosted |
| `prod.yaml` | 🦕 Legacy Docker build (ветка `prod-docker-legacy`) | Self-hosted |
| `test.yaml` | 🦕 Legacy Docker build (ветка `test-docker-legacy`) | Self-hosted |
| `ai-review.yml` | AI code review через Cursor Cloud Agents | Self-hosted |
| `ai-pr-description.yml` | AI описание PR | Self-hosted |
| `ai-commands.yml` | Команды `/ai review`, `/ai describe` | Self-hosted |

---

## 🦴 Инвентарь костылей

### 🔴 Критичные (нужно исправить в шаблоне)

| # | Костыль | Проблема | Решение для шаблона |
|---|---------|----------|---------------------|
| 1 | Нет кеш-сервера | Локальный store — единая точка отказа | Attic или Harmonia |
| 2 | Ручные Python оверрайды | Каждый пакет с C-deps — ручная работа | Коллекция типовых оверрайдов + sourcePreference=wheel |
| 3 | curl+jq для retag latest | Скрипт прибит к GHCR API | Вынести в переиспользуемый push.sh |
| 4 | SSH+kubectl деплой | Нет GitOps, ручной SSH | Ок для MVP, но упомянуть nixidy/ArgoCD |

### 🟡 Некритичные (можно улучшить)

| # | Костыль | Что можно лучше |
|---|---------|-----------------|
| 5 | Двухэтапный OCI push | Для простых случаев хватит прямого `nix: → docker://` |
| 6 | nix-output-monitor через pipe | Можно встроить в flake как devShell утилиту |
| 7 | Нет matrix builds | Сейчас один образ — ок, но для multi-arch нужен matrix |

### ✅ Хорошие решения (взять за основу)

| # | Что | Почему хорошо |
|---|-----|---------------|
| 1 | Трёхслойный образ | Инкрементальные push, быстрые деплои |
| 2 | SHA-теги | Иммутабельность, `IfNotPresent` в K8s |
| 3 | uv2nix из uv.lock | Воспроизводимый Python env |
| 4 | `--max-jobs auto --cores 0` | Утилизация всех ресурсов |
| 5 | prod/stage из одного flake | DRY |
| 6 | Decoupled app source от venv | Изменение кода не пересобирает venv |
| 7 | push-tools как Nix пакет | Skopeo+curl+jq — детерминированный набор |
