# Prisma Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variable in `.env` file:**
   ```
   NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require
   ```

3. **Generate Prisma client:**
   ```bash
   cd api
   prisma generate --schema prisma/schema.prisma
   ```

4. **Push schema to database (creates tables):**
   ```bash
   prisma db push --schema prisma/schema.prisma --accept-data-loss
   ```

5. **Start the server:**
   ```bash
   python -m uvicorn main:app --reload
   ```

## What Changed from SQLAlchemy

### ✅ Benefits of Prisma

1. **Better Type Safety**: Full type safety with auto-generated models
2. **Simpler API**: More intuitive query syntax
3. **Better Migrations**: Easy database migrations with `prisma migrate`
4. **Auto-completion**: Full IDE support
5. **Less Boilerplate**: No need for manual SQL queries

### 📝 Key Differences

- **Model Names**: Prisma uses lowercase for client access (e.g., `client.chatsession`, `client.chatmessage`)
- **Field Names**: Uses camelCase as defined in schema (e.g., `customerId`, `sessionId`)
- **Async/Await**: All database operations are async
- **Relations**: Automatic relationship handling with `include`

## Database Models

### Customer
```python
{
    "id": "uuid",
    "age": 30,
    "sex": "male",
    "diabetes": False,
    "hypertension": False,
    "pregnancy": False,
    "city": "Mumbai",
    "metadata": {}
}
```

### ChatSession
```python
{
    "id": "uuid",
    "customerId": "uuid",
    "language": "en",
    "sessionMetadata": {}
}
```

### ChatMessage
```python
{
    "id": "uuid",
    "sessionId": "uuid",
    "role": "user",
    "messageText": "Hello",
    "language": "en",
    "answer": "Hi there!",
    "route": "vector",
    "safetyData": {},
    "facts": [],
    "citations": [],
    "metadata": {}
}
```

## Usage Examples

### Create Customer
```python
customer = await db_service.get_or_create_customer(
    profile_data={
        "age": 30,
        "sex": "male",
        "diabetes": False
    }
)
```

### Create Session
```python
session = await db_service.get_or_create_session(
    customer_id=customer.id,
    language="en"
)
```

### Save Message
```python
message = await db_service.save_chat_message(
    session_id=session.id,
    role="user",
    message_text="Hello",
    language="en"
)
```

### Get Customer Sessions
```python
sessions = await db_service.get_customer_sessions(
    customer_id=customer.id,
    limit=50
)
```

### Get Session Messages
```python
messages = await db_service.get_session_messages(
    session_id=session.id,
    limit=100
)
```

## API Endpoints

All endpoints automatically save to database:

- `POST /chat` - Saves customer, session, and messages
- `POST /voice-chat` - Saves voice chat data
- `GET /customer/{customer_id}` - Get customer info
- `GET /customer/{customer_id}/sessions` - Get customer sessions
- `GET /session/{session_id}` - Get session with messages
- `GET /session/{session_id}/messages` - Get session messages

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

### Import errors
Make sure Prisma client is generated:
```bash
prisma generate --schema prisma/schema.prisma
```

## Next Steps

1. Run migrations for production: `prisma migrate dev --name init`
2. Set up connection pooling if needed
3. Test all endpoints
4. Monitor database performance

## Migration from SQLAlchemy

The old SQLAlchemy code has been replaced with Prisma. All database operations are now async and use Prisma's type-safe API. The API endpoints remain the same, but the underlying database layer uses Prisma.

