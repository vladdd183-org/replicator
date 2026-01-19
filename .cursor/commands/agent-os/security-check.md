# /security-check — Аудит безопасности

Запуск security-reviewer агента для проверки безопасности кода.

## Агент

- Agent: `.cursor/agents/security-reviewer.md`

## Синтаксис

```
/security-check [<target>] [--focus <area>]
```

## Примеры

```
/security-check
/security-check UserModule
/security-check --focus auth
/security-check OrderModule --focus input-validation
```

## Параметры

- `[<target>]` — Модуль для проверки (опционально, по умолчанию весь проект)
- `[--focus]` — Область фокуса (auth, input-validation, sql, secrets, config)

## Области проверки

### 1. Authentication & Authorization
- JWT validation
- Token expiration
- Protected routes
- Role-based access

### 2. Input Validation
- Pydantic validation
- String length limits
- Email/UUID validation
- File upload restrictions

### 3. SQL Injection
- Raw SQL usage
- Parameterized queries
- ORM usage

### 4. Sensitive Data
- Secrets in code
- Password logging
- Response data exposure
- .env in .gitignore

### 5. Error Handling
- Stack traces in production
- Error message leakage

## Вывод

```markdown
# Security Audit Report

## Critical Issues
- [Issue description]

## High Priority
- [Issue description]

## Recommendations
1. [Recommendation]
2. [Recommendation]
```
