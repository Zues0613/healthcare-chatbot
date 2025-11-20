from .client import neo4j_client, run_cypher
from typing import List, Dict


def get_red_flags(symptoms: List[str]) -> List[Dict]:
    """
    Query 1: Get conditions that match red flag symptoms
    
    Args:
        symptoms: List of symptom names (will be lowercased)
        
    Returns:
        List of dicts with symptom and associated conditions
    """
    query = """
    MATCH (s:Symptom)-[:IS_RED_FLAG_FOR]->(c:Condition)
    WHERE toLower(s.name) IN $symptoms
    RETURN s.name AS symptom, collect(DISTINCT c.name) AS conditions
    """
    
    # Lowercase all symptoms for case-insensitive matching
    symptoms_lower = [s.lower() for s in symptoms]
    
    try:
        # Ensure connection is available (will use persistent connection pool)
        if not neo4j_client.is_connected():
            neo4j_client.connect()
        results = run_cypher(query, {"symptoms": symptoms_lower})
        return results
    except Exception as e:
        print(f"Error in get_red_flags: {e}")
        return []


def get_contraindications(user_conditions: List[str]) -> List[Dict]:
    """
    Query 2: Get actions/medications to avoid based on user's conditions
    
    Args:
        user_conditions: List of condition names the user has
        
    Returns:
        List of dicts with actions to avoid and reasons
    """
    query = """
    MATCH (a:Action)-[:AVOID_IN]->(c:Condition)
    WHERE c.name IN $userConditions
    RETURN DISTINCT a.name AS avoid, collect(DISTINCT c.name) AS because
    """
    
    try:
        results = run_cypher(query, {"userConditions": user_conditions})
        return results
    except Exception as e:
        print(f"Error in get_contraindications: {e}")
        return []


def get_safe_actions_for_metabolic_conditions() -> List[Dict]:
    """
    Query 3: Get actions considered safe for diabetes and hypertension profiles
    """
    query = """
    MATCH (a:Action)
    WHERE NOT (a)-[:AVOID_IN]->(:Condition {name:"Diabetes"})
      AND NOT (a)-[:AVOID_IN]->(:Condition {name:"Hypertension"})
    RETURN DISTINCT a.name AS safeAction
    """
    
    try:
        results = run_cypher(query)
        return results
    except Exception as e:
        print(f"Error in get_safe_actions_for_metabolic_conditions: {e}")
        return []


def get_providers_in_city(city: str) -> List[Dict]:
    """
    Query 3: Get healthcare providers in a specific city
    
    Args:
        city: City name
        
    Returns:
        List of dicts with provider info
    """
    query = """
    MATCH (p:Provider)-[:LOCATED_IN]->(l:Location {city: $city})
    OPTIONAL MATCH (p)-[:HAS_MODE]->(s:Service)
    OPTIONAL MATCH (p)-[:HAS_PHONE]->(c:Contact)
    RETURN p.name AS provider, 
           s.name AS mode, 
           c.phone AS phone
    """
    
    try:
        results = run_cypher(query, {"city": city})
        return results
    except Exception as e:
        print(f"Error in get_providers_in_city: {e}")
        return []


