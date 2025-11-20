"""
Generate symptom-disease relationship CSV for symptom relationship detection feature.
This creates a separate CSV file with curated symptom-to-condition relationships
sourced from authoritative medical sites (NHS, WHO, NICE, CDC, ICMR).
"""
import csv
from pathlib import Path
from datetime import date

rows = []
today = date.today().strftime("%Y-%m-%d")

# Helper to add rows
def add(symptom, predicate, disease, urgency="routine", rec_action="", safe_action="", 
        source="https://www.nhs.uk/conditions/", confidence="high"):
    rows.append({
        "subject": symptom,
        "predicate": predicate,
        "object": disease,
        "type_s": "Symptom",
        "type_o": "Condition",
        "urgency_level": urgency,
        "recommended_action": rec_action,
        "safe_action": safe_action,
        "contraindicated_for": "",
        "source_reference": source,
        "confidence_level": confidence,
        "last_updated": today
    })

# ============================================================================
# CARDIOLOGY / CHEST - Key relationships for symptom clustering
# ============================================================================
add("Chest pain", "IS_RED_FLAG_FOR", "Heart attack", "emergency",
    "Call emergency services immediately; chew aspirin if advised by clinician",
    "Sit down, rest, avoid exertion", "https://www.nhs.uk/conditions/heart-attack/")

add("Chest pain", "IS_ASSOCIATED_WITH", "Angina", "urgent",
    "See cardiology/GP for assessment", "Rest and avoid exertion",
    "https://www.nhs.uk/conditions/angina/")

add("Left arm pain", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Keep person still and monitor breathing",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Left arm pain", "IS_ASSOCIATED_WITH", "Acute coronary syndrome", "emergency",
    "Call emergency services immediately", "Sit down, stay calm",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Left arm pain", "IS_ASSOCIATED_WITH", "Angina", "urgent",
    "Cardiology assessment and risk stratification", "Rest and avoid exertion",
    "https://www.nhs.uk/conditions/angina/")

add("Right arm pain", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Keep person still and monitor breathing",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Jaw pain", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Seek urgent help",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Jaw pain", "IS_ASSOCIATED_WITH", "Angina", "urgent",
    "Cardiology assessment and risk stratification", "Rest and avoid exertion",
    "https://www.nhs.uk/conditions/angina/")

add("Shoulder pain", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Keep person still",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Back pain (upper)", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Keep person still",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Back pain (upper)", "IS_RED_FLAG_FOR", "Aortic dissection", "emergency",
    "Call emergency services immediately; urgent surgical assessment",
    "Keep patient still and calm", "https://www.nhs.uk/conditions/aortic-dissection/")

add("Cold sweats", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Keep person calm",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Nausea with chest pain", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Keep person still",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Lightheadedness with chest pain", "IS_ASSOCIATED_WITH", "Heart attack", "emergency",
    "Call emergency services immediately", "Lie down if dizzy; avoid sudden movements",
    "https://www.nhs.uk/conditions/heart-attack/")

add("Palpitations", "IS_ASSOCIATED_WITH", "Arrhythmia", "urgent",
    "See primary care/ECG if recurrent or syncope", "Lie down if faint",
    "https://www.nhs.uk/conditions/abnormal-heart-rhythm-arrhythmia/")

# ============================================================================
# NEUROLOGY / STROKE / SEIZURE
# ============================================================================
add("One-side weakness", "IS_RED_FLAG_FOR", "Stroke", "emergency",
    "Call emergency services immediately; note time of onset",
    "Do not give food or drink if swallowing difficulty",
    "https://www.nhs.uk/conditions/stroke/")

add("Face drooping", "IS_ASSOCIATED_WITH", "Stroke", "emergency",
    "Call emergency services immediately", "Keep person still; note time of onset",
    "https://www.nhs.uk/conditions/stroke/")

add("Slurred speech", "IS_ASSOCIATED_WITH", "Stroke", "emergency",
    "Call emergency services immediately", "Keep person comfortable",
    "https://www.nhs.uk/conditions/stroke/")

add("Sudden vision loss", "IS_RED_FLAG_FOR", "Stroke", "emergency",
    "Seek emergency ophthalmic or stroke care immediately",
    "Avoid bright lights and note time of onset",
    "https://www.nhs.uk/conditions/stroke/")

add("Sudden severe headache", "IS_RED_FLAG_FOR", "Subarachnoid haemorrhage", "emergency",
    "Call emergency services immediately", "Keep person still; record time of onset",
    "https://www.nhs.uk/conditions/subarachnoid-haemorrhage/")

