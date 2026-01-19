# 📊 Архитектурные диаграммы Porto

## 🏗️ Общая архитектура системы

```mermaid
graph TB
    subgraph "External Layer"
        CLIENT["🌐 Web Client"]
        MOBILE["📱 Mobile App"]
        API_CLIENT["🔌 API Client"]
    end
    
    subgraph "API Gateway Layer"
        GATEWAY["🚪 API Gateway<br/>Rate Limiting, Auth, Routing"]
    end
    
    subgraph "Application Layer - Porto"
        subgraph "Containers Layer"
            subgraph "AppSection"
                USER_C["👤 User Container"]
                BOOK_C["📚 Book Container"]
                ORDER_C["🛒 Order Container"]
                AUTH_C["🔐 Auth Container"]
            end
            
            subgraph "VendorSection"
                PAYMENT_C["💳 Payment Container"]
                EMAIL_C["📧 Email Container"]
                SMS_C["📱 SMS Container"]
                STORAGE_C["☁️ Storage Container"]
            end
        end
        
        subgraph "Ship Layer"
            CORE["⚙️ Core<br/>Database, Cache, Logger"]
            PARENTS["🎯 Parents<br/>Base Classes"]
            PROVIDERS["🔌 Providers<br/>DI Container"]
            MIDDLEWARE["🛡️ Middleware<br/>Auth, CORS, etc"]
        end
    end
    
    subgraph "Infrastructure Layer"
        subgraph "Data Storage"
            POSTGRES["🐘 PostgreSQL"]
            REDIS["📦 Redis Cache"]
            S3["☁️ S3 Storage"]
        end
        
        subgraph "Message Queue"
            RABBITMQ["🐰 RabbitMQ"]
            KAFKA["📨 Kafka"]
        end
        
        subgraph "Monitoring"
            LOGFIRE["📊 Logfire"]
            PROMETHEUS["📈 Prometheus"]
            GRAFANA["📉 Grafana"]
        end
    end
    
    CLIENT --> GATEWAY
    MOBILE --> GATEWAY
    API_CLIENT --> GATEWAY
    
    GATEWAY --> USER_C
    GATEWAY --> BOOK_C
    GATEWAY --> ORDER_C
    GATEWAY --> AUTH_C
    
    USER_C --> CORE
    BOOK_C --> CORE
    ORDER_C --> CORE
    AUTH_C --> CORE
    
    ORDER_C --> PAYMENT_C
    USER_C --> EMAIL_C
    USER_C --> SMS_C
    BOOK_C --> STORAGE_C
    
    CORE --> POSTGRES
    CORE --> REDIS
    STORAGE_C --> S3
    
    EMAIL_C --> RABBITMQ
    SMS_C --> RABBITMQ
    
    CORE --> LOGFIRE
    CORE --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    
    style CLIENT fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style MOBILE fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style API_CLIENT fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style GATEWAY fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style USER_C fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style BOOK_C fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style ORDER_C fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style AUTH_C fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style PAYMENT_C fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style EMAIL_C fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style CORE fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style POSTGRES fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style REDIS fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    style RABBITMQ fill:#f1f8e9,stroke:#689f38,stroke-width:2px
```

## 🔄 Request Flow Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant M as Middleware
    participant CT as Controller
    participant A as Action
    participant T1 as Task 1
    participant T2 as Task 2
    participant R as Repository
    participant DB as Database
    participant Q as Queue
    participant N as Notifier
    
    C->>G: HTTP Request
    G->>G: Rate Limiting
    G->>M: Authenticated Request
    M->>M: Validate JWT
    M->>M: Check Permissions
    M->>CT: Authorized Request
    
    CT->>CT: Validate Input
    CT->>A: Execute Action
    
    A->>T1: Run Validation Task
    T1->>R: Check Business Rules
    R->>DB: Query Data
    DB-->>R: Result Set
    R-->>T1: Validated Data
    T1-->>A: Validation OK
    
    A->>T2: Run Creation Task
    T2->>DB: Insert Data
    DB-->>T2: Created Record
    T2-->>A: Created Entity
    
    A->>Q: Publish Event
    Q-->>N: Async Notification
    
    A-->>CT: Action Result
    CT-->>M: Response
    M-->>G: Formatted Response
    G-->>C: HTTP Response
    
    N->>N: Send Email/SMS
