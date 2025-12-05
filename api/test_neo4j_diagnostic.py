"""
Neo4j Connection Diagnostic Tool

Helps diagnose Neo4j connection issues
"""
import os
import sys
import socket
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file, override=True)
else:
    load_dotenv(override=True)

def test_dns_resolution(hostname: str, port: int = 7687):
    """Test DNS resolution for Neo4j hostname"""
    print(f"\n{'='*60}")
    print("DNS Resolution Test")
    print(f"{'='*60}\n")
    
    try:
        print(f"Attempting to resolve: {hostname}")
        ip_addresses = socket.gethostbyname_ex(hostname)
        print(f"✓ DNS Resolution Successful!")
        print(f"  Hostname: {ip_addresses[0]}")
        print(f"  Aliases: {ip_addresses[1]}")
        print(f"  IP Addresses: {ip_addresses[2]}")
        return True
    except socket.gaierror as e:
        print(f"✗ DNS Resolution Failed: {e}")
        print(f"\nPossible causes:")
        print(f"  1. Hostname is incorrect")
        print(f"  2. Database instance was deleted or paused")
        print(f"  3. Network connectivity issues")
        print(f"  4. DNS server problems")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_port_connectivity(hostname: str, port: int = 7687):
    """Test if port is reachable"""
    print(f"\n{'='*60}")
    print("Port Connectivity Test")
    print(f"{'='*60}\n")
    
    try:
        print(f"Attempting to connect to {hostname}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result == 0:
            print(f"✓ Port {port} is reachable!")
            return True
        else:
            print(f"✗ Port {port} is not reachable (error code: {result})")
            print(f"\nPossible causes:")
            print(f"  1. Firewall blocking the connection")
            print(f"  2. Database instance is paused")
            print(f"  3. Wrong port number")
            return False
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False

def check_neo4j_config():
    """Check Neo4j configuration"""
    print(f"\n{'='*60}")
    print("Neo4j Configuration Check")
    print(f"{'='*60}\n")
    
    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USER", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "")
    trust_all = os.getenv("NEO4J_TRUST_ALL_CERTS", "false")
    
    print(f"URI: {uri[:60]}..." if len(uri) > 60 else f"URI: {uri}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
    print(f"Database: {database or 'default'}")
    print(f"Trust All Certs: {trust_all}")
    
    if not uri:
        print("\n✗ NEO4J_URI is not set!")
        return None
    
    # Parse URI
    try:
        parsed = urlparse(uri)
        hostname = parsed.hostname
        port = parsed.port or 7687
        scheme = parsed.scheme
        
        print(f"\nParsed URI:")
        print(f"  Scheme: {scheme}")
        print(f"  Hostname: {hostname}")
        print(f"  Port: {port}")
        
        # Validate scheme
        valid_schemes = ["neo4j", "neo4j+s", "neo4j+ssc", "bolt", "bolt+s", "bolt+ssc"]
        if scheme not in valid_schemes:
            print(f"\n⚠ Warning: Scheme '{scheme}' might not be valid")
            print(f"  Valid schemes: {', '.join(valid_schemes)}")
        
        return {
            "hostname": hostname,
            "port": port,
            "scheme": scheme,
            "uri": uri
        }
    except Exception as e:
        print(f"\n✗ Failed to parse URI: {e}")
        return None

def main():
    """Run diagnostic tests"""
    print(f"\n{'='*60}")
    print("Neo4j Connection Diagnostic Tool")
    print(f"{'='*60}\n")
    
    config = check_neo4j_config()
    
    if not config:
        print("\n✗ Cannot proceed without valid configuration")
        return
    
    hostname = config["hostname"]
    port = config["port"]
    
    # Test DNS
    dns_ok = test_dns_resolution(hostname, port)
    
    # Test port connectivity (only if DNS works)
    if dns_ok:
        port_ok = test_port_connectivity(hostname, port)
    else:
        print("\n⚠ Skipping port connectivity test (DNS resolution failed)")
        port_ok = False
    
    # Summary
    print(f"\n{'='*60}")
    print("Diagnostic Summary")
    print(f"{'='*60}\n")
    
    if dns_ok and port_ok:
        print("✓ DNS and Port connectivity tests passed")
        print("  → The issue might be with SSL/TLS or authentication")
        print("  → Try setting NEO4J_TRUST_ALL_CERTS=true")
    elif dns_ok and not port_ok:
        print("✓ DNS resolution works, but port is not reachable")
        print("  → Check firewall settings")
        print("  → Verify database instance is active in Neo4j Aura dashboard")
    elif not dns_ok:
        print("✗ DNS resolution failed")
        print("  → Verify the hostname is correct")
        print("  → Check if database instance exists in Neo4j Aura")
        print("  → Try accessing Neo4j Aura dashboard to verify instance status")
    
    print(f"\nNext steps:")
    print(f"1. Check Neo4j Aura dashboard: https://console.neo4j.io/")
    print(f"2. Verify instance is active (not paused)")
    print(f"3. Check if instance ID matches: {hostname}")
    print(f"4. Verify credentials are correct")
    print(f"5. If instance was recreated, update NEO4J_URI with new instance ID")

if __name__ == "__main__":
    main()


