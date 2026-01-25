# 04. Communication Patterns

> **Как сервисы общаются друг с другом**

---

## Проблема коммуникации

В монолите вызов функции — это просто вызов в памяти. Наносекунды, гарантированный результат.

В микросервисах:
- Вызов идёт по сети (миллисекунды)
- Сеть ненадёжна
- Сервис может быть недоступен
- Нужны протоколы и форматы

Communication Patterns решают: **как**, **когда** и **чем** общаться.

---

## Два стиля коммуникации

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    СИНХРОННЫЙ vs АСИНХРОННЫЙ                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  СИНХРОННЫЙ (Request/Response)       АСИНХРОННЫЙ (Event-driven)            │
│  ─────────────────────────────       ───────────────────────────           │
│                                                                             │
│  Client ──► Service ──► Response     Producer ──► Broker ──► Consumer      │
│         ◄──────────────┘                                                    │
│                                                                             │
│  • Клиент ЖДЁТ ответа               • Клиент НЕ ждёт                       │
│  • Простая модель                   • Fire-and-forget                       │
│  • Coupling выше                    • Loose coupling                        │
│  • Нужен timeout                    • Eventual consistency                  │
│                                                                             │
│  Когда:                             Когда:                                  │
│  • Нужен ответ СЕЙЧАС               • Уведомления                          │
│  • Валидация                        • Длительные операции                   │
│  • Чтение данных                    • Интеграция между сервисами           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 1: Remote Procedure Invocation (RPI)

### 💡 Суть

Вызвать метод удалённого сервиса как локальную функцию. Синхронно, с ожиданием ответа.

### 📝 Техническое объяснение

RPI включает:
- **REST** (HTTP + JSON)
- **gRPC** (HTTP/2 + Protocol Buffers)
- **GraphQL** (HTTP + запрос/ответ)

Клиент делает запрос → ждёт → получает ответ.

### 🏠 Аналогия: Телефонный звонок

Вы звоните в банк:
1. Набрали номер (request)
2. Ждёте ответа оператора
3. Задали вопрос
4. Получили ответ (response)
5. Положили трубку

Это **синхронная** коммуникация. Вы не можете заниматься другими делами, пока ждёте.

### ✅ Когда использовать

- Нужен **немедленный ответ**
- **Чтение данных** (GET запросы)
- **Валидация** перед операцией
- Простые операции с низкой задержкой

### ❌ Когда НЕ использовать

- Длительные операции (> 30 секунд)
- Fire-and-forget уведомления
- Цепочка вызовов через много сервисов

### 🔧 Сравнение REST vs gRPC

| Аспект | REST | gRPC |
|--------|------|------|
| Протокол | HTTP/1.1 | HTTP/2 |
| Формат | JSON (текст) | Protocol Buffers (бинарный) |
| Размер | Больше | Меньше (в 5-10 раз) |
| Скорость | Медленнее | Быстрее |
| Типизация | Опционально (OpenAPI) | Строгая (.proto) |
| Browser support | Да | Ограничено (grpc-web) |
| Когда | Public API, простота | Internal, производительность |

### 🔧 Пример: REST

```python
# ═══════════════════════════════════════════════════════════════
# SERVER: UserService
# ═══════════════════════════════════════════════════════════════

@get("/users/{user_id}")
async def get_user(user_id: UUID) -> UserResponse:
    user = await user_repository.get(user_id)
    if not user:
        raise NotFoundException()
    return UserResponse.from_entity(user)


# ═══════════════════════════════════════════════════════════════
# CLIENT: OrderService вызывает UserService
# ═══════════════════════════════════════════════════════════════

import httpx

class UserServiceClient:
    """HTTP клиент для UserService."""
    
    def __init__(self, base_url: str = "http://user-service:8000"):
        self.base_url = base_url
    
    async def get_user(self, user_id: UUID) -> UserInfo | None:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.base_url}/users/{user_id}")
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return UserInfo(**response.json())
```

### 🔧 Пример: gRPC

```protobuf
// user_service.proto
syntax = "proto3";

service UserService {
    rpc GetUser (GetUserRequest) returns (UserResponse);
    rpc ListUsers (ListUsersRequest) returns (stream UserResponse);
}

message GetUserRequest {
    string user_id = 1;
}

message UserResponse {
    string id = 1;
    string email = 2;
    string name = 3;
}
```

