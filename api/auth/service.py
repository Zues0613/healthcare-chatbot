"""
Authentication service for user management
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .password import hash_password_for_storage, verify_password_from_storage
from .jwt import create_access_token, create_refresh_token, verify_token
from ..database import db_client, db_service

logger = logging.getLogger("health_assistant")


class AuthService:
    """Authentication service for user management"""
    
    @staticmethod
    async def register_user(
        email: str,
        password: str,
        age: Optional[int] = None,
        sex: Optional[str] = None,
        diabetes: bool = False,
        hypertension: bool = False,
        pregnancy: bool = False,
        city: Optional[str] = None,
        role: str = "user"
    ) -> Optional[Dict[str, Any]]:
        """
        Register a new user
        
        Args:
            email: User email
            password: Plain text password
            age: User age
            sex: User sex
            diabetes: Has diabetes
            hypertension: Has hypertension
            pregnancy: Is pregnant
            city: User city
            role: User role (default: "user")
        
        Returns:
            User data or None if registration failed
        """
        if not await db_client.ensure_connected():
            logger.error("Database not connected")
            return None
        
        try:
            # Check if user already exists
            existing_user = await db_service.get_customer_by_email(email)
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return None
            
            # Hash password
            password_hash = hash_password_for_storage(password)
            
            # Create user
            user = await db_service.create_customer(
                email=email,
                password_hash=password_hash,
                role=role,
                age=age,
                sex=sex,
                diabetes=diabetes,
                hypertension=hypertension,
                pregnancy=pregnancy,
                city=city
            )
            
            if not user:
                return None
            
            logger.info(f"User registered: {user['id']} ({user['email']})")
            
            return {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "age": user.get("age"),
                "sex": user.get("sex"),
                "diabetes": user.get("diabetes", False),
                "hypertension": user.get("hypertension", False),
                "pregnancy": user.get("pregnancy", False),
                "city": user.get("city"),
                "is_active": user.get("is_active", True),
            }
        except Exception as e:
            logger.error(f"Error registering user: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user
        
        Args:
            email: User email
            password: Plain text password
        
        Returns:
            User data or None if authentication failed
        """
        if not await db_client.ensure_connected():
            logger.error("Database not connected")
            return None
        
        try:
            # Find user by email
            user = await db_service.get_customer_by_email(email)
            if not user:
                logger.warning(f"User not found: {email}")
                return None
            
            # Check if user is active
            if not user.get("is_active", True):
                logger.warning(f"User account is inactive: {email}")
                return None
            
            # Verify password
            if not verify_password_from_storage(password, user["password_hash"]):
                logger.warning(f"Invalid password for user: {email}")
                return None
            
            # Update last login
            await db_service.update_customer_last_login(user["id"])
            
            logger.info(f"User authenticated: {user['id']} ({user['email']})")
            
            return {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "age": user.get("age"),
                "sex": user.get("sex"),
                "diabetes": user.get("diabetes", False),
                "hypertension": user.get("hypertension", False),
                "pregnancy": user.get("pregnancy", False),
                "city": user.get("city"),
                "is_active": user.get("is_active", True),
            }
        except Exception as e:
            logger.error(f"Error authenticating user: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
        
        Returns:
            User data or None if not found
        """
        if not await db_client.ensure_connected():
            return None
        
        try:
            user = await db_service.get_customer(user_id)
            
            if not user:
                return None
            
            return {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "age": user.get("age"),
                "sex": user.get("sex"),
                "diabetes": user.get("diabetes", False),
                "hypertension": user.get("hypertension", False),
                "pregnancy": user.get("pregnancy", False),
                "city": user.get("city"),
                "is_active": user.get("is_active", True),
            }
        except Exception as e:
            logger.error(f"Error getting user: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def create_tokens(user_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Create access and refresh tokens for user
        
        Args:
            user_data: User data
        
        Returns:
            Dictionary with access_token and refresh_token
        """
        # Create access token
        access_token = create_access_token({
            "sub": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
        })
        
        # Create refresh token
        refresh_token = create_refresh_token({
            "sub": user_data["id"],
        })
        
        # Store refresh token in database
        if await db_client.ensure_connected():
            try:
                expires_at = datetime.utcnow() + timedelta(days=7)
                await db_service.save_refresh_token(
                    customer_id=user_data["id"],
                    token=refresh_token,
                    expires_at=expires_at
                )
            except Exception as e:
                logger.error(f"Error storing refresh token: {e}", exc_info=True)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    
    @staticmethod
    async def revoke_refresh_token(token: str) -> bool:
        """
        Revoke a refresh token
        
        Args:
            token: Refresh token to revoke
        
        Returns:
            True if token was revoked, False otherwise
        """
        if not await db_client.ensure_connected():
            return False
        
        try:
            await db_service.revoke_refresh_token(token)
            return True
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}", exc_info=True)
            return False


# Global service instance
auth_service = AuthService()
