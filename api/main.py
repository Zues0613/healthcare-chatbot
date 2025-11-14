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

from deep_translator import GoogleTranslator  # type: ignore
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

try:
    from indic_transliteration import sanscript  # type: ignore
    from indic_transliteration.sanscript import transliterate  # type: ignore
except Exception:  # pragma: no cover
    sanscript = None
    transliterate = None

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
from .rag.retriever import retrieve
from .models import ChatRequest, ChatResponse, Profile, VoiceChatResponse

from .graph import fallback as graph_fallback
from .graph.cypher import (
    get_red_flags as neo4j_get_red_flags,
    get_contraindications as neo4j_get_contraindications,
    get_providers_in_city as neo4j_get_providers_in_city,
    get_safe_actions_for_metabolic_conditions as neo4j_get_safe_actions,
)
from .graph.client import neo4j_client
from .services.indic_translator import IndicTransService
from .database import prisma_client, db_service
from .auth.routes import router as auth_router
from .auth.middleware import require_auth, require_role

indic_translator = IndicTransService()

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
    """Initialize persistent database connection pool on startup"""
    try:
        # Initialize PostgreSQL connection pool (persistent, stays alive)
        connected = await prisma_client.connect()
        if connected:
            logger.info("PostgreSQL connection pool initialized successfully (persistent connection)")
        else:
            logger.warning("Database not connected - chat history will not be saved")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        logger.warning("Database not connected - chat history will not be saved")


