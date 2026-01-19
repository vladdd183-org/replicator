# ✅ Checklist: New Module

> Краткий чеклист создания нового Container. Детали: `workflows/create-module.md`

---

## 📁 Структура

- [ ] Создана структура папок
- [ ] `__init__.py` во всех папках
- [ ] Экспорт router в `__init__.py`

## 📊 Data Layer

- [ ] `Models/{Entity}.py` — Piccolo Table
- [ ] `Models/PiccoloApp.py` — Piccolo App config
- [ ] Зарегистрирован в `piccolo_conf.py`
- [ ] Миграция создана (`piccolo migrations new`)
- [ ] Миграция применена (`piccolo migrations forwards`)
- [ ] `Data/Repositories/{Entity}Repository.py`
- [ ] `Data/UnitOfWork.py`
- [ ] `Data/Schemas/Requests.py`
- [ ] `Data/Schemas/Responses.py`

## 🎯 Business Logic

- [ ] `Errors.py` — базовые ошибки модуля
- [ ] `Events.py` — доменные события
- [ ] `Tasks/{TaskName}Task.py` (если нужны атомарные операции)
- [ ] `Queries/Get{Entity}Query.py`
- [ ] `Queries/List{Entities}Query.py`
- [ ] `Actions/Create{Entity}Action.py`
- [ ] `Actions/Update{Entity}Action.py`
- [ ] `Actions/Delete{Entity}Action.py`

## 🌐 Presentation

- [ ] `UI/API/Controllers/{Entity}Controller.py`
- [ ] `UI/API/Routes.py`
- [ ] `Listeners.py` — event handlers

## 💉 DI & Registration

- [ ] `Providers.py` — APP + REQUEST providers
- [ ] Добавлен в `get_all_providers()`
- [ ] Router добавлен в `App.py`
- [ ] Listeners добавлены в `App.py`

## 🧪 Testing

- [ ] Unit тесты для Actions
- [ ] Integration тесты для API
- [ ] Проверена OpenAPI документация

---

## 🔗 Связанные

- **Workflow:** `../workflows/create-module.md`
- **Templates:** `../templates/`



