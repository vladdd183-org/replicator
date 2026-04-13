# 🔥 Firecracker microVM + nixos-fireactions: глубокое исследование

> Эфемерные микро-ВМ для CI/CD с аппаратной изоляцией на уровне KVM.
> Каждая CI job запускается в собственной microVM, уничтожаемой после завершения.

---

## 1. Firecracker microVM — что это и как работает

### 1.1 Суть технологии

Firecracker — это **Virtual Machine Monitor (VMM)**, написанный на Rust компанией AWS. Создан для запуска AWS Lambda и AWS Fargate. Открыт под Apache 2.0 в ноябре 2018 года.

**Ключевая идея:** безопасность полноценной ВМ + скорость и лёгкость контейнеров.

```
┌─────────────────────────────────────────────────────┐
│                    Host Linux                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ microVM 1│  │ microVM 2│  │ microVM N│           │
│  │┌────────┐│  │┌────────┐│  │┌────────┐│           │
│  ││ Guest  ││  ││ Guest  ││  ││ Guest  ││           │
│  ││ Kernel ││  ││ Kernel ││  ││ Kernel ││           │
│  │└────────┘│  │└────────┘│  │└────────┘│           │
│  │ virtio   │  │ virtio   │  │ virtio   │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │              │              │                 │
│  ┌────▼──────────────▼──────────────▼──────────────┐ │
│  │           Firecracker VMM (Rust)                 │ │
│  │         User-space process + Jailer              │ │
│  └──────────────────┬──────────────────────────────┘ │
│                     │                                 │
│  ┌──────────────────▼──────────────────────────────┐ │
│  │                 KVM (Kernel)                     │ │
│  │           Аппаратная виртуализация               │ │
│  │           Intel VT-x / AMD-V / ARM              │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 1.2 Почему быстрый — минималистичный дизайн

Firecracker эмулирует **только 5 устройств** (против сотен в QEMU):

| Устройство | Назначение |
|---|---|
| `virtio-net` | Сеть |
| `virtio-block` | Блочные устройства (диски) |
| `virtio-vsock` | Межпроцессная коммуникация host↔guest |
| Serial console | Консольный вывод |
| Keyboard controller | Только для остановки microVM |

Для сравнения: **QEMU — ~2 млн строк кода**, Firecracker — **~50 000 строк Rust**.

### 1.3 Время старта — реальные замеры

| Метрика | Значение | Примечание |
|---|---|---|
| **Спецификация** (InstanceStart → init) | **< 125 мс** | Только Firecracker VMM |
| **Cold boot** (end-to-end до SSH) | **~1 133 мс** | Включая всю оркестрацию |
| **Snapshot restore** (end-to-end) | **~176 мс** | Восстановление состояния |
| **Snapshot restore** (только API) | **4–10 мс** | Сам вызов restore |
| **Создание microVM** | До **150 VM/сек** | На один хост |

**Разбивка cold boot (~1 133 мс):**

```
Host setup (parallel):        80 мс  ( 7%)
Firecracker API config:      130 мс  (12%)
InstanceStart:                38 мс  ( 3%)
iptables DNAT rules:          33 мс  ( 3%)
Guest boot + readiness:      852 мс  (75%)  ← основное время
```

> Ключевое: спецификация в 125 мс — это **только вклад Firecracker**. 
> 75% времени уходит на загрузку Linux ядра и инициализацию гостевой ОС.

### 1.4 Потребление ресурсов

| Параметр | Значение |
|---|---|
| Memory overhead VMM | **< 5 MiB** на одну microVM |
| Минимальная RAM гостя | от 128 MiB |
| Диск (ядро) | ~5–10 MiB (минимальное ядро) |
| CPU overhead | Минимальный (паравиртуализация virtio) |
| Плотность | Тысячи microVM на одном сервере |

### 1.5 Модель изоляции (KVM + Jailer)

Firecracker использует **двухуровневую изоляцию:**

**Уровень 1 — KVM (аппаратный):**
- Каждая microVM работает в собственном **аппаратном контексте виртуализации**
- Отдельное ядро Linux для каждой VM
- Изоляция на уровне **транзисторов CPU** (VT-x/AMD-V)
- Уязвимость в гостевом ядре **не влияет** на хост и другие VM

**Уровень 2 — Jailer (программный):**
- Companion-процесс для каждого Firecracker VMM
- chroot, cgroups, seccomp фильтры
- **Вторая линия обороны** если виртуализация будет скомпрометирована

### 1.6 Firecracker vs Docker для CI — почему Firecracker лучше

| Аспект | Docker | Firecracker |
|---|---|---|
| **Модель изоляции** | Shared kernel (namespaces, cgroups) | Отдельное ядро (KVM) |
| **Поверхность атаки** | ~2M LOC (QEMU) + ядро хоста | ~50K LOC (Rust) |
| **Container escape** | Возможен (CVE-2019-5736 и др.) | Требует пробить KVM |
| **Boot time** | ~мгновенный (fork) | ~125 мс (спецификация) |
| **Memory overhead** | ~нулевой | < 5 MiB на VM |
| **Вложенный Docker** | Нативно | Требует кастомное ядро |
| **Сетевой throughput** | Нативный | Паравиртуализация (~нативный) |
| **Multi-tenant безопасность** | ❌ Недостаточна | ✅ Продакшн-уровень (AWS Lambda) |

**Вывод для CI/CD:** Docker достаточен при доверенном коде. Firecracker необходим когда:
- CI запускает **чужой/недоверенный код** (fork PR, open-source)
- Требуется **мультитенантность** (несколько клиентов на одном хосте)
- Нужна **гарантия изоляции** между jobs

### 1.7 Текущий статус Firecracker

| Параметр | Значение |
|---|---|
| GitHub Stars | **33 400+** |
| Forks | 2 300+ |
| Commits | 7 780+ |
| Последний релиз | **v1.14.2** (27 февраля 2026) |
| Язык | Rust |
| Лицензия | Apache 2.0 |
| Платформы | x86_64, aarch64 (Intel, AMD, ARM) |
| Пользователи | AWS Lambda, Fargate, Fly.io, Kata Containers, Koyeb и др. |

---

## 2. nixos-fireactions — подробный разбор

**GitHub:** [thpham/nixos-fireactions](https://github.com/thpham/nixos-fireactions)

NixOS модуль + deployment-тулинг для self-hosted CI runners в эфемерных Firecracker microVM.

### 2.1 Четырёхуровневая модульная архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 4: Profiles                        │
│  {runner}-{size}   registry-cache   prod/dev                │
│  Декларативные профили: размер VM, окружение, кеш           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 3: Runner Orchestrators                  │
│   fireactions/     fireteact/     fireglab/                 │
│   Go-программы, управляющие lifecycle microVM               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 2: Registry Cache (standalone)           │
│   Zot OCI cache + Squid HTTP proxy                         │
│   Pull-through кеш для container images                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 1: microvm-base (foundation)             │
│   Network bridges, containerd, DNSmasq, CNI plugins         │
│   Базовая инфраструктура для запуска microVM                │
└─────────────────────────────────────────────────────────────┘
```

