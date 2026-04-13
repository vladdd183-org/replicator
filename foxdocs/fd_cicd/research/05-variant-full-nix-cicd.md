# 🧪 Вариант 3: Полностью Nix CI/CD

> Nix не только собирает, но и **управляет** пайплайном.
> Главный challenge: как показать логи и статусы в GitHub UI?

---

## 🎯 Концепция

Вместо GitHub Actions workflow (YAML) — CI логика определена в Nix:
- `.#checks` — то что нужно проверить
- `.#packages` — то что нужно собрать
- `om ci` / buildbot-nix — оркестрирует сборку
- GitHub Checks API / Commit Status API — отображает результат

---

## 🔧 Инструменты для полностью Nix CI

### 1️⃣ buildbot-nix ⭐ (рекомендуется для self-hosted)

**GitHub**: [nix-community/buildbot-nix](https://github.com/nix-community/buildbot-nix) (248 ⭐)
**Maintainers**: @Mic92, @MagicRB

NixOS модуль, который превращает Buildbot в полноценный Nix CI:

```
Push / PR → GitHub webhook → Buildbot → nix-eval-jobs → nix build → GitHub Status
```

**Фичи:**
- ✅ Быстрая параллельная evaluation через `nix-eval-jobs`
- ✅ **GitHub интеграция**: PR статусы, логин через GitHub
- ✅ **Gitea интеграция**: тоже поддерживается!
- ✅ Shared /nix/store между builds
- ✅ Build matrix из `.#checks`
- ✅ Все builds в Nix sandbox (безопасно)
- ✅ Remote builders для multi-arch
- ✅ Экспериментальная поддержка Hercules CI effects (impure steps: деплой)
- ✅ Open-source, self-hosted, бесплатно

**NixOS конфиг:**
```nix
services.buildbot-nix = {
  master = {
    enable = true;
    github = {
      webhookSecretFile = "/run/secrets/buildbot-github-webhook";
      oauthSecretFile = "/run/secrets/buildbot-github-oauth";
      # GitHub App для status checks
      appId = 12345;
      appSecretKeyFile = "/run/secrets/buildbot-github-app-key";
    };
    # Проекты для мониторинга
    projects = {
      "myorg/myrepo" = {
        defaultBranch = "main";
      };
    };
  };
  worker = {
    enable = true;
    # Workers на том же или отдельных серверах
  };
};
```

**Как это выглядит в GitHub:**
```
PR #42: Add new feature
  ✅ buildbot/nix-eval    — 5s
  ✅ buildbot/packages.x86_64-linux.myapp — 45s
  ✅ buildbot/checks.x86_64-linux.lint — 12s
  ❌ buildbot/checks.x86_64-linux.test — 1m 23s (FAILED)
```

> 💡 buildbot-nix — самый зрелый вариант полностью Nix CI для self-hosted.
> Используется самим nix-community для инфраструктуры.

### 2️⃣ om ci (Omnix) — CLI-подход

**GitHub**: [juspay/omnix](https://github.com/juspay/omnix)
**Docs**: [omnix.page](https://omnix.page/om/ci.html)

CLI утилита для запуска CI из flake. Не CI-платформа, а инструмент:

```bash
# Собрать всё из flake (packages, checks, devShells, nixosConfigurations...)
om ci run

# Собрать конкретный sub-flake
om ci run .#default.backend

# Собрать remote repo
om ci run github:myorg/myrepo

# Собрать GitHub PR
om ci run https://github.com/myorg/myrepo/pull/42

# Собрать удалённо по SSH
om ci run --on ssh://builder@myserver ~/code/myproject
```

**Для GitHub Actions:**
```yaml
# Минимальный шаг — запускает om ci из flake
- name: Install omnix
  run: nix profile install nixpkgs#omnix
- run: om ci
```

**GitHub Actions matrix:**
```yaml
# om ci gh-matrix генерирует matrix JSON
- id: set-matrix
  run: |
    MATRIX="$(om ci gh-matrix --systems=x86_64-linux,aarch64-linux | jq -c .)"
    echo "matrix=$MATRIX" >> $GITHUB_OUTPUT
```

**Плюсы:**
- ✅ CI логика в flake, не в YAML
- ✅ Автоматически собирает все flake outputs
- ✅ Remote execution по SSH
- ✅ Result JSON для cachix push / closure tracking

**Минусы:**
- ⚠️ Не CI-платформа — нужен внешний триггер (GitHub Actions, cron, webhook)
- ⚠️ Нет встроенного GitHub status reporting

### 3️⃣ Гибридный подход: Minimal GitHub Action + Nix-native build

**Идея**: один тонкий GitHub workflow запускает Nix-команду на self-hosted runner:

```yaml
name: Nix CI
on: [push, pull_request]

jobs:
  ci:
    runs-on: nix-builder
    steps:
      - uses: actions/checkout@v4
      - name: Run all checks
        run: om ci run
      - name: Build and push OCI
        if: github.ref == 'refs/heads/main'
        run: |
          nix build .#oci-prod
          # push logic...
```

Это **де-факто Вариант 2 + om ci** — CI логика в Nix, GitHub Actions как триггер и UI.

---

## 🤔 Проблема: как показать логи в GitHub?

### Подход A: Minimal GitHub Action (рекомендуется) ✅

Один step в GitHub Actions, всё остальное в Nix:
- ✅ Логи видны в GitHub Actions UI
- ✅ Статус check — из exit code job
- ✅ Просто

### Подход B: GitHub Checks API (для buildbot-nix) ✅

Buildbot создаёт Check Runs через GitHub App:
```
POST /repos/{owner}/{repo}/check-runs
{
  "name": "nix-build/mypackage",
  "head_sha": "abc123",
  "status": "in_progress",
  "output": { "title": "Building...", "summary": "..." }
}
```
Потом обновляет с результатом:
```
PATCH /repos/{owner}/{repo}/check-runs/{id}
{
  "status": "completed",
  "conclusion": "success",
  "output": { "title": "Build passed", "summary": "Built in 45s" }
}
```

- ✅ Детальные статусы для каждого derivation
- ✅ Аннотации к строкам кода (для linter)
- ⚠️ Требует GitHub App с `checks:write`

### Подход C: Commit Status API (попроще)

```bash
curl -X POST "https://api.github.com/repos/OWNER/REPO/statuses/SHA" \
  -H "Authorization: token $TOKEN" \
  -d '{
    "state": "success",
    "target_url": "https://buildbot.myserver.com/builds/123",
    "description": "Build passed in 45s",
    "context": "nix-ci/build"
  }'
```

- ✅ Проще чем Checks API
- ✅ Достаточно `repo:status` scope
- ⚠️ Менее детальные статусы

### Подход D: repository_dispatch (внешний триггер)

Nix build server слушает webhook, собирает, отправляет статус:
```
GitHub webhook → ваш сервер → nix build → GitHub Status API
```

- ✅ Полный контроль
- ⚠️ Нужно писать webhook handler
- ⚠️ buildbot-nix уже делает это из коробки!

---

## 📊 Сравнение подходов

| | Minimal GH Action | buildbot-nix | om ci + GH Action | Чистый webhook |
|-|-------------------|-------------|-------------------|----------------|
| 📖 Сложность настройки | 🟢 Простая | 🟡 Средняя | 🟢 Простая | 🔴 Сложная |
| 📊 Логи в GitHub | ✅ Actions UI | ✅ Checks API + ссылка на Buildbot | ✅ Actions UI | ⚠️ Только ссылка |
| 🔧 CI логика | YAML + Nix | Nix (.#checks) | Nix (flake) | Nix |
| ⚡ Скорость | Зависит от runner | Быстрая (shared store) | Зависит от runner | Быстрая |
| 🔄 Триггеры | GitHub events | Webhooks | Любые | Custom |
| 🏗️ Инфраструктура | Runner | Buildbot server | Runner | Custom server |
| 🛡️ Безопасность | GitHub secrets | sops-nix + Nix sandbox | GitHub secrets | Полный контроль |

---

## 💡 Мой рекомендуемый подход для Варианта 3

**buildbot-nix** для команд с инфраструктурой:
1. NixOS сервер с buildbot-nix
2. GitHub App для webhooks + status checks
3. `.#checks` и `.#packages` определяют что собирать
4. Attic/Harmonia как кеш-сервер
5. Remote builders для multi-arch

**om ci + Minimal GH Action** для простого старта:
1. Self-hosted runner с NixOS
2. `om ci run` в одном GitHub Actions step
3. Результаты видны в Actions UI
4. Постепенная миграция на buildbot-nix при необходимости

---

## ✅ Когда выбирать

- 🏗️ Большая команда с DevOps-экспертизой
- 🔧 Хочется CI-as-Code (Nix, не YAML)
- 📦 Monorepo с множеством outputs
- 🔄 Multi-arch builds (x86_64 + aarch64)
- 🛡️ Максимальная безопасность и изоляция

## ❌ Когда НЕ подходит

- 🏃 Нужно быстро запуститься (Вариант 1 проще)
- 👤 Маленькая команда без DevOps
- 📖 Нет опыта с Nix (высокий порог входа)
