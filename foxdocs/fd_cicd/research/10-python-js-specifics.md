# 🐍🟢 Python (uv2nix) и JS (bun2nix / node) через Nix

> Специфика сборки нашего основного стека через Nix.
> Подводные камни, паттерны, типовые оверрайды.

---

## 🐍 Python + uv → uv2nix

### 🎯 Как это работает

```
pyproject.toml + uv.lock
       │
       ▼
uv2nix.lib.workspace.loadWorkspace
       │
       ▼
workspace.mkPyprojectOverlay  →  Nix overlay с деривейшнами пакетов
       │
       ▼
pythonSet.mkVirtualEnv  →  /nix/store/xxx-myapp-env (virtualenv)
       │
       ▼
nix2container.buildImage  →  OCI образ
```

### 📋 Минимальный flake.nix для Python + uv

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nix2container = {
      url = "github:nlewo/nix2container";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, nix2container, ... }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    lib = pkgs.lib;
    n2c = nix2container.packages.${system}.nix2container;

    python = pkgs.python313;
    workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
    overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

    pythonBase = pkgs.callPackage pyproject-nix.build.packages { inherit python; };
    pythonSet = pythonBase.overrideScope (
      lib.composeManyExtensions [
        pyproject-build-systems.overlays.wheel
        overlay
        # Кастомные оверрайды (см. ниже)
        customOverrides
      ]
    );

    venv = pythonSet.mkVirtualEnv "myapp-env" workspace.deps.default;
  in {
    packages.${system}.default = n2c.buildImage { ... };
  };
}
```

### 🔧 sourcePreference: wheel vs sdist

| | `"wheel"` ⭐ рекомендуется | `"sdist"` |
|-|--------------------------|----------|
| ⚡ Скорость | Быстро (бинарники) | Медленно (компиляция) |
| 🔧 Оверрайды | Меньше (нет build systems) | Больше (каждый пакет) |
| 🔒 Reproducibility | ⚠️ Wheel может быть не-reproducible | ✅ Из исходников |
| 📦 Наличие | ~95% пакетов имеют wheels | 100% имеют sdist |

> 💡 Для CI/CD: `"wheel"` — быстрее и меньше головной боли.
> `"sdist"` — для параноиков воспроизводимости (но нужно много оверрайдов).

### 🔨 Типовые оверрайды Python-пакетов

#### 1. Пакеты с C-зависимостями (Pillow, lxml, cryptography...)

```nix
customOverrides = final: prev: {
  pillow = prev.pillow.overrideAttrs (old: {
    buildInputs = (old.buildInputs or []) ++ [
      pkgs.libjpeg pkgs.zlib pkgs.freetype
      pkgs.lcms2 pkgs.libtiff pkgs.libwebp
    ];
  });

  lxml = prev.lxml.overrideAttrs (old: {
    buildInputs = (old.buildInputs or []) ++ [
      pkgs.libxml2 pkgs.libxslt
    ];
  });

  cryptography = prev.cryptography.overrideAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or []) ++ [
      pkgs.openssl pkgs.pkg-config
    ];
  });
};
```

#### 2. Пакеты с legacy setup.py (нет pyproject.toml)

```nix
customOverrides = final: prev: {
  pyaes = prev.pyaes.overrideAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or []) ++ [
      final.setuptools
    ];
  });

  # Другие legacy пакеты:
  some-old-lib = prev.some-old-lib.overrideAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or []) ++ [
      final.setuptools final.wheel
    ];
  });
};
```

#### 3. Конфликты между пакетами

```nix
customOverrides = final: prev: {
  # piccolo-admin и piccolo-api оба имеют директорию e2e/
  piccolo-admin = prev.piccolo-admin.overrideAttrs (old: {
    postInstall = (old.postInstall or "") + ''
      rm -rf $out/lib/python*/site-packages/e2e
    '';
  });
};
```

#### 4. Decoupled app source от venv ⭐ ВАЖНО

```nix
customOverrides = final: prev: {
  # Изменение src кода НЕ должно пересобирать весь venv!
  myapp = prev.myapp.overrideAttrs (old: {
    src = pkgs.runCommand "myapp-metadata-only" {} ''
      mkdir -p $out/src
      cp ${./pyproject.toml} $out/pyproject.toml
      touch $out/src/__init__.py
    '';
  });
};
```

> 💡 Без этого: каждый коммит в src/ → пересборка всего venv (200+ MB).
> С этим: venv пересобирается только при изменении pyproject.toml / uv.lock.

### 📊 Типовые проблемные пакеты (из опыта)

| Пакет | Проблема | Оверрайд |
|-------|----------|----------|
| `pillow` | libjpeg, zlib, freetype... | buildInputs += system libs |
| `lxml` | libxml2, libxslt | buildInputs += system libs |
| `cryptography` | OpenSSL, Rust build | nativeBuildInputs += openssl, pkg-config |
| `numpy` | BLAS/LAPACK | buildInputs += openblas |
| `psycopg2` | PostgreSQL client | buildInputs += postgresql |
| `pyaes` | Нет pyproject.toml | nativeBuildInputs += setuptools |
| `grpcio` | gRPC C++ libs | buildInputs += grpc |
| `uvloop` | libuv | buildInputs += libuv |

---

## 🟢 JavaScript + Bun → bun2nix

### 🎯 Как это работает

```
bun.lockb (Bun lockfile v1.2+)
       │
       ▼
bun2nix (Rust binary, ~50ms)
       │
       ▼
default.nix / flake.nix с деривейшнами
       │
       ▼
nix build → node_modules + AOT binary (опционально)
       │
       ▼
