#!/usr/bin/env python3
"""
Script to create an admin user
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from auth.service import auth_service
from database import prisma_client


async def create_admin():
    """Create an admin user"""
    # Connect to database
    await prisma_client.connect()
    
    if not prisma_client.is_connected():
        print("ERROR: Could not connect to database")
        print("Make sure NEON_DB_URL is set in your .env file")
        sys.exit(1)
    
    # Get admin details
    print("Creating admin user...")
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()
    
    if not email or not password:
        print("ERROR: Email and password are required")
        sys.exit(1)
    
    # Create admin user
    user = await auth_service.register_user(
        email=email,
        password=password,
        role="admin"
    )
    
    if user:
        print(f"✅ Admin user created successfully!")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Role: {user['role']}")
    else:
        print("ERROR: Failed to create admin user")
        print("User may already exist")
        sys.exit(1)
    
    await prisma_client.disconnect()


if __name__ == "__main__":
    asyncio.run(create_admin())

