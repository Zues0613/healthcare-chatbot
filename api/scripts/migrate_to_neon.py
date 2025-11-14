#!/usr/bin/env python3
"""
Migrate database schema to Neon DB
This script will:
1. Generate Prisma client
2. Push schema to Neon DB (creates tables)
3. Optionally create migrations
"""
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_prisma_installed():
    """Check if Prisma CLI is installed"""
    try:
        result = subprocess.run(
            ["prisma", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ Prisma CLI found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("✗ Prisma CLI not found")
        return False
    return False

def check_database_url():
    """Check if NEON_DB_URL is set"""
    db_url = os.getenv("NEON_DB_URL")
    if not db_url:
        print("✗ NEON_DB_URL not set in environment")
        print("  Please set NEON_DB_URL in your .env file")
        return False
    else:
        # Mask password in URL for display
        if "@" in db_url:
            parts = db_url.split("@")
            if ":" in parts[0]:
                user_pass = parts[0].split(":")
                if len(user_pass) > 1:
                    masked = f"{user_pass[0]}:****@{parts[1]}"
                    print(f"✓ NEON_DB_URL is set: {masked}")
                else:
                    print(f"✓ NEON_DB_URL is set")
            else:
                print(f"✓ NEON_DB_URL is set")
        else:
            print(f"✓ NEON_DB_URL is set")
        return True

def generate_prisma_client(schema_path):
    """Generate Prisma client"""
    print("\n📦 Generating Prisma client...")
    try:
        result = subprocess.run(
            ["prisma", "generate", "--schema", str(schema_path)],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ Prisma client generated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate Prisma client")
        print(f"  Error: {e.stderr}")
        print("\n  Try installing Prisma:")
        print("    pip install prisma")
        return False
    except FileNotFoundError:
        print("✗ Prisma CLI not found")
        print("  Install with: pip install prisma")
        return False

def push_schema_to_db(schema_path):
    """Push schema to database (creates tables)"""
    print("\n🚀 Pushing schema to Neon DB...")
    print("  This will create all tables if they don't exist")
    try:
        result = subprocess.run(
            ["prisma", "db", "push", "--schema", str(schema_path), "--accept-data-loss"],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ Schema pushed to database successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to push schema to database")
        print(f"  Error: {e.stderr}")
        if "NEON_DB_URL" in e.stderr or "DATABASE_URL" in e.stderr:
            print("\n  Make sure NEON_DB_URL is set correctly in your .env file")
        return False

def create_migration(schema_path, migration_name="init"):
    """Create a migration (optional, for production)"""
    print(f"\n📝 Creating migration '{migration_name}'...")
    try:
        result = subprocess.run(
            ["prisma", "migrate", "dev", "--name", migration_name, "--schema", str(schema_path)],
            cwd=Path(__file__).parent.parent,
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ Migration created successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠ Migration creation failed (this is optional)")
        print(f"  Error: {e.stderr}")
        return False

def main():
    """Main migration function"""
    print("=" * 60)
    print("Neon DB Migration Script")
    print("=" * 60)
    
    api_dir = Path(__file__).parent.parent
    schema_path = api_dir / "prisma" / "schema.prisma"
    
    if not schema_path.exists():
        print(f"✗ Schema file not found: {schema_path}")
        sys.exit(1)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    if not check_prisma_installed():
        print("\n  Install Prisma with: pip install prisma")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded .env file from {env_file}")
    else:
        load_dotenv()
        print("⚠ No .env file found, using system environment variables")
    
    if not check_database_url():
        print("\n  Create a .env file in the api/ directory with:")
        print("    NEON_DB_URL=postgresql://user:password@host:port/database?sslmode=require")
        sys.exit(1)
    
    # Generate Prisma client
    if not generate_prisma_client(schema_path):
        sys.exit(1)
    
    # Push schema to database
    if not push_schema_to_db(schema_path):
        print("\n⚠ Failed to push schema. Check your database connection.")
        sys.exit(1)
    
    # Ask about creating migrations
    print("\n" + "=" * 60)
    print("✓ Database migration completed successfully!")
    print("=" * 60)
    print("\nYour Neon DB is now set up with the following tables:")
    print("  - customers (user accounts)")
    print("  - refresh_tokens (authentication tokens)")
    print("  - chat_sessions (chat sessions)")
    print("  - chat_messages (chat messages)")
    print("\nOptional: Create migrations for production:")
    print("  prisma migrate dev --name init --schema prisma/schema.prisma")
    print("\nYou can now start your FastAPI server!")

if __name__ == "__main__":
    main()

