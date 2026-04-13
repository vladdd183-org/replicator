# Виртуальные Check Runs: Одна джоба, красивый UI в GitHub

> Дата: 2026-04-10
> Контекст: GitHub Actions job overhead составляет ~9-14s на каждую джобу (Set up job + checkout + Complete job).
> При реальной работе Nix в ~7s это >50% overhead.
> Цель: одна быстрая джоба, но красивое отображение отдельных чеков в PR UI.

---

## 1. Проблема: Job Overhead

Каждая GitHub Actions джоба имеет фиксированный overhead:

```
┌─────────────────────────────────────────────────┐
│ Job "Check & Build" (total: 16s)                │
│                                                 │
│ [Set up job]        ~3-5s   ← скачать actions,  │
│                              подготовить workspace│
│ [actions/checkout]  ~2-3s   ← Node.js runtime + │
│                              git init+fetch      │
│ [Nix work]          ~7s     ← РЕАЛЬНАЯ РАБОТА   │
│ [Complete job]      ~1-2s   ← cleanup, logs     │
└─────────────────────────────────────────────────┘

Overhead: ~9s из 16s = 56%

Если 2 джобы: overhead × 2 = ~18s на пустом месте
Если 3 джобы: overhead × 3 = ~27s...
```

### Источники overhead на self-hosted runner (runs-on: [nix])

| Фаза | Что происходит | Время |
|-------|---------------|-------|
| Set up job | GitHub API: получить task, скачать action archives (.tar.gz), распаковать, подготовить env | 3-5s |
| actions/checkout@v4 | Запуск Node.js 20 runtime, `git init`, `git remote add`, `git fetch --depth=1`, `git checkout` | 2-3s |
| Post checkout | Cleanup git credentials, отправка логов | 0.5-1s |
| Complete job | Финализация, отправка статуса | 0.5-1s |

---

## 2. Решение: GitHub Check Runs API

### Что такое Check Runs

GitHub Check Runs — API для создания отдельных "проверок" привязанных к коммиту.
Каждый check run имеет:
- **name** — отображается в PR
- **status** — `queued`, `in_progress`, `completed`
- **conclusion** — `success`, `failure`, `neutral`, `cancelled`, `timed_out`
- **output** — markdown summary, аннотации к файлам

Они отображаются в PR UI точно так же, как отдельные джобы.

### Ключевое: GITHUB_TOKEN может создавать Check Runs

Несмотря на то что документация говорит "only GitHub Apps can create check runs",
`GITHUB_TOKEN` в Actions workflow МОЖЕТ создавать check runs если добавить:

```yaml
permissions:
  checks: write
```

Это работает потому что GitHub Actions workflow token — это фактически GitHub App
installation token (GitHub Actions app), который имеет `checks:write` capability.

### Доступные actions

