#!/usr/bin/env python3
"""
Initialize Prisma client and generate migrations
"""
import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Initialize Prisma"""
    api_dir = Path(__file__).parent.parent
    prisma_dir = api_dir / "prisma"
    
    print("Initializing Prisma...")
    print(f"API directory: {api_dir}")
    print(f"Prisma directory: {prisma_dir}")
    
    # Check if schema file exists
    schema_file = prisma_dir / "schema.prisma"
    if not schema_file.exists():
        print(f"ERROR: Schema file not found at {schema_file}")
        sys.exit(1)
    
    # Generate Prisma client
    print("\n1. Generating Prisma client...")
    try:
        result = subprocess.run(
            ["prisma", "generate", "--schema", str(schema_file)],
            cwd=api_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print("✓ Prisma client generated successfully")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to generate Prisma client: {e}")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: Prisma CLI not found. Install it with: pip install prisma")
        sys.exit(1)
    
    # Check database connection
    print("\n2. Checking database connection...")
    db_url = os.getenv("NEON_DB_URL")
    if not db_url:
        print("WARNING: NEON_DB_URL not set. Database connection cannot be tested.")
        print("Set NEON_DB_URL in your .env file to test the connection.")
    else:
        print("✓ NEON_DB_URL is set")
        # Try to push schema (this will create tables if they don't exist)
        print("\n3. Pushing schema to database...")
        try:
            result = subprocess.run(
                ["prisma", "db", "push", "--schema", str(schema_file), "--accept-data-loss"],
                cwd=api_dir,
                check=True,
                capture_output=True,
                text=True
            )
            print("✓ Schema pushed to database successfully")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"WARNING: Failed to push schema to database: {e}")
            print(e.stderr)
            print("You may need to create migrations manually or check your database connection.")
    
    print("\n✓ Prisma initialization complete!")
    print("\nNext steps:")
    print("1. Make sure NEON_DB_URL is set in your .env file")
    print("2. Run migrations: prisma migrate dev --name init")
    print("3. Start your FastAPI server")

if __name__ == "__main__":
    main()

