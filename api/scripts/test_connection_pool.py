"""
Test script to verify persistent connection pool
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

async def test_pool():
    """Test connection pool"""
    # Load environment
    api_dir = Path(__file__).parent.parent
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    
    print("=" * 60)
    print("Testing Persistent Connection Pool")
    print("=" * 60)
    print()
    
    # Connect
    print("1. Creating connection pool...")
    connected = await db_client.connect()
    if not connected:
        print("[ERROR] Failed to connect")
        return
    
    print("[OK] Connection pool created")
    print()
    
    # Check pool status
    if db_client.pool:
        print("2. Pool Status:")
        print(f"   Pool size: {db_client.pool.get_size()}")
        print(f"   Idle connections: {db_client.pool.get_idle_size()}")
        print(f"   Is closing: {db_client.pool.is_closing()}")
        print()
    
    # Test query
    print("3. Testing query...")
    try:
        result = await db_client.fetchval("SELECT 1")
        print(f"[OK] Query successful: {result}")
    except Exception as e:
        print(f"[ERROR] Query failed: {e}")
    
    print()
    
    # Test multiple queries (should reuse connections)
    print("4. Testing multiple queries (connection reuse)...")
    for i in range(5):
        try:
            result = await db_client.fetchval("SELECT $1", i)
            print(f"   Query {i+1}: {result}")
        except Exception as e:
            print(f"   Query {i+1} failed: {e}")
    
    print()
    
    # Check pool status again
    if db_client.pool:
        print("5. Pool Status After Queries:")
        print(f"   Pool size: {db_client.pool.get_size()}")
        print(f"   Idle connections: {db_client.pool.get_idle_size()}")
        print()
    
    # Disconnect
    print("6. Closing connection pool...")
    await db_client.disconnect()
    print("[OK] Connection pool closed")
    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_pool())

