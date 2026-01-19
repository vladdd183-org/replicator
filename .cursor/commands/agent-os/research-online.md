# Research Online — Ресерч через веб и документацию

Поиск информации в интернете, официальной документации и научных статьях.

## Когда использовать

- Нужна актуальная информация о библиотеке
- Ищем best practices от сообщества
- Нужны примеры из официальной документации
- Исследуем новые паттерны или технологии

## Доступные инструменты

| Инструмент | Назначение |
|------------|------------|
| `web_search` | Поиск в интернете |
| `mcp_parrallel_web_search_preview` | Параллельный веб-поиск |
| `mcp_parrallel_web_fetch` | Загрузка контента со страниц |
| `mcp_context7_resolve-library-id` | Поиск библиотеки в Context7 |
| `mcp_context7_query-docs` | Запрос документации библиотеки |
| `mcp_arxiv-mcp-server_search_papers` | Поиск научных статей |

## Процесс

### PHASE 1: Определить что искать

IF пользователь указал тему, используй её.

OTHERWISE спроси:

```
Что вы хотите найти онлайн?

Примеры:
- "Документация Litestar middleware" — найду в официальных docs
- "Best practices Result pattern Python" — поищу статьи
- "Piccolo ORM migrations" — найду примеры и туториалы
- "Dishka scopes explained" — найду объяснения
```

### PHASE 2: Поиск в документации библиотек

Для библиотек из стека проекта используй Context7:

```
# Сначала найди library ID
mcp_context7_resolve-library-id("litestar middleware", "litestar")

# Затем запроси документацию
mcp_context7_query-docs("/litestar/litestar", "How to create custom middleware?")
```

**Библиотеки проекта:**
- Litestar — web framework
- Piccolo — ORM
- Dishka — DI
- Returns — Result pattern
- Strawberry — GraphQL
- anyio — async

### PHASE 3: Веб-поиск

Для общих вопросов и best practices:

```
# Параллельный поиск
mcp_parrallel_web_search_preview(
  objective="Find best practices for Result pattern in Python",
  search_queries=["Result pattern Python best practices", "Railway oriented programming Python"]
)

# Загрузка найденных страниц
mcp_parrallel_web_fetch(
  urls=["url1", "url2"],
  objective="Extract code examples and recommendations"
)
```

### PHASE 4: Официальная документация

Проверь официальные источники:

- Litestar — <https://docs.litestar.dev/>
- Piccolo ORM — <https://piccolo-orm.com/docs/>
- Dishka DI — <https://dishka.dev/>
- Returns — <https://returns.readthedocs.io/>
- Strawberry GraphQL — <https://strawberry.rocks/docs/>
- anyio — <https://anyio.readthedocs.io/>

### PHASE 5: Научные статьи (опционально)

Для архитектурных паттернов:

```
mcp_arxiv-mcp-server_search_papers(
  query="domain driven design microservices",
  categories=["cs.SE"],
  max_results=5
)
```

### PHASE 6: Сформируй отчёт

```markdown
## 🌐 Результаты онлайн-ресерча: [Тема]

### Официальная документация

**[Название библиотеки]**
- Источник: [URL официальной документации]
- Ключевые находки:
  - [Находка 1]
  - [Находка 2]
- Примеры кода: [если есть]

### Статьи и туториалы

**[Название статьи]** ([источник])
- Суть: [краткое описание]
- Полезное: [что применимо к проекту]

### Best Practices

- [Practice 1]: [описание]
- [Practice 2]: [описание]

### Применимость к Hyper-Porto

- ✅ Подходит: [что можно использовать]
- ⚠️ Адаптировать: [что нужно изменить]
- ❌ Не подходит: [что не применимо]

### Ссылки для дальнейшего изучения

- [URL 1] — [описание]
- [URL 2] — [описание]
```

## Быстрые команды

| Запрос | Что ищем |
|--------|----------|
| `research-online Litestar events` | События в Litestar |
| `research-online Piccolo migrations` | Миграции Piccolo |
| `research-online Dishka scopes` | Scopes в Dishka |
| `research-online Result Railway` | Railway-oriented programming |
| `research-online anyio TaskGroup` | Structured concurrency |



