# 18. Универсальные OCI-образы для nix-snapshotter и обычных нод

## Проблема

Kubernetes кластер содержит два типа нод:
- **Nix-ноды** (perturabo) — с `nix-snapshotter` и `/nix/store`
- **Обычные ноды** (angron) — стандартный containerd без Nix

Нужно: один деплой, который работает на обоих типах нод, с оптимизацией на nix-нодах.

---

## Как containerd обрабатывает pull (важно для понимания)

Скачивание слоёв контролирует **containerd content store**, а не snapshotter:

```
1. containerd → скачивает манифест из реестра
2. containerd → для каждого слоя:
     ↳ проверяет: блоб уже в content store? (по digest)
     ↳ если нет → скачивает из реестра
     ↳ если да → пропускает скачивание
3. containerd → для каждого слоя:
     ↳ вызывает snapshotter.Prepare()      ← тут snapshotter впервые видит аннотации
     ↳ распаковывает tarball в snapshot
4. snapshotter → View/Mounts: добавляет bind mounts
```

**Ключевое ограничение:** snapshotter **не может** сказать containerd "не качай этот слой". Он подключается уже после скачивания. Единственный обход — CRI Image Service (перехватывает pull на уровне kubelet).

---

## Вариант A: Два образа + OCI Manifest Index (рекомендуемый)

### Идея

Один тег в реестре (`ghcr.io/org/app:latest`) содержит **OCI Image Index** (manifest list) с двумя манифестами:
- **n2c-манифест** — полноценные OCI слои, работает везде
- **nix-манифест** — крохотные маунтпоинты (~300B) + аннотации, только для nix-нод

```
ghcr.io/org/app:latest
└── OCI Image Index
    ├── Manifest 1 (linux/amd64)           ← для обычных нод
    │   └── Layers: [cacert, venv, app]     (~150MB реальных файлов)
    └── Manifest 2 (linux/amd64, nix)       ← для nix-нод
        └── Layer: [mountpoints + closure]   (~300B + аннотации)
```

### Как нода выбирает манифест

Стандартный containerd выбирает манифест по `platform` (os/arch). Оба манифеста — `linux/amd64`. Containerd берёт **первый совпадающий**.

Для умного выбора на nix-нодах есть два пути:

**Путь 1 — CRI Image Service nix-snapshotter (патч ~30 строк)**

`image_service.go` сейчас обрабатывает только `nix:0` prefix:

```go
func (is *imageService) PullImage(ctx context.Context, req *runtime.PullImageRequest) (*runtime.PullImageResponse, error) {
    ref := req.Image.Image
    if !strings.HasPrefix(ref, nix2container.ImageRefPrefix) {
        // Не nix:0 → обычный CRI pull
        return client.PullImage(ctx, req)
    }
    // nix:0 → загрузка из Nix store
}
```

Патч: для обычных образов — перед передачей в CRI проверить manifest index, найти манифест с nix-аннотациями, и предпочесть его:

```go
if !strings.HasPrefix(ref, nix2container.ImageRefPrefix) {
    // Проверяем: это manifest index? Есть ли nix-манифест?
    if nixManifest := resolveNixManifest(ctx, ref); nixManifest != nil {
        return pullWithManifest(ctx, nixManifest)
    }
    return client.PullImage(ctx, req)
}
```

**Путь 2 — Два Deployment с общим Service (без патчей)**

nix-snapshotter **полностью обратно совместим** с обычными OCI-образами (из README: "Backwards-compatible with existing non-Nix images"). Если на слое нет nix-аннотаций, snapshotter работает как обычный overlay. Поэтому n2c-образ (`app-std`) **не нужно** ограничивать от nix-нод — он корректно работает везде.