```

## 🎯 Porto Components Interaction

```mermaid
graph LR
    subgraph "HTTP Request"
        REQ["📥 Request"]
        RES["📤 Response"]
    end
    
    subgraph "UI Layer"
        ROUTE["🛤️ Route"]
        CTRL["🎮 Controller"]
        TRANS["🔄 Transformer"]
    end
    
    subgraph "Business Logic"
        ACTION["🎯 Action"]
        subgraph "Tasks"
            T1["⚡ Validate Task"]
            T2["⚡ Process Task"]
            T3["⚡ Save Task"]
            T4["⚡ Notify Task"]
        end
    end
    
    subgraph "Data Layer"
        REPO["📚 Repository"]
        MODEL["💾 Model"]
        CACHE["📦 Cache"]
    end
    
    subgraph "External"
        EXT_API["🌐 External API"]
        QUEUE["📨 Message Queue"]
    end
    
    REQ --> ROUTE
    ROUTE --> CTRL
    CTRL --> ACTION
    
    ACTION --> T1
    T1 --> T2
    T2 --> T3
    T3 --> T4
    
    T1 --> REPO
    T2 --> EXT_API
    T3 --> MODEL
    T4 --> QUEUE
    
    REPO --> CACHE
    REPO --> MODEL
    
    ACTION --> TRANS
    TRANS --> CTRL
    CTRL --> RES
    
    style REQ fill:#ffcccc,stroke:#333,stroke-width:2px
    style ACTION fill:#ccffcc,stroke:#333,stroke-width:3px
    style T1 fill:#ccccff,stroke:#333,stroke-width:2px
    style T2 fill:#ccccff,stroke:#333,stroke-width:2px
    style T3 fill:#ccccff,stroke:#333,stroke-width:2px
    style T4 fill:#ccccff,stroke:#333,stroke-width:2px
    style MODEL fill:#ffffcc,stroke:#333,stroke-width:2px
```

## 📦 Container Internal Structure

```mermaid
graph TD
    subgraph "Book Container"
        subgraph "Entry Points"
            API["🌐 API Controller"]
            CLI["💻 CLI Command"]
            EVENT["📡 Event Handler"]
            CRON["⏰ Cron Job"]
        end
        
        subgraph "Business Logic"
            subgraph "Actions"
                CA["Create Book Action"]
                UA["Update Book Action"]
                DA["Delete Book Action"]
                LA["List Books Action"]
            end
            
            subgraph "Tasks"
                VT["Validate Book Task"]
                CT["Create Book Task"]
                UT["Update Book Task"]
                DT["Delete Book Task"]
                FT["Find Book Task"]
                NT["Notify Task"]
            end
        end
        
        subgraph "Data & Infrastructure"
            subgraph "Models"
                BM["Book Model"]
                BLM["BookLoan Model"]
            end
            
            subgraph "Repositories"
                BR["Book Repository"]
                BLR["BookLoan Repository"]
            end
            
            subgraph "Services"
                IS["ISBN Service"]
                PS["Price Service"]
            end
        end
        
        subgraph "Support"
            EX["Exceptions"]
            VAL["Validators"]
            TRANS["Transformers"]
            PROV["DI Provider"]
        end
    end
    
    API --> CA
    API --> UA
    API --> DA
    API --> LA
    
    CLI --> CA
    EVENT --> UA
    CRON --> LA
    
    CA --> VT
    CA --> CT
    CA --> NT
    
    UA --> FT
    UA --> VT
    UA --> UT
    
    DA --> FT
    DA --> DT
    
    LA --> FT
    
    CT --> BR
    UT --> BR
    DT --> BR
    FT --> BR
    
    BR --> BM
    BLR --> BLM
    
    VT --> IS
    CT --> PS
    
    style API fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style CA fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style VT fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style BM fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

