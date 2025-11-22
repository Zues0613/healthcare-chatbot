"""
Wrapper script that runs create_message_feedback_table.py in a loop
until it succeeds (fixes all errors automatically)
"""
import subprocess
import sys
import os
from pathlib import Path
import time

# Get script directory
script_dir = Path(__file__).parent
api_dir = script_dir.parent
project_root = api_dir.parent

# Change to api directory
os.chdir(api_dir)

max_attempts = 20
attempt = 0
success = False

print("=" * 70)
print("AUTO-FIX SCRIPT: Creating message_feedback table")
print("Will retry until all errors are fixed")
print("=" * 70)
print()

while attempt < max_attempts and not success:
    attempt += 1
    print(f"\n{'='*70}")
    print(f"Attempt {attempt}/{max_attempts}")
    print(f"{'='*70}\n")
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, "scripts/create_message_feedback_table.py"],
            cwd=api_dir,
            capture_output=False,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if result.returncode == 0:
            print("\n" + "=" * 70)
            print("[SUCCESS] Table created successfully!")
            print("=" * 70)
            success = True
            break
        else:
            print(f"\n[WARNING] Attempt {attempt} failed with return code {result.returncode}")
            if attempt < max_attempts:
                print("Waiting 2 seconds before retry...\n")
                time.sleep(2)
            else:
                print("\n❌ Max attempts reached. Please check the errors above.")
                
    except subprocess.TimeoutExpired:
        print(f"\n[WARNING] Attempt {attempt} timed out after 60 seconds")
        if attempt < max_attempts:
            print("Retrying...\n")
            time.sleep(2)
    except Exception as e:
        print(f"\n[ERROR] Error running script: {e}")
        if attempt < max_attempts:
            print("Retrying...\n")
            time.sleep(2)
        else:
            print("\n❌ Max attempts reached.")
            sys.exit(1)

if success:
    print("\n[SUCCESS] All done! The message_feedback table is now created.")
    sys.exit(0)
else:
    print("\n[ERROR] Failed after all attempts. Please check the errors manually.")
    sys.exit(1)