#### Layer 1: microvm-base — фундамент

Базовая инфраструктура, необходимая для запуска любых Firecracker microVM:

- **Network bridges** — виртуальные сетевые мосты для каждого типа runner
- **containerd** — container runtime для управления образами rootfs
- **DNSmasq** — DNS/DHCP для microVM
- **CNI plugins** — сетевые плагины (bridge, host-local, firewall, tc-redirect-tap)
- **Firecracker** + **Jailer** — сам VMM

```nix
services.microvm-base = {
  enable = true;
  bridges = {
    # Каждый оркестратор регистрирует свой bridge
  };
  kernel.source = "upstream";  # или "custom" для Docker bridge внутри VM
  kernel.version = "6.1.141";
  dns.upstreamServers = ["8.8.8.8" "8.8.4.4"];
};
```

#### Layer 2: Registry Cache — кеширование

Standalone модуль, работает с любым runner. Уменьшает время pull образов:

- **Zot** — OCI-нативный pull-through кеш для container images (Docker Hub, ghcr.io и т.д.)
- **Squid** — HTTP/HTTPS прокси для остального трафика
- **SSL bump** — опциональный перехват HTTPS для глубокого кеширования

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Firecracker VM │────▶│   Zot (OCI)     │────▶│  Docker Hub     │
│  (containerd)   │     │   + Squid       │     │  ghcr.io, etc.  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

