# 🤖 AI-Driven Development с Porto Architecture

## 🎯 Почему Porto идеально подходит для AI?

Porto архитектура специально оптимизирована для работы с AI-инструментами благодаря:

1. **Single Responsibility** - каждый файл имеет одну функцию `run()`
2. **Predictable Structure** - AI точно знает, где искать код
3. **Clear Naming** - описательные имена помогают AI понять контекст
4. **Isolated Components** - AI может работать с отдельными частями

## 📋 System Prompts для AI Assistant

### 🎯 Главный System Prompt для Porto разработки

```markdown
You are an expert Python developer specializing in Porto architectural pattern. You work with a codebase that follows these strict principles:

## Architecture Rules:
1. **Porto Pattern**: The codebase is organized into Containers (business logic) and Ship (infrastructure)
2. **Single Responsibility**: Each file contains ONE class with ONE public method called `run()`
3. **Component Types**: Actions (orchestration), Tasks (atomic operations), Models (data), Controllers (HTTP handlers)
4. **Dependency Injection**: All dependencies are injected via constructor using Dishka DI container
5. **Async First**: All I/O operations use async/await pattern

## File Structure:
\```
src/
├── Containers/
│   ├── AppSection/        # Business logic containers
│   │   └── {Container}/   # e.g., User, Book, Order
│   │       ├── Actions/   # Business operations
│   │       ├── Tasks/     # Atomic tasks
│   │       ├── Models/    # Data models (Piccolo ORM)
│   │       ├── UI/API/    # Controllers and routes
│   │       └── Providers.py # DI configuration
│   └── VendorSection/     # External integrations
└── Ship/                  # Shared infrastructure
    ├── Parents/          # Base classes
    ├── Core/            # Core utilities
    └── Providers/       # Global DI
\```

## Naming Conventions:
- Actions: `{Verb}{Entity}Action` (e.g., CreateUserAction, UpdateBookAction)
- Tasks: `{Verb}{Entity}Task` (e.g., ValidateEmailTask, SendNotificationTask)
- Models: `{Entity}` (e.g., User, Book, Order)
- Controllers: `{Entity}Controller` (e.g., UserController, BookController)
- Files match class names exactly

## Code Generation Rules:
1. ALWAYS inherit from appropriate Ship/Parents base class
2. ALWAYS implement single `run()` method in Actions and Tasks
3. ALWAYS use type hints for all parameters and returns
4. ALWAYS use Piccolo ORM for models, not SQLAlchemy
5. ALWAYS use Litestar decorators for controllers, not FastAPI
6. ALWAYS handle exceptions with specific Container exceptions
7. NEVER put business logic in Controllers - delegate to Actions
8. NEVER call Tasks from other Tasks - only Actions orchestrate
9. NEVER access database directly in Actions - use Tasks

## Technology Stack:
- Web Framework: Litestar (async)
- ORM: Piccolo (with SQLite)
- DI Container: Dishka
- Logging: Logfire
- Message Queue: FastStream + RabbitMQ
- Testing: pytest + pytest-asyncio

## Response Format:
When generating code, always:
1. Show complete file path as comment
2. Include all necessary imports
3. Add docstrings with clear descriptions
4. Include type hints
5. Show example usage if applicable
```

### 🔧 Specialized Prompts для разных задач

#### 1. Prompt для создания нового Container

```markdown
I need to create a new Porto Container for {ENTITY} management. Generate the complete structure following Porto architecture:

Requirements:
- Entity: {ENTITY}
- Operations: Create, Read, Update, Delete, List
- Validations: {SPECIFIC_VALIDATIONS}
- Business Rules: {BUSINESS_RULES}

Generate:
1. Model with Piccolo ORM fields
2. All CRUD Actions
3. Required Tasks for each Action
4. Controller with REST endpoints
5. DI Provider configuration
6. Exception classes
7. DTO/Schema classes

Follow Porto single responsibility: each Task does ONE thing, Actions orchestrate Tasks.
```

#### 2. Prompt для создания Action

