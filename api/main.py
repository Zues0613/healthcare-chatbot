import asyncio
import base64
import copy
import json
import logging
import os
import re
import tempfile
import time
from collections import defaultdict, deque
from io import BytesIO
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, Depends, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langdetect import LangDetectException, detect  # type: ignore
from openai import OpenAI
from starlette.middleware.base import RequestResponseEndpoint

try:
    from elevenlabs import VoiceSettings
    from elevenlabs.client import ElevenLabs
except Exception:  # pragma: no cover
    ElevenLabs = None
    VoiceSettings = None

try:
    from gtts import gTTS  # type: ignore
except Exception:  # pragma: no cover
    gTTS = None


def _load_environment() -> None:
    """
    Load .env values from either the api/ directory or the project root.
    This helps when the server starts from the repository root via start_server.py.
    """
    here = Path(__file__).resolve().parent
    candidates = [here / ".env", here.parent / ".env"]
    loaded = False
    for path in candidates:
        if path.exists():
            load_dotenv(path, override=True)
            loaded = True
    if not loaded:
        # Fallback to default behaviour (search current working directory / parents)
        load_dotenv()


_load_environment()

os.environ.setdefault("CHROMADB_DISABLE_TELEMETRY", "1")

from .safety import (
    detect_red_flags,
    detect_mental_health_crisis,
    detect_pregnancy_emergency,
    extract_symptoms,
)
from .router import is_graph_intent, extract_city
from .rag.retriever import retrieve, initialize_chroma_client
from .models import ChatRequest, ChatResponse, Profile, VoiceChatResponse

from .graph import fallback as graph_fallback
from .graph.cypher import (
    get_red_flags as neo4j_get_red_flags,
    get_contraindications as neo4j_get_contraindications,
    get_providers_in_city as neo4j_get_providers_in_city,
    get_safe_actions_for_metabolic_conditions as neo4j_get_safe_actions,
)
from .graph.client import neo4j_client
from .database import db_client, db_service
from .auth.routes import router as auth_router
from .auth.middleware import require_auth, require_role
from .pipeline_functions import (
    detect_and_translate_to_english,
    generate_final_answer,
    generate_final_answer_stream,
    translate_to_user_language,
)
from .services.cache import cache_service

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("health_assistant")

app = FastAPI(title="Health Assistant API")

# Include auth routes
app.include_router(auth_router)


@app.on_event("startup")
async def _startup() -> None:
    """Initialize persistent database connection pool and cache on startup"""
    try:
        # Initialize PostgreSQL connection pool (persistent, stays alive)
        connected = await db_client.connect()
        if connected:
            logger.info("PostgreSQL connection pool initialized successfully (persistent connection)")
        else:
            logger.warning("Database not connected - chat history will not be saved")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        logger.warning("Database not connected - chat history will not be saved")
    
    # Initialize cache service (Redis)
    # Force re-initialization to ensure connection is established
    logger.info("Initializing Redis cache (L2)...")
    cache_service.ensure_redis_connection()
    
    # Give it a moment to connect
    import asyncio
    await asyncio.sleep(0.1)
    
    if cache_service.is_available():
        logger.info("Redis cache (L2) initialized successfully")
    else:
        logger.warning("Redis cache (L2) not available - caching will use L1 and L3 only")
        # Log more details about why Redis is not available
        redis_uri = os.getenv("REDIS_URI")
        if not redis_uri:
            logger.warning("REDIS_URI environment variable is not set")
            logger.warning("Make sure REDIS_URI is set in your .env file")
        else:
            logger.info(f"REDIS_URI is set: {redis_uri[:30]}...")
            logger.warning("Check Redis connection logs above for connection errors")
            # Try one more time with explicit initialization
            logger.info("Attempting explicit Redis re-initialization...")
            try:
                cache_service._init_redis()
                if cache_service.is_available():
                    logger.info("Redis cache (L2) initialized successfully after retry")
                else:
                    logger.error("Redis initialization failed even after retry")
            except Exception as e:
                logger.error(f"Redis initialization error: {e}", exc_info=True)
    
    # Pre-initialize ChromaDB vector database (reduces cold start time)
    logger.info("Pre-initializing ChromaDB vector database...")
    try:
        initialize_chroma_client()
        logger.info("ChromaDB vector database pre-initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to pre-initialize ChromaDB (will initialize on first use): {e}")
    
    # Pre-initialize OpenAI client (reduces cold start time)
    logger.info("Pre-initializing OpenAI client...")
    try:
        openai_client = get_openai_client()
        if openai_client:
            logger.info("OpenAI client pre-initialized successfully")
        else:
            logger.warning("OpenAI client not configured (API key not set)")
    except Exception as e:
        logger.warning(f"Failed to pre-initialize OpenAI client (will initialize on first use): {e}")


@app.on_event("shutdown")
async def _shutdown() -> None:
    """Cleanup database connections on shutdown"""
    logger.info("Shutting down database connections...")
    if neo4j_client.driver:
        neo4j_client.close()
    # Close PostgreSQL connection pool
    await db_client.disconnect()
    logger.info("Database connections closed")

# CORS Configuration
# Parse CORS_ORIGINS from environment variable, allowing multiple origins separated by commas
# Default includes localhost for development
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
# Clean and split origins, handling spaces
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Specific origins from environment variable
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview and production deployments
    allow_credentials=True,  # Required for HTTP-only cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicitly include OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
)

class SimpleRateLimiter:
    def __init__(self, limit: int = 30, window: int = 60) -> None:
        self.limit = limit
        self.window = window
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)

    def configure(self, *, limit: Optional[int] = None, window: Optional[int] = None) -> None:
        if limit is not None:
            self.limit = limit
        if window is not None:
            self.window = window

    async def __call__(self, request: Request, call_next: RequestResponseEndpoint):
        if os.getenv("DISABLE_RATE_LIMIT") == "1" or self.limit <= 0:
            return await call_next(request)

        identifier = request.client.host if request.client else "anonymous"
        now = time.time()
        bucket = self.requests[identifier]

        while bucket and now - bucket[0] > self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:
            logger.warning("Rate limit exceeded", extra={"client": identifier})
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )

        bucket.append(now)
        response = await call_next(request)
        return response


rate_limiter = SimpleRateLimiter(
    limit=int(os.getenv("RATE_LIMIT", "30")),
    window=int(os.getenv("RATE_WINDOW", "60")),
)

if os.getenv("DISABLE_RATE_LIMIT") != "1":
    app.middleware("http")(rate_limiter)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    for error in errors:
        ctx = error.get("ctx")
        if ctx and "error" in ctx:
            ctx["error"] = str(ctx["error"])

    logger.warning(
        "Validation error",
        extra={"path": request.url.path, "errors": errors, "body": exc.body},
    )
    payload = jsonable_encoder({"detail": errors})
    return JSONResponse(status_code=422, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP error",
        extra={"path": request.url.path, "status_code": exc.status_code, "detail": exc.detail},
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

LANGUAGE_LABELS: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
}

SUPPORTED_LANG_CODES = set(LANGUAGE_LABELS.keys())
DEFAULT_LANG = "en"

FALLBACK_MESSAGE_EN = (
    "I'm here to help with health questions. Please note: I cannot provide medical diagnosis. "
    "For emergencies, call 108 or visit the nearest hospital."
)

DISCLAIMER_EN = (
    "⚠️ This is general information only, not medical advice. Consult a healthcare professional for proper diagnosis and treatment."
)

PREGNANCY_ALERT_GUIDANCE_EN = [
    "Severe pregnancy symptoms need urgent medical review.",
    "Contact your obstetrician or emergency services immediately.",
]

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_VOICE_DEFAULT = os.getenv("ELEVENLABS_VOICE", "Bella")
ELEVENLABS_VOICE_MAP = {
    "en": os.getenv("ELEVENLABS_VOICE_EN", ELEVENLABS_VOICE_DEFAULT),
    "hi": os.getenv("ELEVENLABS_VOICE_HI", ELEVENLABS_VOICE_DEFAULT),
    "ta": os.getenv("ELEVENLABS_VOICE_TA", ELEVENLABS_VOICE_DEFAULT),
    "te": os.getenv("ELEVENLABS_VOICE_TE", ELEVENLABS_VOICE_DEFAULT),
    "kn": os.getenv("ELEVENLABS_VOICE_KN", ELEVENLABS_VOICE_DEFAULT),
    "ml": os.getenv("ELEVENLABS_VOICE_ML", ELEVENLABS_VOICE_DEFAULT),
}

GTTS_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
}

ROMANIZED_CLUES: Dict[str, List[str]] = {
    "ta": [
        "ennachu",
        "ennada",
        "thala",
        "thalai",
        "valikuthu",
        "valikkuthu",
        "valichuthu",
        "sollu",
        "sapadu",
        "soru",
        "sollunga",
        "enna",
        "irukku",
        "illai",
        "naan",
        "neenga",
        "paati",
        "amma",
        "appa",
        "bro",
        "dei",
    ],
    "hi": [
        "kya",
        "nahi",
        "hai",
        "dard",
        "bukhar",
        "sir",
        "pet",
        "dawai",
        "davayi",
        "madad",
        "kripa",
        "bhai",
        "behen",
        "ghar",
        "ilaj",
    ],
    "te": [
        "em",
        "emi",
        "aina",
        "ayyayo",
        "nenu",
        "meeru",
        "chelli",
        "cheyyali",
        "noppi",
        "baadha",
        "ledhu",
        "ledu",
        "amma",
        "anna",
        "fever",
        "vundi",
        "pain",
    ],
    "kn": [
        "yen",
        "yenu",
        "maga",
        "thumba",
        "haudu",
        "illa",
        "mane",
        "bega",
        "nodi",
        "saar",
        "akka",
        "gottilla",
        "mane",
    ],
    "ml": [
        "entha",
        "enthaa",
        "vayaru",
        "vedana",
        "pani",
        "cheyyanam",
        "illa",
        "njan",
        "ammachi",
        "appo",
        "chedi",
        "vedana",
        "marunnu",
    ],
}

ROMANIZED_THRESHOLD = 2

LANGUAGE_SCRIPT_MAP: Dict[str, Optional[str]] = {
    "hi": "devanagari",
    "ta": "tamil",
    "te": "telugu",
    "kn": "kannada",
    "ml": "malayalam",
}

