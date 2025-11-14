# Security Setup Guide

This guide explains how to set up and use the security features implemented in the healthcare chatbot.

## Quick Start

1. **Set environment variables:**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit .env and set:
   JWT_SECRET_KEY=your-very-secure-secret-key-minimum-32-characters
   NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require
   ```

2. **Generate Prisma client and push schema:**
   ```bash
   cd api
   prisma generate --schema prisma/schema.prisma
   prisma db push --schema prisma/schema.prisma --accept-data-loss
   ```

3. **Create an admin user (optional):**
   ```bash
   python scripts/create_admin.py
   ```

4. **Start the server:**
   ```bash
   python -m uvicorn main:app --reload
   ```

## Security Features Implemented

### ✅ 1. Password Security
- **SHA-256 hashing** with unique salt per password
- Passwords stored as `hash:salt` format
- Never stored in plain text
- Even if database is leaked, passwords cannot be recovered

### ✅ 2. Input Validation
- **Server-side validation** for all inputs
- **SQL injection prevention** - patterns detected and rejected
- **XSS prevention** - malicious scripts sanitized
- **Type validation** - ensures correct data types
- **Length limits** - prevents buffer overflow attacks

### ✅ 3. Secure Token Storage
- **HTTP-only cookies** - JavaScript cannot access tokens
- **Secure flag** - cookies only sent over HTTPS
- **SameSite=Lax** - CSRF protection
- Tokens never exposed to client-side JavaScript

### ✅ 4. Role-Based Authentication
- **All endpoints protected** - require authentication
- **Role-based access** - users, admins, doctors
- **Data isolation** - users can only access their own data
- **Admin override** - admins can access all data

## API Usage

### Registration

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "age": 30,
    "sex": "male",
    "city": "Mumbai"
  }'
```

**Response:** Sets HTTP-only cookies and returns user profile

### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

**Response:** Sets HTTP-only cookies and returns user profile

### Using Authenticated Endpoints

```bash
# Chat endpoint (requires authentication)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "text": "I have a headache",
    "lang": "en",
    "profile": {
      "age": 30,
      "sex": "male"
    }
  }'
```

### Get Current User

```bash
curl -X GET http://localhost:8000/auth/me \
  -b cookies.txt
```

### Logout

```bash
curl -X POST http://localhost:8000/auth/logout \
  -b cookies.txt
```

## Frontend Integration

### Login Flow

```javascript
// Login
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // Important: include cookies
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123'
  })
});

// Cookies are automatically set by browser
// No need to manually store tokens
```

### Making Authenticated Requests

```javascript
// All subsequent requests automatically include cookies
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include', // Important: include cookies
  body: JSON.stringify({
    text: 'I have a headache',
    lang: 'en',
    profile: { age: 30, sex: 'male' }
  })
});
```

### Token Refresh

```javascript
// Refresh token when access token expires
const response = await fetch('http://localhost:8000/auth/refresh', {
  method: 'POST',
  credentials: 'include'
});
```

## Security Checklist

- [x] Passwords hashed with SHA-256 + salt
- [x] Input validation on all endpoints
- [x] SQL injection prevention
- [x] XSS prevention
- [x] HTTP-only cookie token storage
- [x] Secure cookie flag (HTTPS only)
- [x] Role-based access control
- [x] User data isolation
- [x] Token expiration
- [x] Token refresh mechanism
- [x] Password strength requirements

## Testing Security

### Test Password Hashing

```python
from api.auth.password import hash_password_for_storage, verify_password_from_storage

# Hash password
hashed = hash_password_for_storage("MyPassword123")
print(f"Stored: {hashed}")

# Verify password
is_valid = verify_password_from_storage("MyPassword123", hashed)
print(f"Valid: {is_valid}")  # True

is_invalid = verify_password_from_storage("WrongPassword", hashed)
print(f"Invalid: {is_invalid}")  # False
```

### Test Input Validation

```python
from api.auth.validation import validate_chat_input

# Valid input
safe = validate_chat_input("Hello, I need help")
print(safe)  # Returns sanitized text

# SQL injection attempt
try:
    validate_chat_input("'; DROP TABLE users; --")
except ValueError as e:
    print(f"Blocked: {e}")  # Should raise ValueError
```

## Production Deployment

### Required Environment Variables

```bash
# Critical for production
JWT_SECRET_KEY=<generate-strong-random-key-min-32-chars>
NEON_DB_URL=<your-neon-db-connection-string>
CORS_ORIGINS=<your-production-domain>

# Optional but recommended
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Generate Secure JWT Secret

```python
import secrets
print(secrets.token_urlsafe(32))
```

### HTTPS Configuration

1. **Use HTTPS in production** - Required for secure cookies
2. **Set `secure=True`** in cookie configuration (already done)
3. **Configure SSL certificates** on your server
4. **Update CORS_ORIGINS** to your production domain

### Database Security

1. **Use SSL connection** - Already configured with `sslmode=require`
2. **Restrict database access** - Use firewall rules
3. **Regular backups** - Even with hashed passwords, backups are important
4. **Monitor access logs** - Watch for suspicious activity

## Troubleshooting

### Cookies not being set
- **Check CORS configuration** - `allow_credentials=True` must be set
- **Verify HTTPS** - Secure cookies require HTTPS in production
- **Check browser console** - Look for cookie-related errors

### Authentication failing
- **Check JWT_SECRET_KEY** - Must be set and consistent
- **Verify token expiration** - Tokens expire after 30 minutes
- **Check user account** - Must be active (`isActive=true`)

### Access denied errors
- **Check user role** - Verify user has required permissions
- **Verify data ownership** - Users can only access their own data
- **Check admin status** - Some endpoints require admin role

## Security Best Practices

1. **Never log passwords** - Even in error messages
2. **Use HTTPS** - Always in production
3. **Rotate JWT secrets** - Periodically change JWT_SECRET_KEY
4. **Monitor failed logins** - Watch for brute force attempts
5. **Implement rate limiting** - Already done for API endpoints
6. **Regular security audits** - Review code and dependencies
7. **Keep dependencies updated** - Patch security vulnerabilities

## Additional Security Recommendations

1. **Two-Factor Authentication (2FA)** - Add for sensitive operations
2. **Password Reset Flow** - Implement secure password reset
3. **Account Lockout** - Lock accounts after failed login attempts
4. **IP Whitelisting** - For admin endpoints
5. **Audit Logging** - Log all authentication events
6. **Session Management** - Track active sessions
7. **Password Complexity** - Enforce stronger password requirements