```yaml
# Service (один, общий)
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  selector:
    app: python-uv-nix  # матчит поды из ОБОИХ deployment

---
# Deployment для nix-нод (оптимизированный, маунтпоинты из /nix/store)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-nix
spec:
  template:
    metadata:
      labels:
        app: python-uv-nix
    spec:
      nodeSelector:
        nix-snapshotter: "true"
      containers:
        - name: app
          image: ghcr.io/org/app-nix:latest

---
# Deployment для всех нод (стандартный OCI, работает везде включая nix-ноды)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-std
spec:
  template:
    metadata:
      labels:
        app: python-uv-nix
    spec:
      # БЕЗ affinity/nodeSelector — n2c образ работает на ВСЕХ нодах,
      # включая nix-ноды (nix-snapshotter обратно совместим с обычными OCI)
      containers:
        - name: app
          image: ghcr.io/org/app:latest
```

**Примечание:** на nix-нодах могут оказаться поды от обоих Deployment (и `app-nix`, и `app-std`). Если нужно чтобы на nix-ноде работал **только** оптимизированный образ, добавить affinity `nix-snapshotter: DoesNotExist` к `app-std`. Но обычно лишние реплики — это плюс к доступности.

Генерация из одного определения (Nix / Kustomize / Helm).

### Поведение

| Нода | Образ | Что скачивает | Размер pull |
|------|-------|---------------|-------------|
| Обычная | n2c (реальные слои) | Слои из GHCR | ~150MB (первый раз) |
| Nix | nix-snapshotter (маунтпоинты) | Маунтпоинты (~300B) + closure-info из substituters | ~несколько KB |

На nix-нодах — **НЕ скачивает тяжёлые слои вообще**. Только маунтпоинты + `nix build` closure-info.

### Плюсы и минусы

| | Плюсы | Минусы |
|---|---|---|
| Путь 1 (CRI патч) | Один тег, один Deployment, автоматика | Нужен патч nix-snapshotter |
| Путь 2 (два Deployment) | Работает сейчас, без патчей | Два манифеста (генерируются из одного) |

---

## Вариант B: Гибридный образ (n2c слои + аннотации)

### Идея

Один образ: реальные OCI слои от `nix2container` + `nix-closure` аннотация.

```
ghcr.io/org/app:latest
└── OCI Manifest
    ├── Layer 0: cacert + tzdata (реальные файлы)
    ├── Layer 1: Python venv (реальные файлы)
    └── Layer 2: App source (реальные файлы)
         annotations: { nix-closure: /nix/store/xyz-closure-info }
```

### Поведение

| Нода | Что происходит |
|------|----------------|
| Обычная | Качает слои из GHCR → overlayfs → работает |
| Nix | **Тоже качает слои из GHCR** → overlayfs → ПОТОМ bind mounts из /nix/store затеняют |

**Проблема:** на nix-нодах **всё равно скачиваются полные слои** (containerd content store не знает про аннотации). Bind mounts добавляются snapshotter'ом ПОСЛЕ скачивания.

### Когда это приемлемо

- Слои кешируются в content store → повторные pull мгновенные
- n2c разбивает образ на слои (runtime/deps/app) → при обновлении кода качается только слой app
- Если нет обычных нод → проще использовать чистый nix-snapshotter (вариант C)

---

## Вариант C: Только nix-snapshotter (текущий, для одного типа нод)

### Идея

Один образ через `nix-snapshotter.buildImage`, только для nix-нод.

```nix
nixSnapshotter.buildImage {
  name = "app";
  resolvedByNix = false;
  copyToRoot = [ appSrc ];
  config = { ... };
};
```

### Поведение

| Нода | Что происходит |
|------|----------------|
| Nix | Маунтпоинты (~300B) → bind mounts из /nix/store → работает |
| Обычная | Маунтпоинты (~300B) → пустые файлы → **CrashLoopBackOff** |

**Годится**, если все целевые ноды — nix-ноды. `nodeSelector: nix-snapshotter: "true"` обязателен.

---

## Вариант D: Только nix2container (без оптимизации)

### Идея

Один образ через `nix2container`, работает везде, без nix-snapshotter аннотаций.

```nix
n2c.buildImage {
  name = "app";
  layers = [ ... ];
  config = { ... };
};
```

### Поведение

| Нода | Что происходит |
|------|----------------|
| Любая | Качает слои из GHCR → overlayfs → работает |

Просто, надёжно, без оптимизации. n2c обеспечивает послойный кеш (runtime/deps/app меняются с разной частотой).

