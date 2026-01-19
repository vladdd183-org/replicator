# 🧩 Snippets: Query Patterns (Piccolo ORM)

> Готовые паттерны запросов Piccolo ORM.

---

## Базовые запросы

### Get by ID
```python
user = await User.objects().where(User.id == user_id).first()
```

### Get by field
```python
user = await User.objects().where(User.email == email).first()
```

### Check exists
```python
exists = await User.exists().where(User.email == email)
```

### Count
```python
total = await User.count().where(User.is_active == True)
```

---

## Фильтрация

### Несколько условий (AND)
```python
users = await (
    User.objects()
    .where(User.is_active == True)
    .where(User.role == "admin")
)
```

### OR условие
```python
from piccolo.columns.combination import Or

users = await (
    User.objects()
    .where(
        Or(
            User.role == "admin",
            User.role == "moderator",
        )
    )
)
```

### IN условие
```python
users = await (
    User.objects()
    .where(User.id.is_in(user_ids))
)
```

### LIKE / Contains
```python
users = await (
    User.objects()
    .where(User.name.like("%John%"))
)

# Или ilike для case-insensitive
users = await (
    User.objects()
    .where(User.name.ilike("%john%"))
)
```

### NULL check
```python
users = await (
    User.objects()
    .where(User.deleted_at.is_null())
)
```

### Сравнения
```python
users = await (
    User.objects()
    .where(User.age >= 18)
    .where(User.age < 65)
    .where(User.created_at > datetime(2024, 1, 1))
)
```

---

## Пагинация и сортировка

### Limit/Offset
```python
users = await (
    User.objects()
    .limit(20)
    .offset(40)
)
```

### Order by
```python
# По одному полю
users = await (
    User.objects()
    .order_by(User.created_at, ascending=False)
)

# По нескольким полям
users = await (
    User.objects()
    .order_by(User.role)
    .order_by(User.name)
)
```

### Комбинация для пагинации
```python
users = await (
    User.objects()
    .where(User.is_active == True)
    .order_by(User.created_at, ascending=False)
    .limit(params.limit)
    .offset(params.offset)
)
```

---

## Выбор полей

### Только нужные поля
```python
users = await (
    User.select(User.id, User.name, User.email)
    .where(User.is_active == True)
)
# Возвращает list[dict], не list[User]!
```

### Исключить поля
```python
users = await (
    User.objects()
    .exclude(User.password_hash, User.secret_token)
)
```

---

## Агрегации

### Count с группировкой
```python
from piccolo.query.methods.select import Count

result = await (
    User.select(User.role, Count())
    .group_by(User.role)
)
# [{"role": "admin", "count": 5}, {"role": "user", "count": 100}]
```

### Sum, Avg, Max, Min
```python
from piccolo.query.methods.select import Sum, Avg

result = await (
    Order.select(Sum(Order.total), Avg(Order.total))
    .where(Order.user_id == user_id)
).first()
```

---

## Joins

### Foreign Key (автоматический join)
```python
# Если есть ForeignKey в модели
orders = await (
    Order.objects()
    .where(Order.user.email == "test@example.com")  # Автоматический join
)
```

### Явный join
```python
from piccolo.columns.combination import WhereRaw

orders = await (
    Order.raw("""
        SELECT orders.*, users.name as user_name
        FROM orders
        JOIN users ON orders.user_id = users.id
        WHERE users.is_active = true
    """)
)
```

---

## Raw SQL (когда нужно)

### Raw query
```python
result = await User.raw("SELECT * FROM users WHERE age > {}", 18)
```

### Raw where
```python
from piccolo.columns.combination import WhereRaw

users = await (
    User.objects()
    .where(WhereRaw("LOWER(name) = {}", "john"))
)
```

---

## Паттерны для CQRS Query

### GetEntityQuery
```python
class GetUserQuery(Query[GetUserQueryInput, User | None]):
    async def execute(self, input: GetUserQueryInput) -> User | None:
        return await (
            User.objects()
            .where(User.id == input.user_id)
            .first()
        )
```

### ListEntitiesQuery с фильтрами
```python
class ListUsersQuery(Query[ListUsersQueryInput, ListUsersQueryOutput]):
    async def execute(self, params: ListUsersQueryInput) -> ListUsersQueryOutput:
        query = User.objects()
        count_query = User.count()
        
        # Применяем фильтры
        if params.is_active is not None:
            query = query.where(User.is_active == params.is_active)
            count_query = count_query.where(User.is_active == params.is_active)
        
        if params.role:
            query = query.where(User.role == params.role)
            count_query = count_query.where(User.role == params.role)
        
        if params.search:
            query = query.where(User.name.ilike(f"%{params.search}%"))
            count_query = count_query.where(User.name.ilike(f"%{params.search}%"))
        
        # Пагинация и сортировка
        total = await count_query
        users = await (
            query
            .order_by(User.created_at, ascending=False)
            .limit(params.limit)
            .offset(params.offset)
        )
        
        return ListUsersQueryOutput(
            users=users,
            total=total,
            limit=params.limit,
            offset=params.offset,
        )
```



