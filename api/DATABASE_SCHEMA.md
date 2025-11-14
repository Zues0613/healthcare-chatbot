# Database Schema Documentation

## Customers Table Schema

The `customers` table stores user authentication information and health profile data.

### Table Structure

```sql
CREATE TABLE customers (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Authentication Fields
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(129) NOT NULL,  -- SHA-256 hash (64) + : + salt (64) = 129 chars
    role VARCHAR(20) NOT NULL DEFAULT 'user',  -- user, admin, doctor, etc.
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP,
    
    -- Health Profile Fields
    age INTEGER,                    -- User's age
    sex VARCHAR(20),                -- male, female, other
    diabetes BOOLEAN NOT NULL DEFAULT FALSE,
    hypertension BOOLEAN NOT NULL DEFAULT FALSE,
    pregnancy BOOLEAN NOT NULL DEFAULT FALSE,
    city VARCHAR(100),              -- User's city/location
    
    -- Additional Data
    metadata JSONB                  -- Flexible JSON field for extra profile data
);
```

### Health Profile Fields

**Yes, the customers table stores health profile details!** Here's what's stored:

#### Basic Demographics
- **`age`** (INTEGER, nullable)
  - User's age in years
  - Used for age-appropriate health recommendations
  - Example: `25`, `45`, `null`

- **`sex`** (VARCHAR(20), nullable)
  - User's sex/gender
  - Values: `"male"`, `"female"`, `"other"`, or `null`
  - Used for sex-specific health guidance

- **`city`** (VARCHAR(100), nullable)
  - User's city/location
  - Used for location-based provider recommendations
  - Example: `"Mumbai"`, `"Delhi"`, `null`

#### Medical Conditions
- **`diabetes`** (BOOLEAN, default: FALSE)
  - Whether user has diabetes
  - Used to filter contraindications and provide diabetes-aware responses
  - Example: `true`, `false`

- **`hypertension`** (BOOLEAN, default: FALSE)
  - Whether user has hypertension (high blood pressure)
  - Used to filter contraindications and provide hypertension-aware responses
  - Example: `true`, `false`

- **`pregnancy`** (BOOLEAN, default: FALSE)
  - Whether user is pregnant
  - Critical for filtering unsafe medications and providing pregnancy-specific guidance
  - Example: `true`, `false`

#### Flexible Storage
- **`metadata`** (JSONB, nullable)
  - Flexible JSON field for additional profile data
  - Can store any extra health information
  - Example: `{"allergies": ["penicillin"], "medications": ["aspirin"], "blood_type": "O+"}`

### How Health Profile is Used

1. **Personalized Responses**: The chatbot uses profile data to provide personalized health advice
   - Age-based recommendations (pediatric vs adult)
   - Sex-specific guidance
   - Condition-aware responses (diabetes, hypertension, pregnancy)

2. **Safety Filtering**: Profile data is used to filter unsafe recommendations
   - Pregnancy → filters out NSAIDs, alcohol, smoking
   - Diabetes → filters out high-sugar recommendations
   - Hypertension → filters out high-sodium recommendations

3. **Provider Recommendations**: City is used to find nearby healthcare providers

### Example Customer Record

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-14T10:30:00Z",
  "updated_at": "2025-01-14T10:30:00Z",
  "email": "user@example.com",
  "password_hash": "abc123...:salt456...",
  "role": "user",
  "is_active": true,
  "last_login": "2025-01-14T19:28:00Z",
  "age": 35,
  "sex": "female",
  "diabetes": false,
  "hypertension": true,
  "pregnancy": false,
  "city": "Mumbai",
  "metadata": {
    "allergies": ["penicillin"],
    "preferred_language": "hi"
  }
}
```

### Profile Update Flow

When a user updates their profile (via `/chat` or `/voice-chat` endpoints):

1. Profile data is sent in the request: `{age: 35, sex: "female", diabetes: false, ...}`
2. The system updates the `customers` table with the new values
3. Future chat responses use the updated profile for personalization

### Related Tables

- **`chat_sessions`**: Links to customer via `customer_id`
- **`chat_messages`**: Links to sessions, which link to customers
- **`refresh_tokens`**: Links to customer via `customer_id` for authentication

### Indexes

For performance, the following indexes are created:
- `idx_customers_email` - Fast email lookups (for login)
- `idx_customers_role` - Fast role-based queries (for admin features)

