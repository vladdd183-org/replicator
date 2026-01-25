# 11. Testing Patterns

> **Тестирование в микросервисной архитектуре**

---

## Проблема тестирования

В микросервисах тестирование сложнее:
- Много сервисов с зависимостями
- Сетевые вызовы между сервисами
- Разные базы данных
- End-to-end сценарии через всю систему

Testing Patterns помогают тестировать **эффективно и надёжно**.

---

## Пирамида тестирования

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TESTING PYRAMID                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                              /\                                              │
│                             /  \        E2E Tests                           │
│                            / E2E\       (немного, медленные)                │
│                           /──────\                                          │
│                          /        \                                         │
│                         / Integration\   Integration Tests                  │
│                        /    Tests     \  (средне)                           │
│                       /────────────────\                                    │
│                      /                  \                                   │
│                     /    Unit Tests      \  Unit Tests                      │
│                    /                      \ (много, быстрые)                │
│                   /────────────────────────\                                │
│                                                                             │
│   Больше unit tests → быстрая обратная связь                               │
│   Меньше E2E → меньше flaky, быстрее CI                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 1: Service Component Test

### 💡 Суть

Тестировать **сервис целиком** в изоляции, заменяя внешние зависимости моками.

### 📝 Техническое объяснение

- Поднимаем сервис
- Мокаем внешние сервисы (WireMock, responses)
- Используем реальную БД (testcontainers)
- Вызываем API сервиса
- Проверяем ответы и side effects

### 🏠 Аналогия: Краш-тест автомобиля

При краш-тесте:
- Тестируют **один автомобиль** целиком
- Используют **манекен** (mock пассажира)
- Стена — **контролируемый удар** (mock внешней системы)
- Проверяют, как автомобиль **в целом** справляется

Не тестируют на реальной дороге с другими машинами (E2E) — слишком сложно.

### ✅ Когда использовать

- Проверка сервиса в сборе
- Проверка HTTP API
- Тестирование с реальной БД
- Быстрее чем E2E, надёжнее чем unit

### 🔧 Пример (pytest + httpx + testcontainers)

```python
import pytest
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer

from src.App import create_app

@pytest.fixture(scope="session")
def postgres():
    """Реальный PostgreSQL в контейнере."""
    with PostgresContainer("postgres:15") as pg:
        yield pg

@pytest.fixture
async def app(postgres):
    """Приложение с реальной БД."""
    app = create_app(database_url=postgres.get_connection_url())
    yield app

@pytest.fixture
async def client(app):
    """HTTP клиент для тестирования API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ═══════════════════════════════════════════════════════════════
# COMPONENT TESTS
# ═══════════════════════════════════════════════════════════════

class TestUserService:
    """Component tests для UserService."""
    
    async def test_create_user_success(self, client):
        """Создание пользователя через API."""
        response = await client.post(
            "/api/v1/users",
            json={"email": "test@example.com", "name": "Test User", "password": "secret123"},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "password" not in data  # Не возвращаем пароль
    
    async def test_create_user_duplicate_email(self, client):
        """Дубликат email возвращает 409."""
        # Создаём первого
        await client.post(
            "/api/v1/users",
            json={"email": "duplicate@example.com", "name": "User 1", "password": "secret"},
        )
        
        # Пробуем создать с тем же email
        response = await client.post(
            "/api/v1/users",
            json={"email": "duplicate@example.com", "name": "User 2", "password": "secret"},
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    async def test_get_user_not_found(self, client):
        """Несуществующий пользователь возвращает 404."""
        response = await client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
```

### Мокирование внешних сервисов

```python
import respx
from httpx import Response

@pytest.fixture
def mock_payment_service():
    """Мок Payment Service."""
    with respx.mock:
        # Успешный платёж
        respx.post("http://payment-service/charge").mock(
            return_value=Response(200, json={"payment_id": "pay-123", "status": "success"})
        )
        
        yield respx


async def test_create_order_with_payment(client, mock_payment_service):
    """Создание заказа с платежом (Payment замокан)."""
    response = await client.post(
        "/api/v1/orders",
        json={"user_id": "user-123", "items": [{"product_id": "prod-1", "qty": 2}]},
    )
    
    assert response.status_code == 201
    # Проверяем что Payment Service был вызван
    assert mock_payment_service.calls.call_count == 1
```

---