```markdown
Create a Porto Action class for {OPERATION} following these rules:

Action: {ACTION_NAME}
Purpose: {BUSINESS_PURPOSE}
Input: {INPUT_PARAMETERS}
Output: {EXPECTED_OUTPUT}
Steps:
1. {STEP_1_DESCRIPTION}
2. {STEP_2_DESCRIPTION}
3. {STEP_3_DESCRIPTION}

Requirements:
- Inherit from src.Ship.Parents.Action
- Use dependency injection for all Tasks
- Implement single async run() method
- Add comprehensive error handling
- Include Logfire tracing spans
- Write clear docstrings

The Action should orchestrate Tasks, not implement business logic directly.
```

#### 3. Prompt для создания Task

```markdown
Create a Porto Task with single responsibility:

Task: {TASK_NAME}
Single Responsibility: {ONE_SPECIFIC_OPERATION}
Input: {INPUT_PARAMS}
Output: {OUTPUT_TYPE}
Database Operations: {YES/NO - SPECIFY}
External Services: {YES/NO - SPECIFY}

Requirements:
- Inherit from src.Ship.Parents.Task
- Implement ONLY async run() method
- Do EXACTLY one thing
- Include error handling for specific cases
- Add type hints for all parameters
- Write docstring explaining the single responsibility

Remember: Tasks are atomic and reusable. They should NEVER call other Tasks.
```

## 🎨 AI Code Review Prompts

### Prompt для code review

```markdown
Review this Porto architecture code for compliance:

```python
{CODE_TO_REVIEW}
\```

Check for:
1. **Single Responsibility**: Does each class have one clear purpose?
2. **Porto Structure**: Are files in correct directories?
3. **Naming Convention**: Do names follow {Verb}{Entity}{Component} pattern?
4. **Dependency Injection**: Are dependencies properly injected?
5. **Async Pattern**: Are all I/O operations async?
6. **Error Handling**: Are exceptions specific and informative?
7. **Type Hints**: Are all parameters and returns typed?
8. **Docstrings**: Is the code self-documenting?

Provide:
- Compliance score (1-10)
- Specific violations found
- Suggested improvements
- Refactored code if needed
```

## 🚀 Prompts для оптимизации

### Performance оптимизация

```markdown
Optimize this Porto Task for performance:

```python
{TASK_CODE}
\```

Consider:
1. Database query optimization (N+1 problems, eager loading)
2. Async concurrency (asyncio.gather for parallel operations)
3. Caching opportunities (Redis, in-memory)
4. Batch processing for multiple items
5. Connection pooling
6. Query result limiting and pagination

Maintain Porto principles while optimizing. Show before/after comparison.
```

### Refactoring для лучшей поддержки AI

```markdown
Refactor this code to be more AI-friendly while maintaining Porto architecture:

```python
{CODE_TO_REFACTOR}
\```

Improvements:
1. **Clearer naming**: More descriptive names for AI understanding
2. **Smaller functions**: Break complex logic into smaller Tasks
3. **Better typing**: Add TypedDict, Literal, Union where appropriate
4. **Documentation**: Add examples in docstrings
5. **Predictable patterns**: Use consistent patterns across similar components

Goal: Make code that AI assistants can easily understand, modify, and extend.
```

## 📝 Rules для AI Configuration

### .cursorrules / .github/copilot-instructions.md

```markdown
# Porto Architecture Rules for AI Assistant

## MUST Follow:

### Architecture
- Use Porto pattern: Containers for business logic, Ship for infrastructure
- Each file = one class = one public method `run()`
- Strict separation: Actions orchestrate, Tasks execute, Models store, Controllers route

### File Organization
\```
src/Containers/AppSection/{Container}/{Component}/{Name}{Component}.py
\```
Example: src/Containers/AppSection/Book/Actions/CreateBookAction.py

### Naming Standards
- Actions: {Verb}{Entity}Action (CreateBookAction)
- Tasks: {Verb}{Entity}Task (ValidateBookTask)
- Models: {Entity} (Book)
- Controllers: {Entity}Controller (BookController)
- Exceptions: {Entity}{Error}Exception (BookNotFoundException)

### Code Patterns
```python
# Action Pattern
class {Verb}{Entity}Action(Action):
    def __init__(self, task1: Task1, task2: Task2):
        self.task1 = task1
        self.task2 = task2
    
    async def run(self, *args) -> Result:
        # Orchestrate tasks
        pass

# Task Pattern
class {Verb}{Entity}Task(Task):
    async def run(self, *args) -> Result:
        # Single responsibility
        pass