## 🔐 Authentication & Authorization Flow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as Auth Service
    participant T as Token Store
    participant G as Gateway
    participant S as Service
    
    U->>F: Enter Credentials
    F->>A: POST /auth/login
    A->>A: Validate Credentials
    A->>A: Generate JWT
    A->>T: Store Refresh Token
    A-->>F: Access & Refresh Tokens
    F->>F: Store Tokens
    
    F->>G: Request + JWT
    G->>G: Validate JWT
    G->>G: Check Expiry
    G->>G: Verify Permissions
    G->>S: Authorized Request
    S-->>G: Response
    G-->>F: Response
    
    Note over F,G: Token Expired
    
    F->>A: POST /auth/refresh
    A->>T: Validate Refresh Token
    T-->>A: Token Valid
    A->>A: Generate New JWT
    A-->>F: New Access Token
    F->>F: Update Token
    F->>G: Retry Request
```

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        subgraph "Load Balancer"
            LB["🔄 Nginx/HAProxy"]
        end
        
        subgraph "Application Servers"
            APP1["🖥️ App Server 1<br/>Porto Application"]
            APP2["🖥️ App Server 2<br/>Porto Application"]
            APP3["🖥️ App Server 3<br/>Porto Application"]
        end
        
        subgraph "Background Workers"
            W1["⚙️ Worker 1<br/>Email Processing"]
            W2["⚙️ Worker 2<br/>Report Generation"]
            W3["⚙️ Worker 3<br/>Data Sync"]
        end
        
        subgraph "Data Layer"
            subgraph "Primary DB"
                PG_PRIMARY["🐘 PostgreSQL Primary"]
            end
            
            subgraph "Read Replicas"
                PG_R1["📖 Read Replica 1"]
                PG_R2["📖 Read Replica 2"]
            end
            
            subgraph "Cache Layer"
                REDIS1["📦 Redis Master"]
                REDIS2["📦 Redis Slave"]
            end
        end
        
        subgraph "Message Queue"
            RMQ["🐰 RabbitMQ Cluster"]
        end
        
        subgraph "Storage"
            S3["☁️ S3/MinIO"]
        end
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    
    APP1 --> PG_PRIMARY
    APP2 --> PG_R1
    APP3 --> PG_R2
    
    APP1 --> REDIS1
    APP2 --> REDIS1
    APP3 --> REDIS1
    
    REDIS1 --> REDIS2
    
    APP1 --> RMQ
    APP2 --> RMQ
    APP3 --> RMQ
    
    RMQ --> W1
    RMQ --> W2
    RMQ --> W3
    
    W1 --> PG_PRIMARY
    W2 --> PG_PRIMARY
    W3 --> PG_PRIMARY
    
    APP1 --> S3
    APP2 --> S3
    APP3 --> S3
    
    PG_PRIMARY --> PG_R1
    PG_PRIMARY --> PG_R2
    
    style LB fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style PG_PRIMARY fill:#4caf50,stroke:#2e7d32,stroke-width:3px
    style REDIS1 fill:#f44336,stroke:#c62828,stroke-width:2px
    style RMQ fill:#ff9800,stroke:#e65100,stroke-width:2px
```

## 🔄 Event-Driven Architecture

