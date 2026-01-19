# /create-module — Создание модуля

Создание нового Container (бизнес-модуля).

## Источники

- Инструкция: `agent-os/commands/create-module.md`
- Workflow: `agent-os/workflows/create-module.md`
- Checklist: `agent-os/checklists/new-module.md`
- Templates: `agent-os/templates/`

## Синтаксис

```
/create-module <ModuleName> [в <Section>] [с сущностью <Entity>]
```

## Примеры

```
/create-module OrderModule
/create-module PaymentModule в VendorSection
/create-module ShopModule с сущностью Product
```

## Действие

1. Загрузи инструкцию из `agent-os/commands/create-module.md`
2. Используй templates из `agent-os/templates/`
3. Создай структуру модуля
4. Следуй checklist из `agent-os/checklists/new-module.md`

