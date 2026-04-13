# 🔮 Будущее: nixidy (K8s через Nix) и nix-snapshotter

> Два проекта, которые могут изменить наш деплой.
> Пока не для production, но важно знать и следить.

---

## 🚢 nixidy — Kubernetes манифесты через Nix

### 🎯 Что это

**nixidy** = Nix + Argo CD. Декларативное управление Kubernetes через Nix вместо YAML/Helm/Kustomize.

**Сайт**: [nixidy.dev](https://nixidy.dev)

### 📊 Как работает

```
Nix modules → nixidy build → YAML манифесты → Git → Argo CD → Kubernetes
```

```
┌─────────────┐     ┌──────────┐     ┌─────────┐     ┌────────────┐
│  flake.nix  │────▶│ nixidy   │────▶│  YAML   │────▶│  Argo CD   │
│  (K8s as    │     │ build    │     │ (plain, │     │  (GitOps)  │
│   Nix       │     │ .#prod   │     │  review-│     │            │
│   modules)  │     │          │     │  able)  │     │            │
└─────────────┘     └──────────┘     └─────────┘     └────────────┘
```

### 🟢 Что даёт

| Фича | Описание |
|------|----------|
| 🔒 Type-checking | Каждый K8s ресурс проверяется на типы при сборке |
| 🔁 Reproducibility | Одинаковый input → одинаковый YAML, всегда |
| 🎛️ Multi-env | dev / staging / prod из общей базы + overrides |
| 🧩 Helm + Kustomize | Интегрирует существующие Helm charts, можно override'ить values |
| 📋 Reviewable | Генерирует чистый YAML → легко review в PR |
| 🔄 Git strategies | Monorepo / environment branches / separate repos |

### 📋 Пример

```nix
# flake.nix
{
  inputs.nixidy.url = "github:arnarg/nixidy";

  outputs = { nixidy, ... }: {
    nixidyEnvs.x86_64-linux = nixidy.lib.mkEnvs {
      prod = {
        # Kubernetes ресурсы как Nix модули
        applications.myapp = {
          helm.releases.myapp = {
            chart = nixidy.lib.helm.fetch {
              repo = "https://charts.example.com";
              chart = "myapp";
              version = "1.2.3";
            };
            values = {
              replicaCount = 3;
              image.repository = "ghcr.io/myorg/myapp";
              image.tag = "prod";
            };
          };
        };
      };
    };
  };
}
```

```bash
nixidy build .#prod     # → генерирует YAML
git add . && git commit  # → Argo CD подхватывает
```

### 🤔 Как это вписывается в наш CI/CD

```
nix build .#oci-prod       → OCI-образ в registry
nixidy build .#prod         → K8s YAML с тегом нового образа
git push manifests          → Argo CD деплоит
```

Вместо `SSH + kubectl` (как в автопостере) → полный GitOps:
- ✅ Версионированные манифесты в Git
- ✅ Argo CD следит за diff и деплоит
- ✅ Rollback = git revert
- ✅ Audit trail

### ⚠️ Текущий статус

- Проект активный, документация хорошая
- Но: требует ArgoCD в кластере
- Порог входа: Nix + Kubernetes + GitOps — нужен опыт во всех трёх
- **Рекомендация**: упомянуть в шаблоне как "advanced" путь, не базовый

---

## 📦 nix-snapshotter — Nix вместо Docker вообще

### 🎯 Что это

containerd плагин, который понимает Nix store paths как контейнерные образы.
Вместо `docker pull image:tag` → `nix build .#myapp` → containerd запускает напрямую.

**GitHub**: [pdtpartners/nix-snapshotter](https://github.com/pdtpartners/nix-snapshotter) (799 ⭐)
**Версия**: v0.4.0 (февраль 2025)

### 📊 Как работает

```
Традиционно:
  Developer → nix build → OCI tarball → Registry → containerd → pull layers → run

С nix-snapshotter:
  Developer → nix build → /nix/store/xxx-myapp → containerd → запуск напрямую!
  
  Нет: tarballs, registry, layers, pull
```

### 🔬 Технические детали

- Nix store path = полный граф зависимостей (runtime closure)
- `/nix/store/hash-name` уже содержит ВСЁ что нужно для запуска
- nix-snapshotter говорит containerd: "используй этот store path как rootfs"
- Binary cache / локальный store = "registry"
- **Обратная совместимость**: обычные Docker-образы тоже работают

### 🚢 Kubernetes интеграция

```yaml
# Pod spec с nix store path вместо image:tag
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: myapp
      image: nix:0rvhnqd9qizxy2m0s0s4mnjjaqiv3ln6-myapp
      # ↑ Nix store path as image reference!
```

- ✅ CRI Image Service — K8s "пуллит" из Nix store
- ✅ Нет registry — `/nix/store` на каждой ноде или binary cache
- ✅ k3s PR #9319 — интеграция в процессе

### 🤔 Что это меняет для CI/CD

Если nix-snapshotter на нодах K8s:
1. ❌ Не нужен OCI registry (GHCR)
2. ❌ Не нужен nix2container
3. ❌ Не нужен skopeo push
4. ✅ `nix build` → store path → K8s manifest → деплой
5. ✅ Binary cache как "registry" (Attic/Harmonia)

**CI/CD упрощается до:**
```
nix build .#myapp → nix copy --to cache → update K8s manifest → deploy
```

### ⚠️ Текущий статус

| Аспект | Статус |
|--------|--------|
| 💻 containerd plugin | ✅ Работает (v0.4.0) |
| 🚢 Kubernetes CRI | ✅ Работает |
| 🐙 k3s интеграция | ⏳ PR открыт (#9319) |
| 📊 Production use | ⚠️ Экспериментально |
| 📖 Документация | 🟡 Базовая |
| 👥 Community | 799 ⭐, активная разработка |

### 💡 Рекомендация для шаблона

- 📌 Упомянуть как **перспективный** подход
- ❌ НЕ делать основным вариантом (ещё не production-ready)
- 📝 Описать архитектуру для понимания куда всё движется
- 🔄 Проверить через полгода — может стать основным

---

## 📊 Сравнение подходов к деплою

| | Текущий (SSH+kubectl) | nixidy + ArgoCD | nix-snapshotter |
|-|----------------------|----------------|-----------------|
| 🏗️ Сложность | 🟢 Простая | 🟡 Средняя | 🔴 Высокая (пока) |
| 🔄 GitOps | ❌ | ✅ | ✅ (с nixidy) |
| 📦 Registry нужен | ✅ | ✅ | ❌ |
| 🐳 OCI нужен | ✅ | ✅ | ❌ |
| 🔒 Воспроизводимость | ⚠️ | ✅ | ✅✅ |
| ⚡ Скорость деплоя | Быстрая | Средняя (Argo sync) | Очень быстрая |
| 📊 Зрелость | ✅ Production | ✅ Production | ⚠️ Experimental |

---

## 🗺️ Дорожная карта

```
СЕЙЧАС:
  nix2container → GHCR → kubectl (Вариант 1/2)

СЛЕДУЮЩИЙ ШАГ:
  nix2container → GHCR → nixidy → ArgoCD (GitOps)

БУДУЩЕЕ:
  nix build → nix-snapshotter → K8s (без OCI, без registry)
```
