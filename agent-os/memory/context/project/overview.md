# 📋 Project Overview

> Общая информация о проекте Hyper-Porto

**Последнее обновление:** 2026-01-19

---

## 🎯 О проекте

**Hyper-Porto** — функциональная архитектура для Python бэкендов, объединяющая:
- **Porto Pattern** — модульная структура Container/Ship
- **Cosmic Python** — Repository, UoW, Domain Events
- **Returns** — Result[T, E], Railway-Oriented Programming
- **anyio** — Structured Concurrency

---

## 🛠️ Tech Stack

| Категория | Технология | Версия |
|-----------|------------|--------|
| Framework | Litestar | latest |
| ORM | Piccolo | latest |
| DI | Dishka | latest |
| Validation | Pydantic v2 | latest |
| Result | returns | latest |
| Async | anyio | latest |
| GraphQL | Strawberry | latest |
| Background | TaskIQ | latest |
| Testing | pytest | latest |
| Linting | ruff | latest |
| Types | mypy (strict) | latest |

---

## 📁 Структура

```
src/
├── App.py                    # Litestar factory
├── Main.py                   # Entry point
├── Ship/                     # Общая инфраструктура
│   ├── Parents/              # Базовые классы
│   ├── Core/                 # Ядро (Errors, Schemas, Protocols)
│   ├── Infrastructure/       # Cache, Telemetry, Workers
│   └── Providers/            # DI провайдеры
└── Containers/               # Бизнес-модули
    ├── AppSection/           # Основные модули
    │   ├── UserModule/
    │   ├── AuditModule/
    │   ├── NotificationModule/
    │   ├── SearchModule/
    │   └── SettingsModule/
    └── VendorSection/        # Внешние интеграции
```

---

## 🎨 Ключевые паттерны

| Паттерн | Где используется |
|---------|------------------|
| Result[T, E] | Все Actions |
| CQRS | Actions (write) vs Queries (read) |
| Repository | Data layer |
| Unit of Work | Транзакции + Events |
| Domain Events | Межмодульное общение |

---

## 📊 Текущее состояние

| Метрика | Значение |
|---------|----------|
| Модулей | 5+ |
| Actions | ~20 |
| Tests coverage | TBD |
| Last activity | 2026-01-19 |

---

## 🔗 Ключевые файлы

- [CLAUDE.md](../../../../CLAUDE.md) — Quick Reference для AI
- [docs/](../../../../docs/) — Полная документация
- [agent-os/](../../) — AI Development Standards
