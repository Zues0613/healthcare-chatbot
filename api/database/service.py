"""
Database service layer using asyncpg (replaces Prisma)
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import uuid

from .db_client import db_client

logger = logging.getLogger("health_assistant")


class DatabaseService:
    """Service layer for database operations using asyncpg"""
    
    @staticmethod
    async def get_or_create_customer(
        profile_data: Dict[str, Any],
        customer_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing customer or update profile
        
        Args:
            profile_data: Profile data from request
            customer_id: Customer ID (required for updates)
        
        Returns:
            Customer dict or None
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot save customer")
            return None
        
        if not customer_id:
            logger.warning("Customer ID is required for profile updates")
            return None
        
        try:
            # Get existing customer
            customer = await db_client.fetchrow(
                "SELECT * FROM customers WHERE id = $1",
                customer_id
            )
            
            if not customer:
                logger.warning(f"Customer not found: {customer_id}")
                return None
            
            # Update customer metadata if provided (keep in customers table)
            customer_update_fields = []
            customer_update_values = []
            param_num = 1
            
            if "metadata" in profile_data:
                customer_update_fields.append(f"metadata = ${param_num}::jsonb")
                customer_update_values.append(json.dumps(profile_data["metadata"]))
                param_num += 1
            
            if customer_update_fields:
                customer_update_values.append(customer_id)
                query = f"""
                    UPDATE customers 
                    SET {', '.join(customer_update_fields)}, updated_at = NOW()
                    WHERE id = ${param_num}
                """
                await db_client.execute(query, *customer_update_values)
            
            # Update or insert customer profile (in customer_profiles table)
            profile_fields = ["age", "sex", "diabetes", "hypertension", "pregnancy", "city", "medical_conditions"]
            profile_update_fields = []
            profile_insert_fields = ["customer_id"]
            profile_insert_values = [customer_id]
            
            # Build INSERT fields and values, and UPDATE fields
            # Note: UPDATE clause uses EXCLUDED to reference INSERT values, so we don't need separate parameter numbers
            for field in profile_fields:
                if field in profile_data:
                    profile_insert_fields.append(field)
                    if field == "medical_conditions":
                        profile_insert_values.append(json.dumps(profile_data[field]))
                        profile_update_fields.append(f"{field} = EXCLUDED.{field}")
                    elif field == "age":
                        # Ensure age is an integer
                        age_value = int(profile_data[field]) if profile_data[field] is not None else None
                        profile_insert_values.append(age_value)
                        profile_update_fields.append(f"{field} = EXCLUDED.{field}")
                    else:
                        profile_insert_values.append(profile_data[field])
                        profile_update_fields.append(f"{field} = EXCLUDED.{field}")
            
            if profile_update_fields:
                # Use INSERT ... ON CONFLICT to handle both insert and update
                # EXCLUDED references the values being inserted, avoiding parameter numbering issues
                update_clause = ", ".join(profile_update_fields)
                insert_clause = ", ".join(profile_insert_fields)
                placeholders = ", ".join([f"${i+1}" for i in range(len(profile_insert_values))])
                
                query = f"""
                    INSERT INTO customer_profiles ({insert_clause}, updated_at)
                    VALUES ({placeholders}, NOW())
                    ON CONFLICT (customer_id)
                    DO UPDATE SET {update_clause}, updated_at = NOW()
                """
                await db_client.execute(query, *profile_insert_values)
                logger.info(f"Updated customer profile: {customer_id}")
            
            # Return updated customer with profile
            return await DatabaseService.get_customer(customer_id)
        except Exception as e:
            logger.error(f"Error updating customer: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_or_create_session(
        customer_id: str,
        language: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing session or create a new one
        
        Args:
            customer_id: Customer ID
            language: Language code
            session_id: Optional session ID to retrieve existing session
        
        Returns:
            ChatSession dict or None
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot save session")
            return None
        
        try:
            if session_id:
                # Try to get existing session
                logger.info(f"Looking for existing session: session_id={session_id}, customer_id={customer_id}")
                session = await db_client.fetchrow(
                    "SELECT * FROM chat_sessions WHERE id = $1 AND customer_id = $2",
                    session_id, customer_id
                )
                if session:
                    logger.info(f"Found existing session: {session_id}")
                    # Update language if provided
                    if language:
                        session = await db_client.fetchrow(
                            """
                            UPDATE chat_sessions 
                            SET language = $1, updated_at = NOW()
                            WHERE id = $2
                            RETURNING *
                            """,
                            language, session_id
                        )
                    return dict(session) if session else None
                else:
                    logger.warning(f"Session not found: session_id={session_id}, customer_id={customer_id}. Creating new session.")
            
            # Create new session
            new_session_id = str(uuid.uuid4())
            logger.info(f"Creating new session: new_session_id={new_session_id}, customer_id={customer_id}")
            session = await db_client.fetchrow(
                """
                INSERT INTO chat_sessions (id, customer_id, language, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                RETURNING *
                """,
                new_session_id, customer_id, language
            )
            logger.info(f"Created new chat session: {new_session_id}")
            return dict(session) if session else None
        except Exception as e:
            logger.error(f"Error getting/creating session: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_cached_chat_response(
        text: str,
        profile: Dict[str, Any],
        lang: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached chat response from database (L3 cache)
        Searches for recent assistant responses matching the query and profile
        
        Args:
            text: User's query text
            profile: User profile dict
            lang: Language code
            
        Returns:
            Cached response dict or None
        """
        if not await db_client.ensure_connected():
            return None
        
        try:
            # Normalize text for matching
            normalized_text = text.lower().strip()
            
            # Build query with proper parameter binding
            param_num = 1
            params = [normalized_text]
            conditions = [f"LOWER(TRIM(cm.message_text)) = ${param_num}"]
            param_num += 1
            
            # Add language filter
            if lang:
                conditions.append(f"cm.language = ${param_num}")
                params.append(lang)
                param_num += 1
            
            # Add profile filters
            if profile.get("age"):
                conditions.append(f"cm.metadata->>'age' = ${param_num}")
                params.append(str(profile["age"]))
                param_num += 1
            if profile.get("sex"):
                conditions.append(f"cm.metadata->>'sex' = ${param_num}")
                params.append(profile["sex"])
                param_num += 1
            if profile.get("diabetes"):
                conditions.append("(cm.metadata->>'diabetes')::boolean = true")
            if profile.get("hypertension"):
                conditions.append("(cm.metadata->>'hypertension')::boolean = true")
            if profile.get("pregnancy"):
                conditions.append("(cm.metadata->>'pregnancy')::boolean = true")
            
            # Query for recent matching assistant responses (within last 24 hours)
            query = f"""
                SELECT 
                    cm.answer,
                    cm.route,
                    cm.safety_data,
                    cm.facts,
                    cm.citations,
                    cm.metadata,
                    cm.language,
                    cm.created_at
                FROM chat_messages cm
                WHERE cm.role = 'assistant'
                    AND {' AND '.join(conditions)}
                    AND cm.created_at > NOW() - INTERVAL '24 hours'
                ORDER BY cm.created_at DESC
                LIMIT 1
            """
            
            result = await db_client.fetchrow(query, *params)
            
            if result:
                logger.debug(f"Cache HIT (L3 Database): Found matching response")
                
                # Parse JSONB fields if they're strings
                safety_data = result["safety_data"]
                if isinstance(safety_data, str):
                    try:
                        safety_data = json.loads(safety_data)
                    except (json.JSONDecodeError, TypeError):
                        safety_data = {}
                elif safety_data is None:
                    safety_data = {}
                
                facts_data = result["facts"]
                if isinstance(facts_data, str):
                    try:
                        facts_data = json.loads(facts_data)
                    except (json.JSONDecodeError, TypeError):
                        facts_data = []
                elif facts_data is None:
                    facts_data = []
                
                citations_data = result["citations"]
                if isinstance(citations_data, str):
                    try:
                        citations_data = json.loads(citations_data)
                    except (json.JSONDecodeError, TypeError):
                        citations_data = []
                elif citations_data is None:
                    citations_data = []
                
                metadata_data = result["metadata"]
                if isinstance(metadata_data, str):
                    try:
                        metadata_data = json.loads(metadata_data)
                    except (json.JSONDecodeError, TypeError):
                        metadata_data = {}
                elif metadata_data is None:
                    metadata_data = {}
                
                return {
                    "answer": result["answer"],
                    "route": result["route"],
                    "safety": safety_data,
                    "facts": facts_data,
                    "citations": citations_data,
                    "metadata": metadata_data,
                    "language": result["language"],
                    "cached_at": result["created_at"].isoformat() if result["created_at"] else None,
                }
            
            return None
        except Exception as e:
            logger.warning(f"Error querying cached response from database: {e}")
            return None
    
    @staticmethod
    async def save_chat_message(
        session_id: str,
        role: str,
        message_text: str,
        language: Optional[str] = None,
        answer: Optional[str] = None,
        route: Optional[str] = None,
        safety_data: Optional[Dict[str, Any]] = None,
        facts: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Save a chat message to the database
        
        Args:
            session_id: Chat session ID
            role: Message role (user, assistant)
            message_text: Message text
            language: Language code
            answer: Assistant's answer (for assistant messages)
            route: Route used (graph, vector)
            safety_data: Safety analysis data
            facts: Facts array
            citations: Citations array
            metadata: Additional metadata
        
        Returns:
            ChatMessage dict or None
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot save message")
            return None
        
        try:
            message_id = str(uuid.uuid4())
            
            # Log citations being saved (for assistant messages)
            if role == "assistant" and citations:
                logger.info(f"💾 Saving citations for message {message_id[:8]}: {len(citations)} citations")
                logger.debug(f"   Citations data: {json.dumps(citations[:2] if len(citations) > 2 else citations, indent=2)}")
            elif role == "assistant":
                logger.warning(f"⚠️ No citations provided for assistant message {message_id[:8]}")
            
            # Save message
            message = await db_client.fetchrow(
                """
                INSERT INTO chat_messages (
                    id, session_id, role, message_text, language, answer, route,
                    safety_data, facts, citations, metadata, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10::jsonb, $11::jsonb, NOW())
                RETURNING *
                """,
                message_id, session_id, role, message_text, language, answer, route,
                json.dumps(safety_data) if safety_data else None,
                json.dumps(facts) if facts else None,
                json.dumps(citations) if citations else None,
                json.dumps(metadata) if metadata else None
            )
            # Update session's updated_at to reflect last activity (last message time)
            await db_client.execute(
                "UPDATE chat_sessions SET updated_at = NOW() WHERE id = $1",
                session_id
            )
            logger.debug(f"Saved chat message: {message_id} and updated session last activity")
            return dict(message) if message else None
        except Exception as e:
            logger.error(f"Error saving chat message: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_customer_sessions(
        customer_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get chat sessions for a customer
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of sessions to return
        
        Returns:
            List of session dicts
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot retrieve sessions")
            return []
        
        try:
            # Get sessions with last activity time, message count, and first message in one query
            sessions = await db_client.fetch(
                """
                SELECT 
                    cs.*,
                    COALESCE(MAX(cm.created_at), cs.created_at) as last_activity_at,
                    COUNT(cm.id) as message_count,
                    (
                        SELECT message_text 
                        FROM chat_messages 
                        WHERE session_id = cs.id AND role = 'user' 
                        ORDER BY created_at ASC 
                        LIMIT 1
                    ) as first_message_text
                FROM chat_sessions cs
                LEFT JOIN chat_messages cm ON cm.session_id = cs.id
                WHERE cs.customer_id = $1
                GROUP BY cs.id
                ORDER BY last_activity_at DESC
                LIMIT $2
                """,
                customer_id, limit
            )
            return [dict(s) for s in sessions]
        except Exception as e:
            logger.error(f"Error retrieving customer sessions: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_session_first_message(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the first user message from a session (for display as title)
        
        Args:
            session_id: Session ID
            
        Returns:
            First user message dict or None
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot retrieve first message")
            return None
        
        try:
            messages = await db_client.fetch(
                """
                SELECT message_text, role
                FROM chat_messages
                WHERE session_id = $1 AND role = 'user'
                ORDER BY created_at ASC
                LIMIT 1
                """,
                session_id
            )
            if messages:
                return dict(messages[0])
            return None
        except Exception as e:
            logger.error(f"Error retrieving first message: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_session_message_count(session_id: str) -> int:
        """
        Get the count of messages in a session (efficient COUNT query)
        
        Args:
            session_id: Session ID
            
        Returns:
            Number of messages in the session
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot retrieve message count")
            return 0
        
        try:
            result = await db_client.fetchrow(
                """
                SELECT COUNT(*) as count
                FROM chat_messages
                WHERE session_id = $1
                """,
                session_id
            )
            if result:
                return result.get("count", 0)
            return 0
        except Exception as e:
            logger.error(f"Error retrieving message count: {e}", exc_info=True)
            return 0
    
    @staticmethod
    async def get_session_messages(
        session_id: str,
        limit: int = 100,
        customer_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a session
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
            customer_id: Optional customer ID to filter feedback (if provided, only returns feedback from this customer)
        
        Returns:
            List of message dicts
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot retrieve messages")
            return []
        
        try:
            logger.info(f"Retrieving messages for session_id: {session_id}, limit: {limit}, customer_id: {customer_id}")
            
            if customer_id:
                # Try to include feedback only for the specified customer
                # Fall back to query without feedback if message_feedback table doesn't exist
                try:
                    messages = await db_client.fetch(
                        """
                        SELECT 
                            m.*,
                            f.feedback as user_feedback
                        FROM chat_messages m
                        LEFT JOIN message_feedback f ON m.id = f.message_id AND f.customer_id = $3
                        WHERE m.session_id = $1
                        ORDER BY m.created_at ASC
                        LIMIT $2
                        """,
                        session_id, limit, customer_id
                    )
                except Exception as e:
                    # If message_feedback table doesn't exist, fall back to query without feedback
                    if "message_feedback" in str(e) or "does not exist" in str(e):
                        logger.warning(f"message_feedback table not found, retrieving messages without feedback: {e}")
                        messages = await db_client.fetch(
                            """
                            SELECT 
                                m.*,
                                NULL as user_feedback
                            FROM chat_messages m
                            WHERE m.session_id = $1
                            ORDER BY m.created_at ASC
                            LIMIT $2
                            """,
                            session_id, limit
                        )
                    else:
                        # Re-raise if it's a different error
                        raise
            else:
                # Get messages without filtering feedback (for admin or when customer_id not needed)
                messages = await db_client.fetch(
                    """
                    SELECT 
                        m.*,
                        NULL as user_feedback
                    FROM chat_messages m
                    WHERE m.session_id = $1
                    ORDER BY m.created_at ASC
                    LIMIT $2
                    """,
                    session_id, limit
                )
            logger.info(f"Found {len(messages)} messages for session_id: {session_id}")
            
            # Parse JSONB fields properly
            parsed_messages = []
            for m in messages:
                msg_dict = dict(m)
                # Parse JSONB fields if they're strings
                for json_field in ["citations", "facts", "safety_data", "metadata"]:
                    if json_field in msg_dict:
                        value = msg_dict[json_field]
                        # Log raw value for citations to debug
                        if json_field == "citations" and msg_dict.get("role") == "assistant":
                            logger.info(f"🔍 Raw citations from DB for message {msg_dict.get('id', 'unknown')[:8]}: type={type(value)}, value={value}")
                        
                        if isinstance(value, str):
                            try:
                                parsed_value = json.loads(value) if value else None
                                msg_dict[json_field] = parsed_value
                                if json_field == "citations" and msg_dict.get("role") == "assistant":
                                    logger.info(f"✅ Parsed citations: {len(parsed_value) if isinstance(parsed_value, list) else 'not a list'}")
                            except (json.JSONDecodeError, TypeError) as e:
                                logger.warning(f"⚠️ Failed to parse {json_field}: {e}, value: {value}")
                                msg_dict[json_field] = None
                        elif value is None:
                            # Ensure empty arrays for citations and facts, empty dict for others
                            if json_field in ["citations", "facts"]:
                                msg_dict[json_field] = []
                            elif json_field in ["safety_data", "metadata"]:
                                msg_dict[json_field] = {}
                        # If value is already a list/dict (from JSONB), keep it as is
                        elif json_field == "citations" and msg_dict.get("role") == "assistant":
                            logger.info(f"✅ Citations already parsed: type={type(value)}, length={len(value) if isinstance(value, list) else 'N/A'}")
                parsed_messages.append(msg_dict)
            
            return parsed_messages
        except Exception as e:
            logger.error(f"Error retrieving session messages: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID with profile data (JOIN with customer_profiles)"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            customer = await db_client.fetchrow(
                """
                SELECT 
                    c.*,
                    cp.age,
                    cp.sex,
                    cp.diabetes,
                    cp.hypertension,
                    cp.pregnancy,
                    cp.city,
                    cp.medical_conditions
                FROM customers c
                LEFT JOIN customer_profiles cp ON c.id = cp.customer_id
                WHERE c.id = $1
                """,
                customer_id
            )
            if customer:
                customer_dict = dict(customer)
                # Ensure medical_conditions is a list if it exists
                if customer_dict.get("medical_conditions") and isinstance(customer_dict["medical_conditions"], str):
                    try:
                        customer_dict["medical_conditions"] = json.loads(customer_dict["medical_conditions"])
                    except:
                        customer_dict["medical_conditions"] = []
                elif customer_dict.get("medical_conditions") is None:
                    customer_dict["medical_conditions"] = []
                return customer_dict
            return None
        except Exception as e:
            logger.error(f"Error retrieving customer: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def update_customer_profile(
        customer_id: str,
        profile_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update customer profile"""
        return await DatabaseService.get_or_create_customer(profile_data, customer_id)
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID with messages"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            session = await db_client.fetchrow(
                "SELECT * FROM chat_sessions WHERE id = $1",
                session_id
            )
            if session:
                session_dict = dict(session)
                # Get messages
                messages = await DatabaseService.get_session_messages(session_id, customer_id=session.get("customer_id"))
                session_dict["messages"] = messages
                return session_dict
            return None
        except Exception as e:
            logger.error(f"Error retrieving session: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def create_customer(
        email: str,
        password_hash: str,
        role: str = "user",
        profile_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new customer (and profile if profile_data provided)"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            customer_id = str(uuid.uuid4())
            # Insert into customers table (only auth/account info)
            customer = await db_client.fetchrow(
                """
                INSERT INTO customers (
                    id, email, password_hash, role, is_active, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                RETURNING *
                """,
                customer_id, email, password_hash, role, True
            )
            
            # If profile_data provided, create profile
            if profile_data:
                profile_fields = ["age", "sex", "diabetes", "hypertension", "pregnancy", "city", "medical_conditions"]
                profile_insert_fields = ["customer_id"]
                profile_insert_values = [customer_id]
                
                for field in profile_fields:
                    if field in profile_data:
                        profile_insert_fields.append(field)
                        if field == "medical_conditions":
                            profile_insert_values.append(json.dumps(profile_data[field]))
                        elif field == "age":
                            # Ensure age is an integer
                            age_value = int(profile_data[field]) if profile_data[field] is not None else None
                            profile_insert_values.append(age_value)
                        else:
                            profile_insert_values.append(profile_data[field])
                
                if len(profile_insert_fields) > 1:  # More than just customer_id
                    placeholders = ", ".join([f"${i+1}" for i in range(len(profile_insert_values))])
                    insert_clause = ", ".join(profile_insert_fields)
                    await db_client.execute(
                        f"""
                        INSERT INTO customer_profiles ({insert_clause}, created_at, updated_at)
                        VALUES ({placeholders}, NOW(), NOW())
                        """,
                        *profile_insert_values
                    )
            
            # Return customer with profile (using get_customer to get JOINed data)
            return await DatabaseService.get_customer(customer_id)
        except Exception as e:
            logger.error(f"Error creating customer: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email with profile data (JOIN with customer_profiles)"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            customer = await db_client.fetchrow(
                """
                SELECT 
                    c.*,
                    cp.age,
                    cp.sex,
                    cp.diabetes,
                    cp.hypertension,
                    cp.pregnancy,
                    cp.city,
                    cp.medical_conditions
                FROM customers c
                LEFT JOIN customer_profiles cp ON c.id = cp.customer_id
                WHERE c.email = $1
                """,
                email
            )
            if customer:
                customer_dict = dict(customer)
                # Ensure medical_conditions is a list if it exists
                if customer_dict.get("medical_conditions") and isinstance(customer_dict["medical_conditions"], str):
                    try:
                        customer_dict["medical_conditions"] = json.loads(customer_dict["medical_conditions"])
                    except:
                        customer_dict["medical_conditions"] = []
                elif customer_dict.get("medical_conditions") is None:
                    customer_dict["medical_conditions"] = []
                return customer_dict
            return None
        except Exception as e:
            logger.error(f"Error retrieving customer by email: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_all_customers(limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all customers from the database"""
        if not await db_client.ensure_connected():
            return []
        
        try:
            customers = await db_client.fetch(
                """
                SELECT 
                    c.id,
                    c.email,
                    c.role,
                    c.is_active,
                    c.created_at,
                    c.last_login,
                    cp.age,
                    cp.sex,
                    cp.diabetes,
                    cp.hypertension,
                    cp.pregnancy,
                    cp.city,
                    cp.medical_conditions
                FROM customers c
                LEFT JOIN customer_profiles cp ON c.id = cp.customer_id
                ORDER BY c.created_at DESC
                LIMIT $1
                """,
                limit
            )
            # Parse medical_conditions JSONB for each customer
            result = []
            for customer in customers:
                customer_dict = dict(customer)
                if customer_dict.get("medical_conditions") and isinstance(customer_dict["medical_conditions"], str):
                    try:
                        customer_dict["medical_conditions"] = json.loads(customer_dict["medical_conditions"])
                    except:
                        customer_dict["medical_conditions"] = []
                elif customer_dict.get("medical_conditions") is None:
                    customer_dict["medical_conditions"] = []
                result.append(customer_dict)
            return result
        except Exception as e:
            logger.error(f"Error retrieving all customers: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def update_customer_last_login(customer_id: str) -> None:
        """Update customer's last login time"""
        if not await db_client.ensure_connected():
            return
        
        try:
            await db_client.execute(
                "UPDATE customers SET last_login = NOW() WHERE id = $1",
                customer_id
            )
        except Exception as e:
            logger.error(f"Error updating last login: {e}", exc_info=True)
    
    @staticmethod
    async def save_refresh_token(
        customer_id: str,
        token: str,
        expires_at: datetime
    ) -> None:
        """Save refresh token"""
        if not await db_client.ensure_connected():
            return
        
        try:
            token_id = str(uuid.uuid4())
            await db_client.execute(
                """
                INSERT INTO refresh_tokens (id, token, customer_id, expires_at, created_at, revoked)
                VALUES ($1, $2, $3, $4, NOW(), FALSE)
                ON CONFLICT (token) DO UPDATE SET expires_at = $4, revoked = FALSE
                """,
                token_id, token, customer_id, expires_at
            )
        except Exception as e:
            logger.error(f"Error saving refresh token: {e}", exc_info=True)
    
    @staticmethod
    async def get_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """Get refresh token"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            token_data = await db_client.fetchrow(
                """
                SELECT * FROM refresh_tokens 
                WHERE token = $1 AND revoked = FALSE AND expires_at > NOW()
                """,
                token
            )
            return dict(token_data) if token_data else None
        except Exception as e:
            logger.error(f"Error retrieving refresh token: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def revoke_refresh_token(token: str) -> None:
        """Revoke refresh token"""
        if not await db_client.ensure_connected():
            return
        
        try:
            await db_client.execute(
                "UPDATE refresh_tokens SET revoked = TRUE WHERE token = $1",
                token
            )
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}", exc_info=True)
    
    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """
        Delete a chat session and all its messages
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if not await db_client.ensure_connected():
            return False
        
        try:
            # Delete all messages first (CASCADE should handle this, but being explicit)
            await db_client.execute(
                "DELETE FROM chat_messages WHERE session_id = $1",
                session_id
            )
            # Delete the session
            result = await db_client.execute(
                "DELETE FROM chat_sessions WHERE id = $1",
                session_id
            )
            return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Error deleting session: {e}", exc_info=True)
            return False


# Global service instance
db_service = DatabaseService()
