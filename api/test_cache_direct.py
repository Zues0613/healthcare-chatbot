"""
Direct Redis cache test to verify it's working
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.cache import cache_service

async def test_cache():
    print("Testing Redis cache directly...")
    print(f"Redis available: {cache_service.is_available()}")
    print(f"Cache enabled: {cache_service.cache_enabled}")
    
    if cache_service.is_available():
        # Test write
        test_key = "test:ip_check:127.0.0.1"
        test_value = {"is_known": True, "has_authenticated": False, "ip_address": "127.0.0.1"}
        
        print("\nTesting cache write...")
        result = await cache_service.set(test_key, test_value, ttl=60)
        print(f"Write result: {result}")
        
        print("\nTesting cache read...")
        import time
        start = time.time()
        cached = await cache_service.get_from_cache(test_key, retry_count=0, fast_path=True)
        elapsed = (time.time() - start) * 1000
        print(f"Read result: {cached}")
        print(f"Read time: {elapsed:.2f}ms")
        
        if cached and cached.get("ip_address") == "127.0.0.1":
            print("\n[SUCCESS] Cache is working!")
        else:
            print("\n[FAILED] Cache read returned wrong data")
    else:
        print("\n[WARN] Redis is not available")
        print("Check REDIS_URI or UPSTASH_REDIS_REST_URL in .env")

if __name__ == "__main__":
    asyncio.run(test_cache())

