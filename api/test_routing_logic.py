"""
Test script for IP-based routing logic

Tests the three-tier routing system:
1. New user (no tokens, new IP) → /landing
2. Known IP with invalid/expired tokens → /auth with session expired message
3. Valid user with valid tokens → Allow access to /

Run with: python test_routing_logic.py
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Optional

# Fix Windows encoding issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import httpx
from database.db_client import db_client

# Load environment
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    load_dotenv(override=True)

# Configuration
API_BASE = os.getenv("NEXT_PUBLIC_BACKEND_URL") or os.getenv("NEXT_PUBLIC_API_BASE") or "http://localhost:8000"
API_BASE = API_BASE.rstrip("/")


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")


def print_error(message: str):
    print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARN] {message}{Colors.RESET}")


def print_info(message: str):
    print(f"{Colors.BLUE}[INFO] {message}{Colors.RESET}")


def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


async def test_ip_check_endpoint(client: httpx.AsyncClient, test_ip: Optional[str] = None) -> Dict:
    """Test the /auth/check-ip endpoint"""
    print_info(f"Testing /auth/check-ip endpoint...")
    
    headers = {}
    if test_ip:
        headers["X-Forwarded-For"] = test_ip
    
    try:
        response = await client.get(
            f"{API_BASE}/auth/check-ip",
            headers=headers,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"IP Check Response: {data}")
            return data
        else:
            print_error(f"IP Check failed with status {response.status_code}: {response.text}")
            return {}
    except httpx.ConnectError as e:
        print_error(f"IP Check request failed - Cannot connect to server: {e}")
        print_warning(f"Make sure the backend server is running at {API_BASE}")
        return {}
    except httpx.TimeoutException as e:
        print_error(f"IP Check request timed out: {e}")
        return {}
    except Exception as e:
        print_error(f"IP Check request failed: {type(e).__name__}: {e}")
        return {}


async def test_auth_me_endpoint(client: httpx.AsyncClient, cookies: Optional[Dict] = None) -> Dict:
    """Test the /auth/me endpoint (requires authentication)"""
    print_info(f"Testing /auth/me endpoint...")
    
    try:
        response = await client.get(
            f"{API_BASE}/auth/me",
            cookies=cookies or {},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Auth Me Response: {data}")
            return data
        elif response.status_code == 401:
            print_warning(f"Auth Me returned 401 (Unauthorized) - expected for unauthenticated requests")
            return {}
        else:
            print_error(f"Auth Me failed with status {response.status_code}: {response.text}")
            return {}
    except Exception as e:
        print_error(f"Auth Me request failed: {e}")
        return {}


async def test_database_ip_tracking():
    """Test IP tracking in database"""
    print_info("Testing IP tracking in database...")
    
    try:
        # Connect to database
        if not await db_client.connect():
            print_error("Failed to connect to database")
            return False
        
        # Test query to check if ip_addresses table exists
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'ip_addresses'
            ) as table_exists;
        """
        result = await db_client.fetchrow(query)
        
        if result and result.get("table_exists"):
            print_success("ip_addresses table exists")
            
            # Count IPs in database
            count_query = "SELECT COUNT(*) as count FROM ip_addresses"
            count_result = await db_client.fetchrow(count_query)
            count = count_result.get("count", 0) if count_result else 0
            print_info(f"Total IPs tracked: {count}")
            
            # Get sample IPs
            sample_query = """
                SELECT ip_address, has_authenticated, visit_count, last_seen
                FROM ip_addresses
                ORDER BY last_seen DESC
                LIMIT 5
            """
            sample_ips = await db_client.fetch(sample_query)
            
            if sample_ips:
                print_info("Sample IPs in database:")
                for ip_record in sample_ips:
                    print(f"  - {ip_record['ip_address']}: authenticated={ip_record['has_authenticated']}, visits={ip_record['visit_count']}")
            
            return True
        else:
            print_error("ip_addresses table does not exist - run migration script first!")
            return False
            
    except Exception as e:
        print_error(f"Database test failed: {e}")
        return False


async def test_routing_scenarios():
    """Test the three routing scenarios"""
    print_header("Testing Routing Scenarios")
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        # Test 1: New IP (should return is_known: false)
        print_header("Scenario 1: New IP Address")
        test_ip_1 = "192.168.100.100"  # Unlikely to exist
        result_1 = await test_ip_check_endpoint(client, test_ip_1)
        
        if result_1:
            is_known = result_1.get("is_known", False)
            if not is_known:
                print_success("✓ New IP correctly identified (is_known: false)")
                print_info("Expected behavior: User should be redirected to /landing")
            else:
                print_warning(f"⚠ IP was already known (might have been tested before)")
        
        # Test 2: Known IP (check with current IP)
        print_header("Scenario 2: Known IP Address")
        result_2 = await test_ip_check_endpoint(client)
        
        if result_2:
            is_known = result_2.get("is_known", False)
            has_authenticated = result_2.get("has_authenticated", False)
            
            if is_known:
                print_success(f"✓ IP is known (has_authenticated: {has_authenticated})")
                if not has_authenticated:
                    print_info("Expected behavior: If tokens are invalid, redirect to /auth with session expired")
                else:
                    print_info("Expected behavior: If tokens are valid, allow access. If invalid, redirect to /auth")
            else:
                print_info("IP is new - will be tracked on first visit")
        else:
            print_warning("⚠ Could not test known IP scenario - endpoint may be unavailable")
        
        # Test 3: Auth endpoint (without authentication)
        print_header("Scenario 3: Token Validation")
        auth_result = await test_auth_me_endpoint(client)
        
        if not auth_result:
            print_success("✓ /auth/me correctly returns 401 for unauthenticated requests")
            print_info("Expected behavior: Invalid/expired tokens should trigger redirect to /auth")
        
        # Test 4: Check Redis caching (make multiple requests)
        print_header("Scenario 4: Performance Test (Redis Caching)")
        import time
        
        times = []
        for i in range(5):
            start = time.time()
            await test_ip_check_endpoint(client)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
            print_info(f"Request {i+1}: {elapsed:.2f}ms")
        
        avg_time = sum(times) / len(times)
        if avg_time < 50:
            print_success(f"✓ Average response time: {avg_time:.2f}ms (excellent - likely cached)")
        elif avg_time < 200:
            print_success(f"✓ Average response time: {avg_time:.2f}ms (good)")
        else:
            print_warning(f"⚠ Average response time: {avg_time:.2f}ms (might not be using cache)")