```nix
services.registry-cache = {
  enable = true;
  useMicrovmBaseBridges = true;  # авто-определение сетей

  zot = {
    enable = true;
    mirrors = {
      "docker.io" = {};
      "ghcr.io" = {};
    };
  };

  squid = {
    enable = true;
    sslBump.mode = "selective";
  };
};
```

#### Layer 3: Runner Orchestrators — Go-оркестраторы

Три отдельные Go-программы для разных CI-платформ:

| Оркестратор | Платформа | Метод Auth | Runner Agent | Bridge |
|---|---|---|---|---|
| **fireactions** | GitHub Actions | GitHub App | actions/runner | fireactions0 |
| **fireteact** | Gitea Actions | API Token | act_runner | fireteact0 |
| **fireglab** | GitLab CI | PAT (glrt-*) | gitlab-runner | fireglab0 |

Каждый оркестратор:
- Регистрирует свой network bridge через `microvm-base`
- Использует per-pool containerd namespaces для изоляции
- Поддерживает пулы runners с авто-масштабированием
- Интегрируется с `registry-cache`

#### Layer 4: Profiles — декларативные профили

Профили размеров (3 runner × 3 размера = 9 профилей):

| Размер | Ресурсы VM | Max Runners | Профили |
|---|---|---|---|
| small | 1 GB RAM, 1 vCPU | 2 | `fireactions-small`, `fireteact-small`, `fireglab-small` |
| medium | 2 GB RAM, 2 vCPU | 5 | `fireactions-medium`, `fireteact-medium`, `fireglab-medium` |
| large | 4 GB RAM, 4 vCPU | 10 | `fireactions-large`, `fireteact-large`, `fireglab-large` |

Профили окружений: `prod` (строгая безопасность) | `dev` (debug logging)

Профили нагрузки: `github-runners`, `gitea-runners`, `gitlab-runners`, `registry-cache`

### 2.2 Как происходит изоляция каждой job

```
CI Platform (GitHub/Gitea/GitLab)
    │
    │ Job назначен на self-hosted runner
    ▼
Оркестратор (fireactions/fireteact/fireglab)
    │
    │ 1. Pull rootfs image через containerd
    │ 2. Создать tap-устройство + сеть (CNI)
    │ 3. Подготовить rootfs (devmapper thin provisioning)
    ▼
Firecracker VMM + Jailer
    │
    │ 4. Запуск microVM с собственным Linux ядром
    │ 5. Guest boot → cloud-init → runner agent start
    │ 6. Runner регистрируется на CI-платформе
    ▼
CI Job выполняется внутри microVM
    │
    │ 7. Job завершён
    ▼
Оркестратор
    │
    │ 8. Runner де-регистрация
    │ 9. microVM уничтожается (SIGKILL)
    │ 10. Rootfs + thin pool удаляются
    │ 11. Сетевые ресурсы освобождаются
    ▼
Чистое состояние — ноль артефактов от предыдущей job
```

**Ключевые свойства изоляции:**
- Каждая job = **отдельная microVM с собственным ядром Linux**
- **Эфемерность** — VM уничтожается после job, zero state leaks
- **Per-pool containerd namespaces** — образы изолированы между пулами
- **Devmapper thin provisioning** — эффективное управление rootfs
- **KVM** — аппаратная изоляция между VM

### 2.3 Поддерживаемые CI-платформы

| Платформа | Модуль | Оркестратор | Auth | Статус |
|---|---|---|---|---|
| **GitHub Actions** | `nixosModules.fireactions` | fireactions (Go) | GitHub App (app_id + private_key) | ✅ Production |
| **Gitea Actions** | `nixosModules.fireteact` | fireteact (Go) | API Token | ✅ Работает |
| **GitLab CI** | `nixosModules.fireglab` | fireglab (Go) | PAT с `create_runner` scope | ✅ Работает |

Можно запускать **все три одновременно** на одном хосте:

```bash
./deploy/deploy.sh -p do -n multi-1 \
  -t prod,github-runners,gitlab-runners,fireactions-small,fireglab-medium <ip>
```

