"""
Database client wrapper (replaces Prisma)
This file maintains backward compatibility by providing the same interface
but using asyncpg instead of Prisma
"""
from .db_client import db_client

# For backward compatibility, export db_client as prisma_client
prisma_client = db_client

# Mock PRISMA_AVAILABLE for compatibility
PRISMA_AVAILABLE = False


async def get_prisma_client():
    """Get database client (for backward compatibility)"""
    await db_client.ensure_connected()
    return db_client
