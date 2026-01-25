# 01. Cross-cutting Concerns

> **Паттерны, пронизывающие систему насквозь**

---

## Что такое Cross-cutting Concerns?

**Cross-cutting concerns** (сквозная функциональность) — это аспекты системы, которые затрагивают множество компонентов и не могут быть изолированы в одном модуле.

### 🏠 Аналогия: Электропроводка в доме

Представьте дом. В нём есть комнаты (модули): кухня, спальня, ванная. Каждая комната имеет свою функцию. Но **электричество** проходит через ВСЕ комнаты. Нельзя сказать "электричество — это часть кухни". Электропроводка — это *сквозная забота* (cross-cutting concern).

Также в софте:
- **Логирование** нужно везде
- **Конфигурация** нужна везде
- **Аутентификация** нужна везде
- **Обработка ошибок** нужна везде

---

## Паттерн 1: Externalized Configuration

### 💡 Суть

Вынести всю конфигурацию (настройки) за пределы кода приложения.

### 📝 Техническое объяснение

Приложение не должно содержать hardcoded значения для:
- URL баз данных
- API ключи
- Лимиты и таймауты
- Feature flags

Вместо этого конфигурация читается из:
- Переменных окружения (env vars)
- Файлов конфигурации (.env, .yaml)
- Централизованного хранилища (Consul, etcd, AWS Parameter Store)

### 🏠 Аналогия: Термостат в доме

Hardcoded конфигурация — это если бы температура в доме была **замурована в стену**: "всегда 22°C". Чтобы изменить, надо ломать стену (перекомпилировать код).

Externalized configuration — это **термостат на стене**. Хочешь 25°C? Просто повернул ручку (изменил env var). Дом (приложение) тот же, но поведение изменилось.

### ✅ Когда использовать

- **Всегда**. Это базовый паттерн для любого приложения.
- Особенно важен когда:
  - Несколько окружений (dev, staging, prod)
  - Разные клиенты с разными настройками
  - Нужно менять поведение без деплоя

### ❌ Когда НЕ использовать

- Для констант, которые **никогда** не меняются (π = 3.14159...)
- Для внутренней логики, которая не должна настраиваться извне

### 🔧 Пример реализации

```python
# ❌ ПЛОХО — hardcoded
class EmailService:
    def __init__(self):
        self.smtp_host = "smtp.gmail.com"  # Замуровано!
        self.smtp_port = 587
        self.api_key = "sk-xxx-secret"  # Секрет в коде!

# ✅ ХОРОШО — externalized
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Конфигурация читается из окружения."""
    
    model_config = {"env_file": ".env"}
    
    smtp_host: str = "localhost"  # Дефолт для разработки
    smtp_port: int = 587
    api_key: str  # Обязательно из env, нет дефолта
    
    db_url: str = "postgresql://localhost/mydb"
    debug: bool = False

# Использование
settings = Settings()  # Автоматически читает из ENV
email_service = EmailService(
    host=settings.smtp_host,
    port=settings.smtp_port,
)
```

```bash
# .env файл (НЕ коммитится в git!)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
API_KEY=SG.xxx-production-key
DB_URL=postgresql://user:pass@prod-db:5432/app
DEBUG=false
```

### Уровни конфигурации

```
┌─────────────────────────────────────────────────────────────────┐
│                    ИЕРАРХИЯ КОНФИГУРАЦИИ                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Приоритет ↑                                                    │
│                                                                 │
│  1. CLI аргументы          --port=8080                         │
│  2. Переменные окружения   PORT=8080                           │
│  3. .env файл              PORT=8080                           │
│  4. Конфиг файл            config.yaml: port: 8080             │
│  5. Дефолты в коде         port: int = 8000                    │
│                                                                 │
│  Приоритет ↓                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 2: Microservice Chassis

### 💡 Суть

Создать **базовый каркас** (шасси), который содержит всю сквозную функциональность, чтобы каждый новый сервис не изобретал велосипед.

### 📝 Техническое объяснение

Microservice Chassis — это библиотека или шаблон, содержащий:
- Health check endpoints
- Metrics (Prometheus)
- Distributed tracing
- Logging setup
- Configuration loading
- Error handling
- Security (auth middleware)

Каждый новый сервис **наследует** этот каркас и сразу получает всю инфраструктуру.

### 🏠 Аналогия: Шасси автомобиля

Когда завод выпускает новые модели машин, они не создают колёса, тормоза и двигатель с нуля для каждой модели. Есть **шасси** — базовая платформа, на которую ставят разные кузова.

- **Шасси** = Microservice Chassis (общий код)
- **Кузов** = Бизнес-логика конкретного сервиса

BMW 3-серии и BMW X3 могут использовать одно шасси. Сервисы UserService и OrderService используют один Chassis.

### ✅ Когда использовать

- Когда у вас **больше 2-3 сервисов**
- Когда команды создают новые сервисы регулярно
- Когда хотите единообразие в мониторинге и логировании

### ❌ Когда НЕ использовать

- Один монолит — избыточно
- Сервисы на разных языках — нужны разные chassis

### 🔧 Пример реализации

```
# Структура Chassis (Ship Layer в Hyper-Porto)

ship/
├── core/
│   ├── errors.py          # Базовые ошибки
│   ├── protocols.py       # Интерфейсы
│   └── base_schema.py     # Базовые DTO
│
├── infrastructure/
│   ├── health_check.py    # /health endpoints
│   ├── telemetry/
│   │   ├── logfire.py     # Distributed tracing
│   │   └── metrics.py     # Prometheus metrics
│   ├── cache/
│   │   └── cashews.py     # Redis cache
│   └── events/
│       └── bus.py         # Event bus
│
├── middleware/
│   ├── auth.py            # JWT validation
│   ├── errors.py          # Error handling
│   └── idempotency.py     # Idempotency keys
│
├── decorators/
│   ├── audited.py         # Audit logging
│   └── result_handler.py  # Result → Response
│
└── parents/
    ├── action.py          # Base Action class
    ├── task.py            # Base Task class
    ├── query.py           # Base Query class
    ├── repository.py      # Base Repository
    └── unit_of_work.py    # Base UoW