### 2.4 Полная конфигурация NixOS модуля

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixos-fireactions.url = "github:thpham/nixos-fireactions";
    nixos-fireactions.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, nixos-fireactions, ... }: {
    nixosConfigurations.my-runner = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        # Layer 1: Foundation
        nixos-fireactions.nixosModules.microvm-base

        # Layer 2: Caching (опционально)
        nixos-fireactions.nixosModules.registry-cache

        # Layer 3: Runner orchestrators (один или несколько)
        nixos-fireactions.nixosModules.fireactions   # GitHub Actions
        nixos-fireactions.nixosModules.fireteact      # Gitea Actions
        nixos-fireactions.nixosModules.fireglab        # GitLab CI

        {
          # ── GitHub Actions ──
          services.fireactions = {
            enable = true;
            github.appIdFile = "/run/secrets/github-app-id";
            github.appPrivateKeyFile = "/run/secrets/github-app-key";
            logLevel = "info";
            metricsEnable = true;       # Prometheus метрики
            metricsAddress = "127.0.0.1:8081";
            pools = [{
              name = "default";
              maxRunners = 5;
              minRunners = 1;
              runner = {
                organization = "your-org";
                labels = [ "self-hosted" "fireactions" "linux" ];
              };
            }];
          };

          # ── Gitea Actions ──
          services.fireteact = {
            enable = true;
            # ... gitea-specific config
          };

          # ── GitLab CI ──
          services.fireglab = {
            enable = true;
            # ... gitlab-specific config
          };

          # ── microvm-base (Foundation) ──
          services.microvm-base = {
            enable = true;
            kernel.source = "upstream";  # "custom" если нужен Docker bridge внутри VM
            kernel.version = "6.1.141";
            dns.upstreamServers = ["8.8.8.8" "8.8.4.4"];
          };

          # ── Registry Cache ──
          services.registry-cache = {
            enable = true;
            useMicrovmBaseBridges = true;
            zot = {
              enable = true;
              mirrors = {
                "docker.io" = {};
                "ghcr.io" = {};
              };
            };
          };
        }
      ];
    };
  };
}
```

### 2.5 Выбор ядра

| Ядро | Когда использовать | Время сборки |
|---|---|---|
| `firecracker-kernel` (upstream) | По умолчанию, быстрый boot, нет Docker внутри VM | ~30 сек (fetch) |
| `firecracker-kernel-custom` | Docker с bridge networking внутри VM | ~10–15 мин (компиляция) |

Custom ядро нужно если workflow использует `docker run` **без** `--network=host`.

### 2.6 Requirements

| Требование | Детали |
|---|---|
| **ОС хоста** | NixOS 25.11+ (kernel 6.1+) |
| **KVM** | Обязательно — `/dev/kvm` должен существовать |
| **CPU** | Intel VT-x или AMD-V или ARM с HW virtualization |
| **Железо** | Bare-metal (**рекомендуется**) или VPS с nested virtualization |
| **RAM** | Зависит от кол-ва runners (1–4 GB на VM + хост) |
| **Диск** | Выделенный блочный девайс для containerd (50 GB+ рекомендуется) |
| **Хостинг-провайдеры** | Hetzner bare-metal, DigitalOcean (2GB+ droplet), Azure |

**Nested virtualization:** работает на DigitalOcean, Hetzner Cloud и некоторых AWS инстансах (metal), но **не рекомендуется** для продакшна из-за overhead.

### 2.7 Deployment модель

Двухэтапный деплой:

**Этап 1 — Initial deploy (nixos-anywhere):**
```bash
# DigitalOcean
./deploy/deploy.sh --provider do --name do-runner-1 \
  --tags prod,github-runners,fireactions-medium 167.71.100.50

# Hetzner
./deploy/deploy.sh --provider hetzner --name hetzner-prod-1 \
  --tags prod 95.217.xxx.xxx