\```

### Technology Stack
- Web: Litestar (NOT FastAPI)
- ORM: Piccolo (NOT SQLAlchemy)
- DI: Dishka
- Async: asyncio, httpx
- Testing: pytest-asyncio

## NEVER Do:
- Put business logic in Controllers
- Call Tasks from other Tasks
- Access database in Actions
- Create "Service" classes (use Actions/Tasks)
- Use synchronous I/O operations
- Mix concerns in single file
- Use generic names (Helper, Utils, Manager)

## AI Behavior:
1. When asked to create feature, generate complete Container structure
2. When fixing bugs, maintain Porto patterns
3. When refactoring, split into smaller Tasks if needed
4. When reviewing, check single responsibility first
5. Always suggest Porto-compliant solutions

## Examples Priority:
1. Check existing Containers for patterns
2. Follow Ship/Parents base classes
3. Maintain consistency with project style
4. Optimize for clarity and AI readability
```

## 🧠 Cognitive Load Optimization

### Правила для уменьшения когнитивной нагрузки

```markdown
# Cognitive Load Optimization Rules

## For AI Understanding:

### 1. Explicit Over Implicit
```python
# ❌ Bad - AI needs to infer
async def process(self, d):
    return await self.h(d["id"])

# ✅ Good - AI understands immediately
async def process_order(self, order_data: OrderDTO):
    return await self.handle_order(order_data.order_id)
\```

### 2. Descriptive Names
```python
# ❌ Bad - unclear purpose
class DTTask(Task):
    async def run(self, u, b):
        pass

# ✅ Good - self-documenting
class DeliverOrderTask(Task):
    async def run(self, user_id: int, book_id: int):
        """Delivers book order to user"""
        pass
\```

### 3. Type Information
```python
# ❌ Bad - AI guesses types
async def calculate(items, discount=None):
    pass

# ✅ Good - AI knows exact types
async def calculate_total(
    items: List[OrderItem],
    discount: Optional[Decimal] = None
) -> Decimal:
\    pass
```

### 4. Single Purpose
```python
# ❌ Bad - multiple responsibilities
class UserTask(Task):
    async def run(self, action, data):
        if action == "create":
            # create logic
        elif action == "update":
            # update logic
        elif action == "delete":
            # delete logic

# ✅ Good - single responsibility
class CreateUserTask(Task):
    async def run(self, user_data: UserDTO) -> User:
        # only creation logic
\```

### 5. Context in Docstrings
```python
# ✅ Good - AI understands context
class CreateBookAction(Action):
    """
    Manages book creation process.

    Flow:
    1. Validates book data
    2. Checks ISBN uniqueness
    3. Creates book record
    4. Returns book DTO

    Example:
        action = CreateBookAction(...)
        book = await action.run(title="Clean Code", author="Robert Martin", isbn="9780132350884")
    """
```

## 🔍 AI Testing Prompts

### Unit Test Generation

```markdown
Generate comprehensive unit tests for this Porto component:

```python
{COMPONENT_CODE}
\```

Requirements:
1. Use pytest with async support
2. Mock all dependencies (Tasks for Actions, Repositories for Tasks)
3. Test success path and all error cases
4. Use descriptive test names: test_{method}_{scenario}_{expected_result}
5. Include fixtures for common test data
6. Add parametrized tests for multiple scenarios

Follow AAA pattern: Arrange, Act, Assert
```

### Integration Test Generation

```markdown
Create integration tests for this Porto Container:

Container: {CONTAINER_NAME}
Test scenarios:
1. Complete workflow from Controller to Database
2. Error handling across layers
3. Transaction rollback scenarios
4. Concurrent operation handling

Use test database, real DI container, but mock external services.
```

## 📊 Metrics для AI-Friendly Code

### Checklist для AI-оптимизированного кода

