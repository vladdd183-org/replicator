# nix-snapshotter: пилотная интеграция на perturabo

> Глубокий анализ nix-snapshotter v0.4.0 для гетерогенного k3s кластера.
> Включает исследование /nix/store pollution, механизм работы, и стратегию интеграции.

---

## Что такое nix-snapshotter

**nix-snapshotter** — containerd snapshotter plugin. Заменяет стандартный
механизм "скачать OCI-слои из реестра" на "взять `/nix/store` paths из
binary cache и создать bind mounts".

- **Репозиторий**: https://github.com/pdtpartners/nix-snapshotter
- **Версия**: v0.3.0 (в nixpkgs unstable)
- **k3s поддержка**: через proxy plugin + `--image-service-endpoint`

### Ключевые свойства

- Обратная совместимость: ноды с nix-snapshotter тянут и обычные OCI-образы
- Каждая k3s нода настраивает snapshotter независимо (мастера — `overlayfs`, агенты — `nix`)
- Два режима образов:
  - `resolvedByNix = true`: ссылка `nix:0/nix/store/xxx.tar`, реестр не нужен
  - `resolvedByNix = false`: ссылка `name:tag`, обычный OCI с nix-аннотациями

---

## Как nix-snapshotter работает внутри

### Архитектура

```
containerd (k3s embedded)
  ├── proxy_plugins.nix → remote snapshotter (gRPC socket)
  └── --image-service-endpoint → nix-snapshotter CRI proxy

nix-snapshotter (отдельный systemd сервис)
  ├── SnapshotsServer — remote snapshotter protocol
  └── ImageService — проксирует PullImage, резолвит nix:0 ссылки
```

### Процесс pull образа

1. containerd получает запрос на pull
2. nix-snapshotter читает OCI-манифест с аннотациями:
   ```json
   {
     "containerd.io/snapshot/nix-store-path.0": "/nix/store/xxx-glibc-2.37-8",
     "containerd.io/snapshot/nix-store-path.1": "/nix/store/yyy-python-3.13",
     ...
   }
   ```
3. Для каждого store path вызывает `NixBuilder`:
   ```go
   // pkg/nix/nix.go — defaultNixBuilder
   func defaultNixBuilder(ctx context.Context, outLink, nixStorePath string) error {
       args = append(args, "--add-root", outLink)
       args = append(args, "--realise", nixStorePath)
       exec.Command("nix-store", args...).CombinedOutput()
   }
   ```
4. `nix-store --realise` идёт через системный nix-daemon → скачивает NAR из substituters → распаковывает в `/nix/store`
5. Создаёт GC root в `<root>/gcroots/<snapshot-id>/`
6. При создании контейнера — bind mounts из `/nix/store/*` в rootfs:
   ```go
   // pkg/nix/snapshotter.go — withNixBindMounts
   mounts = append(mounts, mount.Mount{
       Type:    "bind",
       Source:  nixStorePath,    // /nix/store/xxx
       Target:  nixStorePath,    // /nix/store/xxx
       Options: []string{"ro", "rbind"},
   })
   ```

### Garbage Collection

Двойной GC:
- **containerd GC**: удаляет snapshot → удаляет GC roots из `gcroots/`
- **nix GC**: удаляет store paths без GC roots

Пока pod жив — paths защищены. После удаления — автоматическая очистка.

### Расширяемость

nix-snapshotter поддерживает замену `NixBuilder`:
- `WithNixBuilder(fn)` — программная замена
- `NewExternalBuilder(name)` — кастомный внешний скрипт

Это открывает путь для будущей интеграции с overlay-store (mount namespace).

---

## Критический момент: containerd proxy plugin

### Проблема

k3s embedded containerd по умолчанию не знает, что такое snapshotter "nix".
При `--snapshotter nix` containerd ищет зарегистрированный plugin, не находит,
и k3s застревает в бесконечном цикле:

```
level=info msg="Waiting for containerd startup: rpc error: code = Unimplemented
  desc = unknown service runtime.v1.RuntimeService"
```