@app.on_event("shutdown")
async def _shutdown() -> None:
    """Cleanup database connections on shutdown"""
    logger.info("Shutting down database connections...")
    if neo4j_client.driver:
        neo4j_client.close()
    # Close PostgreSQL connection pool
    await prisma_client.disconnect()
    logger.info("Database connections closed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(","),
    allow_credentials=True,  # Required for HTTP-only cookies
    allow_methods=["*"],
    allow_headers=["*"],
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
    if not text.strip():
        return text

    if src_lang and src_lang == target_lang:
        return text

    try:
        translator = GoogleTranslator(
            source=src_lang if src_lang else "auto",
            target=target_lang,
        )
        return translator.translate(text)
    except Exception as exc:
        logger.warning(
            "Translation error",
            extra={"source": src_lang or "auto", "target": target_lang, "error": str(exc)},
        )
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
    try:
        converted = GoogleTranslator(source=lang, target=lang).translate(text)
        if converted and converted.strip().lower() != text.strip().lower():
            return converted
    except Exception as exc:
        logger.debug(
            "Native script conversion failed",
            extra={"lang": lang, "error": str(exc)},
        )
    return None


def translate_romanized_to_english(
    text: str, lang: str
) -> Tuple[str, Optional[str], Dict[str, Any]]:
    """
    Translate romanized Indic text to English. Tries IndicTrans2 first (if available),
    then falls back to Google Translate heuristics.
    """
    meta: Dict[str, Any] = {"attempts": []}

    if indic_translator.is_enabled():
        result = indic_translator.translate_romanized_to_english(text, lang)
        meta["attempts"].append(
            {
                "provider": "indictrans2",
                "success": result.success,
                **result.details,
            }
        )
        if result.success and result.translated_text:
            meta["provider"] = "indictrans2"
            return result.translated_text or text, result.native_script, meta

    initial = translate_text(text, target_lang="en", src_lang=lang)
    if initial.strip().lower() != text.strip().lower():
        meta["provider"] = "google_translate"
        meta["attempts"].append(
            {
                "provider": "google_translate",
                "success": True,
                "native_script_conversion": False,
            }
        )
        return initial, None, meta

    native_script = attempt_native_script_conversion(text, lang)
    if native_script:
        translated = translate_text(native_script, target_lang="en", src_lang=lang)
        meta["provider"] = "google_translate"
        meta["attempts"].append(
            {
                "provider": "google_translate",
                "success": True,
                "native_script_conversion": True,
            }
        )
        return translated, native_script, meta

    meta["provider"] = "google_translate"
    meta["attempts"].append(
        {
            "provider": "google_translate",
            "success": True,
            "native_script_conversion": False,
            "note": "direct passthrough (no better translation available)",
        }
    )
    return initial, None, meta


def romanize_text(text: str, lang: str) -> str:
    if (
        not text
        or lang == "en"
        or transliterate is None
        or sanscript is None
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
    meta: Dict[str, Any] = {}

    if target_lang == src_lang:
        meta.update({"provider": "identity", "success": True})
        if capture_meta is not None:
            capture_meta.update(meta)
        return text

    translated = None

    if src_lang == "en" and indic_translator.is_enabled():
        result = indic_translator.translate_english_to_local(text, target_lang)
        meta = {
            "provider": result.provider,
            "success": result.success,
            **result.details,
        }
        if result.success and result.translated_text:
            translated = result.translated_text

    if translated is None:
        translated = translate_text(text, target_lang=target_lang, src_lang=src_lang)
        meta.setdefault("provider", "google_translate")
        meta.setdefault("success", True)
        meta.setdefault("reason", "fallback_to_google")

    if response_style == "romanized" and target_lang != "en":
        translated = romanize_text(translated, target_lang)

    if capture_meta is not None:
        capture_meta.update(meta)

    return translated


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
_chat_model_openai: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-3.5-turbo")
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
            "database": prisma_client.is_connected()
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


def process_chat_request(request: ChatRequest) -> Tuple[ChatResponse, str, Dict[str, float]]:
    timings: Dict[str, float] = {}
    total_start = time.perf_counter()

    text = request.text
    requested_lang_raw = request.lang if request.lang in SUPPORTED_LANG_CODES else None
    romanized_lang = detect_romanized_language(text)
    detected_lang = detect_language(text) if text else DEFAULT_LANG
    detected_supported = detected_lang if detected_lang in SUPPORTED_LANG_CODES else None

    requested_lang = requested_lang_raw
    response_style = "native"
    native_script_variant: Optional[str] = None
    debug_info: Dict[str, Any] = {
        "input_text": text,
        "requested_language": requested_lang_raw,
        "detected_language": detected_lang,
        "romanized_detected_language": romanized_lang,
    }

    if romanized_lang:
        if not requested_lang or requested_lang in {DEFAULT_LANG, romanized_lang}:
            requested_lang = romanized_lang
            response_style = "romanized"
        if not detected_supported or detected_supported in {DEFAULT_LANG, "en"}:
            detected_supported = romanized_lang

    target_lang = requested_lang or detected_supported or DEFAULT_LANG
    language_label = get_language_label(target_lang, response_style=response_style)
    debug_info["target_language"] = target_lang
    debug_info["response_style"] = response_style

    profile: Profile = request.profile
    personalization_notes = build_personalization_notes(profile)

    processed_text = text
    source_lang_for_processing = detected_supported or DEFAULT_LANG
    romanization_meta: Dict[str, Any] = {}
    if romanized_lang and response_style == "romanized":
        processed_text, native_script_variant, romanization_meta = translate_romanized_to_english(
            text, romanized_lang
        )
        source_lang_for_processing = romanized_lang
    elif source_lang_for_processing != "en":
        processed_text = translate_text(text, target_lang="en", src_lang=source_lang_for_processing)
    debug_info["processed_text_en"] = processed_text
    debug_info["processed_text_source_language"] = source_lang_for_processing
    if native_script_variant:
        debug_info["native_script_variant"] = native_script_variant
    if romanization_meta:
        debug_info["romanized_translation"] = romanization_meta

    safety_start = time.perf_counter()
    safety_result = detect_red_flags(processed_text, "en")
    mental_health_en = detect_mental_health_crisis(processed_text, "en")
    pregnancy_alert_en = detect_pregnancy_emergency(processed_text)
    timings["safety_analysis"] = time.perf_counter() - safety_start

    mental_health_display = mental_health_en
    if target_lang != "en" and mental_health_en["first_aid"]:
        mental_health_display = {
            **mental_health_en,
            "first_aid": localize_list(
                mental_health_en["first_aid"],
                target_lang,
                response_style=response_style,
            ),
        }

    pregnancy_guidance_display = (
        PREGNANCY_ALERT_GUIDANCE_EN
        if target_lang == "en"
        else localize_list(
            PREGNANCY_ALERT_GUIDANCE_EN,
            target_lang,
            response_style=response_style,
        )
    )
    pregnancy_alert_display = {
        **pregnancy_alert_en,
        "guidance": pregnancy_guidance_display,
    }

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
        
        rag_start = time.perf_counter()
        rag_results = retrieve(processed_text, k=3)
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

        generation_start = time.perf_counter()
        answer_en, provider_meta = generate_answer(
            context=context,
            query_en=processed_text,
            llm_language_label="English",
            original_query=text,
            facts=facts_en,
            citations=citations,
        )
        if provider_meta.get("fallback"):
            localized_answer = build_fallback_answer(
                query_en=processed_text,
                rag_results=rag_results,
                facts=facts_en,
                citations=citations,
                target_lang=target_lang,
                response_style=response_style,
            )
            answer_en = FALLBACK_MESSAGE_EN
        else:
            localization_meta: Dict[str, Any] = {}
            localized_answer = localize_text(
                answer_en,
                target_lang=target_lang,
                response_style=response_style,
                capture_meta=localization_meta,
            )
            if localization_meta:
                debug_info["localization"] = localization_meta
        timings["answer_generation"] = time.perf_counter() - generation_start
        debug_info["llm"] = provider_meta
        debug_info["answer_en"] = answer_en
        debug_info["answer_localized"] = localized_answer
        answer = localized_answer
        
    else:
        rag_start = time.perf_counter()
        rag_results = retrieve(processed_text, k=4)
        timings["retrieval"] = time.perf_counter() - rag_start
        debug_info["rag_context_snippets"] = [r["chunk"][:200] for r in rag_results]
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

            generation_start = time.perf_counter()
            answer_en, provider_meta = generate_answer(
                context=context,
                query_en=processed_text,
                llm_language_label="English",
                original_query=text,
                facts=facts_en,
                citations=citations,
            )
            if provider_meta.get("fallback"):
                localized_answer = build_fallback_answer(
                    query_en=processed_text,
                    rag_results=rag_results,
                    facts=facts_en,
                    citations=citations,
                    target_lang=target_lang,
                    response_style=response_style,
                )
                answer_en = FALLBACK_MESSAGE_EN
            else:
                localization_meta: Dict[str, Any] = {}
                localized_answer = localize_text(
                    answer_en,
                    target_lang=target_lang,
                    response_style=response_style,
                    capture_meta=localization_meta,
                )
                if localization_meta:
                    debug_info["localization"] = localization_meta
            timings["answer_generation"] = time.perf_counter() - generation_start
            debug_info["llm"] = provider_meta
            debug_info["answer_en"] = answer_en
            debug_info["answer_localized"] = localized_answer
            answer = localized_answer

    if not safety_result["red_flag"]:
        answer += "\n\n" + get_localized_disclaimer(target_lang, response_style=response_style)

    facts_response = localize_fact_guidance(facts_en, target_lang, response_style=response_style)

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
            "response_style": response_style,
        },
    )
    timings["total"] = time.perf_counter() - total_start

    metadata_payload: Dict[str, Any] = {
        "timings": timings,
        "target_language": target_lang,
        "response_style": response_style,
    }
    if request.debug:
        metadata_payload["debug"] = debug_info
        debug_info["response_length"] = len(answer)
        debug_info["rag_context_count"] = len(debug_info.get("rag_context_snippets") or [])
    response.metadata = metadata_payload

    return response, target_lang, timings


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
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
        
        if prisma_client.is_connected():
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
                
                customer_id = customer.id
                
                # Get or create session
                chat_session = await db_service.get_or_create_session(
                    customer_id=customer_id,
                    language=request.lang,
                    session_id=session_id
                )
                
                if chat_session:
                    session_id = chat_session["id"]
                    
                    # Save user message
                    await db_service.save_chat_message(
                        session_id=session_id,
                        role="user",
                        message_text=request.text,
                        language=request.lang,
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to save customer/session data: {e}", exc_info=True)
        
        # Process chat request
        response, target_lang, timings = process_chat_request(request)
        
        # Save assistant response to database
        if prisma_client.is_connected() and session_id:
            try:
                # Convert safety to dict
                safety_dict = response.safety.model_dump() if hasattr(response.safety, 'model_dump') else dict(response.safety)
                
                await db_service.save_chat_message(
                    session_id=session_id,
                    role="assistant",
                    message_text=request.text,  # User's original question
                    language=target_lang,
                    answer=response.answer,
                    route=response.route,
                    safety_data=safety_dict,
                    facts=response.facts,
                    citations=response.citations,
                    metadata=response.metadata,
                )
            except Exception as e:
                logger.warning(f"Failed to save chat message: {e}", exc_info=True)
        
        # Add customer_id and session_id to response metadata
        if customer_id:
            response.metadata["customer_id"] = customer_id
        if session_id:
            response.metadata["session_id"] = session_id
        
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
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat processing failed")
        raise HTTPException(
            status_code=500,
            detail="Unable to process your request right now. Please try again in a moment.",
        ) from e


@app.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat(
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

        # Save customer data to database (same logic as chat endpoint)
        if prisma_client.is_connected():
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
                
                chat_session = await db_service.get_or_create_session(
                    customer_id=customer_id,
                    language=chat_request.lang,
                    session_id=session_id
                )
                
                if chat_session:
                    session_id = chat_session["id"]
                    
                    # Save user message
                    await db_service.save_chat_message(
                        session_id=session_id,
                        role="user",
                        message_text=transcript,
                        language=chat_request.lang,
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to save customer/session data in voice_chat: {e}", exc_info=True)

        chat_response, target_lang, chat_timings = process_chat_request(chat_request)

        # Save assistant response to database
        if prisma_client.is_connected() and session_id:
            try:
                safety_dict = chat_response.safety.model_dump() if hasattr(chat_response.safety, 'model_dump') else dict(chat_response.safety)
                
                await db_service.save_chat_message(
                    session_id=session_id,
                    role="assistant",
                    message_text=transcript,
                    language=target_lang,
                    answer=chat_response.answer,
                    route=chat_response.route,
                    safety_data=safety_dict,
                    facts=chat_response.facts,
                    citations=chat_response.citations,
                    metadata=chat_response.metadata,
                )
            except Exception as e:
                logger.warning(f"Failed to save chat message in voice_chat: {e}", exc_info=True)

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
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid
    try:
        customer_id = validate_uuid(customer_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not prisma_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if user is accessing their own profile or is admin
    user_role = user.get("role", "user")
    user_id = user.get("user_id")
    
    if user_role != "admin" and user_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own profile"
        )
    
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
    
    return {
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
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid, validate_query_limit
    try:
        customer_id = validate_uuid(customer_id)
        limit = validate_query_limit(limit, max_limit=100, min_limit=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not prisma_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
    # Check if user is accessing their own sessions or is admin
    user_role = user.get("role", "user")
    user_id = user.get("user_id")
    
    if user_role != "admin" and user_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own sessions"
        )
    
    sessions = await db_service.get_customer_sessions(customer_id, limit=limit)
    result = []
    for session in sessions:
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
        })
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
        limit = validate_query_limit(limit, max_limit=200, min_limit=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not prisma_client.is_connected():
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
    
    messages = await db_service.get_session_messages(session_id, limit=limit)
    return [
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


@app.get("/session/{session_id}")
async def get_session(
    session_id: str,
    user: dict = Depends(require_auth)
):
    """
    Get session information with messages
    Requires authentication
    Users can only view their own sessions, admins can view any session
    """
    # Validate path parameter to prevent SQL injection
    from .auth.validation import validate_uuid
    try:
        session_id = validate_uuid(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not prisma_client.is_connected():
        raise HTTPException(status_code=503, detail="Database not available")
    
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
        
        return {
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve session") from e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)