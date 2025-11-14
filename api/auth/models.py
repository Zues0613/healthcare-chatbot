"""
Authentication request/response models with validation
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

# Password validation
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


class RegisterRequest(BaseModel):
    """User registration request with validation"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    age: Optional[int] = Field(None, ge=0, le=130, description="User age")
    sex: Optional[str] = Field(None, pattern="^(male|female|other)$", description="User sex")
    diabetes: bool = Field(False, description="Has diabetes")
    hypertension: bool = Field(False, description="Has hypertension")
    pregnancy: bool = Field(False, description="Is pregnant")
    city: Optional[str] = Field(None, max_length=100, description="User city")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters long")
        
        if len(v) > PASSWORD_MAX_LENGTH:
            raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters long")
        
        # Check for at least one letter and one number
        if not re.search(r'[A-Za-z]', v):
            raise ValueError("Password must contain at least one letter")
        
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one number")
        
        # Check for SQL injection patterns (basic check)
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE', 'UNION', '--', ';', '/*', '*/']
        v_upper = v.upper()
        for keyword in sql_keywords:
            if keyword in v_upper:
                raise ValueError("Password contains invalid characters")
        
        # Import validation to use sanitize_string
        from .validation import sanitize_string
        try:
            # Sanitize password (but don't HTML escape it)
            return sanitize_string(v, max_length=PASSWORD_MAX_LENGTH, allow_html=False)
        except ValueError as e:
            raise ValueError(f"Invalid password: {str(e)}")
    
    @field_validator("city")
    @classmethod
    def validate_city(cls, v: Optional[str]) -> Optional[str]:
        """Validate city name"""
        if v is None:
            return v
        
        # Import validation function
        from .validation import sanitize_string
        
        try:
            # Sanitize city name
            sanitized = sanitize_string(v.strip(), max_length=100)
            return sanitized if sanitized else None
        except ValueError as e:
            raise ValueError(f"Invalid city name: {str(e)}")


class LoginRequest(BaseModel):
    """User login request with validation"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=PASSWORD_MAX_LENGTH)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Basic password validation"""
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        
        if len(v) > PASSWORD_MAX_LENGTH:
            raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters long")
        
        # Import validation function
        from .validation import sanitize_string
        
        try:
            # Sanitize password (but don't HTML escape it)
            return sanitize_string(v, max_length=PASSWORD_MAX_LENGTH, allow_html=False)
        except ValueError as e:
            raise ValueError(f"Invalid password: {str(e)}")


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    role: str
    age: Optional[int] = None
    sex: Optional[str] = None
    diabetes: bool = False
    hypertension: bool = False
    pregnancy: bool = False
    city: Optional[str] = None
    is_active: bool = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str

