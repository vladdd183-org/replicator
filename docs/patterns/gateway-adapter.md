# Паттерн: Gateway и Adapter

> Gateway = межмодульная синхронная связь через Protocol. Adapter = подменяемая реализация транспорта через DI.

---

## Gateway Pattern (межмодульная связь)

Когда Container A нужны данные из Container B **синхронно**, используется Gateway:

```python
# В Container A определяется Protocol (контракт)
class PaymentGateway(Protocol):
    async def get_balance(self, user_id: UUID) -> Decimal: ...
    async def charge(self, user_id: UUID, amount: Decimal) -> str: ...

# Реализация -- Direct (монолит)
class DirectPaymentGateway(PaymentGateway):
    def __init__(self, query: GetBalanceQuery) -> None:
        self.query = query

    async def get_balance(self, user_id: UUID) -> Decimal:
        return await self.query.execute(GetBalanceInput(user_id=user_id))

# Реализация -- HTTP (микросервис)
class HTTPPaymentGateway(PaymentGateway):
    def __init__(self, base_url: str, http_client: AsyncClient) -> None:
        self.base_url = base_url
        self.http_client = http_client

    async def get_balance(self, user_id: UUID) -> Decimal:
        resp = await self.http_client.get(f"{self.base_url}/balance/{user_id}")
        return Decimal(resp.json()["balance"])
```

**Переключение монолит -> микросервис:**

```python
# Монолит
class OrderProvider(Provider):
    gateway = provide(DirectPaymentGateway, provides=PaymentGateway)

# Микросервис
class OrderProvider(Provider):
    gateway = provide(HTTPPaymentGateway, provides=PaymentGateway)
```

Бизнес-логика (Action) не меняется. Она зависит от `PaymentGateway` Protocol.

---

## Adapter Pattern (транспортный слой)

Адаптеры абстрагируют внешнюю инфраструктуру:

```
Action -> Protocol -> Adapter -> Внешняя система
```

| Слой | Пример |
|---|---|
| Action | `SaveArtifactAction` -- бизнес-логика |
| Protocol | `StoragePort` -- интерфейс хранения |
| Adapter | `LocalStorageAdapter` -- реализация для файловой системы |
| Внешняя система | `/data/artifacts/` -- конкретная директория |

---

## Adapter vs Gateway

| Аспект | Gateway | Adapter |
|---|---|---|
| Что абстрагирует | Другой Container | Внешнюю инфраструктуру |
| Где определяется Protocol | В Container-потребителе | В Ship/Adapters/ |
| Кто реализует | Container-поставщик или HTTP stub | Ship/Adapters/{Type}/ |
| Когда меняется | Монолит -> микросервис | Web2 -> Web3 |
| Scope | Бизнес-домен | Технический |

---

## Паттерн Replica Data (репликация данных по событиям)

Когда Gateway вызовы слишком частые, используется репликация:

```
Container B публикует событие UserCreated
    -> Container A слушает и сохраняет локальную копию
    -> Container A читает из локальной копии (без Gateway)
```

Это eventual consistency. Подходит для данных, которые читаются часто, меняются редко.

---

## Для Replicator

Gateway и Adapter -- два ключевых инструмента адаптерной нейтральности:

- **Gateway** позволяет Container-ам общаться, не зная друг о друге напрямую
- **Adapter** позволяет всей системе работать на разных транспортах (Web2/Web3)
- **Оба** переключаются через DI без изменения бизнес-логики
