"""
View detailed information about a specific user from the Neon database
Updated with IST (India Standard Time) timezone support
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client

# India Standard Time (IST) is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))


def format_datetime_ist(dt: datetime) -> str:
    """Format datetime in IST with clear timezone indication"""
    if dt is None:
        return "Not available"
    
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = dt.replace(tzinfo=timezone.utc).astimezone(IST)
        else:
            dt = dt.astimezone(IST)
        return dt.strftime('%Y-%m-%d %I:%M:%S %p IST')
    else:
        return str(dt)


def format_user_details(user: Dict[str, Any]) -> None:
    """Format and display user details in a readable, non-tabular format"""
    if not user:
        print("\n[INFO] User not found.")
        return
    
    print("\n" + "=" * 80)
    print("USER DETAILS")
    print("=" * 80)
    
    # Basic Information
    print("\n📋 BASIC INFORMATION")
    print("-" * 80)
    
    # Check for name fields (might be in different places)
    name = user.get('name') or user.get('full_name') or user.get('first_name')
    last_name = user.get('last_name')
    
    # Also check metadata for name
    metadata = user.get('metadata')
    if metadata and isinstance(metadata, dict):
        if not name:
            name = metadata.get('name') or metadata.get('full_name') or metadata.get('first_name')
        if not last_name:
            last_name = metadata.get('last_name')
    
    if name:
        if last_name:
            print(f"Full Name: {name} {last_name}")
        else:
            print(f"Name: {name}")
    else:
        print("Name: Not provided")
    
    print(f"ID: {user.get('id', 'N/A')}")
    print(f"Email: {user.get('email', 'N/A')}")
    print(f"Role: {user.get('role', 'N/A')}")
    print(f"Active Status: {'Yes' if user.get('is_active', False) else 'No'}")
    
    # Profile Information
    print("\n👤 PROFILE INFORMATION")
    print("-" * 80)
    age = user.get('age')
    print(f"Age: {age if age is not None else 'Not specified'}")
    
    sex = user.get('sex')
    print(f"Sex: {sex if sex else 'Not specified'}")
    
    city = user.get('city')
    print(f"City: {city if city else 'Not specified'}")
    
    # Medical Conditions
    print("\n🏥 MEDICAL CONDITIONS")
    print("-" * 80)
    print(f"Diabetes: {'Yes' if user.get('diabetes', False) else 'No'}")
    print(f"Hypertension: {'Yes' if user.get('hypertension', False) else 'No'}")
    print(f"Pregnancy: {'Yes' if user.get('pregnancy', False) else 'No'}")
    
    # Medical Conditions (JSON field)
    medical_conditions = user.get('medical_conditions')
    if medical_conditions:
        if isinstance(medical_conditions, str):
            try:
                medical_conditions = json.loads(medical_conditions)
            except:
                pass
        if isinstance(medical_conditions, list) and medical_conditions:
            print(f"Other Medical Conditions: {', '.join(str(c) for c in medical_conditions)}")
        elif isinstance(medical_conditions, dict) and medical_conditions:
            print("Other Medical Conditions:")
            for key, value in medical_conditions.items():
                print(f"  - {key}: {value}")
    
    # Timestamps
    print("\n📅 TIMESTAMPS (IST - Indian Standard Time)")
    print("-" * 80)
    created_at = user.get('created_at')
    print(f"Account Created: {format_datetime_ist(created_at)}")
    
    updated_at = user.get('updated_at')
    print(f"Last Updated: {format_datetime_ist(updated_at)}")
    
    last_login = user.get('last_login')
    if last_login:
        print(f"Last Login: {format_datetime_ist(last_login)}")
    else:
        print("Last Login: Never logged in")
    
    # Metadata (skip name fields already shown)
    metadata = user.get('metadata')
    if metadata:
        print("\n📝 ADDITIONAL METADATA")
        print("-" * 80)
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                pass
        if isinstance(metadata, dict) and metadata:
            # Filter out name fields that were already displayed
            skip_keys = {'name', 'full_name', 'first_name', 'last_name'}
            filtered_metadata = {k: v for k, v in metadata.items() if k not in skip_keys}
            if filtered_metadata:
                for key, value in filtered_metadata.items():
                    print(f"{key}: {value}")
            else:
                print("No additional metadata (excluding name fields)")
        else:
            print(f"{metadata}")
    
    # Password Hash (truncated for security)
    password_hash = user.get('password_hash')
    if password_hash:
        print("\n🔐 AUTHENTICATION")
        print("-" * 80)
        print(f"Password Hash: {password_hash[:30]}... (truncated for security)")
    
    print("\n" + "=" * 80)


def format_messages(messages: List[Dict[str, Any]]) -> None:
    """Format and display messages in a chat session"""
    if not messages:
        print("    No messages in this session.")
        return
    
    for msg in messages:
        role = msg.get('role', 'unknown')
        message_text = msg.get('message_text', '')
        created_at = msg.get('created_at')
        
        # Format timestamp in IST
        timestamp = format_datetime_ist(created_at)
        
        # Display based on role
        if role == 'user':
            print(f"    👤 User ({timestamp}):")
            print(f"       {message_text}")
        elif role == 'assistant':
            answer = msg.get('answer', '')
            print(f"    🤖 Assistant ({timestamp}):")
            if answer:
                print(f"       {answer}")
            else:
                print(f"       {message_text}")
        else:
            print(f"    {role.title()} ({timestamp}):")
            print(f"       {message_text}")
        
        print()


def format_chat_sessions(sessions: List[Dict[str, Any]], messages_by_session: Dict[str, List[Dict[str, Any]]]) -> None:
    """Format and display chat sessions information"""
    if not sessions:
        print("\n💬 CHAT SESSIONS")
        print("-" * 80)
        print("No chat sessions found for this user.")
        return
    
    print("\n💬 CHAT SESSIONS")
    print("-" * 80)
    print(f"Total Chat Sessions: {len(sessions)}")
    print()
    
    for idx, session in enumerate(sessions, 1):
        session_id = session.get('id', 'N/A')
        print(f"Session #{idx}")
        print(f"  Session ID: {session_id}")
        
        language = session.get('language')
        if language:
            print(f"  Language: {language}")
        else:
            print(f"  Language: Not specified")
        
        created_at = session.get('created_at')
        print(f"  Created: {format_datetime_ist(created_at)}")
        
        updated_at = session.get('updated_at')
        print(f"  Last Updated: {format_datetime_ist(updated_at)}")
        
        # Get message count for this session
        message_count = session.get('message_count', 0)
        print(f"  Messages: {message_count}")
        
        session_metadata = session.get('session_metadata')
        if session_metadata:
            if isinstance(session_metadata, str):
                try:
                    session_metadata = json.loads(session_metadata)
                except:
                    pass
            if isinstance(session_metadata, dict) and session_metadata:
                print(f"  Metadata: {json.dumps(session_metadata, indent=2)}")
        
        # Display messages for this session
        print("  Messages:")
        if session_id in messages_by_session:
            format_messages(messages_by_session[session_id])
        else:
            print("    No messages found.")
        
        if idx < len(sessions):
            print()
            print("-" * 80)
            print()


async def view_user_details(email: Optional[str] = None, user_id: Optional[str] = None):
    """View detailed information about a specific user"""
    # Load environment
    api_dir = Path(__file__).parent.parent
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Try loading from current directory
        load_dotenv(override=True)
    
    print("=" * 80)
    print("User Details - Neon Database")
    print("=" * 80)
    
    # Validate input
    if not email and not user_id:
        print("\n[ERROR] Please provide either an email or user ID")
        print("\nUsage:")
        print("  python scripts/view_user_details.py --email user@example.com")
        print("  python scripts/view_user_details.py --id user-id-here")
        return
    
    # Connect to database
    if not await db_client.connect():
        print("\n[ERROR] Failed to connect to database")
        print("Please check your NEON_DB_URL in .env file")
        return
    
    try:
        # Query user by email or ID
        if email:
            print(f"\n[INFO] Fetching user with email: {email}...")
            user = await db_client.fetchrow(
                "SELECT * FROM customers WHERE email = $1",
                email
            )
            user_id_for_sessions = user.get('id') if user else None
        else:
            print(f"\n[INFO] Fetching user with ID: {user_id}...")
            user = await db_client.fetchrow(
                "SELECT * FROM customers WHERE id = $1",
                user_id
            )
            user_id_for_sessions = user_id
        
        if user:
            # Convert to dict
            user_dict = dict(user)
            
            # Show all available fields for debugging
            print(f"\n[DEBUG] All available fields in database: {list(user_dict.keys())}")
            
            # Display details
            format_user_details(user_dict)
            
            # Fetch chat sessions for this user
            print("\n[INFO] Fetching chat sessions for this user...")
            sessions = await db_client.fetch("""
                SELECT 
                    cs.*,
                    COUNT(cm.id) as message_count
                FROM chat_sessions cs
                LEFT JOIN chat_messages cm ON cs.id = cm.session_id
                WHERE cs.customer_id = $1
                GROUP BY cs.id
                ORDER BY cs.created_at DESC
            """, user_id_for_sessions)
            
            # Convert to list of dicts
            sessions_list = [dict(session) for session in sessions]
            
            # Fetch messages for all sessions
            messages_by_session = {}
            if sessions_list:
                session_ids = [session['id'] for session in sessions_list]
                print("[INFO] Fetching messages for all chat sessions...")
                
                for session_id in session_ids:
                    messages = await db_client.fetch("""
                        SELECT 
                            id,
                            role,
                            message_text,
                            answer,
                            language,
                            created_at
                        FROM chat_messages
                        WHERE session_id = $1
                        ORDER BY created_at ASC
                    """, session_id)
                    
                    messages_by_session[session_id] = [dict(msg) for msg in messages]
            
            # Display chat sessions with messages
            format_chat_sessions(sessions_list, messages_by_session)
            
        else:
            print(f"\n[INFO] User not found.")
            if email:
                print(f"  No user found with email: {email}")
            else:
                print(f"  No user found with ID: {user_id}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to fetch user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_client.disconnect()
        print("\n[INFO] Database connection closed.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View detailed information about a specific user")
    parser.add_argument("--email", type=str, help="User email address")
    parser.add_argument("--id", type=str, help="User ID")
    
    args = parser.parse_args()
    
    asyncio.run(view_user_details(email=args.email, user_id=args.id))

