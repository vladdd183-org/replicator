# 📚 Nix CI/CD Showcase — Общий обзор и ограничения

> 🏗️ Репозиторий-шаблон для CI/CD на Nix: от сборки OCI-образов до деплоя.
> Основной стек FetData: **Python (uv)** и **JS (bun / nodejs)**.

---

## 🎯 Цель проекта

Создать **showcase-репозиторий** с готовыми шаблонами CI/CD на Nix:
- Собирать OCI-образы **без Docker daemon** (через nix2container)
- Пушить в container registry
- Деплоить в Kubernetes
- Поддержка Python (uv) и JS (bun/node) проектов

---

## 🚧 ЖЁСТКИЕ ОГРАНИЧЕНИЯ

| Ограничение | Обоснование |
|-------------|-------------|
| ❌ Никакого vendor-lock | Garnix, Hercules CI, nixbuild.net, FlakeHub — НЕ используем как CI/CD |
| ✅ Только open-source | Весь стек должен быть бесплатным и open-source |
| ✅ Только self-hosted | Кроме GitHub runners (бесплатный tier) |
| ✅ Публичные кеши — ок | cache.nixos.org, nix-community.cachix.org — можно |
| ❌ Приватный код в публичные кеши — нет | Свой кеш-сервер (Attic / Harmonia) для приватных деривейшнов |
| ✅ GitHub как платформа | GitHub runners + GitHub API для отображения статусов |

---

## 📑 Карта заметок

| # | Файл | Тема |
|---|-------|------|
| 01 | [01-autoposter-analysis.md](./01-autoposter-analysis.md) | 🔍 Разбор текущего CI/CD автопостера |
| 02 | [02-nix2container.md](./02-nix2container.md) | 🐳 Сборка OCI-образов (nix2container, nix-oci, dockerTools) |
| 03 | [03-variant-github-runner.md](./03-variant-github-runner.md) | 🏃 Вариант 1: GitHub Hosted Runner + Nix Action |
| 04 | [04-variant-selfhost-runner.md](./04-variant-selfhost-runner.md) | 🖥️ Вариант 2: Self-hosted NixOS GitHub Runner |
| 05 | [05-variant-full-nix-cicd.md](./05-variant-full-nix-cicd.md) | 🧪 Вариант 3: Полностью Nix CI/CD (buildbot-nix, om ci) |
| 06 | [06-caching.md](./06-caching.md) | 💾 Кеширование (Attic vs Harmonia, post-build-hook, публичные) |
| 07 | [07-optimization.md](./07-optimization.md) | ⚡ Оптимизация сборок (параллелизм, remote builders, слои) |
| 08 | [08-nixidy-snapshotter.md](./08-nixidy-snapshotter.md) | 🔮 Будущее: nixidy (K8s через Nix) + nix-snapshotter |
| 09 | [09-ecosystem-tools.md](./09-ecosystem-tools.md) | 🧰 Экосистема (flake-parts, nix-oci, std, omnix) |
| 10 | [10-python-js-specifics.md](./10-python-js-specifics.md) | 🐍🟢 Python (uv2nix) и JS (bun2nix) через Nix |

---

## 🏛️ Три архитектурных варианта

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  📦 Вариант 1: GitHub Hosted Runner + Nix Action                       │
│  ├── DeterminateSystems/nix-installer-action                            │
│  ├── magic-nix-cache-action (кеш через GitHub Actions Cache)            │
│  ├── nix build → skopeo push → deploy                                   │
│  ├── ✅ Нулевая инфраструктура, бесплатно (2000 мин/мес)               │
│  └── ⚠️ Каждый раз чистая машина → медленнее без кеша                  │
│                                                                         │
│  🖥️ Вариант 2: Self-hosted NixOS GitHub Runner                         │
│  ├── srvos / github-nix-ci NixOS модули                                 │
│  ├── Nix store персистентный → быстрые повторные сборки                 │
│  ├── Свой кеш-сервер (Attic/Harmonia) для приватных путей               │
│  ├── ✅ Полный контроль, максимальная скорость                          │
│  └── ⚠️ Нужно содержать сервер(а)                                      │
│                                                                         │
│  🧪 Вариант 3: Полностью Nix CI/CD                                     │
│  ├── buildbot-nix — self-hosted CI с GitHub/Gitea интеграцией            │
│  ├── om ci — CLI для запуска CI из flake                                 │
│  ├── GitHub Checks API / Commit Status API для отображения              │
│  ├── ✅ Максимальная Nix-нативность                                     │
│  └── ⚠️ Сложность настройки, нужен отдельный сервер                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Общие принципы (для всех вариантов)

