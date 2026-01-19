# 01. Создание первого Action

> Пошаговое создание Action с нуля — основного компонента бизнес-логики

**Уровень:** Beginner  
**Время:** 30 минут  
**Темы:** Action, Result[T, E], Pydantic DTO, DI

---

## Цель

После этого туториала ты сможешь:

- Создавать Action, который возвращает `Result[T, E]`
- Использовать Pydantic для входных и выходных DTO
- Обрабатывать успех и ошибки через pattern matching
- Регистрировать Action в DI-контейнере

---

## Что такое Action?

**Action** — это Use Case в терминах Clean Architecture. Он:

- Содержит бизнес-логику одной операции
- Принимает DTO на вход, возвращает `Result[T, E]`
- Оркестрирует Tasks, Repositories, UnitOfWork
- Не знает о HTTP, GraphQL и других транспортах

```
Controller → Action → Task/Repository/UoW
```

---

## Шаг 1: Понимаем структуру

Action в Hyper-Porto имеет фиксированную структуру:

```python
from returns.result import Result, Success, Failure
from src.Ship.Parents.Action import Action

class MyAction(Action[TInput, TOutput, TError]):
    """Use Case: описание."""
    
    def __init__(
        self,
        some_task: SomeTask,
        repository: SomeRepository,
    ) -> None:
        self.some_task = some_task
        self.repository = repository
    
    async def run(self, data: TInput) -> Result[TOutput, TError]:
        # Бизнес-логика
        return Success(result)  # или Failure(error)
```

**Важно:**
- `Action[TInput, TOutput, TError]` — дженерик с тремя типами
- Метод `run()` — точка входа, всегда возвращает `Result`
- Зависимости инжектятся через `__init__` конструктор

---

## Шаг 2: Создаём DTO

Начнём с создания входного и выходного DTO.

### Создай файл: `src/Containers/AppSection/TrainingModule/Data/Schemas/Requests.py`

```python
"""Request DTO для TrainingModule."""

from pydantic import BaseModel, Field


class GreetUserRequest(BaseModel):
    """Входной DTO для приветствия пользователя."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Имя пользователя")
    language: str = Field(default="ru", pattern="^(ru|en)$", description="Язык приветствия")
```

### Создай файл: `src/Containers/AppSection/TrainingModule/Data/Schemas/Responses.py`

```python
"""Response DTO для TrainingModule."""

from src.Ship.Core.BaseSchema import EntitySchema


class GreetUserResponse(EntitySchema):
    """Выходной DTO с приветствием."""
    
    greeting: str
    name: str
    language: str
```

### Почему так?

- **Request DTO** — наследует `BaseModel`, содержит валидацию
- **Response DTO** — наследует `EntitySchema` (расширение BaseModel)
- **Field(...)** — обязательное поле с валидацией
- Разделение по файлам — `Requests.py` и `Responses.py`

## Шаг 3: Создаём ошибки

Ошибки в Hyper-Porto — это frozen Pydantic модели.

### Создай файл: `src/Containers/AppSection/TrainingModule/Errors.py`

```python
"""Ошибки TrainingModule."""

from typing import ClassVar
from src.Ship.Core.Errors import BaseError, ErrorWithTemplate


class TrainingError(BaseError):
    """Базовая ошибка модуля Training."""
    
    code: str = "TRAINING_ERROR"


class InvalidLanguageError(ErrorWithTemplate, TrainingError):
    """Неподдерживаемый язык."""
    
    _message_template: ClassVar[str] = "Language '{language}' is not supported"
    code: str = "INVALID_LANGUAGE"
    http_status: int = 400
    language: str
```

### Почему так?

- **BaseError** — базовый класс для всех ошибок (frozen Pydantic)
- **ErrorWithTemplate** — автоматически генерирует `message` из шаблона
- **http_status** — используется `@result_handler` для HTTP-ответа

---

## Шаг 4: Создаём Action

Теперь главное — сам Action.

### Создай файл: `src/Containers/AppSection/TrainingModule/Actions/GreetUserAction.py`

```python
"""Action для приветствия пользователя."""

from returns.result import Result, Success, Failure

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.TrainingModule.Data.Schemas.Requests import (
    GreetUserRequest,
)
from src.Containers.AppSection.TrainingModule.Data.Schemas.Responses import (
    GreetUserResponse,
)
from src.Containers.AppSection.TrainingModule.Errors import (
    TrainingError,
    InvalidLanguageError,
)


# Словарь приветствий
GREETINGS = {
    "ru": "Привет",
    "en": "Hello",
}


class GreetUserAction(Action[GreetUserRequest, GreetUserResponse, TrainingError]):
    """Use Case: Генерирует приветствие для пользователя.
    
    Steps:
        - Получает имя и язык
        - Возвращает локализованное приветствие
        
    Errors:
        - InvalidLanguageError: если язык не поддерживается
    """
    
    async def run(self, data: GreetUserRequest) -> Result[GreetUserResponse, TrainingError]:
        """Выполняет приветствие."""
        
        # Проверяем язык
        greeting_template = GREETINGS.get(data.language)
        
        if greeting_template is None:
            return Failure(InvalidLanguageError(language=data.language))
        
        # Формируем приветствие
        greeting = f"{greeting_template}, {data.name}!"
        
        # Возвращаем успешный результат
        return Success(
            GreetUserResponse(
                greeting=greeting,
                name=data.name,
                language=data.language,
            )
        )
```

