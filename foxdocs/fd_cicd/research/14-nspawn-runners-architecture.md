# Архитектура nspawn-runners с snix overlay-store

> Дата: 2026-04-07
> Контекст: microVM runners заменяются на systemd-nspawn контейнеры.
> MicroVM имели проблемы с virtiofs/sandbox и высокий overhead (hypervisor + VM kernel).
> nspawn обеспечивает нативную производительность overlay и значительно проще в дебаге.

---

## 1. Почему nspawn вместо microVM

| Критерий | microVM (cloud-hypervisor) | nspawn (systemd-nspawn) |
|----------|---------------------------|------------------------|
| Изоляция | KVM (полная) | Linux namespaces (достаточная для CI) |
| Store sharing | virtiofs (problematic sandbox) | OverlayFS native (ядро Linux) |
| Overhead | ~200-400MB RAM per VM + VM kernel | ~20-50MB per container |
| Дебаг | ssh root@vm, serial console | `machinectl shell runner-*` |
| Eval/build время | Замедляет flake eval (microvm input) | Нулевой overhead на eval |
| Startup time | 5-15s (VM boot) | <1s (container start) |
| Зависимости | cloud-hypervisor, virtiofsd, microvm.nix flake input | Только systemd (уже есть) |

Для trusted internal CI (сборка собственных проектов FatData) полная KVM-изоляция избыточна.
Namespace isolation через nspawn достаточна и является standard practice для CI runners.

---

## 2. Общая архитектура

```
┌──────────────────────────────────────────────────────────────────────┐
│  Host: perturabo                                                     │
│                                                                      │
│  ┌─────────────────────┐   ┌──────────────────────────────────────┐ │
│  │ snix-store-daemon    │   │ Host /nix/store (54 GB, read-only)  │ │
│  │ gRPC :8000           │   │ NixOS system closure + packages     │ │
│  │ castore /mnt (17 GB) │   └──────────┬─────────────────────────┘ │
│  └───┬──────────────────┘              │                            │
│      │                                  │                            │
│      ├─── snix FUSE mount              │                            │
│      │    /srv/snix-store (ro)         │                            │
│      │                                  │                            │
│      ├─── snix-nix-daemon              │                            │
│      │    /run/snix-daemon.sock        │                            │
│      │                                  │                            │
│      └─── snix-nar-bridge              │                            │
│           HTTP :9000                    │                            │
│                                         │                            │
│  ┌──────────────────────────────────────┴──────────────────────────┐ │
│  │  nspawn container: runner-fatdata-nix-build-1                   │ │
│  │                                                                  │ │
│  │  /nix/store = OverlayFS                                         │ │
│  │    lower 1: host /nix/store (bind-mount, ro)                    │ │
│  │    lower 2: /srv/snix-store (bind-mount, ro)                    │ │
│  │    upper:   /var/lib/runner-stores/...-nix-build-1/upper (rw)   │ │
│  │                                                                  │ │
│  │  nix-daemon (local-overlay-store)                                │ │
│  │    lower = unix:///run/snix-daemon.sock                         │ │
│  │    upper = per-runner writable layer                             │ │
│  │                                                                  │ │
│  │  github-runner (labels: snix, nspawn)                            │ │
│  │  docker.service                                                  │ │
│  │  post-build-hook → nix copy --to snix                           │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  nspawn container: runner-fatdata-nix-build-2                   │ │
│  │  (аналогичная структура)                                         │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  nspawn container: runner-fatdata-deploy-1                      │ │
│  │  (non-ephemeral, upper сохраняется между jobs)                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. OverlayFS /nix/store внутри контейнера

Каждый контейнер получает собственный OverlayFS `/nix/store` с двумя read-only lower layers
и одним writable upper layer:

```
mount -t overlay overlay \
  -o lowerdir=/nix/.host-store:/nix/.snix-store,\
     upperdir=/nix/.rw-store/upper,\
     workdir=/nix/.rw-store/work \
  /nix/store
