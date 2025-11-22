"""
Input validation utilities to prevent SQL injection and XSS attacks
"""
import re
import html
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("health_assistant")

# SQL injection patterns - more specific to avoid false positives
SQL_INJECTION_PATTERNS = [
    # SQL keywords in suspicious contexts - requires SQL keyword BEFORE FROM/INTO/WHERE
    r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|TRUNCATE)\s+.*?\b(FROM|INTO|WHERE)\b",
    # SQL comment patterns (but not em dashes in text)
    r"(--\s|/\*|\*/)",
    # SQL injection attempts with OR/AND (specific patterns only)
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    r"(\b(OR|AND)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"])",
    # Suspicious patterns: semicolons followed by SQL keywords, or multiple quotes in suspicious context
    r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION))",
    r"(['\"].*?['\"])\s*(OR|AND|UNION)\s+",
]

# XSS patterns
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"<iframe[^>]*>.*?</iframe>",
    r"javascript:",
    r"on\w+\s*=",
    r"<img[^>]*onerror",
    r"<svg[^>]*onload",
    r"<body[^>]*onload",
]

# Dangerous file extensions
DANGEROUS_EXTENSIONS = [
    ".exe", ".bat", ".cmd", ".com", ".pif", ".scr", ".vbs", ".js", ".jar",
    ".app", ".deb", ".pkg", ".rpm", ".dmg", ".iso", ".sh", ".ps1", ".py",
]


def sanitize_string(value: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
    """
    Sanitize a string input to prevent SQL injection and XSS
    
    Args:
        value: String to sanitize
        max_length: Maximum length of the string
        allow_html: If True, don't HTML escape (for chat messages that may need formatting)
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {value[:50]}")
            raise ValueError("Invalid input: potentially dangerous content detected")
    
    # Check for XSS patterns (but allow basic formatting for chat)
    if not allow_html:
        for pattern in XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {value[:50]}")
                raise ValueError("Invalid input: potentially dangerous content detected")
        
        # HTML escape to prevent XSS
        value = html.escape(value)
    else:
        # For chat messages, remove dangerous patterns but allow basic HTML
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<iframe[^>]*>.*?</iframe>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
    
    # Trim whitespace
    value = value.strip()
    
    # Limit length
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value


def validate_email(email: str) -> str:
    """
    Validate and sanitize email address
    
    Args:
        email: Email address to validate
    
    Returns:
        Validated email address
    
    Raises:
        ValueError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email is required")
    
    email = email.strip().lower()
    
    # Basic email format validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    # Check for SQL injection
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, email, re.IGNORECASE):
            raise ValueError("Invalid email format")
    
    return email


def validate_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    """
    Validate and sanitize integer input
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
    
    Returns:
        Validated integer
    
    Raises:
        ValueError: If value is invalid
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValueError("Invalid integer value")
    
    if min_value is not None and int_value < min_value:
        raise ValueError(f"Value must be at least {min_value}")
    
    if max_value is not None and int_value > max_value:
        raise ValueError(f"Value must be at most {max_value}")
    
    return int_value


def validate_boolean(value: Any) -> bool:
    """
    Validate and sanitize boolean input
    
    Args:
        value: Value to validate
    
    Returns:
        Validated boolean
    
    Raises:
        ValueError: If value is invalid
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ('true', '1', 'yes', 'on'):
            return True
        elif value_lower in ('false', '0', 'no', 'off'):
            return False
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    raise ValueError("Invalid boolean value")