### Разбор кода:

1. **`Action[TInput, TOutput, TError]`** — типизация с тремя типами
2. **`__init__()`** — позволяет инжектить зависимости через DI (пока их нет)
3. **`async def run()`** — основной метод
4. **`Failure(error)`** — возврат ошибки
5. **`Success(result)`** — возврат успеха

---

## Шаг 5: Проверяем себя

Убедись, что:

- [ ] Используешь **абсолютные импорты** (`from src.Containers...`)
- [ ] Action наследуется от **`Action[TInput, TOutput, TError]`**
- [ ] Метод `run()` возвращает **`Result[..., ...]`**
- [ ] DTO — **Pydantic BaseModel**
- [ ] Ошибки — **frozen Pydantic** с `http_status`

Скажи агенту:

```
@training проверь шаг 5
```

---

## Шаг 6: Регистрируем в DI

Action нужно зарегистрировать в Dishka.

### Создай файл: `src/Containers/AppSection/TrainingModule/Providers.py`

```python
"""DI провайдеры для TrainingModule."""

from dishka import Provider, Scope, provide

from src.Containers.AppSection.TrainingModule.Actions.GreetUserAction import (
    GreetUserAction,
)


class TrainingModuleProvider(Provider):
    """Провайдер для TrainingModule."""
    
    scope = Scope.REQUEST
    
    # Регистрируем Action
    greet_user_action = provide(GreetUserAction)
```

### Добавь провайдер в `src/Ship/Providers/AppProvider.py`:

```python
from src.Containers.AppSection.TrainingModule.Providers import TrainingModuleProvider

# В функции создания контейнера добавь:
# container = make_container(
#     ...,
#     TrainingModuleProvider(),
# )
```

---

## Шаг 7: Тестируем Action

Создадим простой тест.

### Создай файл: `tests/unit/test_greet_user_action.py`

```python
"""Тесты для GreetUserAction."""

import pytest
from returns.result import Success, Failure

from src.Containers.AppSection.TrainingModule.Actions.GreetUserAction import (
    GreetUserAction,
)
from src.Containers.AppSection.TrainingModule.Data.Schemas.Requests import GreetUserRequest
from src.Containers.AppSection.TrainingModule.Errors import InvalidLanguageError


@pytest.mark.asyncio
async def test_greet_user_success_ru():
    """Успешное приветствие на русском."""
    action = GreetUserAction()
    request = GreetUserRequest(name="Иван", language="ru")
    
    result = await action.run(request)
    
    assert isinstance(result, Success)
    assert result.unwrap().greeting == "Привет, Иван!"


@pytest.mark.asyncio
async def test_greet_user_success_en():
    """Успешное приветствие на английском."""
    action = GreetUserAction()
    request = GreetUserRequest(name="John", language="en")
    
    result = await action.run(request)
    
    assert isinstance(result, Success)
    assert result.unwrap().greeting == "Hello, John!"


@pytest.mark.asyncio
async def test_greet_user_invalid_language():
    """Ошибка при неподдерживаемом языке."""
    action = GreetUserAction()
    request = GreetUserRequest(name="Test", language="de")
    
    result = await action.run(request)
    
    assert isinstance(result, Failure)
    error = result.failure()
    assert isinstance(error, InvalidLanguageError)
    assert error.language == "de"
```

### Запуск тестов:

```bash
uv run pytest tests/unit/test_greet_user_action.py -v
```

---

## Итоговое задание

Создай **новый Action** `CalculateSumAction`:

1. **Input:** `CalculateSumRequest` с полями `a: int`, `b: int`
2. **Output:** `CalculateSumResponse` с полем `result: int`
3. **Error:** `NegativeNumberError` если a или b < 0
4. Action складывает числа и возвращает результат

Требования:
- Абсолютные импорты
- Возвращает `Result[T, E]`
- Pydantic DTO
- Frozen error с http_status = 400

```
@training проверь итоговое задание
```

---

## Что дальше?

Поздравляю! Ты создал свой первый Action в Hyper-Porto.

### Следующие шаги:

1. [Туториал 02: Spec-Driven Workflow](./02-spec-driven-workflow.md) — как описывать требования в spec-файлах
2. [Симуляция: create-user-module](../simulations/create-user-module/) — создание полноценного модуля

### Полезные ресурсы:

- [Документация по компонентам](../../../docs/03-components.md)
- [Result и Railway-oriented programming](../../../docs/04-result-railway.md)
- [Сниппет Action](../../snippets/action.md)

---

## Резюме

| Компонент | Что делает | Где находится |
|-----------|------------|---------------|
| Action | Бизнес-логика, возвращает Result | `Actions/` |
| Request DTO | Входные данные с валидацией | `Data/Schemas/` |
| Response DTO | Выходные данные | `Data/Schemas/` |
| Error | Типизированная ошибка | `Errors.py` |
| Provider | DI регистрация | `Providers.py` |
