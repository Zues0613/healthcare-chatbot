# NeonDB Database Setup

This document describes the NeonDB (PostgreSQL) database integration for storing customer data and chat content.

## Environment Variables

Add the following to your `.env` file:

```
NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require
```

## Database Schema

The database consists of three main tables:

### 1. `customers`
Stores customer/user profile information:
- `id` (String, UUID, Primary Key)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `age` (Integer, nullable)
- `sex` (String, nullable) - male, female, other
- `diabetes` (Boolean)
- `hypertension` (Boolean)
- `pregnancy` (Boolean)
- `city` (String, nullable)
- `metadata` (JSON, nullable)

### 2. `chat_sessions`
Stores chat session information:
- `id` (String, UUID, Primary Key)
- `customer_id` (String, Foreign Key to customers)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `language` (String, nullable) - en, hi, ta, te, kn, ml
- `session_metadata` (JSON, nullable)

### 3. `chat_messages`
Stores individual chat messages:
- `id` (String, UUID, Primary Key)
- `session_id` (String, Foreign Key to chat_sessions)
- `created_at` (DateTime)
- `role` (String) - user, assistant
- `message_text` (Text) - User's message
- `language` (String, nullable)
- `answer` (Text, nullable) - Assistant's response
- `route` (String, nullable) - graph, vector
- `safety_data` (JSON, nullable) - Safety analysis results
- `facts` (JSON, nullable) - Facts array
- `citations` (JSON, nullable) - Citations array
- `metadata` (JSON, nullable) - Additional metadata

## API Endpoints

### Chat Endpoints

#### `POST /chat`
Main chat endpoint that saves customer data and chat messages to the database.

**Request Body:**
```json
{
  "text": "User's message",
  "lang": "en",
  "profile": {
    "age": 30,
    "sex": "male",
    "diabetes": false,
    "hypertension": false,
    "pregnancy": false,
    "city": "Mumbai"
  },
  "customer_id": "optional-existing-customer-id",
  "session_id": "optional-existing-session-id",
  "debug": false
}
```

**Response:**
The response includes `customer_id` and `session_id` in the metadata, which should be used for subsequent requests.

#### `POST /voice-chat`
Voice chat endpoint that also saves to the database. Accepts the same parameters as `/chat` plus:
- `customer_id` (Form field, optional)
- `session_id` (Form field, optional)

### Database Query Endpoints

#### `GET /customer/{customer_id}`
Get customer information by ID.

#### `GET /customer/{customer_id}/sessions`
Get all chat sessions for a customer.

**Query Parameters:**
- `limit` (optional, default: 50) - Maximum number of sessions to return

#### `GET /session/{session_id}`
Get session information with all messages.

#### `GET /session/{session_id}/messages`
Get all messages for a session.

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of messages to return

## Usage Flow

1. **First Request**: Send a chat request without `customer_id` or `session_id`. The system will:
   - Create a new customer record
   - Create a new chat session
   - Save the user message and assistant response
   - Return `customer_id` and `session_id` in the response metadata

2. **Subsequent Requests**: Use the `customer_id` and `session_id` from the previous response:
   - If `customer_id` is provided, the system will update the customer profile if it exists
   - If `session_id` is provided, new messages will be added to that session
   - If `session_id` is not provided, a new session will be created for the customer

## Database Initialization

The database tables are automatically created on application startup if the `NEON_DB_URL` environment variable is set. The initialization happens in the `startup` event handler.

## Error Handling

- If the database is not connected, the application will continue to work but won't save data
- Database errors are logged but don't prevent the chat functionality from working
- All database operations are wrapped in try-catch blocks to prevent failures from affecting the main functionality

## Dependencies

- `sqlalchemy==2.0.25` - SQL toolkit and ORM
- `psycopg2-binary==2.9.9` - PostgreSQL adapter

## Notes

- The database connection uses SSL (sslmode=require) for security
- NullPool is used for connection pooling, which works better with NeonDB
- All database operations are asynchronous-friendly and use context managers for proper resource cleanup

