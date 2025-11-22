"""
Migration script to normalize customer profile data into a separate table
This ensures no data loss by:
1. Creating customer_profiles table
2. Migrating all existing data
3. Verifying data integrity
4. Keeping old columns temporarily for safety
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

# Migration SQL template - will be customized based on customers.id type
# Note: Use {{ and }} to escape curly braces in SQL, and {customer_id_type} for the placeholder
def build_migration_sql(customer_id_type: str) -> str:
    """Build migration SQL with correct customer_id type"""
    return f"""
-- Step 1: Create customer_profiles table
CREATE TABLE IF NOT EXISTS customer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id {customer_id_type} NOT NULL UNIQUE REFERENCES customers(id) ON DELETE CASCADE,
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

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_customer_profiles_customer_id ON customer_profiles(customer_id);

-- Step 2: Migrate existing data from customers table to customer_profiles
-- Only migrate customers that have profile data
INSERT INTO customer_profiles (
    customer_id,
    age,
    sex,
    diabetes,
    hypertension,
    pregnancy,
    city,
    medical_conditions,
    created_at,
    updated_at
)
SELECT 
    id as customer_id,
    age,
    sex,
    COALESCE(diabetes, FALSE) as diabetes,
    COALESCE(hypertension, FALSE) as hypertension,
    COALESCE(pregnancy, FALSE) as pregnancy,
    city,
    COALESCE(
        CASE 
            WHEN metadata IS NOT NULL AND metadata::text != 'null' AND metadata::text != '{{}}'
            THEN metadata->'medical_conditions'
            ELSE '[]'::jsonb
        END,
        '[]'::jsonb
    ) as medical_conditions,
    created_at,
    updated_at
FROM customers
WHERE 
    age IS NOT NULL 
    OR sex IS NOT NULL 
    OR diabetes = TRUE 
    OR hypertension = TRUE 
    OR pregnancy = TRUE 
    OR city IS NOT NULL
    OR (metadata IS NOT NULL AND metadata::text != 'null' AND metadata::text != '{{}}' AND metadata->'medical_conditions' IS NOT NULL)
ON CONFLICT (customer_id) DO NOTHING;

-- Step 3: Verify data migration
-- This query will show any customers with profile data that weren't migrated
DO $$
DECLARE
    unmigrated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO unmigrated_count
    FROM customers c
    LEFT JOIN customer_profiles cp ON c.id = cp.customer_id
    WHERE cp.customer_id IS NULL
    AND (
        c.age IS NOT NULL 
        OR c.sex IS NOT NULL 
        OR c.diabetes = TRUE 
        OR c.hypertension = TRUE 
        OR c.pregnancy = TRUE 
        OR c.city IS NOT NULL
        OR (c.metadata IS NOT NULL AND c.metadata::text != 'null' AND c.metadata::text != '{{}}' AND c.metadata->'medical_conditions' IS NOT NULL)
    );
    
    IF unmigrated_count > 0 THEN
        RAISE EXCEPTION 'Migration verification failed: % customers with profile data were not migrated', unmigrated_count;
    END IF;
    
    RAISE NOTICE 'Migration verification passed: All profile data migrated successfully';
