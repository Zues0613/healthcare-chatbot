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
            
            # Update customer profile if provided
            update_fields = []
            update_values = []
            param_num = 1
            
            for field in ["age", "sex", "diabetes", "hypertension", "pregnancy", "city"]:
                if field in profile_data:
                    update_fields.append(f"{field} = ${param_num}")
                    update_values.append(profile_data[field])
                    param_num += 1
            
            if "medical_conditions" in profile_data:
                update_fields.append(f"medical_conditions = ${param_num}::jsonb")
                update_values.append(json.dumps(profile_data["medical_conditions"]))
                param_num += 1
            
            if "metadata" in profile_data:
                update_fields.append(f"metadata = ${param_num}::jsonb")
                update_values.append(json.dumps(profile_data["metadata"]))
                param_num += 1
            
            if update_fields:
                update_values.append(customer_id)
                query = f"""
                    UPDATE customers 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE id = ${param_num}
                    RETURNING *
                """
                customer = await db_client.fetchrow(query, *update_values)
                logger.info(f"Updated customer profile: {customer_id}")
            
            return dict(customer) if customer else None
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
                session = await db_client.fetchrow(
                    "SELECT * FROM chat_sessions WHERE id = $1 AND customer_id = $2",
                    session_id, customer_id
                )
                if session:
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
            
            # Create new session
            new_session_id = str(uuid.uuid4())
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
            logger.debug(f"Saved chat message: {message_id}")
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
            sessions = await db_client.fetch(
                """
                SELECT * FROM chat_sessions
                WHERE customer_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                customer_id, limit
            )
            return [dict(s) for s in sessions]
        except Exception as e:
            logger.error(f"Error retrieving customer sessions: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_session_messages(
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get messages for a session
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
        
        Returns:
            List of message dicts
        """
        if not await db_client.ensure_connected():
            logger.warning("Database not connected, cannot retrieve messages")
            return []
        
        try:
            messages = await db_client.fetch(
                """
                SELECT * FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                session_id, limit
            )
            return [dict(m) for m in messages]
        except Exception as e:
            logger.error(f"Error retrieving session messages: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            customer = await db_client.fetchrow(
                "SELECT * FROM customers WHERE id = $1",
                customer_id
            )
            return dict(customer) if customer else None
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
                messages = await DatabaseService.get_session_messages(session_id)
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
        age: Optional[int] = None,
        sex: Optional[str] = None,
        diabetes: bool = False,
        hypertension: bool = False,
        pregnancy: bool = False,
        city: Optional[str] = None,
        medical_conditions: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a new customer"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            customer_id = str(uuid.uuid4())
            conditions_json = json.dumps(medical_conditions or [])
            customer = await db_client.fetchrow(
                """
                INSERT INTO customers (
                    id, email, password_hash, role, age, sex, diabetes, 
                    hypertension, pregnancy, city, medical_conditions, is_active, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12, NOW(), NOW())
                RETURNING *
                """,
                customer_id, email, password_hash, role, age, sex, diabetes,
                hypertension, pregnancy, city, conditions_json, True
            )
            return dict(customer) if customer else None
        except Exception as e:
            logger.error(f"Error creating customer: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_customer_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email"""
        if not await db_client.ensure_connected():
            return None
        
        try:
            customer = await db_client.fetchrow(
                "SELECT * FROM customers WHERE email = $1",
                email
            )
            return dict(customer) if customer else None
        except Exception as e:
            logger.error(f"Error retrieving customer by email: {e}", exc_info=True)
            return None
    
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


# Global service instance
db_service = DatabaseService()