```python
# gRPC клиент (сгенерирован из .proto)
async def get_user(user_id: str) -> UserResponse:
    async with grpc.aio.insecure_channel("user-service:50051") as channel:
        stub = UserServiceStub(channel)
        response = await stub.GetUser(GetUserRequest(user_id=user_id))
        return response
```

---

## Паттерн 2: Messaging (Асинхронные сообщения)

### 💡 Суть

Сервисы общаются через **посредника** (message broker), не дожидаясь друг друга.

### 📝 Техническое объяснение

Компоненты:
- **Producer** — отправляет сообщение
- **Broker** — хранит и доставляет сообщения
- **Consumer** — получает и обрабатывает

Паттерны:
- **Point-to-Point** — одно сообщение → один consumer
- **Pub/Sub** — одно сообщение → много consumers

### 🏠 Аналогия: Почтовый ящик

Вместо звонка (RPI) вы отправляете письмо:
1. Написали письмо (создали сообщение)
2. Бросили в почтовый ящик (отправили в broker)
3. Пошли заниматься другими делами (не ждёте)
4. Почтальон доставит получателю

Преимущества:
- Не ждёте ответа
- Почтальон доставит даже если получатель был занят
- Можно отправить одно письмо нескольким (Pub/Sub)

### ✅ Когда использовать

- **Fire-and-forget** операции
- **Уведомления** между сервисами
- **Длительные операции** (background tasks)
- **Интеграция** со внешними системами
- **Буферизация** при пиковой нагрузке

### ❌ Когда НЕ использовать

- Нужен **немедленный ответ**
- Простые read-запросы
- Синхронная валидация

### 🔧 Пример

```python
# ═══════════════════════════════════════════════════════════════
# PRODUCER: UserService публикует событие
# ═══════════════════════════════════════════════════════════════

class CreateUserAction(Action):
    async def run(self, data: CreateUserRequest) -> Result[User, UserError]:
        async with self.uow:
            user = User(email=data.email, name=data.name)
            await self.uow.users.add(user)
            
            # Публикуем событие — НЕ ЖДЁМ обработки
            self.uow.add_event(UserCreated(
                user_id=str(user.id),
                email=user.email,
            ))
            
            await self.uow.commit()
        
        return Success(user)  # Возвращаемся сразу


# ═══════════════════════════════════════════════════════════════
# CONSUMER: EmailService подписан на событие
# ═══════════════════════════════════════════════════════════════

@subscribe("UserCreated")
async def send_welcome_email(user_id: str, email: str, **kwargs):
    """Отправка email — асинхронно, не блокирует регистрацию."""
    await email_service.send(
        to=email,
        template="welcome",
        context={"user_id": user_id},
    )


# ═══════════════════════════════════════════════════════════════
# CONSUMER: SearchService подписан на то же событие
# ═══════════════════════════════════════════════════════════════

@subscribe("UserCreated")
async def index_user(user_id: str, email: str, name: str, **kwargs):
    """Индексация — асинхронно."""
    await search_index.add(
        entity_type="user",
        entity_id=user_id,
        content=f"{name} ({email})",
    )
```

### Брокеры сообщений

| Брокер | Тип | Когда использовать |
|--------|-----|-------------------|
| **Redis Streams** | Log-based | Простой старт, уже есть Redis |
| **RabbitMQ** | Queue-based | Сложный routing, DLQ |
| **Apache Kafka** | Log-based | Big Data, Event Sourcing |
| **AWS SQS/SNS** | Managed | Serverless, AWS |

---

## Паттерн 3: Event-driven Architecture

### 💡 Суть

Строить систему вокруг **событий**: что-то произошло → кто-то реагирует.

### 📝 Техническое объяснение

В event-driven:
- Сервисы не вызывают друг друга напрямую
- Сервисы **публикуют события** о том, что произошло
- Заинтересованные сервисы **подписываются** и реагируют

### 🏠 Аналогия: Новостная лента

Вместо того чтобы звонить каждому другу и рассказывать новости:
1. Вы публикуете пост в соцсети (событие)
2. Все подписчики видят его в ленте
3. Кто хочет — реагирует (лайк, комментарий)