---

## Обратная совместимость nix-snapshotter

nix-snapshotter **полностью обратно совместим** с обычными OCI-образами. Если слой не содержит nix-аннотаций, snapshotter работает как стандартный overlay:

```go
// snapshotter.go — нет nix-closure, нет nix-layer → обычный overlayfs
return o.withNixBindMounts(ctx, key, mounts)
```

Это значит:
- n2c-образ (без аннотаций) **корректно работает** на nix-нодах
- `app-std` Deployment не нужно ограничивать от nix-нод
- На nix-ноде могут работать оба типа образов одновременно

---

## Сравнение вариантов

| | A: Два образа | B: Гибрид | C: Только nix-snap | D: Только n2c |
|---|---|---|---|---|
| Работает на обычных нодах | Да | Да | **Нет** | Да |
| Работает на nix-нодах | Да | Да | Да | Да |
| Nix-нода качает слои из GHCR | **Нет** (nix-образ) | Да | **Нет** | Да |
| Nix-нода использует /nix/store | Да | Да (shadow) | Да | Нет |
| Один тег в реестре | Да (с патчем) / Нет | Да | Да | Да |
| Один Deployment | С патчем / Нет | Да | Да | Да |
| Сложность CI | Средняя | Средняя | Простая | Простая |
| Нужен патч upstream | Для одного тега | Нет | Нет | Нет |
| nodeSelector обязателен | Только для nix-деплоя | Нет | **Да** | Нет |

---

## Форматы аннотаций nix-snapshotter

### Новый формат (v0.3.0+)

Одна аннотация на слой — путь к closure-info деривации:

```json
{
  "containerd.io/snapshot/nix-closure": "/nix/store/xyz-closure-info"
}
```

Closure-info — Nix-деривация (директория), содержащая файл `store-paths`:

```
/nix/store/abc-python-3.13.0
/nix/store/def-openssl-3.1.0
...
```

При pull: один вызов `nix build /nix/store/xyz-closure-info` → все store paths доступны.

**Требование:** closure-info деривация должна быть доступна через substituters.

### Legacy формат (до v0.3.0)

Маркер + отдельная аннотация на каждый store path:

```json
{
  "containerd.io/snapshot/nix-layer": "true",
  "containerd.io/snapshot/nix-store-path.0": "/nix/store/abc-python-3.13.0",
  "containerd.io/snapshot/nix-store-path.1": "/nix/store/def-openssl-3.1.0"
}
```

При pull: N вызовов `nix build` (по одному на каждый path). Медленно при 100+ paths.

### Сравнение

| | Новый (nix-closure) | Legacy (nix-store-path.N) |
|---|---|---|
| Скорость | 1 nix build | N nix build |
| Размер манифеста | Минимальный | Растёт с N |
| Требует binary cache | Да (для closure-info) | Нет |
| Статус | Актуальный | Deprecated |

### Комбинирование (fallback невозможен без патча)

Код проверяет новый формат первым и делает `return` без fallback:

```go
if closurePath, ok := base.Labels[NixClosureAnnotation]; ok {
    err = o.prepareNixGCRoot(ctx, key, closurePath)
    return mounts, err  // НЕ проваливается к legacy
}
```

Патч для fallback (~5 строк):

```go
if closurePath, ok := base.Labels[NixClosureAnnotation]; ok {
    if err := o.prepareNixGCRoot(ctx, key, closurePath); err == nil {
        return mounts, nil
    }
    log.G(ctx).Warnf("closure fallback to legacy: %v", err)
}
```

---

## CI/CD реализация (для варианта A)

### Nix: два образа + closure-info

