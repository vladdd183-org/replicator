# 02. Spec-Driven Workflow

> Полный цикл разработки от идеи до кода через spec-файлы

**Уровень:** Intermediate  
**Время:** 45 минут  
**Темы:** Spec-файлы, итеративная разработка, генерация кода  
**Пререквизиты:** [01-first-action](./01-first-action.md)

---

## Цель

После этого туториала ты сможешь:

- Описывать требования в spec-файлах
- Использовать AI для генерации кода из spec
- Итеративно улучшать спецификацию
- Понимать цикл "spec → code → feedback → spec"

---

## Что такое Spec-Driven Development?

**Spec-Driven Development** — подход, где разработка начинается с описания требований в структурированном формате (spec-файле), который затем используется для генерации кода.

### Преимущества

- Явное описание требований до написания кода
- AI понимает контекст и генерирует консистентный код
- Легко отслеживать изменения в требованиях
- Спецификация служит документацией

### Цикл разработки

```
1. Idea → 2. Spec → 3. Review → 4. Generate → 5. Test → 6. Refine
     ↑                                                         ↓
     └─────────────────────────────────────────────────────────┘
```

---

## Шаг 1: Знакомство со spec-файлами

Spec-файл — это YAML-документ с описанием функциональности.

### Структура spec-файла

```yaml
# agent-os/specs/{feature-name}.spec.yml
feature: Название функциональности
version: "1.0"
status: draft | review | approved | implemented

# Контекст
context:
  module: В каком модуле
  description: Что делает

# Модель данных
models:
  - name: EntityName
    fields:
      - name: field_name
        type: str | int | UUID | etc
        constraints: [required, unique, etc]

# Use Cases (Actions)
actions:
  - name: ActionName
    description: Что делает
    input:
      - name: param
        type: type
    output:
      type: OutputType
    errors:
      - ErrorName

# API Endpoints
endpoints:
  - method: POST | GET | etc
    path: /api/v1/...
    action: ActionName
```

---

## Шаг 2: Создаём первый spec-файл

Представим задачу: нужен модуль для управления заметками (Notes).

### Создай файл: `agent-os/specs/notes-module.spec.yml`

