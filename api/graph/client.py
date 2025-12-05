from neo4j import GraphDatabase
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("health_assistant")

class Neo4jClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "testpass")
        self.database = os.getenv("NEO4J_DATABASE")
        self.trust_all = os.getenv("NEO4J_TRUST_ALL_CERTS", "false").lower() in {"1", "true", "yes"}
        self.driver = None
        self._is_connected = False
    
    def connect(self):
        """
        Connect to Neo4j database (persistent connection)
        Creates a connection pool that's reused across requests
        """
        # If already connected and driver is valid, return True
        if self.driver and self._is_connected:
            try:
                # Quick health check
                session_args = {}
                if self.database:
                    session_args["database"] = self.database
                with self.driver.session(**session_args) as session:
                    session.run("RETURN 1 AS test").single()
                return True
            except Exception:
                # Connection lost, need to reconnect
                logger.warning("Neo4j connection lost, reconnecting...")
                self._is_connected = False
                if self.driver:
                    try:
                        self.driver.close()
                    except:
                        pass
                    self.driver = None
        
        # Connect if not already connected
        if not self.driver:
            try:
                logger.info(f"Attempting to connect to Neo4j at {self.uri[:50]}..." if len(self.uri) > 50 else f"Attempting to connect to Neo4j at {self.uri}")
                logger.debug(f"Neo4j connection settings: user={self.user}, database={self.database or 'default'}, trust_all={self.trust_all}")
                
                uri = self.uri
                if self.trust_all:
                    uri = (
                        uri.replace("neo4j+s://", "neo4j+ssc://", 1)
                        .replace("bolt+s://", "bolt+ssc://", 1)
                    )
                    logger.debug("Neo4j trust_all_certs enabled - using self-signed certificate mode")

                # Create driver with connection pool (persistent connection)
                # Neo4j driver manages connection pooling internally
                logger.debug("Creating Neo4j driver with connection pool...")
                self.driver = GraphDatabase.driver(
                    uri,
                    auth=(self.user, self.password),
                    # Connection pool settings for better performance
                    max_connection_lifetime=3600,  # 1 hour
                    max_connection_pool_size=50,   # Pool size
                    connection_acquisition_timeout=30,  # 30 seconds timeout
                )
                
                # Test connection
                logger.debug("Testing Neo4j connection with health check query...")
                session_args = {}
                if self.database:
                    session_args["database"] = self.database

                with self.driver.session(**session_args) as session:
                    result = session.run("RETURN 1 AS test")
                    result.single()
                
                self._is_connected = True
                logger.info(f"✅ Neo4j connection pool initialized successfully at {uri}")
                logger.info(f"Neo4j connection pool ready (max_pool_size=50, timeout=30s)")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to connect to Neo4j: {e}")
                logger.error(f"Connection details: URI={self.uri[:50]}..., User={self.user}, Database={self.database or 'default'}")
                if "DNS" in str(e) or "resolve" in str(e).lower():
                    logger.error("DNS resolution failed - check if Neo4j instance is active and URI is correct")
                elif "authentication" in str(e).lower() or "unauthorized" in str(e).lower():
                    logger.error("Authentication failed - check NEO4J_USER and NEO4J_PASSWORD")
                elif "certificate" in str(e).lower() or "ssl" in str(e).lower():
                    logger.error("SSL/TLS certificate error - try setting NEO4J_TRUST_ALL_CERTS=true")
                self._is_connected = False
                if self.driver:
                    try:
                        self.driver.close()
                    except:
                        pass
                    self.driver = None
                return False
        
        return self._is_connected
    
    def is_connected(self) -> bool:
        """Check if Neo4j is connected"""
        return self._is_connected and self.driver is not None
    
    def close(self):
        """Close the connection pool"""
        if self.driver:
            try:
                self.driver.close()
                logger.info("Neo4j connection pool closed")
            except Exception as e:
                logger.warning(f"Error closing Neo4j connection: {e}")
            finally:
                self.driver = None
                self._is_connected = False
    
    def run_cypher(self, query: str, params: dict = None):
        """
        Execute a Cypher query using persistent connection pool
        
        Args:
            query: Cypher query string
            params: Query parameters
            
        Returns:
            List of records
        """
        # Ensure connection is established (lazy connection if needed)
        if not self.is_connected():
            if not self.connect():
                raise Exception("Not connected to Neo4j and connection attempt failed.")
        
        session_args = {}
        if self.database:
            session_args["database"] = self.database

        try:
            # Use connection pool (driver manages session reuse)
            with self.driver.session(**session_args) as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except Exception as e:
            # Connection might have dropped, try to reconnect once
            logger.warning(f"Neo4j query failed, attempting reconnect: {e}")
            self._is_connected = False
            if self.connect():
                # Retry query once
                with self.driver.session(**session_args) as session:
                    result = session.run(query, params or {})
                    return [record.data() for record in result]
            raise


# Global client instance
neo4j_client = Neo4jClient()


def run_cypher(query: str, params: dict = None):
    """Helper function to run Cypher queries"""
    return neo4j_client.run_cypher(query, params)