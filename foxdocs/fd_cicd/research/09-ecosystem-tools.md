# 🧰 Экосистема инструментов Nix CI/CD

> Обзор всех релевантных open-source инструментов.
> Только то, что подходит под наши ограничения (self-hosted, бесплатно).

---

## 🧩 flake-parts — модульный flake.nix

**GitHub**: [hercules-ci/flake-parts](https://github.com/hercules-ci/flake-parts)
**Docs**: [flake.parts](https://flake.parts)

### 🎯 Что это

Модульная система для Nix flakes. Вместо одного гигантского `flake.nix` — набор модулей.

### 📊 Зачем нам

```nix
# Без flake-parts: всё в одном файле, copy-paste между проектами
{
  outputs = { self, nixpkgs, ... }: {
    packages.x86_64-linux.default = ...;
    devShells.x86_64-linux.default = ...;
    # ... повторяется для каждой system ...
  };
}

# С flake-parts: модульно, переиспользуемо
{
  inputs.flake-parts.url = "github:hercules-ci/flake-parts";

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } {
    systems = [ "x86_64-linux" "aarch64-linux" ];
    imports = [
      ./nix/oci.nix        # Контейнеры (nix-oci модуль)
      ./nix/python.nix     # Python env
      ./nix/devshell.nix   # Dev shell
    ];
  };
}
```

### 🔑 Ключевые модули для CI/CD

| Модуль | Описание | Ссылка |
|--------|----------|--------|
| **nix-oci** | Декларативные OCI-образы | [github](https://github.com/Dauliac/nix-oci) |
| **treefmt-nix** | Декларативное форматирование кода | [github](https://github.com/numtide/treefmt-nix) |
| **pre-commit-hooks.nix** | Git hooks как Nix | [github](https://github.com/cachix/pre-commit-hooks.nix) |
| **devshell** | Улучшенные dev shells | [github](https://github.com/numtide/devshell) |
| **process-compose-flake** | docker-compose но Nix | [github](https://github.com/Platonic-Systems/process-compose-flake) |

### 💡 Рекомендация

✅ Использовать flake-parts в шаблоне: модульность, переиспользуемость, чистота.
Особенно с nix-oci модулем для OCI-образов.

---

## 📦 nix-oci — OCI через flake-parts

**GitHub**: [Dauliac/nix-oci](https://github.com/Dauliac/nix-oci) (89 ⭐)

### 🎯 Что это

Flake-parts модуль для декларативного управления OCI-образами.
Обёртка над nix2container с security scanning.

### 📋 Минимальный пример

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    nix-oci.url = "github:Dauliac/nix-oci";
  };

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } {
    imports = [ inputs.nix-oci.flakeModules.default ];
    systems = [ "x86_64-linux" ];

    perSystem = { pkgs, ... }: {
      oci.containers = {
        myapp = {
          package = pkgs.hello;  # Или наш кастомный derivation
          # Автоматически:
          # ✅ non-root user
          # ✅ минимальная ФС
          # ✅ CVE scan (Grype)
          # ✅ credential leak (Trivy)
        };
      };
    };
  };
}
```

### 🔒 Security scanning

- **Grype** — CVE сканирование зависимостей
- **Trivy** — обнаружение утечек credentials
- Результаты как `checks` в flake → автоматически в CI

### 💡 Рекомендация

🟡 Перспективно, но молодой (89 ⭐). Для шаблона — как "advanced" вариант.
Для простого старта — прямой nix2container.

---

## 🔧 std (Standard) — DevOps фреймворк

**GitHub**: [divnix/std](https://github.com/divnix/std) (483 ⭐)
**Docs**: [std.divnix.com](https://std.divnix.com)

### 🎯 Что это

Фреймворк для организации Nix flakes с TUI/CLI для навигации.
"Что можно сделать с этим репозиторием?" — std отвечает.

### 📊 Архитектура

```
Cells (папки) → Cell Blocks (модули) → Block Types (packages, shells, containers, etc.)
```

### 🤔 Нужен ли нам?

| За | Против |
|-----|--------|
| ✅ Красивая организация | ⚠️ Высокий порог входа |
| ✅ CLI/TUI для навигации | ⚠️ Ещё один уровень абстракции |
| ✅ Интеграция с nix2container | ⚠️ Меньше community чем flake-parts |
| ✅ Operables → OCI | ⚠️ Overkill для простых проектов |

**Вердикт**: 🟡 Знать, но для шаблона — flake-parts проще и популярнее.

---

## 🔄 omnix (om ci) — CI CLI

**GitHub**: [juspay/omnix](https://github.com/juspay/omnix)
**Docs**: [omnix.page](https://omnix.page/om/ci.html)

Уже описан в [05-variant-full-nix-cicd.md](./05-variant-full-nix-cicd.md).

Ключевые команды:
```bash
om ci run            # Собрать всё из flake
om ci run .#backend  # Собрать конкретный sub-flake
om ci gh-matrix      # GitHub Actions matrix JSON
om health            # Проверить Nix setup
```

### 💡 Рекомендация

✅ Полезен как **утилита** внутри GitHub Actions step.
Не как CI-платформа, а как "умный `nix build` для CI".

---

## 🏗️ dream2nix — универсальный lang→nix

**GitHub**: [nix-community/dream2nix](https://github.com/nix-community/dream2nix)
**Docs**: [dream2nix.dev](https://dream2nix.dev)

### 📊 Текущий статус

| Аспект | Статус |
|--------|--------|
| 🐍 Python (pip) | ✅ Работает (но uv2nix лучше для uv проектов) |
| 🟢 Node.js | ⚠️ Нестабильно, API меняется |
| 🦀 Rust | ✅ Работает |
| 📖 Документация | 🟡 Есть, но путаница с v1/v2 API |
| 🔄 Активность | Активная, последний коммит ~2 мес назад |

### 🤔 Нужен ли нам?

Для **Python (uv)** — нет, uv2nix лучше.
Для **Node.js** — возможная опция, но dream2nix нестабилен.
Для **Bun** — нет, bun2nix лучше.

**Вердикт**: 🟡 Упомянуть как альтернативу, но не основной инструмент.

---

## 🐍 uv2nix — Python через uv

**GitHub**: [pyproject-nix/uv2nix](https://github.com/pyproject-nix/uv2nix)
**Docs**: [pyproject-nix.github.io/uv2nix](https://pyproject-nix.github.io/uv2nix/)

Подробно описан в [10-python-js-specifics.md](./10-python-js-specifics.md).

### 💡 Рекомендация

✅ **Основной инструмент** для Python + uv проектов.

---

## 🟢 bun2nix — JavaScript через Bun

**GitHub**: [nix-community/bun2nix](https://github.com/nix-community/bun2nix) (120 ⭐)
**Docs**: [nix-community.github.io/bun2nix](https://nix-community.github.io/bun2nix/)

Подробно описан в [10-python-js-specifics.md](./10-python-js-specifics.md).

### 💡 Рекомендация

✅ **Основной инструмент** для Bun проектов.

---

## 📊 Итоговая матрица: что используем в шаблоне

| Инструмент | Роль в шаблоне | Приоритет |
|------------|---------------|-----------|
| **nix2container** | Сборка OCI | 🔴 Обязательно |
| **flake-parts** | Модульность flake | 🔴 Обязательно |
| **uv2nix** | Python packaging | 🔴 Для Python шаблона |
| **bun2nix** | Bun packaging | 🔴 Для Bun шаблона |
| **Attic** или **Harmonia** | Приватный binary cache | 🟡 Для Вариантов 2/3 |
| **srvos** | Self-hosted runners | 🟡 Для Варианта 2 |
| **buildbot-nix** | Full Nix CI | 🟢 Для Варианта 3 |
| **omnix** | CI CLI | 🟢 Как утилита |
| **nix-oci** | Декларативный OCI | 🟢 Как "advanced" вариант |
| **nixidy** | K8s GitOps | 🔵 Будущее |
| **nix-snapshotter** | containerd + Nix | 🔵 Будущее |
| **std** | DevOps framework | ⚪ Упомянуть |
| **dream2nix** | Node.js packaging | ⚪ Альтернатива |
| **node2nix** | Node.js packaging | ⚪ Альтернатива (legacy) |
