"""
Comprehensive SQL injection test suite with 1000+ test cases
Tests SQL injection detection while ensuring legitimate chat messages pass
"""
import sys
import re
from typing import List, Tuple


# Copy of validate_chat_input function from validation.py (standalone version)
def validate_chat_input(text: str) -> str:
    """
    Validate chat input text (standalone version for testing)
    """
    if not text or not isinstance(text, str):
        raise ValueError("Chat text is required")
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Check length
    if len(text) > 5000:
        raise ValueError("Chat text is too long (maximum 5000 characters)")
    
    # Check for SQL injection - use more lenient patterns for chat messages
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
        
        # SQL DML statements
        r"\b(SELECT|INSERT|DELETE)\s+(?:\*|[\w,\s]+)\s+(FROM|INTO)\s+\w+\s+(WHERE|;|--|\s+(UNION|OR|AND))",
        r"\bUPDATE\s+\w+\s+SET\s+",
        
        # Quoted strings followed by SQL operators
        r"['\"][^'\"]*['\"]\s+(OR|AND|UNION)\s+",
    ]
    
    for pattern in chat_sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Invalid input: potentially dangerous content detected")
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > 5000:
        text = text[:5000]
    
    return text


def generate_test_cases() -> List[Tuple[str, bool, str]]:
    """
    Generate comprehensive test cases
    Returns: List of (prompt, should_pass, description) tuples
    """
    test_cases = []
    
    # ========== LEGITIMATE CHAT MESSAGES (Should PASS) ==========
    
    # Basic health questions
    legitimate_health = [
        ("I have a headache. What should I do?", True, "Basic health question"),
        ("I'm feeling sick today", True, "Feeling sick message"),
        ("What are the symptoms of flu?", True, "Symptom inquiry"),
        ("Can you help me understand my medication?", True, "Medication question"),
        ("I need to see a doctor. Where should I go?", True, "Doctor location question"),
        ("My blood pressure is high. What does that mean?", True, "Blood pressure question"),
        ("I've been coughing for a week", True, "Cough symptom"),
        ("What's the best treatment for fever?", True, "Treatment question"),
        ("I don't feel well. Can you help?", True, "General help request"),
        ("How can I improve my sleep?", True, "Sleep improvement question"),
        ("I'd like to know more about diabetes", True, "Contraction: I'd"),
        ("What's the best medicine for pain?", True, "Contraction: What's"),
        ("I'm experiencing chest pain", True, "Contraction: I'm"),
        ("You're very helpful", True, "Contraction: You're"),
        ("It's been a week since I felt better", True, "Contraction: It's"),
        ("I don't understand this prescription", True, "Contraction: don't"),
        ("Let's talk about my symptoms", True, "Contraction: Let's"),
        ("I can't sleep at night", True, "Contraction: can't"),
        ("That's not what I expected", True, "Contraction: That's"),
        ("Where's the nearest pharmacy?", True, "Contraction: Where's"),
        ("Where should I go for treatment?", True, "Natural 'where' usage"),
        ("I need to select a doctor from the list", True, "Natural 'select' usage"),
        ("Can you help me insert my insurance information?", True, "Natural 'insert' usage"),
        ("Please update my appointment time", True, "Natural 'update' usage"),
        ("Can you delete my old messages?", True, "Natural 'delete' usage"),
        ("I have diabetes and hypertension", True, "Natural 'and' usage"),
        ("Should I take this with or without food?", True, "Natural 'or' usage"),
        ("My blood pressure is 140/90", True, "Blood pressure numbers"),
        ("I take 2 pills daily at 8 AM and 8 PM", True, "Dosage with times"),
        ("The doctor said 'take this twice daily'", True, "Quoted instruction"),
        ("My symptom is 'severe headache'", True, "Quoted symptom"),
        ("Hello", True, "Simple greeting"),
        ("Thanks!", True, "Simple thanks"),
        ("मुझे सिरदर्द हो रहा है", True, "Hindi text - should pass"),
    ]
    test_cases.extend(legitimate_health)
    
    # Generate more legitimate messages programmatically
    symptoms = ["headache", "fever", "cough", "sore throat", "back pain", "chest pain"]
    for symptom in symptoms:
        test_cases.append((f"I have a {symptom}. What should I do?", True, f"Symptom question: {symptom}"))
    
    # ========== SQL INJECTION ATTEMPTS (Should FAIL) ==========
    
    # Classic SQL injection patterns
    sql_classic = [
        ("' OR '1'='1", False, "Classic OR bypass"),
        ("' OR 1=1--", False, "OR 1=1 with comment"),
        ("' OR '1'='1'--", False, "OR with quotes and comment"),
        ("' OR 1=1#", False, "OR with hash comment"),
        ("admin'--", False, "Username with comment"),
        ("' OR 'x'='x", False, "OR with x pattern"),
        ("1' OR '1'='1", False, "Number with OR bypass"),
        ("' OR 1=1 OR 'a'='a", False, "Multiple OR conditions"),
        ("' OR '1'='1' AND '1'='1", False, "OR and AND combination"),
    ]
    test_cases.extend(sql_classic)
    
    # SQL injection with UNION
    sql_union = [
        ("' UNION SELECT * FROM users--", False, "UNION SELECT all columns"),
        ("' UNION SELECT null, null--", False, "UNION SELECT with nulls"),
        ("' UNION SELECT username, password FROM users--", False, "UNION SELECT specific columns"),
        ("' UNION ALL SELECT * FROM admin--", False, "UNION ALL SELECT"),
        ("UNION SELECT * FROM users", False, "UNION SELECT without prefix"),
        ("' UNION SELECT * FROM information_schema.tables--", False, "UNION SELECT system tables"),
        ("' UNION SELECT user(), database(), version()--", False, "UNION SELECT functions"),
        ("admin' UNION SELECT 1,2,3--", False, "Username with UNION SELECT"),
    ]
    test_cases.extend(sql_union)
    
    # SQL injection with semicolons
    sql_semicolon = [
        ("'; DROP TABLE users; --", False, "DROP TABLE with semicolon"),
        ("'; DELETE FROM users--", False, "DELETE with semicolon"),
        ("'; SELECT * FROM users--", False, "SELECT with semicolon"),
        ("'; INSERT INTO users VALUES (1, 'hacker')--", False, "INSERT with semicolon"),
        ("'; UPDATE users SET password='hacked'--", False, "UPDATE with semicolon"),
        ("test'; SELECT * FROM users--", False, "Text with SELECT after semicolon"),
        ("'; DELETE FROM sessions;--", False, "DELETE from sessions"),
        ("'; DROP TABLE patients; SELECT 1--", False, "Multiple statements"),
        ("'; TRUNCATE TABLE logs--", False, "TRUNCATE with semicolon"),
    ]
    test_cases.extend(sql_semicolon)
    
    # SQL injection with DDL
    sql_ddl = [
        ("'; DROP TABLE users--", False, "DROP TABLE"),
        ("'; DROP DATABASE health_db--", False, "DROP DATABASE"),
        ("'; CREATE TABLE test (id int)--", False, "CREATE TABLE"),
        ("'; ALTER TABLE users ADD COLUMN hacked varchar(255)--", False, "ALTER TABLE"),
        ("'; TRUNCATE TABLE logs--", False, "TRUNCATE TABLE"),
        ("DROP TABLE users", False, "DROP TABLE standalone"),
        ("CREATE TABLE test (id int)", False, "CREATE TABLE standalone"),
        ("ALTER TABLE users ADD COLUMN test varchar(100)", False, "ALTER TABLE standalone"),
        ("TRUNCATE TABLE sessions", False, "TRUNCATE TABLE standalone"),
    ]
    test_cases.extend(sql_ddl)
    
    # SQL injection with WHERE clauses
    sql_where = [
        ("SELECT * FROM users WHERE id='1' OR '1'='1", False, "SELECT with WHERE OR"),
        ("SELECT * FROM customers WHERE email='admin' OR 1=1--", False, "SELECT WHERE OR"),
        ("DELETE FROM messages WHERE user_id='1' OR '1'='1", False, "DELETE WHERE OR"),
        ("UPDATE users SET password='hacked' WHERE id=1 OR 1=1", False, "UPDATE WHERE OR"),
    ]
    test_cases.extend(sql_where)
    
    # SQL injection with EXEC/EXECUTE
    sql_exec = [
        ("'; EXEC xp_cmdshell('rm -rf /')--", False, "EXEC xp_cmdshell"),
        ("'; EXECUTE sp_executesql 'SELECT * FROM users'--", False, "EXECUTE sp_executesql"),
        ("'; EXEC('SELECT * FROM users')--", False, "EXEC with SELECT"),
    ]
    test_cases.extend(sql_exec)
    
    # SQL injection with comments
    sql_comments = [
        ("admin'--", False, "Username with SQL comment"),
        ("'--", False, "Quote with comment"),
        ("'/*", False, "Quote with block comment start"),
        ("*/'", False, "Block comment end with quote"),
        ("'/**/", False, "Quote with empty block comment"),
        ("test'/*comment*/", False, "Text with block comment"),
    ]
    test_cases.extend(sql_comments)
    
    # SQL injection with AND conditions
    sql_and = [
        ("admin' AND '1'='1", False, "Username with AND condition"),
        ("' AND 1=1--", False, "AND 1=1 with comment"),
        ("' AND 'x'='x", False, "AND with x pattern"),
        ("' AND '1'='1'--", False, "AND with quotes and comment"),
        ("1' AND '1'='1", False, "Number with AND bypass"),
    ]
    test_cases.extend(sql_and)
    
    # SQL injection variations (case, spacing)
    sql_variations = [
        ("' Or '1'='1", False, "OR with capital O"),
        ("' oR '1'='1", False, "OR with mixed case"),
        ("' OR'1'='1", False, "OR without space after"),
        ("'OR '1'='1", False, "OR without space before"),
        ("'OR'1'='1", False, "OR without spaces"),
        ("'  OR  '1'='1", False, "OR with extra spaces"),
        ("' OR '1' = '1", False, "OR with spaces around equals"),
        ("' OR '1'='1' OR '2'='2", False, "Multiple OR conditions"),
    ]
    test_cases.extend(sql_variations)
    
    # SQL injection with time-based delays
    sql_time_based = [
        ("'; WAITFOR DELAY '00:00:05'--", False, "SQL Server time delay"),
        ("'; SELECT SLEEP(5)--", False, "MySQL time delay"),
        ("'; pg_sleep(5)--", False, "PostgreSQL time delay"),
    ]
    test_cases.extend(sql_time_based)
    
    # SQL injection with stacked queries
    sql_stacked = [
        ("'; INSERT INTO users (username) VALUES ('hacker');--", False, "Stacked INSERT"),
        ("'; UPDATE users SET active=0; DELETE FROM logs;--", False, "Multiple stacked queries"),
        ("test'; DROP TABLE users; SELECT 1;--", False, "Stacked DROP and SELECT"),
    ]
    test_cases.extend(sql_stacked)
    
    # SQL injection with boolean-based blind
    sql_boolean = [
        ("' AND 1=1--", False, "Boolean-based 1=1"),
        ("' AND 1=2--", False, "Boolean-based 1=2"),
    ]
    test_cases.extend(sql_boolean)
    
    # Generate many more SQL injection variations programmatically to reach 1000+
    base_sql_patterns = [
        ("' OR '1'='1", "Classic OR bypass"),
        ("' OR 1=1--", "OR 1=1"),
        ("admin'--", "Username comment"),
        ("'; DROP TABLE users--", "DROP TABLE"),
        ("' UNION SELECT * FROM users--", "UNION SELECT"),
        ("' OR 'x'='x", "OR with x"),
        ("1' OR '1'='1", "Number OR bypass"),
        ("' OR 1=1#", "OR with hash"),
        ("' AND '1'='1", "AND bypass"),
        ("'; SELECT * FROM users--", "SELECT with semicolon"),
        ("'; DELETE FROM users--", "DELETE with semicolon"),
        ("'; UPDATE users SET password='test'--", "UPDATE with semicolon"),
        ("'; INSERT INTO users VALUES (1)--", "INSERT with semicolon"),
        ("' UNION SELECT null--", "UNION SELECT null"),
        ("' OR 1=1 OR 'a'='a", "Multiple OR"),
    ]
    
    prefixes = ["", "test", "admin", "user", "1", "test123", "admin123", "user1", "abc", "xyz", "123", "test1", "admin1", "user123"]
    suffixes = ["", "--", " #", "/*", "*/", "-- ", " --", "/*test*/"]
    
    for base_pattern, base_desc in base_sql_patterns:
        for prefix in prefixes:
            for suffix in suffixes:
                if prefix:
                    pattern = f"{prefix}'{base_pattern[1:]}" + suffix
                else:
                    pattern = base_pattern + suffix
                
                if pattern not in [tc[0] for tc in test_cases]:
                    test_cases.append((pattern, False, f"Variation: {base_desc}"))
    
    # Generate more SQL injection with different table names
    sql_tables = ["users", "customers", "patients", "admins", "accounts", "sessions", "logs", "messages"]
    sql_columns = ["id", "username", "password", "email", "name", "user_id", "session_id"]
    
    for table in sql_tables[:5]:
        for column in sql_columns[:3]:
            test_cases.append((f"' UNION SELECT {column} FROM {table}--", False, f"UNION SELECT from {table}"))
            test_cases.append((f"'; SELECT {column} FROM {table}--", False, f"SELECT {column} from {table}"))
            test_cases.append((f"'; DROP TABLE {table}--", False, f"DROP TABLE {table}"))
            test_cases.append((f"'; DELETE FROM {table}--", False, f"DELETE from {table}"))
    
    # Generate more legitimate messages programmatically
    legitimate_phrases = [
        "I have a headache",
        "My temperature is high",
        "I feel dizzy",
        "Can you help me",
        "What should I do",
        "I need to see a doctor",
        "Where can I find",
        "How can I treat",
        "What are the symptoms",
        "I'd like to know",
        "Please help",
        "Thank you",
        "I don't understand",
        "Can you explain",
        "I'm feeling",
        "My doctor said",
        "The medication",
        "I take",
        "My blood pressure",
        "I have diabetes",
    ]
    
    questions = [
        "What should I do?",
        "Can you help?",
        "Where should I go?",
        "How can I treat this?",
        "What are the symptoms?",
        "Is this normal?",
        "Should I see a doctor?",
        "What does this mean?",
        "Can you explain?",
        "I need help",
    ]
    
    # Generate legitimate combinations
    for phrase in legitimate_phrases[:15]:
        for question in questions[:5]:
            message = f"{phrase}. {question}"
            if message not in [tc[0] for tc in test_cases]:
                test_cases.append((message, True, "Generated legitimate message"))
    
    # Add more SQL injection with different operators
    operators = ["=", "!=", "<>", ">", "<", ">=", "<=", "LIKE", "IN"]
    for op in operators[:5]:
        test_cases.append((f"' OR 1{op}1--", False, f"OR with {op} operator"))
        test_cases.append((f"' AND 1{op}1--", False, f"AND with {op} operator"))
    
    # Add more legitimate variations
    templates = [
        ("I have {symptom}. What should I do?", True),
        ("My {measurement} is {value}. Is that normal?", True),
        ("I'd like to know more about {condition}", True),
    ]
    
    symptoms_more = ["headache", "fever", "cough", "sore throat", "back pain"]
    measurements = ["blood pressure", "temperature", "cholesterol", "blood sugar"]
    values = ["high", "low", "normal"]
    conditions = ["diabetes", "hypertension", "asthma", "arthritis"]
    
    for template, should_pass in templates[:2]:
        if '{symptom}' in template:
            for symptom in symptoms_more:
                test_cases.append((template.format(symptom=symptom), should_pass, "Template-generated legitimate"))
        elif '{measurement}' in template and '{value}' in template:
            for measurement in measurements[:3]:
                for value in values:
                    test_cases.append((template.format(measurement=measurement, value=value), should_pass, "Template-generated legitimate"))
        elif '{condition}' in template:
            for condition in conditions:
                test_cases.append((template.format(condition=condition), should_pass, "Template-generated legitimate"))
    
    return test_cases


