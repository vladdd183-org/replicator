# 📋 Specs — Спецификации фич

Эта папка содержит спецификации для разрабатываемых фич.

## Структура

```
agent-os/specs/
├── README.md                           # Этот файл
├── YYYY-MM-DD-feature-name/            # Папка спецификации
│   ├── planning/
│   │   ├── requirements.md             # Собранные требования
│   │   ├── research.md                 # Результаты ресерча
│   │   └── visuals/                    # Макеты, скриншоты
│   ├── implementation/                 # Отчёты реализации
│   ├── verifications/
│   │   └── final-verification.md       # Итоговая верификация
│   ├── spec.md                         # Формальная спецификация
│   ├── tasks.md                        # Список задач
│   └── orchestration.yml               # Настройки оркестрации (опц.)
│
├── 2026-01-18-user-management/         # Пример
├── 2026-01-20-order-processing/
└── ...
```

## Workflow создания спецификации

```
1. agent-os/plan-product     → Планирование продукта (один раз)
2. agent-os/shape-spec       → Сбор требований, создание папки
3. agent-os/research         → Ресерч (опционально)
4. agent-os/write-spec       → Написание spec.md
5. agent-os/create-tasks     → Создание tasks.md
6. agent-os/implement-tasks  → Реализация
```

## Команды

| Команда | Описание |
|---------|----------|
| `agent-os/shape-spec` | Создать папку и собрать требования |
| `agent-os/write-spec` | Написать спецификацию |
| `agent-os/create-tasks` | Создать список задач |
| `agent-os/implement-tasks` | Реализовать задачи |
| `agent-os/orchestrate-tasks` | Реализация с subagents |
| `agent-os/research` | Комплексный ресерч |
| `agent-os/research-codebase` | Ресерч в коде проекта |
| `agent-os/research-online` | Ресерч онлайн |

## Именование папок

Формат: `YYYY-MM-DD-kebab-case-name`

Примеры:
- `2026-01-18-user-management`
- `2026-01-20-payment-integration`
- `2026-01-25-notification-system`

## Связь с Containers

После реализации спецификации, код создаётся в:

```
src/Containers/
├── AppSection/
│   └── [ModuleName]/        # Основные бизнес-модули
└── VendorSection/
    └── [ModuleName]/        # Внешние интеграции
```

Маппинг:
- User Story → Action
- Acceptance Criteria → Tests
- Data Model → Models + Repository
- API Contract → Controller + Schemas



