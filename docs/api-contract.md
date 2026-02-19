# API Contract Documentation

## POST /api/auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 201 Created:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-02-17T10:00:00Z",
  "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Email already registered"
}
```

---

## POST /api/auth/login

Authenticate user and return JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 200 OK:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response 401 Unauthorized:**
```json
{
  "detail": "Invalid credentials"
}
```

---

## GET /api/auth/me

Get current authenticated user's profile information.

**Authorization:** Bearer token required in Authorization header

**Response 200 OK:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z"
}
```

**Response 401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```