## Паттерн 2: Service Integration Contract Test

### 💡 Суть

Тестировать **контракт между сервисами** — формат запросов и ответов.

### 📝 Техническое объяснение

**Consumer-Driven Contract Testing:**
1. **Consumer** (клиент) определяет ожидаемый контракт
2. Контракт публикуется в **Pact Broker**
3. **Provider** (сервер) тестируется против контракта
4. Если Provider сломал контракт — тест падает

### 🏠 Аналогия: Договор между компаниями

Consumer (OrderService) и Provider (UserService) подписывают **договор**:
- "Я буду запрашивать GET /users/{id}"
- "Ты вернёшь JSON с полями: id, email, name"

Если Provider изменит ответ (убрал поле email) — нарушение договора!

### ✅ Когда использовать

- Много потребителей одного API
- Независимые команды
- Частые изменения API
- Хотите избежать E2E

### 🔧 Пример (Pact)

```python
# ═══════════════════════════════════════════════════════════════
# CONSUMER SIDE (Order Service)
# ═══════════════════════════════════════════════════════════════

from pact import Consumer, Provider

pact = Consumer("OrderService").has_pact_with(
    Provider("UserService"),
    pact_dir="./pacts",
)

def test_get_user_contract():
    """Consumer contract: Order Service ожидает от User Service."""
    
    # Определяем ожидаемое взаимодействие
    (pact
     .given("user 123 exists")
     .upon_receiving("a request for user 123")
     .with_request("GET", "/users/123")
     .will_respond_with(200, body={
         "id": "123",
         "email": Regex(r".+@.+", "user@example.com"),
         "name": Like("John Doe"),
     }))
    
    with pact:
        # Вызываем код, который обращается к User Service
        user = user_client.get_user("123")
        assert user.email == "user@example.com"
    
    # Pact записывает контракт в ./pacts/orderservice-userservice.json


# ═══════════════════════════════════════════════════════════════
# PROVIDER SIDE (User Service)
# ═══════════════════════════════════════════════════════════════

from pact import Verifier

def test_provider_against_contracts():
    """Provider verification: User Service соответствует контрактам."""
    
    verifier = Verifier(
        provider="UserService",
        provider_base_url="http://localhost:8000",
    )
    
    # Проверяем все контракты из Pact Broker
    success, logs = verifier.verify_with_broker(
        broker_url="https://pact-broker.example.com",
        publish_verification_results=True,
    )
    
    assert success
```

### Contract Testing Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CONTRACT TESTING FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐                        ┌──────────────────┐         │
│   │  Order Service   │                        │  User Service    │         │
│   │   (Consumer)     │                        │   (Provider)     │         │
│   └────────┬─────────┘                        └────────┬─────────┘         │
│            │                                           │                    │
│   1. Consumer Test                            3. Provider Verification      │
│      ─────────────                               ────────────────────       │
│      Определяет ожидания                         Тестируется против         │
│      (что хочу получить)                         контракта                  │
│            │                                           │                    │
│            ▼                                           │                    │
│   ┌──────────────────┐                                │                    │
│   │   Pact File      │                                │                    │
│   │  (contract.json) │                                │                    │
│   └────────┬─────────┘                                │                    │
│            │                                           │                    │
│   2. Publish                                           │                    │
│      ───────                                           │                    │
│            │                                           │                    │
│            ▼                                           │                    │
│   ┌──────────────────┐                                │                    │
│   │   Pact Broker    │ ◄──────────────────────────────┘                    │
│   │                  │                                                      │
│   │  Хранит контракты│                                                      │
│   │  Версионирование │                                                      │
│   │  Webhook → CI    │                                                      │
│   └──────────────────┘                                                      │
│                                                                             │
│   Если Provider изменит API несовместимо → CI падает!                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 3: End-to-End Test

### 💡 Суть

Тестировать **весь путь** запроса через всю систему.

### 📝 Техническое объяснение

- Поднимаем все сервисы
- Реальные БД, брокеры
- Тестируем бизнес-сценарии целиком
- Самые медленные и нестабильные тесты

### 🏠 Аналогия: Тест-драйв автомобиля

E2E — это **реальный тест-драйв**:
- Настоящая дорога (prod-like environment)
- Настоящий водитель (user scenarios)
- Все системы работают вместе

Дорого, долго, но даёт уверенность что всё работает.

