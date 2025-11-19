"""
3-Level Caching Service (Improved)
L1: Browser Storage (HTTP Cache Headers)
L2: Redis Cache (Server-side with connection pooling)
L3: Database (PostgreSQL)
"""

import hashlib
import json
import logging
import os
import gzip
import base64
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from datetime import timedelta
from collections import defaultdict
from threading import Lock
import time

# Load .env file to ensure REDIS_URI is available
try:
    from dotenv import load_dotenv
    # Try to load .env from api/ directory or project root
    api_dir = Path(__file__).resolve().parent.parent
    env_candidates = [api_dir / ".env", api_dir.parent / ".env"]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            break
    else:
        # Fallback to default dotenv behavior
        load_dotenv()
except ImportError:
    # dotenv not available, will rely on environment variables being set
    pass

try:
    from upstash_redis import Redis as UpstashRedis
    REDIS_AVAILABLE = True
    UPSTASH_REDIS_AVAILABLE = True
except ImportError:
    try:
        # Fallback to standard redis if upstash_redis is not available
        import redis
        from redis import Redis
        from redis.connection import ConnectionPool
        REDIS_AVAILABLE = True
        UPSTASH_REDIS_AVAILABLE = False
    except ImportError:
        REDIS_AVAILABLE = False
        UPSTASH_REDIS_AVAILABLE = False
        Redis = None
        ConnectionPool = None
        UpstashRedis = None

logger = logging.getLogger("health_assistant")


