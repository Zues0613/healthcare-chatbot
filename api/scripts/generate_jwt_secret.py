"""
Generate a secure JWT secret key for production use.

This script generates a cryptographically secure random key suitable for JWT signing.
"""

import secrets
import sys

def generate_jwt_secret(length: int = 64) -> str:
    """
    Generate a secure JWT secret key.
    
    Args:
        length: Length of the key in bytes (default: 64 bytes = 86 characters when base64 encoded)
    
    Returns:
        A URL-safe base64-encoded random string
    """
    # Generate random bytes and encode as URL-safe base64
    # This produces a string that's safe to use in environment variables
    key = secrets.token_urlsafe(length)
    return key

def main():
    """Generate and display a JWT secret key."""
    print("=" * 60)
    print("JWT Secret Key Generator")
    print("=" * 60)
    print()
    
    # Generate a 64-byte key (recommended for HS256)
    # This will produce ~86 characters when base64 encoded
    key = generate_jwt_secret(64)
    
    print("Generated JWT Secret Key:")
    print("-" * 60)
    print(key)
    print("-" * 60)
    print()
    print("Key Length:", len(key), "characters")
    print()
    print("IMPORTANT SECURITY NOTES:")
    print("1. Keep this key SECRET - never commit it to version control")
    print("2. Use different keys for development and production")
    print("3. Store it securely in your .env file or environment variables")
    print("4. If this key is compromised, regenerate it immediately")
    print("5. All existing tokens will be invalidated if you change this key")
    print()
    print("To use this key, add it to your .env file:")
    print(f"JWT_SECRET_KEY={key}")
    print()
    
    # Option to copy to clipboard (Windows)
    try:
        import pyperclip
        pyperclip.copy(key)
        print("[OK] Key copied to clipboard!")
    except ImportError:
        print("Tip: Install 'pyperclip' to automatically copy to clipboard")
    except Exception:
        pass  # Clipboard not available, that's okay

if __name__ == "__main__":
    main()

