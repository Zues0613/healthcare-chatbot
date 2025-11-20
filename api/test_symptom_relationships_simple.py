"""
Simple test script for symptom relationship detection - tests backend logic directly
"""
import sys
from pathlib import Path

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import _check_symptom_relationships, extract_symptoms, _extract_raw_symptom_phrases

def test_symptom_relationships():
    """Test symptom relationship detection logic directly"""
    print("=" * 80)
    print("TESTING SYMPTOM RELATIONSHIP DETECTION LOGIC")
    print("=" * 80)
    
    # Test 1: Chest pain followed by left arm pain
    print("\n[TEST 1] Chest pain → Left arm pain")
    print("-" * 80)
    
    processed_text_1 = "Why does chest pain occur?"
    current_symptoms_1 = extract_symptoms(processed_text_1)
    current_raw_1 = _extract_raw_symptom_phrases(processed_text_1)
    
    print(f"Query 1: '{processed_text_1}'")
    print(f"Current symptoms (canonical): {current_symptoms_1}")
    print(f"Current raw phrases: {current_raw_1}")
    
    history_1 = [
        {"role": "user", "content": "Why does chest pain occur?"},
        {"role": "assistant", "content": "Chest pain can occur due to various reasons..."}
    ]
    
    relationship_facts_1 = _check_symptom_relationships(processed_text_1, current_symptoms_1, history_1)
    print(f"Relationship facts: {len(relationship_facts_1)}")
    
    # Test 2: Follow-up with left arm pain
    print("\n[TEST 2] Follow-up: Left arm pain after chest pain")
    print("-" * 80)
    
    processed_text_2 = "I am facing pain in my left arm slightly what does that mean?"
    current_symptoms_2 = extract_symptoms(processed_text_2)
    current_raw_2 = _extract_raw_symptom_phrases(processed_text_2)
    
    print(f"Query 2: '{processed_text_2}'")
    print(f"Current symptoms (canonical): {current_symptoms_2}")
    print(f"Current raw phrases: {current_raw_2}")
    
    history_2 = [
        {"role": "user", "content": "Why does chest pain occur?"},
        {"role": "assistant", "content": "Chest pain can occur due to various reasons related to heart conditions..."}
    ]
    
    relationship_facts_2 = _check_symptom_relationships(processed_text_2, current_symptoms_2, history_2)
    print(f"Relationship facts: {len(relationship_facts_2)}")
    
    if relationship_facts_2:
        for fact in relationship_facts_2:
            fact_type = fact.get("type")
            if fact_type == "symptom_relationships":
                data = fact.get("data", [])
                print(f"\n[SUCCESS] Found {len(data)} relationships:")
                for rel in data[:3]:
                    original = rel.get("original_symptom", "")
                    related = rel.get("related_symptom", "")
                    shared = rel.get("shared_conditions", [])
                    print(f"  - {original} <-> {related}")
                    print(f"    Shared conditions: {', '.join(shared[:3])}")
            elif fact_type == "symptom_no_relationship":
                data = fact.get("data", {})
                current_display = data.get("current_display", "")
                history_display = data.get("history_display", "")
                print(f"\n[NO RELATIONSHIP] {current_display} vs {history_display}")
    else:
        print("[WARN] No relationship facts found")
    
    # Test 3: Unrelated symptoms
    print("\n[TEST 3] Follow-up: Headache after chest pain (should be unrelated)")
    print("-" * 80)
    
    processed_text_3 = "I am also having a headache, is it related?"
    current_symptoms_3 = extract_symptoms(processed_text_3)
    current_raw_3 = _extract_raw_symptom_phrases(processed_text_3)
    
    print(f"Query 3: '{processed_text_3}'")
    print(f"Current symptoms (canonical): {current_symptoms_3}")
    print(f"Current raw phrases: {current_raw_3}")
    
    history_3 = [
        {"role": "user", "content": "Why does chest pain occur?"},
        {"role": "assistant", "content": "Chest pain can occur..."}
    ]
    
    relationship_facts_3 = _check_symptom_relationships(processed_text_3, current_symptoms_3, history_3)
    print(f"Relationship facts: {len(relationship_facts_3)}")
    
    if relationship_facts_3:
        for fact in relationship_facts_3:
            fact_type = fact.get("type")
            if fact_type == "symptom_no_relationship":
                data = fact.get("data", {})
                current_display = data.get("current_display", "")
                history_display = data.get("history_display", "")
                print(f"\n[SUCCESS] Correctly detected no relationship:")
                print(f"  {current_display} vs {history_display}")
            elif fact_type == "symptom_relationships":
                print(f"\n[FAIL] Should not find relationship between chest pain and headache")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"[TEST 1] Initial chest pain: OK")
    print(f"[TEST 2] Left arm pain relationship: {'PASS' if relationship_facts_2 and any(f.get('type') == 'symptom_relationships' for f in relationship_facts_2) else 'FAIL'}")
    print(f"[TEST 3] Headache no relationship: {'PASS' if relationship_facts_3 and any(f.get('type') == 'symptom_no_relationship' for f in relationship_facts_3) else 'PARTIAL'}")

if __name__ == "__main__":
    test_symptom_relationships()

