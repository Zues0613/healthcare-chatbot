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
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL from environment"""
        return os.getenv("NEON_DB_URL")
    
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
                logger.warning("NEON_DB_URL not found in environment variables. Database features will be disabled.")
                return False
            
            try:
                # Create persistent connection pool with optimized settings
                self.pool = await asyncpg.create_pool(
                    database_url,
                    min_size=2,  # Keep at least 2 connections alive
                    max_size=20,  # Allow up to 20 concurrent connections
                    command_timeout=60,
                    max_queries=50000,  # Recycle connections after many queries
                    max_inactive_connection_lifetime=300,  # Close idle connections after 5 minutes
                    setup=self._setup_connection,  # Setup each connection
                )
                self._is_connected = True
                logger.info("Successfully created persistent PostgreSQL connection pool")
                
                # Test connection
                async with self.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                
                # Start connection health monitoring
                self._start_health_monitoring()
                
                return True
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}", exc_info=True)
                self._is_connected = False
                self.pool = None
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
                        await self.connect()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Connection health check failed: {e}")
                    # Try to reconnect
                    if self._is_connected:
                        logger.info("Attempting to reconnect to database...")
                        await self.connect()
        
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
        return await self.connect()
    
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

