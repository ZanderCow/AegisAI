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

---

## PUT /api/auth/change-password

Change the current user's password.

**Authorization:** Bearer token required in Authorization header

**Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePass456!"
}
```

**Response 200 OK:**
```json
{
  "message": "Password changed successfully"
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Current password is incorrect"
}
```

**Response 401 Unauthorized:**
```json
{
  "detail": "Not authenticated"
}
```

---

## POST /api/auth/password-reset

Request a password reset token via email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response 200 OK:**
```json
{
  "message": "Password reset email sent"
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Email not found"
}
```

---

## POST /api/auth/password-reset/confirm

Confirm password reset with token and set new password.

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass456!"
}
```

**Response 200 OK:**
```json
{
  "message": "Password reset successfully"
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Invalid or expired reset token"
}
```

---

## POST /api/auth/verify-email

Verify user email address with verification token.

**Request Body:**
```json
{
  "token": "verification-token-from-email"
}
```

**Response 200 OK:**
```json
{
  "message": "Email verified successfully"
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Invalid or expired verification token"
}
```