```yaml
feature: Notes Management
version: "1.0"
status: draft

context:
  module: NotesModule
  section: AppSection
  description: |
    Модуль для создания и управления текстовыми заметками.
    Пользователь может создавать, просматривать, редактировать и удалять заметки.

# Модель данных
models:
  - name: Note
    table: notes
    fields:
      - name: id
        type: UUID
        constraints: [primary_key, auto_generate]
      - name: title
        type: str
        constraints: [required, max_length:200]
      - name: content
        type: str
        constraints: [required]
      - name: user_id
        type: UUID
        constraints: [required, foreign_key:users.id]
      - name: is_pinned
        type: bool
        constraints: [default:false]
      - name: created_at
        type: datetime
        constraints: [auto_now_add]
      - name: updated_at
        type: datetime
        constraints: [auto_now]

# Use Cases
actions:
  - name: CreateNoteAction
    description: Создание новой заметки
    input:
      - name: title
        type: str
        validation: min_length:1, max_length:200
      - name: content
        type: str
        validation: min_length:1
      - name: user_id
        type: UUID
    output:
      type: Note
    errors:
      - NoteTitleTooLongError
    events:
      - NoteCreated

  - name: GetNoteAction
    description: Получение заметки по ID
    input:
      - name: note_id
        type: UUID
      - name: user_id
        type: UUID
    output:
      type: Note | None
    errors:
      - NoteNotFoundError
      - NoteAccessDeniedError

  - name: UpdateNoteAction
    description: Обновление заметки
    input:
      - name: note_id
        type: UUID
      - name: user_id
        type: UUID
      - name: title
        type: str | None
      - name: content
        type: str | None
      - name: is_pinned
        type: bool | None
    output:
      type: Note
    errors:
      - NoteNotFoundError
      - NoteAccessDeniedError
    events:
      - NoteUpdated

  - name: DeleteNoteAction
    description: Удаление заметки
    input:
      - name: note_id
        type: UUID
      - name: user_id
        type: UUID
    output:
      type: bool
    errors:
      - NoteNotFoundError
      - NoteAccessDeniedError
    events:
      - NoteDeleted

  - name: ListUserNotesAction
    description: Получение всех заметок пользователя
    input:
      - name: user_id
        type: UUID
      - name: pinned_only
        type: bool
        default: false
      - name: limit
        type: int
        default: 50
      - name: offset
        type: int
        default: 0
    output:
      type: list[Note]

# API Endpoints
endpoints:
  - method: POST
    path: /api/v1/notes
    action: CreateNoteAction
    auth: required
    request_body: CreateNoteRequest
    response: NoteResponse
    status_codes:
      201: Created
      400: Validation error
      401: Unauthorized

  - method: GET
    path: /api/v1/notes/{note_id}
    action: GetNoteAction
    auth: required
    response: NoteResponse
    status_codes:
      200: OK
      404: Not found
      403: Access denied

  - method: PATCH
    path: /api/v1/notes/{note_id}
    action: UpdateNoteAction
    auth: required
    request_body: UpdateNoteRequest
    response: NoteResponse

  - method: DELETE
    path: /api/v1/notes/{note_id}
    action: DeleteNoteAction
    auth: required
    status_codes:
      204: Deleted
      404: Not found

  - method: GET
    path: /api/v1/notes
    action: ListUserNotesAction
    auth: required
    query_params:
      - pinned_only: bool
      - limit: int
      - offset: int
    response: list[NoteResponse]

# Ошибки
errors:
  - name: NoteNotFoundError
    code: NOTE_NOT_FOUND
    http_status: 404
    message_template: "Note with id {note_id} not found"
    fields:
      - note_id: UUID

  - name: NoteAccessDeniedError
    code: NOTE_ACCESS_DENIED
    http_status: 403
    message_template: "Access to note {note_id} denied"
    fields:
      - note_id: UUID

  - name: NoteTitleTooLongError
    code: NOTE_TITLE_TOO_LONG
    http_status: 400
    message_template: "Title exceeds maximum length of {max_length} characters"
    fields:
      - max_length: int

# События
events:
  - name: NoteCreated
    fields:
      - note_id: UUID
      - user_id: UUID
      - title: str

  - name: NoteUpdated
    fields:
      - note_id: UUID
      - user_id: UUID
      - changes: dict

  - name: NoteDeleted
    fields:
      - note_id: UUID
      - user_id: UUID
```

---

## Шаг 3: Ревью спецификации

Перед генерацией кода важно проверить spec-файл.

### Чек-лист ревью

- [ ] Все поля модели описаны с типами и ограничениями
- [ ] Все Actions имеют input, output, errors
- [ ] Endpoints соответствуют REST-конвенциям
- [ ] Ошибки имеют уникальные коды и http_status
- [ ] События покрывают важные изменения состояния

### Попроси AI проверить

```
@spec-review agent-os/specs/notes-module.spec.yml
```

Агент проверит:
- Консистентность типов
- Покрытие edge cases
- Соответствие архитектуре Hyper-Porto

---

## Шаг 4: Генерация кода

Теперь генерируем код из спецификации.

### Команда генерации

```
@generate-from-spec agent-os/specs/notes-module.spec.yml
```

### Что будет сгенерировано

```
src/Containers/AppSection/NotesModule/
├── Models/
│   └── Note.py              # Piccolo Table
├── Data/
│   ├── Schemas.py           # Pydantic DTOs
│   ├── Repository.py        # NoteRepository
│   └── UnitOfWork.py        # NoteUnitOfWork
├── Actions/
│   ├── CreateNoteAction.py
│   ├── GetNoteAction.py
│   ├── UpdateNoteAction.py
│   ├── DeleteNoteAction.py
│   └── ListUserNotesAction.py
├── UI/
│   └── API/
│       ├── Controllers.py   # NoteController
│       └── Routes.py
├── Events.py                # Domain Events
├── Errors.py                # Ошибки модуля
└── Providers.py             # DI регистрация
```

---

## Шаг 5: Проверка сгенерированного кода

После генерации нужно проверить код.

### Пример сгенерированного Action