### ✅ Когда использовать

- Критичные бизнес-сценарии
- Smoke tests после деплоя
- **Минимум тестов** (5-10 ключевых)

### ❌ Когда НЕ использовать

- Как основной способ тестирования
- Для edge cases
- Для быстрой обратной связи

### 🔧 Пример (Playwright / pytest)

```python
import pytest
from playwright.sync_api import Page

class TestOrderFlow:
    """E2E тесты основного бизнес-процесса."""
    
    def test_complete_order_flow(self, page: Page):
        """Полный цикл: регистрация → каталог → заказ → оплата."""
        
        # 1. Регистрация
        page.goto("/register")
        page.fill("[name=email]", "e2e-test@example.com")
        page.fill("[name=password]", "SecurePass123!")
        page.click("button[type=submit]")
        
        assert page.url == "/dashboard"
        
        # 2. Добавить товар в корзину
        page.goto("/products")
        page.click("[data-product-id='prod-1'] >> text=Add to cart")
        
        # 3. Оформить заказ
        page.goto("/cart")
        page.click("text=Checkout")
        page.fill("[name=address]", "123 Test Street")
        page.click("text=Place Order")
        
        # 4. Проверить успех
        assert page.locator("text=Order Confirmed").is_visible()
        
        # 5. Проверить в истории заказов
        page.goto("/orders")
        assert page.locator("text=prod-1").is_visible()
```

---

## Сравнение подходов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   TESTING PATTERNS COMPARISON                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Тип теста       │ Скорость │ Изоляция │ Уверенность │ Количество         │
│  ────────────────│──────────│──────────│─────────────│────────────────────│
│                  │          │          │             │                     │
│  Unit            │ ⚡ Очень │ Полная   │ Низкая      │ Много (70%)        │
│                  │   быстро │          │ (1 функция) │                     │
│                  │          │          │             │                     │
│  Component       │ 🚀 Быстро│ Высокая  │ Средняя     │ Средне (20%)       │
│                  │          │ (моки)   │ (1 сервис)  │                     │
│                  │          │          │             │                     │
│  Contract        │ 🚀 Быстро│ Высокая  │ Средняя     │ По API             │
│                  │          │          │ (интеграция)│                     │
│                  │          │          │             │                     │
│  E2E             │ 🐢 Медлен│ Нет      │ Высокая     │ Мало (5%)          │
│                  │   но     │          │ (вся система│                     │
│                  │          │          │             │                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Test Doubles (моки, стабы, фейки)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TEST DOUBLES                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Тип        │ Описание                     │ Пример                        │
│  ───────────│──────────────────────────────│───────────────────────────────│
│             │                              │                                │
│  Stub       │ Возвращает заранее           │ def get_user(): return User() │
│             │ заданное значение            │                                │
│             │                              │                                │
│  Mock       │ Stub + проверка вызовов      │ mock.assert_called_once()     │
│             │                              │                                │
│  Fake       │ Упрощённая реализация        │ InMemoryRepository вместо     │
│             │                              │ PostgresRepository            │
│             │                              │                                │
│  Spy        │ Обёртка над реальным         │ spy = spyOn(service.call)     │
│             │ объектом + запись вызовов    │ spy.calls.count == 1          │
│             │                              │                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Чеклист Testing

```markdown
## Testing Checklist

### Unit Tests
- [ ] Покрытие бизнес-логики (Actions, Tasks)
- [ ] Тестирование edge cases
- [ ] Fast feedback (<1 секунда на тест)

### Component Tests
- [ ] Testcontainers для БД
- [ ] Моки внешних сервисов
- [ ] Тестирование API endpoints
- [ ] Happy path + error cases

### Contract Tests
- [ ] Consumer contracts для каждого API
- [ ] Provider verification в CI
- [ ] Pact Broker для хранения
- [ ] Breaking change detection

### E2E Tests
- [ ] Только критичные сценарии
- [ ] Smoke tests после деплоя
- [ ] Retry flaky tests
- [ ] Отдельный stage в CI

### General
- [ ] CI запускает все уровни
- [ ] Быстрые тесты сначала
- [ ] Test data management
- [ ] Cleanup after tests
```

---

<div align="center">

[← Deployment](./10-deployment-patterns.md) | **Testing** | [UI Patterns →](./12-ui-patterns.md)

</div>