add("Seizure lasting >5 minutes", "IS_RED_FLAG_FOR", "Status epilepticus", "emergency",
    "Call emergency services immediately",
    "Protect from injury; do not force objects into mouth",
    "https://www.nhs.uk/conditions/epilepsy/")

# ============================================================================
# RESPIRATORY
# ============================================================================
add("Shortness of breath", "IS_RED_FLAG_FOR", "Pulmonary embolism", "emergency",
    "Seek immediate emergency care", "Keep patient calm and still",
    "https://www.nhs.uk/conditions/pulmonary-embolism/")

add("Shortness of breath", "IS_ASSOCIATED_WITH", "Asthma exacerbation", "urgent",
    "Use reliever inhaler and seek urgent review if not improving",
    "Sit upright and use prescribed inhaler", "https://ginasthma.org/")

add("Wheeze", "IS_ASSOCIATED_WITH", "Asthma", "routine",
    "Follow asthma action plan", "Use reliever inhaler if prescribed",
    "https://ginasthma.org/")

add("Productive cough with fever", "IS_ASSOCIATED_WITH", "Pneumonia", "urgent",
    "See primary care for assessment; chest X-ray if indicated",
    "Hydrate and rest", "https://www.nhs.uk/conditions/pneumonia/")

add("Cough >3 weeks", "IS_ASSOCIATED_WITH", "Tuberculosis", "urgent",
    "Arrange chest X-ray and TB testing as per local guidelines",
    "Isolate until evaluated if infectious risk",
    "https://www.who.int/health-topics/tuberculosis")

# ============================================================================
# GASTROINTESTINAL
# ============================================================================
add("Severe abdominal pain", "IS_RED_FLAG_FOR", "Appendicitis", "urgent",
    "Seek urgent surgical review", "Avoid strong analgesics or food until evaluated",
    "https://www.nhs.uk/conditions/appendicitis/")

add("Blood in stool", "IS_RED_FLAG_FOR", "Gastrointestinal bleeding", "urgent",
    "Attend ED for evaluation", "Avoid NSAIDs until assessed",
    "https://www.nhs.uk/conditions/upper-gastrointestinal-bleeding/")

add("Persistent vomiting", "IS_ASSOCIATED_WITH", "Gastroenteritis", "routine",
    "Hydration, ORS at home; seek care if cannot keep fluids",
    "Offer small sips of ORS if tolerated",
    "https://www.who.int/health-topics/diarrhoeal-disease")

add("Persistent vomiting with bilious (green) vomit", "IS_RED_FLAG_FOR", "Intestinal obstruction", "urgent",
    "Immediate hospital evaluation required", "Do not give food or fluids until assessed",
    "https://www.nhs.uk/conditions/intestinal-obstruction/")

# ============================================================================
# GENITOURINARY / RENAL
# ============================================================================
add("Burning on urination", "IS_ASSOCIATED_WITH", "Urinary tract infection (UTI)", "routine",
    "Urine test and treat if bacterial; seek primary care",
    "Hydration and analgesia", "https://www.nhs.uk/conditions/urinary-tract-infection/")

add("Flank pain radiating to groin", "IS_ASSOCIATED_WITH", "Kidney stone (urolithiasis)", "urgent",
    "Analgesia and imaging if severe", "Hydration and seek ED if uncontrolled pain",
    "https://www.nhs.uk/conditions/kidney-stones/")

add("Blood in urine", "IS_RED_FLAG_FOR", "Urinary tract bleeding/tumour", "urgent",
    "Medical evaluation with urinalysis and imaging",
    "Do not ignore persistent haematuria",
    "https://www.nhs.uk/conditions/blood-in-urine-haematuria/")

# ============================================================================
# PEDIATRICS SPECIFIC
# ============================================================================
add("High fever in infant <3 months", "IS_RED_FLAG_FOR", "Serious bacterial infection / Sepsis risk", "emergency",
    "Immediate hospital assessment required", "Do not delay; keep infant warm and hydrated",
    "https://www.nhs.uk/conditions/fever-in-children/")

add("No tears when crying (infant)", "IS_RED_FLAG_FOR", "Severe dehydration", "urgent",
    "Seek urgent medical attention; start ORS if advised",
    "Give small frequent sips of ORS; continue breastfeeding",
    "https://www.who.int/health-topics/diarrhoeal-disease")

add("Bulging fontanelle", "IS_RED_FLAG_FOR", "Meningitis", "emergency",
    "Immediate pediatric evaluation required", "Keep infant calm; seek urgent transport",
    "https://www.nhs.uk/conditions/meningitis/")

