# 🎮 Command: /generate-crud

> Генерация полного CRUD для сущности.

---

## Синтаксис

```
/generate-crud <Entity> [в <Module>] [поля: <fields>]
```

## Параметры

| Параметр | Обязательный | Пример |
|----------|--------------|--------|
| Entity | ✅ | `Product`, `Category` |
| Module | ❌ | `ShopModule` |
| fields | ❌ | `name:str, price:float, active:bool` |

---

## Примеры

### Базовый
```
/generate-crud Product в ShopModule
```
→ Создаст полный CRUD для Product

### С полями
```
/generate-crud Product в ShopModule поля: name:str, price:Decimal, stock:int, active:bool
```

### Минимальный
```
/generate-crud Category
```
→ Спросит модуль и создаст с базовыми полями

---

## Что создаётся

### Model
```python
from datetime import datetime, timezone

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Product(Table, tablename="products"):
    id = UUID(primary_key=True, default=uuid4)
    name = Varchar(length=100)
    price = Numeric(digits=(10, 2))
    stock = Integer(default=0)
    active = Boolean(default=True)
    created_at = Timestamptz(default=_utc_now)
    updated_at = Timestamptz(null=True)
```

### Errors
```python
class ProductError(BaseError): ...
class ProductNotFoundError(ErrorWithTemplate, ProductError): ...
class ProductAlreadyExistsError(ErrorWithTemplate, ProductError): ...
```

### Events
```python
class ProductCreated(DomainEvent): ...
class ProductUpdated(DomainEvent): ...
class ProductDeleted(DomainEvent): ...
```

### Schemas
```python
# Requests
class CreateProductRequest(BaseModel): ...
class UpdateProductRequest(BaseModel): ...

# Responses
class ProductResponse(EntitySchema): ...
class ProductListResponse(BaseModel): ...
```

### Repository
```python
class ProductRepository(Repository[Product]):
    model = Product
    async def find_by_name(self, name: str) -> Product | None: ...
```

### UnitOfWork
```python
class ShopUnitOfWork(BaseUnitOfWork):
    @property
    def products(self) -> ProductRepository: ...
```

### Queries
```python
class GetProductQuery(Query[GetProductQueryInput, Product | None]): ...
class ListProductsQuery(Query[ListProductsQueryInput, ListProductsQueryOutput]): ...
```

### Actions
```python
class CreateProductAction(Action[CreateProductRequest, Product, ProductError]): ...
class UpdateProductAction(Action[UpdateProductRequest, Product, ProductError]): ...
class DeleteProductAction(Action[UUID, None, ProductError]): ...
```

### Controller
```python
class ProductController(Controller):
    path = "/products"
    
    @post("/")
    @result_handler(ProductResponse, success_status=HTTP_201_CREATED)
    async def create_product(...): ...
    
    @get("/")
    async def list_products(...): ...
    
    @get("/{product_id:uuid}")
    async def get_product(...): ...
    
    @patch("/{product_id:uuid}")
    @result_handler(ProductResponse)
    async def update_product(...): ...
    
    @delete("/{product_id:uuid}")
    @result_handler(None, success_status=HTTP_204_NO_CONTENT)
    async def delete_product(...): ...
```

### Listeners
```python
@listener("ProductCreated")
async def on_product_created(...): ...

@listener("ProductUpdated")
async def on_product_updated(...): ...

@listener("ProductDeleted")
async def on_product_deleted(...): ...
```

### Providers
```python
class ShopModuleProvider(Provider):
    scope = Scope.APP

class ShopRequestProvider(Provider):
    scope = Scope.REQUEST
    product_repository = provide(ProductRepository)
    create_product_action = provide(CreateProductAction)
    # ... все остальные
```

---

## Действия после генерации

1. ✅ Добавить PiccoloApp в `piccolo_conf.py`
2. ✅ Создать миграцию
3. ✅ Добавить providers в `get_all_providers()`
4. ✅ Добавить router в `App.py`
5. ✅ Добавить listeners в `App.py`
6. ⚠️ Проверить/настроить поля Model
7. ⚠️ Добавить бизнес-логику в Actions

---

## Связанные ресурсы

- **Command:** `/create-module`
- **Templates:** `../templates/`
- **Workflow:** `../workflows/create-module.md`



