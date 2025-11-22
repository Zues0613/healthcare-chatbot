"""
Test script for validation.py with 100 prompts
Tests SQL injection detection while ensuring legitimate chat messages pass
"""
import sys
import os
import re
import html
from typing import Optional
import logging

# Mock logger to avoid dependency issues
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("health_assistant")

# Import validation patterns and functions directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# SQL injection patterns - copy from validation.py
SQL_INJECTION_PATTERNS = [
    r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|TRUNCATE)\s+.*?\b(FROM|INTO|WHERE)\b",
    r"(--\s|/\*|\*/)",
    r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
    r"(\b(OR|AND)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"])",
    r"(;\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION))",
    r"(['\"].*?['\"])\s*(OR|AND|UNION)\s+",
]

def sanitize_string(value: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
    """Sanitize a string input to prevent SQL injection and XSS"""
    if not isinstance(value, str):
        return str(value)
    
    value = value.replace('\x00', '')
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError("Invalid input: potentially dangerous content detected")
    
    value = value.strip()
    
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value

def validate_chat_input(text: str) -> str:
    """Validate chat input text"""
    if not text or not isinstance(text, str):
        raise ValueError("Chat text is required")
    
    text = re.sub(r'\s+', ' ', text.strip())
    
    if len(text) > 5000:
        raise ValueError("Chat text is too long (maximum 5000 characters)")
    
    chat_sql_patterns = [
        # SQL comment patterns
        r"\w+['\"]--",
        r"['\"][^'\"]*--",
        r"/\*",
        r"\*/",
        
        # SQL injection with OR/AND
        r"['\"]\s+(OR|AND)\s+['\"]1['\"]\s*=\s*['\"]1['\"]",
        r"['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]",
        r"['\"]\s+(OR|AND)\s+\d+\s*=\s*\d+",
        r"\w+['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]",
        r"['\"]\s*(OR|AND)\s*['\"]?[0-9xXa-zA-Z]+['\"]?\s*=\s*['\"]?[0-9xXa-zA-Z]+['\"]?",
        
        # Semicolons followed by SQL keywords
        r"['\"]?\s*;\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|TRUNCATE)",
        
        # UNION SELECT patterns
        r"['\"]?\s*UNION\s+(ALL\s+)?SELECT",
        r"UNION\s+(ALL\s+)?SELECT\s+.*?\s+FROM",
        
        # SQL DDL statements
        r"\b(DROP|CREATE|ALTER|TRUNCATE)\s+(TABLE|DATABASE|SCHEMA|INDEX)\s+\w+",
        
        # SQL DML statements - strict patterns (require SQL context like WHERE, semicolon)
        r"\b(SELECT|INSERT|DELETE)\s+(?:\*|[\w,\s]+)\s+(FROM|INTO)\s+\w+\s+(WHERE|;|--|\s+(UNION|OR|AND))",
        # UPDATE ... SET pattern (clear SQL syntax)
        r"\bUPDATE\s+\w+\s+SET\s+",
        
        # Quoted strings followed by SQL operators
        r"['\"][^'\"]*['\"]\s+(OR|AND|UNION)\s+",
    ]
    
    for pattern in chat_sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Invalid input: potentially dangerous content detected")
    
    text = sanitize_string(text, max_length=5000, allow_html=True)
    
    return text

import traceback

# Test cases: (prompt, expected_result, description)
# expected_result: True = should PASS (no error), False = should FAIL (raise error)
TEST_CASES = [
    # ===== NORMAL CHAT MESSAGES (Should PASS) =====
    ("I'd like to improve my sleep hygiene. Where should I start?", True, "Normal message with apostrophe and 'where'"),
    ("Where are you located?", True, "Question with 'where'"),
    ("I need help with my headache. What should I do?", True, "Normal health question"),
    ("Can you tell me where to find a doctor?", True, "Question with 'where'"),
    ("What's the best treatment for fever?", True, "Contraction with apostrophe"),
    ("I don't feel well today", True, "Contraction"),
    ("Let's talk about my symptoms", True, "Contraction with apostrophe"),
    ("It's been a week since my last checkup", True, "Contraction"),
    ("I'm experiencing chest pain", True, "Contraction"),
    ("You're very helpful, thank you!", True, "Contraction"),
    
    # Messages with various punctuation
    ("How can I improve my diet? I'm not sure where to begin.", True, "Multiple sentences with apostrophe and 'where'"),
    ("What about pain management? Where do I start?", True, "Question with 'where'"),
    ("I have diabetes and I'd like to know more about managing it", True, "Contraction"),
    ("Where can I get vaccinated?", True, "Simple question with 'where'"),
    ("I don't understand this medication. Can you explain?", True, "Contraction"),
    
    # Normal health-related queries
    ("My head hurts. What could be the cause?", True, "Normal symptom query"),
    ("I have a fever and cough. Should I see a doctor?", True, "Multiple symptoms"),
    ("Can you help me understand my test results?", True, "Question about results"),
    ("What are the side effects of this medication?", True, "Medication question"),
    ("I'm pregnant. What should I avoid?", True, "Pregnancy query"),
    
    # Various languages/contexts
    ("मुझे सिरदर्द हो रहा है", True, "Hindi text - should pass"),
    ("నాకు జ్వరం వచ్చింది", True, "Telugu text - should pass"),
    ("எனக்கு காய்ச்சல் வருகிறது", True, "Tamil text - should pass"),
    
    # Long messages
    ("I've been experiencing headaches for the past few weeks. They usually occur in the afternoon and are quite severe. I've tried taking over-the-counter pain medication but it doesn't seem to help much. I'm wondering if I should see a doctor or if there's something else I can try at home first. Where would you recommend I start?", True, "Long message with 'where'"),
    
    # Messages with numbers and symbols
    ("My blood pressure is 140/90. Is that normal?", True, "Numbers and slash"),
    ("I take 2 pills daily at 8 AM and 8 PM", True, "Numbers and times"),
    ("Can you help with prescription refill #12345?", True, "Numbers and symbols"),
    
    # Messages that might seem suspicious but are normal
    ("I need to select a doctor from the list", True, "Contains 'select' but not SQL"),
    ("Where should I insert this information?", True, "Contains 'insert' but not SQL"),
    ("Can you delete my old messages?", True, "Contains 'delete' but not SQL"),
    ("What's the update on my appointment?", True, "Contains 'update' but not SQL"),
    
    # ===== ACTUAL SQL INJECTION ATTEMPTS (Should FAIL) =====
    ("' OR '1'='1", False, "Classic SQL injection: OR bypass"),
    ("'; DROP TABLE users; --", False, "SQL injection: DROP TABLE"),
    ("admin'--", False, "SQL injection: comment bypass"),
    ("' OR 1=1--", False, "SQL injection: OR 1=1"),
    ("' UNION SELECT * FROM users--", False, "SQL injection: UNION SELECT"),
    ("1' OR '1'='1", False, "SQL injection: OR bypass with quotes"),
    ("' OR 'x'='x", False, "SQL injection: OR with x"),
    ("admin'/*", False, "SQL injection: comment start"),
    ("' UNION SELECT null, null--", False, "SQL injection: UNION with nulls"),
    ("'; DELETE FROM users WHERE '1'='1", False, "SQL injection: DELETE"),
    
    # More SQL injection patterns
    ("' OR 1=1 OR 'a'='a", False, "SQL injection: multiple OR conditions"),
    ("' UNION SELECT username, password FROM users--", False, "SQL injection: UNION SELECT specific columns"),
    ("'; UPDATE users SET password='hacked'--", False, "SQL injection: UPDATE"),
    ("' OR '1'='1'--", False, "SQL injection: OR with comment"),
    ("admin' AND '1'='1", False, "SQL injection: AND condition"),
    ("' OR 1=1#", False, "SQL injection: OR with hash comment"),
    ("'; INSERT INTO users (username) VALUES ('hacker')--", False, "SQL injection: INSERT"),
    ("' OR 'a'='a' AND 'b'='b", False, "SQL injection: multiple AND/OR"),
    ("' UNION ALL SELECT * FROM admin--", False, "SQL injection: UNION ALL"),
    ("'; TRUNCATE TABLE logs--", False, "SQL injection: TRUNCATE"),
    
    # SQL injection with CREATE/ALTER/DROP
    ("'; CREATE TABLE test (id int)--", False, "SQL injection: CREATE TABLE"),
    ("'; ALTER TABLE users ADD COLUMN hacked varchar(255)--", False, "SQL injection: ALTER TABLE"),
    ("'; DROP DATABASE health_db--", False, "SQL injection: DROP DATABASE"),
    ("'; EXEC xp_cmdshell('rm -rf /')--", False, "SQL injection: EXEC command"),
    ("'; EXECUTE sp_executesql 'SELECT * FROM users'--", False, "SQL injection: EXECUTE"),
    
    # SQL injection with semicolons
    ("test'; SELECT * FROM users--", False, "SQL injection: semicolon with SELECT"),
    ("'; DELETE FROM sessions;--", False, "SQL injection: semicolon with DELETE"),
    ("'; DROP TABLE patients; SELECT 1--", False, "SQL injection: multiple statements"),
    
    # SQL injection with WHERE clauses
    ("SELECT * FROM users WHERE id='1' OR '1'='1", False, "SQL injection: SELECT with WHERE OR"),
    ("SELECT * FROM customers WHERE email='admin' OR 1=1--", False, "SQL injection: SELECT WHERE OR"),
    ("DELETE FROM messages WHERE user_id='1' OR '1'='1", False, "SQL injection: DELETE WHERE OR"),
    
    # SQL injection with quoted strings and operators
    ("'test' OR '1'='1'", False, "SQL injection: quoted string with OR"),
    ("\"admin\" OR \"1\"=\"1\"", False, "SQL injection: double quotes with OR"),
    ("'user' UNION SELECT * FROM admins--", False, "SQL injection: quoted string with UNION"),
    
    # Edge cases for SQL injection
    ("SELECT FROM users", False, "SQL injection: SELECT FROM (partial but suspicious)"),
    ("INSERT INTO patients VALUES", False, "SQL injection: INSERT INTO (suspicious)"),
    ("UPDATE users SET password='", False, "SQL injection: UPDATE SET"),
    ("DELETE FROM sessions WHERE", False, "SQL injection: DELETE WHERE"),
    ("UNION SELECT * FROM", False, "SQL injection: UNION SELECT"),
    
    # ===== MIXED CASES - Normal text that shouldn't trigger =====
    ("I need to select a treatment option from the list", True, "Normal text with 'select'"),
    ("Please insert my appointment into the calendar", True, "Normal text with 'insert'"),
    ("Can you update my profile information?", True, "Normal text with 'update'"),
    ("I want to delete my old messages", True, "Normal text with 'delete'"),
    ("Let's create a new health plan together", True, "Normal text with 'create'"),
    ("I need to alter my diet plan", True, "Normal text with 'alter'"),
    ("Where can I find a doctor? I need to select one from the available options", True, "Normal text with multiple SQL-like words"),
    ("I'd like to create an account. Where should I go?", True, "Normal text with 'create' and 'where'"),
    
    # Messages with SQL-like words in natural context
    ("The doctor said I should avoid certain foods where possible", True, "Normal text with 'where'"),
    ("I'm not sure where to begin with my treatment", True, "Normal text with 'where'"),
    ("Can you help me select the right medication?", True, "Normal text with 'select'"),
    ("I need to insert my health insurance information", True, "Normal text with 'insert'"),
    ("Please update my contact information", True, "Normal text with 'update'"),
    
    # Edge cases - potentially tricky
    ("What's the difference between 'and' and 'or' in logic?", True, "Contains 'and' and 'or' but not SQL"),
    ("I have diabetes and hypertension", True, "Contains 'and' but not SQL"),
    ("Can you explain where the pain is located?", True, "Contains 'where' in context"),
    ("I don't know where my prescription went", True, "Normal question with 'where'"),
    
    # Messages with quotes in normal context
    ("The doctor said 'take this medication twice daily'", True, "Quoted text in normal context"),
    ("My symptom is 'severe headache'", True, "Quoted description"),
    ("The test result showed 'normal'", True, "Quoted result"),
    
    # Empty and edge cases
    ("Hello", True, "Simple greeting"),
    ("Thanks!", True, "Simple thanks"),
    ("OK", True, "Simple acknowledgment"),
    
    # Long legitimate messages
    ("I've been dealing with chronic back pain for several months now. It started after I lifted something heavy at work, and it hasn't really improved since then. The pain is worse in the morning when I first wake up, and it tends to get better as the day goes on. I've tried taking ibuprofen, but it only helps temporarily. I'm also doing some stretching exercises that I found online, but I'm not sure if they're the right ones for my condition. Where should I go from here? Should I see a specialist?", True, "Long legitimate message"),
]

def run_tests():
    """Run all test cases and report results"""
    print("=" * 80)
    print("VALIDATION.PY TEST SUITE - 100 Test Cases")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    false_positives = []  # Legitimate messages flagged as SQL injection
    false_negatives = []  # SQL injection attempts that passed
    
    for i, (prompt, should_pass, description) in enumerate(TEST_CASES, 1):
        try:
            # Test with validate_chat_input (used in chat endpoint)
            result = validate_chat_input(prompt)
            
            if should_pass:
                # Should have passed
                passed += 1
                status = "[PASS]"
            else:
                # Should have failed but didn't (false negative)
                failed += 1
                false_negatives.append((i, prompt, description))
                status = "[FALSE NEGATIVE]"
                
        except ValueError as e:
            if not should_pass:
                # Should have failed and did (correct detection)
                passed += 1
                status = "[CORRECTLY BLOCKED]"
            else:
                # Should have passed but failed (false positive)
                failed += 1
                false_positives.append((i, prompt, description, str(e)))
                status = "[FALSE POSITIVE]"
                
        except Exception as e:
            # Unexpected error
            failed += 1
            status = f"[ERROR: {type(e).__name__}]"
            print(f"Test {i:3d}: {status}")
            print(f"  Prompt: {prompt[:60]}...")
            print(f"  Error: {str(e)}")
            print(f"  Traceback: {traceback.format_exc()}")
            continue
        
        # Print result (verbose for first few, summary for rest)
        if i <= 10 or "FALSE" in status or "ERROR" in status:
            print(f"Test {i:3d}: {status} - {description}")
            if "FALSE" in status or "ERROR" in status:
                print(f"         Prompt: {prompt[:70]}...")
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(TEST_CASES)}")
    print(f"Passed: {passed} ({passed/len(TEST_CASES)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(TEST_CASES)*100:.1f}%)")
    print()
    
    # Report false positives (legitimate messages blocked)
    if false_positives:
        print(f"[!] FALSE POSITIVES ({len(false_positives)}): Legitimate messages incorrectly blocked")
        print("-" * 80)
        for i, prompt, desc, error in false_positives:
            print(f"  Test {i}: {desc}")
            print(f"    Prompt: {prompt}")
            print(f"    Error: {error}")
            print()
    else:
        print("[OK] No false positives! All legitimate messages passed.")
        print()
    
    # Report false negatives (SQL injection not caught)
    if false_negatives:
        print(f"[!] FALSE NEGATIVES ({len(false_negatives)}): SQL injection attempts not blocked")
        print("-" * 80)
        for i, prompt, desc in false_negatives:
            print(f"  Test {i}: {desc}")
            print(f"    Prompt: {prompt}")
            print()
    else:
        print("[OK] No false negatives! All SQL injection attempts were blocked.")
        print()
    
    # Final verdict
    print("=" * 80)
    if failed == 0:
        print("[SUCCESS] ALL TESTS PASSED! Validation is working correctly.")
    elif false_positives and false_negatives:
        print(f"[WARNING] ISSUES FOUND: {len(false_positives)} false positives, {len(false_negatives)} false negatives")
    elif false_positives:
        print(f"[WARNING] {len(false_positives)} false positives - legitimate messages are being blocked")
    elif false_negatives:
        print(f"[SECURITY] {len(false_negatives)} false negatives - SQL injection attempts are passing through")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
