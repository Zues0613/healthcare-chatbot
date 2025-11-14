# Security Implementation Guide

This document describes the security measures implemented in the healthcare chatbot application.

## Security Features

### 1. Password Security (SHA-256 Hashing)

**Implementation:**
- Passwords are hashed using SHA-256 with a random salt
- Salt is stored alongside the hash in the format: `hash:salt`
- Each password gets a unique salt, preventing rainbow table attacks
- Passwords are never stored in plain text

**Location:**
- `api/auth/password.py` - Password hashing and verification functions
- `api/auth/service.py` - Uses password hashing in registration and authentication

**Usage:**
```python
from api.auth.password import hash_password_for_storage, verify_password_from_storage

# Hash password for storage
password_hash = hash_password_for_storage("user_password")

# Verify password
is_valid = verify_password_from_storage("user_password", password_hash)
```

**Note:** While SHA-256 with salt is implemented as requested, for production environments, consider using bcrypt or Argon2 which are specifically designed for password hashing and provide better protection against brute-force attacks.

### 2. Input Validation and SQL Injection Prevention

**Implementation:**
- All user inputs are validated using Pydantic models
- Server-side validation prevents malicious input from reaching the database
- SQL injection patterns are detected and rejected
- XSS (Cross-Site Scripting) patterns are sanitized

**Location:**
- `api/auth/validation.py` - Input validation utilities
- `api/models.py` - Pydantic models with field validators
- All API endpoints use validated models

**Validation Features:**
- SQL injection pattern detection
- XSS pattern sanitization
- Input length limits
- Type validation
- Format validation (email, UUID, etc.)

**Example:**
```python
from api.auth.validation import validate_chat_input, sanitize_string

# Validate chat input
safe_text = validate_chat_input(user_input)

# Sanitize string
safe_string = sanitize_string(user_input, max_length=100)
```

### 3. Secure Token Storage (HTTP-Only Cookies)

**Implementation:**
- JWT tokens are stored in HTTP-only cookies
- Cookies have `Secure` flag (HTTPS only)
- Cookies have `SameSite=Lax` to prevent CSRF attacks
- Client-side JavaScript cannot access tokens

**Location:**
- `api/auth/jwt.py` - JWT token creation and verification
- `api/auth/routes.py` - Cookie management in login/register endpoints

**Cookie Configuration:**
```python
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,      # JavaScript cannot access
    secure=True,         # HTTPS only
    samesite="lax",     # CSRF protection
    max_age=30 * 60,    # 30 minutes
)
```

**Token Types:**
- **Access Token**: Short-lived (30 minutes), stored in HTTP-only cookie
- **Refresh Token**: Long-lived (7 days), stored in HTTP-only cookie, can be revoked

### 4. Role-Based Authentication (RBAC)

**Implementation:**
- All API endpoints require authentication
- Role-based access control for different user types
- Users can only access their own data (unless admin)
- Admin role can access all data

**Location:**
- `api/auth/middleware.py` - Authentication and authorization middleware
- All protected endpoints use `Depends(require_auth)`
- Role-specific endpoints use `Depends(require_role(["admin"]))`

**Roles:**
- `user` - Regular users (default)
- `admin` - Administrators with full access
- `doctor` - Medical professionals (can be added)

**Usage:**
```python
from api.auth.middleware import require_auth, require_role

# Require authentication
@app.get("/protected")
async def protected_endpoint(user: dict = Depends(require_auth)):
    return {"user_id": user["user_id"]}

# Require specific role
@app.get("/admin-only")
async def admin_endpoint(user: dict = Depends(require_role(["admin"]))):
    return {"message": "Admin access"}
```

## Protected Endpoints

