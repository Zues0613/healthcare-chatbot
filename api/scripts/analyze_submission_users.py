"""
Analyze user creation times around hackathon submission deadline
Helps identify timezone issues and verify user creation times
Updated for India timezone (IST - UTC+5:30)
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

# India Standard Time (IST) is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))


def convert_to_ist(utc_time: datetime) -> datetime:
    """Convert UTC datetime to IST"""
    if utc_time.tzinfo is None:
        # Assume it's UTC if no timezone info
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    return utc_time.astimezone(IST)


def format_datetime_ist(dt: datetime) -> str:
    """Format datetime in IST with clear timezone indication"""
    if dt.tzinfo is None:
        # If no timezone, assume UTC and convert to IST
        dt = dt.replace(tzinfo=timezone.utc).astimezone(IST)
    else:
        dt = dt.astimezone(IST)
    return dt.strftime('%Y-%m-%d %I:%M:%S %p IST')


async def analyze_submission_users():
    """Analyze all users created around the submission deadline"""
    # Load environment
    api_dir = Path(__file__).parent.parent
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(override=True)
    
    print("=" * 100)
    print("HACKATHON SUBMISSION USER ANALYSIS (INDIA TIMEZONE)")
    print("=" * 100)
    print("\n📅 SUBMISSION DETAILS (IST - Indian Standard Time):")
    print("  Submission Time: November 16, 2025 at 7:30 AM IST")
    print("  Deadline: November 16, 2025 at 12:00 PM IST")
    print("  IST = UTC + 5:30 hours")
    print()
    
    # Connect to database
    if not await db_client.connect():
        print("\n[ERROR] Failed to connect to database")
        return
    
    try:
        # First, check database timezone
        print("[INFO] Checking database timezone...")
        db_timezone = await db_client.fetchval("SHOW timezone")
        current_db_time = await db_client.fetchval("SELECT NOW()")
        print(f"  Database Timezone: {db_timezone}")
        print(f"  Current Database Time: {current_db_time}")
        
        # Convert current DB time to IST for reference
        if isinstance(current_db_time, datetime):
            if current_db_time.tzinfo is None:
                current_db_time_utc = current_db_time.replace(tzinfo=timezone.utc)
            else:
                current_db_time_utc = current_db_time
            current_db_time_ist = current_db_time_utc.astimezone(IST)
            print(f"  Current Database Time (IST): {format_datetime_ist(current_db_time_ist)}")
        print()
        
        # Fetch all users created on Nov 16, 2025
        print("[INFO] Fetching all users created on November 16, 2025...")
        users = await db_client.fetch("""
            SELECT 
                id,
                email,
                created_at,
                updated_at,
                last_login,
                role
            FROM customers
            WHERE DATE(created_at) = '2025-11-16'
            ORDER BY created_at ASC
        """)
        
        users_list = [dict(user) for user in users]
        
        print(f"\n📊 FOUND {len(users_list)} USER(S) CREATED ON NOVEMBER 16, 2025")
        print("=" * 100)
        
        if not users_list:
            print("No users found created on November 16, 2025.")
            return
        
        # Submission time reference (7:30 AM IST on Nov 16)
        # Create in IST timezone
        submission_time_ist = datetime(2025, 11, 16, 7, 30, 0, tzinfo=IST)
        deadline_time_ist = datetime(2025, 11, 16, 12, 0, 0, tzinfo=IST)
        
        # Convert to UTC for comparison (if DB stores in UTC)
        submission_time_utc = submission_time_ist.astimezone(timezone.utc)
        deadline_time_utc = deadline_time_ist.astimezone(timezone.utc)
        
        print("\n⏰ USER CREATION TIMELINE:")
        print("-" * 100)
        print(f"Submission Time: {format_datetime_ist(submission_time_ist)} (UTC: {submission_time_utc.strftime('%Y-%m-%d %I:%M:%S %p UTC')})")
        print(f"Deadline Time: {format_datetime_ist(deadline_time_ist)} (UTC: {deadline_time_utc.strftime('%Y-%m-%d %I:%M:%S %p UTC')})")
        print()
        
        for idx, user in enumerate(users_list, 1):
            created_at = user.get('created_at')
            email = user.get('email', 'N/A')
            user_id = user.get('id', 'N/A')
            
            if created_at:
                if isinstance(created_at, datetime):
                    # Handle timezone conversion
                    if created_at.tzinfo is None:
                        # Assume UTC if no timezone info
                        created_at_utc = created_at.replace(tzinfo=timezone.utc)
                    else:
                        created_at_utc = created_at
                    
                    created_at_ist = created_at_utc.astimezone(IST)
                    
                    # Display in both formats
                    ist_time_str = format_datetime_ist(created_at_ist)
                    utc_time_str = created_at_utc.strftime('%Y-%m-%d %I:%M:%S %p UTC')
                    
                    # Compare with submission time (in IST)
                    time_diff = created_at_ist - submission_time_ist
                    hours_diff = time_diff.total_seconds() / 3600
                    
                    print(f"\n{'='*100}")
                    print(f"User #{idx}: {email}")
                    print(f"  User ID: {user_id[:36]}...")
                    print(f"  Created At (IST): {ist_time_str}")
                    print(f"  Created At (UTC): {utc_time_str}")
                    print(f"  Role: {user.get('role', 'N/A')}")
                    
                    # Determine if before or after submission
                    if created_at_ist < submission_time_ist:
                        print(f"  ⚠️  CREATED {abs(hours_diff):.2f} HOURS BEFORE SUBMISSION (7:30 AM IST)")
                        print(f"     This user was created BEFORE you submitted your project!")
                        if abs(hours_diff) < 2:
                            print(f"  🔍 SUSPICIOUS: Created very close to submission time!")
                    elif created_at_ist >= submission_time_ist and created_at_ist <= deadline_time_ist:
                        print(f"  ✅ CREATED {abs(hours_diff):.2f} HOURS AFTER SUBMISSION")
                        print(f"     This user was created AFTER your submission but BEFORE deadline")
                    else:
                        print(f"  📝 CREATED AFTER DEADLINE (12:00 PM IST)")
                    
                    # Check if this is the suspicious user (5:45 AM)
                    if created_at_ist.hour == 5 and created_at_ist.minute == 45:
                        print(f"  🔍 THIS IS THE SUSPICIOUS USER (5:45 AM timestamp)")
                        print(f"  ⚠️  NEEDS INVESTIGATION - Created 1 hour 45 minutes before submission")
                        print(f"  📊 Time Analysis:")
                        print(f"     - If DB stores UTC: 5:45 AM UTC = 11:15 AM IST (AFTER submission)")
                        print(f"     - If DB stores IST: 5:45 AM IST = 5:45 AM IST (BEFORE submission)")
                        print(f"     - Actual IST time shown above: {ist_time_str}")
                else:
                    print(f"\nUser #{idx}: {email}")
                    print(f"  Created At: {created_at}")
        
        print("\n" + "=" * 100)
        print("\n💡 TIMEZONE ANALYSIS:")
        print("-" * 100)
        print("India Standard Time (IST) = UTC + 5:30 hours")
        print("\nKey Conversions:")
        print("  - 5:45 AM UTC = 11:15 AM IST (AFTER your 7:30 AM submission)")
        print("  - 5:45 AM IST = 12:15 AM UTC (same day, but earlier)")
        print("  - 7:30 AM IST = 2:00 AM UTC (your submission time)")
        print("\n⚠️  IMPORTANT:")
        print("  1. Check if Neon DB stores timestamps in UTC or IST")
        print("  2. The actual IST time is shown above for each user")
        print("  3. If the user shows 5:45 AM IST, they were created BEFORE your submission")
        print("  4. If the user shows 11:15 AM IST (5:45 AM UTC), they were created AFTER your submission")
        
        # Summary
        print("\n📋 SUMMARY:")
        print("-" * 100)
        before_submission = []
        after_submission = []
        for user in users_list:
            created_at = user.get('created_at')
            if isinstance(created_at, datetime):
                if created_at.tzinfo is None:
                    created_at_utc = created_at.replace(tzinfo=timezone.utc)
                else:
                    created_at_utc = created_at
                created_at_ist = created_at_utc.astimezone(IST)
                
                if created_at_ist < submission_time_ist:
                    before_submission.append((user.get('email'), format_datetime_ist(created_at_ist)))
                else:
                    after_submission.append((user.get('email'), format_datetime_ist(created_at_ist)))
        
        print(f"Users created BEFORE submission (7:30 AM IST): {len(before_submission)}")
        for email, time_str in before_submission:
            print(f"  - {email} at {time_str}")
        
        print(f"\nUsers created AFTER submission (7:30 AM IST): {len(after_submission)}")
        for email, time_str in after_submission:
            print(f"  - {email} at {time_str}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to analyze users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_client.disconnect()
        print("\n[INFO] Database connection closed.")


if __name__ == "__main__":
    asyncio.run(analyze_submission_users())

