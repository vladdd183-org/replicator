# 🌐 Istio Ambient Mesh для Hyper-Porto

> **Версия:** 1.0  
> **Дата:** Январь 2026  
> **Назначение:** Практическое руководство по применению Istio Ambient Mesh в архитектуре Hyper-Porto — от модульного монолита до микросервисов

---

## 📋 Содержание

1. [Что такое Istio Ambient Mesh](#1-что-такое-istio-ambient-mesh)
2. [Почему Ambient Mesh идеально подходит для Hyper-Porto](#2-почему-ambient-mesh-идеально-подходит-для-hyper-porto)
3. [Архитектурные диаграммы](#3-архитектурные-диаграммы)
4. [Три уровня зрелости с Ambient Mesh](#4-три-уровня-зрелости-с-ambient-mesh)
5. [Практические сценарии применения](#5-практические-сценарии-применения)
6. [Интеграция с существующей инфраструктурой](#6-интеграция-с-существующей-инфраструктурой)
7. [Безопасность и mTLS](#7-безопасность-и-mtls)
8. [Observability и телеметрия](#8-observability-и-телеметрия)
9. [Traffic Management](#9-traffic-management)
10. [Пошаговое внедрение](#10-пошаговое-внедрение)
11. [Изменения в коде](#11-изменения-в-коде)
12. [Kubernetes манифесты](#12-kubernetes-манифесты)
13. [Чеклисты и лучшие практики](#13-чеклисты-и-лучшие-практики)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Что такое Istio Ambient Mesh

### 1.1 Проблема традиционного Sidecar режима

В классическом Istio каждый pod получает **sidecar proxy (Envoy)**, который:
- Добавляет **~100-200MB RAM** на каждый pod
- Увеличивает **latency** на каждый запрос
- Требует **перезапуска pod** при обновлении proxy
- Усложняет **debugging** (traffic идёт через прокси)

### 1.2 Революция Ambient Mesh

**Ambient Mesh** — это новый режим Istio без sidecar'ов:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIDECAR MODE (классический)                          │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Pod                                                                      │ │
│  │  ┌───────────────────┐  ┌──────────────────────────────────┐            │ │
│  │  │   Application     │  │   Envoy Sidecar                  │            │ │
│  │  │   Container       │◄─┤   (100-200MB RAM)                │◄── Traffic │ │
│  │  │                   │  │   - mTLS                          │            │ │
│  │  │                   │  │   - L7 Policy                     │            │ │
│  │  │                   │  │   - Telemetry                     │            │ │
│  │  └───────────────────┘  └──────────────────────────────────┘            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

                                    ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│                         AMBIENT MODE (новый)                                  │
│                                                                               │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐            │
│  │ Pod A           │   │ Pod B           │   │ Pod C           │            │
│  │  ┌───────────┐  │   │  ┌───────────┐  │   │  ┌───────────┐  │            │
│  │  │   App     │  │   │  │   App     │  │   │  │   App     │  │            │
│  │  │   Only!   │  │   │  │   Only!   │  │   │  │   Only!   │  │            │
│  │  └───────────┘  │   │  └───────────┘  │   │  └───────────┘  │            │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘            │
│           │                     │                     │                      │
│           └──────────────┬──────┴──────────────┬──────┘                      │
│                          │                     │                              │
│                          ▼                     ▼                              │
│              ┌─────────────────────────────────────────────┐                 │
│              │              ztunnel (per-node)              │                 │
│              │  - L4 mTLS encryption                        │                 │
│              │  - Identity (SPIFFE)                         │                 │
│              │  - L4 Authorization                          │                 │
│              │  - L4 Telemetry                              │                 │
│              └─────────────────────────────────────────────┘                 │
│                                    │                                          │
│                                    ▼ (только если нужен L7)                   │
│              ┌─────────────────────────────────────────────┐                 │
│              │           Waypoint Proxy (optional)          │                 │
│              │  - L7 Routing (HTTPRoute)                    │                 │
│              │  - L7 Authorization                          │                 │
│              │  - L7 Telemetry                              │                 │
│              │  - Traffic splitting / Canary                │                 │
│              └─────────────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Компоненты Ambient Mesh

| Компонент | Назначение | Где работает |
|-----------|------------|--------------|
| **ztunnel** | L4 secure overlay (mTLS, identity, L4 policy) | DaemonSet на каждой ноде |
| **Waypoint Proxy** | L7 features (routing, L7 policy, telemetry) | Deployment per-namespace |
| **istiod** | Control Plane (конфигурация, сертификаты) | Отдельный pod |
| **HBONE** | HTTP-Based Overlay Network (туннель) | Протокол между ztunnel'ами |

### 1.4 Преимущества для Hyper-Porto

| Аспект | Sidecar | Ambient | Выигрыш для Hyper-Porto |
|--------|---------|---------|-------------------------|
| **RAM** | +100-200MB/pod | Общий ztunnel | 8 модулей × 100MB = **800MB экономии** |
| **CPU** | Per-pod | Shared | Меньше ресурсов |
| **Startup** | Медленнее | Быстрее | Fast scaling |
| **Updates** | Restart pods | Hot reload | Zero-downtime |
| **Complexity** | Высокая | Ниже | Проще debugging |
| **L7 opt-in** | Всегда | По требованию | Платим за то, что используем |

---

## 2. Почему Ambient Mesh идеально подходит для Hyper-Porto

### 2.1 Архитектурное соответствие

Ваша архитектура Hyper-Porto уже подготовлена для Service Mesh:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HYPER-PORTO ARCHITECTURE                              │
│                                                                               │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                          App.py (Litestar)                           │   │
│   │  ┌──────────────────────────────────────────────────────────────┐   │   │
│   │  │                     Containers (Modules)                      │   │   │
│   │  │                                                               │   │   │
│   │  │  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────────┐│   │   │
│   │  │  │ UserModule  │ │ SearchModule │ │ NotificationModule     ││   │   │
│   │  │  │ - Auth      │ │ - Indexing   │ │ - Alerts                ││   │   │
│   │  │  │ - Profile   │ │ - Full-text  │ │ - Push                  ││   │   │
│   │  │  └─────────────┘ └──────────────┘ └─────────────────────────┘│   │   │
│   │  │                                                               │   │   │
│   │  │  ┌─────────────┐ ┌──────────────┐ ┌─────────────────────────┐│   │   │
│   │  │  │AuditModule  │ │SettingsModule│ │ VendorSection           ││   │   │
│   │  │  │ - Logging   │ │ - Flags      │ │ - Email, Payment,       ││   │   │
│   │  │  │ - Tracking  │ │ - Config     │ │   Webhooks              ││   │   │
│   │  │  └─────────────┘ └──────────────┘ └─────────────────────────┘│   │   │
│   │  └──────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
│   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐   │
│   │    litestar.events │  │   Redis (Cache)    │  │  PostgreSQL (DB)   │   │
│   │    Domain Events   │  │   TaskIQ Queue     │  │  Per-module tables │   │
│   └────────────────────┘  └────────────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

                                    ▼
                         
                    AMBIENT MESH ДОПОЛНЯЕТ ЭТО:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│   🔐 mTLS между сервисами (ztunnel)                                          │
│   📊 L4/L7 метрики без изменения кода                                        │
│   🚦 Traffic management (canary, A/B)                                        │
│   🛡️ Authorization policies (L4 + L7)                                       │
│   🔍 Distributed tracing (интеграция с Logfire)                              │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Эволюция от монолита к микросервисам с Ambient Mesh

Согласно вашей документации (`docs/17-microservice-extraction-guide.md`), система эволюционирует в три этапа:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                   │
│  УРОВЕНЬ 1: МОДУЛЬНЫЙ МОНОЛИТ                                                                                    │
│  ─────────────────────────────                                                                                   │
│                                                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                    Single Pod + ztunnel                                                      │ │
│  │                                                                                                               │ │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐   │ │
│  │   │                              Hyper-Porto App                                                         │   │ │
│  │   │   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │   │ │
│  │   │   │  UserModule   │ │  SearchModule │ │NotificationMod│ │  AuditModule  │ │SettingsModule │         │   │ │
│  │   │   └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘         │   │ │
│  │   │                                    litestar.events (in-process)                                      │   │ │
│  │   └─────────────────────────────────────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                    │                                                         │ │
│  │                                                    │                                                         │ │
│  │                                              ztunnel                                                         │ │
│  │                                          (L4 mTLS к Redis/DB)                                               │ │
│  │                                                    │                                                         │ │
│  └────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────┘ │
│                                                       │                                                           │
│                                          ┌────────────┴───────────┐                                              │
│                                          ▼                        ▼                                              │
│                                   ┌────────────┐           ┌────────────┐                                        │
│                                   │   Redis    │           │ PostgreSQL │                                        │
│                                   └────────────┘           └────────────┘                                        │
│                                                                                                                   │
│  ✅ Ambient Mesh даёт:                                                                                           │
│     - mTLS к Redis/PostgreSQL                                                                                    │
│     - L4 telemetry (TCP metrics)                                                                                 │
│     - Authorization policies                                                                                      │
│                                                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

                                                    ▼

┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                   │
│  УРОВЕНЬ 2: DISTRIBUTED MONOLITH                                                                                 │
│  ───────────────────────────────                                                                                 │
│                                                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                    Kubernetes Cluster                                                       │  │
│  │                                                                                                              │  │
│  │   ┌────────────────────────┐    ┌────────────────────────┐    ┌────────────────────────┐                   │  │
│  │   │   Main App Pod         │    │   Search Service Pod   │    │   Worker Pod           │                   │  │
│  │   │                        │    │                        │    │                        │                   │  │
│  │   │   ┌──────────────────┐ │    │   ┌──────────────────┐ │    │   ┌──────────────────┐ │                   │  │
│  │   │   │   UserModule     │ │    │   │   SearchModule   │ │    │   │   TaskIQ Worker  │ │                   │  │
│  │   │   │   AuditModule    │ │    │   │                  │ │    │   │                  │ │                   │  │
│  │   │   │   Notification   │ │    │   │                  │ │    │   │                  │ │                   │  │
│  │   │   │   Settings       │ │    │   │                  │ │    │   │                  │ │                   │  │
│  │   │   └──────────────────┘ │    │   └──────────────────┘ │    │   └──────────────────┘ │                   │  │
│  │   └───────────┬────────────┘    └───────────┬────────────┘    └───────────┬────────────┘                   │  │
│  │               │                             │                             │                                 │  │
│  │               │                             │                             │                                 │  │
│  │               ▼                             ▼                             ▼                                 │  │
│  │   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐ │  │
│  │   │                                         ztunnel (per-node)                                            │ │  │
│  │   │                                                                                                        │ │  │
│  │   │      ┌─────────────────────────────────────────────────────────────────────────────────┐              │ │  │
│  │   │      │                           HBONE Tunnel (mTLS)                                    │              │ │  │
│  │   │      │   Main App ◄───────────────► Search Service ◄───────────────► Worker            │              │ │  │
│  │   │      │         ▲                           ▲                            ▲               │              │ │  │
│  │   │      │         │                           │                            │               │              │ │  │
│  │   │      │         └────────────────┬──────────┴────────────┬───────────────┘               │              │ │  │
│  │   │      └──────────────────────────┼───────────────────────┼───────────────────────────────┘              │ │  │
│  │   │                                 │                       │                                              │ │  │
│  │   └─────────────────────────────────┼───────────────────────┼──────────────────────────────────────────────┘ │  │
│  │                                     ▼                       ▼                                                │  │
│  │                            ┌─────────────────┐     ┌─────────────────┐                                       │  │
│  │                            │  Redis Streams  │     │   PostgreSQL    │                                       │  │
│  │                            │  (Events)       │     │                 │                                       │  │
│  │                            └─────────────────┘     └─────────────────┘                                       │  │
│  │                                                                                                              │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                                   │
│  ✅ Ambient Mesh даёт:                                                                                           │
│     - mTLS между всеми сервисами (автоматически!)                                                                │
│     - Service discovery                                                                                           │
│     - L4 Authorization между сервисами                                                                           │
│     - Централизованные метрики                                                                                   │
│                                                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

                                                    ▼

┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                   │
│  УРОВЕНЬ 3: МИКРОСЕРВИСЫ + WAYPOINT PROXIES                                                                      │
│  ──────────────────────────────────────────                                                                      │
│                                                                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                                    Kubernetes Cluster                                                       │  │
│  │                                                                                                              │  │
│  │   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐            │  │
│  │   │ user-service   │ │ search-service │ │notification-svc│ │ payment-service│ │webhook-service │            │  │
│  │   │                │ │                │ │                │ │                │ │                │            │  │
│  │   │  ┌──────────┐  │ │  ┌──────────┐  │ │  ┌──────────┐  │ │  ┌──────────┐  │ │  ┌──────────┐  │            │  │
│  │   │  │UserModule│  │ │  │SearchMod │  │ │  │NotifMod  │  │ │  │PaymentMod│  │ │  │WebhookMod│  │            │  │
│  │   │  └──────────┘  │ │  └──────────┘  │ │  └──────────┘  │ │  └──────────┘  │ │  └──────────┘  │            │  │
│  │   └───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬────────┘ └───────┬────────┘            │  │
│  │           │                  │                  │                  │                  │                      │  │
│  │           │                  │                  │                  │                  │                      │  │
│  │           └──────────────────┴──────────────────┴──────────────────┴──────────────────┘                      │  │
│  │                                                 │                                                             │  │
│  │                                                 │                                                             │  │
│  │                                                 ▼                                                             │  │
│  │           ┌─────────────────────────────────────────────────────────────────────────────────────────────┐    │  │
│  │           │                                   ztunnel (L4)                                               │    │  │
│  │           │                                                                                               │    │  │
│  │           │   ┌─────────────────────────────────────────────────────────────────────────────────────┐    │    │  │
│  │           │   │                               HBONE (mTLS)                                           │    │    │  │
│  │           │   │   user-svc ◄────► search-svc ◄────► notif-svc ◄────► payment-svc ◄────► webhook-svc │    │    │  │
│  │           │   └─────────────────────────────────────────────────────────────────────────────────────┘    │    │  │
│  │           │                                                                                               │    │  │
│  │           └───────────────────────────────────────┬───────────────────────────────────────────────────────┘    │  │
│  │                                                   │                                                             │  │
│  │                                                   │ (L7 features needed)                                        │  │
│  │                                                   ▼                                                             │  │
│  │           ┌─────────────────────────────────────────────────────────────────────────────────────────────┐    │  │
│  │           │                              Waypoint Proxy (L7)                                             │    │  │
│  │           │                                                                                               │    │  │
│  │           │   ┌──────────────────────────────────────────────────────────────────────────────────────┐   │    │  │
│  │           │   │   HTTPRoute: Canary Deployments                                                       │   │    │  │
│  │           │   │   - 90% traffic → user-service-v1                                                     │   │    │  │
│  │           │   │   - 10% traffic → user-service-v2                                                     │   │    │  │
│  │           │   │                                                                                        │   │    │  │
│  │           │   │   AuthorizationPolicy: L7 rules                                                        │   │    │  │
│  │           │   │   - Allow GET /api/v1/users/** from any authenticated                                 │   │    │  │
│  │           │   │   - Deny POST /api/v1/admin/** unless from admin namespace                            │   │    │  │
│  │           │   │                                                                                        │   │    │  │
│  │           │   │   RequestAuthentication: JWT validation                                                │   │    │  │
│  │           │   │   - Validate tokens from issuer                                                        │   │    │  │
│  │           │   └──────────────────────────────────────────────────────────────────────────────────────┘   │    │  │
│  │           │                                                                                               │    │  │
│  │           └───────────────────────────────────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                                                              │  │
│  │                                                                                                              │  │
│  │   ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐   │  │
│  │   │                                       External Dependencies                                          │   │  │
│  │   │                                                                                                       │   │  │
│  │   │   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │   │  │
│  │   │   │  PostgreSQL  │   │    Redis     │   │    Kafka     │   │ Elasticsearch│   │  Prometheus  │       │   │  │
│  │   │   │  (user-db)   │   │   (cache)    │   │  (events)    │   │  (search)    │   │  (metrics)   │       │   │  │
│  │   │   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘       │   │  │
│  │   │                                                                                                       │   │  │
│  │   └─────────────────────────────────────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                                                              │  │
│  └──────────────────────────────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                                                   │
│  ✅ Ambient Mesh даёт (полный набор):                                                                            │
│     - Zero-trust networking (mTLS everywhere)                                                                     │
│     - L7 traffic management (canary, A/B, fault injection)                                                       │
│     - L7 authorization (path-based, header-based)                                                                │
│     - JWT validation на уровне mesh                                                                              │
│     - Rich observability (Kiali, Jaeger, Prometheus)                                                             │
│     - Circuit breakers, retries, timeouts                                                                        │
│                                                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Архитектурные диаграммы

### 3.1 Текущее состояние: Модульный монолит

```mermaid
flowchart TB
    subgraph Client["🌐 Clients"]
        Browser["Browser"]
        Mobile["Mobile App"]
        CLI["CLI"]
    end

    subgraph K8s["☸️ Kubernetes Cluster"]
        subgraph AmbientMesh["🌊 Istio Ambient Mesh"]
            subgraph MainPod["📦 Main Application Pod"]
                Litestar["Litestar App<br/>:8000"]
                
                subgraph Containers["Containers (Modules)"]
                    UserMod["UserModule<br/>Auth, Profile"]
                    SearchMod["SearchModule<br/>Full-text search"]
                    NotifMod["NotificationModule<br/>Alerts, Push"]
                    AuditMod["AuditModule<br/>Logging"]
                    SettingsMod["SettingsModule<br/>Feature Flags"]
                    EmailMod["EmailModule<br/>Virtual"]
                    PaymentMod["PaymentModule<br/>Virtual"]
                    WebhookMod["WebhookModule<br/>Outbound"]
                end
                
                Events["litestar.events<br/>(in-process)"]
            end
            
            subgraph WorkerPod["⚙️ Worker Pod"]
                TaskIQ["TaskIQ Worker<br/>Background Jobs"]
            end
            
            ztunnel1["ztunnel<br/>(Node DaemonSet)"]
        end
        
        subgraph Infra["🏗️ Infrastructure"]
            Redis["Redis<br/>Cache + Queue"]
            PostgreSQL["PostgreSQL<br/>app.db"]
        end
    end
    
    Browser --> Litestar
    Mobile --> Litestar
    CLI --> Litestar
    
    UserMod <--> Events
    SearchMod <--> Events
    NotifMod <--> Events
    AuditMod <--> Events
    WebhookMod <--> Events
    
    Litestar <--> ztunnel1
    TaskIQ <--> ztunnel1
    ztunnel1 <--> Redis
    ztunnel1 <--> PostgreSQL
    
    style AmbientMesh fill:#e1f5fe
    style ztunnel1 fill:#c8e6c9
```

### 3.2 Целевое состояние: Микросервисы с Waypoint Proxies

```mermaid
flowchart TB
    subgraph Client["🌐 Clients"]
        Browser["Browser"]
        Mobile["Mobile App"]
        API["External APIs"]
    end

    subgraph K8s["☸️ Kubernetes Cluster"]
        subgraph Ingress["🚪 Ingress"]
            Gateway["Istio Gateway<br/>(Ingress)"]
        end
        
        subgraph AmbientMesh["🌊 Istio Ambient Mesh"]
            subgraph DefaultNS["📁 default namespace"]
                subgraph UserSvc["user-service"]
                    UserApp["UserModule<br/>Auth, Profile, CRUD"]
                end
                
                subgraph SearchSvc["search-service"]
                    SearchApp["SearchModule<br/>Indexing, Full-text"]
                end
                
                subgraph NotifSvc["notification-service"]
                    NotifApp["NotificationModule<br/>Alerts, Push"]
                end
                
                WaypointDefault["Waypoint Proxy<br/>(default namespace)"]
            end
            
            subgraph VendorNS["📁 vendor namespace"]
                subgraph PaymentSvc["payment-service"]
                    PaymentApp["PaymentModule<br/>Payments, Refunds"]
                end
                
                subgraph WebhookSvc["webhook-service"]
                    WebhookApp["WebhookModule<br/>Delivery, Retry"]
                end
                
                WaypointVendor["Waypoint Proxy<br/>(vendor namespace)"]
            end
            
            subgraph SupportNS["📁 support namespace"]
                subgraph AuditSvc["audit-service"]
                    AuditApp["AuditModule<br/>Logging, Compliance"]
                end
            end
            
            ztunnel["ztunnel<br/>(per-node DaemonSet)"]
        end
        
        subgraph DataNS["📁 data namespace"]
            PostgreSQL["PostgreSQL<br/>(per-service DB)"]
            Redis["Redis<br/>Cache + Events"]
            Kafka["Kafka<br/>Event Streaming"]
        end
        
        subgraph ObservabilityNS["📁 observability namespace"]
            Prometheus["Prometheus"]
            Grafana["Grafana"]
            Kiali["Kiali<br/>Service Mesh UI"]
            Jaeger["Jaeger<br/>Tracing"]
            Logfire["Logfire<br/>(already integrated)"]
        end
    end
    
    Browser --> Gateway
    Mobile --> Gateway
    API --> Gateway
    
    Gateway --> WaypointDefault
    WaypointDefault --> UserApp
    WaypointDefault --> SearchApp
    WaypointDefault --> NotifApp
    
    Gateway --> WaypointVendor
    WaypointVendor --> PaymentApp
    WaypointVendor --> WebhookApp
    
    UserApp <--> ztunnel
    SearchApp <--> ztunnel
    NotifApp <--> ztunnel
    PaymentApp <--> ztunnel
    WebhookApp <--> ztunnel
    AuditApp <--> ztunnel
    
    ztunnel <--> PostgreSQL
    ztunnel <--> Redis
    ztunnel <--> Kafka
    
    ztunnel -.-> Prometheus
    Prometheus --> Grafana
    Prometheus --> Kiali
    
    style AmbientMesh fill:#e1f5fe
    style ztunnel fill:#c8e6c9
    style WaypointDefault fill:#fff3e0
    style WaypointVendor fill:#fff3e0
```

### 3.3 Потоки данных с Ambient Mesh

```mermaid
sequenceDiagram
    participant Client as 🌐 Client
    participant Gateway as 🚪 Istio Gateway
    participant ztunnel_src as ztunnel (source)
    participant Waypoint as Waypoint Proxy
    participant ztunnel_dst as ztunnel (dest)
    participant UserSvc as user-service
    participant SearchSvc as search-service
    participant Kafka as Kafka
    
    Note over Client, Kafka: 1️⃣ HTTP Request Flow (L7 через Waypoint)
    
    Client->>Gateway: POST /api/v1/users
    Gateway->>ztunnel_src: Route to user-service
    ztunnel_src->>Waypoint: HBONE tunnel (mTLS)
    
    Note over Waypoint: L7 Processing:<br/>- JWT validation<br/>- AuthorizationPolicy<br/>- Rate limiting<br/>- Routing rules
    
    Waypoint->>ztunnel_dst: Forward (HBONE)
    ztunnel_dst->>UserSvc: Decrypt & deliver
    
    Note over UserSvc: CreateUserAction<br/>→ UoW.commit()<br/>→ UserCreated event
    
    UserSvc-->>ztunnel_dst: Response
    ztunnel_dst-->>Waypoint: HBONE
    Waypoint-->>ztunnel_src: HBONE
    ztunnel_src-->>Gateway: Response
    Gateway-->>Client: 201 Created
    
    Note over Client, Kafka: 2️⃣ Event Flow (L4 через ztunnel)
    
    UserSvc->>ztunnel_dst: Publish UserCreated
    ztunnel_dst->>Kafka: HBONE (mTLS, L4)
    
    Kafka->>ztunnel_src: Deliver to search-service
    ztunnel_src->>SearchSvc: Decrypt & deliver
    
    Note over SearchSvc: IndexEntityTask<br/>→ Update search index
    
    Note over Client, Kafka: ✅ Весь трафик зашифрован<br/>✅ Identity проверен (SPIFFE)<br/>✅ Метрики собраны автоматически
```

### 3.4 Структура сети с ztunnel и HBONE

```mermaid
flowchart LR
    subgraph Node1["🖥️ Node 1"]
        subgraph Pod1["Pod: user-service"]
            App1["Application<br/>(no sidecar!)"]
        end
        
        ztunnel1["ztunnel<br/>DaemonSet"]
        
        App1 -.->|"iptables<br/>redirect"| ztunnel1
    end
    
    subgraph Node2["🖥️ Node 2"]
        subgraph Pod2["Pod: search-service"]
            App2["Application<br/>(no sidecar!)"]
        end
        
        ztunnel2["ztunnel<br/>DaemonSet"]
        
        ztunnel2 -.->|"iptables<br/>redirect"| App2
    end
    
    ztunnel1 <-->|"HBONE Tunnel<br/>mTLS + HTTP/2<br/>Port 15008"| ztunnel2
    
    subgraph istiod["Control Plane"]
        Istiod["istiod"]
    end
    
    Istiod -->|"xDS API<br/>Config + Certs"| ztunnel1
    Istiod -->|"xDS API<br/>Config + Certs"| ztunnel2
    
    style ztunnel1 fill:#c8e6c9
    style ztunnel2 fill:#c8e6c9
    style istiod fill:#bbdefb
```

---

## 4. Три уровня зрелости с Ambient Mesh

### 4.1 Уровень 1: L4 Only (ztunnel)

**Когда использовать:** Начальный этап, монолит или distributed monolith.

**Что получаем:**
- ✅ mTLS между всеми pods (автоматически)
- ✅ L4 Authorization Policies
- ✅ TCP метрики (bytes, connections)
- ✅ SPIFFE identity для каждого workload

**Что НЕ получаем:**
- ❌ L7 routing (HTTPRoute)
- ❌ L7 authorization (path-based)
- ❌ HTTP метрики (latency, status codes)
- ❌ Request-level tracing

```yaml
# Включение L4 для namespace
apiVersion: v1
kind: Namespace
metadata:
  name: hyper-porto
  labels:
    istio.io/dataplane-mode: ambient  # Только это!
```

### 4.2 Уровень 2: L4 + Waypoint для критичных сервисов

**Когда использовать:** Нужен L7 для части сервисов (user-service, payment-service).

**Что получаем:**
- Всё из L4
- ✅ L7 routing для выбранных сервисов
- ✅ JWT validation на mesh уровне
- ✅ Rate limiting, retries, timeouts
- ✅ HTTP метрики и tracing

```yaml
# Waypoint для user-service
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: user-waypoint
  namespace: hyper-porto
  labels:
    istio.io/waypoint-for: service
spec:
  gatewayClassName: istio-waypoint
  listeners:
  - name: mesh
    port: 15008
    protocol: HBONE

---
# Привязка сервиса к waypoint
apiVersion: v1
kind: Service
metadata:
  name: user-service
  labels:
    istio.io/use-waypoint: user-waypoint  # Использовать waypoint
```

### 4.3 Уровень 3: Полный L7 для всех сервисов

**Когда использовать:** Production микросервисы, нужен полный контроль.

```yaml
# Waypoint для всего namespace
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: namespace-waypoint
  namespace: hyper-porto
  labels:
    istio.io/waypoint-for: service
spec:
  gatewayClassName: istio-waypoint
  listeners:
  - name: mesh
    port: 15008
    protocol: HBONE

---
# Namespace использует waypoint
apiVersion: v1
kind: Namespace
metadata:
  name: hyper-porto
  labels:
    istio.io/dataplane-mode: ambient
    istio.io/use-waypoint: namespace-waypoint  # Весь namespace через waypoint
```

### 4.4 Матрица выбора уровня

| Модуль | L4 Only | L7 (Waypoint) | Причина |
|--------|---------|---------------|---------|
| **UserModule** | ✅ | ✅ | JWT validation, fine-grained auth, canary |
| **SearchModule** | ✅ | ❌ | Простой read-only, L4 достаточно |
| **NotificationModule** | ✅ | ❌ | Fire-and-forget, L4 достаточно |
| **AuditModule** | ✅ | ❌ | Internal only, L4 достаточно |
| **PaymentModule** | ✅ | ✅ | Критичный, нужен L7 для compliance |
| **WebhookModule** | ✅ | ❌ | Outbound only, L4 достаточно |
| **SettingsModule** | ✅ | ❌ | Internal config, L4 достаточно |
| **EmailModule** | ✅ | ❌ | Virtual, L4 достаточно |

---

## 5. Практические сценарии применения

### 5.1 Сценарий: Canary Deployment для UserModule

```yaml
# HTTPRoute для canary между версиями user-service
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: user-service-canary
  namespace: hyper-porto
spec:
  parentRefs:
  - kind: Service
    name: user-service
    port: 8000
  rules:
  - matches:
    - headers:
      - name: x-canary
        value: "true"
    backendRefs:
    - name: user-service-v2
      port: 8000
      weight: 100
  - backendRefs:
    - name: user-service-v1
      port: 8000
      weight: 90
    - name: user-service-v2
      port: 8000
      weight: 10
```

**В коде ничего менять не нужно!** Ambient Mesh управляет routing на уровне mesh.

### 5.2 Сценарий: Rate Limiting для API

```yaml
# Rate limiting через EnvoyFilter (на waypoint)
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit-user-api
  namespace: hyper-porto
spec:
  workloadSelector:
    labels:
      gateway.networking.k8s.io/gateway-name: user-waypoint
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: GATEWAY
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.local_ratelimit
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
          stat_prefix: http_local_rate_limiter
          token_bucket:
            max_tokens: 100
            tokens_per_fill: 100
            fill_interval: 1s
          filter_enabled:
            runtime_key: local_rate_limit_enabled
            default_value:
              numerator: 100
              denominator: HUNDRED
```

### 5.3 Сценарий: mTLS между сервисами

```yaml
# PeerAuthentication: требуем mTLS для всего namespace
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: strict-mtls
  namespace: hyper-porto
spec:
  mtls:
    mode: STRICT  # Только mTLS, plaintext запрещён
```

**Результат:** Все соединения между сервисами зашифрованы автоматически.

### 5.4 Сценарий: Authorization Policies

```yaml
# L4 Authorization: разрешить только из определённых namespaces
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-internal-only
  namespace: hyper-porto
spec:
  action: ALLOW
  rules:
  - from:
    - source:
        namespaces:
        - hyper-porto
        - monitoring

---
# L7 Authorization (требует waypoint): разрешить только GET для anonymous
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: user-service-policy
  namespace: hyper-porto
spec:
  targetRefs:
  - kind: Service
    name: user-service
  action: ALLOW
  rules:
  - to:
    - operation:
        methods: ["GET"]
        paths: ["/api/v1/users/*"]
  - from:
    - source:
        principals:
        - cluster.local/ns/hyper-porto/sa/admin-service
    to:
    - operation:
        methods: ["POST", "PUT", "DELETE"]
        paths: ["/api/v1/users/*"]
```

### 5.5 Сценарий: JWT Validation на уровне Mesh

```yaml
# RequestAuthentication: валидация JWT
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: hyper-porto
spec:
  targetRefs:
  - kind: Gateway
    name: user-waypoint
  jwtRules:
  - issuer: "https://auth.hyper-porto.io"
    jwksUri: "https://auth.hyper-porto.io/.well-known/jwks.json"
    forwardOriginalToken: true
    outputPayloadToHeader: x-jwt-payload

---
# AuthorizationPolicy: требовать JWT для protected endpoints
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: require-jwt
  namespace: hyper-porto
spec:
  targetRefs:
  - kind: Service
    name: user-service
  action: DENY
  rules:
  - to:
    - operation:
        paths: ["/api/v1/auth/me", "/api/v1/users/*/settings"]
    when:
    - key: request.auth.principal
      notValues: ["*"]
```

**Важно:** Это дополняет вашу существующую JWT логику в `src/Ship/Auth/`. Mesh даёт дополнительный уровень защиты.

---

## 6. Интеграция с существующей инфраструктурой

### 6.1 Интеграция с Redis

```yaml
# ServiceEntry для внешнего Redis (если вне mesh)
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: redis-external
  namespace: hyper-porto
spec:
  hosts:
  - redis.hyper-porto.svc.cluster.local
  ports:
  - number: 6379
    name: tcp
    protocol: TCP
  resolution: DNS
  location: MESH_INTERNAL

---
# DestinationRule: настройки подключения
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: redis-dr
  namespace: hyper-porto
spec:
  host: redis.hyper-porto.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 5s
    tls:
      mode: ISTIO_MUTUAL  # mTLS к Redis
```

### 6.2 Интеграция с PostgreSQL

```yaml
# ServiceEntry для PostgreSQL
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: postgresql-external
  namespace: hyper-porto
spec:
  hosts:
  - postgresql.data.svc.cluster.local
  ports:
  - number: 5432
    name: tcp
    protocol: TCP
  resolution: DNS
  location: MESH_INTERNAL

---
# DestinationRule с connection pooling
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: postgresql-dr
  namespace: hyper-porto
spec:
  host: postgresql.data.svc.cluster.local
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 50
        connectTimeout: 10s
```

### 6.3 Интеграция с Kafka (для событий)

```yaml
# ServiceEntry для Kafka
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: kafka-external
  namespace: hyper-porto
spec:
  hosts:
  - kafka.data.svc.cluster.local
  ports:
  - number: 9092
    name: tcp
    protocol: TCP
  resolution: DNS
  location: MESH_INTERNAL

---
# DestinationRule для Kafka
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: kafka-dr
  namespace: hyper-porto
spec:
  host: kafka.data.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
```

### 6.4 Интеграция с Logfire (уже есть в проекте)

Ambient Mesh автоматически добавляет trace headers. Ваш существующий Logfire интеграция (`src/Ship/Infrastructure/Telemetry/Logfire.py`) будет получать enriched traces:

```python
# src/Ship/Infrastructure/Telemetry/Logfire.py
# Без изменений! Istio добавляет headers автоматически:
# - x-request-id
# - x-b3-traceid
# - x-b3-spanid
# - traceparent (W3C)

# Logfire уже инструментирует Litestar:
logfire.instrument_litestar(app)  # Уже подхватит mesh headers
```

---

## 7. Безопасность и mTLS

### 7.1 Как работает mTLS в Ambient

```mermaid
sequenceDiagram
    participant App1 as user-service
    participant ztunnel1 as ztunnel (node 1)
    participant istiod as istiod
    participant ztunnel2 as ztunnel (node 2)
    participant App2 as search-service
    
    Note over istiod: Control Plane<br/>CA + Config
    
    rect rgb(200, 230, 201)
        Note over istiod, ztunnel1: Certificate Provisioning
        istiod->>ztunnel1: x509 cert for user-service SA
        istiod->>ztunnel2: x509 cert for search-service SA
    end
    
    rect rgb(227, 242, 253)
        Note over App1, App2: Request Flow with mTLS
        App1->>ztunnel1: Plain TCP (localhost)
        
        Note over ztunnel1: 1. Identify destination<br/>2. Encrypt with dest cert
        
        ztunnel1->>ztunnel2: HBONE + mTLS<br/>spiffe://cluster.local/ns/hyper-porto/sa/user-service
        
        Note over ztunnel2: 1. Verify source identity<br/>2. Check AuthorizationPolicy<br/>3. Decrypt
        
        ztunnel2->>App2: Plain TCP (localhost)
    end
    
    Note over App1, App2: ✅ Apps не знают о mTLS<br/>✅ Zero code changes
```

### 7.2 SPIFFE Identities в Hyper-Porto

| Service | Service Account | SPIFFE Identity |
|---------|----------------|-----------------|
| user-service | `user-sa` | `spiffe://cluster.local/ns/hyper-porto/sa/user-sa` |
| search-service | `search-sa` | `spiffe://cluster.local/ns/hyper-porto/sa/search-sa` |
| payment-service | `payment-sa` | `spiffe://cluster.local/ns/vendor/sa/payment-sa` |
| worker | `worker-sa` | `spiffe://cluster.local/ns/hyper-porto/sa/worker-sa` |

### 7.3 Authorization Policy Best Practices

```yaml
# 1. Default Deny для namespace
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: default-deny
  namespace: hyper-porto
spec:
  {}  # Empty = deny all

---
# 2. Allow specific paths
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-user-service-read
  namespace: hyper-porto
spec:
  selector:
    matchLabels:
      app: user-service
  action: ALLOW
  rules:
  - to:
    - operation:
        methods: ["GET"]
        paths: ["/api/v1/users/*", "/health/*"]

---
# 3. Allow inter-service communication
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-search-from-user
  namespace: hyper-porto
spec:
  selector:
    matchLabels:
      app: search-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - cluster.local/ns/hyper-porto/sa/user-sa
```

---

## 8. Observability и телеметрия

### 8.1 Метрики (автоматически)

Ambient Mesh автоматически собирает метрики:

**L4 метрики (ztunnel):**
- `istio_tcp_sent_bytes_total`
- `istio_tcp_received_bytes_total`
- `istio_tcp_connections_opened_total`
- `istio_tcp_connections_closed_total`

**L7 метрики (waypoint):**
- `istio_requests_total`
- `istio_request_duration_milliseconds`
- `istio_request_bytes_total`
- `istio_response_bytes_total`

### 8.2 Prometheus интеграция

```yaml
# PodMonitor для ztunnel
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: ztunnel
  namespace: istio-system
spec:
  selector:
    matchLabels:
      app: ztunnel
  podMetricsEndpoints:
  - port: http-monitoring
    path: /metrics
```

### 8.3 Grafana Dashboards

Istio предоставляет готовые dashboards:
- **Mesh Dashboard** — общий обзор
- **Service Dashboard** — per-service метрики
- **Workload Dashboard** — per-pod метрики

### 8.4 Kiali (Service Mesh Visualization)

```yaml
# Установка Kiali
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.28/samples/addons/kiali.yaml

# Доступ
istioctl dashboard kiali
```

### 8.5 Интеграция с Logfire

Ваш существующий Logfire setup продолжает работать. Дополнительно можно:

```python
# src/Ship/Infrastructure/Telemetry/Logfire.py

def setup_logfire(app: Litestar) -> None:
    """Setup Logfire with Istio trace context propagation."""
    import logfire
    
    logfire.configure(
        service_name=settings.app_name,
        service_version=settings.app_version,
        # Istio добавляет W3C traceparent header автоматически
        # Logfire подхватит его
    )
    
    logfire.instrument_litestar(app)
    logfire.instrument_asyncpg()  # Если PostgreSQL
    logfire.instrument_redis()    # Если Redis
```

---

## 9. Traffic Management

### 9.1 Retry Policy

```yaml
# VirtualService с retry (требует waypoint)
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: user-service-retry
  namespace: hyper-porto
spec:
  hosts:
  - user-service
  http:
  - route:
    - destination:
        host: user-service
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset,connect-failure
```

### 9.2 Timeout Policy

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: search-service-timeout
  namespace: hyper-porto
spec:
  hosts:
  - search-service
  http:
  - route:
    - destination:
        host: search-service
    timeout: 10s  # Таймаут для поисковых запросов
```

### 9.3 Circuit Breaker

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: payment-service-circuit-breaker
  namespace: vendor
spec:
  host: payment-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 60s
      maxEjectionPercent: 50
```

### 9.4 Fault Injection (для тестирования)

```yaml
# Inject delay для тестирования resilience
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: search-service-fault
  namespace: hyper-porto
spec:
  hosts:
  - search-service
  http:
  - fault:
      delay:
        percentage:
          value: 10
        fixedDelay: 2s
    route:
    - destination:
        host: search-service
```

---

## 10. Пошаговое внедрение

### 10.1 Фаза 1: Установка Istio с Ambient

```bash
# 1. Установка istioctl
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# 2. Установка Istio с ambient profile
istioctl install --set profile=ambient --skip-confirmation

# 3. Проверка
kubectl get pods -n istio-system
# Должны быть: istiod, ztunnel (DaemonSet), istio-cni

# 4. Установка Gateway API CRDs
kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
  kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/experimental-install.yaml
```

### 10.2 Фаза 2: Включение Ambient для namespace

```bash
# 1. Включить ambient mode для namespace
kubectl label namespace hyper-porto istio.io/dataplane-mode=ambient

# 2. Проверить, что pods "в mesh"
istioctl ztunnel-config workloads

# 3. Проверить mTLS
kubectl exec deploy/user-service -- curl -s http://search-service:8000/health
# Трафик теперь идёт через ztunnel с mTLS
```

### 10.3 Фаза 3: Добавление Waypoint для L7

```bash
# 1. Создать waypoint для user-service
istioctl waypoint apply --name user-waypoint --namespace hyper-porto

# 2. Привязать к сервису
kubectl label service user-service istio.io/use-waypoint=user-waypoint

# 3. Проверить
istioctl proxy-status
kubectl get gateway user-waypoint -n hyper-porto
```

### 10.4 Фаза 4: Настройка Policies

```bash
# 1. Применить PeerAuthentication
kubectl apply -f manifests/peer-authentication.yaml

# 2. Применить AuthorizationPolicies
kubectl apply -f manifests/authorization-policies.yaml

# 3. Проверить
istioctl analyze -n hyper-porto
```

### 10.5 Фаза 5: Observability

```bash
# 1. Установить Prometheus, Grafana, Kiali
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.28/samples/addons/prometheus.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.28/samples/addons/grafana.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.28/samples/addons/kiali.yaml

# 2. Доступ
istioctl dashboard kiali
istioctl dashboard grafana
```

---

## 11. Изменения в коде

### 11.1 Хорошая новость: Минимальные изменения!

Ambient Mesh работает на уровне сети. **Ваш код Hyper-Porto остаётся без изменений** для базового функционала.

### 11.2 Рекомендуемые улучшения

#### 11.2.1 Health Checks (уже есть!)

```python
# src/Ship/Infrastructure/HealthCheck.py
# Уже реализовано! Istio использует эти endpoints

@get("/health")
async def liveness() -> dict:
    return {"status": "ok"}

@get("/health/ready")
async def readiness() -> dict:
    # Проверка Redis, DB
    return {"status": "ready"}
```

#### 11.2.2 Graceful Shutdown

```python
# src/App.py — добавить обработку SIGTERM

import signal
import asyncio

@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan with graceful shutdown."""
    
    shutdown_event = asyncio.Event()
    
    def handle_sigterm(*args):
        shutdown_event.set()
    
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    yield
    
    # Graceful shutdown: дождаться завершения активных запросов
    # Istio drains connections gracefully
    await asyncio.sleep(5)  # Drain period
    
    if hasattr(app.state, "dishka_container"):
        await app.state.dishka_container.close()
```

#### 11.2.3 Propagation Trace Headers

```python
# src/Ship/Decorators/trace_propagation.py (опционально)
"""Propagate Istio trace headers to outbound requests."""

from functools import wraps
from contextvars import ContextVar
from typing import Callable

# Istio trace headers
TRACE_HEADERS = [
    "x-request-id",
    "x-b3-traceid",
    "x-b3-spanid",
    "x-b3-sampled",
    "x-b3-flags",
    "traceparent",
    "tracestate",
]

# Context var для хранения headers
_trace_context: ContextVar[dict] = ContextVar("trace_context", default={})


def capture_trace_headers(request) -> dict:
    """Extract trace headers from incoming request."""
    headers = {}
    for header in TRACE_HEADERS:
        value = request.headers.get(header)
        if value:
            headers[header] = value
    return headers


def get_trace_headers() -> dict:
    """Get current trace headers."""
    return _trace_context.get()


# Middleware для capture
class TraceContextMiddleware:
    async def __call__(self, request, call_next):
        headers = capture_trace_headers(request)
        token = _trace_context.set(headers)
        try:
            response = await call_next(request)
            return response
        finally:
            _trace_context.reset(token)


# Использование в Tasks для outbound requests
# src/Containers/VendorSection/WebhookModule/Tasks/DeliverWebhookTask.py
import httpx
from src.Ship.Decorators.trace_propagation import get_trace_headers

class DeliverWebhookTask:
    async def run(self, webhook_url: str, payload: dict) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=get_trace_headers(),  # Propagate trace!
            )
            return response.is_success
```

#### 11.2.4 Service Account в Kubernetes

```yaml
# manifests/service-accounts.yaml
# Для каждого модуля/сервиса свой ServiceAccount

apiVersion: v1
kind: ServiceAccount
metadata:
  name: user-service-sa
  namespace: hyper-porto

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: search-service-sa
  namespace: hyper-porto

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: payment-service-sa
  namespace: vendor
```

### 11.3 Что НЕ нужно менять

| Компонент | Изменения |
|-----------|-----------|
| Actions | ❌ Не нужно |
| Tasks | ❌ Не нужно |
| Queries | ❌ Не нужно |
| Repositories | ❌ Не нужно |
| UnitOfWork | ❌ Не нужно |
| Controllers | ❌ Не нужно |
| Events/Listeners | ❌ Не нужно |
| JWT Auth | ❌ Продолжает работать (+ mesh level) |
| Logfire | ❌ Продолжает работать (+ enriched traces) |

---

## 12. Kubernetes манифесты

### 12.1 Структура манифестов

```
manifests/
├── base/
│   ├── namespace.yaml
│   ├── service-accounts.yaml
│   └── network-policies.yaml
│
├── istio/
│   ├── peer-authentication.yaml
│   ├── authorization-policies/
│   │   ├── default-deny.yaml
│   │   ├── user-service.yaml
│   │   ├── search-service.yaml
│   │   └── payment-service.yaml
│   ├── waypoints/
│   │   ├── user-waypoint.yaml
│   │   └── payment-waypoint.yaml
│   └── traffic-management/
│       ├── canary-user-service.yaml
│       ├── retry-policies.yaml
│       └── circuit-breakers.yaml
│
├── apps/
│   ├── user-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── hpa.yaml
│   ├── search-service/
│   │   └── ...
│   └── ...
│
└── observability/
    ├── prometheus-config.yaml
    └── grafana-dashboards.yaml
```

### 12.2 Пример: Deployment с Ambient

```yaml
# manifests/apps/user-service/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: hyper-porto
  labels:
    app: user-service
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
        version: v1
      # НЕТ sidecar annotation!
      # Ambient работает автоматически через namespace label
    spec:
      serviceAccountName: user-service-sa
      containers:
      - name: user-service
        image: ghcr.io/your-org/user-service:v1.0.0
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: APP_NAME
          value: user-service
        - name: DB_URL
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: db-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: user-service-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        # Graceful shutdown
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 5"]
      terminationGracePeriodSeconds: 30
```

### 12.3 Пример: AuthorizationPolicy

```yaml
# manifests/istio/authorization-policies/user-service.yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: user-service-policy
  namespace: hyper-porto
spec:
  selector:
    matchLabels:
      app: user-service
  action: ALLOW
  rules:
  # Public endpoints (health, docs)
  - to:
    - operation:
        paths: ["/health", "/health/*", "/api/docs"]
        methods: ["GET"]
  
  # Public read for users list/get
  - to:
    - operation:
        paths: ["/api/v1/users", "/api/v1/users/*"]
        methods: ["GET"]
  
  # Auth endpoints
  - to:
    - operation:
        paths: ["/api/v1/auth/login", "/api/v1/auth/refresh"]
        methods: ["POST"]
  
  # Protected endpoints - require valid JWT principal
  - from:
    - source:
        requestPrincipals: ["*"]  # Any authenticated user
    to:
    - operation:
        paths: ["/api/v1/auth/me", "/api/v1/auth/change-password"]
        methods: ["GET", "POST"]
  
  # Admin endpoints - only from specific service accounts
  - from:
    - source:
        principals:
        - cluster.local/ns/hyper-porto/sa/admin-service-sa
    to:
    - operation:
        paths: ["/api/v1/users/*"]
        methods: ["POST", "PUT", "DELETE"]
  
  # Inter-service: allow search-service to read users
  - from:
    - source:
        principals:
        - cluster.local/ns/hyper-porto/sa/search-service-sa
    to:
    - operation:
        paths: ["/api/v1/users", "/api/v1/users/*"]
        methods: ["GET"]
```

### 12.4 Пример: Waypoint для namespace

```yaml
# manifests/istio/waypoints/namespace-waypoint.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: hyper-porto-waypoint
  namespace: hyper-porto
  labels:
    istio.io/waypoint-for: service
spec:
  gatewayClassName: istio-waypoint
  listeners:
  - name: mesh
    port: 15008
    protocol: HBONE

---
# Namespace использует waypoint
apiVersion: v1
kind: Namespace
metadata:
  name: hyper-porto
  labels:
    istio.io/dataplane-mode: ambient
    istio.io/use-waypoint: hyper-porto-waypoint
```

---

## 13. Чеклисты и лучшие практики

### 13.1 Чеклист: Подготовка к Ambient Mesh

```markdown
## Подготовка к Ambient Mesh

### Инфраструктура
- [ ] Kubernetes 1.30+ установлен
- [ ] Istio 1.28+ с ambient profile установлен
- [ ] Gateway API CRDs установлены
- [ ] Prometheus/Grafana для observability

### Приложение
- [ ] Health endpoints реализованы (/health, /health/ready)
- [ ] Graceful shutdown настроен (SIGTERM handling)
- [ ] Service Accounts созданы для каждого сервиса
- [ ] Resources (requests/limits) настроены

### Network
- [ ] Namespace labeled: istio.io/dataplane-mode=ambient
- [ ] Services имеют корректные ports/names
- [ ] NetworkPolicy не блокирует ports 15001, 15006, 15008

### Security
- [ ] PeerAuthentication: STRICT mTLS
- [ ] AuthorizationPolicy: default deny
- [ ] Per-service policies созданы
```

### 13.2 Чеклист: Production Readiness

```markdown
## Production Readiness с Ambient Mesh

### Performance
- [ ] Waypoint proxy replicas настроены (HPA)
- [ ] Connection pool limits настроены
- [ ] Timeouts настроены
- [ ] Circuit breakers настроены

### Security
- [ ] mTLS STRICT для всех namespaces
- [ ] Default deny policies
- [ ] JWT validation для public endpoints
- [ ] Secrets в Kubernetes Secrets или Vault

### Observability
- [ ] Prometheus scraping настроен
- [ ] Grafana dashboards импортированы
- [ ] Kiali доступен
- [ ] Alerts настроены

### Operations
- [ ] Backup/restore для Istio config
- [ ] Runbook для troubleshooting
- [ ] Canary deployment процесс задокументирован
```

### 13.3 Лучшие практики

| Категория | Best Practice |
|-----------|---------------|
| **Namespaces** | Один namespace = одна "зона доверия" |
| **Waypoints** | Используй только когда нужен L7 |
| **mTLS** | STRICT mode в production |
| **Policies** | Start with deny-all, allow specific |
| **Observability** | Настрой alerts на 5xx и latency |
| **Canary** | Всегда используй для production releases |
| **Health** | Readiness probe = можно принимать трафик |
| **Shutdown** | PreStop hook + terminationGracePeriod |

---

## 14. Troubleshooting

### 14.1 Проверка статуса ztunnel

```bash
# Проверить workloads в mesh
istioctl ztunnel-config workloads

# Пример вывода:
# NAMESPACE    POD NAME                    IP         NODE    WAYPOINT  PROTOCOL
# hyper-porto  user-service-xxx            10.0.0.5   node1   None      HBONE
# hyper-porto  search-service-xxx          10.0.0.6   node1   None      HBONE
```

### 14.2 Проверка mTLS

```bash
# Проверить mTLS между сервисами
istioctl proxy-status

# Проверить сертификаты
istioctl ztunnel-config certificates <ZTUNNEL_POD> -n istio-system
```

### 14.3 Проверка политик

```bash
# Analyze namespace
istioctl analyze -n hyper-porto

# Проверить AuthorizationPolicy
kubectl get authorizationpolicy -n hyper-porto

# Debug policy evaluation
kubectl logs -n istio-system -l app=istiod | grep -i authz
```

### 14.4 Проверка waypoint

```bash
# Проверить waypoint proxy
istioctl proxy-status

# Logs waypoint
kubectl logs -n hyper-porto -l gateway.networking.k8s.io/gateway-name=user-waypoint

# Config dump
istioctl proxy-config all deploy/user-waypoint -n hyper-porto
```

### 14.5 Проверка traffic flow

```bash
# Проверить, что трафик идёт через mesh
kubectl exec deploy/user-service -n hyper-porto -- \
  curl -v http://search-service:8000/health

# В логах ztunnel будет:
# INFO access connection complete src.addr=10.0.0.5:xxxxx ... direction="outbound"
```

### 14.6 Типичные проблемы

| Проблема | Причина | Решение |
|----------|---------|---------|
| Connection refused | NetworkPolicy блокирует | Добавить allow для ports 15008 |
| 403 RBAC denied | AuthorizationPolicy | Проверить principals/paths |
| mTLS handshake failed | Сертификаты | istioctl ztunnel-config certificates |
| Slow startup | Ожидание ztunnel | Проверить readiness ztunnel |
| Missing traces | Headers не propagate | Добавить trace propagation |

---

## 15. Service Discovery: Как сервисы находят друг друга

### 15.1 Проблема: Хардкод — это плохо

```python
# ❌ ПЛОХО: хардкод адресов
NOTIFICATION_SERVICE_URL = "http://192.168.1.100:8001"
AUDIT_SERVICE_URL = "http://audit-server.company.com:8002"
```

**Почему плохо:**
- IP адреса меняются
- Разные адреса в dev/staging/prod
- Нет load balancing
- Нет failover
- Сложно масштабировать

### 15.2 Решение: Kubernetes DNS + Istio

В Kubernetes каждый Service автоматически получает DNS имя:

```
<service-name>.<namespace>.svc.cluster.local
```

**Примеры для вашего проекта:**

| Сервис | Полное DNS имя | Короткое (внутри namespace) |
|--------|----------------|------------------------------|
| user-service | `user-service.hyper-porto.svc.cluster.local` | `user-service` |
| notification-service | `notification-service.hyper-porto.svc.cluster.local` | `notification-service` |
| audit-service | `audit-service.support.svc.cluster.local` | `audit-service.support` |
| payment-service | `payment-service.vendor.svc.cluster.local` | `payment-service.vendor` |

### 15.3 Архитектура Service Discovery

```mermaid
flowchart TB
    subgraph K8s["☸️ Kubernetes Cluster"]
        subgraph DNS["🌐 CoreDNS"]
            CoreDNS["CoreDNS<br/>Cluster DNS"]
        end
        
        subgraph Istio["🌊 Istio Control Plane"]
            istiod["istiod<br/>Service Registry"]
        end
        
        subgraph NS1["📁 hyper-porto namespace"]
            UserSvc["user-service<br/>ClusterIP: 10.96.0.10"]
            SearchSvc["search-service<br/>ClusterIP: 10.96.0.11"]
        end
        
        subgraph NS2["📁 support namespace"]
            AuditSvc["audit-service<br/>ClusterIP: 10.96.0.20"]
            NotifSvc["notification-service<br/>ClusterIP: 10.96.0.21"]
        end
        
        subgraph Pods["📦 Application Pods"]
            App1["user-service pod"]
            App2["search-service pod"]
        end
    end
    
    App1 -->|"1. DNS query:<br/>audit-service.support"| CoreDNS
    CoreDNS -->|"2. Return IP:<br/>10.96.0.20"| App1
    App1 -->|"3. Connect to<br/>10.96.0.20:8000"| AuditSvc
    
    istiod -->|"xDS: service<br/>endpoints"| App1
    istiod -->|"xDS: service<br/>endpoints"| App2
    
    style DNS fill:#e3f2fd
    style Istio fill:#c8e6c9
```

### 15.4 Конфигурация через Environment Variables

Вместо хардкода используем **Settings** (Pydantic) + **Environment Variables**:

```python
# src/Ship/Configs/Settings.py

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with service discovery."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # === Идентификация сервиса ===
    service_name: str = Field(default="hyper-porto")
    service_version: str = Field(default="1.0.0")
    
    # === Основные настройки ===
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_debug: bool = Field(default=False)
    
    # === База данных ===
    db_url: str = Field(default="postgresql://localhost/app")
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # === Service Discovery ===
    # В Kubernetes используем DNS имена сервисов
    # В локальной разработке — localhost с портами
    
    # Notification Service
    notification_service_url: str = Field(
        default="http://notification-service:8000",
        description="URL NotificationService (K8s DNS или localhost)"
    )
    
    # Audit Service  
    audit_service_url: str = Field(
        default="http://audit-service.support:8000",
        description="URL AuditService (другой namespace)"
    )
    
    # Search Service
    search_service_url: str = Field(
        default="http://search-service:8000",
        description="URL SearchService"
    )
    
    # Payment Service (VendorSection)
    payment_service_url: str = Field(
        default="http://payment-service.vendor:8000",
        description="URL PaymentService (vendor namespace)"
    )
    
    # Email Service (VendorSection)
    email_service_url: str = Field(
        default="http://email-service.vendor:8000",
        description="URL EmailService"
    )
    
    # Webhook Service
    webhook_service_url: str = Field(
        default="http://webhook-service.vendor:8000",
        description="URL WebhookService"
    )
    
    # === Event Broker ===
    # Redis Streams для событий между сервисами
    event_broker_url: str = Field(
        default="redis://redis:6379/0",
        description="URL брокера событий"
    )
    
    # Kafka (если используется)
    kafka_bootstrap_servers: str = Field(
        default="kafka:9092",
        description="Kafka bootstrap servers"
    )
```

### 15.5 Разные конфигурации для разных окружений

```yaml
# === LOCAL DEVELOPMENT (.env.local) ===
# Все сервисы на localhost с разными портами

SERVICE_NAME=hyper-porto-dev
APP_DEBUG=true

# Локальные адреса
NOTIFICATION_SERVICE_URL=http://localhost:8001
AUDIT_SERVICE_URL=http://localhost:8002
SEARCH_SERVICE_URL=http://localhost:8003
PAYMENT_SERVICE_URL=http://localhost:8004

# Локальные базы
DB_URL=postgresql://localhost:5432/app_dev
REDIS_URL=redis://localhost:6379/0
```

```yaml
# === KUBERNETES STAGING (ConfigMap) ===
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
  namespace: hyper-porto
data:
  SERVICE_NAME: "user-service"
  APP_DEBUG: "false"
  
  # Kubernetes DNS (внутри того же namespace)
  SEARCH_SERVICE_URL: "http://search-service:8000"
  
  # Kubernetes DNS (другой namespace)
  NOTIFICATION_SERVICE_URL: "http://notification-service.support:8000"
  AUDIT_SERVICE_URL: "http://audit-service.support:8000"
  PAYMENT_SERVICE_URL: "http://payment-service.vendor:8000"
  
  # Shared services
  REDIS_URL: "redis://redis.data:6379/0"
  EVENT_BROKER_URL: "redis://redis.data:6379/1"
```

```yaml
# === KUBERNETES PRODUCTION (ConfigMap + Secrets) ===
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
  namespace: hyper-porto-prod
data:
  SERVICE_NAME: "user-service"
  APP_DEBUG: "false"
  
  # Production DNS
  NOTIFICATION_SERVICE_URL: "http://notification-service.support-prod:8000"
  AUDIT_SERVICE_URL: "http://audit-service.support-prod:8000"
  PAYMENT_SERVICE_URL: "http://payment-service.vendor-prod:8000"
  
  # Production Redis cluster
  REDIS_URL: "redis://redis-cluster.data-prod:6379/0"
  
  # Production Kafka
  KAFKA_BOOTSTRAP_SERVERS: "kafka-1.data-prod:9092,kafka-2.data-prod:9092"
```

### 15.6 Gateway Pattern с Service Discovery

Используйте паттерн **Module Gateway** из `docs/15-module-gateway-pattern.md`:

```python
# src/Containers/AppSection/UserModule/Gateways/NotificationGateway.py
"""Gateway для взаимодействия с NotificationService."""

from typing import Protocol
from dataclasses import dataclass
from returns.result import Result, Success, Failure
import httpx

from src.Ship.Configs import get_settings


# === Port (Interface) ===
class NotificationGateway(Protocol):
    """Порт для отправки уведомлений."""
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
    ) -> Result[str, Exception]:
        """Отправить уведомление пользователю."""
        ...


# === Adapter: Local (для монолита) ===
@dataclass
class LocalNotificationAdapter:
    """Локальный адаптер — прямой вызов Action."""
    
    action: "CreateNotificationAction"  # DI injection
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
    ) -> Result[str, Exception]:
        from src.Containers.AppSection.NotificationModule.Data.Schemas.Requests import (
            CreateNotificationRequest
        )
        
        result = await self.action.run(CreateNotificationRequest(
            user_id=user_id,
            title=title,
            message=message,
        ))
        
        return result.map(lambda n: str(n.id))


# === Adapter: HTTP (для микросервиса) ===
@dataclass
class HttpNotificationAdapter:
    """HTTP адаптер — вызов внешнего сервиса."""
    
    # URL берём из Settings (Service Discovery!)
    base_url: str | None = None
    timeout: float = 5.0
    
    def __post_init__(self):
        if self.base_url is None:
            settings = get_settings()
            self.base_url = settings.notification_service_url
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
    ) -> Result[str, Exception]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/notifications",
                    json={
                        "user_id": user_id,
                        "title": title,
                        "message": message,
                    },
                    # Propagate trace headers для distributed tracing
                    headers=self._get_trace_headers(),
                )
                response.raise_for_status()
                data = response.json()
                return Success(data["id"])
        except Exception as e:
            return Failure(e)
    
    def _get_trace_headers(self) -> dict:
        """Получить trace headers для propagation."""
        from src.Ship.Decorators.trace_propagation import get_trace_headers
        return get_trace_headers()


# === Adapter: Event-based (fire-and-forget) ===
@dataclass  
class EventNotificationAdapter:
    """Event адаптер — отправка через Event Bus."""
    
    event_bus: "EventBus"  # DI injection
    
    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
    ) -> Result[str, Exception]:
        import uuid
        
        notification_id = str(uuid.uuid4())
        
        await self.event_bus.publish(
            "NotificationRequested",
            {
                "notification_id": notification_id,
                "user_id": user_id,
                "title": title,
                "message": message,
            }
        )
        
        return Success(notification_id)
```

### 15.7 DI-регистрация адаптеров

```python
# src/Containers/AppSection/UserModule/Providers.py

from dishka import Provider, Scope, provide
from src.Ship.Configs import get_settings
from src.Containers.AppSection.UserModule.Gateways.NotificationGateway import (
    NotificationGateway,
    LocalNotificationAdapter,
    HttpNotificationAdapter,
    EventNotificationAdapter,
)


class UserModuleProvider(Provider):
    """Провайдеры UserModule."""
    
    scope = Scope.REQUEST
    
    @provide
    def notification_gateway(self) -> NotificationGateway:
        """Выбор адаптера на основе конфигурации."""
        settings = get_settings()
        
        # Стратегия выбора адаптера:
        # 1. Если URL указан — используем HTTP
        # 2. Если production и есть event bus — используем Events
        # 3. Иначе — локальный вызов (монолит)
        
        if settings.notification_service_url.startswith("http"):
            # Микросервисный режим — HTTP
            return HttpNotificationAdapter(
                base_url=settings.notification_service_url
            )
        elif settings.app_env == "production":
            # Production с event bus
            from src.Ship.Infrastructure.EventBus import get_event_bus
            return EventNotificationAdapter(
                event_bus=get_event_bus()
            )
        else:
            # Локальный режим (монолит)
            # Нужен прямой import — DI разрешит зависимости
            from src.Containers.AppSection.NotificationModule.Actions.CreateNotificationAction import (
                CreateNotificationAction
            )
            # Это упрощённый пример — в реальности DI сам резолвит
            return LocalNotificationAdapter(action=...)
```

### 15.8 Использование в Action

```python
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py

from dataclasses import dataclass
from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.UserModule.Gateways.NotificationGateway import (
    NotificationGateway
)


@dataclass
class CreateUserAction(Action[CreateUserRequest, AppUser, UserError]):
    """Создание пользователя с отправкой уведомления."""
    
    hash_password: HashPasswordTask
    uow: UserUnitOfWork
    notification_gateway: NotificationGateway  # DI инъекция!
    
    async def run(self, data: CreateUserRequest) -> Result[AppUser, UserError]:
        # ... создание пользователя ...
        
        async with self.uow:
            user = AppUser(
                email=data.email,
                password_hash=password_hash,
                name=data.name,
            )
            await self.uow.users.add(user)
            self.uow.add_event(UserCreated(user_id=user.id, email=user.email))
            await self.uow.commit()
        
        # Отправка уведомления через Gateway
        # Gateway сам знает — вызвать локально или по HTTP
        await self.notification_gateway.send_notification(
            user_id=str(user.id),
            title="Добро пожаловать!",
            message=f"Привет, {user.name}! Ваш аккаунт создан.",
        )
        
        return Success(user)
```

### 15.9 Istio + Service Discovery = Magic

С Istio Ambient Mesh вы получаете **дополнительные преимущества**:

```mermaid
sequenceDiagram
    participant UserSvc as user-service
    participant ztunnel as ztunnel
    participant CoreDNS as CoreDNS
    participant Istiod as istiod
    participant NotifSvc as notification-service
    
    Note over UserSvc: httpx.post("http://notification-service:8000/...")
    
    UserSvc->>CoreDNS: DNS: notification-service?
    CoreDNS-->>UserSvc: 10.96.0.21 (ClusterIP)
    
    UserSvc->>ztunnel: Connect to 10.96.0.21:8000
    
    Note over ztunnel: Istio magic:<br/>1. mTLS encryption<br/>2. Load balancing<br/>3. Retry on failure<br/>4. Circuit breaker<br/>5. Telemetry
    
    ztunnel->>Istiod: Get endpoints for notification-service
    Istiod-->>ztunnel: [pod1:8000, pod2:8000, pod3:8000]
    
    ztunnel->>NotifSvc: HBONE (mTLS) → pod2:8000
    NotifSvc-->>ztunnel: Response
    ztunnel-->>UserSvc: Response
    
    Note over UserSvc, NotifSvc: ✅ mTLS автоматически<br/>✅ Load balancing<br/>✅ Retries при 5xx<br/>✅ Метрики собраны
```

**Что Istio даёт поверх Kubernetes DNS:**

| Функция | Только K8s DNS | + Istio Ambient |
|---------|----------------|-----------------|
| Service Discovery | ✅ | ✅ |
| Load Balancing | Round-robin | Умный (latency-based) |
| mTLS | ❌ Ручная настройка | ✅ Автоматически |
| Retries | ❌ В коде | ✅ На уровне mesh |
| Circuit Breaker | ❌ В коде (tenacity) | ✅ На уровне mesh |
| Timeout | ❌ В коде | ✅ На уровне mesh |
| Tracing | ❌ Ручной | ✅ Автоматический |
| Metrics | ❌ Ручные | ✅ Автоматические |

### 15.10 Полная схема Service Discovery

```mermaid
flowchart TB
    subgraph Dev["🖥️ Local Development"]
        DevApp["user-service<br/>localhost:8000"]
        DevNotif["notification-service<br/>localhost:8001"]
        DevAudit["audit-service<br/>localhost:8002"]
        
        DevApp -->|".env.local:<br/>NOTIFICATION_SERVICE_URL=<br/>http://localhost:8001"| DevNotif
        DevApp -->|".env.local:<br/>AUDIT_SERVICE_URL=<br/>http://localhost:8002"| DevAudit
    end
    
    subgraph K8s["☸️ Kubernetes + Istio Ambient"]
        subgraph NS1["hyper-porto namespace"]
            K8sUser["user-service<br/>ClusterIP"]
            K8sSearch["search-service<br/>ClusterIP"]
        end
        
        subgraph NS2["support namespace"]
            K8sNotif["notification-service<br/>ClusterIP"]
            K8sAudit["audit-service<br/>ClusterIP"]
        end
        
        subgraph NS3["vendor namespace"]
            K8sPayment["payment-service<br/>ClusterIP"]
        end
        
        DNS["CoreDNS"]
        ztunnel["ztunnel<br/>(mTLS + LB)"]
        
        K8sUser -->|"ConfigMap:<br/>notification-service.support"| DNS
        DNS --> ztunnel
        ztunnel -->|"HBONE mTLS"| K8sNotif
        
        K8sUser -->|"ConfigMap:<br/>audit-service.support"| DNS
        ztunnel -->|"HBONE mTLS"| K8sAudit
        
        K8sUser -->|"ConfigMap:<br/>payment-service.vendor"| DNS
        ztunnel -->|"HBONE mTLS"| K8sPayment
    end
    
    style Dev fill:#fff3e0
    style K8s fill:#e1f5fe
    style ztunnel fill:#c8e6c9
```

### 15.11 Best Practices для Service Discovery

| Практика | Описание |
|----------|----------|
| **Используй DNS имена** | `http://service-name` вместо IP адресов |
| **Храни URLs в Settings** | Pydantic Settings + Environment Variables |
| **Используй ConfigMaps** | Для K8s — настройки в ConfigMaps |
| **Разделяй по namespace** | `service.namespace` для cross-namespace |
| **Gateway Pattern** | Абстракция поверх HTTP/Events/Local |
| **Health Checks** | Каждый сервис должен иметь `/health` |
| **Timeouts везде** | `httpx.AsyncClient(timeout=5.0)` |
| **Retries с backoff** | Tenacity или Istio DestinationRule |

---

## 16. Мультикластер с Istio Ambient Mesh

### 16.1 Зачем нужен мультикластер?

| Причина | Описание |
|---------|----------|
| **Geo-распределение** | Сервисы ближе к пользователям (EU, US, Asia) |
| **Изоляция failure** | Падение одного кластера не убивает всё |
| **Compliance** | Данные EU в EU кластере (GDPR) |
| **Масштабирование** | Разные команды — разные кластеры |
| **Hybrid Cloud** | Часть в AWS, часть в GCP, часть on-premise |

### 16.2 Топологии мультикластера

```mermaid
flowchart TB
    subgraph Topology1["🔷 Primary-Remote"]
        direction TB
        P1["Primary Cluster<br/>istiod + workloads"]
        R1["Remote Cluster<br/>только workloads"]
        P1 <-->|"Control Plane"| R1
    end
    
    subgraph Topology2["🔷 Multi-Primary"]
        direction TB
        P2A["Primary Cluster A<br/>istiod + workloads"]
        P2B["Primary Cluster B<br/>istiod + workloads"]
        P2A <-->|"Синхронизация"| P2B
    end
    
    subgraph Topology3["🔷 Multi-Primary + Remote"]
        direction TB
        P3A["Primary A<br/>istiod"]
        P3B["Primary B<br/>istiod"]
        R3["Remote<br/>workloads"]
        P3A <--> P3B
        P3A --> R3
        P3B --> R3
    end
```

### 16.3 Архитектура Multi-Cluster Ambient Mesh

```mermaid
flowchart TB
    subgraph Internet["🌐 Internet"]
        Users["Users"]
    end
    
    subgraph Cluster1["☸️ Cluster EU (Frankfurt)"]
        subgraph CP1["Control Plane"]
            istiod1["istiod"]
        end
        
        subgraph DP1["Data Plane"]
            ztunnel1["ztunnel"]
            EWG1["East-West<br/>Gateway"]
        end
        
        subgraph Apps1["Applications"]
            User1["user-service"]
            Search1["search-service"]
        end
        
        IG1["Ingress<br/>Gateway"]
    end
    
    subgraph Cluster2["☸️ Cluster US (Virginia)"]
        subgraph CP2["Control Plane"]
            istiod2["istiod"]
        end
        
        subgraph DP2["Data Plane"]
            ztunnel2["ztunnel"]
            EWG2["East-West<br/>Gateway"]
        end
        
        subgraph Apps2["Applications"]
            User2["user-service"]
            Notif2["notification-service"]
            Audit2["audit-service"]
        end
        
        IG2["Ingress<br/>Gateway"]
    end
    
    subgraph Cluster3["☸️ Cluster Asia (Tokyo)"]
        subgraph CP3["Control Plane"]
            istiod3["istiod"]
        end
        
        subgraph DP3["Data Plane"]
            ztunnel3["ztunnel"]
            EWG3["East-West<br/>Gateway"]
        end
        
        subgraph Apps3["Applications"]
            User3["user-service"]
            Payment3["payment-service"]
        end
        
        IG3["Ingress<br/>Gateway"]
    end
    
    Users --> IG1 & IG2 & IG3
    
    EWG1 <-->|"mTLS HBONE<br/>Cross-cluster"| EWG2
    EWG2 <-->|"mTLS HBONE<br/>Cross-cluster"| EWG3
    EWG1 <-->|"mTLS HBONE<br/>Cross-cluster"| EWG3
    
    istiod1 <-->|"Service Registry<br/>Sync"| istiod2
    istiod2 <-->|"Service Registry<br/>Sync"| istiod3
    istiod1 <-->|"Service Registry<br/>Sync"| istiod3
    
    style Cluster1 fill:#e3f2fd
    style Cluster2 fill:#fff3e0
    style Cluster3 fill:#f3e5f5
    style EWG1 fill:#c8e6c9
    style EWG2 fill:#c8e6c9
    style EWG3 fill:#c8e6c9
```

### 16.4 Ключевые компоненты мультикластера

| Компонент | Роль | Описание |
|-----------|------|----------|
| **istiod** | Control Plane | Синхронизирует service registry между кластерами |
| **East-West Gateway** | Cross-cluster traffic | Envoy Gateway для трафика между кластерами |
| **ztunnel** | L4 proxy | mTLS + маршрутизация (в т.ч. cross-cluster) |
| **Shared Root CA** | Trust | Общий корневой сертификат для mTLS между кластерами |
| **DNS** | Discovery | Резолвит сервисы из других кластеров |

### 16.5 Service Discovery в мультикластере

```mermaid
sequenceDiagram
    participant App as user-service<br/>(Cluster EU)
    participant ztunnel1 as ztunnel<br/>(Cluster EU)
    participant istiod1 as istiod<br/>(Cluster EU)
    participant EWG1 as East-West GW<br/>(Cluster EU)
    participant EWG2 as East-West GW<br/>(Cluster US)
    participant ztunnel2 as ztunnel<br/>(Cluster US)
    participant Notif as notification-service<br/>(Cluster US)
    
    Note over App: httpx.post("http://notification-service:8000/...")
    
    App->>ztunnel1: Connect to notification-service
    ztunnel1->>istiod1: Where is notification-service?
    
    Note over istiod1: Service Registry:<br/>notification-service exists in:<br/>- Cluster US (3 pods)<br/>- Cluster Asia (2 pods)
    
    istiod1-->>ztunnel1: Endpoints:<br/>- eastwest-gw.us:15443<br/>- eastwest-gw.asia:15443
    
    Note over ztunnel1: Locality-aware LB:<br/>→ Choose closest cluster
    
    ztunnel1->>EWG1: HBONE tunnel request
    EWG1->>EWG2: mTLS over Internet
    EWG2->>ztunnel2: Forward to notification-service
    ztunnel2->>Notif: Local delivery
    
    Notif-->>ztunnel2: Response
    ztunnel2-->>EWG2: Response
    EWG2-->>EWG1: Response
    EWG1-->>ztunnel1: Response
    ztunnel1-->>App: Response
    
    Note over App, Notif: ✅ Прозрачно для приложения!<br/>Код не знает о мультикластере
```

### 16.6 Конфигурация для мультикластера

#### Шаг 1: Shared Trust (общий Root CA)

```bash
# Создаём общий Root CA для всех кластеров
# (в production используйте Vault, cert-manager или облачный CA)

# Генерируем Root CA
openssl req -x509 -sha256 -nodes -days 3650 \
  -newkey rsa:4096 \
  -subj "/O=HyperPorto/CN=Root CA" \
  -keyout root-key.pem \
  -out root-cert.pem

# Для каждого кластера — Intermediate CA
for CLUSTER in eu us asia; do
  mkdir -p certs/${CLUSTER}
  
  # Intermediate CA key
  openssl req -newkey rsa:4096 -nodes \
    -subj "/O=HyperPorto/CN=Intermediate CA ${CLUSTER}" \
    -keyout certs/${CLUSTER}/ca-key.pem \
    -out certs/${CLUSTER}/ca-csr.pem
  
  # Sign with Root CA
  openssl x509 -req -days 730 -CAcreateserial \
    -CA root-cert.pem -CAkey root-key.pem \
    -in certs/${CLUSTER}/ca-csr.pem \
    -out certs/${CLUSTER}/ca-cert.pem
  
  # Copy root cert
  cp root-cert.pem certs/${CLUSTER}/root-cert.pem
  
  # Create cert chain
  cat certs/${CLUSTER}/ca-cert.pem root-cert.pem > \
    certs/${CLUSTER}/cert-chain.pem
done
```

#### Шаг 2: Установка Istio с Multi-Cluster

```yaml
# cluster-eu.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-eu
spec:
  profile: ambient
  
  values:
    global:
      meshID: hyper-porto-mesh      # Одинаковый для всех кластеров!
      multiCluster:
        clusterName: cluster-eu
      network: network-eu           # Сетевая зона
      
  components:
    ingressGateways:
    - name: istio-eastwestgateway
      label:
        istio: eastwestgateway
        topology.istio.io/network: network-eu
      enabled: true
      k8s:
        env:
        - name: ISTIO_META_ROUTER_MODE
          value: "sni-dnat"
        - name: ISTIO_META_REQUESTED_NETWORK_VIEW
          value: network-eu
        service:
          ports:
          - name: tls
            port: 15443
            targetPort: 15443
```

```bash
# Применяем для каждого кластера
istioctl install -f cluster-eu.yaml --context=cluster-eu
istioctl install -f cluster-us.yaml --context=cluster-us
istioctl install -f cluster-asia.yaml --context=cluster-asia
```

#### Шаг 3: Cross-Cluster Service Discovery

```bash
# Cluster EU должен знать о сервисах в Cluster US
# Создаём Secret с kubeconfig удалённого кластера

# На Cluster EU — добавляем доступ к Cluster US
istioctl create-remote-secret \
  --context=cluster-us \
  --name=cluster-us | \
  kubectl apply -f - --context=cluster-eu

# На Cluster EU — добавляем доступ к Cluster Asia
istioctl create-remote-secret \
  --context=cluster-asia \
  --name=cluster-asia | \
  kubectl apply -f - --context=cluster-eu

# Повторяем для всех пар кластеров (full mesh)
```

#### Шаг 4: East-West Gateway для cross-cluster traffic

```yaml
# east-west-gateway.yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: cross-cluster-gateway
  namespace: istio-system
spec:
  selector:
    istio: eastwestgateway
  servers:
  - port:
      number: 15443
      name: tls
      protocol: TLS
    tls:
      mode: AUTO_PASSTHROUGH  # SNI-based routing
    hosts:
    - "*.local"  # Все .local домены (Kubernetes services)
```

### 16.7 Service Discovery: Ваш код НЕ меняется!

**Главное преимущество Istio Multi-Cluster:**

```python
# src/Containers/AppSection/UserModule/Actions/CreateUserAction.py

# Ваш код остаётся ТОЧНО ТАКИМ ЖЕ!
# Istio сам находит сервис в нужном кластере

async def send_notification(self, user_id: str):
    async with httpx.AsyncClient() as client:
        # notification-service может быть в:
        # - Этом же кластере
        # - Другом кластере EU
        # - Кластере US
        # - Кластере Asia
        # Istio сам выберет оптимальный!
        
        response = await client.post(
            "http://notification-service:8000/api/v1/notifications",
            json={"user_id": user_id, "message": "Welcome!"}
        )
```

**Settings тоже не меняются:**

```python
# src/Ship/Configs/Settings.py

class Settings(BaseSettings):
    # Тот же URL — Istio резолвит автоматически
    notification_service_url: str = Field(
        default="http://notification-service:8000"
    )
    
    # Istio знает, что notification-service есть в:
    # - cluster-us (3 replicas)
    # - cluster-asia (2 replicas)
    # И выберет ближайший!
```

### 16.8 Locality-Aware Load Balancing

Istio автоматически предпочитает **локальные** инстансы:

```mermaid
flowchart LR
    subgraph EU["Cluster EU"]
        UserEU["user-service"]
        NotifEU["notification-service<br/>(если есть)"]
    end
    
    subgraph US["Cluster US"]
        NotifUS["notification-service<br/>⭐ Primary"]
    end
    
    subgraph Asia["Cluster Asia"]
        NotifAsia["notification-service"]
    end
    
    UserEU -->|"1️⃣ Приоритет:<br/>Локальный"| NotifEU
    UserEU -->|"2️⃣ Fallback:<br/>Ближайший кластер"| NotifUS
    UserEU -->|"3️⃣ Last resort:<br/>Дальний кластер"| NotifAsia
    
    style NotifEU fill:#c8e6c9
    style NotifUS fill:#fff9c4
    style NotifAsia fill:#ffcdd2
```

**Настройка Locality Load Balancing:**

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: notification-service-locality
  namespace: support
spec:
  host: notification-service.support.svc.cluster.local
  trafficPolicy:
    connectionPool:
      http:
        h2UpgradePolicy: UPGRADE  # HTTP/2
    loadBalancer:
      simple: LEAST_REQUEST
      localityLbSetting:
        enabled: true
        # Распределение при failover
        failover:
        - from: eu/*          # Если EU недоступен
          to: us/*            # → идём в US
        - from: us/*          # Если US недоступен  
          to: eu/*            # → идём в EU
        - from: asia/*        # Если Asia недоступен
          to: us/*            # → идём в US
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 30s
      baseEjectionTime: 30s
```

### 16.9 Cross-Cluster Authorization

```yaml
# Разрешаем user-service из любого кластера
# обращаться к notification-service
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-cross-cluster-notification
  namespace: support
spec:
  selector:
    matchLabels:
      app: notification-service
  action: ALLOW
  rules:
  - from:
    - source:
        # Principal содержит cluster ID
        principals:
        - "cluster.local/ns/hyper-porto/sa/user-service"
        # Или по namespace
        namespaces:
        - "hyper-porto"
    to:
    - operation:
        methods: ["POST", "GET"]
        paths: ["/api/v1/notifications*"]
```

### 16.10 Схема трафика в мультикластере

```mermaid
flowchart TB
    subgraph Users["🌐 Global Users"]
        UserEU["Users EU"]
        UserUS["Users US"]
        UserAsia["Users Asia"]
    end
    
    subgraph GLB["Global Load Balancer"]
        DNS["GeoDNS /<br/>Cloud LB"]
    end
    
    subgraph ClusterEU["☸️ Cluster EU"]
        IGEU["Ingress GW"]
        subgraph AppsEU["Services"]
            UserSvcEU["user-service"]
            SearchSvcEU["search-service"]
        end
        EWGEU["East-West GW"]
    end
    
    subgraph ClusterUS["☸️ Cluster US"]
        IGUS["Ingress GW"]
        subgraph AppsUS["Services"]
            UserSvcUS["user-service"]
            NotifSvcUS["notification-service"]
            AuditSvcUS["audit-service"]
        end
        EWGUS["East-West GW"]
    end
    
    subgraph ClusterAsia["☸️ Cluster Asia"]
        IGAsia["Ingress GW"]
        subgraph AppsAsia["Services"]
            UserSvcAsia["user-service"]
            PaymentSvcAsia["payment-service"]
        end
        EWGAsia["East-West GW"]
    end
    
    UserEU --> DNS
    UserUS --> DNS
    UserAsia --> DNS
    
    DNS -->|"EU users"| IGEU
    DNS -->|"US users"| IGUS
    DNS -->|"Asia users"| IGAsia
    
    IGEU --> UserSvcEU
    IGUS --> UserSvcUS
    IGAsia --> UserSvcAsia
    
    UserSvcEU -->|"notification-service<br/>не в EU → cross-cluster"| EWGEU
    EWGEU <-->|"mTLS"| EWGUS
    EWGUS --> NotifSvcUS
    
    UserSvcAsia -->|"audit-service<br/>не в Asia → cross-cluster"| EWGAsia
    EWGAsia <-->|"mTLS"| EWGUS
    EWGUS --> AuditSvcUS
    
    style DNS fill:#ffeb3b
    style EWGEU fill:#c8e6c9
    style EWGUS fill:#c8e6c9
    style EWGAsia fill:#c8e6c9
```

### 16.11 Распределение сервисов Hyper-Porto по кластерам

**Пример стратегии размещения:**

| Сервис | Cluster EU | Cluster US | Cluster Asia | Причина |
|--------|------------|------------|--------------|---------|
| user-service | ✅ | ✅ | ✅ | Нужен везде (latency) |
| search-service | ✅ | ✅ | ✅ | Нужен везде (latency) |
| notification-service | ❌ | ✅ Primary | ✅ | Можно централизовать |
| audit-service | ❌ | ✅ Primary | ❌ | Централизованный аудит |
| payment-service | ❌ | ❌ | ✅ Primary | Asia payment providers |
| email-service | ❌ | ✅ Primary | ❌ | Централизованная отправка |
| webhook-service | ✅ | ✅ | ✅ | Нужен везде (callbacks) |

### 16.12 Settings для мультикластера

```python
# src/Ship/Configs/Settings.py

class Settings(BaseSettings):
    """Settings с поддержкой мультикластера."""
    
    # === Идентификация ===
    service_name: str = Field(default="user-service")
    cluster_name: str = Field(default="cluster-eu")  # Текущий кластер
    region: str = Field(default="eu-west-1")
    
    # === Service URLs ===
    # Istio резолвит автоматически — не нужно указывать кластер!
    notification_service_url: str = Field(
        default="http://notification-service.support:8000"
    )
    audit_service_url: str = Field(
        default="http://audit-service.support:8000"
    )
    
    # === Для сервисов, которые ДОЛЖНЫ быть локальными ===
    # Используем locality-specific naming
    local_cache_url: str = Field(
        default="redis://redis.data:6379/0"  # Локальный Redis
    )
    
    # === Для централизованных сервисов ===
    # Явно указываем "primary" кластер через ServiceEntry
    central_audit_url: str = Field(
        default="http://audit-service.support:8000"  # Istio найдёт primary
    )
```

### 16.13 ServiceEntry для внешних сервисов

Если нужно обращаться к сервисам **вне** mesh:

```yaml
# Внешний email провайдер
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: sendgrid-api
  namespace: vendor
spec:
  hosts:
  - api.sendgrid.com
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  location: MESH_EXTERNAL
  resolution: DNS
---
# DestinationRule для mTLS к внешнему сервису
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: sendgrid-api
  namespace: vendor
spec:
  host: api.sendgrid.com
  trafficPolicy:
    tls:
      mode: SIMPLE  # TLS к внешнему сервису
    connectionPool:
      http:
        h2UpgradePolicy: DO_NOT_UPGRADE
```

### 16.14 Мониторинг Cross-Cluster трафика

```yaml
# Prometheus query для cross-cluster метрик
# Трафик между кластерами
sum(rate(istio_requests_total{
  source_cluster!="",
  destination_cluster!="",
  source_cluster!=destination_cluster
}[5m])) by (source_cluster, destination_cluster, destination_service)

# Latency cross-cluster
histogram_quantile(0.99,
  sum(rate(istio_request_duration_milliseconds_bucket{
    source_cluster!=destination_cluster
  }[5m])) by (le, source_cluster, destination_cluster)
)
```

### 16.15 Best Practices для мультикластера

| Практика | Описание |
|----------|----------|
| **Shared Root CA** | Один Root CA для всех кластеров |
| **Unique Cluster Names** | `cluster-eu`, `cluster-us`, не `cluster1` |
| **Network Naming** | Отражает реальную топологию (`network-eu`) |
| **Locality Labels** | `topology.kubernetes.io/region`, `topology.kubernetes.io/zone` |
| **East-West Gateway** | Для каждого кластера свой |
| **Locality LB** | Предпочитать локальные инстансы |
| **Circuit Breaker** | Outlier detection для failover |
| **Централизованный observability** | Grafana/Jaeger смотрят на все кластеры |

### 16.12 Пример: Полная конфигурация для Production

```yaml
# === Deployment ===
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
  namespace: hyper-porto
spec:
  template:
    spec:
      containers:
      - name: user-service
        image: user-service:v1.0.0
        envFrom:
        - configMapRef:
            name: user-service-config
        - secretRef:
            name: user-service-secrets

---
# === ConfigMap (non-sensitive) ===
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
  namespace: hyper-porto
data:
  SERVICE_NAME: "user-service"
  APP_ENV: "production"
  APP_DEBUG: "false"
  
  # Service Discovery — Kubernetes DNS
  NOTIFICATION_SERVICE_URL: "http://notification-service.support:8000"
  AUDIT_SERVICE_URL: "http://audit-service.support:8000"
  SEARCH_SERVICE_URL: "http://search-service:8000"
  PAYMENT_SERVICE_URL: "http://payment-service.vendor:8000"
  
  # Shared infrastructure
  REDIS_URL: "redis://redis.data:6379/0"
  EVENT_BROKER_URL: "redis://redis.data:6379/1"
  KAFKA_BOOTSTRAP_SERVERS: "kafka.data:9092"

---
# === Secret (sensitive) ===
apiVersion: v1
kind: Secret
metadata:
  name: user-service-secrets
  namespace: hyper-porto
type: Opaque
stringData:
  DB_URL: "postgresql://user:password@postgres.data:5432/users"
  JWT_SECRET: "super-secret-jwt-key"

---
# === Service ===
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: hyper-porto
  labels:
    app: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 8000
    targetPort: 8000
    name: http
```

---

## 📚 Связанная документация

- [00-philosophy.md](00-philosophy.md) — Философия Hyper-Porto
- [17-microservice-extraction-guide.md](17-microservice-extraction-guide.md) — Вынос модулей
- [17-microservice-extraction-guide.md](17-microservice-extraction-guide.md) — Практическое руководство
- [13-cross-module-communication.md](13-cross-module-communication.md) — Кросс-модульное взаимодействие

### Внешние ресурсы

- [Istio Ambient Mode Documentation](https://istio.io/latest/docs/ambient/)
- [Kubernetes Gateway API](https://gateway-api.sigs.k8s.io/)
- [SPIFFE/SPIRE](https://spiffe.io/)

---

<div align="center">

**Hyper-Porto + Istio Ambient Mesh**

*Zero-trust networking без sidecar'ов*

🌊 Ambient + 🔐 mTLS + 📊 Observability = 🚀 Production-Ready Microservices

</div>

