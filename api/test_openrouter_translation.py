"""
Test OpenRouter's translation capabilities for Indian languages
Tests romanized text detection and translation to English
"""
import json
import os
import re
import time
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import requests


def load_environment() -> None:
    """Load .env from api/ or project root."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, ".env"),
        os.path.join(os.path.dirname(here), ".env"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            load_dotenv(candidate)
            return
    load_dotenv()


def build_headers() -> Dict[str, str]:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY or DEEPSEEK_API_KEY not set in environment")

    referer = os.getenv("OPENROUTER_SITE_URL", "http://localhost")
    title = os.getenv("OPENROUTER_SITE_NAME", os.getenv("OPENROUTER_APP_NAME", "Healthcare Chatbot"))

    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": referer,
        "X-Title": title,
    }


def create_translation_prompt(test_text: str) -> str:
    """Create the prompt template for translation testing"""
    return f"""detect the below text language and translate it to english 

{test_text}

output from the ai should be for example :

language : tamil 

english translation : i am sick right now"""


def parse_ai_response(response_text: str) -> Tuple[str, str]:
    """
    Parse AI response to extract language and translation
    Expected format:
    language : <language>
    english translation : <translation>
    """
    language = None
    translation = None
    
    # Try to extract language
    lang_patterns = [
        r'language\s*:\s*([^\n]+)',
        r'language\s*:\s*([^\n]+)',
        r'Language\s*:\s*([^\n]+)',
    ]
    
    for pattern in lang_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            language = match.group(1).strip()
            break
    
    # Try to extract translation
    trans_patterns = [
        r'english translation\s*:\s*(.+?)(?:\n|$)',
        r'English translation\s*:\s*(.+?)(?:\n|$)',
        r'translation\s*:\s*(.+?)(?:\n|$)',
        r'Translation\s*:\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in trans_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            translation = match.group(1).strip()
            break
    
    # If no structured format found, try to extract from free text
    if not language or not translation:
        lines = response_text.strip().split('\n')
        for line in lines:
            if 'language' in line.lower() and not language:
                language = line.split(':')[-1].strip() if ':' in line else None
            if 'translation' in line.lower() and not translation:
                translation = line.split(':')[-1].strip() if ':' in line else None
    
    return language or "unknown", translation or response_text.strip()


def test_translation(test_text: str, expected_lang: str, expected_translation: str, model: str) -> Dict:
    """Test a single translation"""
    prompt = create_translation_prompt(test_text)
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 200,
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=build_headers(),
            data=json.dumps(payload),
            timeout=60,
        )
        
        if response.status_code != 200:
            return {
                "test_text": test_text,
                "expected_lang": expected_lang,
                "expected_translation": expected_translation,
                "status": "error",
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
                "detected_lang": None,
                "translation": None,
                "match": False,
            }
        
        body = response.json()
        choice = body.get("choices", [{}])[0]
        message = choice.get("message", {})
        ai_response = message.get("content", "")
        
        detected_lang, translation = parse_ai_response(ai_response)
        
        # Normalize for comparison
        detected_lang_lower = detected_lang.lower()
        expected_lang_lower = expected_lang.lower()
        
        translation_lower = translation.lower().strip()
        expected_translation_lower = expected_translation.lower().strip()
        
        # Check if translation matches (allowing for minor variations)
        translation_match = (
            translation_lower == expected_translation_lower or
            expected_translation_lower in translation_lower or
            translation_lower in expected_translation_lower
        )
        
        lang_match = (
            expected_lang_lower in detected_lang_lower or
            detected_lang_lower in expected_lang_lower
        )
        
        return {
            "test_text": test_text,
            "expected_lang": expected_lang,
            "expected_translation": expected_translation,
            "status": "success",
            "detected_lang": detected_lang,
            "translation": translation,
            "raw_response": ai_response,
            "lang_match": lang_match,
            "translation_match": translation_match,
            "overall_match": lang_match and translation_match,
        }
        
    except Exception as e:
        return {
            "test_text": test_text,
            "expected_lang": expected_lang,
            "expected_translation": expected_translation,
            "status": "error",
            "error": str(e),
            "detected_lang": None,
            "translation": None,
            "match": False,
        }


def main() -> int:
    load_environment()
    
    # Get model from environment or use default
    model = (
        os.getenv("DEEPSEEK_MODEL") or 
        os.getenv("OPENROUTER_MODEL") or 
        "deepseek/deepseek-r1-0528:free"
    )
    
    print("=" * 80)
    print("OpenRouter Translation Capability Test")
    print("=" * 80)
    print(f"Model: {model}")
    print()
    print("NOTE: This test makes multiple API calls. Free tier has rate limits.")
    print("If you hit rate limits, wait a few minutes or add credits to your account.")
    print()
    
    # Test cases: (test_text, expected_language, expected_translation)
    test_cases = [
        # Tamil (தமிழ்)
        ("naa toongitan", "tamil", "I slept"),
        ("enakku pasikuduthu", "tamil", "I am hungry"),
        ("nee epdi iruka?", "tamil", "How are you?"),
        ("naan velaila poren", "tamil", "I am going to work"),
        ("indha paatu romba nalla iruku", "tamil", "This song is really good"),
        
        # Malayalam (മലയാളം)
        ("njan kazhichu", "malayalam", "I ate"),
        ("ninakku sukhamano?", "malayalam", "Are you fine?"),
        ("ente peru anu rahul", "malayalam", "My name is Rahul"),
        ("njan veettil aanu", "malayalam", "I am at home"),
        ("ithu nalla pusthakam aanu", "malayalam", "This is a good book"),
        
        # Hindi (हिन्दी)
        ("main thak gaya hoon", "hindi", "I am tired"),
        ("tum kahan ja rahe ho?", "hindi", "Where are you going?"),
        ("mujhe bhook lagi hai", "hindi", "I am hungry"),
        ("aaj mausam bahut accha hai", "hindi", "The weather is very nice today"),
        ("mujhe yeh pasand hai", "hindi", "I like this"),
        
        # Kannada (ಕನ್ನಡ)
        ("nanu oota maadide", "kannada", "I have eaten"),
        ("neenu hegiddiya?", "kannada", "How are you?"),
        ("nan hesaru praveen", "kannada", "My name is Praveen"),
        ("nanu kelasa ge hogtha idini", "kannada", "I am going to work"),
        ("ee haadu tumba chennagide", "kannada", "This song is very nice"),
        
        # Telugu (తెలుగు)
        ("nenu tinanu", "telugu", "I ate"),
        ("nee peru emiti?", "telugu", "What is your name?"),
        ("nenu baagunnanu", "telugu", "I am fine"),
        ("idi chala manchidi", "telugu", "This is very good"),
        ("nenu intiki veltunna", "telugu", "I am going home"),
    ]
    
    results = []
    total_tests = len(test_cases)
    passed_tests = 0
    
    print(f"Running {total_tests} translation tests...")
    print()
    
    # Group by language for better output
    language_groups = {}
    for test_text, lang, translation in test_cases:
        if lang not in language_groups:
            language_groups[lang] = []
        language_groups[lang].append((test_text, translation))
    
    for lang, tests in language_groups.items():
        print(f"\n{'=' * 80}")
        print(f"Testing {lang.upper()} ({len(tests)} tests)")
        print(f"{'=' * 80}")
        print()
        
        for test_text, expected_translation in tests:
            print(f"Test: {test_text}")
            print(f"Expected: {expected_translation}")
            
            result = test_translation(test_text, lang, expected_translation, model)
            results.append(result)
            
            # Add delay to avoid rate limits (2 seconds between requests)
            if len(results) < total_tests:
                time.sleep(2)
            
            if result["status"] == "error":
                print(f"[ERROR] {result.get('error', 'Unknown error')}")
            elif result["overall_match"]:
                print(f"[PASSED]")
                print(f"   Detected Language: {result['detected_lang']}")
                print(f"   Translation: {result['translation']}")
                passed_tests += 1
            else:
                print(f"[PARTIAL/FAILED]")
                print(f"   Detected Language: {result['detected_lang']} (Expected: {lang})")
                print(f"   Translation: {result['translation']}")
                print(f"   Language Match: {result['lang_match']}")
                print(f"   Translation Match: {result['translation_match']}")
                if result.get('raw_response'):
                    print(f"   Raw Response: {result['raw_response'][:200]}")
            
            print()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed/Partial: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")
    print()
    
    # Detailed breakdown
    print("Language-wise Results:")
    for lang in language_groups.keys():
        lang_results = [r for r in results if r.get('expected_lang', '').lower() == lang.lower()]
        lang_passed = sum(1 for r in lang_results if r.get('overall_match', False))
        print(f"  {lang.capitalize()}: {lang_passed}/{len(lang_results)} passed")
    
    print()
    
    # Show failures
    failures = [r for r in results if not r.get('overall_match', False) and r['status'] == 'success']
    if failures:
        print("Failed/Partial Tests:")
        for failure in failures:
            print(f"  - '{failure['test_text']}'")
            print(f"    Expected: {failure['expected_translation']}")
            print(f"    Got: {failure['translation']}")
            print()
    
    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    raise SystemExit(main())
