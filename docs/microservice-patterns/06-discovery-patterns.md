# 06. Service Discovery Patterns

> **Как сервисы находят друг друга**

---

## Проблема обнаружения

В микросервисах адреса сервисов динамические:
- Сервисы масштабируются (появляются новые instances)
- Контейнеры перезапускаются (меняются IP)
- Деплои обновляют версии

**Hardcoded адреса не работают!**

Service Discovery отвечает: **где сейчас находится нужный сервис?**

---

## Паттерн 1: Client-side Discovery

### 💡 Суть

**Клиент сам** запрашивает Service Registry и выбирает instance для вызова.

### 📝 Техническое объяснение

1. Сервис регистрируется в **Service Registry** (Consul, etcd, Eureka)
2. Клиент запрашивает Registry: "где UserService?"
3. Registry возвращает список адресов
4. Клиент сам выбирает (load balancing на клиенте)

### 🏠 Аналогия: Справочник телефонов

Вам нужно позвонить в пиццерию. Client-side discovery:
1. Открываете **справочник** (Service Registry)
2. Находите все пиццерии в районе
3. **Сами выбираете**, куда звонить (ближайшую, с лучшими отзывами)
4. Звоните напрямую

Вы принимаете решение, куда обращаться.

### ✅ Когда использовать

- Нужен **умный load balancing** на клиенте
- Клиент хочет **кэшировать** адреса
- Не хотите доп. hop через load balancer

### ❌ Когда НЕ использовать

- Клиенты на разных языках (нужна библиотека для каждого)
- Хотите централизованный контроль routing
- Kubernetes (встроенный server-side)

### 🔧 Архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CLIENT-SIDE DISCOVERY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌────────────────────────────────────────────────────────┐               │
│   │                  Service Registry                       │               │
│   │                  (Consul / etcd)                        │               │
│   │                                                         │               │
│   │   user-service:                                         │               │
│   │     - 10.0.0.1:8000 (healthy)                          │               │
│   │     - 10.0.0.2:8000 (healthy)                          │               │
│   │     - 10.0.0.3:8000 (unhealthy)                        │               │
│   │                                                         │               │
│   └────────────────────────────────────────────────────────┘               │
│                              ▲                                              │
│                              │ 1. Query: "where is user-service?"          │
│                              │ 2. Response: [10.0.0.1, 10.0.0.2]           │
│                              │                                              │
│   ┌────────────────────────────────────────────────────────┐               │
│   │                     Order Service                       │               │
│   │                     (CLIENT)                            │               │
│   │                                                         │               │
│   │   3. Client-side load balancing                        │               │
│   │      → Round Robin / Random / Least Connections        │               │
│   │                                                         │               │
│   │   4. Direct call to chosen instance                    │               │
│   │      → GET http://10.0.0.1:8000/users/123              │               │
│   └─────────────────────────────┬──────────────────────────┘               │
│                                 │                                           │
│                                 ▼                                           │
│                        ┌────────────────┐                                  │
│                        │  User Service  │                                  │
│                        │  10.0.0.1:8000 │                                  │
│                        └────────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 2: Server-side Discovery

### 💡 Суть

Клиент обращается к **Load Balancer**, который сам находит и выбирает instance.

### 📝 Техническое объяснение

1. Сервисы регистрируются в Registry (или LB знает о них)
2. Клиент вызывает Load Balancer по фиксированному адресу
3. LB выбирает healthy instance
4. LB проксирует запрос

### 🏠 Аналогия: Колл-центр

Вам нужна техподдержка. Server-side discovery:
1. Звоните на **единый номер колл-центра** (Load Balancer)
2. Колл-центр **сам находит** свободного оператора
3. Соединяет вас

Вы не выбираете оператора — система делает это за вас.

### ✅ Когда использовать

- **Kubernetes** (DNS-based discovery из коробки)
- Клиенты на **разных языках**
- Хотите **централизованный** load balancing
- Простота для клиента

### ❌ Когда НЕ использовать

- Нужен client-specific load balancing
- Load Balancer — bottleneck
- Нужно минимизировать latency (доп. hop)

### 🔧 Архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SERVER-SIDE DISCOVERY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌────────────────────────────────────────────────────────┐               │
│   │                     Order Service                       │               │
│   │                     (CLIENT)                            │               │
│   │                                                         │               │
│   │   1. Call: GET http://user-service/users/123           │               │
│   │      (DNS name, not IP)                                │               │
│   │                                                         │               │
│   └─────────────────────────────┬──────────────────────────┘               │
│                                 │                                           │
│                                 ▼                                           │
│   ┌────────────────────────────────────────────────────────┐               │
│   │                   Load Balancer                         │               │
│   │              (Kubernetes Service / ELB)                 │               │
│   │                                                         │               │
│   │   2. DNS resolves "user-service" → LB                  │               │
│   │   3. LB selects healthy instance                       │               │
│   │   4. LB proxies request                                │               │
│   │                                                         │               │
│   └────────────┬────────────────────────────┬──────────────┘               │
│                │                            │                               │
│                ▼                            ▼                               │
│        ┌────────────────┐          ┌────────────────┐                      │
│        │  User Service  │          │  User Service  │                      │
│        │  Pod 1         │          │  Pod 2         │                      │
│        │  10.0.0.1:8000 │          │  10.0.0.2:8000 │                      │
│        └────────────────┘          └────────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Kubernetes Service Discovery