```nix
# nix/oci.nix
{
  perSystem = { pkgs, system, venv, ... }:
  let
    n2c = inputs.nix2container.packages.${system}.nix2container;
    nixSnapshotter = inputs.nix-snapshotter.packages.${system}.nix-snapshotter;

    appSrc = pkgs.stdenv.mkDerivation { ... };

    ociClosureInfo = pkgs.closureInfo {
      rootPaths = [ pkgs.cacert pkgs.tzdata venv appSrc ];
    };
  in {
    packages = {
      # Обычный OCI (для нод без nix-snapshotter)
      oci-prod = n2c.buildImage {
        name = "app";
        config = { ... };
        layers = [
          (n2c.buildLayer { deps = [ pkgs.cacert pkgs.tzdata ]; })
          (n2c.buildLayer { deps = [ venv ]; })
          (n2c.buildLayer { deps = [ appSrc ]; })
        ];
      };

      # Nix-образ (для нод с nix-snapshotter)
      oci-nix = nixSnapshotter.buildImage {
        name = "app";
        resolvedByNix = false;
        copyToRoot = [ appSrc ];
        config = { ... };
      };

      # closure-info для аннотаций (если нужен гибрид)
      inherit ociClosureInfo;
    };
  };
}
```

### CI: сборка и push обоих образов

```bash
# Сборка
N2C=$(nix build .#oci-prod --print-out-paths --no-link)
NIX=$(nix build .#oci-nix --print-out-paths --no-link)

# Push n2c (для обычных нод)
nix run .#skopeo -- copy nix:$N2C docker://ghcr.io/org/app:${SHA}
nix run .#skopeo -- copy nix:$N2C docker://ghcr.io/org/app:latest

# Push nix (для nix-нод)
SKOPEO=$(nix build nixpkgs#skopeo.out --print-out-paths --no-link)
${SKOPEO}/bin/skopeo copy oci-archive:$NIX docker://ghcr.io/org/app-nix:${SHA}
${SKOPEO}/bin/skopeo copy oci-archive:$NIX docker://ghcr.io/org/app-nix:latest
```

### Deploy: kubectl set image для обоих deployment

```bash
kubectl set image deployment/app-std app=ghcr.io/org/app:${SHA}
kubectl set image deployment/app-nix app=ghcr.io/org/app-nix:${SHA}
kubectl rollout status deployment/app-std --timeout=120s
kubectl rollout status deployment/app-nix --timeout=120s
```

---

## Рекомендуемый план

### Сейчас (v1) — Вариант A, путь 2

Два Deployment + два образа. Без патчей, работает сегодня:

```
CI: build n2c + build nix-snap → push оба → deploy оба
Обычная нода: pull n2c → полные слои → работает
Nix-нода: pull nix-snap → маунтпоинты → bind mounts → мгновенно
```

### Скоро (v2) — P2P binary cache

Все ноды объединены в mesh substituters. Closure-info доступен мгновенно.

### Будущее (v3) — Вариант A, путь 1

Патч CRI Image Service → один тег, один Deployment:

```
CI: build оба → push в OCI Index → deploy
Любая нода: pull → CRI резолвит нужный манифест → оптимально
```

### Далёкое будущее (v4) — PR в nix-snapshotter

nix-snapshotter нативно генерирует гибридные образы с реальными слоями + аннотациями, и не качает слои на nix-нодах (remote snapshotter). Один образ для всех.

---

## Ссылки

- [nix-snapshotter](https://github.com/pdtpartners/nix-snapshotter) — containerd plugin (800 stars)
- [nix-snapshotter architecture](https://github.com/pdtpartners/nix-snapshotter/blob/main/docs/architecture.md)
- [nix-snapshotter v0.3.0](https://github.com/pdtpartners/nix-snapshotter/releases/tag/v0.3.0) — новый формат аннотаций
- [nix-snapshotter image_service.go](https://github.com/pdtpartners/nix-snapshotter/blob/main/pkg/nix/image_service.go) — CRI Image Service
- [nix-snapshotter snapshotter.go](https://github.com/pdtpartners/nix-snapshotter/blob/main/pkg/nix/snapshotter.go) — обработка аннотаций
- [nix2container](https://github.com/nlewo/nix2container) — Nix OCI image builder
- [OCI Image Index Spec](https://github.com/opencontainers/image-spec/blob/main/image-index.md) — manifest list формат
- [SOCI Snapshotter](https://github.com/awslabs/soci-snapshotter) — пример lazy-loading snapshotter (для референса)