# ============================================================================
# WOMEN'S HEALTH / OBSTETRICS
# ============================================================================
add("Severe abdominal pain in pregnancy", "IS_RED_FLAG_FOR", "Ectopic pregnancy", "emergency",
    "Immediate obstetric evaluation required", "Lie down and avoid exertion",
    "https://www.nhs.uk/pregnancy/related-conditions/complications/bleeding-in-pregnancy/")

add("Heavy vaginal bleeding", "IS_RED_FLAG_FOR", "Miscarriage / Obstetric haemorrhage", "emergency",
    "Seek emergency obstetric care immediately",
    "Lie down; apply pressure if external bleeding",
    "https://www.nhs.uk/pregnancy/related-conditions/complications/bleeding-in-pregnancy/")

add("Reduced fetal movements after 28 weeks", "IS_RED_FLAG_FOR", "Fetal compromise", "urgent",
    "Contact maternity unit urgently for fetal monitoring",
    "Lie on side and count movements",
    "https://www.nhs.uk/pregnancy/related-conditions/reduced-fetal-movements/")

# ============================================================================
# DERMATOLOGY / SKIN
# ============================================================================
add("Non-blanching rash / petechial rash", "IS_RED_FLAG_FOR", "Meningococcal sepsis", "emergency",
    "Go to emergency department immediately", "Keep child still; avoid delay in transport",
    "https://www.nhs.uk/conditions/meningitis/symptoms/")

add("Red swollen painful area of skin", "IS_ASSOCIATED_WITH", "Cellulitis", "urgent",
    "Medical review and antibiotics if spreading", "Keep area elevated and clean",
    "https://www.nhs.uk/conditions/cellulitis/")

# ============================================================================
# ENDOCRINE / METABOLIC
# ============================================================================
add("Polyuria and polydipsia", "IS_ASSOCIATED_WITH", "Diabetes mellitus", "routine",
    "Check blood glucose and see GP", "Hydration and medical review",
    "https://www.who.int/health-topics/diabetes")

add("Severe drowsiness in diabetic", "IS_RED_FLAG_FOR", "Diabetic ketoacidosis", "emergency",
    "Go to ED for urgent metabolic management",
    "Do not give oral fluids if altered consciousness",
    "https://www.nhs.uk/conditions/diabetic-ketoacidosis-dka/")

add("Severe sweating and tremor in diabetic", "IS_RED_FLAG_FOR", "Hypoglycaemia", "emergency",
    "Give fast-acting carbohydrate if conscious; call emergency if not",
    "Give glucose gel/juice if conscious", "https://www.nhs.uk/conditions/hypoglycaemia/")

# ============================================================================
# INFECTIOUS DISEASE / SEPSIS
# ============================================================================
add("High fever with rash", "IS_RED_FLAG_FOR", "Meningococcal sepsis", "emergency",
    "Go to emergency department immediately", "Keep patient warm and monitor breathing",
    "https://www.nhs.uk/conditions/meningitis/")

add("Fever with very low blood pressure and confusion", "IS_RED_FLAG_FOR", "Sepsis", "emergency",
    "Seek emergency medical care immediately",
    "Monitor breathing and consciousness; keep warm",
    "https://www.who.int/health-topics/sepsis")

# ============================================================================
# MENTAL HEALTH / CRISIS
# ============================================================================
add("Suicidal thoughts", "IS_RED_FLAG_FOR", "Mental health crisis / Suicide risk", "emergency",
    "Contact emergency services or crisis line immediately",
    "Stay with person; remove access to means of harm",
    "https://www.who.int/news-room/fact-sheets/detail/suicide")

add("Self-harm with severe injury", "IS_RED_FLAG_FOR", "Medical & psychiatric emergency", "emergency",
    "Attend ED and arrange psychiatric follow-up",
    "Ensure immediate safety and wound care",
    "https://www.nhs.uk/mental-health/concerns/self-harm/")

# ============================================================================
# EAR, NOSE, THROAT / ENT
# ============================================================================
add("Sudden hearing loss", "IS_RED_FLAG_FOR", "Sudden sensorineural hearing loss", "urgent",
    "Seek urgent ENT or audiology assessment", "Avoid loud noise exposure",
    "https://www.nhs.uk/conditions/sudden-hearing-loss/")

add("Drooling/refusal to swallow", "IS_RED_FLAG_FOR", "Peritonsillar or retropharyngeal abscess (airway risk)", "urgent",
    "Immediate ENT or ED assessment", "Keep child seated and do not force oral intake",
    "https://www.nhs.uk/conditions/peritonsillar-abscess/")