```

```python
# Каждый сервис наследует от Chassis

from ship.parents import Action
from ship.infrastructure import health_controller
from ship.middleware import AuthMiddleware

# Бизнес-логика сервиса
class CreateOrderAction(Action[CreateOrderRequest, Order, OrderError]):
    """Наследует всё от Action:
    - Типизацию Result[T, E]
    - Интеграцию с tracing
    - Паттерн выполнения
    """
    
    async def run(self, data: CreateOrderRequest) -> Result[Order, OrderError]:
        # Только бизнес-логика!
        ...

# App.py сервиса
app = Litestar(
    route_handlers=[
        health_controller,  # Из chassis
        order_router,       # Бизнес-роуты
    ],
    middleware=[
        AuthMiddleware,     # Из chassis
    ],
)
```

### Chassis vs Framework

| Аспект | Framework | Chassis |
|--------|-----------|---------|
| Владение | Внешняя компания | Ваша команда |
| Кастомизация | Ограничена | Полная |
| Обновления | Внешние | Контролируемые |
| Примеры | Django, Rails | Ship Layer, Spring Boot Starter |

---

## Паттерн 3: Service Template

### 💡 Суть

**Шаблонный репозиторий** для быстрого создания новых сервисов с правильной структурой.

### 📝 Техническое объяснение

Service Template — это git repository template или cookiecutter/copier шаблон, содержащий:
- Структуру папок
- Базовые файлы (Dockerfile, docker-compose, CI/CD)
- Пустые заглушки для бизнес-логики
- Подключённый Chassis

### 🏠 Аналогия: Типовой проект дома

При строительстве коттеджного посёлка не проектируют каждый дом с нуля. Есть **типовой проект**: фундамент, несущие стены, крыша. Покупатель выбирает отделку и планировку внутри.

Service Template = Типовой проект дома
- Фундамент = Chassis
- Несущие стены = Структура папок, CI/CD
- Отделка = Бизнес-логика

### ✅ Когда использовать

- При активном создании новых сервисов (более 1 в месяц)
- Когда хотите единый стиль и структуру
- Для быстрого onboarding новых разработчиков

### 🔧 Пример: Porto CLI Generator

```bash
# Hyper-Porto использует CLI генератор вместо шаблона

# Создать новый модуль
uv run porto make:module Payment

# Результат:
src/Containers/AppSection/PaymentModule/
├── __init__.py
├── Actions/
│   └── __init__.py
├── Tasks/
│   └── __init__.py
├── Queries/
│   └── __init__.py
├── Data/
│   ├── Repositories/
│   ├── Schemas/
│   └── UnitOfWork.py
├── Models/
│   └── PiccoloApp.py
├── UI/
│   └── API/
├── Events.py
├── Errors.py
└── Providers.py

# Всё уже подключено и готово к разработке!
```

---

## Сравнение паттернов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-CUTTING CONCERNS: СРАВНЕНИЕ                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Externalized           Microservice              Service                   │
│  Configuration          Chassis                   Template                  │
│  ──────────────         ─────────────             ────────────              │
│                                                                             │
│  ┌──────────────┐       ┌──────────────┐          ┌──────────────┐         │
│  │   .env       │       │    Ship/     │          │  Template    │         │
│  │   Config     │       │   Parents/   │          │  Repo        │         │
│  │   Server     │       │   Infra/     │          │              │         │
│  └──────────────┘       │   Middleware │          │  ├── src/    │         │
│                         └──────────────┘          │  ├── tests/  │         │
│                                                   │  ├── Docker  │         │
│                                                   │  └── CI/CD   │         │
│                                                   └──────────────┘         │
│                                                                             │
│  Решает:                Решает:                   Решает:                   │
│  "Как настроить?"       "Как не дублировать      "Как быстро               │
│                          инфраструктуру?"         создать сервис?"         │
│                                                                             │
│  Зависимости:           Зависимости:              Зависимости:              │
│  Независим              Ext. Config               Ext. Config + Chassis     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Чеклист внедрения

```markdown
## Cross-cutting Concerns Checklist

### Externalized Configuration
- [ ] Все секреты в ENV, не в коде
- [ ] .env файл в .gitignore
- [ ] Есть .env.example с дефолтами
- [ ] Pydantic Settings или аналог
- [ ] Разные конфиги для dev/staging/prod

### Microservice Chassis
- [ ] Единая библиотека/слой для инфраструктуры
- [ ] Health check endpoints
- [ ] Structured logging
- [ ] Error handling
- [ ] Auth middleware
- [ ] Базовые классы для бизнес-логики

### Service Template
- [ ] Шаблон репозитория или CLI генератор
- [ ] Dockerfile и docker-compose
- [ ] CI/CD пайплайн
- [ ] Структура папок
- [ ] README с инструкциями
```

---

## Связь с другими паттернами

```
Externalized Configuration
         │
         ├──────► Microservice Chassis (использует конфиг)
         │                │
         │                ├──────► Service Template (включает chassis)
         │                │
         │                └──────► Health Check API (часть chassis)
         │
         └──────► API Gateway (читает routing из конфига)
```

---

<div align="center">

[← Обзор](./00-overview.md) | **Cross-cutting Concerns** | [Decomposition →](./02-decomposition-patterns.md)

</div>
