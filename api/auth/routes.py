"""
Authentication routes
"""
import os
import time
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPBearer
import logging
from collections import OrderedDict
from threading import Lock

from .models import RegisterRequest, LoginRequest, TokenResponse, UserResponse, RefreshTokenRequest
from .service import auth_service
from .jwt import verify_token, get_current_user
from .middleware import require_auth, require_role

# Import at module level to avoid lazy loading on first request
from ..database.db_client import db_client
from ..services.cache import cache_service
import asyncio

logger = logging.getLogger("health_assistant")

# In-memory cache fallback when Redis is not available
# LRU cache with max 1000 entries, 5 minute TTL
_ip_cache: OrderedDict = OrderedDict()
_ip_cache_lock = Lock()
_ip_cache_ttl = 300  # 5 minutes
_max_cache_size = 1000


def _get_from_memory_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get from in-memory cache (fallback when Redis unavailable)"""
    with _ip_cache_lock:
        if cache_key in _ip_cache:
            entry = _ip_cache[cache_key]
            # Use the entry's own TTL (not global TTL)
            entry_ttl = entry.get("ttl", _ip_cache_ttl)
            elapsed = time.time() - entry["timestamp"]
            if elapsed < entry_ttl:
                # Move to end (LRU)
                _ip_cache.move_to_end(cache_key)
                logger.debug(f"Memory cache HIT for {cache_key} (age: {elapsed:.2f}s, ttl: {entry_ttl}s)")
                return entry["data"]
            else:
                # Expired, remove it
                logger.debug(f"Memory cache EXPIRED for {cache_key} (age: {elapsed:.2f}s, ttl: {entry_ttl}s)")
                del _ip_cache[cache_key]
    return None


def _set_to_memory_cache(cache_key: str, data: dict, ttl: int = 300):
    """Set to in-memory cache (fallback when Redis unavailable) - FAST PATH"""
    try:
        with _ip_cache_lock:
            _ip_cache[cache_key] = {
                "data": data,
                "timestamp": time.time(),
                "ttl": ttl
            }
            # Move to end (LRU) - O(1) operation
            _ip_cache.move_to_end(cache_key)
            
            # Remove oldest if cache is full (O(1) for OrderedDict)
            if len(_ip_cache) > _max_cache_size:
                _ip_cache.popitem(last=False)  # Remove oldest
    except Exception:
        # Fail silently - cache write failure is acceptable
        pass

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


@router.get("/cache-status")
async def cache_status():
    """Diagnostic endpoint to check Redis cache status"""
    from ..services.cache import cache_service
    
    status = {
        "redis_available": cache_service.is_available(),
        "cache_enabled": cache_service.cache_enabled,
        "stats": cache_service.get_statistics(),
    }
    
    # Test cache with a simple operation
    if cache_service.is_available():
        try:
            test_key = "__cache_test__"
            test_value = {"test": "value", "timestamp": time.time()}
            await cache_service.set(test_key, test_value, ttl=10)
            retrieved = await cache_service.get(test_key)
            status["cache_working"] = retrieved is not None and retrieved.get("test") == "value"
            await cache_service.delete(test_key)
        except Exception as e:
            status["cache_working"] = False
            status["cache_error"] = str(e)
    else:
        status["cache_working"] = False
        status["cache_error"] = "Redis not available"
    
    return status


@router.get("/check-ip")
async def check_ip(request: Request, background_tasks: BackgroundTasks):
    """
    Check if an IP address has been seen before and track it
    
    Optimized for speed - uses Redis cache and defers database updates
    Fast timeout (200ms) to ensure quick response even if DB is slow
    
    Returns:
    - is_known: bool - Whether this IP has been seen before
    - has_authenticated: bool - Whether this IP has ever authenticated
    - ip_address: str - The IP address checked
    """
    # Track total request time
    request_start = time.time()
    
    # Get client IP address (fast - no DB query)
    client_ip = request.client.host if request.client else "unknown"
    
    # Handle forwarded IPs (from proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Also check X-Real-IP header (common in nginx/proxy setups)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and (client_ip == "unknown" or not client_ip):
        client_ip = real_ip.strip()
    
    if client_ip == "unknown" or not client_ip:
        logger.debug("IP check: Unknown or missing IP address")
        return {
            "is_known": False,
            "has_authenticated": False,
            "ip_address": None
        }
    
    # Try Redis cache first (fastest - should be <10ms)
    # Make this SUPER fast - cache should respond in <5ms
    cache_key = f"ip_check:{client_ip}"
    
    # Check cache availability first (fast check)
    # Try Redis first, then fallback to in-memory cache
    cache_available = cache_service.is_available()
    cached_result = None
    
    # Try Redis cache first (if available)
    if cache_available:
        try:
            # Use FAST PATH for IP checks - no retries, no error handling overhead
            # This should respond in <5ms if Redis is working
            cache_start = time.time()
            cached_result = await asyncio.wait_for(
                cache_service.get_from_cache(cache_key, retry_count=0, fast_path=True),
                timeout=0.03  # 30ms timeout - Redis should respond in <5ms
            )
            cache_elapsed = (time.time() - cache_start) * 1000
            if cached_result:
                logger.info(f"✅ Redis cache HIT for {client_ip} ({cache_elapsed:.2f}ms)")
                # Schedule async update in background (don't wait)
                background_tasks.add_task(_update_ip_tracking, client_ip)
                return cached_result
        except asyncio.TimeoutError:
            logger.debug(f"Redis cache timeout for IP {client_ip}, trying memory cache")
        except Exception as e:
            logger.debug(f"Redis cache error: {e}, trying memory cache")
    
    # Fallback to in-memory cache (fast, no network)
    memory_cache_start = time.time()
    cached_result = _get_from_memory_cache(cache_key)
    memory_cache_elapsed = (time.time() - memory_cache_start) * 1000
    if cached_result:
        logger.info(f"✅ Memory cache HIT for {client_ip} ({memory_cache_elapsed:.2f}ms)")
        # Schedule async update in background (don't wait)
        background_tasks.add_task(_update_ip_tracking, client_ip)
        return cached_result
    else:
        logger.debug(f"Memory cache MISS for {client_ip} (check took {memory_cache_elapsed:.2f}ms)")
    
    logger.debug(f"Cache miss for {client_ip} - querying database")
    
    # Fast-fail if request is already taking too long (circuit breaker)
    elapsed_so_far = (time.time() - request_start) * 1000
    if elapsed_so_far > 1000:  # If already >1s, return fast
        logger.warning(f"Request already taking {elapsed_so_far:.2f}ms, returning fast defaults for {client_ip}")
        result = {
            "is_known": False,
            "has_authenticated": False,
            "ip_address": client_ip
        }
        # Cache the result anyway (short TTL)
        _set_to_memory_cache(cache_key, result, ttl=30)
        return result
    
    # Ensure database connection is ready (should be instant if pre-warmed)
    db_ready_start = time.time()
    if not db_client.is_connected():
        logger.warning(f"Database not connected for IP check {client_ip}, attempting connection...")
        try:
            await asyncio.wait_for(db_client.ensure_connected(), timeout=0.5)
        except asyncio.TimeoutError:
            logger.error(f"Database connection timeout for {client_ip}")
            result = {
                "is_known": False,
                "has_authenticated": False,
                "ip_address": client_ip
            }
            _set_to_memory_cache(cache_key, result, ttl=30)
            return result
    db_ready_elapsed = (time.time() - db_ready_start) * 1000
    if db_ready_elapsed > 10:
        logger.warning(f"Database connection check took {db_ready_elapsed:.2f}ms")
    
    # Database query with aggressive timeout (max 100ms for fast response)
    db_query_start = time.time()
    try:
        # Fast SELECT query only (no UPDATE in critical path)
        # Using index on ip_address for fast lookup
        query = """
            SELECT has_authenticated
            FROM ip_addresses
            WHERE ip_address = $1
            LIMIT 1
        """
        
        # Aggressive timeout - if DB is slow, return fast defaults
        # With proper index and pre-warmed pool, this should be <30ms
        ip_record = await asyncio.wait_for(
            db_client.fetchrow(query, client_ip),
            timeout=0.1  # 100ms timeout - fail fast if DB is slow
        )
        db_query_elapsed = (time.time() - db_query_start) * 1000
        if db_query_elapsed > 50:
            logger.warning(f"Database query took {db_query_elapsed:.2f}ms for {client_ip} (expected <30ms)")
        else:
            logger.debug(f"Database query took {db_query_elapsed:.2f}ms for {client_ip}")
        
        if ip_record:
            # IP is known
            result = {
                "is_known": True,
                "has_authenticated": ip_record["has_authenticated"],
                "ip_address": client_ip
            }
            
            # Cache result for 5 minutes (non-blocking write)
            # Try Redis first, then fallback to memory cache
            if cache_service.is_available():
                # Write to Redis in background (don't block response)
                background_tasks.add_task(
                    _cache_ip_result, cache_key, result, 300
                )
            # Also cache in memory (fast fallback) - SYNC write for immediate availability
            _set_to_memory_cache(cache_key, result, ttl=300)
            logger.debug(f"Cached IP result in memory: {cache_key}")
            
            # Schedule async update in background (don't wait)
            background_tasks.add_task(_update_ip_tracking, client_ip)
            
            logger.debug(f"IP check: Known IP {client_ip} (authenticated: {ip_record['has_authenticated']})")
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
            # Try Redis first, then fallback to memory cache
            if cache_service.is_available():
                # Write to Redis in background (don't block response)
                background_tasks.add_task(
                    _cache_ip_result, cache_key, result, 60
                )
            # Also cache in memory (fast fallback) - SYNC write for immediate availability
            _set_to_memory_cache(cache_key, result, ttl=60)
            logger.debug(f"Cached new IP result in memory: {cache_key}")
            
            logger.debug(f"IP check: New IP {client_ip}")
            return result
    
    except asyncio.TimeoutError:
        total_elapsed = (time.time() - request_start) * 1000
        logger.warning(f"IP check database query timed out for {client_ip} (total: {total_elapsed:.2f}ms)")
        # Return fast defaults and cache them (short TTL to retry soon)
        result = {
            "is_known": False,
            "has_authenticated": False,
            "ip_address": client_ip
        }
        # Cache timeout results with short TTL (30s) to avoid repeated timeouts
        _set_to_memory_cache(cache_key, result, ttl=30)
        return result
    except Exception as e:
        total_elapsed = (time.time() - request_start) * 1000
        logger.error(f"Error checking IP address {client_ip}: {e} (total: {total_elapsed:.2f}ms)", exc_info=True)
        # Return fast defaults and cache them (short TTL)
        result = {
            "is_known": False,
            "has_authenticated": False,
            "ip_address": client_ip
        }
        _set_to_memory_cache(cache_key, result, ttl=30)
        return result


async def _cache_ip_result(cache_key: str, result: dict, ttl: int):
    """Background task to cache IP check result (non-blocking, fast path)"""
    from ..services.cache import cache_service
    try:
        # Use fast path for cache writes (no retries, no connection checks)
        await cache_service.set_to_cache(cache_key, result, ttl=ttl, retry_count=0, fast_path=True)
        logger.debug(f"Cached IP check result for {cache_key}")
    except Exception as e:
        logger.debug(f"Background cache write failed: {e}")


async def _update_ip_tracking(client_ip: str):
    """Background task to update IP tracking (non-blocking)"""
    from ..database.db_client import db_client
    try:
        update_query = """
            UPDATE ip_addresses
            SET last_seen = NOW(), visit_count = visit_count + 1
            WHERE ip_address = $1
        """
        await db_client.execute(update_query, client_ip)
    except Exception as e:
        logger.debug(f"Background IP update failed: {e}")


async def _create_ip_record(client_ip: str):
    """Background task to create IP record (non-blocking)"""
    from ..database.db_client import db_client
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
