"""
Check if all required database tables exist in Neon DB
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os

async def check_tables():
    """Check if all required tables exist"""
    # Load environment
    api_dir = Path(__file__).parent.parent
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Try loading from current directory
        load_dotenv(override=True)
    
    # Import database client after loading env
    from database.db_client import db_client
    
    print("=" * 60)
    print("Checking Neon DB Connection and Tables")
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
    
    # Check for required tables
    required_tables = [
        "customers",
        "refresh_tokens",
        "chat_sessions",
        "chat_messages"
    ]
    
    print("Checking for required tables...")
    print()
    
    all_exist = True
    for table in required_tables:
        try:
            # Check if table exists
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                );
            """
            exists = await db_client.fetchval(query, table)
            
            if exists:
                # Get row count
                count_query = f'SELECT COUNT(*) FROM {table}'
                count = await db_client.fetchval(count_query)
                print(f"[OK] Table '{table}' exists ({count} rows)")
            else:
                print(f"[MISSING] Table '{table}' does not exist")
                all_exist = False
        except Exception as e:
            print(f"[ERROR] Error checking table '{table}': {e}")
            all_exist = False
    
    print()
    print("=" * 60)
    
    if all_exist:
        print("[OK] All required tables exist!")
        print()
        print("Your database is ready to use.")
    else:
        print("[WARN] Some tables are missing!")
        print()
        print("You need to create the tables. Run:")
        print("  python scripts/create_tables.py")
    
    print("=" * 60)
    
    await db_client.disconnect()
    return all_exist

if __name__ == "__main__":
    success = asyncio.run(check_tables())
    sys.exit(0 if success else 1)

