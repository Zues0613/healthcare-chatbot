"""
Authentication routes
"""
import os
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
import logging

from .models import RegisterRequest, LoginRequest, TokenResponse, UserResponse, RefreshTokenRequest
from .service import auth_service
from .jwt import verify_token, get_current_user
from .middleware import require_auth, require_role

logger = logging.getLogger("health_assistant")

# Check if we're in production for secure cookie settings
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"
# For cross-origin requests (Vercel frontend to Render backend), we need samesite="none" with secure=True
# "none" is required for cross-origin cookies, and it always requires secure=True (HTTPS)
# In production (deployed environments), both frontend and backend are HTTPS, so use "none"
# In local development, if using localhost, we can use "lax" or "none" with secure=False
USE_CROSS_ORIGIN = os.getenv("USE_CROSS_ORIGIN_COOKIES", "true").lower() == "true"
SAMESITE_POLICY = "none" if (IS_PRODUCTION or USE_CROSS_ORIGIN) else "lax"
# When samesite="none", secure must be True. In production, always True. In dev, True if cross-origin
SECURE_COOKIE = IS_PRODUCTION or USE_CROSS_ORIGIN

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request_data: RegisterRequest,
    request: Request,
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
        
        # Track IP address as authenticated
        try:
            from ..database.db_client import db_client
            client_ip = request.client.host if request.client else None
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            
            if client_ip and client_ip != "unknown":
                update_ip_query = """
                    INSERT INTO ip_addresses (ip_address, has_authenticated, customer_id, first_seen, last_seen, visit_count)
                    VALUES ($1, TRUE, $2, NOW(), NOW(), 1)
                    ON CONFLICT (ip_address) DO UPDATE
                    SET has_authenticated = TRUE,
                        customer_id = COALESCE(ip_addresses.customer_id, $2),
                        last_seen = NOW(),
                        visit_count = ip_addresses.visit_count + 1
                """
                await db_client.execute(update_ip_query, client_ip, user["id"])
        except Exception as e:
            logger.warning(f"Failed to track IP address: {e}")
        
        # Set HTTP-only cookies with secure flag for cross-origin support
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=SECURE_COOKIE,  # Required for samesite="none" (cross-origin)
            samesite=SAMESITE_POLICY,  # "none" for cross-origin, "lax" for same-origin
            max_age=7 * 24 * 60 * 60,  # 7 days (frontend handles 12-hour activity-based expiration)
            path="/",  # Ensure cookie is available for all paths
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=SECURE_COOKIE,  # Required for samesite="none" (cross-origin)
            samesite=SAMESITE_POLICY,  # "none" for cross-origin, "lax" for same-origin
            max_age=7 * 24 * 60 * 60,  # 7 days
            path="/",  # Ensure cookie is available for all paths
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
    request: Request,
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
        
        # Track IP address as authenticated
        try:
            from ..database.db_client import db_client
            client_ip = request.client.host if request.client else None
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            
            if client_ip and client_ip != "unknown":
                update_ip_query = """
                    INSERT INTO ip_addresses (ip_address, has_authenticated, customer_id, first_seen, last_seen, visit_count)
                    VALUES ($1, TRUE, $2, NOW(), NOW(), 1)
                    ON CONFLICT (ip_address) DO UPDATE
                    SET has_authenticated = TRUE,
                        customer_id = COALESCE(ip_addresses.customer_id, $2),
                        last_seen = NOW(),
                        visit_count = ip_addresses.visit_count + 1
                """
                await db_client.execute(update_ip_query, client_ip, user["id"])
        except Exception as e:
            logger.warning(f"Failed to track IP address: {e}")
        
        # Set HTTP-only cookies with secure flag for cross-origin support
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=SECURE_COOKIE,  # Required for samesite="none" (cross-origin)
            samesite=SAMESITE_POLICY,  # "none" for cross-origin, "lax" for same-origin
            max_age=7 * 24 * 60 * 60,  # 7 days (frontend handles 12-hour activity-based expiration)
            path="/",  # Ensure cookie is available for all paths
        )
        
        response.set_cookie(
            key="refresh_token",
            value=tokens["refresh_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=SECURE_COOKIE,  # Required for samesite="none" (cross-origin)
            samesite=SAMESITE_POLICY,  # "none" for cross-origin, "lax" for same-origin
            max_age=7 * 24 * 60 * 60,  # 7 days
            path="/",  # Ensure cookie is available for all paths
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
    user_id = user.get("user_id", "unknown")
    logger.info(f"Logout request received for user: {user_id}")
    
    try:
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if refresh_token:
            # Revoke refresh token
            logger.info(f"Revoking refresh token for user: {user_id}")
            await auth_service.revoke_refresh_token(refresh_token)
            logger.info(f"Refresh token revoked successfully for user: {user_id}")
        else:
            logger.info(f"No refresh token found in cookies for user: {user_id}")
        
        # Clear cookies with same settings as when they were set
        response.delete_cookie(key="access_token", httponly=True, secure=SECURE_COOKIE, samesite=SAMESITE_POLICY)
        response.delete_cookie(key="refresh_token", httponly=True, secure=SECURE_COOKIE, samesite=SAMESITE_POLICY)
        
        logger.info(f"Logout successful for user: {user_id}")
        return {"message": "Logged out successfully"}
    
    except Exception as e:
        logger.error(f"Error in logout for user {user_id}: {e}", exc_info=True)
        # Clear cookies even if there's an error
        response.delete_cookie(key="access_token", httponly=True, secure=IS_PRODUCTION, samesite="lax")
        response.delete_cookie(key="refresh_token", httponly=True, secure=IS_PRODUCTION, samesite="lax")
        logger.info(f"Logout completed (with error) for user: {user_id}")
        return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: dict = Depends(require_auth),
    request: Request = None
):
    """
    Get current user information
    
    Requires authentication
    Cached in Redis for 5 minutes
    """
    from ..services.cache import cache_service
    
    user_id = user["user_id"]
    cache_key = f"user_info:{user_id}"
    
    # Try to get from Redis cache first
    if cache_service.is_available():
        cached_user = await cache_service.get(cache_key)
        if cached_user is not None:
            logger.debug(f"Cache hit for user info: {user_id}")
            return UserResponse(**cached_user)
    
    try:
        user_data = await auth_service.get_user_by_id(user_id)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Cache in Redis for 5 minutes (300 seconds)
        if cache_service.is_available():
            await cache_service.set(cache_key, user_data, ttl=300)
        
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
        
        # Check if token is revoked using database service
        from ..database import service as db_service
        token_record = await db_service.get_refresh_token(refresh_token)
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or expired"
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
        
        # Set new access token cookie with secure flag for cross-origin support
        response.set_cookie(
            key="access_token",
            value=tokens["access_token"],
            httponly=True,  # Client-side JavaScript cannot access
            secure=SECURE_COOKIE,  # Required for samesite="none" (cross-origin)
            samesite=SAMESITE_POLICY,  # "none" for cross-origin, "lax" for same-origin
            max_age=7 * 24 * 60 * 60,  # 7 days (frontend handles 12-hour activity-based expiration)
            path="/",  # Ensure cookie is available for all paths
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


@router.get("/check-ip")
async def check_ip(request: Request, background_tasks: BackgroundTasks):
    """
    Check if an IP address has been seen before and track it
    
    Optimized for speed - uses Redis cache and defers database updates
    
    Returns:
    - is_known: bool - Whether this IP has been seen before
    - has_authenticated: bool - Whether this IP has ever authenticated
    """
    from ..database.db_client import db_client
    from ..services.cache import cache_service
    
    # Get client IP address (fast - no DB query)
    client_ip = request.client.host if request.client else "unknown"
    
    # Handle forwarded IPs (from proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        client_ip = forwarded_for.split(",")[0].strip()
    
    if client_ip == "unknown" or not client_ip:
        return {
            "is_known": False,
            "has_authenticated": False,
            "ip_address": None
        }
    
    # Try Redis cache first (fastest)
    cache_key = f"ip_check:{client_ip}"
    if cache_service.is_available():
        try:
            cached_result = await cache_service.get(cache_key)
            if cached_result:
                # Return cached result immediately
                # Schedule async update in background (don't wait)
                background_tasks.add_task(_update_ip_tracking, client_ip)
                return cached_result
        except Exception as e:
            logger.debug(f"Cache read failed for IP check: {e}")
    
    try:
        # Fast SELECT query only (no UPDATE in critical path)
        query = """
            SELECT has_authenticated
            FROM ip_addresses
            WHERE ip_address = $1
        """
        ip_record = await db_client.fetchrow(query, client_ip)
        
        if ip_record:
            # IP is known
            result = {
                "is_known": True,
                "has_authenticated": ip_record["has_authenticated"],
                "ip_address": client_ip
            }
            
            # Cache result for 5 minutes
            if cache_service.is_available():
                try:
                    await cache_service.set(cache_key, result, ttl=300)
                except Exception:
                    pass
            
            # Schedule async update in background (don't wait)
            background_tasks.add_task(_update_ip_tracking, client_ip)
            
            return result
        else:
            # New IP - create record (async, don't wait)
            background_tasks.add_task(_create_ip_record, client_ip)
            
            result = {
                "is_known": False,
                "has_authenticated": False,
                "ip_address": client_ip
            }
            
            # Cache result for 1 minute (new IPs might be created soon)
            if cache_service.is_available():
                try:
                    await cache_service.set(cache_key, result, ttl=60)
                except Exception:
                    pass
            
            return result
    
    except Exception as e:
        logger.error(f"Error checking IP address: {e}", exc_info=True)
        # Return safe defaults on error
        return {
            "is_known": False,
            "has_authenticated": False,
            "ip_address": client_ip
        }


async def _update_ip_tracking(client_ip: str, db_client):
    """Background task to update IP tracking (non-blocking)"""
    try:
        update_query = """
            UPDATE ip_addresses
            SET last_seen = NOW(), visit_count = visit_count + 1
            WHERE ip_address = $1
        """
        await db_client.execute(update_query, client_ip)
    except Exception as e:
        logger.debug(f"Background IP update failed: {e}")


async def _create_ip_record(client_ip: str, db_client):
    """Background task to create IP record (non-blocking)"""
    try:
        insert_query = """
            INSERT INTO ip_addresses (ip_address, first_seen, last_seen, visit_count)
            VALUES ($1, NOW(), NOW(), 1)
            ON CONFLICT (ip_address) DO UPDATE
            SET last_seen = NOW(), visit_count = ip_addresses.visit_count + 1
        """
        await db_client.execute(insert_query, client_ip)
    except Exception as e:
        logger.debug(f"Background IP creation failed: {e}")