class CacheService:
    """3-level caching service for chat responses (Improved)"""
    
    def __init__(self):
        self.redis_client: Optional[Any] = None
        self.connection_pool: Optional[Any] = None
        self.is_upstash: bool = False
        self.cache_enabled = os.getenv("ENABLE_CACHE", "1").lower() == "1"
        self.cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # Default 1 hour
        self.cache_version = os.getenv("CACHE_VERSION", "1")  # For cache invalidation on schema changes
        self.compress_threshold = int(os.getenv("CACHE_COMPRESS_THRESHOLD", "1024"))  # Compress if > 1KB
        
        # Cache statistics
        self.stats = {
            "hits": defaultdict(int),
            "misses": defaultdict(int),
            "errors": defaultdict(int),
            "total_requests": 0,
            "total_hits": 0,
            "total_misses": 0,
        }
        self.stats_lock = Lock()
        
        # Initialize Redis connection
        if REDIS_AVAILABLE and self.cache_enabled:
            self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client using Upstash Redis SDK"""
        # Check if redis module is available
        if not REDIS_AVAILABLE:
            logger.warning("Redis module not available. Install with: pip install upstash-redis")
            self.redis_client = None
            self.connection_pool = None
            return
        
        try:
            # Try Upstash Redis first (preferred method)
            if UPSTASH_REDIS_AVAILABLE:
                # Check for Upstash Redis REST API credentials (preferred)
                upstash_url = (
                    os.getenv("UPSTASH_REDIS_REST_URL") or 
                    os.getenv("UPSTASH_REDIS_URL") or 
                    os.getenv("REDIS_URL")
                )
                upstash_token = (
                    os.getenv("UPSTASH_REDIS_REST_TOKEN") or 
                    os.getenv("UPSTASH_REDIS_TOKEN") or 
                    os.getenv("REDIS_TOKEN")
                )
                
                if upstash_url and upstash_token:
                    # Remove quotes if present (from .env file)
                    upstash_url = upstash_url.strip('"\'')
                    upstash_token = upstash_token.strip('"\'')
                    
                    logger.debug(f"Initializing Upstash Redis with URL: {upstash_url[:30]}...")
                    self.redis_client = UpstashRedis(url=upstash_url, token=upstash_token)
                    self.is_upstash = True
                    
                    # Test connection
                    logger.debug("Testing Upstash Redis connection...")
                    if self._test_connection_with_retry():
                        logger.info("Upstash Redis cache (L2) initialized successfully")
                        return
                    else:
                        raise Exception("Upstash Redis connection test failed")
                else:
                    logger.debug("UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN not found in environment, trying fallback to standard Redis with REDIS_URI...")
            
            # Fallback to standard redis with REDIS_URI
            redis_uri = os.getenv("REDIS_URI")
            if not redis_uri:
                logger.warning("REDIS_URI not found in environment, Redis caching disabled")
                logger.debug("Make sure either UPSTASH_REDIS_URL/UPSTASH_REDIS_TOKEN or REDIS_URI is set in your .env file")
                return
            
            logger.debug(f"Initializing standard Redis connection with URI: {redis_uri[:30]}...")
            
            # Import redis module here to ensure it's available
            import redis
            from redis.connection import ConnectionPool as RedisConnectionPool
            
            # Configure connection pool for better performance
            connection_kwargs = {
                "decode_responses": True,
                "socket_connect_timeout": 10,
                "socket_timeout": 10,
                "retry_on_timeout": True,
                "health_check_interval": 30,
                "max_connections": 50,
            }
            
            if redis_uri.startswith("rediss://"):
                # SSL/TLS connection
                connection_kwargs["ssl_cert_reqs"] = None
                connection_kwargs["ssl_check_hostname"] = False
            
            try:
                logger.debug("Attempting to create Redis connection pool...")
                self.connection_pool = RedisConnectionPool.from_url(redis_uri, **connection_kwargs)
                logger.debug("Connection pool created successfully")
            except Exception as pool_error:
                # Fallback: try without connection pool
                logger.warning(f"Connection pool failed, trying direct connection: {pool_error}")
                self.redis_client = redis.from_url(redis_uri, **connection_kwargs)
                self.is_upstash = False
                # Test connection
                logger.debug("Testing direct Redis connection...")
                if self._test_connection_with_retry():
                    logger.info("Redis cache (L2) initialized successfully (direct connection)")
                    return
                else:
                    raise Exception("Direct connection test failed")
            
            # Create Redis client from connection pool
            logger.debug("Creating Redis client from connection pool...")
            from redis import Redis as StandardRedis
            self.redis_client = StandardRedis(connection_pool=self.connection_pool)
            self.is_upstash = False
            
            # Test connection with retry
            logger.debug("Testing Redis connection from pool...")
            if self._test_connection_with_retry():
                logger.info("Redis cache (L2) initialized successfully with connection pooling")
            else:
                raise Exception("Connection pool test failed")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {type(e).__name__}: {e}. Caching will use L1 and L3 only.")
            logger.debug(f"Redis initialization error details: {e}", exc_info=True)
            if UPSTASH_REDIS_AVAILABLE:
                logger.info("Tip: Make sure UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN are set correctly")
            else:
                logger.info("Tip: Check your REDIS_URI format or install upstash-redis: pip install upstash-redis")
            self.redis_client = None
            self.connection_pool = None
    
    def _test_connection_with_retry(self, max_retries: int = 3):
        """Test Redis connection with retry logic"""
        for attempt in range(max_retries):
            try:
                if self.is_upstash:
                    # Upstash Redis - test with a simple set/get operation
                    test_key = f"__test_conn_{int(time.time())}__"
                    self.redis_client.set(test_key, "test", ex=1)  # Set with 1 second expiry
                    result = self.redis_client.get(test_key)
                    if result == "test":
                        logger.debug("Upstash Redis connection test successful")
                        return True
                    else:
                        raise Exception(f"Upstash Redis test failed: expected 'test', got '{result}'")
                else:
                    # Standard redis uses ping()
                    if asyncio.iscoroutinefunction(self.redis_client.ping):
                        # This shouldn't happen in sync context, but handle it
                        logger.warning("Async redis client in sync context")
                    else:
                        self.redis_client.ping()
                    return True
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5
                    time.sleep(wait_time)
                    logger.debug(f"Redis connection test retry {attempt + 1}/{max_retries}: {e}")
                else:
                    logger.error(f"Redis connection test failed after {max_retries} attempts: {e}")
                    raise e
        return False
    
    def generate_cache_key(
        self,
        text: str,
        lang: Optional[str] = None,
        profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a cache key from query text, language, and profile
        
        Args:
            text: User's query text
            lang: Language code
            profile: User profile dict
            
        Returns:
            Cache key string
        """
        # Normalize text (lowercase, strip whitespace)
        normalized_text = text.lower().strip()
        
        # Create key components
        key_parts = {
            "text": normalized_text,
            "lang": lang or "en",
        }
        
        # Add profile components if provided (only relevant fields)
        if profile:
            profile_key = {
                "age": profile.get("age"),
                "sex": profile.get("sex"),
                "diabetes": profile.get("diabetes", False),
                "hypertension": profile.get("hypertension", False),
                "pregnancy": profile.get("pregnancy", False),
            }
            key_parts["profile"] = profile_key
        
        # Create JSON string and hash it
        key_string = json.dumps(key_parts, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()
        
        # Include cache version for schema changes
        return f"chat:response:v{self.cache_version}:{key_hash}"
    
    def _decompress_data(self, data: str) -> str:
        """Decompress gzipped data"""
        try:
            compressed_bytes = base64.b64decode(data.encode())
            decompressed = gzip.decompress(compressed_bytes)
            return decompressed.decode('utf-8')
        except Exception:
            # If decompression fails, assume it's not compressed
            return data
    
    def _compress_data(self, data: str) -> Tuple[str, bool]:
        """Compress data if it exceeds threshold"""
        data_bytes = data.encode('utf-8')
        if len(data_bytes) > self.compress_threshold:
            compressed = gzip.compress(data_bytes, compresslevel=6)
            compressed_b64 = base64.b64encode(compressed).decode('utf-8')
            return compressed_b64, True
        return data, False
    
    async def get(self, cache_key: str) -> Optional[Any]:
        """
        Alias for get_from_cache for simpler API
        """
        return await self.get_from_cache(cache_key)
    
    async def set(self, cache_key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Alias for set_to_cache for simpler API
        """
        return await self.set_to_cache(cache_key, value, ttl=ttl)
    
    async def get_from_cache(
        self,
        cache_key: str,
        retry_count: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response from L2 (Upstash Redis) with retry logic
        L1 (browser) is handled by HTTP headers
        L3 (Database) is handled separately in main.py
        
        Args:
            cache_key: Cache key string
            retry_count: Number of retries on failure
            
        Returns:
            Cached response dict or None
        """
        # Ensure Redis connection is active
        self.ensure_redis_connection()
        
        # Try L2: Upstash Redis or standard Redis
        if self.redis_client:
            for attempt in range(retry_count):
                try:
                    # Upstash Redis is synchronous, standard redis might be async
                    if self.is_upstash:
                        cached_data = self.redis_client.get(cache_key)
                    else:
                        # Standard redis - check if async
                        if asyncio.iscoroutinefunction(self.redis_client.get):
                            cached_data = await self.redis_client.get(cache_key)
                        else:
                            cached_data = self.redis_client.get(cache_key)
                    
                    if cached_data:
                        # Check if data is compressed (starts with base64 gzip header)
                        if cached_data.startswith('H4sI'):  # gzip magic bytes in base64
                            cached_data = self._decompress_data(cached_data)
                        
                        response_data = json.loads(cached_data)
                        self._record_stat("hits", "L2")
                        logger.debug(f"Cache HIT (L2 Redis): {cache_key[:20]}...")
                        return response_data
                    else:
                        self._record_stat("misses", "L2")
                        return None
                        
                except Exception as e:
                    # Check if it's a Redis-specific error
                    error_type = type(e).__name__
                    if "Connection" in error_type or "ConnectionError" in str(type(e)):
                        self._record_stat("errors", "L2-Connection")
                        if attempt < retry_count - 1:
                            # Try to reconnect
                            try:
                                self._test_connection_with_retry()
                            except:
                                pass
                            await asyncio.sleep(0.1 * (attempt + 1))
                            continue
                        logger.warning(f"Redis connection error: {e}")
                    elif "Timeout" in error_type or "TimeoutError" in str(type(e)):
                        self._record_stat("errors", "L2-Timeout")
                        if attempt < retry_count - 1:
                            await asyncio.sleep(0.1 * (attempt + 1))
                            continue
                        logger.warning(f"Redis timeout error: {e}")
                    elif isinstance(e, json.JSONDecodeError):
                        logger.warning(f"Failed to decode cached data: {e}")
                        # Invalid cache entry, delete it
                        try:
                            if self.is_upstash:
                                self.redis_client.delete(cache_key)
                            else:
                                if asyncio.iscoroutinefunction(self.redis_client.delete):
                                    await self.redis_client.delete(cache_key)
                                else:
                                    self.redis_client.delete(cache_key)
                        except:
                            pass
                        return None
                    else:
                        self._record_stat("errors", "L2-Other")
                        logger.warning(f"Redis get error: {e}")
                        if attempt < retry_count - 1:
                            await asyncio.sleep(0.1 * (attempt + 1))
                            continue
        
        # L3: Database (handled separately in main.py)
        # This function only handles L2
        return None
    
    async def set_to_cache(
        self,
        cache_key: str,
        response_data: Dict[str, Any],
        ttl: Optional[int] = None,
        retry_count: int = 2
    ) -> bool:
        """
        Store response in L2 (Upstash Redis) cache with compression
        L1 (browser) is handled by HTTP headers
        L3 (database) is handled separately in main.py
        
        Args:
            cache_key: Cache key string
            response_data: Response data to cache
            ttl: Time to live in seconds (defaults to self.cache_ttl)
            retry_count: Number of retries on failure
            
        Returns:
            True if successful, False otherwise
        """
        # Ensure Redis connection is active
        self.ensure_redis_connection()
        
        if not self.redis_client:
            return False
        
        ttl = ttl or self.cache_ttl
        
        for attempt in range(retry_count):
            try:
                serialized = json.dumps(response_data)
                
                # Compress if data is large
                compressed_data, is_compressed = self._compress_data(serialized)
                
                # Store with compression flag in metadata (optional)
                # Upstash Redis uses setex, standard redis might use set with ex parameter
                if self.is_upstash:
                    self.redis_client.setex(cache_key, ttl, compressed_data)
                else:
                    # Standard redis
                    if asyncio.iscoroutinefunction(self.redis_client.setex):
                        await self.redis_client.setex(cache_key, ttl, compressed_data)
                    elif hasattr(self.redis_client, 'setex'):
                        self.redis_client.setex(cache_key, ttl, compressed_data)
                    else:
                        # Fallback to set with ex parameter
                        if asyncio.iscoroutinefunction(self.redis_client.set):
                            await self.redis_client.set(cache_key, compressed_data, ex=ttl)
                        else:
                            self.redis_client.set(cache_key, compressed_data, ex=ttl)
                
                compression_info = f" (compressed)" if is_compressed else ""
                logger.debug(f"Cache SET (L2 Redis): {cache_key[:20]}... (TTL: {ttl}s{compression_info})")
                return True
                
            except Exception as e:
                error_type = type(e).__name__
                if "Connection" in error_type or "ConnectionError" in str(type(e)):
                    self._record_stat("errors", "L2-Connection")
                    if attempt < retry_count - 1:
                        try:
                            self._test_connection_with_retry()
                        except:
                            pass
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    logger.warning(f"Redis connection error: {e}")
                    return False
                elif "Timeout" in error_type or "TimeoutError" in str(type(e)):
                    self._record_stat("errors", "L2-Timeout")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    logger.warning(f"Redis timeout error: {e}")
                    return False
                else:
                    self._record_stat("errors", "L2-Other")
                    logger.warning(f"Redis set error: {e}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    return False
        
        return False
    
    def get_cache_headers(
        self,
        cache_hit: bool = False,
        max_age: Optional[int] = None,
        content_hash: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate HTTP cache headers for L1 (Browser Storage)
        Uses content hash for proper ETag generation
        
        Args:
            cache_hit: Whether this is a cache hit
            max_age: Max age in seconds (defaults to self.cache_ttl)
            content_hash: Optional content hash for ETag (generated if not provided)
            
        Returns:
            Dictionary of HTTP headers
        """
        max_age = max_age or self.cache_ttl
        
        # Generate ETag from content hash if provided, otherwise use cache status
        if content_hash:
            etag = f'"{content_hash[:16]}"'  # Use first 16 chars of hash
        else:
            etag = f'"{hashlib.md5(str(cache_hit).encode()).hexdigest()}"'
        
        headers = {
            "Cache-Control": f"public, max-age={max_age}, stale-while-revalidate=300",
            "ETag": etag,
            "Vary": "Accept-Encoding",  # Important for compression
        }
        
        if cache_hit:
            headers["X-Cache"] = "HIT"
        else:
            headers["X-Cache"] = "MISS"
        
        return headers
    
    def _generate_content_hash(self, content: Any) -> str:
        """Generate hash from response content for ETag"""
        if isinstance(content, dict):
            content_str = json.dumps(content, sort_keys=True)
        else:
            content_str = str(content)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _record_stat(self, stat_type: str, level: str):
        """Record cache statistics"""
        with self.stats_lock:
            self.stats[stat_type][level] += 1
            if stat_type == "hits":
                self.stats["total_hits"] += 1
            elif stat_type == "misses":
                self.stats["total_misses"] += 1
            self.stats["total_requests"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.stats_lock:
            total = self.stats["total_requests"]
            hit_rate = (self.stats["total_hits"] / total * 100) if total > 0 else 0
            return {
                **self.stats,
                "hit_rate_percent": round(hit_rate, 2),
                "cache_enabled": self.cache_enabled,
                "redis_available": self.is_available(),
            }
    
    def reset_statistics(self):
        """Reset cache statistics"""
        with self.stats_lock:
            self.stats = {
                "hits": defaultdict(int),
                "misses": defaultdict(int),
                "errors": defaultdict(int),
                "total_requests": 0,
                "total_hits": 0,
                "total_misses": 0,
            }
    
    async def delete(self, cache_key: str) -> bool:
        """
        Delete a specific cache key
        
        Args:
            cache_key: Cache key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            if self.is_upstash:
                # Upstash Redis uses delete method
                result = self.redis_client.delete(cache_key)
                return result > 0
            else:
                # Standard redis
                if asyncio.iscoroutinefunction(self.redis_client.delete):
                    result = await self.redis_client.delete(cache_key)
                else:
                    result = self.redis_client.delete(cache_key)
                return result > 0 if result else False
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    async def invalidate_cache(
        self,
        pattern: Optional[str] = None,
        cache_key: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries matching a pattern or specific key
        
        Args:
            pattern: Redis key pattern (e.g., "chat:response:*")
            cache_key: Specific cache key to invalidate
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            if cache_key:
                # Delete specific key
                deleted = await self.delete(cache_key)
                return 1 if deleted else 0
            elif pattern:
                # Delete keys matching pattern (use SCAN for large datasets)
                deleted_count = 0
                cursor = 0
                while True:
                    if self.is_upstash:
                        # Upstash Redis scan
                        cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                    else:
                        # Standard redis scan
                        if asyncio.iscoroutinefunction(self.redis_client.scan):
                            cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                        else:
                            cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                    
                    if keys:
                        for key in keys:
                            if await self.delete(key):
                                deleted_count += 1
                    if cursor == 0:
                        break
                return deleted_count
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return 0
    
    async def invalidate_all_cache(self) -> int:
        """Invalidate all chat response cache entries"""
        return await self.invalidate_cache("chat:response:*")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache system information"""
        info = {
            "enabled": self.cache_enabled,
            "ttl_seconds": self.cache_ttl,
            "version": self.cache_version,
            "redis_available": self.is_available(),
            "compress_threshold": self.compress_threshold,
        }
        
        if self.redis_client and self.connection_pool:
            try:
                pool_info = self.connection_pool.connection_kwargs
                info["redis_pool"] = {
                    "max_connections": pool_info.get("max_connections", "unknown"),
                    "connected": self.redis_client.ping() if self.redis_client else False,
                }
            except:
                pass
        
        return info
    
    def is_available(self) -> bool:
        """Check if Redis cache is available"""
        if self.redis_client is None:
            return False
        # Test connection if available
        try:
            self.redis_client.ping()
            return True
        except:
            # Connection lost, try to reconnect
            try:
                self._init_redis()
                return self.redis_client is not None
            except:
                return False
    
    def ensure_redis_connection(self):
        """Ensure Redis connection is active, reconnect if needed"""
        if not self.redis_client:
            if REDIS_AVAILABLE and self.cache_enabled:
                logger.info("Redis client is None, attempting to initialize...")
                try:
                    self._init_redis()
                    if self.redis_client:
                        logger.info("Redis connection established successfully")
                    else:
                        logger.warning("Redis initialization completed but client is still None")
                except Exception as e:
                    logger.error(f"Redis reconnection attempt failed: {e}", exc_info=True)
        else:
            # Test if connection is still alive
            try:
                self.redis_client.ping()
                logger.debug("Redis connection is alive")
            except Exception as e:
                # Connection lost, try to reconnect
                logger.warning(f"Redis connection lost: {e}, attempting reconnection...")
                self.redis_client = None
                self.connection_pool = None
                if REDIS_AVAILABLE and self.cache_enabled:
                    try:
                        self._init_redis()
                        if self.redis_client:
                            logger.info("Redis reconnection successful")
                        else:
                            logger.warning("Redis reconnection completed but client is still None")
                    except Exception as e:
                        logger.error(f"Redis reconnection failed: {e}", exc_info=True)


# Global cache service instance
cache_service = CacheService()

