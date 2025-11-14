"""
Authentication routes
"""
import os
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer
import logging

from .models import RegisterRequest, LoginRequest, TokenResponse, UserResponse, RefreshTokenRequest
from .service import auth_service
from .jwt import verify_token, get_current_user
from .middleware import require_auth, require_role

logger = logging.getLogger("health_assistant")

# Check if we're in production for secure cookie settings
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request_data: RegisterRequest,
    response: Response
):
    """
    Register a new user
    
    Validates input, hashes password, and creates user account
    """
    try:
        # Register user
        user = await auth_service.register_user(
            email=request_data.email,
            password=request_data.password,
            age=request_data.age,
            sex=request_data.sex,
            diabetes=request_data.diabetes,
            hypertension=request_data.hypertension,
            pregnancy=request_data.pregnancy,
            city=request_data.city,
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists or registration failed"
            )
        
        # Create tokens
        tokens = await auth_service.create_tokens(user)
        
        # Set HTTP-only cookies with secure flag in production
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=IS_PRODUCTION,  # Only send over HTTPS in production
            samesite="lax",
            max_age=30 * 60,  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=IS_PRODUCTION,  # Only send over HTTPS in production
            samesite="lax",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )
        
        return UserResponse(**user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        ) from e


@router.post("/login", response_model=UserResponse)
async def login(
    request_data: LoginRequest,
    response: Response
):
    """
    Login user
    
    Validates credentials and returns tokens in HTTP-only cookies
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=request_data.email,
            password=request_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create tokens
        tokens = await auth_service.create_tokens(user)
        
        # Set HTTP-only cookies with secure flag in production
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=IS_PRODUCTION,  # Only send over HTTPS in production
            samesite="lax",
            max_age=30 * 60,  # 30 minutes
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=IS_PRODUCTION,  # Only send over HTTPS in production
            samesite="lax",
            max_age=7 * 24 * 60 * 60,  # 7 days
        )
        
        return UserResponse(**user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        ) from e


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: dict = Depends(require_auth)
):
    """
    Logout user
    
    Revokes refresh token and clears cookies
    """
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if refresh_token:
            # Revoke refresh token
            await auth_service.revoke_refresh_token(refresh_token)
        
        # Clear cookies
        response.delete_cookie(key="access_token", httponly=True, secure=IS_PRODUCTION, samesite="lax")
        response.delete_cookie(key="refresh_token", httponly=True, secure=IS_PRODUCTION, samesite="lax")
        
        return {"message": "Logged out successfully"}
    
    except Exception as e:
        logger.error(f"Error in logout: {e}", exc_info=True)
        # Clear cookies even if there's an error
        response.delete_cookie(key="access_token", httponly=True, secure=IS_PRODUCTION, samesite="lax")
        response.delete_cookie(key="refresh_token", httponly=True, secure=IS_PRODUCTION, samesite="lax")
        return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: dict = Depends(require_auth)
):
    """
    Get current user information
    
    Requires authentication
    """
    try:
        user_data = await auth_service.get_user_by_id(user["user_id"])
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user_info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        ) from e


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response
):
    """
    Refresh access token using refresh token
    
    Validates refresh token and issues new access token
    """
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Check if token is revoked
        from ..database import prisma_client, get_prisma_client
        if await prisma_client.ensure_connected():
            client = await get_prisma_client()
            token_record = await client.refreshtoken.find_unique(where={"token": refresh_token})
            
            if not token_record or token_record.revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token has been revoked"
                )
        
        # Get user data
        user_id = payload.get("sub")
        user_data = await auth_service.get_user_by_id(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create new access token
        tokens = await auth_service.create_tokens(user_data)
        
        # Set new access token cookie with secure flag in production
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=IS_PRODUCTION,  # Only send over HTTPS in production
            samesite="lax",
            max_age=30 * 60,  # 30 minutes
        )
        
        return {"message": "Token refreshed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in refresh_token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token"
        ) from e

