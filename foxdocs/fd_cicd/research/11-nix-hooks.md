# 🪝 Nix хуки (hooks) для CI/CD

> Полный обзор всех видов хуков в экосистеме Nix, полезных для CI/CD пайплайнов.

---

## 1. post-build-hook — стандартный механизм Nix

**Документация**: [nix.dev/manual/nix/advanced-topics/post-build-hook](https://nix.dev/manual/nix/2.28/advanced-topics/post-build-hook)

### 🎯 Что это

Настройка `post-build-hook` в `nix.conf` — путь к программе, которая выполняется **после каждого завершённого билда**. Основное применение — автоматическая загрузка результатов сборки в бинарный кеш.

### ⚙️ Как работает

1. Nix завершает сборку деривации
2. Вызывает скрипт, указанный в `post-build-hook`
3. Скрипту доступны переменные окружения:
   - `$OUT_PATHS` — пробелами разделённый список выходных store-путей
   - `$DRV_PATH` — путь к .drv файлу
4. Скрипт выполняется от `root` (nix-daemon)
5. **Билд-цикл блокируется** до завершения скрипта

### 📋 Настройка в nix.conf

```ini
# /etc/nix/nix.conf
secret-key-files = /etc/nix/key.private
post-build-hook = /etc/nix/upload-to-cache.sh
```

### 📋 Пример скрипта загрузки в S3

```bash
#!/bin/sh
# /etc/nix/upload-to-cache.sh
set -eu
set -f  # отключаем glob-подстановку
export IFS=' '

echo "Uploading paths" $OUT_PATHS
exec nix copy --to "s3://example-nix-cache" $OUT_PATHS
```

### 📋 NixOS конфигурация

```nix
# configuration.nix
{
  nix.settings = {
    secret-key-files = [ "/etc/nix/key.private" ];
    post-build-hook = "/etc/nix/upload-to-cache.sh";

    # Для использования кеша как substituter
    substituters = [
      "https://cache.nixos.org/"
      "s3://example-nix-cache"
    ];
    trusted-public-keys = [
      "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
      "example-nix-cache-1:1/cKDz3QCCOmwcztD2eV6Coggp6rqc9DGjWv7C0G+rM="
    ];
  };
}
```

### ⚠️ Проблема блокировки

**Главная проблема**: хук **блокирует build loop**. Пока скрипт не завершится, зависимые билды не могут начаться.

```
[build A завершён] → [upload A → 30 сек...] → [build B может начаться]
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^
                      Блокировка! B ждёт.
```

**Конкретные проблемы**:

| Проблема | Описание |
|----------|----------|
| Медленная сеть | Nix становится «unusable» при медленном интернете |
| Deadlock (issue #3560) | Если билд-машина загружает в кеш, который она же использует как builder — зависание |
| Ошибка хука = остановка | Build loop полностью прекращается если хук вернул ненулевой exit code |

**Статус**: В issue [#15406](https://github.com/nixos/nix/issues/15406) предложен `async-post-build-hook` (PR #15451). На начало 2026 года — всё ещё в обсуждении.

---

## 2. Асинхронные очереди для post-build-hook

Из-за проблемы блокировки возникли сторонние решения.

### 2.1 nix-community/queued-build-hook

**GitHub**: [nix-community/queued-build-hook](https://github.com/nix-community/queued-build-hook)
**Язык**: Go
**Лицензия**: MIT
**Maintainer**: @jfroche

#### Как работает

Архитектура «клиент + демон»:

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Nix build   │───▸│  client (hook)    │───▸│  daemon (queue)  │
│  завершён    │    │  Мгновенный       │    │  Async upload    │
│              │    │  ← не блокирует   │    │  + retry         │
└─────────────┘    └──────────────────┘    └─────────────────┘
```

1. **Client** — минимальный скрипт, вызывается как `post-build-hook`, мгновенно передаёт store path в очередь и завершается
2. **Daemon** — systemd-сервис, обрабатывает очередь в фоне, загружает в кеш с настраиваемыми retry

#### Ключевые возможности

- Асинхронная обработка — не блокирует build loop
- Настраиваемые retry при ошибках сети
- Очередь сохраняется между перезапусками
- NixOS module для декларативной настройки

#### Примерная NixOS конфигурация

```nix
# configuration.nix
{ inputs, ... }:
{
  imports = [ inputs.queued-build-hook.nixosModules.default ];

  services.queued-build-hook = {
    enable = true;
    postBuildScriptContent = ''
      set -eu
      set -f
      export IFS=' '
      exec nix copy --to "s3://my-cache" $OUT_PATHS
    '';
  };

  nix.settings = {
    # queued-build-hook автоматически настраивает post-build-hook
    secret-key-files = [ "/etc/nix/key.private" ];
  };
}
```

### 2.2 nix-post-build-push (~tomeon)

**SourceHut**: [~tomeon/nix-post-build-push](https://git.sr.ht/~tomeon/nix-post-build-push)

Альтернативный инструмент с аналогичным подходом:
- Асинхронная загрузка через symlink-очередь
- Опция `closureType` — загрузка полного closure или только путей
- Настраиваемые `destination` и `interval`

### 2.3 Предложенный async-post-build-hook (PR #15451)

Нативное решение в самом Nix. Предлагается новая опция `nix.conf`:

```ini
# Вместо post-build-hook
async-post-build-hook = /etc/nix/upload-to-cache.sh
```

Отличия: хук вызывается асинхронно, не блокирует зависимые билды. На начало 2026 — не влит.

---

## 3. pre-commit-hooks.nix (cachix/git-hooks.nix)

**GitHub**: [cachix/git-hooks.nix](https://github.com/cachix/git-hooks.nix) (ранее cachix/pre-commit-hooks.nix)
**flake-parts docs**: [flake.parts/options/git-hooks-nix](https://flake.parts/options/git-hooks-nix)

### 🎯 Что это

Декларативная Nix-интеграция для [pre-commit](https://pre-commit.com/) git-хуков. Все инструменты для проверки кода управляются через Nix — воспроизводимо, без `pip install` / `npm install`.

### 📊 Доступные хуки (полный список)

Более 170 хуков. Ключевые категории:

#### Форматирование (Formatting)

| Хук | Язык | Описание |
|------|------|----------|
| `alejandra` | Nix | Nix code formatter |
| `nixfmt` | Nix | Official Nix formatter |
| `nixfmt-rfc-style` | Nix | Nix formatter (RFC 166) |
| `black` | Python | Python code formatter |
| `ruff-format` | Python | Ultra-fast Python formatter (Rust) |
| `isort` | Python | Python import sorter |
| `prettier` | JS/TS/CSS | Multi-language formatter |
| `eslint` | JS/TS | JS linter + formatter |
| `rustfmt` | Rust | Rust formatter |
| `gofmt` | Go | Go formatter |
| `stylua` | Lua | Lua formatter |
| `shfmt` | Shell | Shell formatter |
| `clang-format` | C/C++ | C/C++ formatter |
| `treefmt` | Multi | Universal formatter engine |
| `dart-format` | Dart | Dart formatter |
| `elm-format` | Elm | Elm formatter |
| `ormolu` | Haskell | Haskell formatter |

#### Линтинг (Linting)

| Хук | Язык | Описание |
|------|------|----------|
| `ruff` | Python | Ultra-fast Python linter (Rust) |
| `mypy` | Python | Python static type checker |
| `pylint` | Python | Python linter |
| `pyright` | Python | Python type checker |
| `flake8` | Python | Python linter |
| `eslint` | JS/TS | JavaScript linter |
| `clippy` | Rust | Rust linter |
| `golangci-lint` | Go | Go meta-linter |
| `shellcheck` | Shell | Shell script linter |
| `statix` | Nix | Nix linter + suggestions |
| `deadnix` | Nix | Dead Nix code scanner |
| `hlint` | Haskell | Haskell linter |
| `luacheck` | Lua | Lua linter |

#### Безопасность (Security)

| Хук | Описание |
|------|----------|
| `trufflehog` | Сканер секретов (ключи, пароли) |
| `ripsecrets` | Поиск случайно закоммиченных секретов |
| `detect-aws-credentials` | Обнаружение AWS credentials |
| `detect-private-keys` | Обнаружение приватных ключей |
| `pre-commit-hook-ensure-sops` | Проверка SOPS шифрования |
| `zizmor` | Анализ безопасности GitHub Actions |

#### Прочие полезные

| Хук | Описание |
|------|----------|
| `typos` | Spell checker для кода |
| `commitizen` | Conventional commits |
| `check-merge-conflicts` | Маркеры конфликтов |
| `check-json` / `check-yaml` / `check-toml` | Валидация конфигов |
| `hadolint` | Dockerfile linter |
| `actionlint` | GitHub Actions linter |
| `markdownlint` | Markdown linter |
| `end-of-file-fixer` | Гарантирует newline в конце файла |
| `trim-trailing-whitespace` | Убирает trailing whitespace |

### 📋 Интеграция с flake-parts

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    git-hooks-nix.url = "github:cachix/git-hooks.nix";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.git-hooks-nix.flakeModule
      ];

      systems = [ "x86_64-linux" "aarch64-linux" ];

      perSystem = { config, pkgs, ... }: {
        # ═══════════════════════════════════════
        # Конфигурация git-hooks
        # ═══════════════════════════════════════
        pre-commit.settings.hooks = {
          # --- Nix ---
          nixfmt-rfc-style.enable = true;
          deadnix.enable = true;
          statix.enable = true;

          # --- Python ---
          ruff.enable = true;
          ruff-format.enable = true;
          mypy = {
            enable = true;
            settings.binPath = "${pkgs.mypy}/bin/mypy";
          };

          # --- JavaScript/TypeScript ---
          eslint.enable = true;
          prettier.enable = true;

          # --- Безопасность ---
          trufflehog.enable = true;
          detect-private-keys.enable = true;

          # --- Общее ---
          check-merge-conflicts.enable = true;
          end-of-file-fixer.enable = true;
          trim-trailing-whitespace.enable = true;
        };

        # devShell автоматически включает хуки
        devShells.default = pkgs.mkShell {
          shellHook = ''
            ${config.pre-commit.installationScript}
          '';
        };
      };
    };
}
```

### 📋 Пример: Python-проект (ruff + mypy)

```nix
perSystem = { config, pkgs, ... }: {
  pre-commit.settings = {
    hooks = {
      ruff = {
        enable = true;
        args = [ "--fix" ];  # автоисправление
      };
      ruff-format.enable = true;
      mypy = {
        enable = true;
        # Дополнительные пакеты для type stubs
        extraPackages = with pkgs.python3Packages; [
          types-requests
          types-pyyaml
        ];
      };
      isort = {
        enable = true;
        args = [ "--profile" "black" ];
      };
    };
  };
};
```

### 📋 Пример: JS/TS-проект (eslint + prettier)

```nix
perSystem = { config, pkgs, ... }: {
  pre-commit.settings = {
    hooks = {
      eslint = {
        enable = true;
        files = "\\.(js|jsx|ts|tsx)$";
        args = [ "--fix" ];
      };
      prettier = {
        enable = true;
        files = "\\.(js|jsx|ts|tsx|css|json|md)$";
      };
    };
  };
};
```

### 📋 Использование в CI

```yaml
# .github/workflows/checks.yml
jobs:
  pre-commit:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - uses: cachix/install-nix-action@v30
      - run: nix flake check  # запускает все хуки в sandbox
```

### ⚠️ Ограничения

- **Sandbox проблема**: `nix flake check` запускает хуки в sandbox — инструменты без сетевого доступа (clippy + cargo fetch) могут упасть
- **Решение**: запускать через `nix develop -c pre-commit run --all-files` для полного доступа
- Альтернатива `pre-commit`: поддерживается [prek](https://github.com/prek-sh/prek) — совместимый runner с параллельным выполнением

---

## 4. diff-hook — проверка воспроизводимости билдов

**Документация**: [nix.dev/manual/nix/advanced-topics/diff-hook](https://nix.dev/manual/nix/2.24/advanced-topics/diff-hook)

### 🎯 Что это

Механизм для верификации **детерминистичности** сборок. Хук вызывается **только если** результаты повторной сборки отличаются от сохранённых.

### ⚙️ Как работает

```
nix-build ./pkg.nix --check
                      │
    ┌─────────────────┘
    ▼
[Повторная сборка] ──▸ [Сравнение с сохранённым результатом]
                              │
                   ┌──────────┴──────────┐
                   │ Совпадают           │ Отличаются
                   │ exit 0              │ → вызов diff-hook
                   └─────────────────────└──▸ /etc/nix/my-diff-hook $1 $2 $3
                                               $1 = первый результат
                                               $2 = второй результат  
                                               $3 = путь к .drv
```

### 📋 Конфигурация

```ini
# /etc/nix/nix.conf
diff-hook = /etc/nix/my-diff-hook
run-diff-hook = true
```

```bash
#!/bin/sh
# /etc/nix/my-diff-hook
exec >&2
echo "For derivation $3:"
/run/current-system/sw/bin/diff -r "$1" "$2"
```

### 📋 NixOS конфигурация

```nix
{
  nix.settings = {
    diff-hook = "/etc/nix/my-diff-hook";
    run-diff-hook = true;
  };

  environment.etc."nix/my-diff-hook" = {
    mode = "0755";
    text = ''
      #!/bin/sh
      exec >&2
      echo "Non-deterministic build detected for derivation $3:"
      ${pkgs.diffutils}/bin/diff -r "$1" "$2"
    '';
  };
}
```

### 📊 Применение в CI/CD

```bash
# В CI пайплайне: проверить что пакет собирается детерминистично
nix-build ./my-package.nix --check --keep-failed
# exit 0 = детерминистично
# exit 1 = недетерминистично, результат сохранён в /nix/store/...-name.check
```

Полезно для:
- Верификации reproducible builds в пайплайне
- Обнаружения недетерминизма до деплоя
- Аудита безопасности (SBOM/SLSA compliance)

---

## 5. pre-build-hook — настройка sandbox перед сборкой

**Документация**: [nix.dev/manual/nix/command-ref/conf-file](https://nix.dev/manual/nix/2.34/command-ref/conf-file.html)

### 🎯 Что это

Программа, запускаемая **перед** каждой сборкой. Позволяет установить дополнительные настройки для конкретной деривации, которые нельзя описать в самой деривации.

### ⚙️ Как работает

Хуку передаются:
1. **Путь к деривации** (`.drv`)
2. **Путь к sandbox-директории** (если sandbox включён)

Хук может выводить команды в stdout:

| Команда | Действие |
|---------|----------|
| `extra-sandbox-paths` | Добавить пути в sandbox для этой сборки (один путь на строку, завершается пустой строкой) |

### 📋 Конфигурация

```ini
# /etc/nix/nix.conf
pre-build-hook = /etc/nix/my-pre-build-hook
```

```bash
#!/bin/sh
# /etc/nix/my-pre-build-hook
# $1 = путь к деривации (.drv)
# $2 = путь к sandbox (если включён)

# Пример: добавить специфичные пути в sandbox
if echo "$1" | grep -q "my-special-package"; then
  echo "extra-sandbox-paths"
  echo "/etc/special-config"
  echo ""
fi
```

### 📊 Применение в CI/CD

- Динамическое добавление сертификатов/конфигов в sandbox
- Условная настройка sandbox для специфичных пакетов
- Используется редко, но полезен для нестандартных сценариев

---

## 6. run-diff-hook — управляющая настройка

```ini
# /etc/nix/nix.conf
run-diff-hook = true   # включает выполнение diff-hook
run-diff-hook = false  # по умолчанию — выключен
```

Важно: при использовании nix-daemon, `run-diff-hook` **должен** быть установлен в `nix.conf`, а не через командную строку.

---

## 7. build-hook — внутренний механизм удалённых билдеров

Не путать с `post-build-hook`. `build-hook` — это внутренняя настройка Nix, определяющая программу для делегирования сборок удалённым машинам. По умолчанию — `nix-daemon --build-hook`. Обычно не меняется вручную.

---

## 📊 Сводная таблица всех хуков

| Хук | Когда выполняется | Блокирует | Применение в CI/CD |
|------|-------------------|-----------|-------------------|
| `post-build-hook` | После каждого билда | **Да** | Загрузка в кеш |
| `pre-build-hook` | Перед каждым билдом | **Да** | Настройка sandbox |
| `diff-hook` | При расхождении rebuild | **Да** | Проверка reproducibility |
| `run-diff-hook` | (управляющая опция) | — | Вкл/выкл diff-hook |
| `build-hook` | При delegated builds | — | Remote builders (внутренний) |
| `git-hooks.nix` | git pre-commit / CI check | — | Formatting, linting, security |
| `queued-build-hook` | После билда (async) | **Нет** | Async загрузка в кеш |

---

## 🏁 Рекомендации для CI/CD шаблона

### Стратегия хуков

```
┌─────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. pre-commit (git-hooks.nix)                          │
│     └─ ruff, eslint, nixfmt, deadnix, trufflehog        │
│     └─ Запуск: nix flake check или nix develop           │
│                                                          │
│  2. Build                                                │
│     └─ pre-build-hook (если нужна кастомизация sandbox)  │
│     └─ nix build .#package                               │
│                                                          │
│  3. Post-build (загрузка в кеш)                          │
│     └─ ВАРИАНТ A: cachix push (простой)                  │
│     └─ ВАРИАНТ B: queued-build-hook (self-hosted)        │
│     └─ ВАРИАНТ C: post-build-hook (если сеть стабильна)  │
│                                                          │
│  4. Reproducibility check (опционально)                  │
│     └─ diff-hook + nix build --check                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Минимальный набор

Для нашего шаблона (self-hosted runner, Gitea):

1. **git-hooks.nix** через flake-parts — обязательно (formatting + linting + security)
2. **post-build-hook** или **queued-build-hook** — для загрузки в локальный кеш
3. **diff-hook** — опционально, для reproducibility-аудита