```yaml
# Kubernetes Service — автоматический server-side discovery
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP

---
# Теперь другие сервисы могут вызывать:
# http://user-service/users/123
# Kubernetes DNS резолвит → LB → Pod
```

---

## Паттерн 3: Service Registry

### 💡 Суть

**Централизованная база данных** с адресами всех сервисов.

### 📝 Техническое объяснение

Service Registry:
- Хранит список сервисов и их instances
- Health checks для определения доступности
- API для регистрации/обнаружения

### 🏠 Аналогия: Телефонный справочник

Service Registry — это **жёлтые страницы**:
- Все компании (сервисы) регистрируются
- Указывают адрес и телефон (host:port)
- Справочник обновляется при изменениях
- Любой может найти нужную компанию

### Популярные Registry

| Registry | Консенсус | Когда |
|----------|-----------|-------|
| **Consul** | Raft | Health checks, KV store, multi-DC |
| **etcd** | Raft | Kubernetes, простота |
| **Eureka** | Peer-to-peer | Netflix stack, Java |
| **Zookeeper** | ZAB | Legacy, Kafka |
| **Kubernetes DNS** | — | K8s native |

### 🔧 Пример: Consul

```python
# Регистрация сервиса в Consul
import consul

c = consul.Consul(host="consul", port=8500)

# Регистрация при старте
c.agent.service.register(
    name="user-service",
    service_id="user-service-1",
    address="10.0.0.1",
    port=8000,
    check=consul.Check.http(
        url="http://10.0.0.1:8000/health",
        interval="10s",
        timeout="5s",
    ),
)

# Обнаружение сервиса
_, services = c.health.service("user-service", passing=True)
instances = [
    f"{s['Service']['Address']}:{s['Service']['Port']}"
    for s in services
]
# ['10.0.0.1:8000', '10.0.0.2:8000']
```

---

## Сравнение Discovery Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  СРАВНЕНИЕ DISCOVERY PATTERNS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Паттерн          │ Кто выбирает │ Сложность │ Когда                       │
│  ─────────────────│──────────────│───────────│─────────────────────────────│
│                   │              │           │                              │
│  Client-side      │ Клиент       │ Высокая   │ Умный LB нужен              │
│                   │              │ (библ.)   │ Кэширование на клиенте      │
│                   │              │           │                              │
│  Server-side      │ LB/Router    │ Низкая    │ Kubernetes                   │
│                   │              │           │ Разные языки клиентов       │
│                   │              │           │                              │
│  Service Registry │ Хранит данные│ Средняя   │ Основа для обоих            │
│                   │              │           │ Consul/etcd/Eureka          │
│                   │              │           │                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Self-Registration vs Third-Party Registration

### Self-Registration

Сервис **сам регистрируется** при старте:

```python
# При запуске сервиса
async def on_startup():
    await consul.register(
        name="user-service",
        address=get_my_ip(),
        port=8000,
    )

# При остановке
async def on_shutdown():
    await consul.deregister()
```

### Third-Party Registration

**Внешний процесс** (registrar) следит за сервисами и регистрирует их:

```yaml
# Kubernetes делает это автоматически
# Registrar = kubelet + kube-proxy

# Когда Pod создаётся:
# 1. kubelet видит новый Pod
# 2. Обновляет Endpoints
# 3. kube-proxy обновляет правила
# 4. DNS резолвит Service name → Pod IPs
```

---

## Чеклист Discovery

```markdown
## Service Discovery Checklist

### Общее
- [ ] Выбран Registry (Consul / K8s DNS / etcd)
- [ ] Health checks настроены
- [ ] TTL для записей
- [ ] Graceful shutdown (deregister)

### Client-side
- [ ] Библиотека discovery для языка
- [ ] Кэширование адресов
- [ ] Refresh при ошибках
- [ ] Load balancing стратегия

### Server-side (Kubernetes)
- [ ] Service для каждого deployment
- [ ] Правильные selectors
- [ ] Readiness probes
- [ ] Service type (ClusterIP / LoadBalancer)
```

---

<div align="center">

[← API Patterns](./05-api-patterns.md) | **Discovery** | [Observability →](./07-observability-patterns.md)

</div>