# Generic bare-metal
./deploy/deploy.sh --provider generic --name my-vm <ip>
```

**Этап 2 — Fleet updates (Colmena):**
```bash
colmena apply --on do-runner-1 --build-on-target   # один хост
colmena apply --on @prod --build-on-target          # по тегу
colmena apply --build-on-target                     # весь флот
```

### 2.8 Secrets management

Используется **sops-nix**:

| Секрет | Путь | Платформа |
|---|---|---|
| `github-app-id` | `/run/secrets/github-app-id` | GitHub |
| `github-app-key` | `/run/secrets/github-app-key` | GitHub |
| `gitea-api-token` | `/run/secrets/gitea-api-token` | Gitea |
| `gitea-instance-url` | `/run/secrets/gitea-instance-url` | Gitea |
| `gitlab-access-token` | `/run/secrets/gitlab-access-token` | GitLab |
| `gitlab-instance-url` | `/run/secrets/gitlab-instance-url` | GitLab |

### 2.9 Зрелость и активность проекта

| Параметр | Значение |
|---|---|
| GitHub Stars | **2** |
| Forks | 0 |
| Автор | thpham (единственный контрибьютор) |
| Первый коммит | ~декабрь 2025 |
| Последний коммит | **2 января 2026** |
| Текущая фаза | **Phase 3: Runtime** (core complete) |
| Лицензия | MIT |
| Архитектуры | x86_64-linux, aarch64-linux |

**Roadmap:**
- [x] Phase 1: Foundation (flake, module, packages)
- [x] Phase 2: Image builders & Deployment (nixos-anywhere, Azure, DO)
- [x] Phase 3: Runtime (registry cache, networking, Gitea/GitLab support)
- [x] Phase 3.5: Composable architecture (microvm-base, standalone registry-cache)
- [ ] Phase 4: CI & Testing

**Оценка зрелости: 🟡 Ранний проект.** Архитектура продуманная и модульная, активная разработка в декабре 2025 — январе 2026, но пока solo-developer, нет тестов (Phase 4), мало пользователей.

### 2.10 Upstream: fireactions (Hostinger)

nixos-fireactions использует [hostinger/fireactions](https://github.com/hostinger/fireactions) как upstream оркестратор для GitHub Actions:

| Параметр | Значение |
|---|---|
| GitHub Stars | **145** |
| Разработчик | Hostinger |
| Описание | BYOM (Bring Your Own Metal) GitHub runners в Firecracker VM |
| Документация | [fireactions.io](https://fireactions.io) |
| Версия | v2.0.1 |

---

## 3. Firecracker + Nix — экосистема проектов

### 3.1 microvm.nix (astro/microvm.nix)

**GitHub:** [microvm-nix/microvm.nix](https://github.com/microvm-nix/microvm.nix)
**Stars:** 2 439 | **Contributors:** 100+ | **Последний push:** март 2026

**Что это:** Nix Flake для сборки и запуска NixOS MicroVM на **8 разных гипервизорах**, включая Firecracker.

**microvm.nix vs nixos-fireactions:**

| Аспект | microvm.nix | nixos-fireactions |
|---|---|---|
| **Фокус** | Универсальные NixOS microVM | CI runners в Firecracker |
| **Гипервизоры** | 8 (Firecracker, QEMU, cloud-hypervisor, kvmtool, crosvm, stratovirt, vfkit, alioth) | Только Firecracker |
| **CI интеграция** | Нет (generic VM) | GitHub, Gitea, GitLab |
| **Nix store sharing** | ✅ Встроенная поддержка | ❌ Через container images |
| **Зрелость** | Зрелый, 2400+ stars | Ранний, 2 stars |
| **Отношение** | **Дополнение** (можно использовать вместе) | Использует Firecracker напрямую |

**Nix store sharing в microvm.nix:**

```nix
# Шаринг /nix/store хоста с microVM (read-only)
microvm.shares = [{
  tag = "ro-store";
  source = "/nix/store";
  mountPoint = "/nix/.ro-store";
}];