All endpoints require authentication except:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /health` - Health check

### Endpoint Protection:

1. **Chat Endpoints:**
   - `POST /chat` - Requires authentication
   - `POST /voice-chat` - Requires authentication
   - `POST /stt` - Requires authentication

2. **Data Access Endpoints:**
   - `GET /customer/{customer_id}` - Users can only view their own profile
   - `GET /customer/{customer_id}/sessions` - Users can only view their own sessions
   - `GET /session/{session_id}` - Users can only view their own sessions
   - `GET /session/{session_id}/messages` - Users can only view their own messages

3. **Admin Endpoints:**
   - Can be added with `require_role(["admin"])` dependency

## Authentication Flow

### Registration:
1. User provides email and password
2. Password is hashed with SHA-256 and salt
3. User record is created in database
4. JWT tokens are generated
5. Tokens are stored in HTTP-only cookies
6. User profile is returned

### Login:
1. User provides email and password
2. Password is verified against stored hash
3. JWT tokens are generated
4. Tokens are stored in HTTP-only cookies
5. User profile is returned

### Request Flow:
1. Client sends request with HTTP-only cookie
2. Server extracts token from cookie
3. Token is verified
4. User data is extracted from token
5. Request is processed with user context
6. Response is returned

### Token Refresh:
1. Client sends refresh token from cookie
2. Server verifies refresh token
3. New access token is generated
4. New access token is stored in HTTP-only cookie

## Environment Variables

Required environment variables:

```bash
# Database
NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Security Best Practices

### 1. Password Requirements
- Minimum 8 characters
- Must contain at least one letter
- Must contain at least one number
- Maximum 128 characters

### 2. Input Validation
- All inputs are validated on the server
- SQL injection patterns are rejected
- XSS patterns are sanitized
- Input length limits are enforced

### 3. Token Security
- Tokens are stored in HTTP-only cookies
- Cookies are only sent over HTTPS (secure flag)
- Tokens have expiration times
- Refresh tokens can be revoked

### 4. Access Control
- Users can only access their own data
- Admins can access all data
- Role-based permissions are enforced

### 5. Database Security
- Passwords are hashed, never stored in plain text
- Prisma ORM prevents SQL injection
- Database connections use SSL

## API Endpoints

### Authentication Endpoints

#### `POST /auth/register`
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "age": 30,
  "sex": "male",
  "diabetes": false,
  "hypertension": false,
  "pregnancy": false,
  "city": "Mumbai"
}
```

**Response:**
- Sets HTTP-only cookies with tokens
- Returns user profile (without password)

#### `POST /auth/login`
Login user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:**
- Sets HTTP-only cookies with tokens
- Returns user profile

#### `POST /auth/logout`
Logout user.

**Response:**
- Clears HTTP-only cookies
- Revokes refresh token

#### `GET /auth/me`
Get current user information.

**Requires:** Authentication

**Response:**
- Returns user profile

#### `POST /auth/refresh`
Refresh access token.

**Response:**
- Sets new access token in HTTP-only cookie

## Security Considerations

### Current Implementation:
✅ SHA-256 password hashing with salt
✅ Input validation and sanitization
✅ HTTP-only cookie token storage
✅ Role-based access control
✅ SQL injection prevention
✅ XSS prevention

### Recommendations for Production:
1. **Password Hashing**: Consider upgrading to bcrypt or Argon2
2. **Rate Limiting**: Add rate limiting to authentication endpoints
3. **CORS**: Configure CORS properly for production
4. **HTTPS**: Ensure all traffic uses HTTPS
5. **Token Rotation**: Implement token rotation for refresh tokens
6. **Audit Logging**: Log all authentication attempts
7. **2FA**: Consider adding two-factor authentication
8. **Password Reset**: Implement secure password reset flow

## Testing Security

### Test Password Hashing:
```python
from api.auth.password import hash_password_for_storage, verify_password_from_storage

password = "TestPassword123"
hashed = hash_password_for_storage(password)
assert verify_password_from_storage(password, hashed) == True
assert verify_password_from_storage("WrongPassword", hashed) == False
```

### Test Input Validation:
```python
from api.auth.validation import validate_chat_input

# Should pass
safe = validate_chat_input("Hello, how are you?")

# Should raise ValueError
try:
    validate_chat_input("'; DROP TABLE users; --")
except ValueError:
    pass  # Expected
```

## Troubleshooting

### Token not found
- Check if cookies are being sent with requests
- Verify `secure=True` is not blocking HTTP (use HTTPS in production)
- Check browser console for cookie errors

### Authentication failed
- Verify JWT_SECRET_KEY is set
- Check token expiration
- Verify user account is active

### Access denied
- Check user role
- Verify user is accessing their own data
- Check if admin role is required

