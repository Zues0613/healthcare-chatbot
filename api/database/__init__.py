from .prisma_client import prisma_client, get_prisma_client, PRISMA_AVAILABLE
from .service import db_service

__all__ = ["prisma_client", "get_prisma_client", "db_service", "PRISMA_AVAILABLE"]

# Export get_prisma_client for use in other modules
def get_prisma_client_export():
    """Export get_prisma_client function"""
    return get_prisma_client

# Try to import Prisma models if available
if PRISMA_AVAILABLE:
    try:
        from prisma.models import Customer, ChatMessage, ChatSession
        __all__.extend(["Customer", "ChatMessage", "ChatSession"])
    except ImportError:
        pass

