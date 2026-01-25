# 09. Security Patterns

> **Защита распределённой системы**

---

## Проблема безопасности

В микросервисах **поверхность атаки** увеличивается:
- Много точек входа (каждый сервис)
- Сетевой трафик между сервисами
- Много мест для хранения секретов
- Сложнее контролировать доступ

Security Patterns защищают данные и сервисы.

---

## Паттерн 1: Access Token (JWT)

### 💡 Суть

Использовать **токен** для передачи identity пользователя между сервисами.

### 📝 Техническое объяснение

**JWT (JSON Web Token)** содержит:
- **Header** — алгоритм подписи
- **Payload** — данные (user_id, roles, exp)
- **Signature** — подпись для проверки подлинности

Токен **подписан**, но **не зашифрован** (base64). Изменить нельзя, прочитать можно.

### 🏠 Аналогия: Пропуск в бизнес-центр

JWT — это **пропуск** с фотографией:
- На пропуске написано: Иванов, компания "Ромашка", доступ на 3 этаж
- Охрана видит информацию (payload)
- Подделать нельзя — есть голограмма (signature)
- Пропуск выдаёт ресепшен (Auth Service)
- Показываете пропуск на каждом этаже (каждому сервису)

### ✅ Когда использовать

- Аутентификация пользователей
- Передача identity между сервисами
- Stateless авторизация

### ❌ Когда НЕ использовать

- Очень чувствительные данные в payload (видно!)
- Нужен мгновенный revoke (JWT живёт до expiry)

### 🔧 Пример

```python
from jose import jwt
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════
# AUTH SERVICE: Создание токена
# ═══════════════════════════════════════════════════════════════

SECRET_KEY = "your-secret-key"  # Из env!
ALGORITHM = "HS256"

def create_access_token(user_id: str, roles: list[str]) -> str:
    """Создать JWT токен."""
    payload = {
        "sub": user_id,
        "roles": roles,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Результат:
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
# eyJzdWIiOiJ1c2VyLTEyMyIsInJvbGVzIjpbImFkbWluIl19.
# signature


# ═══════════════════════════════════════════════════════════════
# ANY SERVICE: Проверка токена
# ═══════════════════════════════════════════════════════════════

def verify_token(token: str) -> dict:
    """Проверить и декодировать JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.JWTError:
        raise AuthError("Invalid token")


# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE: Проверка на каждом запросе
# ═══════════════════════════════════════════════════════════════

from litestar import Request
from litestar.middleware import AbstractMiddleware

class JWTMiddleware(AbstractMiddleware):
    async def __call__(self, scope, receive, send):
        request = Request(scope)
        
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = verify_token(token)
                scope["user"] = payload
            except AuthError:
                pass
        
        await self.app(scope, receive, send)
```

### JWT Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JWT AUTHENTICATION FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐                  ┌──────────────┐                           │
│   │  Client  │                  │ Auth Service │                           │
│   └────┬─────┘                  └──────┬───────┘                           │
│        │                               │                                    │
│        │  1. POST /login               │                                    │
│        │     {email, password}         │                                    │
│        │ ─────────────────────────────►│                                    │
│        │                               │ Validate credentials               │
│        │                               │ Create JWT                         │
│        │  2. {access_token: "eyJ..."}  │                                    │
│        │ ◄─────────────────────────────│                                    │
│        │                               │                                    │
│        │                                                                    │
│        │                  ┌──────────────┐                                 │
│        │                  │ Order Service│                                 │
│        │                  └──────┬───────┘                                 │
│        │                         │                                          │
│        │  3. GET /orders         │                                          │
│        │     Authorization:      │                                          │
│        │     Bearer eyJ...       │                                          │
│        │ ────────────────────────►│                                          │
│        │                         │ Verify JWT signature                     │
│        │                         │ Check expiration                         │
│        │                         │ Extract user_id, roles                   │
│        │  4. [orders...]         │                                          │
│        │ ◄────────────────────────│                                          │
│        │                         │                                          │
│                                                                             │
│   JWT передаётся с каждым запросом                                         │
│   Каждый сервис верифицирует самостоятельно (stateless)                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 2: API Key Authentication

