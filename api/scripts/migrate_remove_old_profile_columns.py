"""
Migration script to remove old profile columns from customers table
ONLY RUN THIS AFTER:
1. Migration to customer_profiles is complete
2. Application code has been updated
3. Thorough testing has been done
4. You're confident no data loss will occur
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

# Migration SQL - Remove old profile columns
# Note: Verification is done in Python code, SQL just removes columns
REMOVE_COLUMNS_SQL = """
-- Remove old profile columns (using IF EXISTS to handle already-removed columns)
ALTER TABLE customers 
    DROP COLUMN IF EXISTS age,
    DROP COLUMN IF EXISTS sex,
    DROP COLUMN IF EXISTS diabetes,
    DROP COLUMN IF EXISTS hypertension,
    DROP COLUMN IF EXISTS pregnancy,
    DROP COLUMN IF EXISTS city,
    DROP COLUMN IF EXISTS medical_conditions;
"""

async def remove_old_columns(skip_confirmation: bool = False):
    """Remove old profile columns from customers table"""
    # Load environment
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(override=True)
    
    print("=" * 60)
    print("Remove Old Profile Columns from Customers Table")
    print("=" * 60)
    print()
    print("WARNING: This will permanently remove columns:")
    print("   - age")
    print("   - sex")
    print("   - diabetes")
    print("   - hypertension")
    print("   - pregnancy")
    print("   - city")
    print("   - medical_conditions")
    print()
    print("This action CANNOT be undone!")
    print()
    print("Prerequisites:")
    print("1. Migration to customer_profiles must be complete")
    print("2. Application code must be updated to use customer_profiles")
    print("3. Thorough testing must be done")
    print()
    
    if not skip_confirmation:
        response = input("Are you absolutely sure you want to proceed? (type 'DELETE COLUMNS' to confirm): ")
        if response != "DELETE COLUMNS":
            print("Operation cancelled.")
            return False
    else:
        print("Skipping confirmation (--yes flag provided)")
    
    # Connect to database
    print("\nConnecting to database...")
    if not await db_client.connect():
        print("[ERROR] Failed to connect to database")
        return False
    
    print("[OK] Connected to database")
    print()
    
    # Verify migration - check if old columns still exist first
    print("Verifying migration status...")
    try:
        # Check which old columns still exist
        existing_columns = await db_client.fetch(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'customers' 
            AND column_name IN ('age', 'sex', 'diabetes', 'hypertension', 'pregnancy', 'city', 'medical_conditions')
            """
        )
        
        existing_col_names = [col['column_name'] for col in existing_columns]
        
        if not existing_col_names:
            print("[OK] All old columns have already been removed")
            print("     (No verification needed - columns don't exist)")
        else:
            # Only check for unmigrated data if columns still exist
            # Build dynamic query based on existing columns
            conditions = []
            for col in existing_col_names:
                if col == 'medical_conditions':
                    conditions.append(f"c.{col} IS NOT NULL")
                elif col in ['diabetes', 'hypertension', 'pregnancy']:
                    conditions.append(f"c.{col} = TRUE")
                else:
                    conditions.append(f"c.{col} IS NOT NULL")
            
            if conditions:
                condition_str = " OR ".join(conditions)
                unmigrated = await db_client.fetchval(
                    f"""
                    SELECT COUNT(*) FROM customers c
                    LEFT JOIN customer_profiles cp ON c.id = cp.customer_id
                    WHERE cp.customer_id IS NULL
                    AND ({condition_str})
                    """
                )
                
                if unmigrated > 0:
                    print(f"[ERROR] Found {unmigrated} customers with profile data in old columns")
                    print("Cannot proceed. Please complete migration first.")
                    return False
                
                print(f"[OK] All profile data has been migrated (checked {len(existing_col_names)} existing columns)")
            else:
                print("[OK] No old columns found to verify")
    except Exception as e:
        # If error is about columns not existing, that's fine - they're already removed
        if "does not exist" in str(e) or "column" in str(e).lower():
            print("[OK] Old columns don't exist (already removed or never existed)")
        else:
            print(f"[ERROR] Verification failed: {e}")
            return False
    
    print()
    
    # Remove columns
    print("Removing old columns...")
    try:
        await db_client.execute(REMOVE_COLUMNS_SQL)
        print("[OK] Old columns removed successfully")
        print()
        print("=" * 60)
        print("[OK] Migration completed!")
        print("=" * 60)
    except Exception as e:
        print(f"[ERROR] Failed to remove columns: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    await db_client.disconnect()
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove old profile columns from customers table")
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)"
    )
    args = parser.parse_args()
    
    success = asyncio.run(remove_old_columns(skip_confirmation=args.yes))
    sys.exit(0 if success else 1)