1. 🐳 **Без Docker daemon** — nix2container → OCI-образ → skopeo push
2. 💾 **Слоистое кеширование** — runtime / deps / app source в отдельных слоях
3. ⚡ **Параллелизм** — `--max-jobs auto --cores 0` + remote builders
4. 🔒 **Безопасность** — приватный код не утекает; публичные deps из публичных кешей
5. 🔄 **Воспроизводимость** — `flake.lock` фиксирует всё
6. 📦 **Инкрементальность** — skopeo пропускает неизменённые слои при push

---

## 🗂️ Допустимый стек инструментов

### ✅ Можно использовать (open-source, self-hosted)

| Инструмент | Роль | Ссылка |
|------------|------|--------|
| **nix2container** | Сборка OCI-образов | [github](https://github.com/nlewo/nix2container) |
| **nix-oci** | flake-parts модуль для OCI | [github](https://github.com/Dauliac/nix-oci) |
| **Attic** | Self-hosted binary cache (S3-backed) | [github](https://github.com/zhaofengli/attic) |
| **Harmonia** | Self-hosted binary cache (serves /nix/store) | [github](https://github.com/nix-community/harmonia) |
| **srvos** | NixOS модуль для GitHub runners | [github](https://github.com/nix-community/srvos) |
| **github-nix-ci** | Упрощённый модуль для runners | [github](https://github.com/juspay/github-nix-ci) |
| **buildbot-nix** | Self-hosted Nix CI (альтернатива Hydra) | [github](https://github.com/nix-community/buildbot-nix) |
| **omnix (om ci)** | CLI для CI из flake | [github](https://github.com/juspay/omnix) |
| **uv2nix** | Python (uv) → Nix | [github](https://github.com/pyproject-nix/uv2nix) |
| **bun2nix** | Bun → Nix | [github](https://github.com/nix-community/bun2nix) |
| **dream2nix** | Универсальный lang→nix (вкл. Node.js) | [github](https://github.com/nix-community/dream2nix) |
| **flake-parts** | Модульный flake.nix | [github](https://github.com/hercules-ci/flake-parts) |
| **nixidy** | K8s манифесты через Nix + ArgoCD | [nixidy.dev](https://nixidy.dev) |
| **nix-snapshotter** | containerd + Nix store (без OCI) | [github](https://github.com/pdtpartners/nix-snapshotter) |

### ✅ Внешние сервисы (бесплатные / публичные)

| Сервис | Роль |
|--------|------|
| GitHub Actions (hosted runners) | CI runner, бесплатно 2000 мин/мес |
| GitHub Packages (GHCR) | Container registry |
| cache.nixos.org | Публичный кеш nixpkgs |
| nix-community.cachix.org | Публичный кеш nix-community |

### ❌ НЕ используем

| Сервис | Причина |
|--------|---------|
| Garnix | Vendor-lock, платный, их серверы |
| Hercules CI | Vendor-lock, платный |
| nixbuild.net | Vendor-lock, платный |
| FlakeHub | Vendor-lock |
| Cachix (платный tier) | Для приватного кеша лучше Attic/Harmonia |

---

## 🧠 Ключевые инсайты из ресерча

1. **nix2container** — однозначный выбор для OCI. В 5-6x быстрее dockerTools, не пишет tarball в store, пропускает уже загруженные слои
2. **magic-nix-cache-action** — бесплатный кеш через GitHub Actions Cache для Варианта 1, не требует Cachix
3. **Attic > Harmonia** для CI-кеша: Attic поддерживает S3, multi-tenancy, managed signing. Harmonia проще но просто сервит /nix/store
4. **buildbot-nix** — зрелая замена Hydra для Варианта 3, с GitHub PR интеграцией
5. **post-build-hook** + очередь — паттерн для автоматического пуша в кеш после каждой сборки
6. **GitHub Checks API** — способ отображать статусы внешнего CI прямо в GitHub PR
7. **bun2nix** — готов для продакшена (v2.0.8), 50ms на 2k пакетов
8. **dream2nix для Node.js** — всё ещё нестабилен, для Node лучше node2nix или bun2nix
9. **nixos-fireactions** — Firecracker microVM для изоляции jobs (для параноиков)
10. **nix-oci** (flake-parts) — высокоуровневая абстракция над nix2container, security scanning из коробки
