# Prisma Setup Guide

This guide explains how to set up and use Prisma with NeonDB for the healthcare chatbot.

## Prerequisites

1. Python 3.8+
2. PostgreSQL database (NeonDB)
3. `NEON_DB_URL` environment variable set

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Prisma CLI (if not already installed):
```bash
pip install prisma
```

## Database Setup

### 1. Environment Variables

Add to your `.env` file:
```
NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require
```

### 2. Generate Prisma Client

Generate the Prisma client from the schema:
```bash
cd api
prisma generate --schema prisma/schema.prisma
```

Or use the initialization script:
```bash
python scripts/init_prisma.py
```

### 3. Push Schema to Database

Push the schema to your database (creates tables):
```bash
cd api
prisma db push --schema prisma/schema.prisma
```

### 4. Create Migrations (Optional)

For production, create migrations:
```bash
cd api
prisma migrate dev --name init --schema prisma/schema.prisma
```

## Database Schema

The schema defines three models:

### Customer
- Stores user profile information
- Fields: id, age, sex, diabetes, hypertension, pregnancy, city, metadata

### ChatSession
- Stores chat session information
- Related to Customer (one-to-many)
- Fields: id, customerId, language, sessionMetadata

### ChatMessage
- Stores individual chat messages
- Related to ChatSession (many-to-one)
- Fields: id, sessionId, role, messageText, language, answer, route, safetyData, facts, citations, metadata

## Usage

### In Python Code

```python
from database import prisma_client, db_service

# Connect to database
await prisma_client.connect()

# Create customer
customer = await db_service.get_or_create_customer(
    profile_data={
        "age": 30,
        "sex": "male",
        "diabetes": False,
        "hypertension": False,
    }
)

# Create session
session = await db_service.get_or_create_session(
    customer_id=customer.id,
    language="en"
)

# Save message
message = await db_service.save_chat_message(
    session_id=session.id,
    role="user",
    message_text="Hello",
    language="en"
)

# Disconnect
await prisma_client.disconnect()
```

## API Endpoints

All endpoints are async and use Prisma:

- `POST /chat` - Save chat messages
- `POST /voice-chat` - Save voice chat messages
- `GET /customer/{customer_id}` - Get customer
- `GET /customer/{customer_id}/sessions` - Get customer sessions
- `GET /session/{session_id}` - Get session with messages
- `GET /session/{session_id}/messages` - Get session messages

## Migration Commands

### Create a new migration
```bash
prisma migrate dev --name migration_name --schema prisma/schema.prisma
```

### Apply migrations
```bash
prisma migrate deploy --schema prisma/schema.prisma
```

### Reset database (development only)
```bash
prisma migrate reset --schema prisma/schema.prisma
```

## Troubleshooting

### Prisma client not generated
```bash
prisma generate --schema prisma/schema.prisma
```

### Database connection issues
1. Check `NEON_DB_URL` is set correctly
2. Verify database is accessible
3. Check SSL mode is set (sslmode=require)

### Schema changes not applied
```bash
prisma db push --schema prisma/schema.prisma
```

## Development Workflow

1. Make changes to `prisma/schema.prisma`
2. Generate Prisma client: `prisma generate --schema prisma/schema.prisma`
3. Push schema changes: `prisma db push --schema prisma/schema.prisma`
4. Update code to use new schema
5. Test changes
6. Create migration: `prisma migrate dev --name descriptive_name --schema prisma/schema.prisma`

## Production Deployment

1. Set `NEON_DB_URL` environment variable
2. Run migrations: `prisma migrate deploy --schema prisma/schema.prisma`
3. Ensure Prisma client is generated in build process
4. Start application

## Benefits of Prisma

1. **Type Safety**: Full type safety with Python type hints
2. **Migrations**: Easy database migrations
3. **Relations**: Easy relationship management
4. **Query Builder**: Intuitive query API
5. **Auto-completion**: IDE support with auto-completion
6. **Validation**: Automatic data validation

