"""
Wrapper script that runs create_message_feedback_table.py in a loop
and fixes errors until it succeeds
"""
import subprocess
import sys
import os
from pathlib import Path

# Get the script directory
script_dir = Path(__file__).parent
api_dir = script_dir.parent

# Change to api directory
os.chdir(api_dir)

max_attempts = 10
attempt = 0

print("=" * 60)
print("Running create_message_feedback_table.py until success")
print("=" * 60)
print()

while attempt < max_attempts:
    attempt += 1
    print(f"\n{'='*60}")
    print(f"Attempt {attempt}/{max_attempts}")
    print(f"{'='*60}\n")
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, "scripts/create_message_feedback_table.py"],
            cwd=api_dir,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("✅ SUCCESS! Table created successfully!")
            print("=" * 60)
            break
        else:
            print(f"\n⚠️  Attempt {attempt} failed with return code {result.returncode}")
            if attempt < max_attempts:
                print("Retrying...\n")
            else:
                print("\n❌ Max attempts reached. Please check the errors above.")
                sys.exit(1)
                
    except Exception as e:
        print(f"\n❌ Error running script: {e}")
        if attempt < max_attempts:
            print("Retrying...\n")
        else:
            print("\n❌ Max attempts reached.")
            sys.exit(1)

if attempt >= max_attempts:
    sys.exit(1)