Преимущества:
- Вы не знаете, кто подписан (loose coupling)
- Новые подписчики добавляются без изменений у вас
- Каждый реагирует в своём темпе

### ✅ Когда использовать

- Много **независимых реакций** на одно событие
- Нужен **loose coupling** между сервисами
- Интеграция со сторонними системами
- **Eventual consistency** приемлема

### ❌ Когда НЕ использовать

- Нужен **синхронный ответ**
- Простая система с 2-3 сервисами
- Сложность eventual consistency неприемлема

### 🔧 Пример: Событийная архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EVENT-DRIVEN ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────┐                                                         │
│   │  UserService  │                                                         │
│   │               │                                                         │
│   │  user.create()├──────► UserCreated ────────────┐                       │
│   │               │              │                  │                       │
│   └───────────────┘              │                  │                       │
│                                  │                  │                       │
│                                  ▼                  ▼                       │
│                           ┌──────────────────────────────────┐             │
│                           │         Event Bus / Broker        │             │
│                           └──────────────────────────────────┘             │
│                                  │         │         │                      │
│                    ┌─────────────┘         │         └─────────────┐       │
│                    │                       │                       │        │
│                    ▼                       ▼                       ▼        │
│            ┌───────────────┐      ┌───────────────┐      ┌───────────────┐ │
│            │ EmailService  │      │ SearchService │      │ AuditService  │ │
│            │               │      │               │      │               │ │
│            │ send_welcome  │      │ index_user    │      │ log_action    │ │
│            └───────────────┘      └───────────────┘      └───────────────┘ │
│                                                                             │
│   UserService НЕ ЗНАЕТ о подписчиках!                                      │
│   Добавить нового подписчика = добавить handler, не трогая UserService     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Типы событий

| Тип | Данные | Когда |
|-----|--------|-------|
| **Event Notification** | Минимум (entity_id) | Уведомить, что что-то произошло |
| **Event-Carried State Transfer** | Полные данные | Consumer не вызывает API для данных |
| **Domain Event** | Бизнес-данные | DDD, бизнес-смысл |

```python
# Event Notification — минимум данных
class UserCreated(DomainEvent):
    user_id: UUID  # Только ID, за данными — к UserService

# Event-Carried State Transfer — полные данные
class UserCreated(DomainEvent):
    user_id: UUID
    email: str
    name: str
    created_at: datetime
    # Consumer имеет все данные, не нужен API call
```

---

## Паттерн 4: API Composition

### 💡 Суть

**Агрегировать данные** из нескольких сервисов в одном запросе.

### 📝 Техническое объяснение

Клиенту нужны данные из разных сервисов. Вместо N запросов:
- Один запрос к **API Composer**
- Composer параллельно запрашивает данные из сервисов
- Собирает ответ и возвращает клиенту

### 🏠 Аналогия: Турагент

Вы хотите забронировать отпуск. Можно:
1. Самому звонить в авиакомпанию
2. Потом в отель
3. Потом в прокат машин
4. Собирать всё вместе

Или обратиться к **турагенту** (API Composer):
- Говорите что нужно
- Он сам обзванивает всех
- Возвращает готовый пакет

### ✅ Когда использовать

- Клиенту нужны данные из **нескольких сервисов**
- Хотите **уменьшить количество запросов** от клиента
- Нужна **агрегация и трансформация**

### ❌ Когда НЕ использовать

- Данные из одного сервиса
- Клиент может сам сделать параллельные запросы
- Composer становится bottleneck

### 🔧 Пример

```python
# ═══════════════════════════════════════════════════════════════
# API COMPOSER: Агрегирует данные для дашборда
# ═══════════════════════════════════════════════════════════════

class DashboardComposer:
    """Собирает данные дашборда из разных сервисов."""
    
    def __init__(
        self,
        user_client: UserServiceClient,
        order_client: OrderServiceClient,
        analytics_client: AnalyticsServiceClient,
    ):
        self.user_client = user_client
        self.order_client = order_client
        self.analytics_client = analytics_client
    
    async def get_dashboard(self, user_id: UUID) -> DashboardResponse:
        # Параллельные запросы к сервисам
        async with anyio.create_task_group() as tg:
            user_task = tg.start_soon(self.user_client.get_user, user_id)
            orders_task = tg.start_soon(self.order_client.get_recent_orders, user_id)
            stats_task = tg.start_soon(self.analytics_client.get_user_stats, user_id)
        
        # Агрегация результатов
        return DashboardResponse(
            user=user_task.result,
            recent_orders=orders_task.result,
            statistics=stats_task.result,
        )


# ═══════════════════════════════════════════════════════════════
# ENDPOINT
# ═══════════════════════════════════════════════════════════════

@get("/dashboard")
async def get_dashboard(
    user_id: UUID,
    composer: FromDishka[DashboardComposer],
) -> DashboardResponse:
    return await composer.get_dashboard(user_id)
```