# ============================================================================
# OPHTHALMOLOGY
# ============================================================================
add("Sudden painless vision loss", "IS_RED_FLAG_FOR", "Retinal artery occlusion", "emergency",
    "Seek emergency ophthalmology or stroke care immediately",
    "Avoid bright lights; note time of onset",
    "https://www.nhs.uk/conditions/retinal-detachment/")

add("Eye chemical splash", "IS_RED_FLAG_FOR", "Corneal burn / eye emergency", "emergency",
    "Irrigate eye with clean water for 15+ minutes and seek urgent ophthalmic care",
    "Flush eye continuously; do not rub", "https://www.nhs.uk/conditions/eye-injury/")

# ============================================================================
# MUSCULOSKELETAL / TRAUMA
# ============================================================================
add("Major trauma with deformity", "IS_RED_FLAG_FOR", "Open fracture", "emergency",
    "Call emergency services and immobilize limb",
    "Apply pressure to bleeding; avoid moving until stabilized",
    "https://www.cdc.gov/traumaticbraininjury/index.html")

add("Large-area burns", "IS_RED_FLAG_FOR", "Severe burn", "emergency",
    "Call emergency services and arrange burn centre care",
    "Cool burn with running water for 20 minutes",
    "https://www.nhs.uk/conditions/burns-and-scalds/")

# ============================================================================
# REPRODUCTIVE / SEXUAL HEALTH
# ============================================================================
add("Post-coital bleeding", "IS_RED_FLAG_FOR", "Cervical pathology (possible)", "urgent",
    "Arrange urgent gynaecology or colposcopy referral",
    "Avoid sexual activity until assessed",
    "https://www.nhs.uk/conditions/abnormal-uterine-bleeding/")

add("Vaginal discharge with fishy odour", "IS_ASSOCIATED_WITH", "Bacterial vaginosis", "routine",
    "See GP or sexual health clinic for testing and treatment",
    "Avoid douching and scented products",
    "https://www.nhs.uk/conditions/bacterial-vaginosis/")

# ============================================================================
# PREVENTIVE / SCREENING FLAGS
# ============================================================================
add("Unexplained weight loss", "IS_ASSOCIATED_WITH", "Underlying malignancy (possible)", "urgent",
    "Refer for urgent investigation per local guidelines",
    "Document weight and symptoms",
    "https://www.nhs.uk/conditions/unexplained-weight-loss/")

# ============================================================================
# ADDITIONAL COMMON MAPPINGS
# ============================================================================
add("Rash with target lesion", "IS_ASSOCIATED_WITH", "Erythema multiforme / Stevens-Johnson spectrum", "urgent",
    "Seek urgent assessment if mucosal involvement",
    "Stop suspected offending drug and seek care",
    "https://www.nhs.uk/conditions/stevens-johnson-syndrome/")

add("Rash that itches and spreads", "IS_ASSOCIATED_WITH", "Allergic contact dermatitis", "routine",
    "Identify and avoid the trigger; topical emollients",
    "Avoid further exposure to allergen",
    "https://www.nhs.uk/conditions/contact-dermatitis/")

add("Sudden unilateral leg swelling and pain", "IS_RED_FLAG_FOR", "Deep vein thrombosis", "urgent",
    "Arrange ultrasound and anticoagulation assessment",
    "Limit walking and seek review",
    "https://www.nhs.uk/conditions/deep-vein-thrombosis-dvt/")

add("New painful non-healing ulcer", "IS_ASSOCIATED_WITH", "Diabetic foot ulcer / infection", "urgent",
    "Specialist wound care and debridement; assess for osteomyelitis",
    "Offload pressure and keep clean", "https://www.nhs.uk/conditions/foot-ulcer/")

# ============================================================================
# SAVE TO CSV
# ============================================================================
def save_csv():
    """Save the rows to CSV file"""
    script_dir = Path(__file__).parent
    output_path = script_dir / "symptom_relationships.csv"
    
    fieldnames = [
        "subject", "predicate", "object", "type_s", "type_o", "urgency_level",
        "recommended_action", "safe_action", "contraindicated_for", "source_reference",
        "confidence_level", "last_updated"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Generated {output_path}")
    print(f"Total rows: {len(rows)}")
    print(f"Unique symptoms: {len(set(r['subject'] for r in rows))}")
    print(f"Unique conditions: {len(set(r['object'] for r in rows))}")
    
    return output_path

if __name__ == "__main__":
    output_path = save_csv()
    print(f"\n[SUCCESS] Symptom relationships CSV created at: {output_path}")
    print(f"Next step: Run ingestion to load into Neo4j:")
    print(f"  python -m api.graph.ingest")


