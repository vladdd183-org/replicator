# 11. Глубокий анализ nix-oci (Dauliac/nix-oci)

## Общее описание

**nix-oci** — flake-parts модуль для декларативного управления OCI-образами. Использует **nix2container** как бэкенд. Репозиторий: https://github.com/Dauliac/nix-oci (89 звёзд, MIT License).

Позиционирование: высокоуровневая обёртка над nix2container для быстрого создания минималистичных single-binary контейнеров с автоматической настройкой безопасности.

---

## 1. Кастомизируемость OCI-образов

### 1.1. Управление слоями (layers)

**Вердикт: НЕТ возможности управлять слоями.**

В `mkSimpleOCI.nix` вызов nix2container.buildImage зашит жёстко:

```nix
perSystemConfig.packages.nix2container.buildImage {
  inherit (oci) tag;
  name = fullName;
  inherit fromImage;
  copyToRoot = [
    (ociLib.mkRoot {
      inherit (oci) package dependencies tag user;
    })
  ];
  config = {
    inherit (oci) entrypoint;
    User = oci.user;
    Env = [
      "PATH=/bin"
      "USER=${oci.user}"
    ];
  };
};
```

Ключевые ограничения:
- **`layers` не передаётся** — всё идёт через `copyToRoot` как один `buildEnv`
- **`perms` не передаётся** — нет возможности задать права на файлы
- **`maxLayers` не передаётся** — нет контроля над количеством слоёв
- **`config` захардкожен** — только `entrypoint`, `User`, `Env` с фиксированным `PATH=/bin`
- **`Env` нельзя расширить** — нет опции для пользовательских env variables

### 1.2. Escape hatch к nix2container API

**Вердикт: НЕТ escape hatch.**

Модуль экспонирует `oci.packages.nix2container` (сам пакет nix2container), но **нет** никакого механизма для:
- Передачи произвольных параметров в `buildImage`
- Override'а итогового вызова `buildImage`
- Подмены builder-функции

Единственный путь «обойти» — использовать `oci.packages.nix2container.buildImage` напрямую, **полностью минуя** nix-oci, что делает модуль бесполезным.

### 1.3. Отключение автоматического поведения

| Поведение | Можно отключить? | Как |
|-----------|-----------------|-----|
| Auto non-root user | Частично | `isRoot = true` запускает от root |
| Auto shadow setup (/etc/passwd, etc.) | **НЕТ** | Всегда генерируется |
| Auto minimal fs (buildEnv) | **НЕТ** | Зашито в mkRoot |
| Auto `PATH=/bin` | **НЕТ** | Захардкожено в mkSimpleOCI |
| Auto `USER` env var | **НЕТ** | Захардкожено |

### 1.4. `mkRoot` — структура root filesystem

Всё собирается в один плоский `buildEnv`:

```nix
pkgs.buildEnv {
  name = "root";
  version = tag;
  paths = package' ++ shadowSetup ++ dependencies;
  pathsToLink = [ "/bin" "/lib" "/etc" ];
};
```

- Нет разделения на слои
- `pathsToLink` фиксирован — нельзя добавить `/share`, `/var` и т.д.
- Всё идёт в один `copyToRoot`

---

## 2. Архитектура модуля

### 2.1. Доступные опции `oci.containers.<name>`

Полный список опций, собранный из исходного кода:

**Основные:**
| Опция | Тип | По умолчанию | Описание |
|-------|-----|-------------|----------|
| `package` | `nullOr package` | `null` | Основной пакет |
| `dependencies` | `listOf package` | `[]` | Дополнительные зависимости |
| `entrypoint` | `listOf str` | Авто из package | Entrypoint |
| `name` | `str` | Имя атрибута | Имя образа |
| `tag` | `str` | `"latest"` | Тег образа |
| `tags` | `listOf str` | `[]` | Дополнительные теги |
| `registry` | `nullOr str` | Из global | Registry URL |
| `user` | `nullOr str` | Авто из name/isRoot | Пользователь |
| `isRoot` | `bool` | `false` | Запуск от root |
| `installNix` | `bool` | `false` | Установить Nix в контейнер |
| `push` | `bool` | `false` | Включить push |
| `rootPath` | `path` | Из global | Корневой путь проекта |

**fromImage (базовый образ из DockerHub):**
| Опция | Тип | Описание |
|-------|-----|----------|
| `fromImage.enabled` | `bool` | Использовать базовый образ |
| `fromImage.imageName` | `str` | Имя базового образа |
| `fromImage.imageTag` | `str` | Тег базового образа |
| `fromImage.os` | `str` | ОС базового образа |
| `fromImage.arch` | `str` | Архитектура |

