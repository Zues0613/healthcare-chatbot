"""
Create ip_addresses table to track IP addresses
This table tracks IPs that have visited the application, even if they haven't authenticated
"""
import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

# SQL to create ip_addresses table
CREATE_IP_ADDRESSES_TABLE_SQL = """
-- Create ip_addresses table to track IP addresses
CREATE TABLE IF NOT EXISTS ip_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL UNIQUE, -- IPv6 max length is 45 chars
    first_seen TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP NOT NULL DEFAULT NOW(),
    has_authenticated BOOLEAN NOT NULL DEFAULT FALSE, -- Whether this IP has ever authenticated
    customer_id TEXT REFERENCES customers(id) ON DELETE SET NULL, -- Link to customer if authenticated (matches customers.id type)
    visit_count INTEGER NOT NULL DEFAULT 1, -- Number of times this IP has visited
    metadata JSONB DEFAULT '{}'::jsonb -- Store additional metadata
);

-- Create indexes for ip_addresses
CREATE INDEX IF NOT EXISTS idx_ip_addresses_ip_address ON ip_addresses(ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_addresses_customer_id ON ip_addresses(customer_id);
CREATE INDEX IF NOT EXISTS idx_ip_addresses_has_authenticated ON ip_addresses(has_authenticated);
CREATE INDEX IF NOT EXISTS idx_ip_addresses_last_seen ON ip_addresses(last_seen);
"""

async def create_ip_addresses_table():
    """Create ip_addresses table"""
    # Load environment
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Try loading from current directory
        load_dotenv(override=True)
    
    print("=" * 60)
    print("Creating IP Addresses Table")
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
    
    # Create table
    print("Creating ip_addresses table...")
    try:
        # Execute the SQL to create the table
        await db_client.execute(CREATE_IP_ADDRESSES_TABLE_SQL)
        print("[OK] ip_addresses table created successfully!")
        print()
        
        # Verify table was created
        print("Verifying table...")
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'ip_addresses'
            );
        """
        exists = await db_client.fetchval(query)
        if exists:
            print("  [OK] Table 'ip_addresses' exists")
        else:
            print("  [ERROR] Table 'ip_addresses' was not created")
        
        print()
        print("=" * 60)
        print("[OK] IP addresses table setup complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Failed to create table: {e}")
        print()
        print("This might be because:")
        print("1. Table already exists")
        print("2. Database connection issue")
        print("3. Permission issue")
        return False
    
    await db_client.disconnect()
    return True

if __name__ == "__main__":
    success = asyncio.run(create_ip_addresses_table())
    sys.exit(0 if success else 1)