### Решение: config.toml.tmpl

k3s позволяет расширять конфиг containerd через template файл:
`/var/lib/rancher/k3s/agent/etc/containerd/config.toml.tmpl`

Шаблон использует Go template синтаксис. `{{ template "base" . }}` вставляет
стандартный k3s containerd конфиг, а мы добавляем proxy plugin:

```toml
{{ template "base" . }}

[proxy_plugins.nix]
  type = "snapshot"
  address = "/run/nix-snapshotter/nix-snapshotter.sock"
```

Это говорит containerd: "для snapshotter nix — шли gRPC запросы на сокет
nix-snapshotter". Теперь containerd знает, как маршрутизировать snapshot
операции на внешний nix-snapshotter сервис.

### Реализация в NixOS модуле

Template создаётся через `system.activationScripts` (выполняется при
`nixos-rebuild switch` до перезапуска сервисов):

```nix
containerdNixTmpl = pkgs.writeText "k3s-containerd-nix.toml.tmpl" ''
  {{ template "base" . }}

  [proxy_plugins.nix]
    type = "snapshot"
    address = "/run/nix-snapshotter/nix-snapshotter.sock"
'';

system.activationScripts.k3s-nix-snapshotter = lib.mkIf (cfg.snapshotter == "nix") ''
  mkdir -p /var/lib/rancher/k3s/agent/etc/containerd
  cp -f ${containerdNixTmpl} /var/lib/rancher/k3s/agent/etc/containerd/config.toml.tmpl
'';
```

### Диагностика

Если `ctr plugins ls` НЕ показывает "nix" — это нормально. nix-snapshotter
работает как **remote/proxy** snapshotter, не как built-in containerd plugin.
Он не появляется в списке плагинов, но containerd маршрутизирует на него через
proxy_plugins конфиг.

Проверить работу:
```bash
# Сокет существует
ls -la /run/nix-snapshotter/nix-snapshotter.sock

# Сервис работает
systemctl status nix-snapshotter

# containerd config содержит proxy_plugins
sudo cat /var/lib/rancher/k3s/agent/etc/containerd/config.toml.tmpl
```

---

## Исправленная проблема: extraFlags list vs string

### Проблема

Модуль nix-snapshotter из флейка добавлял `services.k3s.extraFlags` как список:
```nix
extraFlags = [ "--snapshotter ${cfg.snapshotter}" ];
```

Наш k3s модуль использовал `toString(...)`, превращая список в строку.
NixOS не может смержить определения разных типов (list + string) для одной опции:

```
error: A definition for option `services.k3s.extraFlags' is not of type
  `string or list of string'.
  - In `.../modules/nixos/k3s.nix': ["--snapshotter overlayfs"]
  - In `.../services/k3s/default.nix': "--node-ip 10.0.0.2 ..."
```

Плюс оба модуля добавляли `--snapshotter`, создавая дублирование.

### Решение

1. Убрали `toString()` — extraFlags теперь выдаёт список
2. Убрали `--snapshotter` из наших флагов — модуль nix-snapshotter сам добавляет
3. Добавили `snapshotter = cfg.snapshotter;` для проброса значения в модуль nix-snapshotter

```nix
services.k3s = {
  snapshotter = cfg.snapshotter;  # bridge к модулю nix-snapshotter
  extraFlags =
    cfg.extraFlags
    ++ lib.optional (cfg.nodeIP != null) "--node-ip ${cfg.nodeIP}"
    ++ lib.optional (cfg.nodeIP != null) "--node-external-ip ${cfg.nodeIP}"
    ++ lib.optional (cfg.flannelInterface != null) "--flannel-iface=${cfg.flannelInterface}"
    ++ lib.optional (cfg.snapshotter == "nix")
      "--image-service-endpoint unix:///run/nix-snapshotter/nix-snapshotter.sock"
    ++ map (l: "--node-label ${l}") cfg.nodeLabels;
};
```

---

## Проблема: /nix/store pollution

### Суть