nix2container → OCI образ
```

**GitHub**: [nix-community/bun2nix](https://github.com/nix-community/bun2nix) (120 ⭐)
**Версия**: v2.0.8

### 📋 Минимальный пример

```bash
# 1. Генерация Nix выражений из bun.lockb
bun2nix
# → создаёт bun2nix.lock.json (или подобный lockfile для nix)
```

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    bun2nix.url = "github:nix-community/bun2nix";
    nix2container.url = "github:nlewo/nix2container";
  };

  outputs = { self, nixpkgs, bun2nix, nix2container, ... }:
  let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
    n2c = nix2container.packages.${system}.nix2container;

    nodeModules = bun2nix.lib.${system}.mkNodeModules {
      src = ./.;
    };

    appSrc = pkgs.stdenv.mkDerivation {
      name = "myapp-src";
      src = ./.;
      phases = [ "installPhase" ];
      installPhase = ''
        mkdir -p $out/app
        cp -r $src/src $out/app/src
        cp $src/package.json $out/app/package.json
      '';
    };
  in {
    packages.${system}.default = n2c.buildImage {
      name = "myapp";
      layers = [
        (n2c.buildLayer { deps = [ pkgs.bun pkgs.cacert ]; })
        (n2c.buildLayer { deps = [ nodeModules ]; maxLayers = 1; })
        (n2c.buildLayer { deps = [ appSrc ]; })
      ];
      config = {
        Entrypoint = [ "${pkgs.bun}/bin/bun" "run" "/app/src/index.ts" ];
        WorkingDir = "/app";
        Env = [ "NODE_ENV=production" ];
      };
    };
  };
}
```

### 🚀 AOT-компиляция с Bun

```nix
# Собрать standalone binary
app = pkgs.stdenv.mkDerivation {
  name = "myapp";
  src = ./.;
  buildInputs = [ pkgs.bun ];
  buildPhase = ''
    bun build --compile --minify src/index.ts --outfile myapp
  '';
  installPhase = ''
    mkdir -p $out/bin
    cp myapp $out/bin/
  '';
};

# OCI-образ с одним бинарником — минимальный размер!
n2c.buildImage {
  name = "myapp";
  config.Entrypoint = [ "${app}/bin/myapp" ];
};
```

### ⚠️ Известные проблемы bun2nix

- 🐛 Проблемы с tarball-зависимостями содержащими `@` в URL (issue #76)
- ⚠️ Только Bun v1.2+ lockfiles
- ⚠️ Нет поддержки native addons (node-gyp)

---

## 🟢 JavaScript + Node.js → варианты

### 📊 Сравнение

| | **bun2nix** | **dream2nix** | **node2nix** |
|-|-----------|-------------|------------|
| ⚡ Скорость | 🚀 ~50ms | 🐢 Медленнее | 🐢 Медленнее |
| 📦 Lock format | bun.lockb | package-lock.json | package-lock.json / package.json |
| 📊 Зрелость | 🟡 v2.0.8 | 🟡 Unstable (API breaks) | ✅ Stable v1.11 |
| 🔧 Overrides | Простые | Модульные (drv-parts) | Через Nix expressions |
| 📖 Документация | 🟢 Хорошая | 🟡 Путаница v1/v2 | 🟢 Стабильная |
| 👥 Community | 120 ⭐ | Активная | Менее активная |
| 🎯 Рекомендация | ✅ Для Bun | ⚠️ Осторожно | ✅ Для Node.js |

### 💡 Наша стратегия

| Стек | Инструмент | Обоснование |
|------|-----------|-------------|
| 🐍 Python + uv | **uv2nix** | Нативная интеграция с uv.lock |
| 🟢 Bun | **bun2nix** | Быстрый, хорошо документирован |
| 🟢 Node.js + npm | **node2nix** или **dream2nix** | node2nix стабильнее, dream2nix гибче |
| 🟢 Node.js + yarn | **yarn2nix** | Для yarn проектов |

---

## 📊 Общий паттерн OCI-образа (любой стек)

```nix
# Универсальная структура для Python / Bun / Node.js
n2c.buildImage {
  name = "myapp";
  tag = "latest";

  layers = [
    # 🟢 Слой 1: Системные зависимости (runtime)
    (n2c.buildLayer {
      deps = [ pkgs.cacert pkgs.tzdata pkgs.bash pkgs.coreutils ]
             ++ runtimeDeps;  # libxml2, etc.
    })

    # 🟡 Слой 2: Языковые зависимости (venv / node_modules)
    (n2c.buildLayer {
      deps = [ languageDeps ];  # venv / nodeModules
      maxLayers = 1;
    })

    # 🔴 Слой 3: App source
    (n2c.buildLayer { deps = [ appSrc ]; })
  ];

  config = {
    Entrypoint = entrypoint;
    WorkingDir = "/app";
    Env = commonEnv ++ appSpecificEnv;
    User = "1000:1000";
  };
};
```

---

## 🧪 Тестирование через Nix checks

```nix
# В flake.nix
checks.${system} = {
  # Python: pytest
  pytest = pkgs.runCommand "pytest" { buildInputs = [ venv ]; } ''
    cd ${appSrc}/app
    python -m pytest tests/ -v
    touch $out
  '';

  # JS: bun test
  bun-test = pkgs.runCommand "bun-test" { buildInputs = [ pkgs.bun nodeModules ]; } ''
    cd ${appSrc}/app
    bun test
    touch $out
  '';

  # Lint: ruff / eslint
  lint = pkgs.runCommand "lint" { buildInputs = [ pkgs.ruff ]; } ''
    ruff check ${appSrc}/app/src
    touch $out
  '';
};
```

> 💡 `nix flake check` запустит все checks.
> `om ci` подхватит их автоматически.
> В GitHub Actions: `nix build .#checks.x86_64-linux.pytest`
