"""
Authentication and authorization middleware
"""
from typing import List, Optional, Callable
from fastapi import Request, HTTPException, status
from functools import wraps
import logging

from .jwt import get_current_user_required

logger = logging.getLogger("health_assistant")


async def require_auth(request: Request) -> dict:
    """
    Middleware to require authentication
    
    Args:
        request: FastAPI request object
    
    Returns:
        User data from token
    
    Raises:
        HTTPException: If user is not authenticated
    """
    return await get_current_user_required(request)


async def require_role(allowed_roles: List[str]):
    """
    Middleware factory to require specific roles
    
    Args:
        allowed_roles: List of allowed roles
    
    Returns:
        Middleware function
    """
    async def role_checker(request: Request) -> dict:
        """
        Check if user has required role
        
        Args:
            request: FastAPI request object
        
        Returns:
            User data from token
        
        Raises:
            HTTPException: If user is not authenticated or doesn't have required role
        """
        user = await get_current_user_required(request)
        
        user_role = user.get("role", "user")
        
        if user_role not in allowed_roles:
            logger.warning(
                f"Access denied: User {user.get('email')} with role {user_role} "
                f"attempted to access resource requiring roles {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        
        return user
    
    return role_checker


def role_required(allowed_roles: List[str]):
    """
    Decorator for route handlers to require specific roles
    
    Usage:
        @app.get("/admin")
        @role_required(["admin"])
        async def admin_endpoint(request: Request, user: dict = Depends(require_auth)):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get("request")
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Check authentication and role
            user = await get_current_user_required(request)
            user_role = user.get("role", "user")
            
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
                )
            
            # Add user to kwargs
            kwargs["user"] = user
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

