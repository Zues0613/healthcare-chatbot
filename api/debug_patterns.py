"""Debug script to test regex patterns"""
import re

test_cases = [
    ("' OR '1'='1", "OR bypass"),
    ("admin'--", "comment bypass"),
    ("' UNION SELECT null, null--", "UNION with nulls"),
    ("admin' AND '1'='1", "AND condition"),
    ("'; TRUNCATE TABLE logs--", "TRUNCATE"),
    ("' OR 'x'='x", "OR with x"),
    ("1' OR '1'='1", "OR bypass with quotes"),
]

patterns = [
    (r"\w+['\"]--", "Word quote comment"),
    (r"['\"][^'\"]*--", "Quote text comment"),
    (r"['\"]\s+(OR|AND)\s+['\"]1['\"]\s*=\s*['\"]1['\"]", "OR/AND '1'='1"),
    (r"['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]", "OR/AND quoted"),
    (r"['\"]\s+(OR|AND)\s+\d+\s*=\s*\d+", "OR/AND number"),
    (r"\w+['\"]\s+(OR|AND)\s+['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"]", "Word quote OR/AND"),
    (r"['\"]?\s*;\s*(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|TRUNCATE)", "Semicolon SQL"),
    (r"['\"]?\s*UNION\s+(ALL\s+)?SELECT", "UNION SELECT"),
    (r"['\"]\s*(OR|AND)\s*['\"]?[0-9xXa-zA-Z]+['\"]?\s*=\s*['\"]?[0-9xXa-zA-Z]+['\"]?", "OR/AND loose"),
]

print("Testing patterns against SQL injection attempts:\n")
for test_str, desc in test_cases:
    print(f"Test: {test_str} ({desc})")
    matches = []
    for pattern, pattern_desc in patterns:
        if re.search(pattern, test_str, re.IGNORECASE):
            matches.append(pattern_desc)
    if matches:
        print(f"  Matches: {', '.join(matches)}")
    else:
        print(f"  NO MATCHES!")
    print()
