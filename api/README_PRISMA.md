# Prisma Setup for Healthcare Chatbot

This project uses Prisma as the ORM for database operations with NeonDB (PostgreSQL).

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variable:**
   ```bash
   export NEON_DB_URL="postgresql://user:password@host:port/database?sslmode=require"
   ```
   Or add it to your `.env` file:
   ```
   NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require
   ```

3. **Generate Prisma client:**
   ```bash
   cd api
   prisma generate --schema prisma/schema.prisma
   ```

4. **Push schema to database:**
   ```bash
   prisma db push --schema prisma/schema.prisma --accept-data-loss
   ```

5. **Start the server:**
   ```bash
   python -m uvicorn main:app --reload
   ```

## Database Models

### Customer
- Stores user profile information
- Fields: id, age, sex, diabetes, hypertension, pregnancy, city, metadata

### ChatSession
- Stores chat session information
- Related to Customer (many-to-one)
- Fields: id, customerId, language, sessionMetadata

### ChatMessage
- Stores individual chat messages
- Related to ChatSession (many-to-one)
- Fields: id, sessionId, role, messageText, language, answer, route, safetyData, facts, citations, metadata

## API Endpoints

### Chat Endpoints
- `POST /chat` - Save chat messages to database
- `POST /voice-chat` - Save voice chat messages to database

### Database Query Endpoints
- `GET /customer/{customer_id}` - Get customer information
- `GET /customer/{customer_id}/sessions` - Get customer sessions
- `GET /session/{session_id}` - Get session with messages
- `GET /session/{session_id}/messages` - Get session messages

## Development

### Create a migration
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
prisma db push --schema prisma/schema.prisma --accept-data-loss
```

## Benefits of Prisma

1. **Type Safety**: Full type safety with Python type hints
2. **Migrations**: Easy database migrations
3. **Relations**: Easy relationship management
4. **Query Builder**: Intuitive query API
5. **Auto-completion**: IDE support with auto-completion
6. **Validation**: Automatic data validation

## Notes

- Prisma uses camelCase for model names in Python (e.g., `chatsession`, `chatmessage`)
- Fields use camelCase as defined in the schema (e.g., `customerId`, `sessionId`)
- All database operations are async
- The Prisma client is automatically connected on application startup

