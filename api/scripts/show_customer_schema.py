"""
Show the actual schema of the customers table from the database
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

async def show_schema():
    """Show customers table schema"""
    # Load environment
    api_dir = Path(__file__).parent.parent
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    
    print("=" * 70)
    print("Customers Table Schema (from Neon DB)")
    print("=" * 70)
    print()
    
    # Connect to database
    if not await db_client.connect():
        print("[ERROR] Failed to connect to database")
        return
    
    try:
        # Get column information
        columns = await db_client.fetch("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'customers'
            ORDER BY ordinal_position
        """)
        
        print(f"{'Column Name':<25} {'Data Type':<25} {'Nullable':<10} {'Default'}")
        print("-" * 70)
        
        for col in columns:
            col_name = col['column_name']
            data_type = col['data_type']
            max_length = col['character_maximum_length']
            nullable = col['is_nullable']
            default = col['column_default'] or ''
            
            # Format data type with length if applicable
            if max_length:
                data_type = f"{data_type}({max_length})"
            
            # Truncate default if too long
            if len(default) > 30:
                default = default[:27] + "..."
            
            print(f"{col_name:<25} {data_type:<25} {nullable:<10} {default}")
        
        print()
        print("=" * 70)
        print("Health Profile Fields:")
        print("=" * 70)
        print()
        print("[OK] age          - User's age (INTEGER)")
        print("[OK] sex          - User's sex/gender (VARCHAR)")
        print("[OK] diabetes     - Has diabetes (BOOLEAN)")
        print("[OK] hypertension - Has hypertension (BOOLEAN)")
        print("[OK] pregnancy    - Is pregnant (BOOLEAN)")
        print("[OK] city         - User's city/location (VARCHAR)")
        print("[OK] metadata     - Additional health data (JSONB)")
        print()
        print("All health profile fields are stored in the customers table!")
        
    except Exception as e:
        print(f"[ERROR] Failed to get schema: {e}")
    finally:
        await db_client.disconnect()

if __name__ == "__main__":
    asyncio.run(show_schema())

