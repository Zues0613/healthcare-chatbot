"""
Migration script to add medical_conditions field to customers table
This allows storing multiple medical conditions beyond just diabetes, hypertension, and pregnancy
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

# SQL to add medical_conditions column
MIGRATION_SQL = """
-- Add medical_conditions JSONB column to store array of conditions
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS medical_conditions JSONB DEFAULT '[]'::jsonb;

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_customers_medical_conditions 
ON customers USING GIN (medical_conditions);

-- Migrate existing boolean conditions to the array
-- This preserves existing data
UPDATE customers
SET medical_conditions = (
    SELECT jsonb_agg(condition)
    FROM (
        SELECT 'diabetes' as condition WHERE diabetes = TRUE
        UNION ALL
        SELECT 'hypertension' as condition WHERE hypertension = TRUE
        UNION ALL
        SELECT 'pregnancy' as condition WHERE pregnancy = TRUE
    ) conditions
)
WHERE medical_conditions = '[]'::jsonb 
AND (diabetes = TRUE OR hypertension = TRUE OR pregnancy = TRUE);
"""

async def migrate():
    """Run migration to add medical_conditions field"""
    # Load environment
    api_dir = Path(__file__).parent.parent
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    
    print("=" * 60)
    print("Migration: Add Medical Conditions Support")
    print("=" * 60)
    print()
    print("This migration will:")
    print("1. Add 'medical_conditions' JSONB column to customers table")
    print("2. Create an index for efficient querying")
    print("3. Migrate existing diabetes/hypertension/pregnancy data to the array")
    print()
    
    # Connect to database
    print("Connecting to database...")
    if not await db_client.connect():
        print("[ERROR] Failed to connect to database")
        return False
    
    print("[OK] Connected to database")
    print()
    
    # Check if column already exists
    print("Checking if migration is needed...")
    try:
        column_exists = await db_client.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'customers'
                AND column_name = 'medical_conditions'
            );
        """)
        
        if column_exists:
            print("[INFO] medical_conditions column already exists")
            print("Migration may have already been run.")
            print()
            response = input("Do you want to run the migration anyway? (y/n): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                await db_client.disconnect()
                return True
    except Exception as e:
        print(f"[WARN] Could not check column existence: {e}")
    
    # Run migration
    print()
    print("Running migration...")
    try:
        await db_client.execute(MIGRATION_SQL)
        print("[OK] Migration completed successfully!")
        print()
        
        # Verify migration
        print("Verifying migration...")
        column_exists = await db_client.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'customers'
                AND column_name = 'medical_conditions'
            );
        """)
        
        if column_exists:
            print("[OK] medical_conditions column created")
            
            # Check if any data was migrated
            migrated_count = await db_client.fetchval("""
                SELECT COUNT(*) FROM customers 
                WHERE medical_conditions != '[]'::jsonb
            """)
            print(f"[OK] Found {migrated_count} customers with conditions migrated")
        else:
            print("[ERROR] Column was not created")
            return False
        
        print()
        print("=" * 60)
        print("[OK] Migration complete!")
        print("=" * 60)
        print()
        print("The customers table now supports multiple medical conditions.")
        print("You can store conditions like: ['diabetes', 'asthma', 'heart_disease', ...]")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        print()
        print("This might be because:")
        print("1. Column already exists with different structure")
        print("2. Database permission issue")
        print("3. Connection issue")
        return False
    
    await db_client.disconnect()
    return True

if __name__ == "__main__":
    success = asyncio.run(migrate())
    sys.exit(0 if success else 1)

