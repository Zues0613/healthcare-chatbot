import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from .prisma_client import prisma_client, get_prisma_client, PRISMA_AVAILABLE

logger = logging.getLogger("health_assistant")

# Try to import Prisma models
if PRISMA_AVAILABLE:
    try:
        from prisma.models import Customer, ChatSession, ChatMessage
    except ImportError:
        Customer = None
        ChatSession = None
        ChatMessage = None
else:
    Customer = None
    ChatSession = None
    ChatMessage = None


class DatabaseService:
    """Service layer for database operations using Prisma"""
    
    @staticmethod
    async def get_or_create_customer(
        profile_data: Dict[str, Any],
        customer_id: Optional[str] = None
    ) -> Optional[Customer]:
        """
        Get existing customer or update profile
        
        Note: Customer creation is now handled through authentication (register endpoint)
        This method only updates profile data for existing authenticated customers
        
        Args:
            profile_data: Profile data from request
            customer_id: Customer ID (required for updates)
        
        Returns:
            Customer instance or None
        """
        if not await prisma_client.ensure_connected():
            logger.warning("Database not connected, cannot save customer")
            return None
        
        if not customer_id:
            logger.warning("Customer ID is required for profile updates")
            return None
        
        try:
            client = await get_prisma_client()
            
            # Get existing customer
            customer = await client.customer.find_unique(where={"id": customer_id})
            if not customer:
                logger.warning(f"Customer not found: {customer_id}")
                return None
            
            # Update customer profile if provided
            update_data = {}
            if "age" in profile_data:
                update_data["age"] = profile_data.get("age")
            if "sex" in profile_data:
                update_data["sex"] = profile_data.get("sex")
            if "diabetes" in profile_data:
                update_data["diabetes"] = profile_data.get("diabetes", False)
            if "hypertension" in profile_data:
                update_data["hypertension"] = profile_data.get("hypertension", False)
            if "pregnancy" in profile_data:
                update_data["pregnancy"] = profile_data.get("pregnancy", False)
            if "city" in profile_data:
                update_data["city"] = profile_data.get("city")
            if "metadata" in profile_data:
                update_data["metadata"] = profile_data.get("metadata")
            
            if update_data:
                customer = await client.customer.update(
                    where={"id": customer_id},
                    data=update_data
                )
                logger.info(f"Updated customer profile: {customer_id}")
            
            return customer
        except Exception as e:
            logger.error(f"Error updating customer: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_or_create_session(
        customer_id: str,
        language: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Optional[ChatSession]:
        """
        Get existing session or create a new one
        
        Args:
            customer_id: Customer ID
            language: Language code
            session_id: Optional session ID to retrieve existing session
        
        Returns:
            ChatSession instance or None
        """
        if not await prisma_client.ensure_connected():
            logger.warning("Database not connected, cannot save session")
            return None
        
        try:
            client = await get_prisma_client()
            
            if session_id:
                # Try to get existing session
                chat_session = await client.chatsession.find_unique(
                    where={"id": session_id}
                )
                if chat_session and chat_session.customerId == customer_id:
                    # Update language if provided
                    if language:
                        chat_session = await client.chatsession.update(
                            where={"id": session_id},
                            data={"language": language}
                        )
                    return chat_session
            
            # Create new session
            chat_session = await client.chatsession.create(
                data={
                    "customerId": customer_id,
                    "language": language,
                }
            )
            logger.info(f"Created new chat session: {chat_session.id}")
            return chat_session
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
    ) -> Optional[ChatMessage]:
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
            ChatMessage instance or None
        """
        if not await prisma_client.ensure_connected():
            logger.warning("Database not connected, cannot save message")
            return None
        
        try:
            client = await get_prisma_client()
            
            # Prepare data dict, handling None values
            message_data = {
                "sessionId": session_id,
                "role": role,
                "messageText": message_text,
            }
            
            if language is not None:
                message_data["language"] = language
            if answer is not None:
                message_data["answer"] = answer
            if route is not None:
                message_data["route"] = route
            if safety_data is not None:
                message_data["safetyData"] = safety_data
            if facts is not None:
                message_data["facts"] = facts
            if citations is not None:
                message_data["citations"] = citations
            if metadata is not None:
                message_data["metadata"] = metadata
            
            message = await client.chatmessage.create(data=message_data)
            logger.debug(f"Saved chat message: {message.id}")
            return message
        except Exception as e:
            logger.error(f"Error saving chat message: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_customer_sessions(
        customer_id: str,
        limit: int = 50
    ) -> List[ChatSession]:
        """
        Get chat sessions for a customer
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of sessions to return
        
        Returns:
            List of ChatSession instances
        """
        if not await prisma_client.ensure_connected():
            logger.warning("Database not connected, cannot retrieve sessions")
            return []
        
        try:
            client = await get_prisma_client()
            sessions = await client.chatsession.find_many(
                where={"customerId": customer_id},
                order={"createdAt": "desc"},
                take=limit,
                include={"messages": True}
            )
            return sessions
        except Exception as e:
            logger.error(f"Error retrieving customer sessions: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_session_messages(
        session_id: str,
        limit: int = 100
    ) -> List[ChatMessage]:
        """
        Get messages for a session
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages to return
        
        Returns:
            List of ChatMessage instances
        """
        if not await prisma_client.ensure_connected():
            logger.warning("Database not connected, cannot retrieve messages")
            return []
        
        try:
            client = await get_prisma_client()
            messages = await client.chatmessage.find_many(
                where={"sessionId": session_id},
                order={"createdAt": "asc"},
                take=limit
            )
            return messages
        except Exception as e:
            logger.error(f"Error retrieving session messages: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_customer(customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        if not await prisma_client.ensure_connected():
            return None
        
        try:
            client = await get_prisma_client()
            customer = await client.customer.find_unique(
                where={"id": customer_id},
                include={"chatSessions": True}
            )
            return customer
        except Exception as e:
            logger.error(f"Error retrieving customer: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def update_customer_profile(
        customer_id: str,
        profile_data: Dict[str, Any]
    ) -> Optional[Customer]:
        """
        Update customer profile
        
        Args:
            customer_id: Customer ID
            profile_data: Profile data to update
        
        Returns:
            Updated customer or None
        """
        return await DatabaseService.get_or_create_customer(profile_data, customer_id)
    
    @staticmethod
    async def get_session(session_id: str) -> Optional[ChatSession]:
        """Get session by ID with messages"""
        if not await prisma_client.ensure_connected():
            return None
        
        try:
            client = await get_prisma_client()
            session = await client.chatsession.find_unique(
                where={"id": session_id},
                include={
                    "customer": True,
                    "messages": True
                }
            )
            if session and session.messages:
                # Sort messages by createdAt
                session.messages.sort(key=lambda m: m.createdAt)
            return session
        except Exception as e:
            logger.error(f"Error retrieving session: {e}", exc_info=True)
            return None


# Global service instance
db_service = DatabaseService()
