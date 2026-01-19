# 📚 API Reference

## 🌐 REST API Endpoints

### 📖 Books API

#### Create Book
```http
POST /api/books
Content-Type: application/json

{
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "isbn": "9780132350884",
  "description": "Optional description",
  "is_available": true
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "isbn": "9780132350884",
  "description": "Optional description",
  "is_available": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Get Book
```http
GET /api/books/{book_id}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "isbn": "9780132350884",
  "description": "Optional description",
  "is_available": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### List Books
```http
GET /api/books?limit=20&offset=0
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| limit | integer | No | Items per page (default: 100, max: 1000) |
| offset | integer | No | Items to skip (default: 0) |

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Clean Code",
    "author": "Robert C. Martin",
    "isbn": "9780132350884",
    "description": "Optional description",
    "is_available": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Update Book
```http
PATCH /api/books/{book_id}
Content-Type: application/json

{
  "title": "Clean Code: Updated Edition",
  "description": "Updated"
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Clean Code: Updated Edition",
  "author": "Robert C. Martin",
  "isbn": "9780132350884",
  "description": "Updated",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### Delete Book
```http
DELETE /api/books/{book_id}
```

**Response:**
```http
204 No Content
```


### 👤 Users API

#### Create User
```http
POST /api/users
Content-Type: application/json

{
  "email": "john@example.com",
  "username": "john",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "john@example.com",
  "username": "john",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": null
}
```

#### Get User
```http
GET /api/users/{user_id}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "john@example.com",
  "username": "john",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": null
}
```

#### List Users
```http
GET /api/users?limit=20&offset=0
```

**Response:**
```json
[
  {
    "id": "uuid",
    "email": "john@example.com",
    "username": "john",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "last_login": null
  }
]
```

#### Update User
```http
PATCH /api/users/{user_id}
Content-Type: application/json

{
  "first_name": "Johnny",
  "is_active": false
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "john@example.com",
  "username": "john",
  "first_name": "Johnny",
  "last_name": "Doe",
  "role": "user",
  "is_active": false,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "last_login": null
}
```

#### Delete User
```http
DELETE /api/users/{user_id}
```

**Response:**
```http
204 No Content
```

### 🔐 Authentication API

<!-- Auth API не реализовано в коде. Раздел удалён. -->

## 🔍 Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "ENTITY_NOT_FOUND",
    "message": "Entity not found",
    "details": {
      "id": "uuid"
    }
  }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | VALIDATION_ERROR | Invalid request data |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource already exists |
| 422 | UNPROCESSABLE_ENTITY | Business logic violation |
| 500 | INTERNAL_ERROR | Server error |

## 🔧 Health Check

### Endpoint
```http
GET /health
```

### Response
```json
{
  "status": "healthy"
}
```

## 📖 OpenAPI Specification

### Access OpenAPI Schema
```http
GET /api/docs
```

### Download OpenAPI JSON
```bash
curl http://localhost:8000/schema > openapi.json
```

### Generate Client Code
```bash
openapi-generator generate -i openapi.json -g typescript-axios -o ./sdk
```

## 📚 Следующие шаги

1. [**Архитектурные диаграммы**](10-diagrams.md) - визуализация архитектуры
2. [**AI Development**](11-ai-development.md) - интеграция с AI
3. [**Best Practices**](08-best-practices.md) - лучшие практики

---

<div align="center">

**📚 Complete API Reference for Porto Template!**

[← Best Practices](08-best-practices.md) | [Диаграммы →](10-diagrams.md)

</div>