**Debug:**
| Опция | Тип | Описание |
|-------|-----|----------|
| `debug.enabled` | `bool` | Создать debug-вариант |
| `debug.packages` | `listOf package` | Пакеты для debug (curl, bash...) |
| `debug.entrypoint.enabled` | `bool` | Заменить entrypoint на debug |
| `debug.entrypoint.wrapper` | `package` | Wrapper-скрипт |

**CVE сканирование (per-container):**
| Опция | Тип | Описание |
|-------|-----|----------|
| `cve.trivy.enabled` | `bool` | Trivy сканирование |
| `cve.trivy.ignore.fileEnabled` | `bool` | Использовать ignore-файл |
| `cve.trivy.ignore.path` | `path` | Путь к ignore-файлу |
| `cve.trivy.ignore.extra` | `listOf str` | Список CVE для игнора |
| `cve.grype.enabled` | `bool` | Grype сканирование |
| `cve.grype.config.enabled` | `bool` | Использовать config-файл |
| `cve.grype.config.path` | `path` | Путь к config-файлу |

**SBOM:**
| Опция | Тип | Описание |
|-------|-----|----------|
| `sbom.syft.enabled` | `bool` | Генерация SBOM через Syft |
| `sbom.syft.config.enabled` | `bool` | Использовать config |
| `sbom.syft.config.path` | `path` | Путь к config |

**Credentials Leak:**
| Опция | Тип | Описание |
|-------|-----|----------|
| `credentialsLeak.trivy.enabled` | `bool` | Проверка утечки секретов |

**Тестирование:**
| Опция | Тип | Описание |
|-------|-----|----------|
| `test.dive.enabled` | `bool` | Анализ образа через Dive |
| `test.containerStructureTest.enabled` | `bool` | Container Structure Test |
| `test.containerStructureTest.configs` | `listOf path` | Конфиги для CST |
| `test.dgoss.enabled` | `bool` | DGoss тестирование |
| `test.dgoss.optionsPath` | `path` | Путь к goss-файлу |

**Multi-Arch:**
| Опция | Тип | Описание |
|-------|-----|----------|
| `multiArch.enabled` | `bool` | Multi-arch сборка |
| `multiArch.tempTagPrefix` | `str` | Префикс для временных тегов |

### 2.2. Глобальные опции `oci.*`

| Опция | Описание |
|-------|----------|
| `oci.enabled` | Включить nix-oci |
| `oci.enableFlakeOutputs` | Экспортировать в flake outputs |
| `oci.enableDevShell` | Добавить инструменты в devShell |
| `oci.devShellPackage` | Пакет для devShell |
| `oci.rootPath` | Корневой путь проекта |
| `oci.registry` | Глобальный registry |
| `oci.fromImageManifestRootPath` | Путь для manifest locks |
| `oci.cve.*` | Глобальные настройки CVE |

### 2.3. Архитектура flake-parts модуля

Используется сложный паттерн `perContainer` (аналог `perSystem` из flake-parts):
- Каждая опция контейнера определена в своём файле
- Файлы "вносят вклад" в deferred module через `oci.perContainer`
- Модули собираются и применяются к каждому контейнеру
- `import-tree` используется для автоматической загрузки всех модулей

### 2.4. Документация

Формальная документация **отсутствует** (нет сгенерированных docs, нет подробного README). Единственный источник — исходный код и примеры в `examples/`.

---

## 3. Security scanning

### 3.1. Trivy

**Доступные настройки:**
- `enabled` — включить/выключить (по умолчанию `false`, наследуется из global)
- `ignore.fileEnabled` — использовать `.trivyignore`
- `ignore.path` — путь к ignore-файлу
- `ignore.extra` — список CVE для программного игнорирования (per-container)
- Глобальный `oci.cve.trivy.ignore.extra` — игнор для ВСЕХ контейнеров

**НЕ доступные настройки:**
- **Severity threshold** — не настраивается (нет `--severity` флага)
- **Тип сканера** — зашит `--scanners vuln` (нельзя добавить `misconfig`, `secret` и т.д.)
- **Exit code** — зашит `--exit-code 1`
- **Формат вывода** — не настраивается

### 3.2. Grype

**Доступные настройки:**
- `enabled` — включить/выключить
- `config.enabled` — использовать конфигурационный файл
- `config.path` — путь к YAML-файлу конфигурации Grype

**НЕ доступные настройки:**
- **Severity threshold** — только через внешний YAML config
- **Ignore list** — только через внешний YAML config
- Нет программного API для настройки severity, output format и т.д.

### 3.3. Можно ли полностью отключить?

**ДА.** По умолчанию оба сканера выключены (`enabled = false`). Включаются явно.

---