def validate_dict(data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate and sanitize dictionary input
    
    Args:
        data: Dictionary to validate
        schema: Optional schema for validation
    
    Returns:
        Validated dictionary
    """
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")
    
    validated = {}
    
    for key, value in data.items():
        # Sanitize key
        key = sanitize_string(str(key), max_length=100)
        
        # Validate value based on schema
        if schema and key in schema:
            value_type = schema[key].get("type")
            if value_type == "string":
                value = sanitize_string(str(value), max_length=schema[key].get("max_length"))
            elif value_type == "integer":
                value = validate_integer(
                    value,
                    min_value=schema[key].get("min_value"),
                    max_value=schema[key].get("max_value")
                )
            elif value_type == "boolean":
                value = validate_boolean(value)
        else:
            # Default validation
            if isinstance(value, str):
                value = sanitize_string(value)
            elif isinstance(value, dict):
                value = validate_dict(value)
            elif isinstance(value, list):
                value = [sanitize_string(str(item)) if isinstance(item, str) else item for item in value]
        
        validated[key] = value
    
    return validated


def validate_chat_input(text: str) -> str:
    """
    Validate chat input text
    
    Args:
        text: Chat text to validate
    
    Returns:
        Validated chat text
    
    Raises:
        ValueError: If text is invalid
    """
    if not text or not isinstance(text, str):
        raise ValueError("Chat text is required")
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Check length
    if len(text) > 5000:  # Reasonable limit for chat messages
        raise ValueError("Chat text is too long (maximum 5000 characters)")
    
    # Check for SQL injection - use more lenient patterns for chat messages
    # Only flag actual SQL injection attempts, not normal punctuation like apostrophes
    chat_sql_patterns = [
        # SQL comment patterns - catch '--' after quotes or in suspicious context
        # Pattern 1: Word/identifier followed by quote then -- (e.g., "admin'--")
        r"\w+['\"]--",
        # Pattern 2: Quote followed by optional text and then -- (e.g., "' OR 1=1--", "'--")
        r"['\"][^'\"]*--",
        # Pattern 3: /* or */ comment markers  
        r"/\*",
        r"\*/",
        
        # SQL injection with OR/AND - classic patterns like ' OR '1'='1
        # Pattern 1: Quote (single or double), space, OR/AND, space, then '1'='1 (most common)
        # Match: ' OR '1'='1, " OR "1"="1
        r"['\"]\s+(OR|AND)\s+['\"]1['\"]\s*=\s*['\"]1['\"]",
        # Pattern 2: Quote, space, OR/AND, space, then quoted string = quoted string
        # Match: ' OR 'x'='x, " OR "a"="a
        r"['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]",
        # Pattern 3: Quote, space, OR/AND, then number = number (no quotes)
        # Match: ' OR 1=1, " OR 2=2
        r"['\"]\s+(OR|AND)\s+\d+\s*=\s*\d+",
        # Pattern 4: Word/identifier, quote, space, OR/AND, then pattern
        # Match: admin' OR '1'='1, 1' OR '1'='1
        r"\w+['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]",
        # Pattern 5: Quote at start, OR/AND (less strict on spaces for edge cases)
        # Match: 'OR'1'='1 (no spaces), 'OR 1=1
        r"['\"]\s*(OR|AND)\s*['\"]?[0-9xXa-zA-Z]+['\"]?\s*=\s*['\"]?[0-9xXa-zA-Z]+['\"]?",
        
        # Semicolons followed by SQL keywords (command chaining - clear SQL injection)
        r"['\"]?\s*;\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|TRUNCATE)",
        
        # UNION SELECT patterns (clear SQL injection)
        r"['\"]?\s*UNION\s+(ALL\s+)?SELECT",
        r"UNION\s+(ALL\s+)?SELECT\s+.*?\s+FROM",
        
        # SQL DDL statements - DROP/CREATE/ALTER/TRUNCATE with TABLE/DATABASE
        r"\b(DROP|CREATE|ALTER|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA|INDEX)\s+\w+",
        
        # SQL DML statements - only match actual SQL syntax, not natural language
        # Be very strict: require SQL-like context
        # Pattern 1: SELECT/INSERT/DELETE with FROM/INTO + SQL context (WHERE, semicolon, comment)
        # Only match if there's SQL-like context after the table (excludes natural language)
        r"\b(SELECT|INSERT|DELETE)\s+(?:\*|[\w,\s]+)\s+(FROM|INTO)\s+\w+\s+(WHERE|;|--|\s+(UNION|OR|AND))",
        # Pattern 2: UPDATE ... SET (clear SQL syntax)
        r"\bUPDATE\s+\w+\s+SET\s+",
        
        # Exclude common English phrases with determiners (to reduce false positives)
        # But still catch actual SQL with WHERE clauses or semicolons
        
        # Quoted strings immediately followed by SQL operators (suspicious)
        r"['\"][^'\"]*['\"]\s+(OR|AND|UNION)\s+",
    ]
    
    for pattern in chat_sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Potential SQL injection in chat input: {text[:50]}")
            raise ValueError("Invalid input: potentially dangerous content detected")
    
    # For chat messages, we've already checked SQL patterns above with more lenient patterns
    # Just do basic sanitization (remove null bytes, trim, length check) without SQL pattern checking
    # to avoid double-checking with more aggressive patterns
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length (already checked above, but ensure)
    if len(text) > 5000:
        text = text[:5000]
    
    return text


def sanitize_file_name(filename: str) -> str:
    """
    Sanitize file name to prevent path traversal and dangerous extensions
    
    Args:
        filename: File name to sanitize
    
    Returns:
        Sanitized file name
    
    Raises:
        ValueError: If filename is invalid
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename is required")
    
    # Remove path traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Check for dangerous extensions
    filename_lower = filename.lower()
    for ext in DANGEROUS_EXTENSIONS:
        if filename_lower.endswith(ext):
            raise ValueError(f"File type not allowed: {ext}")
    
    # Sanitize
    filename = sanitize_string(filename, max_length=255)
    
    return filename


def validate_uuid(uuid_string: str) -> str:
    """
    Validate UUID format to prevent SQL injection through path parameters
    
    Args:
        uuid_string: UUID string to validate
    
    Returns:
        Validated UUID string
    
    Raises:
        ValueError: If UUID format is invalid
    """
    if not uuid_string or not isinstance(uuid_string, str):
        raise ValueError("UUID is required")
    
    # Remove whitespace
    uuid_string = uuid_string.strip()
    
    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, uuid_string, re.IGNORECASE):
            logger.warning(f"Potential SQL injection in UUID: {uuid_string[:50]}")
            raise ValueError("Invalid UUID format")
    
    # Validate UUID format (basic check - should be 36 characters with dashes)
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    if not re.match(uuid_pattern, uuid_string, re.IGNORECASE):
        raise ValueError("Invalid UUID format")
    
    return uuid_string


def validate_query_limit(limit: int, max_limit: int = 100, min_limit: int = 1) -> int:
    """
    Validate query limit parameter
    
    Args:
        limit: Limit value to validate
        max_limit: Maximum allowed limit
        min_limit: Minimum allowed limit
    
    Returns:
        Validated limit
    
    Raises:
        ValueError: If limit is invalid
    """
    return validate_integer(limit, min_value=min_limit, max_value=max_limit)
