import csv
from pathlib import Path
from .client import neo4j_client


def create_constraints():
    """Create uniqueness constraints for node types"""
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Symptom) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Condition) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Action) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Provider) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Location) REQUIRE n.city IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Advice) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Guideline) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Service) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Contact) REQUIRE n.phone IS UNIQUE"
    ]
    
    print("Creating constraints...")
    for constraint in constraints:
        try:
            neo4j_client.run_cypher(constraint)
            print(f"  [OK] {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
        except Exception as e:
            print(f"  [WARN] Constraint may already exist: {e}")


def ingest_triples_from_csv(csv_path: Path, file_name: str = ""):
    """Ingest triples from a CSV file"""
    print(f"\nIngesting triples from {csv_path.name}...")
    
    if not csv_path.exists():
        print(f"  [SKIP] File not found: {csv_path}")
        return 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        triples = list(reader)
    
    print(f"  Found {len(triples)} triples to ingest")
    
    # Process triples in batches
    batch_size = 50
    ingested_count = 0
    
    for i in range(0, len(triples), batch_size):
        batch = triples[i:i + batch_size]
        
        for triple in batch:
            subject = triple['subject']
            predicate = triple['predicate']
            obj = triple['object']
            type_s = triple['type_s']
            type_o = triple['type_o']
            
            # Create Cypher query to merge nodes and relationship
            query = f"""
            MERGE (s:{type_s} {{name: $subject}})
            MERGE (o:{type_o} {{name: $object}})
            MERGE (s)-[r:{predicate}]->(o)
            """
            
            try:
                neo4j_client.run_cypher(query, {
                    'subject': subject,
                    'object': obj
                })
                ingested_count += 1
            except Exception as e:
                print(f"  [WARN] Error ingesting triple: {subject} -> {predicate} -> {obj}: {e}")
        
        print(f"  Processed {min(i + batch_size, len(triples))}/{len(triples)} triples")
    
    print(f"  [DONE] Ingested {ingested_count} triples from {csv_path.name}")
    return ingested_count


def ingest_triples():
    """Ingest triples from all CSV files"""
    script_dir = Path(__file__).parent
    
    # Ingest from seed.csv (main data)
    seed_csv = script_dir / "seed.csv"
    count1 = ingest_triples_from_csv(seed_csv, "seed.csv")
    
    # Ingest from symptom_relationships.csv (symptom relationship feature)
    symptom_csv = script_dir / "symptom_relationships.csv"
    count2 = ingest_triples_from_csv(symptom_csv, "symptom_relationships.csv")
    
    total = count1 + count2
    print(f"\n[COMPLETE] Total triples ingested: {total} (seed.csv: {count1}, symptom_relationships.csv: {count2})")


def verify_ingestion():
    """Verify the ingestion by counting nodes and relationships"""
    print("\nVerifying ingestion...")
    
    # Count nodes by type
    node_types = ["Symptom", "Condition", "Action", "Provider", "Location", "Advice", "Guideline", "Service", "Contact"]
    
    for node_type in node_types:
        query = f"MATCH (n:{node_type}) RETURN count(n) as count"
        result = neo4j_client.run_cypher(query)
        count = result[0]['count'] if result else 0
        if count > 0:
            print(f"  {node_type}: {count} nodes")
    
    # Count relationships
    query = "MATCH ()-[r]->() RETURN count(r) as count"
    result = neo4j_client.run_cypher(query)
    rel_count = result[0]['count'] if result else 0
    print(f"  Total relationships: {rel_count}")


def main():
    """Main ingestion process"""
    print("=" * 60)
    print("Neo4j Graph Database Ingestion")
    print("=" * 60)
    
    # Connect to Neo4j
    if not neo4j_client.connect():
        print("\n[ERROR] Cannot connect to Neo4j. Please ensure:")
        print("  1. Neo4j is running (docker or local)")
        print("  2. Connection details in .env are correct")
        print("  3. Default: bolt://localhost:7687, neo4j/testpass")
        return
    
    try:
        # Create constraints
        create_constraints()
        
        # Ingest triples
        ingest_triples()
        
        # Verify
        verify_ingestion()
        
        print("\n[DONE] Graph database setup complete!")
        
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()