## 4. Совместимость с нашей архитектурой

### 4.1. Трёхслойная структура (runtime / deps / app)

**Вердикт: НЕ реализуема через nix-oci.**

Причины:
1. `mkSimpleOCI` НЕ передаёт `layers` в nix2container
2. Всё содержимое идёт через один `copyToRoot` → один `buildEnv`
3. Нет механизма для определения пользовательских слоёв
4. Нет `maxLayers` для автоматического расщепления

При нашей архитектуре нужно:
```nix
# Это НЕВОЗМОЖНО через nix-oci API
layers = [
  runtimeLayer   # python, system libs — меняется редко
  depsLayer      # pip зависимости — меняется при poetry.lock
  appLayer       # исходный код — меняется часто
];
```

### 4.2. Decoupled venv от source code

**Вердикт: НЕ поддерживается.**

- `dependencies` — плоский список пакетов, без контроля размещения
- Нет понятия "слой зависимостей" отдельно от "слой приложения"
- `buildEnv` объединяет всё в одну директорию

### 4.3. Вариант "installNix"

При `installNix = true` используется `mkNixOCI`, который ИСПОЛЬЗУЕТ `layers`:
```nix
layers = [
  (ociLib.mkNixOCILayer { ... })
];
```

Но это только для встраивания Nix внутрь контейнера, а не для наших задач.

---

## 5. Что nix-oci делает хорошо

1. **Быстрый старт** — минималистичный контейнер за 3 строки
2. **Auto non-root** — безопасность по умолчанию
3. **Security tooling** — интеграция с Trivy, Grype, Syft, Dive
4. **Debug-образы** — автоматическое создание debug-вариантов
5. **Container testing** — Container Structure Test, DGoss, Dive
6. **Multi-arch** — поддержка мультиархитектурных сборок
7. **fromImage** — возможность базироваться на DockerHub-образе
8. **SBOM** — автоматическая генерация Software Bill of Materials
9. **Монорепо** — хорошо работает с несколькими контейнерами

---

## 6. Принципиальные ограничения

| Ограничение | Критичность для нас |
|-------------|-------------------|
| Нет управления слоями | **КРИТИЧЕСКАЯ** |
| Нет `layers` в buildImage | **КРИТИЧЕСКАЯ** |
| Нет `perms` для файловых прав | ВЫСОКАЯ |
| Нет `maxLayers` | ВЫСОКАЯ |
| Нет кастомных Env vars | ВЫСОКАЯ |
| Захардкоженный `PATH=/bin` | ВЫСОКАЯ |
| Нет escape hatch | **КРИТИЧЕСКАЯ** |
| `pathsToLink` фиксирован | СРЕДНЯЯ |
| Нет severity threshold | СРЕДНЯЯ |
| Отсутствие документации | СРЕДНЯЯ |

---

## 7. Итоговый вердикт

### Подходит ли nix-oci как высокоуровневая обёртка при сохранении полного контроля?

## **НЕТ. nix-oci НЕ подходит для нашей архитектуры.**

**Причины:**

1. **Нет контроля над слоями** — невозможно реализовать трёхслойную оптимизацию (runtime/deps/app), которая критична для быстрых push/pull в CI/CD

2. **Нет escape hatch** — нельзя передать произвольные параметры nix2container. Модуль полностью инкапсулирует вызов `buildImage`, не давая к нему доступа

3. **Захардкоженная структура** — `Env`, `copyToRoot`, `config` зашиты в код модуля без возможности override

4. **Opinionated design** — модуль спроектирован для single-binary минималистичных контейнеров (kubectl, hello), а не для сложных приложений с зависимостями

### Рекомендация

**Использовать прямой nix2container** с собственными обёртками:
- Полный контроль над `layers`, `perms`, `maxLayers`, `config`
- Возможность реализации трёхслойной архитектуры
- Гибкость в настройке `Env`, `User`, `Cmd`
- Возможность интеграции security-инструментов по своим правилам

Можно **заимствовать идеи** из nix-oci:
- Паттерн `perContainer` (deferred modules) — элегантен для monorepo
- Auto shadow setup (`mkNonRootShadowSetup`) — полезная утилита
- Интеграция с Trivy/Grype как `nix flake check` — хороший подход
- Debug-варианты образов — удобная концепция

### Альтернативный вариант: Fork nix-oci?

Теоретически можно форкнуть и добавить недостающие опции (`layers`, `perms`, `extraConfig`, `extraEnv`). Однако архитектура модуля настолько "opinionated", что это потребует переписывания `mkSimpleOCI`, `mkRoot`, `mkOCI` и всей цепочки builder'ов. Проще написать свой thin wrapper поверх nix2container с нужным уровнем абстракции.
