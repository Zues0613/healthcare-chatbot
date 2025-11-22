"""
Create all required database tables in Neon DB
This script creates the tables if they don't exist
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

# SQL to create all tables
CREATE_TABLES_SQL = """
-- Create customers table (normalized - only auth and account info)
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(129) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMP,
    metadata JSONB
);

-- Create indexes for customers
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_role ON customers(role);

-- Create customer_profiles table (normalized - profile data separate from auth)
CREATE TABLE IF NOT EXISTS customer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL UNIQUE REFERENCES customers(id) ON DELETE CASCADE,
    age INTEGER,
    sex VARCHAR(20),
    diabetes BOOLEAN NOT NULL DEFAULT FALSE,
    hypertension BOOLEAN NOT NULL DEFAULT FALSE,
    pregnancy BOOLEAN NOT NULL DEFAULT FALSE,
    city VARCHAR(100),
    medical_conditions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for customer_profiles
CREATE INDEX IF NOT EXISTS idx_customer_profiles_customer_id ON customer_profiles(customer_id);

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token VARCHAR(255) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revoked BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create indexes for refresh_tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_customer_id ON refresh_tokens(customer_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    language VARCHAR(10),
    session_metadata JSONB
);

-- Create indexes for chat_sessions
CREATE INDEX IF NOT EXISTS idx_chat_sessions_customer_id_created_at ON chat_sessions(customer_id, created_at);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    role VARCHAR(20) NOT NULL,
    message_text TEXT NOT NULL,
    language VARCHAR(10),
    route VARCHAR(20),
    answer TEXT,
    safety_data JSONB,
    facts JSONB,
    citations JSONB,
    metadata JSONB
);

-- Create indexes for chat_messages
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id_created_at ON chat_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role);

-- Create message_feedback table
CREATE TABLE IF NOT EXISTS message_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    feedback VARCHAR(20) NOT NULL CHECK (feedback IN ('positive', 'negative')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(message_id, customer_id) -- One feedback per user per message
);

-- Create indexes for message_feedback
CREATE INDEX IF NOT EXISTS idx_message_feedback_message_id ON message_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_message_feedback_customer_id ON message_feedback(customer_id);
CREATE INDEX IF NOT EXISTS idx_message_feedback_feedback ON message_feedback(feedback);
"""

async def create_tables():
    """Create all required tables"""
    # Load environment
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Try loading from current directory
        load_dotenv(override=True)
    
    print("=" * 60)
    print("Creating Database Tables in Neon DB")
    print("=" * 60)
    print()
    
    # Connect to database
    print("Connecting to database...")
    if not await db_client.connect():
        print("[ERROR] Failed to connect to database")
        print("Please check your NEON_DB_URL in .env file")
        return False
    
    print("[OK] Successfully connected to PostgreSQL database")
    print()
    
    # Create tables
    print("Creating tables...")
    try:
        # Execute the SQL to create all tables
        await db_client.execute(CREATE_TABLES_SQL)
        print("[OK] All tables created successfully!")
        print()
        
        # Verify tables were created
        print("Verifying tables...")
        required_tables = ["customers", "customer_profiles", "refresh_tokens", "chat_sessions", "chat_messages", "message_feedback"]
        for table in required_tables:
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                );
            """
            exists = await db_client.fetchval(query, table)
            if exists:
                print(f"  [OK] Table '{table}' exists")
            else:
                print(f"  [ERROR] Table '{table}' was not created")
        
        print()
        print("=" * 60)
        print("[OK] Database setup complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        print()
        print("This might be because:")
        print("1. Tables already exist")
        print("2. Database connection issue")
        print("3. Permission issue")
        return False
    
    await db_client.disconnect()
    return True

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)

