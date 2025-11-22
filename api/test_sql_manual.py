"""
Manual test script to verify SQL injection detection is working
Tests specific patterns that might slip through
"""
import re

def validate_chat_input(text: str) -> str:
    """Copy of validation function from validation.py"""
    if not text or not isinstance(text, str):
        raise ValueError("Chat text is required")
    
    text = re.sub(r'\s+', ' ', text.strip())
    
    if len(text) > 5000:
        raise ValueError("Chat text is too long (maximum 5000 characters)")
    
    chat_sql_patterns = [
        r"\w+['\"]--",
        r"['\"][^'\"]*--",
        r"/\*",
        r"\*/",
        r"['\"]\s+(OR|AND)\s+['\"]1['\"]\s*=\s*['\"]1['\"]",
        r"['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]",
        r"['\"]\s+(OR|AND)\s+\d+\s*=\s*\d+",
        r"\w+['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]",
        r"['\"]\s*(OR|AND)\s*['\"]?[0-9xXa-zA-Z]+['\"]?\s*=\s*['\"]?[0-9xXa-zA-Z]+['\"]?",
        r"['\"]?\s*;\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|TRUNCATE)",
        r"['\"]?\s*UNION\s+(ALL\s+)?SELECT",
        r"UNION\s+(ALL\s+)?SELECT\s+.*?\s+FROM",
        r"\b(DROP|CREATE|ALTER|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA|INDEX)\s+\w+",
        r"\b(SELECT|INSERT|DELETE)\s+(?:\*|[\w,\s]+)\s+(FROM|INTO)\s+\w+\s+(WHERE|;|--|\s+(UNION|OR|AND))",
        r"\bUPDATE\s+\w+\s+SET\s+",
        r"['\"][^'\"]*['\"]\s+(OR|AND|UNION)\s+",
    ]
    
    for pattern in chat_sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Invalid input: potentially dangerous content detected")
    
    text = text.replace('\x00', '')
    text = text.strip()
    
    if len(text) > 5000:
        text = text[:5000]
    
    return text

# Test some potentially tricky cases
test_cases = [
    # These should be blocked (SQL injection)
    ("' OR '1'='1", False, "Basic OR bypass"),
    ("'; DROP TABLE users; --", False, "DROP TABLE"),
    ("admin'--", False, "Comment after quote"),
    
    # These should pass (legitimate)
    ("I don't feel well", True, "Legitimate apostrophe"),
    ("Where should I go?", True, "Legitimate 'where'"),
    ("I need to select a doctor", True, "Legitimate 'select'"),
]

print("Testing specific cases manually...")
print("=" * 80)

for prompt, should_pass, desc in test_cases:
    try:
        result = validate_chat_input(prompt)
        if should_pass:
            print(f"[PASS] {desc}: '{prompt}'")
        else:
            print(f"[FAIL - NOT BLOCKED!] {desc}: '{prompt}'")
    except ValueError:
        if not should_pass:
            print(f"[PASS - BLOCKED] {desc}: '{prompt}'")
        else:
            print(f"[FAIL - BLOCKED INCORRECTLY] {desc}: '{prompt}'")