def get_related_symptoms(symptoms: List[str]) -> List[Dict]:
    """
    Query: Find symptoms that are related to the given symptoms through shared conditions
    This helps identify symptom clusters (e.g., chest pain and left arm pain both related to heart attack)
    
    Checks both IS_RED_FLAG_FOR and IS_ASSOCIATED_WITH relationships to find all possible connections.
    
    Args:
        symptoms: List of symptom names (will be lowercased)
        
    Returns:
        List of dicts with related symptoms and shared conditions
        Format: [{"related_symptom": "left arm pain", "shared_conditions": ["Heart attack", "Angina"], "original_symptom": "chest pain"}]
    """
    # Query for IS_RED_FLAG_FOR relationships
    query_red_flag = """
    MATCH (s1:Symptom)-[:IS_RED_FLAG_FOR]->(c:Condition)<-[:IS_RED_FLAG_FOR]-(s2:Symptom)
    WHERE toLower(s1.name) IN $symptoms 
      AND toLower(s2.name) <> toLower(s1.name)
    RETURN s1.name AS original_symptom, 
           s2.name AS related_symptom, 
           collect(DISTINCT c.name) AS shared_conditions,
           'IS_RED_FLAG_FOR' AS relationship_type
    """
    
    # Query for IS_ASSOCIATED_WITH relationships
    query_associated = """
    MATCH (s1:Symptom)-[:IS_ASSOCIATED_WITH]->(c:Condition)<-[:IS_ASSOCIATED_WITH]-(s2:Symptom)
    WHERE toLower(s1.name) IN $symptoms 
      AND toLower(s2.name) <> toLower(s1.name)
    RETURN s1.name AS original_symptom, 
           s2.name AS related_symptom, 
           collect(DISTINCT c.name) AS shared_conditions,
           'IS_ASSOCIATED_WITH' AS relationship_type
    """
    
    # Query for mixed relationships (one symptom uses IS_RED_FLAG_FOR, other uses IS_ASSOCIATED_WITH)
    query_mixed = """
    MATCH (s1:Symptom)-[:IS_RED_FLAG_FOR]->(c:Condition)<-[:IS_ASSOCIATED_WITH]-(s2:Symptom)
    WHERE toLower(s1.name) IN $symptoms 
      AND toLower(s2.name) <> toLower(s1.name)
    RETURN s1.name AS original_symptom, 
           s2.name AS related_symptom, 
           collect(DISTINCT c.name) AS shared_conditions,
           'MIXED' AS relationship_type
    UNION
    MATCH (s1:Symptom)-[:IS_ASSOCIATED_WITH]->(c:Condition)<-[:IS_RED_FLAG_FOR]-(s2:Symptom)
    WHERE toLower(s1.name) IN $symptoms 
      AND toLower(s2.name) <> toLower(s1.name)
    RETURN s1.name AS original_symptom, 
           s2.name AS related_symptom, 
           collect(DISTINCT c.name) AS shared_conditions,
           'MIXED' AS relationship_type
    """
    
    # Lowercase all symptoms for case-insensitive matching
    symptoms_lower = [s.lower() for s in symptoms]
    
    all_results = []
    
    try:
        # Ensure connection is available (will use persistent connection pool)
        if not neo4j_client.is_connected():
            neo4j_client.connect()
        
        # Execute all three queries and combine results
        results_red_flag = run_cypher(query_red_flag, {"symptoms": symptoms_lower})
        results_associated = run_cypher(query_associated, {"symptoms": symptoms_lower})
        results_mixed = run_cypher(query_mixed, {"symptoms": symptoms_lower})
        
        all_results.extend(results_red_flag or [])
        all_results.extend(results_associated or [])
        all_results.extend(results_mixed or [])
        
        # Merge results by symptom pairs and combine shared conditions
        merged = {}
        for result in all_results:
            original = result.get("original_symptom", "")
            related = result.get("related_symptom", "")
            conditions = result.get("shared_conditions", [])
            key = (original.lower(), related.lower())
            
            if key not in merged:
                merged[key] = {
                    "original_symptom": original,
                    "related_symptom": related,
                    "shared_conditions": set(conditions)
                }
            else:
                merged[key]["shared_conditions"].update(conditions)
        
        # Convert sets back to lists and sort by number of shared conditions
        final_results = []
        for key, value in merged.items():
            final_results.append({
                "original_symptom": value["original_symptom"],
                "related_symptom": value["related_symptom"],
                "shared_conditions": sorted(list(value["shared_conditions"]))
            })
        
        # Sort by number of shared conditions (descending)
        final_results.sort(key=lambda x: len(x.get("shared_conditions", [])), reverse=True)
        
        return final_results[:20]  # Limit to top 20
        
    except Exception as e:
        print(f"Error in get_related_symptoms: {e}")
        return []


def count_red_flags(symptoms: List[str]) -> int:
    """
    Count how many red flag symptoms are matched
    
    Args:
        symptoms: List of symptom names
        
    Returns:
        Count of matched red flags
    """
    results = get_red_flags(symptoms)
    return len(results)


def test_queries():
    """Test all query functions"""
    print("\n" + "=" * 60)
    print("Testing Cypher Queries")
    print("=" * 60)
    
    # Test 1: Red flags
    print("\n1. Testing Red Flag Query:")
    print("   Query: ['chest pain', 'shortness of breath', 'cold sweats']")
    red_flags = get_red_flags(['chest pain', 'shortness of breath', 'cold sweats'])
    for rf in red_flags:
        print(f"   [WARN] {rf['symptom']} -> {', '.join(rf['conditions'])}")
    print(f"   Total red flags matched: {len(red_flags)}")
    
    # Test 2: Contraindications
    print("\n2. Testing Contraindications Query:")
    print("   Query: User has ['Hypertension', 'Diabetes']")
    contras = get_contraindications(['Hypertension', 'Diabetes'])
    for c in contras:
        print(f"   ⛔ Avoid {c['avoid']} (because: {', '.join(c['because'])})")
    
    # Test 3: Providers
    print("\n3. Testing Provider Location Query:")
    print("   Query: Providers in 'Mumbai'")
    providers = get_providers_in_city('Mumbai')
    for p in providers:
        print(f"   🏥 {p['provider']} - {p.get('mode', 'N/A')} - {p.get('phone', 'N/A')}")
    
    print("\n[DONE] Query tests complete!")


if __name__ == "__main__":
    from client import neo4j_client
    
    if neo4j_client.connect():
        try:
            test_queries()
        finally:
            neo4j_client.close()
    else:
        print("[ERROR] Cannot connect to Neo4j for testing")