### 💡 Суть

Использовать **уникальный ключ** для идентификации клиента (приложения, партнёра).

### 📝 Техническое объяснение

API Key:
- Длинная случайная строка
- Привязан к клиенту/приложению (не к пользователю)
- Передаётся в header или query param
- Проверяется на каждом запросе

### 🏠 Аналогия: Ключ от подъезда

API Key — это **ключ от домофона**:
- Выдаётся жильцу (клиенту)
- Открывает дверь (даёт доступ к API)
- Не содержит информации о жильце (просто ключ)
- Можно заменить если потерял

### ✅ Когда использовать

- Machine-to-machine коммуникация
- Партнёрские интеграции
- Rate limiting по клиентам

### ❌ Когда НЕ использовать

- Аутентификация пользователей (нет identity)
- Публичные API без ограничений

### 🔧 Пример

```python
import secrets
from hashlib import sha256

# ═══════════════════════════════════════════════════════════════
# ГЕНЕРАЦИЯ API KEY
# ═══════════════════════════════════════════════════════════════

def generate_api_key() -> tuple[str, str]:
    """Сгенерировать API key и его hash."""
    # Показываем клиенту только один раз!
    raw_key = f"hp_{secrets.token_urlsafe(32)}"
    # Храним hash в БД
    key_hash = sha256(raw_key.encode()).hexdigest()
    return raw_key, key_hash

# raw_key: hp_Abc123... → отдаём клиенту
# key_hash: 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069
#           → храним в БД


# ═══════════════════════════════════════════════════════════════
# ПРОВЕРКА API KEY
# ═══════════════════════════════════════════════════════════════

async def verify_api_key(api_key: str) -> Client | None:
    """Проверить API key и вернуть клиента."""
    key_hash = sha256(api_key.encode()).hexdigest()
    
    client = await db.fetch_one(
        "SELECT * FROM api_clients WHERE key_hash = $1 AND is_active = true",
        key_hash,
    )
    
    return client


# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

class APIKeyMiddleware(AbstractMiddleware):
    async def __call__(self, scope, receive, send):
        request = Request(scope)
        
        api_key = request.headers.get("X-API-Key")
        if api_key:
            client = await verify_api_key(api_key)
            if client:
                scope["client"] = client
        
        await self.app(scope, receive, send)
```

---

## Паттерн 3: Service-to-Service Authentication (mTLS)

### 💡 Суть

**Взаимная TLS аутентификация** между сервисами.

### 📝 Техническое объяснение

**mTLS (mutual TLS)**:
- Клиент проверяет сертификат сервера (обычный TLS)
- Сервер проверяет сертификат клиента (mutual)
- Оба знают, с кем общаются

### 🏠 Аналогия: Проверка документов на границе

Обычный TLS: вы проверяете паспорт пограничника (сервера).
mTLS: пограничник тоже проверяет ваш паспорт (клиент).

Оба уверены в identity друг друга.

### ✅ Когда использовать

- Internal service-to-service
- Zero-trust сети
- Compliance requirements

### 🔧 Service Mesh (Istio/Linkerd)

```yaml
# Istio автоматически добавляет mTLS между сервисами

apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # Только mTLS трафик

---
# Теперь все сервисы в namespace "production"
# общаются только через mTLS
# Sidecar proxy (Envoy) делает это автоматически
```

---

## Паттерн 4: Secrets Management

### 💡 Суть

**Централизованное хранение** секретов (пароли, ключи) с контролем доступа.

### 📝 Техническое объяснение

Проблема: секреты в коде/env файлах → утечки.

Решение:
- Хранить в **Vault** (HashiCorp) или **AWS Secrets Manager**
- Сервис запрашивает секрет при старте
- Автоматическая ротация
- Аудит доступа