def run_comprehensive_tests():
    """Run comprehensive test suite and generate detailed report"""
    print("=" * 80)
    print("COMPREHENSIVE SQL INJECTION TEST SUITE")
    print("=" * 80)
    print()
    
    # Generate test cases
    print("Generating test cases...")
    test_cases = generate_test_cases()
    print(f"Generated {len(test_cases)} test cases")
    print()
    
    passed = 0
    failed = 0
    false_positives = []
    false_negatives = []
    
    print("Running tests...")
    print("-" * 80)
    
    for i, (prompt, should_pass, description) in enumerate(test_cases, 1):
        try:
            result = validate_chat_input(prompt)
            
            if should_pass:
                passed += 1
            else:
                failed += 1
                false_negatives.append((i, prompt, description))
                
        except ValueError as e:
            if not should_pass:
                passed += 1
            else:
                failed += 1
                false_positives.append((i, prompt, description, str(e)))
                
        except Exception as e:
            failed += 1
            print(f"Test {i:4d}: [ERROR] {description}")
            print(f"         Error: {type(e).__name__}: {str(e)}")
            continue
        
        # Show progress for every 100 tests
        if i % 100 == 0:
            print(f"Progress: {i}/{len(test_cases)} tests completed...")
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed} ({passed/len(test_cases)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(test_cases)*100:.1f}%)")
    print()
    
    # Report false positives
    if false_positives:
        print(f"[!] FALSE POSITIVES ({len(false_positives)}): Legitimate messages incorrectly blocked")
        print("-" * 80)
        for i, prompt, desc, error in false_positives[:20]:
            print(f"  Test {i:4d}: {desc}")
            print(f"    Prompt: {prompt}")
            print()
        if len(false_positives) > 20:
            print(f"  ... and {len(false_positives) - 20} more false positives")
            print()
    else:
        print("[OK] No false positives! All legitimate messages passed.")
        print()
    
    # Report false negatives
    if false_negatives:
        print(f"[CRITICAL] FALSE NEGATIVES ({len(false_negatives)}): SQL injection attempts NOT BLOCKED")
        print("-" * 80)
        for i, prompt, desc in false_negatives[:50]:
            print(f"  Test {i:4d}: {desc}")
            print(f"    Prompt: {prompt}")
            print()
        if len(false_negatives) > 50:
            print(f"  ... and {len(false_negatives) - 50} more false negatives")
            print()
    else:
        print("[OK] No false negatives! All SQL injection attempts were blocked.")
        print()
    
    # Final verdict
    print("=" * 80)
    if failed == 0:
        print("[SUCCESS] ALL TESTS PASSED! Validation is working correctly.")
    elif false_negatives:
        print(f"[CRITICAL] {len(false_negatives)} SQL injection attempts are passing through!")
        print("   This is a security issue that needs immediate attention.")
    elif false_positives:
        print(f"[WARNING] {len(false_positives)} legitimate messages are being blocked.")
    else:
        print(f"[WARNING] {failed} tests failed (check output above for details)")
    print("=" * 80)
    print()
    
    # Save detailed report
    with open("sql_injection_test_report.txt", "w", encoding="utf-8") as f:
        f.write("SQL INJECTION TEST REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total Tests: {len(test_cases)}\n")
        f.write(f"Passed: {passed} ({passed/len(test_cases)*100:.1f}%)\n")
        f.write(f"Failed: {failed} ({failed/len(test_cases)*100:.1f}%)\n\n")
        
        if false_positives:
            f.write(f"FALSE POSITIVES ({len(false_positives)}):\n")
            f.write("-" * 80 + "\n")
            for i, prompt, desc, error in false_positives:
                f.write(f"Test {i:4d}: {desc}\n")
                f.write(f"  Prompt: {prompt}\n\n")
        
        if false_negatives:
            f.write(f"FALSE NEGATIVES ({len(false_negatives)}):\n")
            f.write("-" * 80 + "\n")
            for i, prompt, desc in false_negatives:
                f.write(f"Test {i:4d}: {desc}\n")
                f.write(f"  Prompt: {prompt}\n\n")
    
    print(f"Detailed report saved to: sql_injection_test_report.txt")
    
    return {
        "total": len(test_cases),
        "passed": passed,
        "failed": failed,
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "false_positive_list": false_positives,
        "false_negative_list": false_negatives,
    }


if __name__ == "__main__":
    results = run_comprehensive_tests()
    sys.exit(0 if results["failed"] == 0 else 1)