```mermaid
graph LR
    subgraph "Event Producers"
        P1["📚 Book Service"]
        P2["👤 User Service"]
        P3["🛒 Order Service"]
    end
    
    subgraph "Message Broker"
        subgraph "Topics/Exchanges"
            T1["📬 books.events"]
            T2["📬 users.events"]
            T3["📬 orders.events"]
        end
        
        subgraph "Queues"
            Q1["📥 notification.queue"]
            Q2["📥 analytics.queue"]
            Q3["📥 audit.queue"]
            Q4["📥 inventory.queue"]
        end
    end
    
    subgraph "Event Consumers"
        C1["📧 Notification Service"]
        C2["📊 Analytics Service"]
        C3["📝 Audit Service"]
        C4["📦 Inventory Service"]
    end
    
    P1 -->|book.created| T1
    P1 -->|book.updated| T1
    P1 -->|book.deleted| T1
    
    P2 -->|user.registered| T2
    P2 -->|user.updated| T2
    
    P3 -->|order.placed| T3
    P3 -->|order.cancelled| T3
    
    T1 --> Q1
    T1 --> Q2
    T1 --> Q3
    T1 --> Q4
    
    T2 --> Q1
    T2 --> Q2
    T2 --> Q3
    
    T3 --> Q1
    T3 --> Q2
    T3 --> Q4
    
    Q1 --> C1
    Q2 --> C2
    Q3 --> C3
    Q4 --> C4
    
    style P1 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style P2 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style P3 fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    style T1 fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style T2 fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style T3 fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style C1 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style C2 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style C3 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style C4 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
```

## 🏗️ Microservices Evolution

```mermaid
graph TD
    subgraph "Phase 1: Monolith"
        MONO["🏢 Monolithic Application<br/>All Containers Together"]
    end
    
    subgraph "Phase 2: Modular Monolith"
        subgraph "Single Process"
            MM_USER["👤 User Module"]
            MM_BOOK["📚 Book Module"]
            MM_ORDER["🛒 Order Module"]
            MM_SHARED["🔧 Shared Ship"]
        end
    end
    
    subgraph "Phase 3: Service Separation"
        subgraph "User Service"
            US_CONT["👤 User Container"]
            US_SHIP["🚢 User Ship"]
        end
        
        subgraph "Book Service"
            BS_CONT["📚 Book Container"]
            BS_SHIP["🚢 Book Ship"]
        end
        
        subgraph "Order Service"
            OS_CONT["🛒 Order Container"]
            OS_SHIP["🚢 Order Ship"]
        end
        
        MQ["📨 Message Queue"]
    end
    
    subgraph "Phase 4: Full Microservices"
        subgraph "API Gateway"
            GW["🚪 Gateway"]
        end
        
        subgraph "Services"
            MS1["👤 User μService<br/>+ Own DB"]
            MS2["📚 Book μService<br/>+ Own DB"]
            MS3["🛒 Order μService<br/>+ Own DB"]
            MS4["💳 Payment μService<br/>+ Own DB"]
        end
        
        subgraph "Infrastructure"
            SD["🔍 Service Discovery"]
            CB["🔌 Circuit Breaker"]
            CONFIG["⚙️ Config Service"]
        end
    end
    
    MONO --> MM_USER
    MONO --> MM_BOOK
    MONO --> MM_ORDER
    
    MM_USER --> US_CONT
    MM_BOOK --> BS_CONT
    MM_ORDER --> OS_CONT
    MM_SHARED --> US_SHIP
    MM_SHARED --> BS_SHIP
    MM_SHARED --> OS_SHIP
    
    US_CONT --> MS1
    BS_CONT --> MS2
    OS_CONT --> MS3
    
    MQ --> GW
    GW --> MS1
    GW --> MS2
    GW --> MS3
    GW --> MS4
    
    MS1 --> SD
    MS2 --> SD
    MS3 --> SD
    MS4 --> SD
    
    style MONO fill:#ffcccc,stroke:#333,stroke-width:3px
    style GW fill:#ccffcc,stroke:#333,stroke-width:3px
    style MS1 fill:#ccccff,stroke:#333,stroke-width:2px
    style MS2 fill:#ccccff,stroke:#333,stroke-width:2px
    style MS3 fill:#ccccff,stroke:#333,stroke-width:2px
    style MS4 fill:#ccccff,stroke:#333,stroke-width:2px
```

## 🧪 Testing Strategy