### 🏠 Аналогия: Сейф в банке

Вместо хранения денег (секретов) дома:
- Арендуете **ячейку в банке** (Vault)
- Приходите с документом (identity)
- Банк даёт доступ к вашей ячейке
- Записывает в журнал (audit log)

### 🔧 Пример (HashiCorp Vault)

```python
import hvac

# Подключение к Vault
client = hvac.Client(url="https://vault.example.com:8200")
client.auth.kubernetes.login(role="order-service")

# Получение секрета
secret = client.secrets.kv.v2.read_secret_version(
    path="database/production",
    mount_point="secret",
)

db_password = secret["data"]["data"]["password"]
# Используем для подключения к БД

# Vault также поддерживает:
# - Dynamic secrets (генерация временных credentials)
# - Auto-rotation
# - Audit logging
```

---

## Принципы Zero Trust

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ZERO TRUST PRINCIPLES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Традиционный подход:           Zero Trust:                               │
│   "Доверяй внутренней сети"      "Не доверяй никому"                       │
│                                                                             │
│   ┌─────────────────────┐        ┌─────────────────────┐                   │
│   │     Firewall        │        │   Каждый запрос     │                   │
│   │  ┌───────────────┐  │        │   проверяется       │                   │
│   │  │  Внутри =     │  │        │                     │                   │
│   │  │  доверенная   │  │        │   ┌───┐ mTLS ┌───┐  │                   │
│   │  │  зона         │  │        │   │ A │◄────►│ B │  │                   │
│   │  └───────────────┘  │        │   └───┘      └───┘  │                   │
│   └─────────────────────┘        │     │          │    │                   │
│                                  │     │JWT       │JWT │                   │
│   Проблема:                      │     ▼          ▼    │                   │
│   Если атакующий внутри —        │   Auth verified     │                   │
│   полный доступ!                 │                     │                   │
│                                  └─────────────────────┘                   │
│                                                                             │
│   Принципы Zero Trust:                                                      │
│   1. Verify explicitly — проверяй каждый запрос                            │
│   2. Least privilege — минимум прав                                        │
│   3. Assume breach — считай что уже взломали                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Сравнение паттернов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SECURITY PATTERNS COMPARISON                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Паттерн      │ Идентифицирует  │ Stateless │ Когда                        │
│  ─────────────│─────────────────│───────────│────────────────────────────│
│               │                 │           │                             │
│  JWT          │ Пользователя    │ Да        │ User authentication         │
│               │                 │           │                             │
│  API Key      │ Приложение/     │ Нет       │ Machine-to-machine,         │
│               │ клиента         │ (DB)      │ partners                    │
│               │                 │           │                             │
│  mTLS         │ Сервис          │ Да        │ Service-to-service,         │
│               │                 │ (PKI)     │ zero trust                  │
│               │                 │           │                             │
│  Vault        │ Сервис (для     │ Нет       │ Secrets storage,            │
│               │ получения       │           │ DB passwords, API keys      │
│               │ секретов)       │           │                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Чеклист Security

```markdown
## Security Checklist

### Authentication
- [ ] JWT для пользователей
- [ ] Short-lived access tokens (15-60 min)
- [ ] Refresh tokens для продления
- [ ] API keys для интеграций
- [ ] Secure token storage (httpOnly cookies)

### Service-to-Service
- [ ] mTLS между сервисами
- [ ] Service accounts / identities
- [ ] Network policies (k8s)

### Secrets
- [ ] Vault или Secrets Manager
- [ ] Никаких секретов в коде
- [ ] Rotation policy
- [ ] Audit logging

### General
- [ ] HTTPS everywhere
- [ ] Input validation
- [ ] Rate limiting
- [ ] CORS configured
- [ ] Security headers (CSP, HSTS)
- [ ] Regular security audits
```

---

<div align="center">

[← Resilience](./08-resilience-patterns.md) | **Security** | [Deployment →](./10-deployment-patterns.md)

</div>
