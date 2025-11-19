"""
Pipeline functions for the multilingual healthcare chatbot
"""

import json
import logging
from typing import Dict, Optional, Tuple, Any, List
from openai import OpenAI
from openai import APIError, RateLimitError

try:
    # Try relative import first (when used as module)
    from .pipeline_prompts import (
        LANGUAGE_DETECTION_TRANSLATION_PROMPT,
        REASONING_ANSWER_PROMPT,
        TRANSLATION_BACK_PROMPT,
        format_facts_context,
        format_user_profile,
    )
except ImportError:
    # Fallback to absolute import (when run as script)
    from pipeline_prompts import (
        LANGUAGE_DETECTION_TRANSLATION_PROMPT,
        REASONING_ANSWER_PROMPT,
        TRANSLATION_BACK_PROMPT,
        format_facts_context,
        format_user_profile,
    )

logger = logging.getLogger("health_assistant")


def detect_language_only(
    client: OpenAI,
    model: str,
    user_text: str,
    retry_count: int = 3
) -> str:
    """
    Detect language only (no translation) using GPT-4o-mini
    
    Args:
        client: OpenAI client
        model: Model name (should be gpt-4o-mini)
        user_text: User's input text
        retry_count: Number of retries on failure
        
    Returns:
        Detected language code (en, hi, ta, te, kn, ml)
    """
    detection_prompt = f"""Detect the language of the following text and respond with ONLY a valid JSON object.

Valid language codes: "en" (English), "hi" (Hindi), "ta" (Tamil), "te" (Telugu), "kn" (Kannada), "ml" (Malayalam)

IMPORTANT: The text may be written in English script (romanized). For example:
- "ennachu thala valikuthu" is Tamil (ta) written in English script (Tanglish)
- "kya hai" is Hindi (hi) written in English script (Hinglish)
- "em chestunnav" is Telugu (te) written in English script
- "yenu aagide" is Kannada (kn) written in English script
- "enthanu cheyyunnu" is Malayalam (ml) written in English script

Detect the INTENDED language based on the words and phrases, even if written in English script.

Text to analyze:
{user_text}

Respond with ONLY this JSON format:
{{
    "detected_language": "en"
}}

Do NOT translate. Only detect the language code."""
    
    for attempt in range(retry_count):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a language detection expert. Respond ONLY with valid JSON containing the detected language code."
                    },
                    {
                        "role": "user",
                        "content": detection_prompt
                    }
                ],
                max_tokens=50,
                temperature=0.1,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                result = json.loads(response_text)
                detected_lang = result.get("detected_language", "en").lower()
                
                # Validate language code
                valid_langs = {"en", "hi", "ta", "te", "kn", "ml"}
                if detected_lang not in valid_langs:
                    logger.warning(f"Invalid language code detected: {detected_lang}, defaulting to 'en'")
                    detected_lang = "en"
                
                return detected_lang
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {response_text[:100]}, error: {e}")
                # Fallback: assume English if JSON parsing fails
                if attempt < retry_count - 1:
                    continue
                return "en"
                
        except RateLimitError as e:
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
                continue
            logger.error(f"Rate limit error after {retry_count} attempts: {e}")
            return "en"
            
        except APIError as e:
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"API error, waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
                continue
            logger.error(f"API error after {retry_count} attempts: {e}")
            return "en"
            
        except Exception as e:
            logger.error(f"Unexpected error in language detection: {e}")
            if attempt < retry_count - 1:
                continue
            return "en"
    
    return "en"


def translate_to_english(
    client: OpenAI,
    model: str,
    user_text: str,
    source_language: str,
    retry_count: int = 3
) -> str:
    """
    Translate text from source language to English using GPT-4o-mini
    
    Args:
        client: OpenAI client
        model: Model name (should be gpt-4o-mini)
        user_text: User's input text in source language
        source_language: Source language code (hi, ta, te, kn, ml)
        retry_count: Number of retries on failure
        
    Returns:
        English translation of the text
    """
    lang_names = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
    }
    
    lang_name = lang_names.get(source_language, "Unknown")
    
    translation_prompt = f"""Translate the following {lang_name} text to English. Translate accurately while maintaining the meaning.

{lang_name} text:
{user_text}

Respond with ONLY the English translation, nothing else."""
    
    for attempt in range(retry_count):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate {lang_name} to English accurately."
                    },
                    {
                        "role": "user",
                        "content": translation_prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3,
            )
            
            translated = response.choices[0].message.content.strip()
            return translated
            
        except RateLimitError as e:
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
                continue
            logger.error(f"Rate limit error after {retry_count} attempts: {e}")
            return user_text
            
        except APIError as e:
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"API error, waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
                continue
            logger.error(f"API error after {retry_count} attempts: {e}")
            return user_text
            
        except Exception as e:
            logger.error(f"Unexpected error in translation: {e}")
            if attempt < retry_count - 1:
                continue
            return user_text
    
    return user_text