```

### Lower layers

| Layer | Источник | Что содержит |
|-------|----------|-------------|
| lower 1 | Host `/nix/store` → bind-mount `/nix/.host-store` (ro) | NixOS system closure, runner binary, все пакеты хоста (~54 GB) |
| lower 2 | `/srv/snix-store` → bind-mount `/nix/.snix-store` (ro) | snix castore через FUSE — deduplicated content (~17 GB, но содержит 54+ GB в дедуплицированном виде) |

### Upper layer

Per-runner writable directory на хосте:

```
/var/lib/runner-stores/<org>-<type>-<idx>/upper/
/var/lib/runner-stores/<org>-<type>-<idx>/work/
```

Для ephemeral runners upper очищается после каждой job.
Для persistent runners (deploy) upper сохраняется между jobs.

### Порядок lookup в overlay

1. **upper** (per-runner writes) → найден? → используется
2. **lower 1** (host /nix/store) → найден? → используется, zero-copy
3. **lower 2** (snix castore) → найден? → FUSE read из castore, zero-copy на уровне overlay

---

## 4. Nix local-overlay-store внутри контейнера

Nix daemon внутри контейнера настраивается с experimental `local-overlay-store`:

```ini
# /etc/nix/nix.conf внутри контейнера
extra-experimental-features = nix-command flakes local-overlay-store
store = local-overlay://?lower-store=unix:///run/snix-daemon.sock&upper-layer=/nix/.rw-store/upper&check-mount=false
```

Это позволяет Nix daemon:
- Знать о содержимом snix castore через socket (lower-store)
- Записывать новые пакеты в upper layer
- Не трогать host /nix/store

**check-mount=false** — overlay mount создаётся вручную через ExecStartPre,
а не через nix daemon (он не имеет прав на mount внутри контейнера).

---

## 5. Поток данных при `nix build`

```
Runner: nix build .#oci-prod
  │
  ▼
nix-daemon (local-overlay-store)
  │
  ├─ 1) Ищет в upper (per-runner) → NOT FOUND (первый билд)
  │
  ├─ 2) Ищет в lower (snix socket) → FOUND?
  │     Если да → читает из snix castore через FUSE
  │     Zero-copy на уровне overlay layer
  │
  ├─ 3) Ищет в host store (через overlay lower) → FOUND?
  │     Если да → читает через overlay, zero-copy
  │
  ├─ 4) Если нигде нет → скачивает из cache.nixos.org
  │     Или собирает из исходников
  │
  ├─ 5) Результат пишется в upper layer
  │     /var/lib/runner-stores/.../upper/nix/store/<hash>-<name>
  │
  └─ 6) post-build-hook:
        nix copy --to unix:///run/snix-daemon.sock $OUT_PATHS
        → Результат попадает в snix castore
        → Следующий контейнер увидит его через lower 2