### Архитектура API Composition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API COMPOSITION                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐                                                              │
│   │  Client  │                                                              │
│   └────┬─────┘                                                              │
│        │                                                                    │
│        │  GET /dashboard                                                    │
│        ▼                                                                    │
│   ┌─────────────────────────────────────────────────┐                      │
│   │              API Composer / BFF                  │                      │
│   │                                                  │                      │
│   │  async with task_group:                         │                      │
│   │      user = get_user(user_id)                   │                      │
│   │      orders = get_orders(user_id)               │   Параллельно!       │
│   │      stats = get_stats(user_id)                 │                      │
│   │                                                  │                      │
│   └────┬──────────────────┬──────────────────┬─────┘                      │
│        │                  │                  │                              │
│        ▼                  ▼                  ▼                              │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐                        │
│   │  User    │      │  Order   │      │Analytics │                        │
│   │ Service  │      │ Service  │      │ Service  │                        │
│   └──────────┘      └──────────┘      └──────────┘                        │
│                                                                             │
│   Один запрос от клиента → один ответ с агрегированными данными            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Сравнение Communication Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 СРАВНЕНИЕ COMMUNICATION PATTERNS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Паттерн          │ Тип        │ Coupling │ Когда                         │
│  ─────────────────│────────────│──────────│───────────────────────────────│
│                   │            │          │                               │
│  REST API         │ Синхронный │ Средний  │ Public API, CRUD              │
│                   │            │          │                               │
│  gRPC             │ Синхронный │ Средний  │ Internal, performance         │
│                   │            │          │                               │
│  Messaging        │ Асинхронный│ Низкий   │ Events, notifications         │
│                   │            │          │                               │
│  Event-driven     │ Асинхронный│ Очень    │ Loose coupling,               │
│                   │            │ низкий   │ scalability                   │
│                   │            │          │                               │
│  API Composition  │ Синхронный │ Высокий  │ Aggregation,                  │
│                   │            │          │ reduce client calls           │
│                   │            │          │                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Дерево принятия решений

```
                    ┌─────────────────────────┐
                    │ Как сервисам общаться?  │
                    └───────────┬─────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ Нужен ответ   │   │ Уведомить     │   │ Агрегировать  │
    │ СЕЙЧАС?       │   │ о событии?    │   │ данные?       │
    └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │    REST /     │   │   Messaging   │   │     API       │
    │    gRPC       │   │ Event-driven  │   │  Composition  │
    └───────────────┘   └───────────────┘   └───────────────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌────────┐    ┌────────┐
│ Public │    │Internal│
│  API?  │    │  API?  │
└────┬───┘    └────┬───┘
     │             │
     ▼             ▼
┌────────┐    ┌────────┐
│  REST  │    │  gRPC  │
└────────┘    └────────┘
```

---

## Чеклист Communication

```markdown
## Communication Checklist

### REST API
- [ ] OpenAPI спецификация
- [ ] Версионирование (/api/v1/)
- [ ] Timeout на клиенте
- [ ] Retry с backoff
- [ ] Circuit breaker

### Messaging
- [ ] Idempotent consumers
- [ ] Dead Letter Queue (DLQ)
- [ ] Мониторинг очередей
- [ ] Retry policy

### Event-driven
- [ ] Версионирование событий
- [ ] Event schema registry
- [ ] Eventual consistency handling

### API Composition
- [ ] Parallel calls (не sequential)
- [ ] Partial failure handling
- [ ] Caching где возможно
```

---

<div align="center">

[← Data Patterns](./03-data-patterns.md) | **Communication** | [API Patterns →](./05-api-patterns.md)

</div>
