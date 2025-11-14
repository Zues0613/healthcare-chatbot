"""
Create admin user for the healthcare chatbot
This script creates an admin user with the specified credentials
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

# Load environment FIRST before importing modules that use env vars
from dotenv import load_dotenv
env_file = api_dir / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    load_dotenv(override=True)

# Now import modules that use environment variables
from database.db_client import db_client
from database.service import DatabaseService
from auth.password import hash_password_for_storage
import uuid

async def create_admin():
    """Create admin user"""
    # Environment already loaded at module level
    
    print("=" * 60)
    print("Create Admin User")
    print("=" * 60)
    print()
    
    # Connect to database
    print("Connecting to database...")
    if not await db_client.connect():
        print("[ERROR] Failed to connect to database")
        print("Please check your NEON_DB_URL in .env file")
        return False
    
    print("[OK] Connected to database")
    print()
    
    # Admin credentials
    ADMIN_EMAIL = "admin@wellness.com"
    ADMIN_PASSWORD = "admin123"  # Change this in production!
    
    print("Admin Credentials:")
    print(f"  Email: {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print()
    print("[WARNING] IMPORTANT: Change the password in production!")
    print()
    
    # Check if admin already exists
    existing = await DatabaseService.get_customer_by_email(ADMIN_EMAIL)
    
    if existing:
        print(f"[INFO] Admin user already exists: {ADMIN_EMAIL}")
        response = input("Do you want to update the password? (y/n): ")
        if response.lower() == 'y':
            # Update password
            password_hash = hash_password_for_storage(ADMIN_PASSWORD)
            await db_client.execute(
                "UPDATE customers SET password_hash = $1, role = 'admin' WHERE email = $2",
                password_hash, ADMIN_EMAIL
            )
            print("[OK] Admin password updated")
        else:
            print("Skipping password update")
        await db_client.disconnect()
        return True
    
    # Create admin user
    print("Creating admin user...")
    try:
        password_hash = hash_password_for_storage(ADMIN_PASSWORD)
        customer_id = str(uuid.uuid4())
        
        customer = await db_client.fetchrow(
            """
            INSERT INTO customers (
                id, email, password_hash, role, is_active, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            RETURNING *
            """,
            customer_id, ADMIN_EMAIL, password_hash, "admin", True
        )
        
        if customer:
            print("[OK] Admin user created successfully!")
            print()
            print("Admin Details:")
            print(f"  ID: {customer['id']}")
            print(f"  Email: {customer['email']}")
            print(f"  Role: {customer['role']}")
            print()
            print("=" * 60)
            print("[OK] Admin user ready!")
            print("=" * 60)
            print()
            print("You can now login with:")
            print(f"  Email: {ADMIN_EMAIL}")
            print(f"  Password: {ADMIN_PASSWORD}")
            print()
            print("[WARNING] Remember to change the password in production!")
        else:
            print("[ERROR] Failed to create admin user")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db_client.disconnect()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(create_admin())
    sys.exit(0 if success else 1)