```

### Эффект: warm cache без дублирования

После первого билда в любом контейнере:
- Результат попадает в snix castore через post-build-hook
- Все остальные контейнеры видят его через lower 2 (snix FUSE)
- Нет копирования данных между контейнерами
- Content-addressed dedup на уровне чанков в snix

---

## 6. Networking

Каждый контейнер получает изолированную veth пару:

```
Host:  ve-runner-<N> → bridge br-runners (10.0.200.1/24)
Guest: host0         → DHCP 10.0.200.10+N
```

NAT masquerade для выхода в интернет:

```
nft add rule ip nat POSTROUTING oifname "enp6s0" ip saddr 10.0.200.0/24 masquerade
```

systemd-networkd на хосте:
- Bridge `br-runners` с DHCP сервером
- Match `ve-runner-*` → bridge

---

## 7. Ephemeral runners

Для `ephemeral = true` runners (рекомендуемо для CI):

1. GitHub runner регистрируется с `--ephemeral`
2. После выполнения одной job runner завершается
3. systemd перезапускает контейнер
4. `ExecStartPre`: очистка upper layer (`rm -rf upper/*`)
5. Контейнер стартует с чистым store (lower layers сохраняются)
6. Время перезапуска: <2s (vs 5-15s для microVM)

---

## 8. Сравнение с предыдущей microVM архитектурой

```
БЫЛО (microVM):

  snix-store-daemon ──→ virtiofsd (problematic, sandbox=none)
                            │
                       cloud-hypervisor
                            │
                        VM kernel boot (5-15s)
                            │
                        /nix/.ro-store (virtiofs)
                            │
                        OverlayFS → /nix/store
                            │
                        github-runner

СТАЛО (nspawn):

  snix-store-daemon ──→ FUSE mount /srv/snix-store (ro)
                            │
                            ├──→ bind-mount в контейнер (zero overhead)
                            │
  Host /nix/store ──────────┤
                            │
                       OverlayFS → /nix/store (native kernel)
                            │
                       github-runner
```

### Ключевые улучшения

1. **Убран virtiofs bottleneck** — overlay работает нативно в ядре
2. **Убран VM overhead** — нет hypervisor, нет отдельного kernel
3. **Убран microvm.nix input** — flake eval на ~30s быстрее
4. **Проще дебаг** — `machinectl shell` вместо ssh в VM
5. **Быстрый рестарт** — <2s вместо 5-15s

---

## 9. Модуль NixOS

Расположение: `vladOS-v2/modules/nixos/services/nspawn-runners/default.nix`

API совместим с `microvm-runners` (organizations/runners):

```nix
vladOS.services.nspawn-runners = {
  enable = true;
  snix.daemonSocket = "/run/snix-daemon.sock";
  snix.fuseMountPoint = "/srv/snix-store";
  networking.subnet = "10.0.200";
  containerDefaults.ephemeralUpper = true;

  organizations.fatdata = {
    url = "https://github.com/FatDataProduct";
    tokenFile = "/secrets/github-tokens/fatdata";
    runners = {
      nix-build = { count = 2; ephemeral = true; };
      deploy = { count = 1; ephemeral = false; };
    };
  };
};
```

Генерирует:
- `containers.runner-<org>-<type>-<idx>` — NixOS nspawn контейнер
- `systemd.services.runner-overlay-setup@<name>` — OverlayFS mount
- `systemd.tmpfiles.rules` — директории upper/work per runner
- Внутри контейнера: github-runner, docker, nix с overlay-store, post-build-hook

---

## 10. Риски и митигации

| Риск | Митигация |
|------|-----------|
| `local-overlay-store` — experimental | Используется production-ready часть (check-mount=false); fallback на обычный store |
| snix FUSE performance | Lower priority; host /nix/store как primary lower layer покрывает большинство пакетов |
| Namespace escape | Доверенный CI код; containers.*.privateNetwork = true; readonly bind mounts |
| Upper layer растёт | Ephemeral runners очищают upper; persistent runners — cron cleanup |

---

## Ресурсы

| Документ | Путь/URL |
|----------|----------|
| Snix overlay guide | https://snix.dev/docs/guides/local-overlay/ |
| Nix local-overlay-store | https://nix.dev/manual/nix/2.28/store/types/experimental-local-overlay-store |
| systemd-nspawn docs | https://www.freedesktop.org/software/systemd/man/systemd-nspawn.html |
| NixOS containers | https://nixos.wiki/wiki/NixOS_Containers |
| Enclaves модуль (паттерн) | `vladOS-v2/modules/nixos/enclaves/default.nix` |
| microvm-runners (заменяемый) | `vladOS-v2/modules/nixos/services/microvm-runners/default.nix` |
| snix модуль | `vladOS-v2/modules/nixos/services/snix/default.nix` |
| Текущий план | `fd_cicd/.cursor/plans/nspawn-runners_snix_overlay_ecf9f9be.plan.md` |