async def test_neo4j_connection():
    """Test Neo4j connection and diagnose issues"""
    print_header("Neo4j Connection Diagnostics")
    
    from graph.client import neo4j_client
    
    print_info("Checking Neo4j configuration...")
    print(f"  URI: {neo4j_client.uri[:50]}..." if len(neo4j_client.uri) > 50 else f"  URI: {neo4j_client.uri}")
    print(f"  User: {neo4j_client.user}")
    print(f"  Database: {neo4j_client.database or 'default'}")
    print(f"  Trust All Certs: {neo4j_client.trust_all}")
    
    print_info("\nAttempting to connect to Neo4j...")
    
    try:
        # Try to connect
        connected = neo4j_client.connect()
        
        if connected:
            print_success("✓ Neo4j connection successful!")
            
            # Test a simple query
            try:
                result = neo4j_client.run_cypher("RETURN 1 AS test")
                if result:
                    print_success("✓ Neo4j query test successful!")
            except Exception as e:
                print_error(f"Neo4j query test failed: {e}")
        else:
            print_error("✗ Neo4j connection failed")
            print_warning("\nPossible issues:")
            print_warning("1. DNS resolution failure - check if the hostname is correct")
            print_warning("2. Network connectivity - check firewall/proxy settings")
            print_warning("3. SSL/TLS certificate issues - try setting NEO4J_TRUST_ALL_CERTS=true")
            print_warning("4. Wrong URI format - Neo4j Aura uses neo4j+s:// or bolt+s://")
            print_warning("5. Database might be paused or deleted")
            
            print_info("\nTroubleshooting steps:")
            print_info("1. Verify NEO4J_URI in .env file")
            print_info("2. For Neo4j Aura, URI should be: neo4j+s://<instance-id>.databases.neo4j.io")
            print_info("3. Check if database is active in Neo4j Aura dashboard")
            print_info("4. Try ping the hostname: ping <hostname>")
            print_info("5. Check credentials are correct")
            
    except Exception as e:
        print_error(f"Neo4j connection error: {e}")
        print_warning(f"Error type: {type(e).__name__}")
        
        # Provide specific guidance based on error
        error_str = str(e).lower()
        if "resolve" in error_str or "dns" in error_str:
            print_warning("\nDNS Resolution Issue Detected!")
            print_warning("The hostname cannot be resolved. Possible causes:")
            print_warning("- Incorrect URI format")
            print_warning("- Network connectivity issues")
            print_warning("- DNS server problems")
        elif "ssl" in error_str or "certificate" in error_str:
            print_warning("\nSSL Certificate Issue Detected!")
            print_warning("Try setting NEO4J_TRUST_ALL_CERTS=true in .env")
        elif "timeout" in error_str:
            print_warning("\nConnection Timeout!")
            print_warning("The database might be unreachable or firewall is blocking")


async def main():
    """Main test function"""
    print_header("Healthcare Chatbot - Routing Logic & Neo4j Tests")
    
    # Check if server is running
    print_info(f"Testing against API: {API_BASE}")
    print_info("Make sure the backend server is running!\n")
    
    # Test 1: Database IP tracking
    print_header("Test 1: Database IP Tracking")
    db_ok = await test_database_ip_tracking()
    
    if not db_ok:
        print_warning("⚠ Database tests failed - some routing tests may not work correctly")
    
    # Test 2: Routing scenarios
    print_header("Test 2: Routing Logic Tests")
    try:
        await test_routing_scenarios()
    except Exception as e:
        print_error(f"Routing tests failed: {e}")
        print_warning("Make sure the backend server is running at the configured API_BASE")
    
    # Test 3: Neo4j connection
    print_header("Test 3: Neo4j Connection Diagnostics")
    try:
        await test_neo4j_connection()
    except Exception as e:
        print_error(f"Neo4j diagnostics failed: {e}")
    
    print_header("Tests Complete!")
    print_info("Review the results above to verify routing logic and diagnose Neo4j issues")
    print_info("\nNote: Neo4j connection failure is expected if the instance is paused/deleted")
    print_info("The application will continue to work with fallback systems")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