def detect_and_translate_to_english(
    client: OpenAI,
    model: str,
    user_text: str,
    retry_count: int = 3
) -> Tuple[str, str]:
    """
    Detect language and translate to English using GPT-4o-mini
    (Kept for backward compatibility, but now uses separate detection and translation)
    
    Args:
        client: OpenAI client
        model: Model name (should be gpt-4o-mini)
        user_text: User's input text
        retry_count: Number of retries on failure
        
    Returns:
        Tuple of (detected_language_code, english_text)
    """
    # First detect language
    detected_lang = detect_language_only(client, model, user_text, retry_count)
    
    # If English, no translation needed
    if detected_lang == "en":
        return "en", user_text
    
    # Otherwise, translate to English
    english_text = translate_to_english(client, model, user_text, detected_lang, retry_count)
    return detected_lang, english_text


async def generate_final_answer_stream(
    client: OpenAI,
    model: str,
    user_question: str,
    rag_context: str,
    facts: list,
    profile: Any,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    retry_count: int = 3
):
    """
    Generate final answer in English using GPT-4o-mini with RAG context and facts (STREAMING VERSION)
    
    Args:
        client: OpenAI client
        model: Model name (should be gpt-4o-mini)
        user_question: User's question in English
        rag_context: Context from ChromaDB RAG
        facts: Facts from Neo4j/graph database
        profile: User profile object
        conversation_history: Previous conversation messages for context (list of {"role": "user"/"assistant", "content": "..."})
        retry_count: Number of retries on failure
        
    Yields:
        Text chunks as they are generated
    """
    facts_context = format_facts_context(facts)
    user_profile_str = format_user_profile(profile)
    
    # Format RAG context - if empty, clearly indicate no information available
    if not rag_context or rag_context.strip() == "":
        formatted_rag_context = "⚠️ NO INFORMATION AVAILABLE IN KNOWLEDGE BASE: The knowledge base does not contain any relevant information for this query."
    else:
        formatted_rag_context = rag_context
    
    prompt = REASONING_ANSWER_PROMPT.format(
        rag_context=formatted_rag_context,
        facts_context=facts_context or "No specific facts from database.",
        user_question=user_question,
        user_profile=user_profile_str
    )
    
    # Build messages array with conversation history
    messages = [
        {
            "role": "system",
            "content": "You are a knowledgeable, empathetic healthcare assistant. For medical facts, use ONLY the indexed knowledge base provided in the context. For understanding follow-up questions, use conversation history to understand what the user is asking about. Once you understand the question from conversation history, use the knowledge base context to provide factual medical information. Never make up or invent medical facts. Always give thorough responses when context is available, covering understanding the concern, causes, solutions, and when to seek medical attention."
        }
    ]
    
    # Add conversation history if provided
    if conversation_history:
        # Limit to last 10 messages to avoid token limits
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        messages.extend(recent_history)
        logger.debug(f"Including {len(recent_history)} previous messages for context")
    
    # Add current user question
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    for attempt in range(retry_count):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,  # Increased for detailed, comprehensive responses
                temperature=0.7,
                stream=True,  # Enable streaming
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
            
            return  # Successfully completed
            
        except Exception as e:
            logger.warning(f"Error in generate_final_answer_stream (attempt {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                import asyncio
                await asyncio.sleep(1)
            else:
                logger.error(f"Failed to generate answer after {retry_count} attempts")
                yield "I apologize, but I encountered an error processing your request. Please try again."
                return
    
    yield "I apologize, but I encountered an error processing your request. Please try again."


def generate_final_answer(
    client: OpenAI,
    model: str,
    user_question: str,
    rag_context: str,
    facts: list,
    profile: Any,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    retry_count: int = 3
) -> str:
    """
    Generate final answer in English using GPT-4o-mini with RAG context and facts
    
    Args:
        client: OpenAI client
        model: Model name (should be gpt-4o-mini)
        user_question: User's question in English
        rag_context: Context from ChromaDB RAG
        facts: Facts from Neo4j/graph database
        profile: User profile object
        conversation_history: Previous conversation messages for context (list of {"role": "user"/"assistant", "content": "..."})
        retry_count: Number of retries on failure
        
    Returns:
        Answer text in English
    """
    facts_context = format_facts_context(facts)
    user_profile_str = format_user_profile(profile)
    
    # Format RAG context - if empty, clearly indicate no information available
    if not rag_context or rag_context.strip() == "":
        formatted_rag_context = "⚠️ NO INFORMATION AVAILABLE IN KNOWLEDGE BASE: The knowledge base does not contain any relevant information for this query."
    else:
        formatted_rag_context = rag_context
    
    prompt = REASONING_ANSWER_PROMPT.format(
        rag_context=formatted_rag_context,
        facts_context=facts_context or "No specific facts from database.",
        user_question=user_question,
        user_profile=user_profile_str
    )
    
    # Build messages array with conversation history
    messages = [
        {
            "role": "system",
            "content": "You are a knowledgeable, empathetic healthcare assistant. For medical facts, use ONLY the indexed knowledge base provided in the context. For understanding follow-up questions, use conversation history to understand what the user is asking about. Once you understand the question from conversation history, use the knowledge base context to provide factual medical information. Never make up or invent medical facts. Always give thorough responses when context is available, covering understanding the concern, causes, solutions, and when to seek medical attention."
        }
    ]
    
    # Add conversation history if provided
    if conversation_history:
        # Limit to last 10 messages to avoid token limits
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
        messages.extend(recent_history)
        logger.debug(f"Including {len(recent_history)} previous messages for context")
    
    # Add current user question
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    for attempt in range(retry_count):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,  # Increased for detailed, comprehensive responses
                temperature=0.7,
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except RateLimitError as e:
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
            else:
                logger.error(f"Rate limit error after {retry_count} attempts: {e}")
                return "I apologize, but I'm experiencing high demand. Please try again in a moment."
                
        except Exception as e:
            logger.warning(f"Error in generate_final_answer (attempt {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                import time
                time.sleep(1)
            else:
                logger.error(f"Failed to generate answer after {retry_count} attempts")
                return "I apologize, but I encountered an error processing your request. Please try again."
    
    return "I apologize, but I encountered an error processing your request. Please try again."


def translate_to_user_language(
    client: OpenAI,
    model: str,
    english_text: str,
    target_language: str,
    retry_count: int = 3
) -> str:
    """
    Translate English answer back to user's language using GPT-4o-mini
    Always outputs in native script (not romanized)
    
    Args:
        client: OpenAI client
        model: Model name (should be gpt-4o-mini)
        english_text: Answer text in English
        target_language: Target language code (hi, ta, te, kn, ml)
        retry_count: Number of retries on failure
        
    Returns:
        Translated text in target language (native script)
    """
    # Language name mapping
    lang_names = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
    }
    
    lang_name = lang_names.get(target_language, "English")
    
    # If target is English, return as is
    if target_language == "en":
        return english_text
    
    # Always use native script (not romanized)
    prompt = TRANSLATION_BACK_PROMPT.format(
        target_language=lang_name,
        english_text=english_text
    )
    
    for attempt in range(retry_count):
        try:
            system_content = f"You are a professional medical translator. Translate accurately to {lang_name} in NATIVE SCRIPT (NOT romanized/English script). For example, Tamil must be in Tamil script (தமிழ்), Telugu in Telugu script (తెలుగు), Kannada in Kannada script (ಕನ್ನಡ), Malayalam in Malayalam script (മലയാളം), and Hindi in Devanagari script (हिंदी)."
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            
            translated = response.choices[0].message.content.strip()
            return translated
            
        except RateLimitError as e:
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"Rate limit hit, waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
            else:
                logger.error(f"Rate limit error after {retry_count} attempts: {e}")
                return english_text  # Fallback to English
                
        except Exception as e:
            logger.warning(f"Error in translate_to_user_language (attempt {attempt + 1}): {e}")
            if attempt < retry_count - 1:
                import time
                time.sleep(1)
            else:
                logger.error(f"Failed to translate after {retry_count} attempts")
                return english_text  # Fallback to English
    
    return english_text  # Final fallback to English