```mermaid
graph TB
    subgraph "Testing Pyramid"
        subgraph "Unit Tests - 70%"
            UT1["✅ Task Tests"]
            UT2["✅ Action Tests"]
            UT3["✅ Model Tests"]
            UT4["✅ Validator Tests"]
        end
        
        subgraph "Integration Tests - 20%"
            IT1["🔄 Container Tests"]
            IT2["🔄 API Tests"]
            IT3["🔄 Database Tests"]
        end
        
        subgraph "E2E Tests - 10%"
            E2E1["🌐 User Journey Tests"]
            E2E2["🌐 Critical Path Tests"]
        end
    end
    
    subgraph "Test Execution"
        LOCAL["💻 Local Tests<br/>Pre-commit"]
        CI["🔧 CI Pipeline<br/>On Push"]
        STAGING["🎯 Staging Tests<br/>Pre-deploy"]
        PROD["✅ Production Tests<br/>Post-deploy"]
    end
    
    UT1 --> LOCAL
    UT2 --> LOCAL
    UT3 --> LOCAL
    UT4 --> LOCAL
    
    IT1 --> CI
    IT2 --> CI
    IT3 --> CI
    
    E2E1 --> STAGING
    E2E2 --> STAGING
    
    STAGING --> PROD
    
    style UT1 fill:#4caf50,stroke:#2e7d32,stroke-width:2px
    style UT2 fill:#4caf50,stroke:#2e7d32,stroke-width:2px
    style UT3 fill:#4caf50,stroke:#2e7d32,stroke-width:2px
    style UT4 fill:#4caf50,stroke:#2e7d32,stroke-width:2px
    style IT1 fill:#ff9800,stroke:#e65100,stroke-width:2px
    style IT2 fill:#ff9800,stroke:#e65100,stroke-width:2px
    style IT3 fill:#ff9800,stroke:#e65100,stroke-width:2px
    style E2E1 fill:#f44336,stroke:#c62828,stroke-width:2px
    style E2E2 fill:#f44336,stroke:#c62828,stroke-width:2px
```

## 📊 Data Flow in Porto

```mermaid
graph TD
    subgraph "Input Sources"
        HTTP["🌐 HTTP Request"]
        WS["🔌 WebSocket"]
        CLI["💻 CLI Command"]
        EVENT["📡 Event"]
        CRON["⏰ Scheduled Job"]
    end
    
    subgraph "Porto Processing"
        subgraph "Entry Layer"
            ROUTE["🛤️ Route/Command"]
            HANDLER["🎮 Handler/Controller"]
        end
        
        subgraph "Business Layer"
            ACTION["🎯 Action<br/>Orchestration"]
            TASKS["⚡ Tasks<br/>Atomic Operations"]
        end
        
        subgraph "Data Layer"
            REPO["📚 Repository<br/>Data Access"]
            MODEL["💾 Model<br/>Data Structure"]
        end
        
        subgraph "Infrastructure"
            DB["🗄️ Database"]
            CACHE["📦 Cache"]
            QUEUE["📨 Queue"]
        end
    end
    
    subgraph "Output"
        RESPONSE["📤 Response"]
        NOTIFICATION["📧 Notification"]
        LOG["📊 Log/Metric"]
    end
    
    HTTP --> ROUTE
    WS --> ROUTE
    CLI --> ROUTE
    EVENT --> HANDLER
    CRON --> HANDLER
    
    ROUTE --> HANDLER
    HANDLER --> ACTION
    ACTION --> TASKS
    TASKS --> REPO
    REPO --> MODEL
    MODEL --> DB
    REPO --> CACHE
    
    ACTION --> QUEUE
    ACTION --> LOG
    
    HANDLER --> RESPONSE
    QUEUE --> NOTIFICATION
    
    style ACTION fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style TASKS fill:#4caf50,stroke:#2e7d32,stroke-width:2px
    style DB fill:#2196f3,stroke:#0d47a1,stroke-width:2px
```

