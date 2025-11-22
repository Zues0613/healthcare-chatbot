"""
Standalone script to create the message_feedback table
Uses direct SQL execution without importing database client
Run: python api/scripts/create_message_feedback_table_standalone.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# Load environment variables
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    load_dotenv(override=True)

async def create_message_feedback_table():
    """Create message_feedback table if it doesn't exist"""
    # Get database URL
    database_url = os.getenv("NEON_DB_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ Neither NEON_DB_URL nor DATABASE_URL found in environment variables")
        return False
    
    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database")
        
        # First, check the actual data type of chat_messages.id column
        print("Checking chat_messages.id column type...")
        message_id_type = await conn.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' 
            AND column_name = 'id';
        """)
        
        if not message_id_type:
            print("⚠️  Could not determine chat_messages.id type, defaulting to TEXT")
            message_id_type = 'text'
        
        print(f"Found chat_messages.id type: {message_id_type}")
        
        # Determine the correct type to use for message_id
        message_id_type_lower = message_id_type.lower()
        if message_id_type_lower in ['uuid', 'uniqueidentifier']:
            message_id_col_type = 'UUID'
            use_fk = True
        elif message_id_type_lower in ['text', 'varchar', 'character varying']:
            message_id_col_type = 'TEXT'
            use_fk = False
        else:
            message_id_col_type = 'TEXT'
            use_fk = False
            print(f"⚠️  Unknown type '{message_id_type}', defaulting to TEXT")
        
        print(f"Using {message_id_col_type} for message_id column")
        
        # Check if table already exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'message_feedback'
            );
        """)
        
        if table_exists:
            print("ℹ️  message_feedback table already exists")
            # Check if we need to drop and recreate due to type mismatch
            if not use_fk:
                # Check current message_id type in message_feedback
                current_type = await conn.fetchval("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'message_feedback' 
                    AND column_name = 'message_id';
                """)
                if current_type and current_type.lower() != message_id_type_lower:
                    print(f"⚠️  Type mismatch detected. Current: {current_type}, Expected: {message_id_type}")
                    print("   Dropping and recreating table...")
                    await conn.execute("DROP TABLE IF EXISTS message_feedback CASCADE;")
                    table_exists = False
        
        # Create message_feedback table with correct type
        if not table_exists:
            if use_fk:
                create_table_sql = """
                CREATE TABLE message_feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
                    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
                    feedback VARCHAR(20) NOT NULL CHECK (feedback IN ('positive', 'negative')),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(message_id, customer_id)
                );
                """
            else:
                create_table_sql = f"""
                CREATE TABLE message_feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    message_id {message_id_col_type} NOT NULL,
                    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
                    feedback VARCHAR(20) NOT NULL CHECK (feedback IN ('positive', 'negative')),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(message_id, customer_id)
                );
                """
                print("⚠️  Note: Created without foreign key constraint to chat_messages")
                print("   (type mismatch - chat_messages.id is TEXT, not UUID)")
            
            await conn.execute(create_table_sql)
            print("✅ Created message_feedback table")
        
        # Create indexes (IF NOT EXISTS handles existing indexes)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_message_feedback_message_id ON message_feedback(message_id);",
            "CREATE INDEX IF NOT EXISTS idx_message_feedback_customer_id ON message_feedback(customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_message_feedback_feedback ON message_feedback(feedback);",
        ]
        
        for index_sql in indexes:
            try:
                await conn.execute(index_sql)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"⚠️  Warning creating index: {e}")
        
        print("✅ Created/verified indexes for message_feedback table")
        print("✅ Successfully completed!")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating message_feedback table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_message_feedback_table())
    exit(0 if success else 1)

