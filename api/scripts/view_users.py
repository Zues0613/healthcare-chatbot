"""
View all users from the Neon database in a tabular format
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from database.db_client import db_client


def format_table(users: List[Dict[str, Any]]) -> None:
    """Format and display users in a table"""
    if not users:
        print("\n[INFO] No users found in the database.")
        return
    
    # Get all column names from the first user
    if users:
        all_columns = set()
        for user in users:
            all_columns.update(user.keys())
        columns = sorted(all_columns)
    else:
        columns = []
    
    # Define column widths (adjust as needed)
    col_widths = {}
    for col in columns:
        # Set default width based on column name
        if col == 'id':
            col_widths[col] = 38
        elif col in ['email', 'password_hash']:
            col_widths[col] = 30
        elif col in ['role', 'sex']:
            col_widths[col] = 10
        elif col in ['age', 'diabetes', 'hypertension', 'pregnancy', 'is_active']:
            col_widths[col] = 12
        elif col in ['city']:
            col_widths[col] = 20
        elif 'created_at' in col or 'updated_at' in col or 'last_login' in col:
            col_widths[col] = 20
        else:
            col_widths[col] = 15
    
    # Calculate actual widths based on data
    for col in columns:
        max_len = len(col)  # Header length
        for user in users:
            value = user.get(col)
            if value is None:
                value_str = 'N/A'
            elif isinstance(value, datetime):
                value_str = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, bool):
                value_str = 'Yes' if value else 'No'
            elif isinstance(value, (dict, list)):
                value_str = str(value)[:30] + '...' if len(str(value)) > 30 else str(value)
            else:
                value_str = str(value)
            max_len = max(max_len, len(value_str))
        col_widths[col] = min(max_len + 2, 50)  # Add padding, cap at 50
    
    # Print header
    header_parts = []
    for col in columns:
        header_parts.append(f"{col.replace('_', ' ').title():<{col_widths[col]}}")
    header = " ".join(header_parts)
    
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))
    
    # Print rows
    for user in users:
        row_parts = []
        for col in columns:
            value = user.get(col)
            if value is None:
                value_str = 'N/A'
            elif isinstance(value, datetime):
                value_str = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, bool):
                value_str = 'Yes' if value else 'No'
            elif isinstance(value, (dict, list)):
                value_str = str(value)[:col_widths[col]-3] + '...' if len(str(value)) > col_widths[col]-3 else str(value)
            else:
                value_str = str(value)
                # Truncate if too long
                if len(value_str) > col_widths[col] - 2:
                    value_str = value_str[:col_widths[col]-5] + '...'
            
            row_parts.append(f"{value_str:<{col_widths[col]}}")
        
        print(" ".join(row_parts))
    
    print("=" * len(header))
    print(f"\nTotal users: {len(users)}")


async def view_users():
    """View all users from the database"""
    # Load environment
    api_dir = Path(__file__).parent.parent
    env_file = api_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Try loading from current directory
        load_dotenv(override=True)
    
    print("=" * 100)
    print("Users (Customers Table) - Neon Database")
    print("=" * 100)
    
    # Connect to database
    if not await db_client.connect():
        print("\n[ERROR] Failed to connect to database")
        print("Please check your NEON_DB_URL in .env file")
        return
    
    try:
        # Query all users from customers table (which stores user data)
        print("\n[INFO] Fetching all users from 'customers' table...")
        users = await db_client.fetch("SELECT * FROM customers ORDER BY created_at DESC")
        
        # Convert to list of dicts
        users_list = [dict(user) for user in users]
        
        # Display in table format
        format_table(users_list)
        
    except Exception as e:
        print(f"\n[ERROR] Failed to fetch users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_client.disconnect()
        print("\n[INFO] Database connection closed.")


if __name__ == "__main__":
    asyncio.run(view_users())