## 🔒 Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Network Security"
            FW["🔥 Firewall"]
            WAF["🛡️ WAF"]
            DDoS["⚡ DDoS Protection"]
        end
        
        subgraph "Application Security"
            AUTH["🔐 Authentication<br/>JWT, OAuth2"]
            AUTHZ["👮 Authorization<br/>RBAC, ABAC"]
            VALID["✅ Input Validation"]
            SANITIZE["🧹 Output Sanitization"]
        end
        
        subgraph "Data Security"
            ENCRYPT["🔒 Encryption at Rest"]
            TLS["🔐 TLS in Transit"]
            HASH["#️⃣ Password Hashing<br/>Argon2, BCrypt"]
            MASK["🎭 Data Masking"]
        end
        
        subgraph "Monitoring"
            AUDIT["📝 Audit Logging"]
            SIEM["🚨 SIEM"]
            ALERT["📢 Security Alerts"]
        end
    end
    
    FW --> WAF
    WAF --> DDoS
    DDoS --> AUTH
    AUTH --> AUTHZ
    AUTHZ --> VALID
    VALID --> SANITIZE
    
    SANITIZE --> ENCRYPT
    ENCRYPT --> TLS
    TLS --> HASH
    HASH --> MASK
    
    MASK --> AUDIT
    AUDIT --> SIEM
    SIEM --> ALERT
    
    style FW fill:#ff5252,stroke:#c62828,stroke-width:3px
    style AUTH fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    style ENCRYPT fill:#4caf50,stroke:#2e7d32,stroke-width:3px
    style AUDIT fill:#2196f3,stroke:#0d47a1,stroke-width:3px
```

## 📈 Performance Monitoring

```mermaid
graph LR
    subgraph "Application"
        APP["🚀 Porto App"]
    end
    
    subgraph "Metrics Collection"
        METRICS["📊 Metrics<br/>Prometheus"]
        LOGS["📝 Logs<br/>Logfire"]
        TRACES["🔍 Traces<br/>OpenTelemetry"]
    end
    
    subgraph "Storage"
        TSDB["⏰ Time Series DB"]
        LOG_STORE["📚 Log Storage"]
        TRACE_STORE["🗄️ Trace Storage"]
    end
    
    subgraph "Visualization"
        GRAFANA["📈 Grafana"]
        KIBANA["🔍 Kibana"]
        JAEGER["🕵️ Jaeger"]
    end
    
    subgraph "Alerting"
        ALERT_MGR["🚨 Alert Manager"]
        PAGER["📟 PagerDuty"]
        SLACK["💬 Slack"]
    end
    
    APP --> METRICS
    APP --> LOGS
    APP --> TRACES
    
    METRICS --> TSDB
    LOGS --> LOG_STORE
    TRACES --> TRACE_STORE
    
    TSDB --> GRAFANA
    LOG_STORE --> KIBANA
    TRACE_STORE --> JAEGER
    
    GRAFANA --> ALERT_MGR
    KIBANA --> ALERT_MGR
    JAEGER --> ALERT_MGR
    
    ALERT_MGR --> PAGER
    ALERT_MGR --> SLACK
    
    style APP fill:#4caf50,stroke:#2e7d32,stroke-width:3px
    style GRAFANA fill:#ff9800,stroke:#e65100,stroke-width:2px
    style ALERT_MGR fill:#f44336,stroke:#c62828,stroke-width:2px
```

## 🎯 Заключение

Эти диаграммы показывают:

1. **Масштабируемость** - от монолита к микросервисам
2. **Модульность** - чёткое разделение ответственности
3. **Гибкость** - легко добавлять новые компоненты
4. **Надёжность** - множественные уровни защиты
5. **Производительность** - оптимизированные потоки данных

Porto архитектура обеспечивает чистую, понятную и масштабируемую структуру для современных приложений.

---

<div align="center">

**📊 Visual Architecture Guide Complete!**

[← API Reference](09-api-reference.md) | [AI Development →](11-ai-development.md)

</div>
