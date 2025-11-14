# Neon DB Migration Guide

## Current Status

✅ **Schema Configured**: Your Prisma schema is already configured for Neon DB  
❌ **Migration Not Run**: The database tables haven't been created yet

## Quick Migration Steps

### 1. Install Prisma (if not already installed)

```bash
pip install prisma
```

### 2. Set Your Neon DB Connection String

Create or update your `.env` file in the `api/` directory:

```env
NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require
```

**To get your Neon DB connection string:**
1. Go to your Neon dashboard
2. Select your project
3. Go to "Connection Details"
4. Copy the connection string
5. Make sure it includes `?sslmode=require` at the end

### 3. Run the Migration Script

```bash
cd api
python scripts/migrate_to_neon.py
```

Or manually run:

```bash
cd api

# Generate Prisma client
prisma generate --schema prisma/schema.prisma

# Push schema to database (creates tables)
prisma db push --schema prisma/schema.prisma --accept-data-loss
```

### 4. Verify Migration

The script will create these tables in your Neon DB:
- ✅ `customers` - User accounts with authentication
- ✅ `refresh_tokens` - Authentication tokens
- ✅ `chat_sessions` - Chat session data
- ✅ `chat_messages` - Individual chat messages

## What Gets Created

### Customers Table
- User authentication (email, password hash, role)
- User profile (age, sex, medical conditions)
- Metadata storage

### Refresh Tokens Table
- JWT refresh tokens
- Token expiration and revocation

### Chat Sessions Table
- Session metadata
- Language preferences
- Links to customer

### Chat Messages Table
- User and assistant messages
- Safety data
- Facts and citations
- Response metadata

## Troubleshooting

### Error: "Prisma CLI not found"
```bash
pip install prisma
```

### Error: "NEON_DB_URL not set"
1. Check your `.env` file exists in `api/` directory
2. Verify the connection string format
3. Make sure it includes `?sslmode=require`

### Error: "Connection refused" or "Connection timeout"
1. Check your Neon DB is running
2. Verify your connection string is correct
3. Check if your IP is whitelisted in Neon (if required)
4. Verify SSL mode is set correctly

### Error: "Schema push failed"
- Make sure you have write permissions on the database
- Check if tables already exist (you may need to drop them first)
- Verify the database user has CREATE TABLE permissions

## After Migration

Once migration is complete:
1. ✅ Your database is ready
2. ✅ You can start the FastAPI server
3. ✅ Users can register and login
4. ✅ Chat sessions will be saved to the database

## Production Migrations (Optional)

For production, create proper migrations:

```bash
cd api
prisma migrate dev --name init --schema prisma/schema.prisma
```

This creates migration files that can be version controlled and applied to production databases.

## Need Help?

If you encounter issues:
1. Check the error message carefully
2. Verify your `NEON_DB_URL` is correct
3. Make sure Prisma is installed: `pip install prisma`
4. Check Neon DB dashboard for connection status