END $$;
"""

async def migrate():
    """Run the migration"""
    # Load environment
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(override=True)
    
    print("=" * 60)
    print("Customer Profile Normalization Migration")
    print("=" * 60)
    print()
    print("This migration will:")
    print("1. Create customer_profiles table")
    print("2. Migrate all existing profile data")
    print("3. Verify data integrity")
    print("4. Keep old columns in customers table (for safety)")
    print()
    
    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() != "yes":
        print("Migration cancelled.")
        return False
    
    # Connect to database
    print("\nConnecting to database...")
    if not await db_client.connect():
        print("[ERROR] Failed to connect to database")
        print("Please check your NEON_DB_URL in .env file")
        return False
    
    print("[OK] Successfully connected to PostgreSQL database")
    print()
    
    # Check current state
    print("Checking current state...")
    try:
        # Check the actual data type of customers.id column
        id_type = await db_client.fetchval(
            """
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'customers' 
            AND column_name = 'id'
            """
        )
        print(f"  Detected customers.id type: {id_type}")
        
        # Use the same type for customer_id in customer_profiles
        # Handle both 'text' and 'uuid' types properly
        if not id_type:
            customer_id_type = 'UUID'
        elif id_type.lower() == 'text' or id_type.lower() == 'character varying':
            customer_id_type = 'TEXT'
        elif id_type.lower() == 'uuid':
            customer_id_type = 'UUID'
        else:
            # Use the detected type as-is (uppercase for SQL)
            customer_id_type = id_type.upper()
        
        print(f"  Using customer_id type: {customer_id_type}")
        
        # Count customers with profile data
        customers_with_profile = await db_client.fetchval(
            """
            SELECT COUNT(*) FROM customers
            WHERE age IS NOT NULL 
            OR sex IS NOT NULL 
            OR diabetes = TRUE 
            OR hypertension = TRUE 
            OR pregnancy = TRUE 
            OR city IS NOT NULL
            OR (metadata IS NOT NULL AND metadata::text != 'null' AND metadata::text != '{}' AND metadata->'medical_conditions' IS NOT NULL)
            """
        )
        print(f"  Found {customers_with_profile} customers with profile data")
        
        # Check if customer_profiles table already exists
        table_exists = await db_client.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'customer_profiles'
            )
            """
        )
        
        if table_exists:
            existing_profiles = await db_client.fetchval("SELECT COUNT(*) FROM customer_profiles")
            print(f"  customer_profiles table already exists with {existing_profiles} records")
            response = input("\nTable already exists. Do you want to continue? (yes/no): ")
            if response.lower() != "yes":
                print("Migration cancelled.")
                return False
    except Exception as e:
        print(f"[ERROR] Failed to check current state: {e}")
        return False
    
    print()
    
    # Build migration SQL with correct customer_id type
    print("Building migration SQL...")
    migration_sql = build_migration_sql(customer_id_type)
    
    # Run migration
    print("Running migration...")
    try:
        await db_client.execute(migration_sql)
        print("[OK] Migration SQL executed successfully")
        print()
        
        # Verify migration
        print("Verifying migration...")
        migrated_count = await db_client.fetchval("SELECT COUNT(*) FROM customer_profiles")
        print(f"  [OK] Migrated {migrated_count} customer profiles")
        
        # Double-check: ensure all customers with profile data have profiles
        unmigrated = await db_client.fetchval(
            """
            SELECT COUNT(*) FROM customers c
            LEFT JOIN customer_profiles cp ON c.id = cp.customer_id
            WHERE cp.customer_id IS NULL
            AND (
                c.age IS NOT NULL 
                OR c.sex IS NOT NULL 
                OR c.diabetes = TRUE 
                OR c.hypertension = TRUE 
                OR c.pregnancy = TRUE 
                OR c.city IS NOT NULL
                OR (c.metadata IS NOT NULL AND c.metadata::text != 'null' AND c.metadata::text != '{}' AND c.metadata->'medical_conditions' IS NOT NULL)
            )
            """
        )
        
        if unmigrated > 0:
            print(f"  [WARNING] {unmigrated} customers with profile data were not migrated")
            print("  This might be expected if they have NULL values only")
        else:
            print("  [OK] All customers with profile data have been migrated")
        
        print()
        print("=" * 60)
        print("[OK] Migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Update application code to use customer_profiles table")
        print("2. Test thoroughly")
        print("3. After verification, you can remove old columns from customers table")
        print("   (age, sex, diabetes, hypertension, pregnancy, city)")
        print("   using: api/scripts/migrate_remove_old_profile_columns.py")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    await db_client.disconnect()
    return True

if __name__ == "__main__":
    success = asyncio.run(migrate())
    sys.exit(0 if success else 1)

