import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("health_assistant")

# Try to import Prisma, handle if not available
try:
    from prisma import Prisma
    from prisma.models import Customer, ChatSession, ChatMessage
    PRISMA_AVAILABLE = True
except ImportError:
    PRISMA_AVAILABLE = False
    logger.warning("Prisma not available. Install with: pip install prisma")
    Prisma = None
    Customer = None
    ChatSession = None
    ChatMessage = None


class PrismaClient:
    """Prisma client wrapper for database operations"""
    
    def __init__(self):
        self.client: Optional[Prisma] = None
        self._is_connected = False
    
    async def connect(self) -> bool:
        """Connect to the database"""
        if not PRISMA_AVAILABLE:
            logger.error("Prisma is not available. Install with: pip install prisma")
            return False
        
        if self._is_connected and self.client:
            return True
        
        try:
            self.client = Prisma()
            await self.client.connect()
            self._is_connected = True
            logger.info("Successfully connected to database using Prisma")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the database"""
        if self.client:
            try:
                await self.client.disconnect()
                self._is_connected = False
                logger.info("Disconnected from database")
            except Exception as e:
                logger.error(f"Error disconnecting from database: {e}")
        self.client = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected and self.client is not None
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        if not self.is_connected():
            return False
        
        try:
            # Try a simple query
            await self.client.customer.find_first(take=1)
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    async def ensure_connected(self) -> bool:
        """Ensure database is connected, connect if not"""
        if not self.is_connected():
            return await self.connect()
        return True


# Global Prisma client instance
prisma_client = PrismaClient()


async def get_prisma_client() -> Prisma:
    """Get Prisma client instance"""
    await prisma_client.ensure_connected()
    if not prisma_client.client:
        raise Exception("Prisma client not initialized")
    return prisma_client.client