_eleven_client: Optional["ElevenLabs"] = None

OPENROUTER_API_KEY = (
    os.getenv("OPENROUTER_API_KEY")
    or os.getenv("DEEPSEEK_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)
OPENROUTER_BASE_URL = (
    os.getenv("DEEPSEEK_BASE_URL")
    or os.getenv("OPENROUTER_BASE_URL")
    or "https://openrouter.ai/api/v1"
)
OPENROUTER_MODEL = (
    os.getenv("DEEPSEEK_MODEL")
    or os.getenv("OPENROUTER_MODEL")
    or "openrouter/auto"
)
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_SITE_NAME", os.getenv("OPENROUTER_APP_NAME", "Healthcare Chatbot"))
OPENROUTER_EXTRA_HEADERS = {
    "HTTP-Referer": OPENROUTER_SITE_URL,
    "X-Title": OPENROUTER_APP_NAME,
}

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "en"


def translate_text(text: str, target_lang: str, src_lang: Optional[str] = None) -> str:
    """Translation is disabled - returns text as-is."""
    return text


def is_mostly_ascii(text: str) -> bool:
    return all(ord(ch) < 128 for ch in text)


def detect_romanized_language(text: str) -> Optional[str]:
    if not text or not is_mostly_ascii(text):
        return None

    lowered = text.lower()
    best_lang: Optional[str] = None
    best_score = 0

    for lang, clues in ROMANIZED_CLUES.items():
        score = sum(1 for clue in clues if clue in lowered)
        if score > best_score:
            best_score = score
            best_lang = lang

    if best_lang and best_score >= ROMANIZED_THRESHOLD:
        return best_lang
    return None


def attempt_native_script_conversion(text: str, lang: str) -> Optional[str]:
    """Native script conversion is disabled."""
    return None


def translate_romanized_to_english(
    text: str, lang: str
) -> Tuple[str, Optional[str], Dict[str, Any]]:
    """
    Translation is disabled - returns text as-is.
    """
    meta: Dict[str, Any] = {
        "provider": "none",
        "success": False,
        "reason": "translation_disabled",
        "attempts": []
    }
    return text, None, meta


def romanize_text(text: str, lang: str) -> str:
    # Check if transliteration libraries are available
    try:
        from indic_transliteration import sanscript  # type: ignore
        from indic_transliteration.sanscript import transliterate  # type: ignore
    except ImportError:
        # Transliteration libraries not available
        return text
    
    if (
        not text
        or lang == "en"
        or is_mostly_ascii(text)
    ):
        return text

    script_key = LANGUAGE_SCRIPT_MAP.get(lang)
    if not script_key:
        return text

    try:
        romanized = transliterate(text, script_key, sanscript.ITRANS)
        # Clean up spacing for readability
        romanized = romanized.replace("##", "").replace("~", "").strip()
        return romanized
    except Exception as exc:  # pragma: no cover
        logger.debug(
            "Romanization failed",
            extra={"lang": lang, "error": str(exc)},
        )
        return text


def _summarize_chunk(chunk: str, sentence_limit: int = 2) -> str:
    if not chunk:
        return ""
    sentences = re.split(r"(?<=[.?!])\s+", chunk.strip())
    summary = " ".join(sentences[:sentence_limit]).strip()
    return summary


def build_fallback_answer(
    *,
    query_en: str,
    rag_results: List[Dict[str, Any]],
    facts: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
    target_lang: str,
    response_style: str,
) -> str:
    lines: List[str] = []

    if rag_results:
        top_chunks = rag_results[:2]
        for idx, result in enumerate(top_chunks, start=1):
            chunk = result.get("chunk", "")
            summary = _summarize_chunk(chunk)
            if summary:
                lines.append(f"Key insight {idx}: {summary}")

    for fact in facts:
        f_type = fact.get("type")
        data = fact.get("data", [])
        if f_type == "safe_actions":
            for entry in data:
                condition = entry.get("condition")
                actions = ", ".join(entry.get("actions", []))
                lines.append(f"For {condition}, safe steps include: {actions}.")
        elif f_type == "contraindications":
            for entry in data:
                condition = entry.get("condition")
                avoids = ", ".join(entry.get("avoid", []))
                lines.append(f"Avoid {avoids} if you have {condition}.")
        elif f_type == "providers":
            providers = "; ".join(
                f"{item.get('provider')} ({item.get('mode', 'care')})"
                for item in data
            )
            if providers:
                lines.append(f"Nearby care options: {providers}.")

    if not lines:
        lines.append(
            "I don't have enough information from my knowledge base to give specific advice."
        )

    lines.append(
        "If symptoms worsen or you feel unwell, seek medical care or call 108 immediately."
    )

    if citations:
        cited_sources = ", ".join(
            cite.get("topic") or cite.get("source", "unknown") for cite in citations[:3]
        )
        lines.append(f"Sources consulted: {cited_sources}.")

    english_text = " ".join(lines)
    localized = localize_text(
        english_text,
        target_lang=target_lang,
        src_lang="en",
        response_style=response_style,
    )
    return localized


def localize_text(
    text: str,
    target_lang: str,
    src_lang: str = "en",
    response_style: str = "native",
    capture_meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Translation is disabled - returns text as-is."""
    meta: Dict[str, Any] = {
        "provider": "none",
        "success": False,
        "reason": "translation_disabled",
    }
    
    if capture_meta is not None:
        capture_meta.update(meta)
    
    return text


def get_language_label(code: str, response_style: str = "native") -> str:
    label = LANGUAGE_LABELS.get(code, LANGUAGE_LABELS[DEFAULT_LANG])
    if response_style == "romanized" and code != "en":
        return f"{label} (Romanized Latin script)"
    return label


def get_localized_disclaimer(lang: str, response_style: str = "native") -> str:
    return localize_text(DISCLAIMER_EN, target_lang=lang, response_style=response_style)


def localize_list(
    entries: List[str],
    lang: str,
    src_lang: str = "en",
    response_style: str = "native",
) -> List[str]:
    if lang == src_lang:
        localized = entries
    else:
        localized = [
            localize_text(item, target_lang=lang, src_lang=src_lang, response_style=response_style)
            for item in entries
        ]

    if response_style == "romanized" and lang != "en":
        return [romanize_text(item, lang) for item in localized]

    return localized


def get_elevenlabs_client() -> Optional["ElevenLabs"]:
    global _eleven_client
    if _eleven_client is None and ELEVENLABS_API_KEY and ElevenLabs:
        try:
            _eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to initialise ElevenLabs client", extra={"error": str(exc)})
            _eleven_client = None
    return _eleven_client


def transcribe_audio_bytes(audio_bytes: bytes, *, language_hint: Optional[str] = None) -> str:
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio data received.")

    client = get_openai_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Speech service unavailable. Configure OPENAI_API_KEY for Whisper transcription.",
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            payload: Dict[str, Any] = {
                "model": "whisper-1",
                "file": audio_file,
            }
            if language_hint and language_hint in SUPPORTED_LANG_CODES:
                payload["language"] = language_hint
            transcription = client.audio.transcriptions.create(**payload)
        logger.info(
            "Speech-to-text processed successfully",
            extra={"bytes": len(audio_bytes), "language_hint": language_hint},
        )
        return transcription.text
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Whisper transcription failed")
        raise HTTPException(status_code=502, detail=f"STT error: {str(exc)}") from exc
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:  # pragma: no cover
            pass


def synthesize_speech(text: str, language_code: str) -> Tuple[bytes, str, str]:
    text = text.strip()
    if not text:
        return b"", "none", "text/plain"

    # Try ElevenLabs first if configured
    if ELEVENLABS_API_KEY and ElevenLabs:
        client = get_elevenlabs_client()
        voice = ELEVENLABS_VOICE_MAP.get(language_code, ELEVENLABS_VOICE_DEFAULT)
        if client:
            try:
                audio_iter = client.generate(
                    text=text,
                    voice=voice,
                    model=ELEVENLABS_MODEL,
                    voice_settings=VoiceSettings(stability=0.4, similarity_boost=0.75)
                    if VoiceSettings
                    else None,
                )
                audio_bytes = b"".join(audio_iter)
                return audio_bytes, "elevenlabs", "audio/mpeg"
            except Exception as exc:  # pragma: no cover
                logger.warning("ElevenLabs synthesis failed", extra={"error": str(exc)})

    if gTTS:
        lang = GTTS_LANG_MAP.get(language_code, "en")
        try:
            tts = gTTS(text=text, lang=lang)
            buffer = BytesIO()
            tts.write_to_fp(buffer)
            return buffer.getvalue(), "gtts", "audio/mpeg"
        except Exception as exc:  # pragma: no cover
            logger.warning("gTTS synthesis failed", extra={"error": str(exc), "lang": lang})

    logger.warning("Falling back to text-only response for TTS", extra={"lang": language_code})
    return b"", "text-only", "text/plain"


def encode_audio_base64(audio_bytes: bytes) -> str:
    if not audio_bytes:
        return ""
    return base64.b64encode(audio_bytes).decode("ascii")


openai_api_key = os.getenv("OPENAI_API_KEY")
openrouter_api_key = OPENROUTER_API_KEY
_openai_client: Optional[OpenAI] = None
_openrouter_client: Optional[OpenAI] = None
_chat_model_openai: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
_chat_model_openrouter: str = OPENROUTER_MODEL
_neo4j_available: Optional[bool] = None


def get_openai_client() -> Optional[OpenAI]:
    global _openai_client, _chat_model_openai
    if _openai_client is not None:
        return _openai_client

    if openai_api_key:
        try:
            _openai_client = OpenAI(api_key=openai_api_key)
            _chat_model_openai = os.getenv("OPENAI_CHAT_MODEL", _chat_model_openai)
            logger.info(
                "OpenAI client initialised",
                extra={"model": _chat_model_openai},
            )
        except Exception as exc:
            logger.error("OpenAI client initialization error", extra={"error": str(exc)})
            _openai_client = None
    return _openai_client


def get_openrouter_client() -> Optional[OpenAI]:
    global _openrouter_client, _chat_model_openrouter
    if _openrouter_client is not None:
        return _openrouter_client

    if openrouter_api_key:
        try:
            _openrouter_client = OpenAI(
                api_key=openrouter_api_key,
                base_url=OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": OPENROUTER_SITE_URL,
                    "X-Title": OPENROUTER_APP_NAME,
                },
            )
            _chat_model_openrouter = OPENROUTER_MODEL
            logger.info(
                "OpenRouter client initialised",
                extra={"model": _chat_model_openrouter, "base_url": OPENROUTER_BASE_URL},
            )
        except Exception as exc:
            logger.error("OpenRouter client initialization error", extra={"error": str(exc)})
            _openrouter_client = None
    return _openrouter_client


def ensure_neo4j() -> bool:
    global _neo4j_available
    if _neo4j_available is None:
        try:
            _neo4j_available = neo4j_client.connect()
            if not _neo4j_available:
                logger.warning("Neo4j connection unavailable, falling back to in-memory graph")
        except Exception as exc:
            logger.error("Neo4j connection error", extra={"error": str(exc)})
            _neo4j_available = False
    return bool(_neo4j_available)


def build_personalization_notes(profile: Profile) -> List[str]:
    notes: List[str] = []

    if profile.age is not None:
        if profile.age < 2:
            notes.append(
                "User is an infant (<2 years). Avoid medication dosing advice and urge immediate pediatric review if symptoms worsen."
            )
        elif profile.age < 12:
            notes.append(
                "User is a child (<12 years). Provide caregiver-friendly guidance and highlight when to see a pediatrician."
            )
        elif profile.age >= 65:
            notes.append(
                "User is an older adult (65+). Emphasise monitoring chronic conditions and the risks of medication interactions."
            )

    if profile.pregnancy:
        notes.append(
            "User is currently pregnant. Avoid contraindicated medicines and recommend contacting the obstetric team for concerning symptoms."
        )

    return notes


def graph_get_red_flags(symptoms: List[str]) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_red_flags(symptoms)
        except Exception as exc:
            logger.error("Neo4j red flag query failed", extra={"error": str(exc)})
    return graph_fallback.get_red_flags(symptoms)


def graph_get_contraindications(user_conditions: List[str]) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_contraindications(user_conditions)
        except Exception as exc:
            logger.error("Neo4j contraindications query failed", extra={"error": str(exc)})
    return graph_fallback.get_contraindications(user_conditions)


def graph_get_providers(city: str) -> List[Dict[str, Any]]:
    if ensure_neo4j():
        try:
            return neo4j_get_providers_in_city(city)
        except Exception as exc:
            logger.error("Neo4j provider query failed", extra={"error": str(exc), "city": city})
    return graph_fallback.get_providers_in_city(city)


def graph_get_safe_actions(user_conditions: List[str]) -> List[Dict[str, Any]]:
    if not user_conditions:
        return []
    
    if ensure_neo4j():
        try:
            return neo4j_get_safe_actions()
        except Exception as exc:
            logger.error("Neo4j safe actions query failed", extra={"error": str(exc)})
    return graph_fallback.get_safe_actions(user_conditions)


def build_fact_blocks(facts: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Prepare fact summaries for LLM context and for direct display.
    """
    if not facts:
        return "", ""

    llm_lines: List[str] = []
    display_lines: List[str] = []

    for fact in facts:
        f_type = fact.get("type")
        data = fact.get("data", [])

        if f_type == "contraindications":
            for entry in data:
                condition = entry.get("condition")
                avoids = ", ".join(entry.get("avoid", []))
                llm_lines.append(f"- Contraindications for {condition}: avoid {avoids}")
                display_lines.append(f"{condition}: avoid {avoids}")
        elif f_type == "safe_actions":
            for entry in data:
                condition = entry.get("condition")
                actions = ", ".join(entry.get("actions", []))
                llm_lines.append(f"- Safe actions for {condition}: {actions}")
                display_lines.append(f"{condition}: {actions}")
        elif f_type == "mental_health_crisis":
            matched = ", ".join(data.get("matched", []))
            actions = "; ".join(data.get("actions", []))
            llm_lines.append(f"- Mental health crisis detected (phrases: {matched}). First aid: {actions}")
            display_lines.append(f"Mental health crisis phrases ({matched}) → {actions}")
        elif f_type == "pregnancy_alert":
            matched = ", ".join(data.get("matched", []))
            guidance = "; ".join(data.get("guidance", []))
            llm_lines.append(f"- Pregnancy alert indicators ({matched}). Guidance: {guidance}")
            display_lines.append(f"Pregnancy alert ({matched}) → {guidance}")
        elif f_type == "providers":
            providers = "; ".join(
                f"{item.get('provider')} ({item.get('mode', 'care')})"
                for item in data
            )
            llm_lines.append(f"- Local providers: {providers}")
            display_lines.append(f"Providers → {providers}")
        elif f_type == "red_flags":
            for entry in data:
                symptom = entry.get("symptom")
                conditions = ", ".join(entry.get("conditions", []))
                llm_lines.append(f"- Red flag: {symptom} → {conditions}")
                display_lines.append(f"{symptom} → {conditions}")
        elif f_type == "personalization":
            for note in data:
                llm_lines.append(f"- Personalization note: {note}")
                display_lines.append(note)

    llm_summary = "\n".join(llm_lines)
    display_summary = "\n".join(display_lines)
    return llm_summary, display_summary


def localize_fact_guidance(
    facts: List[Dict[str, Any]],
    lang: str,
    response_style: str = "native",
) -> List[Dict[str, Any]]:
    if lang == "en":
        return facts

    localized = copy.deepcopy(facts)
    for fact in localized:
        if fact.get("type") == "mental_health_crisis":
            actions = fact.get("data", {}).get("actions", [])
            fact["data"]["actions"] = localize_list(actions, lang, response_style=response_style)
        elif fact.get("type") == "pregnancy_alert":
            guidance = fact.get("data", {}).get("guidance", [])
            fact["data"]["guidance"] = localize_list(guidance, lang, response_style=response_style)
    return localized


def generate_answer(
    *,
    context: str,
    query_en: str,
    llm_language_label: str,
    original_query: str,
    facts: List[Dict[str, Any]],
    citations: List[Dict[str, Any]],
) -> Tuple[str, Dict[str, Any]]:
    """Generate answer using OpenAI or fallback"""
    fact_summary, _ = build_fact_blocks(facts)

    citations_section = ""
    if citations:
        lines = []
        for idx, cite in enumerate(citations, start=1):
            source = cite.get("source", "unknown")
            topic = cite.get("topic")
            cite_id = cite.get("id")
            label = f"{source}" if not topic else f"{topic} ({source})"
            lines.append(f"[{idx}] {label} — {cite_id}")
        citations_section = "\n".join(lines)
    
    system_prompt = """You are a helpful health assistant. Provide clear, accurate health information based on the context provided.

IMPORTANT GUIDELINES:
- You are NOT a doctor and cannot diagnose
- Provide general health information only
- Always include a disclaimer about seeking professional medical care
- Be empathetic and supportive
- Keep answers concise (3-4 short paragraphs) plus a short source list
- Structure answers as:
  1. What the symptoms might indicate (non-diagnostic)
  2. Safe self-care guidance
  3. When to escalate to a healthcare professional
  4. Mandatory disclaimer
- Integrate database facts when helpful (contraindications, safe actions, providers, alerts)
- If facts indicate emergencies or crises, emphasise them clearly
- Respond only in the requested language (no code-switching)
- Use only the supplied context. If the context does not contain sufficient information, state: "I don't have enough information from my sources."
- End with a 'Sources:' section referencing the provided citations by number."""

    sources_blocks: List[str] = []
    if context.strip():
        sources_blocks.append(context.strip())
    if fact_summary:
        sources_blocks.append(f"Structured facts:\n{fact_summary}")
    if citations_section:
        sources_blocks.append(f"Citations metadata:\n{citations_section}")
    sources_payload = "\n\n".join(sources_blocks) if sources_blocks else "None provided."

    user_prompt = (
        f"sources :\n{sources_payload}\n\n"
        "I want you to strictly answer based on the sources provided. "
        "Do not rely on outside knowledge. If the sources do not contain sufficient information, "
        'reply with: "I don\'t have enough information from my sources."\n\n'
        f"user prompt (english) : {query_en}\n"
        f"user prompt (original) : {original_query}\n\n"
        f"Language for response: {llm_language_label}\n"
        f"Respond exclusively in {llm_language_label} following the required structure and cite the supplied sources by number."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    providers_to_try: List[Tuple[str, Optional[OpenAI], str]] = [
        ("openai", get_openai_client(), _chat_model_openai),
        ("openrouter", get_openrouter_client(), _chat_model_openrouter),
    ]

    last_error: Optional[str] = None

    for provider, client, model in providers_to_try:
        if not client:
            continue
        try:
            kwargs: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
            }
            if provider == "openrouter":
                kwargs["extra_headers"] = OPENROUTER_EXTRA_HEADERS
                kwargs["extra_body"] = {}

            response = client.chat.completions.create(**kwargs)
            if provider == "openrouter":
                logger.info("Response generated via OpenRouter", extra={"model": model})
            return response.choices[0].message.content, {
                "provider": provider,
                "model": model,
            }
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            logger.warning(
                "Chat completion attempt failed",
                extra={"provider": provider, "model": model, "status_code": status_code, "error": str(exc)},
            )
            last_error = str(exc)

    if last_error:
        logger.error("All chat providers failed", extra={"error": last_error})
    else:
        logger.error("No chat providers available for completion")

    return FALLBACK_MESSAGE_EN, {
        "provider": None,
        "model": None,
        "fallback": True,
        "reason": last_error or "no_available_client",
    }


@app.get("/health")
async def health_check():
    return {
        "ok": True,
        "openai_configured": get_openai_client() is not None,
        "openrouter_configured": get_openrouter_client() is not None,
            "services": {
            "rag": True,
            "graph": ensure_neo4j(),
            "graph_fallback": True,
            "safety": True,
            "database": db_client.is_connected()
        }
    }


@app.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    lang: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """
    Convert speech to text using OpenAI Whisper
    Requires authentication
    """
    if file.content_type and not file.content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Unsupported media type. Please upload an audio file.")
    
    try:
        audio_bytes = await file.read()
        transcript = transcribe_audio_bytes(audio_bytes, language_hint=lang)
        return {"text": transcript}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Speech-to-text processing failed")
        raise HTTPException(status_code=502, detail=f"STT error: {str(exc)}") from exc


def _enhance_search_query_with_context(current_query: str, conversation_history: Optional[List[Dict[str, str]]]) -> str:
    """
    Enhance search query using conversation history for better RAG retrieval
    
    Args:
        current_query: Current user question
        conversation_history: Previous conversation messages
        
    Returns:
        Enhanced search query
    """
    if not conversation_history or len(conversation_history) == 0:
        return current_query
    
    # Check if current query is a follow-up (short, uses pronouns/references)
    follow_up_indicators = ["this", "that", "it", "these", "those", "what does", "how long", "when should", "why did"]
    is_follow_up = any(indicator in current_query.lower() for indicator in follow_up_indicators) or len(current_query.split()) < 5
    
    if not is_follow_up:
        return current_query
    
    # Extract key terms from previous messages
    key_terms = []
    for msg in conversation_history[-4:]:  # Look at last 4 messages
        content = msg.get("content", "")
        if content:
            # Extract important words (nouns, medical terms)
            words = content.lower().split()
            # Filter for meaningful words (length > 4, not common words)
            meaningful = [
                w for w in words 
                if len(w) > 4 and w not in ["what", "where", "when", "should", "could", "would", "about", "there", "their", "these", "those"]
            ]
            key_terms.extend(meaningful[:5])  # Take top 5 from each message
    
    # Combine current query with key terms from conversation
    if key_terms:
        # Remove duplicates and limit
        unique_terms = list(dict.fromkeys(key_terms))[:5]  # Preserve order, limit to 5
        enhanced_query = f"{current_query} {' '.join(unique_terms)}"
        logger.debug(f"Enhanced search query: {enhanced_query} (original: {current_query})")
        return enhanced_query
    
    return current_query


def _format_conversation_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Format database messages into OpenAI message format
    
    Args:
        messages: List of message dicts from database
        
    Returns:
        List of formatted messages for OpenAI API (with roles: "user" or "assistant")
    """
    formatted = []
    for msg in messages:
        role = msg.get("role")  # "user" or "assistant" from database
        
        # Get content based on role
        if role == "user":
            # For user messages, use message_text
            content = msg.get("message_text") or msg.get("text") or ""
        elif role == "assistant":
            # For assistant messages, use answer if available, otherwise message_text
            content = msg.get("answer") or msg.get("message_text") or msg.get("text") or ""
        else:
            # Skip unknown roles
            continue
        
        # Only add if we have valid role and content
        if role in ("user", "assistant") and content:
            formatted.append({
                "role": role,
                "content": content
            })
    
    return formatted


async def _get_conversation_history(session_id: Optional[str]) -> List[Dict[str, str]]:
    """
    Retrieve conversation history for a session
    
    Args:
        session_id: Session ID to retrieve history for
        
    Returns:
        List of formatted messages for OpenAI API
    """
    if not session_id or not db_client.is_connected():
        return []
    
    try:
        # Retrieve previous messages (excluding the current one being processed)
        messages = await db_service.get_session_messages(session_id, limit=20)
        
        if not messages:
            return []
        
        # Format messages for OpenAI API
        return _format_conversation_history(messages)
    except Exception as e:
        logger.warning(f"Failed to retrieve conversation history: {e}", exc_info=True)
        return []


def process_chat_request(
    request: ChatRequest, 
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Tuple[ChatResponse, str, Dict[str, float]]:
    timings: Dict[str, float] = {}
    total_start = time.perf_counter()

    text = request.text
    profile: Profile = request.profile
    personalization_notes = build_personalization_notes(profile)
    
    # Set default response_style if not provided in request
    response_style = getattr(request, "response_style", "native")
    
    # ============================================================
    # STEP 1: GPT-4o-mini → Detect Language + Translate to English
    # ============================================================
    detection_start = time.perf_counter()
    openai_client = get_openai_client()
    model = _chat_model_openai
    
    # Import pipeline functions at the top to ensure they're available
    from .pipeline_functions import detect_language_only, translate_to_english
    
    # First check for romanized text (Tanglish, Hinglish, etc.) - fast heuristic
    detected_lang = None
    romanized_lang = detect_romanized_language(text)
    if romanized_lang:
        detected_lang = romanized_lang
        logger.info(f"Detected romanized language: {detected_lang} for text: {text[:50]}...")
    
    # If not romanized, use GPT-4o-mini for language detection
    if not detected_lang:
        if openai_client and model:
            detected_lang = detect_language_only(
                client=openai_client,
                model=model,
                user_text=text
            )
            logger.debug(f"GPT-4o-mini detected language: {detected_lang}")
        else:
            # Fallback to old method if OpenAI client not available
            logger.warning("OpenAI client not available, using fallback language detection")
            detected_lang = detect_language(text) if text else DEFAULT_LANG
            detected_lang = detected_lang if detected_lang in SUPPORTED_LANG_CODES else DEFAULT_LANG
    
    # Use requested language if provided, otherwise use detected
    requested_lang_raw = request.lang if request.lang in SUPPORTED_LANG_CODES else None
    target_lang = requested_lang_raw or detected_lang or DEFAULT_LANG
    
    # Log final detected language (for debugging)
    logger.info(f"Language detection complete - detected_lang: {detected_lang}, target_lang: {target_lang}, will translate back to: {detected_lang}")
    
    # Translate to English using GPT-4o-mini (SKIP if English detected)
    if detected_lang == "en":
        # Skip translation entirely if English detected - optimize pipeline
        processed_text = text
        logger.debug("English detected - skipping translation to English step")
    else:
        # Translate to English only if not English
        if openai_client and model:
            processed_text = translate_to_english(
                client=openai_client,
                model=model,
                user_text=text,
                source_language=detected_lang
            )
        else:
            # Fallback to old method
            processed_text = translate_text(text, target_lang="en", src_lang=detected_lang)
    
    timings["language_detection"] = time.perf_counter() - detection_start
    timings["translation_to_english"] = 0.0 if detected_lang == "en" else (time.perf_counter() - detection_start - timings.get("language_detection", 0))
    
    debug_info: Dict[str, Any] = {
        "input_text": text,
        "detected_language": detected_lang,
        "target_language": target_lang,
        "processed_text_en": processed_text,
        "translation_skipped": (detected_lang == "en"),
        "pipeline": "optimized_multilingual_pipeline",
    }

    safety_start = time.perf_counter()
    safety_result = detect_red_flags(processed_text, "en")
    mental_health_en = detect_mental_health_crisis(processed_text, "en")
    pregnancy_alert_en = detect_pregnancy_emergency(processed_text)
    timings["safety_analysis"] = time.perf_counter() - safety_start

    # Translate mental health and pregnancy alerts if needed (skip if English detected)
    # Use detected_lang (not target_lang) to respond in the language user typed in
    mental_health_display = mental_health_en
    if detected_lang != "en" and mental_health_en["first_aid"] and openai_client and model:
        # Translate first aid steps
        translated_first_aid = []
        for step in mental_health_en["first_aid"]:
            translated = translate_to_user_language(
                client=openai_client,
                model=model,
                english_text=step,
                target_language=detected_lang,
            )
            translated_first_aid.append(translated)
        mental_health_display = {
            **mental_health_en,
            "first_aid": translated_first_aid,
        }

    pregnancy_guidance_display = PREGNANCY_ALERT_GUIDANCE_EN
    if detected_lang != "en" and openai_client and model:
        pregnancy_guidance_display = translate_to_user_language(
            client=openai_client,
            model=model,
            english_text="\n".join(PREGNANCY_ALERT_GUIDANCE_EN),
            target_language=detected_lang,
        ).split("\n")
    pregnancy_alert_display = {
        **pregnancy_alert_en,
        "guidance": pregnancy_guidance_display,
    }

    # ============================================================
    # STEP 3: Neo4j (Knowledge graph fallback)
    # ============================================================
    use_graph = is_graph_intent(processed_text)

    facts_en: List[Dict[str, Any]] = []
    citations: List[Dict[str, Any]] = []
    answer = ""
    route = "vector"
    rag_results: List[Dict[str, Any]] = []
    
    if safety_result["red_flag"]:
        symptoms = extract_symptoms(processed_text)
        red_flag_results = graph_get_red_flags(symptoms)
        if red_flag_results:
            facts_en.append({"type": "red_flags", "data": red_flag_results})

    if mental_health_en["crisis"]:
        facts_en.append(
            {
                "type": "mental_health_crisis",
                "data": {
                    "matched": mental_health_en["matched"],
                    "actions": mental_health_en["first_aid"],
                },
            }
        )

    if pregnancy_alert_en["concern"]:
        facts_en.append(
            {
                "type": "pregnancy_alert",
                "data": {
                    "matched": pregnancy_alert_en["matched"],
                    "guidance": PREGNANCY_ALERT_GUIDANCE_EN,
                },
            }
        )

    if use_graph:
        route = "graph"
        
        user_conditions: List[str] = []
        # Add conditions from boolean fields (for backward compatibility)
        if profile.diabetes:
            user_conditions.append("Diabetes")
        if profile.hypertension:
            user_conditions.append("Hypertension")
        if profile.pregnancy:
            user_conditions.append("Pregnancy")
        
        # Add conditions from medical_conditions array
        if hasattr(profile, 'medical_conditions') and profile.medical_conditions:
            for condition in profile.medical_conditions:
                # Capitalize first letter for consistency
                condition_label = condition.capitalize().replace("_", " ")
                if condition_label not in user_conditions:
                    user_conditions.append(condition_label)

        condition_keywords = {
            "diabetes": "Diabetes",
            "hypertension": "Hypertension",
            "pregnancy": "Pregnancy",
            "pregnant": "Pregnancy",
            "asthma": "Asthma",
            "heart disease": "Heart disease",
            "kidney disease": "Kidney disease",
            "liver disease": "Liver disease",
            "epilepsy": "Epilepsy",
        }
        processed_lower = processed_text.lower()
        for keyword, label in condition_keywords.items():
            if keyword in processed_lower and label not in user_conditions:
                user_conditions.append(label)
        
        if user_conditions:
            contras = graph_get_contraindications(user_conditions)
            if contras:
                condition_avoid_map: Dict[str, List[str]] = {}
                for entry in contras:
                    avoid_item = entry.get("avoid")
                    for cond in entry.get("because", []):
                        if cond in user_conditions and avoid_item:
                            condition_avoid_map.setdefault(cond, []).append(avoid_item)

                if condition_avoid_map:
                    facts_en.append(
                        {
                    "type": "contraindications",
                            "data": [
                                {
                                    "condition": cond,
                                    "avoid": sorted(set(items)),
                                }
                                for cond, items in condition_avoid_map.items()
                            ],
                        }
                    )

            safe_actions_map: Dict[str, List[str]] = {}
            for condition in user_conditions:
                safe_entries = graph_get_safe_actions([condition])
                actions = sorted(
                    {
                        entry.get("safeAction")
                        for entry in safe_entries
                        if entry.get("safeAction")
                    }
                )
                if actions:
                    safe_actions_map[condition] = actions

            if safe_actions_map:
                facts_en.append(
                    {
                        "type": "safe_actions",
                        "data": [
                            {"condition": cond, "actions": actions}
                            for cond, actions in safe_actions_map.items()
                        ],
                    }
                )

        city = profile.city or extract_city(processed_text)
        if city:
            providers = graph_get_providers(city)
            if providers:
                facts_en.append({"type": "providers", "data": providers})
        
        # ============================================================
        # STEP 2: ChromaDB (Semantic search)
        # ============================================================
        rag_start = time.perf_counter()
        # Enhance query with conversation history for better context
        enhanced_query = _enhance_search_query_with_context(processed_text, conversation_history)
        rag_results = retrieve(enhanced_query, k=3)
        timings["retrieval"] = time.perf_counter() - rag_start
        context = "\n\n".join([r["chunk"] for r in rag_results])
        citations = [
            {"source": r["source"], "id": r["id"], "topic": r.get("topic")}
            for r in rag_results
        ]
        debug_info["rag_context_snippets"] = [r["chunk"][:200] for r in rag_results]
        debug_info["citations"] = citations
        
        if facts_en:
            fact_summary = "\n\nRelevant facts from database:\n"
            for fact_group in facts_en:
                if fact_group["type"] == "red_flags":
                    fact_summary += "⚠️ Red flag conditions detected\n"
                elif fact_group["type"] == "contraindications":
                    avoid_phrases = []
                    for entry in fact_group["data"]:
                        avoid_items = ", ".join(entry["avoid"])
                        avoid_phrases.append(f"{entry['condition']}: {avoid_items}")
                    if avoid_phrases:
                        fact_summary += f"⛔ Things to avoid — {'; '.join(avoid_phrases)}\n"
                elif fact_group["type"] == "providers":
                    fact_summary += f"🏥 {len(fact_group['data'])} healthcare providers found\n"
            context += fact_summary

        if personalization_notes:
            context += "\n\nPersonalization notes:\n" + "\n".join(
                f"- {note}" for note in personalization_notes
            )
            if not any(f.get("type") == "personalization" for f in facts_en):
                facts_en.append({"type": "personalization", "data": personalization_notes})

        # ============================================================
        # STEP 4: GPT-4o-mini → Final reasoning + Generate answer in English
        # ============================================================
        generation_start = time.perf_counter()
        
        if openai_client and model:
            answer_en = generate_final_answer(
                client=openai_client,
                model=model,
                user_question=processed_text,
                rag_context=context,
                facts=facts_en,
                profile=profile,
                conversation_history=conversation_history,
            )
            provider_meta = {"provider": "openai", "model": model, "fallback": False}
        else:
            # Fallback to old method
            answer_en, provider_meta = generate_answer(
                context=context,
                query_en=processed_text,
                llm_language_label="English",
                original_query=text,
                facts=facts_en,
                citations=citations,
            )
        
        # ============================================================
        # STEP 5: GPT-4o-mini → Translate answer back to user's language (native script)
        # SKIP if English detected
        # ============================================================
        translation_start = time.perf_counter()
        
        # Skip translation back if English was detected (optimization)
        # Use detected_lang (not target_lang) to respond in the language user typed in
        if detected_lang == "en":
            answer = answer_en
            logger.debug("English detected - skipping translation back to user's language step")
        elif detected_lang != "en" and openai_client and model:
            # Translate to user's detected language (always native script, not romanized)
            logger.info(f"Translating answer back to {detected_lang} (native script)")
            answer = translate_to_user_language(
                client=openai_client,
                model=model,
                english_text=answer_en,
                target_language=detected_lang,
            )
            logger.debug(f"Translation complete - answer length: {len(answer)} characters")
        else:
            answer = answer_en
            logger.warning(f"Translation skipped - detected_lang: {detected_lang}, openai_client: {bool(openai_client)}, model: {model}")
        
        timings["answer_generation"] = time.perf_counter() - generation_start
        timings["answer_translation"] = time.perf_counter() - translation_start
        
        debug_info["llm"] = provider_meta
        debug_info["answer_en"] = answer_en
        debug_info["answer_localized"] = answer
        
    else:
        # ============================================================
        # STEP 2: ChromaDB (Semantic search)
        # ============================================================
        rag_start = time.perf_counter()
        # Enhance query with conversation history for better context
        enhanced_query = _enhance_search_query_with_context(processed_text, conversation_history)
        rag_results = retrieve(enhanced_query, k=4)
        timings["retrieval"] = time.perf_counter() - rag_start
        debug_info["rag_context_snippets"] = [r["chunk"][:200] for r in rag_results] if rag_results else []
        
        if not rag_results:
            answer_en = (
                "I don't have enough information from my sources. "
                "For health concerns, please consult a healthcare professional."
            )
            localized_answer = localize_text(
                answer_en,
                target_lang=target_lang,
                response_style=response_style,
            )
            provider_meta = {
                "provider": None,
                "model": None,
                "fallback": True,
                "reason": "insufficient_context",
            }
            answer = localized_answer
            debug_info["llm"] = provider_meta
            debug_info["answer_en"] = answer_en
            debug_info["answer_localized"] = localized_answer
        else:
            context = "\n\n".join([r["chunk"] for r in rag_results])
            citations = [
                {"source": r["source"], "id": r["id"], "topic": r.get("topic")}
                for r in rag_results
            ]
            debug_info["citations"] = citations

            personalized_conditions: List[str] = []
            if profile.diabetes:
                personalized_conditions.append("diabetes")
            if profile.hypertension:
                personalized_conditions.append("hypertension")
            if profile.pregnancy:
                personalized_conditions.append("pregnancy")
            # Add conditions from medical_conditions array
            if hasattr(profile, 'medical_conditions') and profile.medical_conditions:
                personalized_conditions.extend(profile.medical_conditions)
            if personalized_conditions:
                context += (
                    "\n\nNote: User has "
                    + " and ".join(personalized_conditions)
                    + ". Provide relevant precautions."
                )

            if personalization_notes:
                context += "\n\nPersonalization notes:\n" + "\n".join(
                    f"- {note}" for note in personalization_notes
                )
                facts_en.append({"type": "personalization", "data": personalization_notes})

            # ============================================================
            # STEP 4: GPT-4o-mini → Final reasoning + Generate answer in English
            # ============================================================
            generation_start = time.perf_counter()
            
            if openai_client and model:
                answer_en = generate_final_answer(
                    client=openai_client,
                    model=model,
                    user_question=processed_text,
                    rag_context=context,
                    facts=facts_en,
                    profile=profile,
                )
                provider_meta = {"provider": "openai", "model": model, "fallback": False}
            else:
                # Fallback to old method
                answer_en, provider_meta = generate_answer(
                    context=context,
                    query_en=processed_text,
                    llm_language_label="English",
                    original_query=text,
                    facts=facts_en,
                    citations=citations,
                )
            
            # ============================================================
            # STEP 5: GPT-4o-mini → Translate answer back to user's language (native script)
            # SKIP if English detected
            # ============================================================
            translation_start = time.perf_counter()
            
            # Skip translation back if English was detected (optimization)
            # Use detected_lang (not target_lang) to respond in the language user typed in
            if detected_lang == "en":
                answer = answer_en
                logger.debug("English detected - skipping translation back to user's language step")
            elif detected_lang != "en" and openai_client and model:
                # Translate to user's detected language (always native script, not romanized)
                logger.info(f"Translating answer back to {detected_lang} (native script)")
                answer = translate_to_user_language(
                    client=openai_client,
                    model=model,
                    english_text=answer_en,
                    target_language=detected_lang,
                )
                logger.debug(f"Translation complete - answer length: {len(answer)} characters")
            else:
                answer = answer_en
                logger.warning(f"Translation skipped - detected_lang: {detected_lang}, openai_client: {bool(openai_client)}, model: {model}")
            
            timings["answer_generation"] = time.perf_counter() - generation_start
            timings["answer_translation"] = time.perf_counter() - translation_start
            
            debug_info["llm"] = provider_meta
            debug_info["answer_en"] = answer_en
            debug_info["answer_localized"] = answer

    if not safety_result["red_flag"]:
        # Translate disclaimer to user's language (skip if English detected)
        # Use detected_lang (not target_lang) to respond in the language user typed in
        disclaimer_en = DISCLAIMER_EN
        if detected_lang == "en":
            disclaimer = disclaimer_en
        elif detected_lang != "en" and openai_client and model:
            disclaimer = translate_to_user_language(
                client=openai_client,
                model=model,
                english_text=disclaimer_en,
                target_language=detected_lang,
            )
        else:
            disclaimer = disclaimer_en
        answer += "\n\n" + disclaimer

    # Translate facts if needed (simplified - keeping facts in English for now)
    # Can be enhanced later to translate facts
    facts_response = facts_en

    safety_payload = {
        **safety_result,
        "mental_health": mental_health_display,
        "pregnancy": pregnancy_alert_display,
    }

    debug_info["response_preview"] = answer[:200]
    debug_info.setdefault("citations", citations)
    debug_info.setdefault("rag_context_snippets", [])

    response = ChatResponse(
        answer=answer,
        route=route,
        facts=facts_response,
        citations=citations,
        safety=safety_payload,
        metadata={},
    )
    logger.debug(
        "Chat response composed",
        extra={
            "route": route,
            "facts": len(response.facts),
            "target_lang": target_lang,
            "pipeline": "new_multilingual",
        },
    )
    timings["total"] = time.perf_counter() - total_start

    metadata_payload: Dict[str, Any] = {
        "timings": timings,
        "target_language": target_lang,
        "detected_language": detected_lang,
        "pipeline": "new_multilingual",
    }
    if request.debug:
        metadata_payload["debug"] = debug_info
        debug_info["response_length"] = len(answer)
        debug_info["rag_context_count"] = len(debug_info.get("rag_context_snippets") or [])
    response.metadata = metadata_payload

    return response, target_lang, timings


async def save_chat_messages_background(
    session_id: str,
    customer_id: str,
    user_message: str,
    user_lang: str,
    assistant_response: ChatResponse,
    target_lang: str,
) -> None:
    """
    Background task to save both user and assistant messages to database.
    This runs after the response is sent to the user for faster response times.
    """
    if not db_client.is_connected() or not session_id:
        return
    
    try:
        # Save user message
        await db_service.save_chat_message(
            session_id=session_id,
            role="user",
            message_text=user_message,
            language=user_lang,
        )
        
        # Convert safety to dict
        safety_dict = assistant_response.safety.model_dump() if hasattr(assistant_response.safety, 'model_dump') else dict(assistant_response.safety)
        
        # Save assistant response
        await db_service.save_chat_message(
            session_id=session_id,
            role="assistant",
            message_text=user_message,  # User's original question
            language=target_lang,
            answer=assistant_response.answer,
            route=assistant_response.route,
            safety_data=safety_dict,
            facts=assistant_response.facts,
            citations=assistant_response.citations,
            metadata=assistant_response.metadata,
        )
        
        # Invalidate cache for customer sessions and session messages after saving
        try:
            if customer_id:
                # Invalidate customer sessions cache (all limits)
                for limit_val in [10, 50, 100, 200, 500, 1000]:
                    cache_key = f"sessions:{customer_id}:{limit_val}"
                    await cache_service.delete(cache_key)
                    logger.debug(f"Invalidated cache: {cache_key}")
            
            # Invalidate session messages cache (all limits)
            if session_id:
                for limit_val in [10, 50, 100, 200, 500, 1000]:
                    cache_key = f"session_messages:{session_id}:{limit_val}"
                    await cache_service.delete(cache_key)
                    logger.debug(f"Invalidated cache: {cache_key}")
                # Invalidate full session cache
                await cache_service.delete(f"session_full:{session_id}")
                logger.debug(f"Invalidated cache: session_full:{session_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
    except Exception as e:
        logger.warning(f"Failed to save chat messages in background: {e}", exc_info=True)


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_auth)
):
    """
    Main chat endpoint with routing, safety detection, and RAG
    Saves customer data and chat messages to database
    Requires authentication
    """
    logger.info(
        "Received chat request",
        extra={
            "lang": request.lang,
            "profile": request.profile.model_dump(exclude_none=True),
            "customer_id": request.customer_id,
            "session_id": request.session_id,
            "user_id": user.get("user_id"),
        },
    )
    try:
        # Use authenticated user's ID
        customer_id = user.get("user_id") or request.customer_id
        session_id = request.session_id
        
        # Prepare session in background (non-blocking, but needed for message saving)
        if db_client.is_connected():
            try:
                # Update authenticated user's profile if needed
                profile_data = request.profile.model_dump(exclude_none=True)
                
                # Get customer (should exist since user is authenticated)
                customer = await db_service.get_customer(customer_id)
                
                if not customer:
                    logger.error(f"Customer not found: {customer_id}")
                    raise HTTPException(status_code=404, detail="Customer not found")
                
                # Update profile if data provided
                if profile_data:
                    customer = await db_service.update_customer_profile(customer_id, profile_data)
                
                # Handle both dict and object responses
                if isinstance(customer, dict):
                    customer_id = customer.get("id") or customer_id
                else:
                    customer_id = getattr(customer, "id", customer_id)
                
                # Get or create session (needed for session_id)
                chat_session = await db_service.get_or_create_session(
                    customer_id=customer_id,
                    language=request.lang,
                    session_id=session_id
                )
                
                if chat_session:
                    session_id = chat_session["id"]
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to prepare customer/session data: {e}", exc_info=True)
        
        # Retrieve conversation history for context
        conversation_history = []
        if session_id and db_client.is_connected():
            try:
                conversation_history = await _get_conversation_history(session_id)
                if conversation_history:
                    logger.debug(f"Retrieved {len(conversation_history)} previous messages for context")
            except Exception as e:
                logger.warning(f"Failed to retrieve conversation history: {e}", exc_info=True)
        
        # Process chat request (no caching for chat responses)
        # This is the main work - generate AI response
        response, target_lang, timings = process_chat_request(request, conversation_history=conversation_history)
        
        # Add customer_id and session_id to response metadata
        if customer_id:
            response.metadata["customer_id"] = customer_id
        if session_id:
            response.metadata["session_id"] = session_id
        
        # Queue background task to save messages (non-blocking)
        # This allows the response to be returned immediately
        if db_client.is_connected() and session_id:
            background_tasks.add_task(
                save_chat_messages_background,
                session_id=session_id,
                customer_id=customer_id,
                user_message=request.text,
                user_lang=request.lang,
                assistant_response=response,
                target_lang=target_lang,
            )
        
        # Note: Chat responses are NOT cached - only dynamic content (sessions, messages) is cached
        
        logger.info(
            "Chat response ready",
            extra={
                "route": response.route,
                "request_lang": request.lang,
                "target_lang": target_lang,
                "facts": len(response.facts),
                "timings": timings,
                "customer_id": customer_id,
                "session_id": session_id,
            },
        )
        
        # Return response (no caching for chat responses)
        from fastapi.responses import JSONResponse
        response_data = response.model_dump()
        json_response = JSONResponse(content=response_data)
        
        return json_response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat processing failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process your request right now. Please try again in a moment.",
        ) from e


async def process_chat_request_stream(
    request: ChatRequest,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    session_id: Optional[str] = None,
    customer_id: Optional[str] = None
):
    """
    Process chat request and stream the response.
    This is a streaming version that yields chunks as they're generated.
    
    Args:
        request: Chat request
        conversation_history: Previous conversation messages for context
        session_id: Session ID for metadata
        customer_id: Customer ID for metadata
    """
    text = request.text
    profile: Profile = request.profile
    personalization_notes = build_personalization_notes(profile)
    
    # Set default response_style if not provided in request
    response_style = getattr(request, "response_style", "native")
    
    # Language detection and translation to English (same as regular endpoint)
    detection_start = time.perf_counter()
    openai_client = get_openai_client()
    model = _chat_model_openai
    
    from .pipeline_functions import detect_language_only, translate_to_english
    
    detected_lang = None
    romanized_lang = detect_romanized_language(text)
    if romanized_lang:
        detected_lang = romanized_lang
    
    if not detected_lang:
        if openai_client and model:
            detected_lang = detect_language_only(
                client=openai_client,
                model=model,
                user_text=text
            )
        else:
            detected_lang = detect_language(text) if text else DEFAULT_LANG
            detected_lang = detected_lang if detected_lang in SUPPORTED_LANG_CODES else DEFAULT_LANG
    
    requested_lang_raw = request.lang if request.lang in SUPPORTED_LANG_CODES else None
    target_lang = requested_lang_raw or detected_lang or DEFAULT_LANG
    
    # Translate to English if needed
    if detected_lang == "en":
        processed_text = text
    else:
        if openai_client and model:
            processed_text = translate_to_english(
                client=openai_client,
                model=model,
                user_text=text,
                source_language=detected_lang
            )
        else:
            processed_text = translate_text(text, target_lang="en", src_lang=detected_lang)
    
    # Safety analysis
    safety_result = detect_red_flags(processed_text, "en")
    mental_health_en = detect_mental_health_crisis(processed_text, "en")
    pregnancy_alert_en = detect_pregnancy_emergency(processed_text)
    
    # RAG retrieval - enhance query with conversation history for better context
    enhanced_query = _enhance_search_query_with_context(processed_text, conversation_history)
    rag_results = retrieve(enhanced_query, k=4)
    context = "\n\n".join([r["chunk"] for r in rag_results]) if rag_results else ""
    citations = [
        {"source": r["source"], "id": r["id"], "topic": r.get("topic")}
        for r in rag_results
    ]
    
    # Build facts
    facts_en: List[Dict[str, Any]] = []
    if safety_result["red_flag"]:
        symptoms = extract_symptoms(processed_text)
        red_flag_results = graph_get_red_flags(symptoms)
        if red_flag_results:
            facts_en.append({"type": "red_flags", "data": red_flag_results})
    
    if mental_health_en["crisis"]:
        facts_en.append({
            "type": "mental_health_crisis",
            "data": {
                "matched": mental_health_en["matched"],
                "actions": mental_health_en["first_aid"],
            },
        })
    
    if pregnancy_alert_en["concern"]:
        facts_en.append({
            "type": "pregnancy_alert",
            "data": {
                "matched": pregnancy_alert_en["matched"],
                "guidance": PREGNANCY_ALERT_GUIDANCE_EN,
            },
        })
    
    # Add personalization notes
    if personalization_notes:
        context += "\n\nPersonalization notes:\n" + "\n".join(
            f"- {note}" for note in personalization_notes
        )
        facts_en.append({"type": "personalization", "data": personalization_notes})
    
    # Stream the answer generation
    answer_en_chunks = []
    if openai_client and model:
        # Use context if available, otherwise use empty string
        rag_context = context if context else ""
        async for chunk in generate_final_answer_stream(
            client=openai_client,
            model=model,
            user_question=processed_text,
            rag_context=rag_context,
            facts=facts_en,
            profile=profile,
            conversation_history=conversation_history,
        ):
            answer_en_chunks.append(chunk)
            # Send chunk to client (as JSON for SSE)
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
    else:
        # Fallback: generate a simple response if no client/model available
        fallback_answer = build_fallback_answer(
            query_en=processed_text,
            rag_results=rag_results,
            facts=facts_en,
            citations=citations,
            target_lang="en",
            response_style="native",
        )
        # Stream the fallback answer character by character for consistency
        for char in fallback_answer:
            answer_en_chunks.append(char)
            yield f"data: {json.dumps({'type': 'chunk', 'content': char})}\n\n"
    
    # Combine all chunks
    answer_en = "".join(answer_en_chunks)
    
    # Translate if needed
    if detected_lang == "en":
        answer = answer_en
    elif detected_lang != "en" and openai_client and model:
        answer = translate_to_user_language(
            client=openai_client,
            model=model,
            english_text=answer_en,
            target_language=detected_lang,
        )
        # Send final translated answer
        yield f"data: {json.dumps({'type': 'translated', 'content': answer})}\n\n"
    else:
        answer = answer_en
    
    # Add disclaimer
    if not safety_result["red_flag"]:
        disclaimer_en = DISCLAIMER_EN
        if detected_lang == "en":
            disclaimer = disclaimer_en
        elif detected_lang != "en" and openai_client and model:
            disclaimer = translate_to_user_language(
                client=openai_client,
                model=model,
                english_text=disclaimer_en,
                target_language=detected_lang,
            )
        else:
            disclaimer = disclaimer_en
        answer += "\n\n" + disclaimer
    
    # Send completion message with full response metadata
    safety_payload = {
        **safety_result,
        "mental_health": mental_health_en,
        "pregnancy": pregnancy_alert_en,
    }
    
    completion_data = {
        "type": "done",
        "answer": answer,
        "route": "vector",
        "facts": facts_en,
        "citations": citations,
        "safety": safety_payload,
        "metadata": {
            "target_language": target_lang,
            "detected_language": detected_lang,
        }
    }
    
    # Add session_id and customer_id to metadata if available
    if session_id:
        completion_data["metadata"]["session_id"] = session_id
    if customer_id:
        completion_data["metadata"]["customer_id"] = customer_id
    
    yield f"data: {json.dumps(completion_data)}\n\n"


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_auth)
):
    """
    Streaming chat endpoint - streams response as it's generated (typewriter effect)
    Uses Server-Sent Events (SSE) to stream chunks
    """
    logger.info(
        "Received streaming chat request",
        extra={
            "lang": request.lang,
            "user_id": user.get("user_id"),
        },
    )
    try:
        # Use authenticated user's ID
        customer_id = user.get("user_id") or request.customer_id
        session_id = request.session_id
        
        # Prepare session
        if db_client.is_connected():
            try:
                profile_data = request.profile.model_dump(exclude_none=True)
                customer = await db_service.get_customer(customer_id)
                
                if not customer:
                    logger.error(f"Customer not found: {customer_id}")
                    raise HTTPException(status_code=404, detail="Customer not found")
                
                if profile_data:
                    customer = await db_service.update_customer_profile(customer_id, profile_data)
                
                if isinstance(customer, dict):
                    customer_id = customer.get("id") or customer_id
                else:
                    customer_id = getattr(customer, "id", customer_id)
                
                chat_session = await db_service.get_or_create_session(
                    customer_id=customer_id,
                    language=request.lang,
                    session_id=session_id
                )
                
                if chat_session:
                    session_id = chat_session["id"]
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to prepare customer/session data: {e}", exc_info=True)
        
        # Retrieve conversation history for context
        conversation_history = []
        if session_id and db_client.is_connected():
            try:
                conversation_history = await _get_conversation_history(session_id)
                if conversation_history:
                    logger.debug(f"Retrieved {len(conversation_history)} previous messages for context")
            except Exception as e:
                logger.warning(f"Failed to retrieve conversation history: {e}", exc_info=True)
        
        # Stream the response
        async def generate():
            full_answer = ""
            async for chunk_data in process_chat_request_stream(
                request, 
                conversation_history=conversation_history,
                session_id=session_id,
                customer_id=customer_id
            ):
                yield chunk_data
                # Extract content from chunks to build full answer
                try:
                    if chunk_data.startswith("data: "):
                        data_str = chunk_data[6:]  # Remove "data: " prefix
                        data = json.loads(data_str)
                        if data.get("type") == "chunk":
                            full_answer += data.get("content", "")
                        elif data.get("type") == "done":
                            full_answer = data.get("answer", full_answer)
                except:
                    pass
            
            # Save messages in background after streaming completes
            if db_client.is_connected() and session_id and full_answer:
                try:
                    # Create a minimal ChatResponse for saving
                    from .models import Safety, MentalHealthSafety, PregnancySafety
                    safety_data = Safety(
                        red_flag=False,
                        mental_health=MentalHealthSafety(
                            crisis=False,
                            matched=[],
                            first_aid=[]
                        ),
                        pregnancy=PregnancySafety(
                            concern=False,
                            matched=[]
                        )
                    )
                    response_obj = ChatResponse(
                        answer=full_answer,
                        route="vector",
                        facts=[],
                        citations=[],
                        safety=safety_data,
                        metadata={}
                    )
                    
                    background_tasks.add_task(
                        save_chat_messages_background,
                        session_id=session_id,
                        customer_id=customer_id,
                        user_message=request.text,
                        user_lang=request.lang,
                        assistant_response=response_obj,
                        target_lang=request.lang,
                    )
                except Exception as e:
                    logger.warning(f"Failed to queue message save: {e}", exc_info=True)
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering in nginx
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Streaming chat processing failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process your request right now. Please try again in a moment.",
        ) from e


@app.get("/cache/stats")
async def get_cache_stats(
    user: dict = Depends(require_auth)
):
    """
    Get cache statistics (hits, misses, hit rate, etc.)
    Requires authentication
    """
    stats = cache_service.get_statistics()
    info = cache_service.get_cache_info()
    return {
        "statistics": stats,
        "info": info,
    }


@app.get("/cache/info")
async def get_cache_info_endpoint(
    user: dict = Depends(require_auth)
):
    """
    Get cache system information
    Requires authentication
    """
    return cache_service.get_cache_info()


@app.post("/cache/invalidate")
async def invalidate_cache_endpoint(
    pattern: Optional[str] = None,
    user: dict = Depends(require_auth)
):
    """
    Invalidate cache entries by pattern
    Requires authentication and admin role
    """
    # Only admins can invalidate cache
    user_role = user.get("role", "user")
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invalidate cache")
    
    if pattern:
        deleted = await cache_service.invalidate_cache(pattern=pattern)
    else:
        deleted = await cache_service.invalidate_all_cache()
    
    return {
        "deleted_keys": deleted,
        "pattern": pattern or "chat:response:*",
    }


@app.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    lang: Optional[str] = Form(None),
    profile: Optional[str] = Form(None),
    customer_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    user: dict = Depends(require_auth),
):
    """
    Voice-first endpoint: audio -> Whisper STT -> chat -> TTS audio response
    Saves customer data and chat messages to database (through ChatRequest)
    Requires authentication
    """
    if audio.content_type and not audio.content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Unsupported media type. Please upload an audio file.")

    try:
        audio_bytes = await audio.read()
        stt_start = time.perf_counter()
        transcript = transcribe_audio_bytes(audio_bytes, language_hint=lang)
        stt_duration = time.perf_counter() - stt_start

        profile_payload: Dict[str, Any] = {}
        if profile:
            try:
                profile_payload = json.loads(profile)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail=f"Invalid profile JSON: {exc}") from exc

        # Use authenticated user's ID
        authenticated_customer_id = user.get("user_id") or customer_id

        chat_request = ChatRequest(
            text=transcript,
            lang=lang or DEFAULT_LANG,
            profile=Profile(**profile_payload),
            customer_id=authenticated_customer_id,
            session_id=session_id,
        )

        # Prepare session (non-blocking, but needed for message saving)
        if db_client.is_connected():
            try:
                profile_data = chat_request.profile.model_dump(exclude_none=True)
                
                # Get customer (should exist since user is authenticated)
                customer = await db_service.get_customer(authenticated_customer_id)
                
                if not customer:
                    logger.error(f"Customer not found: {authenticated_customer_id}")
                    raise HTTPException(status_code=404, detail="Customer not found")
                
                # Update profile if data provided
                if profile_data:
                    customer = await db_service.update_customer_profile(authenticated_customer_id, profile_data)
                
                customer_id = customer["id"] if customer else authenticated_customer_id
                
                # Get or create session (needed for session_id)
                chat_session = await db_service.get_or_create_session(
                    customer_id=customer_id,
                    language=chat_request.lang,
                    session_id=session_id
                )
                
                if chat_session:
                    session_id = chat_session["id"]
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to prepare customer/session data in voice_chat: {e}", exc_info=True)

        # Retrieve conversation history for context
        conversation_history = []
        if session_id and db_client.is_connected():
            try:
                conversation_history = await _get_conversation_history(session_id)
                if conversation_history:
                    logger.debug(f"Retrieved {len(conversation_history)} previous messages for context")
            except Exception as e:
                logger.warning(f"Failed to retrieve conversation history: {e}", exc_info=True)

        # Process chat request - generate AI response
        chat_response, target_lang, chat_timings = process_chat_request(chat_request, conversation_history=conversation_history)

        # Queue background task to save messages (non-blocking)
        # This allows the response to be returned immediately
        if db_client.is_connected() and session_id:
            background_tasks.add_task(
                save_chat_messages_background,
                session_id=session_id,
                customer_id=customer_id,
                user_message=transcript,
                user_lang=chat_request.lang,
                assistant_response=chat_response,
                target_lang=target_lang,
            )

        tts_start = time.perf_counter()
        audio_bytes_out, tts_provider, audio_mime = synthesize_speech(chat_response.answer, target_lang)
        tts_duration = time.perf_counter() - tts_start

        metadata = {
            "timings": {
                **chat_timings,
                "stt": stt_duration,
                "tts": tts_duration,
            },
            "tts_provider": tts_provider,
            "audio_mime": audio_mime,
            "transcript_length": len(transcript),
            "audio_input_bytes": len(audio_bytes),
            "audio_output_bytes": len(audio_bytes_out),
        }
        
        # Add customer_id and session_id to metadata
        if customer_id:
            metadata["customer_id"] = customer_id
        if session_id:
            metadata["session_id"] = session_id

        return VoiceChatResponse(
            transcript=transcript,
            answer=chat_response.answer,
            audio_base64=encode_audio_base64(audio_bytes_out),
            route=chat_response.route,
            facts=chat_response.facts,
            citations=chat_response.citations,
            safety=chat_response.safety,
            metadata=metadata,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Voice chat processing failed")
        raise HTTPException(
            status_code=500,
            detail="Voice processing failed. Please try again later.",
        ) from exc


@app.get("/customer/{customer_id}")
async def get_customer(
    customer_id: str,
    user: dict = Depends(require_auth)
):
    """
    Get customer information
    Requires authentication
    Users can only view their own profile, admins can view any profile
    Cached in Redis for 5 minutes
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid
    try:
        customer_id = validate_uuid(customer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not db_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if user is accessing their own profile or is admin
    user_role = user.get("role", "user")
    user_id = user.get("user_id")
    
    if user_role != "admin" and user_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own profile"
        )
    
    # Try to get from Redis cache first
    cache_key = f"customer:{customer_id}"
    cached_customer = await cache_service.get(cache_key)
    if cached_customer is not None:
        logger.debug(f"Cache hit for customer: {customer_id}")
        return cached_customer
    
    customer = await db_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get session count
    sessions = await db_service.get_customer_sessions(customer_id, limit=1000)
    session_count = len(sessions)
    
    # Parse medical_conditions from JSONB if it exists
    medical_conditions = customer.get("medical_conditions")
    if isinstance(medical_conditions, str):
        import json
        try:
            medical_conditions = json.loads(medical_conditions)
        except:
            medical_conditions = []
    elif medical_conditions is None:
        medical_conditions = []
    
    result = {
        "id": customer["id"],
        "email": customer["email"],
        "createdAt": customer["created_at"].isoformat() if customer.get("created_at") else None,
        "updatedAt": customer["updated_at"].isoformat() if customer.get("updated_at") else None,
        "age": customer.get("age"),
        "sex": customer.get("sex"),
        "diabetes": customer.get("diabetes", False),
        "hypertension": customer.get("hypertension", False),
        "pregnancy": customer.get("pregnancy", False),
        "city": customer.get("city"),
        "medicalConditions": medical_conditions,
        "metadata": customer.get("metadata"),
        "sessionCount": session_count,
    }
    
    # Cache the result for 5 minutes (300 seconds)
    await cache_service.set(cache_key, result, ttl=300)
    
    return result


@app.get("/admin/users")
async def list_all_users(
    limit: int = 1000,
    user: dict = Depends(require_role(["admin"]))
):
    """
    List all users (Admin only)
    
    Returns a list of all users in the database with their details
    """
    if not db_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        from .auth.validation import validate_query_limit
        limit = validate_query_limit(limit)
        
        customers = await db_service.get_all_customers(limit=limit)
        
        # Format the response
        users_list = []
        for customer in customers:
            # Parse medical_conditions from JSONB if it exists
            medical_conditions = customer.get("medical_conditions")
            if isinstance(medical_conditions, str):
                try:
                    medical_conditions = json.loads(medical_conditions)
                except:
                    medical_conditions = []
            elif medical_conditions is None:
                medical_conditions = []
            
            users_list.append({
                "id": customer["id"],
                "email": customer["email"],
                "role": customer.get("role", "user"),
                "age": customer.get("age"),
                "sex": customer.get("sex"),
                "diabetes": customer.get("diabetes", False),
                "hypertension": customer.get("hypertension", False),
                "pregnancy": customer.get("pregnancy", False),
                "city": customer.get("city"),
                "is_active": customer.get("is_active", True),
                "created_at": customer["created_at"].isoformat() if customer.get("created_at") else None,
                "last_login": customer["last_login"].isoformat() if customer.get("last_login") else None,
                "medical_conditions": medical_conditions,
            })
        
        return {
            "total": len(users_list),
            "users": users_list
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve users")


@app.get("/customer/{customer_id}/sessions")
async def get_customer_sessions(
    customer_id: str,
    limit: int = 50,
    user: dict = Depends(require_auth)
):
    """
    Get chat sessions for a customer
    Requires authentication
    Users can only view their own sessions, admins can view any sessions
    Cached in Redis for 5 minutes
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid, validate_query_limit
    try:
        customer_id = validate_uuid(customer_id)
        limit = validate_query_limit(limit, max_limit=1000, min_limit=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not db_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if user is accessing their own sessions or is admin
    user_role = user.get("role", "user")
    user_id = user.get("user_id")
    
    if user_role != "admin" and user_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own sessions"
        )
    
    # Try to get from Redis cache first
    cache_key = f"sessions:{customer_id}:{limit}"
    cached_result = await cache_service.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for customer sessions: {customer_id}")
        return cached_result
    
    # If not in cache, fetch from database
    sessions = await db_service.get_customer_sessions(customer_id, limit=limit)
    result = []
    for session in sessions:
        # Get first user message for title
        first_message = await db_service.get_session_first_message(session["id"])
        # Get message count for this session
        messages = await db_service.get_session_messages(session["id"], limit=1000)
        result.append({
            "id": session["id"],
            "customerId": session["customer_id"],
            "createdAt": session["created_at"].isoformat() if session.get("created_at") else None,
            "updatedAt": session["updated_at"].isoformat() if session.get("updated_at") else None,
            "language": session.get("language"),
            "sessionMetadata": session.get("session_metadata"),
            "messageCount": len(messages),
            "firstMessage": first_message.get("message_text") if first_message else None,
        })
    
    # Cache the result for 5 minutes (300 seconds)
    await cache_service.set(cache_key, result, ttl=300)
    
    return result


@app.get("/session/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 100,
    user: dict = Depends(require_auth)
):
    """
    Get messages for a session
    Requires authentication
    Users can only view messages from their own sessions, admins can view any messages
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid, validate_query_limit
    try:
        session_id = validate_uuid(session_id)
        limit = validate_query_limit(limit, max_limit=1000, min_limit=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not db_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Verify session belongs to user (unless admin)
    user_role = user.get("role", "user")
    user_id = user.get("user_id")
    
    if user_role != "admin":
        # Get session to verify ownership
        session = await db_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("customer_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view messages from your own sessions"
            )
    
    # Try to get from Redis cache first
    cache_key = f"session_messages:{session_id}:{limit}"
    cached_messages = await cache_service.get(cache_key)
    if cached_messages is not None:
        logger.debug(f"Cache hit for session messages: {session_id}")
        return cached_messages
    
    # If not in cache, fetch from database
    messages = await db_service.get_session_messages(session_id, limit=limit)
    result = [
        {
            "id": message["id"],
            "sessionId": message["session_id"],
            "createdAt": message["created_at"].isoformat() if message.get("created_at") else None,
            "role": message["role"],
            "messageText": message["message_text"],
            "language": message.get("language"),
            "route": message.get("route"),
            "answer": message.get("answer"),
            "safetyData": message.get("safety_data"),
            "facts": message.get("facts"),
            "citations": message.get("citations"),
            "metadata": message.get("metadata"),
        }
        for message in messages
    ]
    
    # Cache the result for 5 minutes (300 seconds)
    await cache_service.set(cache_key, result, ttl=300)
    
    return result


@app.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    user: dict = Depends(require_auth)
):
    """
    Delete a chat session and all its messages
    Requires authentication
    Users can only delete their own sessions, admins can delete any session
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid
    try:
        session_id = validate_uuid(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not db_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Verify session belongs to user (unless admin)
    user_role = user.get("role", "user")
    user_id = user.get("user_id")
    
    if user_role != "admin":
        # Get session to verify ownership
        session = await db_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("customer_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete your own sessions"
            )
    
    # Delete the session
    deleted = await db_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete session")
    
    # Invalidate cache for customer sessions and session data
    if cache_service.is_available():
        try:
            if user_id:
                # Invalidate customer sessions cache (all limits)
                for limit_val in [10, 50, 100, 200, 500, 1000]:
                    cache_key = f"sessions:{user_id}:{limit_val}"
                    await cache_service.delete(cache_key)
            # Invalidate session messages cache (all limits)
            for limit_val in [10, 50, 100, 200, 500, 1000]:
                cache_key = f"session_messages:{session_id}:{limit_val}"
                await cache_service.delete(cache_key)
            # Invalidate full session cache
            await cache_service.delete(f"session_full:{session_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache after session deletion: {e}")
    
    return {"success": True, "message": "Session deleted successfully"}


@app.get("/session/{session_id}")
async def get_session(
    session_id: str,
    user: dict = Depends(require_auth)
):
    """
    Get session information with messages
    Requires authentication
    Users can only view their own sessions, admins can view any session
    Cached in Redis for 5 minutes
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid
    try:
        session_id = validate_uuid(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not db_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Try to get from Redis cache first
    cache_key = f"session_full:{session_id}"
    cached_session = await cache_service.get(cache_key)
    if cached_session is not None:
        logger.debug(f"Cache hit for session: {session_id}")
        # Verify session belongs to user (unless admin)
        user_role = user.get("role", "user")
        user_id = user.get("user_id")
        if user_role != "admin" and cached_session.get("customerId") != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own sessions"
            )
        return cached_session
    
    try:
        chat_session = await db_service.get_session(session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Verify session belongs to user (unless admin)
        user_role = user.get("role", "user")
        user_id = user.get("user_id")
        
        if user_role != "admin" and chat_session.get("customer_id") != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own sessions"
            )
        
        # Get customer info
        customer = None
        if chat_session.get("customer_id"):
            customer_data = await db_service.get_customer(chat_session["customer_id"])
            if customer_data:
                customer = {
                    "id": customer_data["id"],
                    "email": customer_data["email"],
                    "age": customer_data.get("age"),
                    "sex": customer_data.get("sex"),
                    "city": customer_data.get("city"),
                }
        
        # Get messages
        messages = chat_session.get("messages", [])
        
        result = {
            "id": chat_session["id"],
            "customerId": chat_session["customer_id"],
            "createdAt": chat_session["created_at"].isoformat() if chat_session.get("created_at") else None,
            "updatedAt": chat_session["updated_at"].isoformat() if chat_session.get("updated_at") else None,
            "language": chat_session.get("language"),
            "sessionMetadata": chat_session.get("session_metadata"),
            "customer": customer,
            "messages": [
                {
                    "id": message["id"],
                    "createdAt": message["created_at"].isoformat() if message.get("created_at") else None,
                    "role": message["role"],
                    "messageText": message["message_text"],
                    "language": message.get("language"),
                    "route": message.get("route"),
                    "answer": message.get("answer"),
                    "safetyData": message.get("safety_data"),
                    "facts": message.get("facts"),
                    "citations": message.get("citations"),
                    "metadata": message.get("metadata"),
                }
                for message in messages
            ],
        }
        
        # Cache the result for 5 minutes (300 seconds)
        await cache_service.set(cache_key, result, ttl=300)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve session") from e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)