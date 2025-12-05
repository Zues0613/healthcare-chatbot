"""
Async PostgreSQL database client using asyncpg
Replaces Prisma with direct database connections
Maintains persistent connection pool to avoid unnecessary connection requests
"""
import os
import logging
import asyncpg
from typing import Optional
import json
from datetime import datetime
import asyncio

logger = logging.getLogger("health_assistant")


class DatabaseClient:
    """
    Async PostgreSQL database client with persistent connection pooling.
    Maintains a connection pool that stays alive throughout the application lifecycle.
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._is_connected = False
        self._connection_check_task: Optional[asyncio.Task] = None
        self._reconnect_lock: Optional[asyncio.Lock] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._last_connection_error: Optional[str] = None
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL from environment"""
        # Try multiple environment variable names
        database_url = os.getenv("NEON_DB_URL") or os.getenv("DATABASE_URL")
        if database_url:
            # Validate URL format
            if not (database_url.startswith("postgresql://") or database_url.startswith("postgresql+asyncpg://")):
                logger.warning(f"Database URL format may be incorrect. Expected postgresql:// or postgresql+asyncpg://")
            return database_url
        return None
    
    async def connect(self) -> bool:
        """Connect to the database and create persistent connection pool"""
        # Initialize lock if needed
        if self._reconnect_lock is None:
            self._reconnect_lock = asyncio.Lock()
        
        # Use lock to prevent concurrent connection attempts
        async with self._reconnect_lock:
            if self._is_connected and self.pool and not self.pool.is_closing():
                # Test if pool is still alive
                try:
                    async with self.pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                    return True
                except Exception:
                    # Pool is dead, need to reconnect
                    logger.warning("Connection pool is dead, reconnecting...")
                    self._is_connected = False
                    if self.pool:
                        try:
                            await self.pool.close()
                        except:
                            pass
                    self.pool = None
            
            database_url = self._get_database_url()
            if not database_url:
                logger.warning("NEON_DB_URL or DATABASE_URL not found in environment variables. Database features will be disabled.")
                self._last_connection_error = "Database URL not configured"
                return False
            
            # Validate URL format before attempting connection
            try:
                from urllib.parse import urlparse
                parsed = urlparse(database_url)
                if not parsed.hostname:
                    raise ValueError("Database URL missing hostname")
            except Exception as e:
                logger.error(f"Invalid database URL format: {e}")
                logger.error(f"URL format should be: postgresql://user:password@host:port/database")
                self._last_connection_error = f"Invalid URL format: {e}"
                return False
            
            # Check if we've exceeded max reconnection attempts
            if self._reconnect_attempts >= self._max_reconnect_attempts:
                logger.error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached. Stopping reconnection attempts.")
                logger.error(f"Last error: {self._last_connection_error}")
                logger.error("Please check your DATABASE_URL configuration and network connectivity.")
                return False
            
            try:
                # Create persistent connection pool with optimized settings for speed
                # Pre-warm pool with more connections for faster cold start
                self.pool = await asyncpg.create_pool(
                    database_url,
                    min_size=5,  # Keep more connections alive for faster response
                    max_size=30,  # Allow more concurrent connections
                    command_timeout=10,  # Shorter timeout for faster failure detection
                    max_queries=50000,  # Recycle connections after many queries
                    setup=self._setup_connection,  # Setup each connection
                )
                self._is_connected = True
                self._reconnect_attempts = 0  # Reset on successful connection
                self._last_connection_error = None
                logger.info("Successfully created persistent PostgreSQL connection pool")
                
                # Pre-warm pool by acquiring all min_size connections
                # This ensures connections are ready immediately (faster cold start)
                logger.info("Pre-warming connection pool for faster cold start...")
                warmup_connections = []
                try:
                    pool_size = getattr(self.pool, '_minsize', 5)
                    for i in range(min(5, pool_size)):
                        conn = await self.pool.acquire()
                        warmup_connections.append(conn)
                        # Test each connection
                        await conn.fetchval("SELECT 1")
                    logger.info(f"Pre-warmed {len(warmup_connections)} database connections")
                except Exception as e:
                    logger.warning(f"Could not pre-warm all connections: {e}")
                finally:
                    # Release all pre-warmed connections back to pool
                    for conn in warmup_connections:
                        await self.pool.release(conn)
                
                # Final connection test
                async with self.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                # Start connection health monitoring
                self._start_health_monitoring()
                
                return True
            except (asyncpg.InvalidPasswordError, asyncpg.PostgresError) as e:
                # Database-specific errors
                error_msg = f"PostgreSQL connection error: {e}"
                logger.error(error_msg)
                self._last_connection_error = error_msg
                self._is_connected = False
                self.pool = None
                self._reconnect_attempts += 1
                return False
            except (OSError, ConnectionError) as e:
                # Network/DNS errors
                error_msg = f"Network connection error: {e}"
                logger.error(error_msg)
                logger.error("This usually means:")
                logger.error("  1. The database hostname cannot be resolved (DNS error)")
                logger.error("  2. The database server is unreachable")
                logger.error("  3. The DATABASE_URL contains an invalid hostname")
                logger.error(f"  4. Check your DATABASE_URL: {database_url[:50]}...")
                self._last_connection_error = error_msg
                self._is_connected = False
                self.pool = None
                self._reconnect_attempts += 1
                # Don't retry immediately for network errors - wait longer
                if self._reconnect_attempts < self._max_reconnect_attempts:
                    wait_time = min(2 ** self._reconnect_attempts, 30)  # Exponential backoff, max 30s
                    logger.info(f"Waiting {wait_time} seconds before next reconnection attempt...")
                    await asyncio.sleep(wait_time)
                return False
            except Exception as e:
                # Other errors
                error_msg = f"Failed to connect to database: {e}"
                logger.error(error_msg, exc_info=True)
                self._last_connection_error = error_msg
                self._is_connected = False
                self.pool = None
                self._reconnect_attempts += 1
                return False
    
    async def _setup_connection(self, conn: asyncpg.Connection):
        """Setup each connection in the pool"""
        # Set connection parameters for optimal performance
        await conn.set_type_codec(
            'jsonb',
            encoder=json.dumps,
            decoder=json.loads,
            schema='pg_catalog'
        )
        # Set statement timeout (optional, can be adjusted)
        await conn.execute("SET statement_timeout = '60s'")
    
    def _start_health_monitoring(self):
        """Start background task to monitor connection health"""
        if self._connection_check_task and not self._connection_check_task.done():
            return
        
        async def health_check():
            """Periodically check connection health and reconnect if needed"""
            while self._is_connected:
                try:
                    await asyncio.sleep(30)  # Check every 30 seconds
                    if self.pool and not self.pool.is_closing():
                        async with self.pool.acquire() as conn:
                            await conn.fetchval("SELECT 1")
                    else:
                        logger.warning("Connection pool closed, attempting reconnect...")
                        # Reset reconnect attempts for health check reconnections
                        self._reconnect_attempts = 0
                        await self.connect()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Connection health check failed: {e}")
                    # Only try to reconnect if we haven't exceeded max attempts
                    if self._is_connected and self._reconnect_attempts < self._max_reconnect_attempts:
                        logger.info("Attempting to reconnect to database...")
                        await self.connect()
                    elif self._reconnect_attempts >= self._max_reconnect_attempts:
                        logger.error("Max reconnection attempts reached. Health check will stop trying to reconnect.")
                        self._is_connected = False
                        break
        
        self._connection_check_task = asyncio.create_task(health_check())
    
    async def disconnect(self) -> None:
        """Disconnect from the database and close connection pool"""
        # Stop health monitoring
        if self._connection_check_task and not self._connection_check_task.done():
            self._connection_check_task.cancel()
            try:
                await self._connection_check_task
            except asyncio.CancelledError:
                pass
        
        # Close connection pool
        if self.pool:
            try:
                await self.pool.close()
                logger.info("Closed PostgreSQL connection pool")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")
        
        self.pool = None
        self._is_connected = False
    
    def is_connected(self) -> bool:
        """Check if database connection pool is active"""
        return (
            self._is_connected 
            and self.pool is not None 
            and not self.pool.is_closing()
        )
    
    async def ensure_connected(self) -> bool:
        """
        Ensure database is connected.
        This is a lightweight check - the pool should already be alive from startup.
        """
        if self.is_connected():
            return True
        # Only reconnect if pool is truly dead
        # Reset reconnect attempts if we're manually ensuring connection
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.warning("Reconnection attempts exceeded. Resetting counter for manual reconnection attempt.")
            self._reconnect_attempts = 0
        return await self.connect()
    
    def reset_reconnect_attempts(self):
        """Reset reconnection attempts counter (useful for manual retries)"""
        self._reconnect_attempts = 0
        self._last_connection_error = None
        logger.info("Reconnection attempts counter reset")
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        if not await self.ensure_connected():
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query and return the result"""
        if not self.pool or self.pool.is_closing():
            if not await self.connect():
                raise Exception("Database not connected")
        
        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except (asyncpg.PostgresConnectionError, asyncpg.InterfaceError) as e:
            logger.warning(f"Connection error during execute: {e}, attempting reconnect...")
            await self.connect()
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        if not self.pool or self.pool.is_closing():
            if not await self.connect():
                raise Exception("Database not connected")
        
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        except (asyncpg.PostgresConnectionError, asyncpg.InterfaceError) as e:
            logger.warning(f"Connection error during fetch: {e}, attempting reconnect...")
            await self.connect()
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args):
        """Fetch a single row"""
        if not self.pool or self.pool.is_closing():
            if not await self.connect():
                raise Exception("Database not connected")
        
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
        except (asyncpg.PostgresConnectionError, asyncpg.InterfaceError) as e:
            logger.warning(f"Connection error during fetchrow: {e}, attempting reconnect...")
            await self.connect()
            async with self.pool.acquire() as conn:
                return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Fetch a single value"""
        if not self.pool or self.pool.is_closing():
            if not await self.connect():
                raise Exception("Database not connected")
        
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)
        except (asyncpg.PostgresConnectionError, asyncpg.InterfaceError) as e:
            logger.warning(f"Connection error during fetchval: {e}, attempting reconnect...")
            await self.connect()
            async with self.pool.acquire() as conn:
                return await conn.fetchval(query, *args)


# Global database client instance
db_client = DatabaseClient()