```python
# src/Containers/AppSection/NotesModule/Actions/CreateNoteAction.py

from dataclasses import dataclass
from returns.result import Result, Success, Failure
from uuid import UUID

from src.Ship.Parents.Action import Action
from src.Containers.AppSection.NotesModule.Data.Schemas import (
    CreateNoteRequest,
)
from src.Containers.AppSection.NotesModule.Data.UnitOfWork import NoteUnitOfWork
from src.Containers.AppSection.NotesModule.Models.Note import Note
from src.Containers.AppSection.NotesModule.Errors import (
    NoteError,
    NoteTitleTooLongError,
)
from src.Containers.AppSection.NotesModule.Events import NoteCreated


MAX_TITLE_LENGTH = 200


@dataclass
class CreateNoteAction(Action[CreateNoteRequest, Note, NoteError]):
    """Создание новой заметки."""
    
    uow: NoteUnitOfWork
    
    async def run(self, data: CreateNoteRequest) -> Result[Note, NoteError]:
        # Валидация
        if len(data.title) > MAX_TITLE_LENGTH:
            return Failure(NoteTitleTooLongError(max_length=MAX_TITLE_LENGTH))
        
        # Создание заметки
        async with self.uow:
            note = Note(
                title=data.title,
                content=data.content,
                user_id=data.user_id,
            )
            await self.uow.notes.add(note)
            
            # Публикация события
            self.uow.add_event(NoteCreated(
                note_id=note.id,
                user_id=note.user_id,
                title=note.title,
            ))
            
            await self.uow.commit()
        
        return Success(note)
```

### Что проверить

1. **Импорты** — только абсолютные
2. **Типы** — соответствуют spec
3. **Логика** — покрывает edge cases
4. **События** — публикуются правильно

---

## Шаг 6: Итеративное улучшение

Разработка — итеративный процесс. После тестирования обновляем spec.

### Обновление spec-файла

```yaml
# Добавляем новое требование
actions:
  - name: CreateNoteAction
    # ...
    input:
      # Добавляем новое поле
      - name: tags
        type: list[str]
        validation: max_items:10
        default: []
```

### Перегенерация

```
@regenerate-from-spec agent-os/specs/notes-module.spec.yml --action CreateNoteAction
```

---

## Шаг 7: Документирование решений

Важно документировать почему приняты те или иные решения.

### Добавь секцию decisions в spec

```yaml
decisions:
  - id: D001
    date: 2025-01-19
    title: Ограничение на количество заметок
    problem: Нужно ли ограничивать количество заметок на пользователя?
    decision: Нет ограничения в MVP, добавим позже с планами подписки
    consequences:
      - Простая реализация
      - Риск злоупотреблений
      - TODO: добавить rate limiting

  - id: D002
    date: 2025-01-19
    title: Soft delete vs Hard delete
    problem: Как удалять заметки?
    decision: Hard delete в MVP, soft delete в будущем
    consequences:
      - Простая реализация
      - Нельзя восстановить удалённые заметки
```

---

## Итоговое задание

Создай spec-файл для модуля **Tags** (теги для заметок):

### Требования

1. **Model: Tag**
   - id, name, color, user_id, created_at
   - name уникален для пользователя

2. **Actions:**
   - CreateTagAction
   - DeleteTagAction
   - ListUserTagsAction

3. **Endpoints:**
   - POST /api/v1/tags
   - DELETE /api/v1/tags/{tag_id}
   - GET /api/v1/tags

4. **Ошибки:**
   - TagNotFoundError
   - TagAlreadyExistsError

### Создай файл

```
agent-os/specs/tags-module.spec.yml
```

Проверь:

```
@training проверь итоговое задание
```

---

## Что дальше?

### Следующие шаги

1. [Туториал 03: Отладка с агентами](./03-debugging-with-agents.md)
2. Попробуй создать свой spec для реальной задачи

### Полезные ресурсы

- [Документация Spec-Driven Development](../../../docs/07-spec-driven.md)
- [Примеры spec-файлов](../../../foxdocs/spec-kit-main/)
- [Шаблон spec-файла](../../templates/spec.template)

---

## Резюме

| Этап | Что делаем | Инструмент |
|------|------------|------------|
| 1. Idea | Формулируем требования | Голова |
| 2. Spec | Описываем в YAML | `*.spec.yml` |
| 3. Review | Проверяем консистентность | `@spec-review` |
| 4. Generate | Генерируем код | `@generate-from-spec` |
| 5. Test | Тестируем | pytest |
| 6. Refine | Улучшаем spec | Итерация |

### Ключевые принципы

- **Spec — это контракт** между требованиями и кодом
- **Итерации** — нормальная часть процесса
- **Документируй решения** — будущий ты скажет спасибо
