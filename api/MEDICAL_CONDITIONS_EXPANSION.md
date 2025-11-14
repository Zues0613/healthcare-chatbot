# Medical Conditions Expansion Guide

## Current Limitation

The current schema only supports **3 medical conditions** as separate boolean columns:
- `diabetes` (BOOLEAN)
- `hypertension` (BOOLEAN)  
- `pregnancy` (BOOLEAN)

This is **too limited** for a healthcare chatbot that needs to handle many conditions.

## Why Only These Three?

These three were chosen initially because:
1. **Pregnancy** - Critical for medication safety (many drugs are unsafe during pregnancy)
2. **Diabetes** - Very common condition affecting medication choices
3. **Hypertension** - Common condition affecting medication and lifestyle recommendations

However, there are **many other important conditions**:
- Asthma
- Heart disease / Cardiovascular conditions
- Kidney disease
- Liver disease
- Epilepsy / Seizure disorders
- Thyroid conditions (hypothyroidism, hyperthyroidism)
- Autoimmune diseases
- Allergies (medication, food, environmental)
- Mental health conditions
- And many more...

## Solution: Flexible Medical Conditions Storage

### Option 1: JSONB Array (Recommended)

Add a `medical_conditions` JSONB column that stores an array of conditions:

```sql
ALTER TABLE customers 
ADD COLUMN medical_conditions JSONB DEFAULT '[]'::jsonb;
```

**Advantages:**
- ✅ Flexible - can store any number of conditions
- ✅ Easy to query with PostgreSQL JSONB operators
- ✅ Can store additional metadata (diagnosis date, severity, etc.)
- ✅ No schema changes needed for new conditions

**Example data:**
```json
["diabetes", "asthma", "heart_disease", "allergy_penicillin"]
```

### Option 2: Separate Conditions Table

Create a `customer_conditions` table for many-to-many relationship:

```sql
CREATE TABLE customer_conditions (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    condition_name VARCHAR(100),
    diagnosed_date DATE,
    severity VARCHAR(20),
    notes TEXT
);
```

**Advantages:**
- ✅ Normalized database design
- ✅ Can store metadata per condition
- ✅ Easy to query and filter

**Disadvantages:**
- ❌ More complex queries (requires JOINs)
- ❌ More tables to manage

### Recommended Approach: Hybrid

**Keep critical conditions as boolean columns:**
- `pregnancy` - Critical for immediate safety filtering
- `diabetes` - Very common, used frequently
- `hypertension` - Very common, used frequently

**Add flexible storage for other conditions:**
- `medical_conditions` JSONB array for additional conditions
- `metadata` JSONB for condition-specific details

**Example:**
```json
{
  "diabetes": true,           // Quick boolean check
  "hypertension": true,      // Quick boolean check
  "pregnancy": false,         // Quick boolean check
  "medical_conditions": [     // Flexible array
    "asthma",
    "heart_disease",
    "kidney_disease"
  ],
  "metadata": {               // Additional details
    "allergies": ["penicillin", "sulfa"],
    "medications": ["aspirin", "metformin"],
    "conditions_details": {
      "asthma": {"diagnosed": "2020", "severity": "mild"},
      "heart_disease": {"diagnosed": "2018", "type": "coronary_artery_disease"}
    }
  }
}
```

## Implementation

### Step 1: Run Migration

```bash
cd api
python scripts/migrate_add_medical_conditions.py
```

This will:
1. Add `medical_conditions` JSONB column
2. Create an index for efficient querying
3. Migrate existing boolean conditions to the array

### Step 2: Update Profile Model

Update `api/models.py` to support conditions array:

```python
class Profile(BaseModel):
    age: Optional[int] = None
    sex: Optional[Literal["male", "female", "other"]] = None
    diabetes: bool = False
    hypertension: bool = False
    pregnancy: bool = False
    city: Optional[str] = None
    medical_conditions: List[str] = []  # NEW: Array of conditions
```

### Step 3: Update Database Service

Update `api/database/service.py` to handle the conditions array when creating/updating customers.

### Step 4: Update Chat Logic

Update `api/main.py` to check both boolean fields and the conditions array when filtering contraindications.

## Common Medical Conditions to Support

### High Priority (Common + High Impact)
- `asthma` - Affects medication choices
- `heart_disease` - Critical for medication safety
- `kidney_disease` - Affects medication dosing
- `liver_disease` - Affects medication metabolism
- `epilepsy` - Many drug interactions
- `thyroid_disorder` - Common condition

### Medium Priority
- `copd` - Chronic obstructive pulmonary disease
- `arthritis` - Common condition
- `osteoporosis` - Common in elderly
- `anemia` - Common condition
- `depression` - Mental health condition
- `anxiety` - Mental health condition

### Allergies (Critical for Safety)
- `allergy_penicillin`
- `allergy_sulfa`
- `allergy_aspirin`
- `allergy_iodine`
- `allergy_latex`
- Food allergies (peanuts, shellfish, etc.)

## Querying Conditions

### Check if user has a condition:
```sql
-- Check boolean column
SELECT * FROM customers WHERE diabetes = TRUE;

-- Check JSONB array
SELECT * FROM customers 
WHERE medical_conditions @> '["asthma"]'::jsonb;

-- Check multiple conditions
SELECT * FROM customers 
WHERE medical_conditions @> '["asthma", "heart_disease"]'::jsonb;
```

### Get all conditions for a user:
```sql
SELECT 
    id,
    email,
    diabetes,
    hypertension,
    pregnancy,
    medical_conditions
FROM customers
WHERE id = $1;
```

## Next Steps

1. **Run the migration** to add the `medical_conditions` column
2. **Update the Profile model** to accept conditions array
3. **Update the frontend** to allow users to select multiple conditions
4. **Update the chatbot logic** to use all conditions for safety filtering
5. **Expand Neo4j seed data** to include contraindications for more conditions

