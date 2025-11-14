# JWT Secret Key Guide

## What is a JWT Secret Key?

The JWT (JSON Web Token) secret key is used to **sign and verify** authentication tokens in your application. It's critical for security because:

- **If someone gets your secret key**, they can forge tokens and impersonate any user
- **If you change the key**, all existing tokens become invalid
- **The key must be kept secret** - never commit it to version control

## Recommended Key Specifications

### For HS256 Algorithm (Current Setup)

- **Minimum Length**: 32 characters (256 bits)
- **Recommended Length**: 64 bytes (512 bits) = ~86 characters when base64 encoded
- **Character Set**: URL-safe base64 characters (A-Z, a-z, 0-9, -, _)
- **Randomness**: Must be cryptographically random

### Why 64 bytes?

- HS256 uses HMAC-SHA256, which works best with keys at least as long as the hash output (32 bytes)
- Using 64 bytes (512 bits) provides extra security margin
- This is the industry standard for production applications

## How to Generate a Secure Key

### Option 1: Use the Provided Script (Recommended)

```bash
cd api
python scripts/generate_jwt_secret.py
```

This will generate a secure 86-character key and display it.

### Option 2: Generate Using Python Directly

```python
import secrets
key = secrets.token_urlsafe(64)
print(key)
```

### Option 3: Generate Using OpenSSL (Command Line)

```bash
openssl rand -base64 64
```

### Option 4: Generate Using PowerShell (Windows)

```powershell
[Convert]::ToBase64String((1..64 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

## Best Practices

### ✅ DO:

1. **Generate a unique key for each environment**
   - Development: `JWT_SECRET_KEY_DEV`
   - Staging: `JWT_SECRET_KEY_STAGING`
   - Production: `JWT_SECRET_KEY_PROD`

2. **Store securely**
   - Use environment variables (`.env` file)
   - Never commit to Git (add `.env` to `.gitignore`)
   - Use secret management services in production (AWS Secrets Manager, Azure Key Vault, etc.)

3. **Use long, random keys**
   - Minimum 32 characters
   - Recommended 64+ characters
   - Use cryptographically secure random generation

4. **Rotate keys periodically**
   - Change keys every 6-12 months
   - Have a migration plan (users will need to re-login)

5. **Keep backups securely**
   - Store encrypted backups in secure locations
   - Document where keys are stored (for team access)

### ❌ DON'T:

1. **Don't use simple passwords**
   - ❌ `"my-secret-key-123"`
   - ❌ `"password"`
   - ❌ `"jwt-secret-key"`

2. **Don't reuse keys**
   - ❌ Same key for dev and production
   - ❌ Same key across different projects

3. **Don't commit to version control**
   - ❌ Never push `.env` files with real keys
   - ❌ Don't hardcode in source code
   - ❌ Don't share in chat/email

4. **Don't use predictable patterns**
   - ❌ `"secret-key-1"`, `"secret-key-2"`
   - ❌ Dates, names, or dictionary words

## Example Keys (DO NOT USE THESE - Generate Your Own!)

These are examples of what a good key looks like:

```
Good (86 characters):
KlWcF-TxjfApKCgoNbue_w2_KzozD9E1u2RYjgxnFswfS6M1NFm-xOqhVk8FwKHyTvZiRWvxa7UZiAGe-nvxng

Good (64 characters):
aB3dEf9gHiJkLmNoPqRsTuVwXyZ1234567890AbCdEfGhIjKlMnOpQrStUvWxYz

Bad (too short):
my-secret-key

Bad (predictable):
jwt-secret-2024
```

## Setting Up Your Key

### 1. Generate a Key

```bash
cd api
python scripts/generate_jwt_secret.py
```

### 2. Add to `.env` File

Open `api/.env` and add:

```env
JWT_SECRET_KEY=your-generated-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 3. Verify It's Working

Start your server and check the logs. You should NOT see:
```
WARNING: JWT_SECRET_KEY not set, using generated key...
```

If you see this warning, your key isn't being loaded correctly.

## Security Checklist

- [ ] Generated a unique, random key (64+ characters)
- [ ] Added key to `.env` file (not committed to Git)
- [ ] Verified `.env` is in `.gitignore`
- [ ] Using different keys for dev/staging/production
- [ ] Key is stored securely (not in code, not in chat)
- [ ] Team members know where to find the key (secure location)
- [ ] Have a plan for key rotation

## What Happens If Your Key is Compromised?

1. **Immediately regenerate** a new key
2. **Update** the `.env` file with the new key
3. **Restart** the server
4. **All existing tokens** will be invalidated
5. **Users will need to log in again**

This is why it's critical to keep the key secret!

## Current Implementation

Your application uses the key like this:

```python
# From api/auth/jwt.py
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    # Falls back to auto-generated key (not recommended for production)
    JWT_SECRET_KEY = secrets.token_urlsafe(32)
    logger.warning("JWT_SECRET_KEY not set, using generated key...")
```

**Always set `JWT_SECRET_KEY` in your `.env` file for production!**

## Questions?

- **Q: Can I use the same key for multiple servers?**
  - A: Yes, if they're in the same environment (e.g., multiple production servers). But use different keys for different environments.

- **Q: How often should I rotate the key?**
  - A: Every 6-12 months, or immediately if compromised.

- **Q: What if I lose the key?**
  - A: Generate a new one. All users will need to log in again.

- **Q: Can I use a shorter key?**
  - A: Minimum 32 characters is acceptable, but 64+ is recommended for better security.