# Опциональный writable overlay
microvm.writableStoreOverlay = "/nix/.rw-store";
microvm.volumes = [{
  image = "nix-store-overlay.img";
  mountPoint = config.microvm.writableStoreOverlay;
  size = 2048;
}];
```

**Важное ограничение:** Firecracker **не поддерживает** 9p и virtiofs shares! Это означает, что при использовании Firecracker через microvm.nix нельзя шарить `/nix/store` хоста напрямую. Нужно использовать либо block device, либо предзаполненный squashfs/erofs.

### 3.2 Другие проекты Firecracker + Nix

| Проект | Описание | Звёзды |
|---|---|---|
| **microvm.nix** | Универсальный NixOS MicroVM framework | 2 439 |
| **nixos-fireactions** | CI runners в Firecracker | 2 |
| **firecracker-containerd** | containerd runtime для Firecracker (AWS) | ~700 |

### 3.3 Firecracker + Nix Store — текущие ограничения

**Проблема:** Firecracker не поддерживает shared filesystem протоколы (9p, virtiofs).

**Следствие для CI/CD с Nix:**
- Нельзя напрямую монтировать `/nix/store` хоста внутрь Firecracker VM
- Каждая VM должна иметь свой rootfs с нужными пакетами
- Nix store **не персистентен** между job'ами (VM эфемерная)

**Обходные пути:**

1. **OverlayFS на хосте** — базовый rootfs (read-only) + writable overlay для каждой VM:
   ```
   Base rootfs (shared, read-only)
       ↓ overlay
   Per-VM writable layer (уничтожается после job)
   ```

2. **Nix binary cache** — настроить Attic/Harmonia на хосте, VM скачивает нужные пакеты:
   ```
   Host: Attic cache server ← nix store
   VM: substituters = ["http://host-ip:8080"]
   ```

3. **Pre-built rootfs images** — запечь всё необходимое в container image:
   ```
   nix build → rootfs image → containerd → Firecracker VM
   ```

4. **virtio-block device** с `/nix/store` — монтировать block device (поддерживается):
   ```nix
   # Теоретически можно передать block device с /nix/store
   # Но требует специальной настройки и не поддерживается nixos-fireactions из коробки
   ```

---

## 4. Сравнение с обычным self-hosted runner

### 4.1 Развёрнутое сравнение

| Критерий | Self-hosted (bare-metal) | nixos-fireactions (Firecracker) |
|---|---|---|
| **Время старта job** | **~0 мс** (runner уже запущен) | **~1–2 сек** (boot microVM) |
| **Время старта (snapshot)** | N/A | **~176 мс** |
| **Memory overhead** | ~0 (нативный процесс) | **< 5 MiB на VM** + RAM гостя |
| **CPU overhead** | Нулевой | Минимальный (паравиртуализация) |
| **Disk I/O** | Нативный | Через virtio-block (близко к нативному) |
| **Изоляция между jobs** | ⚠️ Процессная (namespaces) | ✅ **KVM** (аппаратная) |
| **Утечка состояния** | ⚠️ Возможна (shared /nix/store, /tmp) | ✅ Невозможна (VM уничтожается) |
| **Персистентный /nix/store** | ✅ **Главный плюс** — повторные сборки ~секунды | ❌ Каждая job с нуля |
| **Nix cache** | Нативный (на диске) | Через binary cache (сеть) |
| **Повторная сборка** | **5–15 сек** | **Минуты** (pull зависимостей) |
| **Безопасность** | ⚠️ Уязвим к вредоносным PR | ✅ VM изоляция |
| **Сложность настройки** | 🟢 Простая (NixOS модуль) | 🟡 Средняя (KVM, bridges, containerd) |
| **Требования** | Любой Linux/NixOS | KVM + bare-metal |
| **Масштабирование** | Ограничено ресурсами хоста | Пулы VM с авто-масштабированием |
| **Multi-tenant** | ❌ Опасно | ✅ Безопасно |

### 4.2 Главный trade-off

```
Self-hosted runner:
  + Персистентный /nix/store = мгновенные повторные сборки
  + Нулевой overhead
  - Слабая изоляция
  - Утечка состояния между jobs

nixos-fireactions:
  + Максимальная изоляция (KVM)
  + Эфемерность = чистое состояние
  + Multi-tenant безопасность
  - Нет персистентного /nix/store
  - Overhead на boot + потеря кеша
