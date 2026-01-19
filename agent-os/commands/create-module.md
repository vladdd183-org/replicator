# 🎮 Command: /create-module

> Создание нового Container (модуля).

---

## Синтаксис

```
/create-module <ModuleName> [в <Section>] [с сущностью <Entity>]
```

## Параметры

| Параметр | Обязательный | По умолчанию | Пример |
|----------|--------------|--------------|--------|
| ModuleName | ✅ | - | `OrderModule` |
| Section | ❌ | `AppSection` | `VendorSection` |
| Entity | ❌ | Из имени модуля | `Order` |

---

## Примеры

### Базовый
```
/create-module OrderModule
```
→ Создаст `src/Containers/AppSection/OrderModule/` с сущностью `Order`

### С указанием секции
```
/create-module PaymentModule в VendorSection
```
→ Создаст `src/Containers/VendorSection/PaymentModule/`

### С другой сущностью
```
/create-module ShopModule с сущностью Product
```
→ Создаст модуль с основной сущностью `Product`

---

## Что создаётся

```
Containers/{Section}/{Module}/
├── __init__.py
├── Actions/
│   ├── __init__.py
│   ├── Create{Entity}Action.py
│   ├── Update{Entity}Action.py
│   └── Delete{Entity}Action.py
├── Tasks/
│   └── __init__.py
├── Queries/
│   ├── __init__.py
│   ├── Get{Entity}Query.py
│   └── List{Entities}Query.py
├── Data/
│   ├── Repositories/
│   │   └── {Entity}Repository.py
│   ├── Schemas/
│   │   ├── Requests.py
│   │   └── Responses.py
│   └── UnitOfWork.py
├── Models/
│   ├── PiccoloApp.py
│   ├── {Entity}.py
│   └── migrations/
├── UI/
│   └── API/
│       ├── Controllers/
│       │   └── {Entity}Controller.py
│       └── Routes.py
├── Events.py
├── Listeners.py
├── Errors.py
└── Providers.py
```

---

## Действия после создания

1. ✅ Зарегистрировать PiccoloApp в `piccolo_conf.py`
2. ✅ Создать миграцию: `piccolo migrations new {module} --auto`
3. ✅ Применить миграцию: `piccolo migrations forwards {module}`
4. ✅ Добавить providers в `get_all_providers()`
5. ✅ Добавить router в `App.py`
6. ✅ Добавить listeners в `App.py`

---

## Связанные ресурсы

- **Workflow:** `../workflows/create-module.md`
- **Checklist:** `../checklists/new-module.md`
- **Templates:** `../templates/`



