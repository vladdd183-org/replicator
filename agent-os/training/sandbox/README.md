# Sandbox — Песочница для экспериментов

> Безопасное место для экспериментов с кодом Hyper-Porto

---

## Что это?

Sandbox — папка для экспериментов. Здесь можно:

- Пробовать новые идеи
- Тестировать компоненты изолированно
- Ломать и чинить без последствий

---

## Использование

### Создание компонента

```
@training sandbox создай action
@training sandbox создай task
@training sandbox создай controller
```

### Очистка

```
@training sandbox очистить
```

---

## Структура

```
sandbox/
├── README.md           # Этот файл
├── experiments/        # Твои эксперименты
└── simulation_workspace/  # Временные файлы симуляций
```

---

## Правила

1. Код здесь **не влияет** на основной проект
2. **Не коммить** sandbox в git (добавлен в .gitignore)
3. Периодически **очищай** старые эксперименты

---

## Примеры экспериментов

### Попробовать новый паттерн

```python
# sandbox/experiments/try_saga.py
from returns.result import Result, Success

class MySagaExperiment:
    async def run(self):
        # Эксперимент с Saga pattern
        pass
```

### Тестировать изолированный компонент

```python
# sandbox/experiments/test_caching.py
from cashews import cache

@cache(ttl="5m")
async def expensive_operation():
    return "cached!"
```

---

## Связанные ресурсы

- [Туториалы](../tutorials/)
- [Симуляции](../simulations/)
- [Сниппеты](../../snippets/)