| Action | Stars | Описание |
|--------|-------|----------|
| [dflydev/check-runs-action](https://github.com/dflydev/check-runs-action) | 15 | Специализирован на pattern prepare→update→complete |
| [LouisBrunner/checks-action](https://github.com/LouisBrunner/checks-action) | 262 | Полный wrapper вокруг Checks API, поддержка аннотаций |

---

## 3. Оптимизированный workflow

### 3.1 Замена actions/checkout на git clone

`actions/checkout@v4` — это Node.js action, который запускает полный Node.js runtime
только чтобы выполнить `git init + git fetch + git checkout`. На self-hosted runner
где git уже установлен, это можно заменить на 1 строку:

```yaml
# Вместо:
- uses: actions/checkout@v4  # ~2-3s (Node.js overhead)

# Используем:
- run: git clone --depth=1 --single-branch "https://github.com/$GITHUB_REPOSITORY" . || git fetch --depth=1 && git checkout "$GITHUB_SHA"
  # ~0.3-0.5s (native git)
```

Для PR нужен чуть более сложный вариант:
```bash
git init
git remote add origin "https://github.com/${GITHUB_REPOSITORY}.git"
git fetch --depth=1 origin "${GITHUB_SHA}"
git checkout FETCH_HEAD
```

**Экономия**: ~2s на каждую джобу.

### 3.2 Объединение джоб + Check Runs

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  checks: write
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  NIX_FLAGS: "--accept-flake-config"

jobs:
  ci:
    name: "CI/CD"
    runs-on: [nix]
    steps:
      - name: Checkout (fast)
        run: |
          git init
          git remote add origin "https://github.com/${GITHUB_REPOSITORY}.git"
          git fetch --depth=1 origin "$GITHUB_SHA"
          git checkout FETCH_HEAD

      # ── Prepare virtual checks ──
      - name: Prepare Check Runs
        uses: dflydev/check-runs-action@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          checks: |
            [
              { "id": "fmt",   "name": "✅ Format" },
              { "id": "check", "name": "✅ Flake Check" },
              { "id": "build", "name": "📦 Build OCI" },
              { "id": "push",  "name": "🚀 Push to GHCR" }
            ]
          status: "queued"

      # ── Format ──
      - uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: fmt, status: in_progress }
      - name: Format
        id: step_fmt
        continue-on-error: true
        run: nix fmt $NIX_FLAGS -- --ci
      - if: always()
        uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: fmt, conclusion: "${{ steps.step_fmt.outcome }}" }

      # ── Flake Check ──
      - uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: check, status: in_progress }
      - name: Flake Check
        id: step_check
        continue-on-error: true
        run: nix flake check --no-build $NIX_FLAGS
      - if: always()
        uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: check, conclusion: "${{ steps.step_check.outcome }}" }

      # ── Build OCI ──
      - uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: build, status: in_progress }
      - name: Build OCI
        id: step_build
        continue-on-error: true
        run: nix build .#oci-prod $NIX_FLAGS
      - if: always()
        uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: build, conclusion: "${{ steps.step_build.outcome }}" }

      # ── Push to GHCR (only on main push) ──
      - uses: dflydev/check-runs-action@v1
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: push, status: in_progress }
      - name: Push to GHCR
        id: step_push
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        continue-on-error: true
        env:
          REGISTRY_AUTH_FILE: /tmp/skopeo-auth.json
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | \
            nix run .#skopeo $NIX_FLAGS -- login $REGISTRY -u ${{ github.actor }} --password-stdin

          IMG=$(nix build .#oci-prod $NIX_FLAGS --print-out-paths --no-link)
          REPO="${IMAGE_NAME,,}"
          SHORT="${GITHUB_SHA:0:7}"

          nix run .#skopeo $NIX_FLAGS -- --insecure-policy copy \
            "nix:$IMG" "docker://${REGISTRY}/${REPO}:${SHORT}"
          nix run .#skopeo $NIX_FLAGS -- --insecure-policy copy \
            "nix:$IMG" "docker://${REGISTRY}/${REPO}:latest"

      - if: always() && github.event_name == 'push' && github.ref == 'refs/heads/main'
        uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: push, conclusion: "${{ steps.step_push.outcome }}" }
      - if: always() && !(github.event_name == 'push' && github.ref == 'refs/heads/main')
        uses: dflydev/check-runs-action@v1
        with: { token: "${{ secrets.GITHUB_TOKEN }}", id: push, conclusion: "skipped" }

      # ── Summary ──
      - name: Summary
        if: always()
        run: |
          echo "## CI/CD Results" >> $GITHUB_STEP_SUMMARY
          echo "| Check | Result |" >> $GITHUB_STEP_SUMMARY
          echo "|-------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Format | ${{ steps.step_fmt.outcome }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Flake Check | ${{ steps.step_check.outcome }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Build OCI | ${{ steps.step_build.outcome }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Push GHCR | ${{ steps.step_push.outcome || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY

      # ── Fail if anything failed ──
      - name: Gate
        if: always()
        run: |
          [[ "${{ steps.step_fmt.outcome }}" == "failure" ]] && exit 1
          [[ "${{ steps.step_check.outcome }}" == "failure" ]] && exit 1
          [[ "${{ steps.step_build.outcome }}" == "failure" ]] && exit 1
          [[ "${{ steps.step_push.outcome }}" == "failure" ]] && exit 1
          exit 0
```

### 3.3 Параллельная версия (check + fmt параллельно, build после)

Если check и fmt не зависят от build, можно запускать параллельно:

```yaml
      # ── Parallel: Format + Flake Check ──
      - name: Parallel checks
        id: step_parallel
        continue-on-error: true
        run: |
          nix fmt $NIX_FLAGS -- --ci &
          FMT_PID=$!
          nix flake check --no-build $NIX_FLAGS &
          CHECK_PID=$!
          
          FMT_OK=0; wait $FMT_PID || FMT_OK=$?
          CHECK_OK=0; wait $CHECK_PID || CHECK_OK=$?
          
          echo "fmt_exit=$FMT_OK" >> $GITHUB_OUTPUT
          echo "check_exit=$CHECK_OK" >> $GITHUB_OUTPUT
