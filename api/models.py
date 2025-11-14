from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Profile(BaseModel):
    age: Optional[int] = None
    sex: Optional[Literal["male", "female", "other"]] = None
    diabetes: bool = False
    hypertension: bool = False
    pregnancy: bool = False
    city: Optional[str] = None
    medical_conditions: List[str] = Field(default_factory=list)  # Additional medical conditions

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: Optional[int]):
        """Validate age input"""
        if value is None:
            return value
        
        # Import validation function
        from .auth.validation import validate_integer
        
        try:
            return validate_integer(value, min_value=0, max_value=130)
        except ValueError as e:
            raise ValueError(f"Invalid age: {str(e)}")

    @field_validator("city")
    @classmethod
    def normalize_city(cls, value: Optional[str]):
        """Validate and sanitize city input"""
        if value is None:
            return value
        
        # Import validation function
        from .auth.validation import sanitize_string
        
        try:
            normalized = sanitize_string(value.strip(), max_length=100)
            return normalized if normalized else None
        except ValueError as e:
            raise ValueError(f"Invalid city: {str(e)}")
    
    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value: Optional[str]):
        """Validate sex input"""
        if value is None:
            return value
        
        if value not in ["male", "female", "other"]:
            raise ValueError("Sex must be one of: male, female, other")
        
        return value


class ChatRequest(BaseModel):
    text: str
    lang: Literal["en", "hi", "ta", "te", "kn", "ml"] = "en"
    profile: Profile
    debug: bool = False
    customer_id: Optional[str] = None
    session_id: Optional[str] = None

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        """Validate and sanitize chat text input"""
        if not value or not value.strip():
            raise ValueError("Query text must not be empty")
        
        # Import validation function
        from .auth.validation import validate_chat_input
        
        # Validate input to prevent SQL injection and XSS
        try:
            return validate_chat_input(value.strip())
        except ValueError as e:
            raise ValueError(f"Invalid input: {str(e)}")
    
    @field_validator("customer_id", "session_id")
    @classmethod
    def validate_ids(cls, value: Optional[str]) -> Optional[str]:
        """Validate ID fields"""
        if value is None:
            return value
        
        # Validate UUID format (basic check)
        import re
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if not re.match(uuid_pattern, value, re.IGNORECASE):
            raise ValueError("Invalid ID format")
        
        return value


class MentalHealthSafety(BaseModel):
    crisis: bool = False
    matched: List[str] = Field(default_factory=list)
    first_aid: List[str] = Field(default_factory=list)


class PregnancySafety(BaseModel):
    concern: bool = False
    matched: List[str] = Field(default_factory=list)


class Safety(BaseModel):
    red_flag: bool = False
    matched: List[str] = Field(default_factory=list)
    mental_health: MentalHealthSafety = Field(default_factory=MentalHealthSafety)
    pregnancy: PregnancySafety = Field(default_factory=PregnancySafety)


class Fact(BaseModel):
    type: str
    data: Any


class Citation(BaseModel):
    source: str
    id: str
    topic: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    route: Literal["graph", "vector"]
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    safety: Safety
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VoiceChatResponse(BaseModel):
    transcript: str
    answer: str
    audio_base64: str
    route: Literal["graph", "vector"]
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    safety: Safety
    metadata: Dict[str, Any] = Field(default_factory=dict)