```markdown
## AI-Friendliness Score

Rate each component 1-5:

### Clarity
- [ ] Names clearly describe purpose
- [ ] Single responsibility is obvious
- [ ] Dependencies are explicit
- [ ] Flow is linear and predictable

### Documentation
- [ ] Docstrings explain "why" not just "what"
- [ ] Examples provided in docstrings
- [ ] Type hints for all parameters
- [ ] Return types specified

### Structure
- [ ] Follows Porto conventions exactly
- [ ] File location matches component type
- [ ] Inherits from correct base class
- [ ] Uses standard method names (run)

### Patterns
- [ ] Consistent with similar components
- [ ] Uses project's error handling style
- [ ] Follows project's logging patterns
- [ ] Matches project's testing approach

Score: ___/20

15-20: Excellent AI compatibility
10-14: Good, minor improvements needed
5-9: Needs refactoring for AI tools
0-4: Major restructuring required
```

## 🚨 Common AI Pitfalls в Porto

### Избегайте этих ошибок при работе с AI

```python
# ❌ Pitfall 1: AI создаёт сервисы вместо Actions/Tasks
class BookService:  # WRONG - не Porto pattern
    def create_book(self): pass
    def update_book(self): pass

# ✅ Correct: Separate Actions
class CreateBookAction(Action): pass
class UpdateBookAction(Action): pass

# ❌ Pitfall 2: AI смешивает ответственности
class ProcessOrderTask(Task):
    async def run(self):
        # validate
        # calculate
        # save
        # notify  # TOO MUCH!

# ✅ Correct: Split into Tasks
class ValidateOrderTask(Task): pass
class CalculatePriceTask(Task): pass
class SaveOrderTask(Task): pass
class NotifyUserTask(Task): pass

# ❌ Pitfall 3: AI использует неправильный фреймворк
from fastapi import FastAPI  # WRONG
app = FastAPI()

# ✅ Correct: Use Litestar
from litestar import Litestar
app = Litestar()

# ❌ Pitfall 4: AI забывает про async
def get_user(id):  # WRONG - blocking
    return User.objects.get(id=id)

# ✅ Correct: Always async
async def get_user(id):
    return await User.objects.get(id=id)
```

## 🎯 Prompt Engineering Best Practices

### Эффективные промпты для Porto

```markdown
## Template for Feature Request

"Create a Porto Container for {FEATURE} with these specifications:

Business Requirements:
- {REQUIREMENT_1}
- {REQUIREMENT_2}

Technical Constraints:
- Database: SQLite with Piccolo ORM
- Must support concurrent operations
- Include audit logging
- Handle these error cases: {ERRORS}

Generate complete Porto structure:
1. Model with all fields and relationships
2. Actions for main operations
3. Atomic Tasks (one responsibility each)
4. REST API Controller
5. Exception classes
6. DI Provider setup
7. Unit tests for Actions
8. Integration test example

Follow Porto single responsibility strictly. Each file should be AI-readable and maintainable."
```

### Итеративная разработка с AI

```markdown
## Iteration 1: Structure
"Create Porto Container structure for {FEATURE}"

## Iteration 2: Implementation
"Implement the CreateAction with proper Task orchestration"

## Iteration 3: Validation
"Add comprehensive validation to all Tasks"

## Iteration 4: Error Handling
"Add specific exceptions and error handling"

## Iteration 5: Testing
"Generate complete test suite"

## Iteration 6: Documentation
"Add detailed docstrings and examples"

## Iteration 7: Optimization
"Optimize for performance while maintaining Porto principles"
```

## 📚 Ресурсы для AI-Driven Development

### Полезные материалы

1. **Porto + AI Best Practices**
   - Single file = Single responsibility
   - Predictable structure for AI navigation
   - Clear naming for context understanding

2. **Prompt Libraries**
   - GitHub Copilot Labs
   - Cursor AI Templates
   - ChatGPT Custom Instructions

3. **AI Tools Integration**
   - GitHub Copilot configuration
   - Cursor IDE setup
   - Tabnine configuration
   - Codeium setup

## 🎓 Заключение

Porto архитектура создана для гармоничной работы с AI-инструментами. Следуя этим правилам и промптам, вы сможете:

1. **Ускорить разработку** - AI точно понимает структуру
2. **Улучшить качество** - AI следует лучшим практикам
3. **Упростить поддержку** - AI легко модифицирует код
4. **Масштабировать команду** - новые разработчики быстро адаптируются

---

<div align="center">

**🤖 + 🚢 = ❤️ AI loves Porto Architecture!**

[← API Reference](09-api-reference.md) | [Диаграммы →](10-diagrams.md)

</div>