```

---

## 4. Branch Protection

Check Runs созданные через API **можно использовать в Branch Protection Rules**.
В настройках репозитория → Branches → Branch protection → Require status checks:

Виртуальные чеки появятся в списке после первого запуска workflow.
Можно сделать required: "✅ Format", "✅ Flake Check", "📦 Build OCI".

---

## 5. Сравнение: было vs стало

### Было: 2 джобы

```
Job "Check & Build":  16s (7s работа + 9s overhead)
Job "Push to GHCR":   ~14s (5s работа + 9s overhead)  [когда запускается]
                      ─────
Total:                ~30s (12s работа, 18s overhead = 60%)
```

### Стало: 1 джоба + virtual checks

```
Job "CI/CD":          ~14s (12s работа + 2s overhead)  [checkout ~0.5s, нет второй джобы]
                      ─────
Total:                ~14s (12s работа, 2s overhead = 14%)
```

**Экономия: ~16s (53%) за счёт**:
- Убрана вторая джоба: -9s overhead
- `git` вместо `actions/checkout`: -2s
- Один Set up job вместо двух: -5s

### Что видит пользователь в GitHub PR UI

```
PR #42: Fix API endpoint
  ✅ Format              — passed
  ✅ Flake Check         — passed
  📦 Build OCI           — passed
  🚀 Push to GHCR        — skipped
```

Каждый чек — кликабельная строка с деталями.

---

## 6. Альтернативы

### 6.1 Commit Status API (без стороннего action)

Можно без `dflydev/check-runs-action`, напрямую через curl:

```bash
curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$GITHUB_REPOSITORY/statuses/$GITHUB_SHA" \
  -d '{"state":"pending","context":"ci/format","description":"Running..."}'
```

Плюсы: нет зависимости от action. Минусы: менее красивый UI (маленькие индикаторы вместо полноценных чеков).

### 6.2 LouisBrunner/checks-action

Более зрелый action (262 stars), поддерживает аннотации к файлам:

```yaml
- uses: LouisBrunner/checks-action@v2.0.0
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
    name: Format Check
    conclusion: ${{ steps.step_fmt.outcome }}
    output: |
      {"summary": "nix fmt -- --check completed"}
```

Плюсы: аннотации к конкретным строкам файлов (как ESLint показывает).
Минусы: нет prepare/update pattern из коробки.

---

## 7. Ограничения

1. **`details_url` не работает с GITHUB_TOKEN** — клик на check run не ведёт на кастомную страницу
2. **dflydev/check-runs-action — 15 stars** — маленький проект, но код простой
3. **Каждый check-runs-action step = HTTP запрос к API** — добавляет ~0.3-0.5s на каждый вызов
4. **Self-hosted runner без Node.js** — dflydev/check-runs-action требует Node.js runtime.
   Если runner чистый (только nix), нужно обеспечить наличие Node.js или использовать
   curl-based подход с Commit Status API.

---

## 8. Рекомендация

Для проекта fd_cicd templates:

1. **Объединить все джобы в одну** — экономия ~9-14s на каждой дополнительной джобе
2. **Заменить `actions/checkout` на `git`** — экономия ~2s
3. **Использовать `dflydev/check-runs-action`** для красивого UI (если Node.js доступен)
4. **Fallback на Commit Status API** если runner без Node.js
5. **`GITHUB_STEP_SUMMARY`** для markdown отчёта в любом случае
6. **Параллелизация Nix команд** внутри одного step (уже сделано)

---

## Ресурсы

| Ресурс | URL |
|--------|-----|
| dflydev/check-runs-action | https://github.com/dflydev/check-runs-action |
| LouisBrunner/checks-action | https://github.com/LouisBrunner/checks-action |
| GitHub Check Runs API | https://docs.github.com/en/rest/checks/runs |
| GitHub Commit Status API | https://docs.github.com/en/rest/commits/statuses |
| GITHUB_STEP_SUMMARY | https://github.blog/2022-05-09-supercharging-github-actions-with-job-summaries/ |
| actions/checkout sparse-checkout | https://depot.dev/blog/why-organizations-have-slow-actions-checkout |