nix-snapshotter пишет runtime closure в системный `/nix/store`. Bind mounts
жёстко привязаны к `/nix/store/*` — пути обязаны существовать в системном store.

Это напоминает старую проблему с CI-сборками, когда build-time deps засоряли
системный store. Но есть принципиальные отличия:

### Сравнение: CI build deps vs runtime closure

| Параметр    | CI-сборка (старая проблема)    | nix-snapshotter runtime         |
|-------------|--------------------------------|---------------------------------|
| Что в store | Компиляторы, headers, dev-deps | Только runtime: python, libs    |
| Объём       | 10-20 ГБ на проект             | 200-500 МБ на приложение        |
| Lifecycle   | Никакого — накапливалось       | GC roots от containerd          |
| Шаринг      | Нет                            | glibc, openssl уже есть на NixOS|

### Выбранная стратегия

Прагматичный подход: runtime closure в `/nix/store` + автоматический GC.

Обоснование:
- Малая часть от build-time deps
- GC roots управляются containerd (удалил pod → убрался root → `nix-collect-garbage` почистит)
- snix `nar-bridge` как substituter — fetch из локального snix (быстро, без интернета)
- На NixOS ноде многие paths уже существуют (shared runtime libs)
- `auto-optimise-store = true` дедуплицирует файлы через hardlinks

### Путь эволюции (если pollution станет проблемой)

Mount namespace для k3s (аналог nspawn-раннеров):
- Overlay `/nix/store`: snix FUSE lower + ephemeral upper
- Системный `/nix/store` остаётся чистым
- nix-snapshotter поддерживает `WithNixBuilder` для кастомной логики

---

## Архитектура пилота на perturabo

### Текущая инфраструктура

- **perturabo-gpu4gb-node0**: NixOS, k3s agent, snix castore, CI nspawn-раннеры
- **snix компоненты**: store daemon (gRPC), FUSE mount `/srv/snix-store`, nix-daemon `/run/snix-daemon.sock`, nar-bridge `:9000`
- **Post-build-hook**: CI автоматически пушит store paths в snix

### Что добавлено

```
snix nar-bridge (localhost:9000) → extra-substituters в nix.settings
nix-snapshotter service → containerd proxy snapshotter
config.toml.tmpl → proxy_plugins.nix регистрация в containerd
k3s --snapshotter=nix → использует nix-snapshotter вместо overlayfs
k3s --image-service-endpoint → CRI image proxy через nix-snapshotter
nix.gc.automatic = true → еженедельная очистка неиспользуемых paths
```

### Поток данных

```
CI build → post-build-hook → snix castore
                                    ↓
k3s pull → nix-snapshotter → nix-store --realise → nix-daemon
                                                      ↓
                                              snix nar-bridge (substituter)
                                                      ↓
                                              /nix/store (runtime closure)
                                                      ↓
                                              bind mounts → container rootfs
```

### CI/CD деплой поток

```
CI: nix build .#nix-image → store path (image manifest)
    ↓
CI: nix build .#nix-image-ref → извлекает image reference (nix:0<path>)
    ↓
CI: sed подставляет image reference в k8s/deployment.yaml
    ↓
CI: kubectl apply → k3s API server
    ↓
k3s scheduler → perturabo (nodeSelector: nix-snapshotter=true)
    ↓
nix-snapshotter → nix-store --realise → snix nar-bridge → /nix/store
    ↓
container запущен с bind mounts из /nix/store
```

### Дедупликация на каждом уровне

| Уровень                | Без nix-snapshotter            | С nix-snapshotter                  |
|------------------------|--------------------------------|------------------------------------|
| Сборка в CI            | snix castore (store paths)     | snix castore (без изменений)       |
| Хранилище образов      | GHCR (OCI-слои)                | snix binary cache (store paths)    |
| Pull на ноду           | Полные OCI-слои из GHCR        | Только отсутствующие store paths   |
| Кросс-проектная дедуп  | Нет                            | Полная (общие пакеты = 1 раз)      |
| Диск на ноде           | containerd snapshots           | /nix/store с GC roots              |