```

### 4.3 Когда что выбирать

**Self-hosted runner (srvos/github-nix-ci):**
- Приватные проекты с доверенным кодом
- Частые сборки (>50/день) — критична скорость
- Большие Nix-проекты — персистентный store решает
- Solo/team разработка

**nixos-fireactions:**
- Open-source проекты (fork PR с чужим кодом)
- Мультитенантные платформы (SaaS CI)
- Требования к compliance/безопасности
- Запуск недоверенного кода
- Несколько CI-платформ одновременно (GitHub + Gitea + GitLab)

### 4.4 Гибридный подход (рекомендация)

Для Nix CI/CD оптимальным может быть **комбинация**:

```
┌──────────────────────────────────────────────────────────┐
│                    NixOS Host                             │
│                                                           │
│  ┌─────────────────────┐  ┌─────────────────────────┐    │
│  │  Self-hosted Runner  │  │  nixos-fireactions      │    │
│  │  (доверенный код)    │  │  (fork PR, чужой код)   │    │
│  │                      │  │                          │    │
│  │  /nix/store          │  │  Firecracker microVM     │    │
│  │  (persistent)        │  │  (ephemeral)             │    │
│  │  Label: nix-trusted  │  │  Label: nix-untrusted    │    │
│  └──────────────────────┘  └─────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Attic / Harmonia Binary Cache                      │  │
│  │  Shared между обоими типами runners                 │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

```yaml
# GitHub Actions workflow
jobs:
  trusted-build:
    if: github.event_name == 'push'
    runs-on: nix-trusted      # Self-hosted, быстрый /nix/store

  untrusted-build:
    if: github.event_name == 'pull_request'
    runs-on: nix-untrusted    # Firecracker VM, изолированный
```

---

## 5. Snapshot Restore — ускорение Firecracker для CI

Snapshot restore — способ частично решить проблему скорости:

### 5.1 Как работает

```
1. Boot microVM до "ready" состояния (все сервисы запущены)
2. Сделать snapshot (память + CPU + devices)
3. Сохранить snapshot на быстрый диск
4. Для новой job: restore snapshot вместо полного boot
```

### 5.2 Производительность snapshot restore

| Метрика | Cold boot | Snapshot restore | Ускорение |
|---|---|---|---|
| End-to-end (до SSH) | ~1 133 мс | **~176 мс** | **6.4×** |
| Firecracker API call | 38 мс | **4–10 мс** | **4–10×** |
| Рекордные замеры | - | **28 мс** (до ready) | - |

### 5.3 Copy-on-Write семантика

Страницы памяти snapshot'а маппятся как **read-only**. При записи — копирование (COW). Поскольку большинство страниц не модифицируются, restore практически мгновенный.

### 5.4 Warm Pool для CI

```
┌─────────────────────────────────────────┐
│            Warm Pool Manager             │
│                                          │
│  snapshot.mem + snapshot.vmstate          │
│  (pre-booted, runner agent ready)        │
│                                          │
│  Job приходит → restore snapshot         │
│  → runner уже запущен за ~176 мс         │
│  → job выполняется                       │
│  → VM уничтожается                       │
│  → следующая job из snapshot              │
└─────────────────────────────────────────┘
```

> Примечание: nixos-fireactions пока **не использует** snapshot restore. 
> Это потенциальное направление оптимизации (Phase 4+).

---

## 6. Итоговая оценка

### Firecracker для CI/CD

| Аспект | Оценка |
|---|---|
| Технологическая зрелость | 🟢 Продакшн (AWS Lambda/Fargate) |
| Безопасность изоляции | 🟢 Лучшая в индустрии (KVM) |
| Скорость boot | 🟢 < 125 мс (Firecracker) |
| Экосистема | 🟢 Большая (33K stars) |
| Пригодность для Nix CI | 🟡 Ограничена (нет shared /nix/store) |

### nixos-fireactions

| Аспект | Оценка |
|---|---|
| Архитектура | 🟢 Продуманная, модульная, composable |
| Multi-platform | 🟢 GitHub + Gitea + GitLab |
| NixOS интеграция | 🟢 Нативные NixOS модули |
| Deployment | 🟢 nixos-anywhere + Colmena |
| Зрелость | 🔴 Ранний проект (2 stars, solo dev) |
| Документация | 🟡 README хороший, но нет гайдов |
| Тесты | 🔴 Phase 4 (ещё не реализовано) |

### Рекомендация для вашего проекта

Для **типичного Nix CI/CD** (приватный проект, доверенный код):
→ **Self-hosted runner с srvos** — проще, быстрее, персистентный store

Для **продвинутых сценариев** (multi-tenant, untrusted code, compliance):
→ **nixos-fireactions** — стоит следить за развитием, архитектура правильная

Для **исследования/упоминания в дипломе/статье:**
→ Firecracker + nixos-fireactions — отличный пример передового подхода к CI безопасности
