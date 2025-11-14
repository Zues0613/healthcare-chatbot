"""
Password hashing and verification using SHA-256
Note: SHA-256 is not ideal for password hashing. Consider using bcrypt or Argon2 for production.
This implementation uses SHA-256 with salt as per requirements.
"""
import hashlib
import secrets
import logging
from typing import Tuple

logger = logging.getLogger("health_assistant")

# For better security, we'll use SHA-256 with a salt
# In production, consider using bcrypt or Argon2 instead


def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash a password using SHA-256 with salt
    
    Args:
        password: Plain text password
        salt: Optional salt (if not provided, generates a new one)
    
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        # Generate a random salt (32 bytes = 64 hex characters)
        salt = secrets.token_hex(32)
    
    # Combine password and salt
    combined = f"{password}{salt}"
    
    # Hash using SHA-256
    password_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify a password against a stored hash and salt
    
    Args:
        password: Plain text password to verify
        password_hash: Stored password hash
        salt: Stored salt
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Hash the provided password with the stored salt
        combined = f"{password}{salt}"
        computed_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
        
        # Compare hashes using constant-time comparison
        return secrets.compare_digest(computed_hash, password_hash)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def hash_password_for_storage(password: str) -> str:
    """
    Hash a password and return a combined string (hash:salt) for storage
    
    Args:
        password: Plain text password
    
    Returns:
        Combined hash and salt as "hash:salt"
    """
    password_hash, salt = hash_password(password)
    return f"{password_hash}:{salt}"


def verify_password_from_storage(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored hash string (format: "hash:salt")
    
    Args:
        password: Plain text password to verify
        stored_hash: Stored hash string in format "hash:salt"
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        if ":" not in stored_hash:
            logger.error("Invalid stored hash format")
            return False
        
        password_hash, salt = stored_hash.split(":", 1)
        return verify_password(password, password_hash, salt)
    except Exception as e:
        logger.error(f"Error verifying password from storage: {e}")
        return False

