"""
Script to create the message_feedback table if it doesn't exist
Run this if you see errors about message_feedback table not existing
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in project root
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    # Try loading from current directory
    load_dotenv(override=True)

# Add parent directory to path to import database client (same as create_tables.py)
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_client import db_client

async def create_message_feedback_table():
    """Create message_feedback table if it doesn't exist"""
    try:
        print("Connecting to database...")
        if not await db_client.connect():
            print("❌ Failed to connect to database")
            print("   Please check your NEON_DB_URL in .env file")
            return False
        
        print("✅ Connected to database")
        
        # Check the actual data types of both referenced columns
        print("Checking column types...")
        
        # Check chat_messages.id type
        message_id_type = await db_client.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages' 
            AND column_name = 'id';
        """)
        
        if not message_id_type:
            print("⚠️  Could not determine chat_messages.id type, defaulting to TEXT")
            message_id_type = 'text'
        
        print(f"Found chat_messages.id type: {message_id_type}")
        
        # Check customers.id type
        customer_id_type = await db_client.fetchval("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'customers' 
            AND column_name = 'id';
        """)
        
        if not customer_id_type:
            print("⚠️  Could not determine customers.id type, defaulting to TEXT")
            customer_id_type = 'text'
        
        print(f"Found customers.id type: {customer_id_type}")
        
        # Determine the correct types to use
        message_id_type_lower = message_id_type.lower()
        customer_id_type_lower = customer_id_type.lower()
        
        # Determine message_id column type - PostgreSQL supports FK with TEXT when types match
        if message_id_type_lower in ['uuid', 'uniqueidentifier']:
            message_id_col_type = 'UUID'
            use_message_fk = True
        elif message_id_type_lower in ['text', 'varchar', 'character varying']:
            # Use the exact type name from the database to ensure FK compatibility
            message_id_col_type = message_id_type.upper()  # Use exact type (TEXT, VARCHAR, etc.)
            use_message_fk = True  # Can create FK with TEXT if types match exactly
        else:
            message_id_col_type = 'TEXT'
            use_message_fk = False
            print(f"[WARNING] Unknown type '{message_id_type}' for message_id, defaulting to TEXT without FK")
        
        # Determine customer_id column type - PostgreSQL supports FK with TEXT when types match
        if customer_id_type_lower in ['uuid', 'uniqueidentifier']:
            customer_id_col_type = 'UUID'
            use_customer_fk = True
        elif customer_id_type_lower in ['text', 'varchar', 'character varying']:
            # Use the exact type name from the database to ensure FK compatibility
            customer_id_col_type = customer_id_type.upper()  # Use exact type (TEXT, VARCHAR, etc.)
            use_customer_fk = True  # Can create FK with TEXT if types match exactly
        else:
            customer_id_col_type = 'TEXT'
            use_customer_fk = False
            print(f"[WARNING] Unknown type '{customer_id_type}' for customer_id, defaulting to TEXT without FK")
        
        print(f"Using {message_id_col_type} for message_id column")
        print(f"Using {customer_id_col_type} for customer_id column")
        
        # Check if table already exists and if we need to recreate it
        table_exists = await db_client.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'message_feedback'
            );
        """)
        
        if table_exists:
            print("ℹ️  message_feedback table already exists, checking structure...")
            # Check current message_id type
            current_type = await db_client.fetchval("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'message_feedback' 
                AND column_name = 'message_id';
            """)
            
            if current_type:
                current_type_lower = current_type.lower()
                expected_type_lower = message_id_type.lower()
                
                # Also check customer_id type
                current_customer_id_type = await db_client.fetchval("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'message_feedback' 
                    AND column_name = 'customer_id';
                """)
                
                current_customer_id_type_lower = current_customer_id_type.lower() if current_customer_id_type else None
                
                # Check if types match
                message_type_match = current_type_lower == message_id_type_lower
                customer_type_match = current_customer_id_type_lower == customer_id_type_lower if current_customer_id_type else False
                
                # Check if FK constraints exist
                fk_count = await db_client.fetchval("""
                    SELECT COUNT(*) 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'message_feedback' 
                    AND constraint_type = 'FOREIGN KEY';
                """)
                
                needs_recreate = False
                if not message_type_match or not customer_type_match:
                    needs_recreate = True
                    if not message_type_match:
                        print(f"[WARNING] message_id type mismatch: table has {current_type}, but chat_messages.id is {message_id_type}")
                    if current_customer_id_type and not customer_type_match:
                        print(f"[WARNING] customer_id type mismatch: table has {current_customer_id_type}, but customers.id is {customer_id_type}")
                
                if fk_count is None or fk_count < 2:
                    needs_recreate = True
                    print(f"[WARNING] Table exists but has {fk_count or 0} FK constraints (expected 2)")
                    print("[INFO] Table will be recreated WITH foreign key constraints")
                
                if needs_recreate:
                    print("[INFO] Dropping and recreating table with FK constraints...")
                    await db_client.execute("DROP TABLE IF EXISTS message_feedback CASCADE;")
                    table_exists = False
                else:
                    print(f"[OK] Table structure is correct (message_id is {current_type}, has {fk_count} FK constraints)")
                    # Just create indexes if they don't exist
                    indexes = [
                        "CREATE INDEX IF NOT EXISTS idx_message_feedback_message_id ON message_feedback(message_id);",
                        "CREATE INDEX IF NOT EXISTS idx_message_feedback_customer_id ON message_feedback(customer_id);",
                        "CREATE INDEX IF NOT EXISTS idx_message_feedback_feedback ON message_feedback(feedback);",
                    ]
                    for index_sql in indexes:
                        try:
                            await db_client.execute(index_sql)
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                print(f"[WARNING] Warning creating index: {e}")
                    print("[OK] All indexes verified")
                    return True
        
        # Create message_feedback table with correct types
        if not table_exists:
            # Build the CREATE TABLE statement with FK constraints
            # PostgreSQL supports FK constraints with TEXT types - types just need to match exactly
            # Since both parent tables use TEXT and we're using the same type, we can create FK constraints
            
            print(f"[INFO] Creating table WITH foreign key constraints (types match: TEXT -> TEXT)...")
            
            # Use FK constraints since types match (both are TEXT)
            message_id_def = f"message_id {message_id_col_type} NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE"
            customer_id_def = f"customer_id {customer_id_col_type} NOT NULL REFERENCES customers(id) ON DELETE CASCADE"
            
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS message_feedback (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                {message_id_def},
                {customer_id_def},
                feedback VARCHAR(20) NOT NULL CHECK (feedback IN ('positive', 'negative')),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(message_id, customer_id)
            );
            """
            
            await db_client.execute(create_table_sql)
            print("[OK] Created message_feedback table WITH foreign key constraints!")
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_message_feedback_message_id ON message_feedback(message_id);",
                "CREATE INDEX IF NOT EXISTS idx_message_feedback_customer_id ON message_feedback(customer_id);",
                "CREATE INDEX IF NOT EXISTS idx_message_feedback_feedback ON message_feedback(feedback);",
            ]
            
            for index_sql in indexes:
                await db_client.execute(index_sql)
            
            print("✅ Created indexes for message_feedback table")
            print("✅ Successfully created message_feedback table and indexes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating message_feedback table: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up connection
        await db_client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(create_message_feedback_table())
    exit(0 if success else 1)