---

## NixOS конфигурация

### vladOS-v2 k3s модуль (modules/nixos/services/k3s/default.nix)

```nix
# Containerd proxy plugin config template
containerdNixTmpl = pkgs.writeText "k3s-containerd-nix.toml.tmpl" ''
  {{ template "base" . }}

  [proxy_plugins.nix]
    type = "snapshot"
    address = "/run/nix-snapshotter/nix-snapshotter.sock"
'';

# Activation script — создаёт template до старта k3s
system.activationScripts.k3s-nix-snapshotter = lib.mkIf (cfg.snapshotter == "nix") ''
  mkdir -p /var/lib/rancher/k3s/agent/etc/containerd
  cp -f ${containerdNixTmpl} /var/lib/rancher/k3s/agent/etc/containerd/config.toml.tmpl
'';

# Bridge our option to nix-snapshotter module
services.k3s = {
  snapshotter = cfg.snapshotter;
  extraFlags = [ ... ]  # list, NOT toString()!
};

# Service dependencies
systemd.services.k3s = lib.mkIf (cfg.snapshotter == "nix") {
  path = [ pkgs.nix ];
  after = [ "nix-snapshotter.service" ];
  wants = [ "nix-snapshotter.service" ];
};
```

### perturabo-gpu4gb-node0/default.nix

```nix
vladOS.services.k3s = {
  snapshotter = "nix";
  setEmbeddedContainerd = true;
  nodeLabels = [ "nix-snapshotter=true" ];
};

services.nix-snapshotter.enable = true;

nix.settings.extra-substituters = [ "http://localhost:9000?priority=30" ];
nix.gc = {
  automatic = lib.mkForce true;
  dates = "weekly";
  options = "--delete-older-than 7d";
};
nix.settings.auto-optimise-store = true;
```

---

## Риски и откат

- **Откат**: убрать `snapshotter = "nix"` → k3s вернётся к overlayfs
- **Совместимость**: nix-snapshotter тянет и обычные OCI-образы (fallback на GHCR)
- **k3s + nix-snapshotter**: свежая интеграция, возможны edge cases
- **Стратегия**: пилот только на perturabo, angron не трогаем
- **proxy_plugins.nix**: обязателен, иначе containerd не знает о nix snapshotter
- **config.toml.tmpl**: k3s генерирует config.toml при каждом старте из этого шаблона

---

## Ошибки и решения (журнал)

### 1. extraFlags: list vs string type mismatch
```
error: A definition for option `services.k3s.extraFlags' is not of type
  `string or list of string'
```
**Причина**: наш модуль использовал `toString()`, а nix-snapshotter модуль — список.
**Решение**: убрали `toString()`, убрали дублирующий `--snapshotter`, добавили bridge.

### 2. nix.gc.automatic: conflicting definitions
```
error: The option `nix.gc.automatic' has conflicting definition values
```
**Причина**: common suite ставит `false`, perturabo ставит `true`.
**Решение**: `lib.mkForce true` в конфиге perturabo.

### 3. systemd.services.k3s: duplicate attribute definition
```
error: attribute 'systemd.services.k3s' already defined
```
**Причина**: два блока `systemd.services.k3s` на одном уровне в Nix.
**Решение**: объединили `path`, `after`, `wants` в один блок.

### 4. containerd startup loop
```
level=info msg="Waiting for containerd startup: rpc error: code = Unimplemented
  desc = unknown service runtime.v1.RuntimeService"
```
**Причина**: containerd не знает snapshotter "nix" — отсутствует proxy plugin config.
**Решение**: добавили `config.toml.tmpl` с `[proxy_plugins.nix]` через activation script.

---

## Следующие шаги

1. Проверить что k3s стартует с proxy plugin config
2. Протестировать деплой nix-snapshotter образа на perturabo
3. Проверить что snix nar-bridge работает как substituter для nix-store --realise
4. Замерить время pull по сравнению с OCI-образом из GHCR
5. Если pollution станет проблемой → mount namespace подход
