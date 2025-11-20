# Recommendations for Extending seed.csv

## Current Situation

- **seed.csv**: 444 triples (445 lines including header)
- **Neo4j**: All data ingested successfully
- **Problem**: Important symptom synonyms (like "left arm pain", "jaw pain") are NOT in Neo4j as separate nodes
- **Impact**: Symptom relationship queries can't find relationships for these synonyms

## Why Extend seed.csv?

Currently, `seed.csv` was designed for **red-flag fallback** only. But for **symptom relationship detection** to work properly, we need:

1. **Separate symptom nodes** for important synonyms (not just mapped to canonical)
2. **Shared condition relationships** so symptoms can be linked through common conditions
3. **More symptom-to-condition mappings** to create relationship clusters

## Recommended Additions

### 1. Add Cardiac-Related Symptom Synonyms

These should be separate nodes with the same conditions as "Chest pain":

```csv
"Left arm pain","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Left arm pain","IS_RED_FLAG_FOR","Acute coronary syndrome","Symptom","Condition","emergency","Call emergency services immediately or go to the nearest emergency department","Sit down, stay calm, loosen tight clothing","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Left arm pain","IS_RED_FLAG_FOR","Angina","Symptom","Condition","urgent","Cardiology assessment and risk stratification","Rest and avoid exertion until evaluated","","https://www.nhs.uk/conditions/angina/","high","2025-11-10"
"Right arm pain","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Right arm pain","IS_RED_FLAG_FOR","Acute coronary syndrome","Symptom","Condition","emergency","Call emergency services immediately or go to the nearest emergency department","Sit down, stay calm, loosen tight clothing","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Jaw pain","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Jaw pain","IS_RED_FLAG_FOR","Acute coronary syndrome","Symptom","Condition","emergency","Call emergency services immediately or go to the nearest emergency department","Sit down, stay calm, loosen tight clothing","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Jaw pain","IS_RED_FLAG_FOR","Angina","Symptom","Condition","urgent","Cardiology assessment and risk stratification","Rest and avoid exertion until evaluated","","https://www.nhs.uk/conditions/angina/","high","2025-11-10"
"Shoulder pain (left)","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Back pain (upper)","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Back pain (upper)","IS_RED_FLAG_FOR","Aortic dissection","Symptom","Condition","emergency","Call emergency services immediately; urgent surgical assessment","Keep patient still and calm","","https://www.nhs.uk/conditions/aortic-dissection/","high","2025-11-10"
```

### 2. Add Stroke-Related Symptom Synonyms

These should share conditions with existing stroke symptoms:

```csv
"One-side weakness","IS_RED_FLAG_FOR","Stroke","Symptom","Condition","emergency","Call emergency services immediately","Do not give food or drink if swallowing difficulty","","https://www.nhs.uk/conditions/stroke/","high","2025-11-10"
"Face drooping","IS_RED_FLAG_FOR","Stroke","Symptom","Condition","emergency","Call emergency services immediately","Keep person still; note time of symptom onset","","https://www.nhs.uk/conditions/stroke/","high","2025-11-10"
"Slurred speech","IS_RED_FLAG_FOR","Stroke","Symptom","Condition","emergency","Call emergency services immediately","Keep person comfortable and note time of onset","","https://www.nhs.uk/conditions/stroke/","high","2025-11-10"
"Sudden vision loss","IS_RED_FLAG_FOR","Stroke","Symptom","Condition","emergency","Seek emergency ophthalmic or stroke care immediately","Avoid bright lights and note time of onset","","https://www.nhs.uk/conditions/stroke/","high","2025-11-10"
```

### 3. Add More Shared Condition Relationships

Add relationships that create symptom clusters:

```csv
"Cold sweats","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Nausea with chest pain","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
"Lightheadedness with chest pain","IS_RED_FLAG_FOR","Heart attack","Symptom","Condition","emergency","Call emergency services immediately; aspirin if advised by a clinician","Rest and avoid exertion","","https://www.nhs.uk/conditions/heart-attack/","high","2025-11-10"
```

## How This Improves Relationships

### Before Extension:
- "Chest pain" → "Heart attack"
- "Left arm pain" → NOT in Neo4j (only in SYMPTOM_SYNONYMS)
- **Result**: No relationship found between "chest pain" and "left arm pain"

### After Extension:
- "Chest pain" → "Heart attack"
- "Left arm pain" → "Heart attack" (NEW)
- **Result**: Relationship found! Both share "Heart attack" condition

## Implementation Steps

1. **Add the new rows** to `api/graph/seed.csv`
2. **Run ingestion**: `python -m api.graph.ingest`
3. **Verify**: Run `python verify_neo4j_data.py` to confirm new relationships
4. **Test**: Query symptom relationships to see improvements

## Priority Additions

**High Priority** (for common follow-up questions):
- Left arm pain → Heart attack, Acute coronary syndrome, Angina
- Right arm pain → Heart attack, Acute coronary syndrome
- Jaw pain → Heart attack, Acute coronary syndrome, Angina
- Cold sweats → Heart attack

**Medium Priority** (for better symptom clusters):
- Shoulder pain → Heart attack
- Back pain (upper) → Heart attack, Aortic dissection
- Nausea with chest pain → Heart attack
- Lightheadedness with chest pain → Heart attack

**Low Priority** (for comprehensive coverage):
- Other stroke-related synonyms
- Other symptom combinations

## Expected Impact

After adding these relationships:
- ✅ "Left arm pain" after "Chest pain" → Relationship found
- ✅ "Jaw pain" after "Chest pain" → Relationship found
- ✅ Better symptom clustering for cardiac conditions
- ✅ More accurate "no relationship" detection for unrelated symptoms

