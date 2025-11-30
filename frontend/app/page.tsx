'use client';

import clsx from 'clsx';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, API_BASE } from '../utils/api';
import { isAuthenticated, clearAuth, getAuthUser, updateActivity } from '../utils/auth';
import {
  AlertTriangle,
  Check,
  HeartPulse,
  Menu,
  Mic,
  Volume2,
  VolumeX,
  Phone,
  SendHorizonal,
  Settings,
  Share2,
  Sparkle,
  X,
  Plus,
  Search,
  User,
  LogOut,
  Trash2,
} from 'lucide-react';
import ChatMessage, { type ChatMessageModel } from '../components/ChatMessage';
import LoadingSkeleton from '../components/LoadingSkeleton';
import ErrorCallout from '../components/ErrorCallout';
import ProfileCard from '../components/ProfileCard';
import TopicSuggestions from '../components/TopicSuggestions';
import WelcomeScreen from '../components/WelcomeScreen';
import SearchChatsModal from '../components/SearchChatsModal';
import ConfirmDeleteModal from '../components/ConfirmDeleteModal';
import QuickLoader from '../components/QuickLoader';
import { TOPIC_CATEGORIES } from '../data/topics';
import { CalendarDays, Heart, MapPin, Stethoscope } from 'lucide-react';

type LangCode = 'en' | 'hi' | 'ta' | 'te' | 'kn' | 'ml';
type SexOption = 'male' | 'female' | 'other';

const LANGUAGE_OPTIONS: Array<{
  value: LangCode;
  label: string;
  speechLang: string;
  placeholder: string;
  introTitle: string;
  introSubtitle: string;
}> = [
  {
    value: 'en',
    label: 'English',
    speechLang: 'en-US',
    placeholder: 'Describe your symptoms or ask about first steps…',
    introTitle: 'How can I care for you today?',
    introSubtitle:
      'Ask about symptoms, self-care, or when it’s safest to see a clinician.',
  },
  {
    value: 'hi',
    label: 'हिन्दी',
    speechLang: 'hi-IN',
    placeholder: 'अपने लक्षण साझा करें या देखभाल के बारे में पूछें…',
    introTitle: 'आज मैं आपकी कैसे मदद कर सकता हूँ?',
    introSubtitle:
      'लक्षणों, घरेलू देखभाल या डॉक्टर से मिलने के सही समय के बारे में पूछें।',
  },
  {
    value: 'ta',
    label: 'தமிழ்',
    speechLang: 'ta-IN',
    placeholder: 'உங்கள் அறிகுறிகளை அல்லது வழிகாட்டலை பற்றி கேளுங்கள்…',
    introTitle: 'இன்று நான் எப்படி உதவலாம்?',
    introSubtitle:
      'அறிகுறிகள், சுய பராமரிப்பு அல்லது மருத்துவரை அணுக வேண்டிய நேரத்தை கேளுங்கள்.',
  },
  {
    value: 'te',
    label: 'తెలుగు',
    speechLang: 'te-IN',
    placeholder: 'మీ లక్షణాలు లేదా జాగ్రత్తల గురించి అడగండి…',
    introTitle: 'ఈ రోజు నేను ఎలా సహాయం చేయగలను?',
    introSubtitle:
      'లక్షణాలు, స్వీయ సంరక్షణ లేదా డాక్టర్‌ను ఎప్పుడు సంప్రదించాలో అడగండి.',
  },
  {
    value: 'kn',
    label: 'ಕನ್ನಡ',
    speechLang: 'kn-IN',
    placeholder: 'ನಿಮ್ಮ ಲಕ್ಷಣಗಳನ್ನು ಅಥವಾ ಆರೈಕೆಯನ್ನು ಕುರಿತು ಕೇಳಿ…',
    introTitle: 'ಇಂದು ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?',
    introSubtitle:
      'ಲಕ್ಷಣಗಳು, ಸ್ವ-ಆರೈಕೆ ಅಥವಾ ವೈದ್ಯರನ್ನು ಭೇಟಿಯಾಗುವ ಸಮಯವನ್ನು ಕುರಿತು ಕೇಳಿ.',
  },
  {
    value: 'ml',
    label: 'മലയാളം',
    speechLang: 'ml-IN',
    placeholder: 'ലക്ഷണങ്ങൾ പങ്കിടുക അല്ലെങ്കിൽ പരിപാലനത്തെക്കുറിച്ച് ചോദിക്കുക…',
    introTitle: 'ഇന്ന് നിങ്ങളെ എങ്ങനെ സഹായിക്കാം?',
    introSubtitle:
      'ലക്ഷണങ്ങൾ, സ്വയംപരിചരണം, ഡോക്ടറെ കാണേണ്ട ശരിയായ സമയം എന്നിവയെക്കുറിച്ച് ചോദിക്കുക.',
  },
];

const LANGUAGE_SPEECH_MAP: Record<LangCode, string> = LANGUAGE_OPTIONS.reduce(
  (acc, option) => {
    acc[option.value] = option.speechLang;
    return acc;
  },
  {} as Record<LangCode, string>
);

interface Profile {
  diabetes: boolean;
  hypertension: boolean;
  pregnancy: boolean;
  age?: number;
  sex?: SexOption;
  city?: string;
}

interface ChatEntry extends ChatMessageModel {
  facts?: any[];
  safety?: any;
}

const defaultProfile: Profile = {
  diabetes: false,
  hypertension: false,
  pregnancy: false,
  age: undefined,
  sex: undefined,
  city: '',
};

const initialAssistantMessage: ChatEntry | null = null;

const createId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

const formatTimestamp = () => new Date().toISOString();

interface HomeProps {
  initialSessionId?: string;
}

export default function Home({ initialSessionId }: HomeProps = {}) {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<LangCode>('en');
  const [showProfile, setShowProfile] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showSafety, setShowSafety] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isAuthChecked, setIsAuthChecked] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [profile, setProfile] = useState<Profile>(defaultProfile);
  const [profileLoading, setProfileLoading] = useState(true);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);
  const [showWelcome, setShowWelcome] = useState(false);
  const [showSearchChats, setShowSearchChats] = useState(false);
  const [deleteConfirmModal, setDeleteConfirmModal] = useState<{
    isOpen: boolean;
    sessionId: string | null;
  }>({ isOpen: false, sessionId: null });
  const [chatSessions, setChatSessions] = useState<Array<{
    id: string;
    customerId: string;
    createdAt: string;
    updatedAt: string;
    lastActivityAt?: string;
    language?: string;
    messageCount: number;
    firstMessage?: string;
  }>>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(initialSessionId || null);
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [narrationEnabled, setNarrationEnabled] = useState<boolean>(false);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [userDisplayName, setUserDisplayName] = useState<string>('User');

  // Persist narration preference per user (email) with a sensible default of enabled
  const narrationPrefKey = useMemo(() => {
    const user = getAuthUser();
    const userKey = user?.email ?? 'guest';
    return `narration_enabled:${userKey}`;
  }, [isAuthChecked]);

  // Set user display name on client side only (prevents hydration mismatch)
  useEffect(() => {
    if (typeof window !== 'undefined' && isAuthChecked) {
      const user = getAuthUser();
      const displayName = user?.fullName || user?.email?.split('@')[0] || 'User';
      setUserDisplayName(displayName);
    }
  }, [isAuthChecked]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      const saved = localStorage.getItem(narrationPrefKey);
      if (saved === null) {
        // default to disabled
        localStorage.setItem(narrationPrefKey, 'false');
        setNarrationEnabled(false);
      } else {
        setNarrationEnabled(saved === 'true');
      }
    } catch {
      // fallback
      setNarrationEnabled(false);
    }
  }, [narrationPrefKey]);

  const toggleNarration = useCallback(() => {
    setNarrationEnabled((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(narrationPrefKey, String(next));
      } catch {}
      if (!next && typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      return next;
    });
  }, [narrationPrefKey]);

  const stopNarration = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }, []);

  // All refs must be declared before any conditional returns
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const shareFeedbackTimeoutRef = useRef<number | null>(null);

  // All useMemo hooks must be before conditional returns

  const currentLanguage =
    LANGUAGE_OPTIONS.find((option) => option.value === lang) ?? LANGUAGE_OPTIONS[0];

  // Load chat sessions from browser cache
  const loadChatSessionsFromCache = useCallback((customerId: string): Array<any> | null => {
    try {
      const cacheKey = `chat_sessions_${customerId}`;
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { data, timestamp } = JSON.parse(cached);
        // Use cache if less than 5 minutes old
        if (Date.now() - timestamp < 5 * 60 * 1000) {
          return data;
        }
      }
    } catch (err) {
      console.warn('Error loading sessions from cache:', err);
    }
    return null;
  }, []);

  // Save chat sessions to browser cache
  const saveChatSessionsToCache = useCallback((customerId: string, sessions: Array<any>) => {
    try {
      const cacheKey = `chat_sessions_${customerId}`;
      const cacheData = {
        data: sessions,
        timestamp: Date.now(),
      };
      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    } catch (err) {
      console.warn('Error saving sessions to cache:', err);
    }
  }, []);

  // Debounce timer for session loading (prevents excessive API calls)
  const sessionLoadTimerRef = useRef<number | null>(null);

  // Internal function that actually fetches sessions (on-demand only)
  const loadChatSessionsInternal = useCallback(async (customerId: string, forceRefresh: boolean = false) => {
    if (!customerId) return;
    
    setSessionsLoading(true);
    try {
      // Try cache first (only if not forcing refresh)
      if (!forceRefresh) {
      const cachedSessions = loadChatSessionsFromCache(customerId);
      if (cachedSessions && cachedSessions.length > 0) {
          // Use cached data immediately (show instantly)
        setChatSessions(cachedSessions);
        setSessionsLoading(false);
          // Fetch from API in background to update cache (non-blocking, silent update)
          // Only fetch recent 50 sessions for performance
          apiClient.get(`/customer/${customerId}/sessions?limit=50`)
            .then((response) => {
              const sessions = response.data || [];
              setChatSessions(sessions);
              saveChatSessionsToCache(customerId, sessions);
            })
            .catch((err) => {
              console.warn('Background session refresh failed:', err);
              // Keep using cached data on error
            });
          return;
        }
      }

      // If no cache or force refresh, fetch from API
      // Only fetch recent 50 sessions for performance
      const response = await apiClient.get(`/customer/${customerId}/sessions?limit=50`);
      const sessions = response.data || [];
      setChatSessions(sessions);
      saveChatSessionsToCache(customerId, sessions);
    } catch (err: any) {
      console.error('Error loading chat sessions:', err);
      // Keep cached data if API fails
      const cachedSessions = loadChatSessionsFromCache(customerId);
      if (cachedSessions && cachedSessions.length > 0) {
        setChatSessions(cachedSessions);
      } else {
        setChatSessions([]);
      }
    } finally {
      setSessionsLoading(false);
    }
  }, [loadChatSessionsFromCache, saveChatSessionsToCache]);

  // Load chat sessions from API with debouncing (prevents excessive API calls)
  const loadChatSessions = useCallback(async (customerId: string, immediate: boolean = false) => {
    if (!customerId) return;
    
    // Clear existing timer if debouncing
    if (sessionLoadTimerRef.current) {
      clearTimeout(sessionLoadTimerRef.current);
      sessionLoadTimerRef.current = null;
    }
    
    // If immediate flag is set, load right away with force refresh (e.g., after sending a message)
    if (immediate) {
      await loadChatSessionsInternal(customerId, true);
      return;
    }
    
    // Otherwise, debounce the call (wait 500ms after last call) - use cache if available
    sessionLoadTimerRef.current = window.setTimeout(() => {
      loadChatSessionsInternal(customerId, false);
      sessionLoadTimerRef.current = null;
    }, 500);
  }, [loadChatSessionsInternal]);

  // Check authentication on mount and get user info
  useEffect(() => {
    // Check if token has expired
    if (!isAuthenticated()) {
      // Token expired or not authenticated, redirect to auth with message
      setIsRedirecting(true);
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('authExpired', 'true');
      }
      router.push('/auth');
      return;
    } else {
      setIsAuthChecked(true);
      // Update activity on mount (user is active)
      updateActivity();
      
      // Get customer ID from user info (with browser cache)
      const fetchUserInfo = async () => {
        try {
          // Try browser cache first
          const cacheKey = 'user_info';
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            const { data, timestamp } = JSON.parse(cached);
            // Use cache if less than 5 minutes old
            if (Date.now() - timestamp < 5 * 60 * 1000 && data?.id) {
              setCustomerId(data.id);
              // Fetch from API in background to update cache (non-blocking)
              apiClient.get('/auth/me')
                .then((response) => {
                  if (response.data?.id) {
                    setCustomerId(response.data.id);
                    // Save to browser cache
                    try {
                      const cacheData = {
                        data: response.data,
                        timestamp: Date.now(),
                      };
                      localStorage.setItem(cacheKey, JSON.stringify(cacheData));
                    } catch (err) {
                      console.warn('Error saving user info to cache:', err);
                    }
                  }
                })
                .catch((err) => {
                  console.warn('Background user info refresh failed:', err);
                  // Keep using cached data on error
                });
              return;
            }
          }
          
          // If no cache or cache is stale, fetch from API
          const response = await apiClient.get('/auth/me');
          if (response.data?.id) {
            setCustomerId(response.data.id);
            // Save to browser cache
            try {
              const cacheData = {
                data: response.data,
                timestamp: Date.now(),
              };
              localStorage.setItem(cacheKey, JSON.stringify(cacheData));
            } catch (err) {
              console.warn('Error saving user info to cache:', err);
            }
          }
        } catch (err) {
          console.error('Error fetching user info:', err);
          // If API fails but we have cached data, use it
          const cacheKey = 'user_info';
          const cached = localStorage.getItem(cacheKey);
          if (cached) {
            try {
              const { data } = JSON.parse(cached);
              if (data?.id) {
                setCustomerId(data.id);
              }
            } catch (parseErr) {
              console.warn('Error parsing cached user info:', parseErr);
            }
          }
        }
      };
      fetchUserInfo();
      
      // Check if we should show welcome screen (when coming from /auth)
      // Use a small delay to ensure sessionStorage is available
      const checkWelcome = () => {
        if (typeof window !== 'undefined') {
          const justLoggedIn = sessionStorage.getItem('justLoggedIn') === 'true';
          
          if (justLoggedIn) {
            setShowWelcome(true);
            // Clear the flag immediately so it doesn't show again on refresh
            sessionStorage.removeItem('justLoggedIn');
          }
        }
      };
      
      // Check immediately and also after a small delay to catch any timing issues
      checkWelcome();
      const timer = setTimeout(checkWelcome, 100);
      return () => clearTimeout(timer);
    }
  }, [router]);

  // Track user activity on various interactions
  useEffect(() => {
    if (!isAuthChecked) return;
    
    // Throttle to avoid excessive updates (update max once per second)
    let lastUpdate = 0;
    const throttledUpdate = () => {
      const now = Date.now();
      if (now - lastUpdate > 1000) { // Update max once per second
        updateActivity();
        lastUpdate = now;
      }
    };
    
    // Track activity on mouse movements, clicks, keyboard input
    window.addEventListener('mousedown', throttledUpdate);
    window.addEventListener('keydown', throttledUpdate);
    window.addEventListener('scroll', throttledUpdate, { passive: true });
    
    return () => {
      window.removeEventListener('mousedown', throttledUpdate);
      window.removeEventListener('keydown', throttledUpdate);
      window.removeEventListener('scroll', throttledUpdate);
    };
  }, [isAuthChecked]);

  // Load session if initialSessionId is provided
  useEffect(() => {
    console.log('Session loading effect triggered:', {
      initialSessionId,
      isAuthChecked,
      customerId,
      hasInitialSessionId: !!initialSessionId
    });
    
    if (initialSessionId && isAuthChecked && customerId) {
      setIsLoadingSession(true);
      const loadInitialSession = async () => {
        try {
          // Try cache first, but only use it if citations are present
          const cacheKey = `session_messages_${initialSessionId}`;
          let useCache = false;
          try {
            const cached = localStorage.getItem(cacheKey);
            if (cached) {
              const { data, timestamp } = JSON.parse(cached);
              if (Date.now() - timestamp < 5 * 60 * 1000 && data && Array.isArray(data) && data.length > 0) {
                // Check if cached messages have citations (at least for assistant messages)
                const hasCitations = data.some((msg: any) => {
                  if (msg.role === 'assistant') {
                    const citations = msg.citations || msg.citation;
                    return citations && (Array.isArray(citations) ? citations.length > 0 : true);
                  }
                  return true; // User messages don't need citations
                });
                
                if (hasCitations) {
                  console.log('Loading from cache:', data.length, 'messages');
                  console.log('First cached message citations:', data[0]?.citations);
                  const chatEntries: ChatEntry[] = data.map((msg: any) => {
                    // Handle citations - check multiple possible field names
                    let citations = [];
                    if (msg.citations) {
                      citations = Array.isArray(msg.citations) ? msg.citations : [msg.citations];
                    } else if (msg.citation) {
                      citations = Array.isArray(msg.citation) ? msg.citation : [msg.citation];
                    }
                    
                    return {
                      id: msg.id,
                      role: msg.role,
                      content: msg.role === 'assistant' 
                        ? (msg.answer || msg.messageText || '') 
                        : (msg.messageText || msg.answer || ''),
                      timestamp: msg.createdAt || formatTimestamp(),
                      language: msg.language || lang,
                      route: msg.route,
                      safety: msg.safetyData,
                      facts: msg.facts,
                      citations: citations,
                      userFeedback: msg.userFeedback || msg.user_feedback, // Include feedback from cache
                    };
                  });
                  console.log('Cached entries citations:', chatEntries[0]?.citations);
                  
                  // Get real session ID from first message if available
                  const realSessionId = data[0]?.sessionId || initialSessionId;
                  
                  setMessages(chatEntries);
                  setCurrentSessionId(realSessionId);
                  setHasInteracted(true);
                  setIsLoadingSession(false);
                  console.log('Loaded from cache, messages count:', chatEntries.length);
                  useCache = true;
                } else {
                  console.log('Cache exists but missing citations, fetching from API');
                }
              }
            }
          } catch (cacheErr) {
            console.warn('Error loading from cache:', cacheErr);
          }
          
          // If we used cache successfully, return early
          if (useCache) {
            return;
          }

          // Fetch from API
          console.log('Loading session messages for:', initialSessionId);
          setIsLoadingSession(true);
          const response = await apiClient.get(`/session/${initialSessionId}/messages?limit=1000`);
          const messages = response.data || [];
          
          console.log('Received messages from API:', messages.length, 'messages');
          console.log('First message sample:', messages[0]);
          console.log('First message citations:', messages[0]?.citations);
          console.log('Assistant messages with citations:', messages.filter((m: any) => m.role === 'assistant' && m.citations && m.citations.length > 0).length);
          console.log('Response structure:', {
            data: response.data,
            status: response.status,
            isArray: Array.isArray(messages)
          });
          
          if (messages && Array.isArray(messages) && messages.length > 0) {
            const chatEntries: ChatEntry[] = messages.map((msg: any) => {
              // Get the real session ID from the first message if available
              const realSessionId = msg.sessionId || initialSessionId;
              
              // Handle citations - check multiple possible field names
              let citations: any[] = [];
              if (msg.citations) {
                if (Array.isArray(msg.citations)) {
                  citations = msg.citations.filter((c: any) => c != null); // Filter out null/undefined
                } else if (msg.citations !== null && msg.citations !== undefined) {
                  citations = [msg.citations];
                }
              } else if (msg.citation) {
                if (Array.isArray(msg.citation)) {
                  citations = msg.citation.filter((c: any) => c != null);
                } else if (msg.citation !== null && msg.citation !== undefined) {
                  citations = [msg.citation];
                }
              }
              
              // Log citation details for assistant messages
              if (msg.role === 'assistant') {
                console.log(`📋 Message ${msg.id?.substring(0, 8)} citations:`, {
                  raw: msg.citations,
                  processed: citations,
                  count: citations.length,
                  hasUrl: citations.some((c: any) => c?.url),
                  sample: citations[0]
                });
              }
              
              return {
                id: msg.id,
                role: msg.role,
                content: msg.role === 'assistant' 
                  ? (msg.answer || msg.messageText || '') 
                  : (msg.messageText || msg.answer || ''),
                timestamp: msg.createdAt || formatTimestamp(),
                language: msg.language || lang,
                route: msg.route,
                safety: msg.safetyData,
                facts: msg.facts,
                citations: citations,
                userFeedback: msg.userFeedback || msg.user_feedback, // Support both camelCase and snake_case
              };
            });
            
            console.log('Mapped chat entries:', chatEntries.length);
            console.log('First entry citations:', chatEntries[0]?.citations);
            
            // Check all assistant messages for citations
            const assistantMessages = chatEntries.filter((e: ChatEntry) => e.role === 'assistant');
            console.log('📊 Assistant messages summary:');
            assistantMessages.forEach((msg: ChatEntry, idx: number) => {
              console.log(`  Message ${idx + 1}:`, {
                id: msg.id?.substring(0, 8),
                hasCitations: !!(msg.citations && msg.citations.length > 0),
                citationsCount: msg.citations?.length || 0,
                citations: msg.citations
              });
            });
            
            // Get real session ID from first message if available
            const realSessionId = messages[0]?.sessionId || initialSessionId;
            
            setMessages(chatEntries);
            setCurrentSessionId(realSessionId);
            setHasInteracted(true);
            setIsLoadingSession(false);

            // Save to cache (use real session ID for cache key if available)
            try {
              const cacheData = {
                data: messages,
                timestamp: Date.now(),
              };
              // Use hashed ID for cache key to match what we'll look for
              localStorage.setItem(cacheKey, JSON.stringify(cacheData));
            } catch (cacheErr) {
              console.warn('Error saving to cache:', cacheErr);
            }
          } else {
            console.warn('No messages found or empty array');
            setMessages([]);
            setCurrentSessionId(initialSessionId);
            setHasInteracted(true);
            setIsLoadingSession(false);
          }
        } catch (err: any) {
          console.error('Error loading initial session:', err);
          console.error('Error details:', {
            status: err.response?.status,
            data: err.response?.data,
            message: err.message
          });
          setIsLoadingSession(false);
          if (err.response?.status === 404) {
            // Session doesn't exist, but don't redirect - just show empty state
            // The user might have a valid hashed ID that just needs to be resolved
            console.warn('Session not found (404), but continuing to show page');
            setMessages([]);
            setCurrentSessionId(initialSessionId); // Keep the hashed ID for now
            setHasInteracted(true);
          } else {
            // Other errors - still show the page but log the error
            console.error('Failed to load session:', err);
            setMessages([]);
            setCurrentSessionId(initialSessionId);
            setHasInteracted(true);
          }
        }
      };
      loadInitialSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSessionId, isAuthChecked, customerId]);

  // Debug: Log when messages change
  useEffect(() => {
    if (initialSessionId) {
      console.log('Messages state updated:', {
        messageCount: messages.length,
        initialSessionId,
        currentSessionId,
        hasInteracted,
        isLoadingSession
      });
      if (messages.length > 0) {
        console.log('First message:', messages[0]);
      }
    }
  }, [messages, initialSessionId, currentSessionId, hasInteracted, isLoadingSession]);

  // Load chat sessions (minimal data: title, lastActivity) when customerId is available
  // This loads on mount, not just when sidebar opens, since sidebar may always be open
  useEffect(() => {
    if (customerId && isAuthChecked && chatSessions.length === 0 && !sessionsLoading) {
      // Try cache first for instant display
      const cachedSessions = loadChatSessionsFromCache(customerId);
      if (cachedSessions && cachedSessions.length > 0) {
        setChatSessions(cachedSessions);
        // Fetch fresh data in background (non-blocking)
        loadChatSessions(customerId, false);
      } else {
        // No cache, fetch from API (only minimal data: title, lastActivity)
        loadChatSessions(customerId, false);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId, isAuthChecked]);

  useEffect(() => {
    const saved = localStorage.getItem('healthProfile');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setProfile({ ...defaultProfile, ...parsed });
      } catch (err) {
        console.warn('Unable to parse saved profile', err);
        setProfile(defaultProfile);
      }
    }
    setProfileLoading(false);
  }, []);

  useEffect(() => {
    localStorage.setItem('healthProfile', JSON.stringify(profile));
  }, [profile]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    const handleScroll = () => {
      if (!container) return;
      container.dataset.scrolled = container.scrollTop > 24 ? 'true' : 'false';
    };
    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    return () => {
      if (shareFeedbackTimeoutRef.current) {
        clearTimeout(shareFeedbackTimeoutRef.current);
      }
    };
  }, []);

  const profileStats = useMemo(() => {
    const chronicConditions = [
      profile.diabetes && 'Diabetes',
      profile.hypertension && 'Hypertension',
      profile.pregnancy && 'Pregnancy',
    ]
      .filter(Boolean)
      .join(', ');

    return [
      {
        label: 'Age',
        value: profile.age ? `${profile.age} years` : 'Not provided',
        icon: <CalendarDays className="h-4 w-4" aria-hidden />,
      },
      {
        label: 'Sex',
        value: profile.sex ? profile.sex : 'Not provided',
        icon: <Stethoscope className="h-4 w-4" aria-hidden />,
      },
      {
        label: 'Chronic',
        value: chronicConditions || 'No chronic conditions logged',
        highlights: chronicConditions ? chronicConditions.split(', ') : undefined,
        icon: <Heart className="h-4 w-4" aria-hidden />,
      },
      {
        label: 'City',
        value: profile.city && profile.city.trim().length > 0 ? profile.city : 'Not provided',
        icon: <MapPin className="h-4 w-4" aria-hidden />,
      },
    ];
  }, [profile]);

  const profileName = useMemo(() => {
    if (profile.city) {
      return `${profile.city} Resident`;
    }
    return 'Guest Member';
  }, [profile.city]);

  const avatarColor: 'teal' | 'mint' | 'blue' =
    profile.diabetes || profile.hypertension ? 'blue' : 'teal';

  // Define handleSend before useCallback hooks that depend on it
  const handleSend = useCallback(async (overrides?: string) => {
    const messageText = (overrides ?? inputValue).trim();
    if (!messageText || isLoading) return;

    // Update activity timestamp on send
    updateActivity();
    setHasInteracted(true);

    const userMessage: ChatEntry = {
      id: createId(),
      role: 'user',
      content: messageText,
      timestamp: formatTimestamp(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      // Create assistant message placeholder for streaming
      const assistantMessageId = createId();
      const assistantMessage: ChatEntry = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: formatTimestamp(),
        citations: [],
        facts: [],
        safety: undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Get API base URL
      const apiBaseUrl = API_BASE;
      
      // Create request body
      const requestBody = {
        text: messageText,
        lang,
        profile,
        session_id: currentSessionId,
      };

      // Use fetch for Server-Sent Events (SSE) streaming
      // Get auth token from cookies (apiClient handles this automatically)
      const response = await fetch(`${apiBaseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        } as Record<string, string>, // Explicit type for TypeScript
        credentials: 'include', // Important for cookie-based auth
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      // Explicitly use UTF-8 decoder for proper non-English character handling
      const decoder = new TextDecoder('utf-8', { fatal: false, ignoreBOM: true });
      let buffer = '';
      let accumulatedContent = '';
      let translatedStarted = false;

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              // Check for session_id in any event type and update URL early (before streaming completes)
              if (data.metadata?.session_id && !currentSessionId) {
                const newSessionId = data.metadata.session_id;
                setCurrentSessionId(newSessionId);
                // Hash the session ID for URL
                const { hashSessionId } = await import('../utils/sessionHash');
                const hashedId = await hashSessionId(newSessionId);
                // Update URL without full page reload using history API only
                // Don't use router.replace/push as it causes Next.js to remount the component
                if (typeof window !== 'undefined' && window.location.pathname === '/') {
                  // Use history.pushState to update URL without triggering Next.js navigation
                  // This prevents the component from remounting and losing state
                  window.history.pushState({ sessionId: newSessionId, hashedId }, '', `/${hashedId}`);
                }
              }
              
              if (data.type === 'translated_start') {
                // Clear the accumulated English content when translation starts
                // This replaces the English loading indicator with translated content
                translatedStarted = true;
                accumulatedContent = '';
              } else if (data.type === 'chunk') {
                // Append chunk to accumulated content
                if (translatedStarted && accumulatedContent === '') {
                  // Start fresh with translated content
                  accumulatedContent = data.content || '';
                } else {
                  accumulatedContent += data.content || '';
                }
                
                // Update the message in real-time (typewriter effect)
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  )
                );
              } else if (data.type === 'translated') {
                // Replace with translated content (legacy support)
                translatedStarted = true;
                accumulatedContent = data.content || accumulatedContent;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  )
                );
              } else if (data.type === 'done') {
                // Final message with metadata
                const finalContent = data.answer || accumulatedContent;
                const citations = Array.isArray(data.citations) ? data.citations : (data.citations ? [data.citations] : []);
                
                console.log('📋 Received "done" event with citations:', {
                  citationsCount: citations.length,
                  citations: citations,
                  hasCitations: !!data.citations,
                  citationsType: typeof data.citations,
                  dataKeys: Object.keys(data)
                });
                
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? {
                          ...msg,
                          content: finalContent,
                          citations: citations,
                          facts: data.facts || [],
                          safety: data.safety,
                        }
                      : msg
                  )
                );

                console.log('✅ Updated message with citations:', citations.length);

                // Update session ID if provided (URL already updated earlier if it was a new session)
                if (data.metadata?.session_id) {
                  const newSessionId = data.metadata.session_id;
                  if (!currentSessionId || currentSessionId !== newSessionId) {
                    setCurrentSessionId(newSessionId);
                    // Only update URL if we haven't already (to avoid double navigation)
                    const { hashSessionId } = await import('../utils/sessionHash');
                    const hashedId = await hashSessionId(newSessionId);
                    if (typeof window !== 'undefined' && window.location.pathname === '/') {
                      // Use history.pushState to update URL without triggering Next.js navigation
                      // This prevents the component from remounting and losing state
                      window.history.pushState({ sessionId: newSessionId, hashedId }, '', `/${hashedId}`);
                    }
                  }
                }

                // Reload chat sessions after receiving response (immediate load after message)
                if (customerId) {
                  try {
                    const cacheKey = `chat_sessions_${customerId}`;
                    localStorage.removeItem(cacheKey);
                  } catch (err) {
                    console.warn('Error clearing cache:', err);
                  }
                  // Load immediately after sending message (not debounced)
                  loadChatSessions(customerId, true);
                }

                // Text-to-speech is now handled per-message via user interaction (removed auto-narration)
              }
            } catch (parseError) {
              console.warn('Error parsing SSE data:', parseError);
            }
          }
        }
      }
    } catch (err) {
      console.error('Chat error', err);
      setError(
        'I had trouble connecting to my clinical sources. Please check your network and try again.'
      );
      setMessages((prev) => [
        ...prev,
        {
          id: createId(),
          role: 'assistant',
          content:
            'I’m sorry—something went wrong while retrieving information. Let’s try again in a few moments.',
          timestamp: formatTimestamp(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputValue, isLoading, lang, profile, currentSessionId, customerId]);

  const handleDismissError = useCallback(() => {
    setError(null);
  }, []);

  const scheduleShareFeedback = useCallback((message: string | null, duration = 3200) => {
    if (shareFeedbackTimeoutRef.current) {
      clearTimeout(shareFeedbackTimeoutRef.current);
      shareFeedbackTimeoutRef.current = null;
    }
    setShareFeedback(message);
    if (message) {
      shareFeedbackTimeoutRef.current = window.setTimeout(() => {
        setShareFeedback(null);
        shareFeedbackTimeoutRef.current = null;
      }, duration);
    }
  }, []);


  const handleShareConversation = useCallback(async () => {
    if (typeof navigator === 'undefined') {
      scheduleShareFeedback('Sharing is unavailable in this environment.');
      return;
    }
    const conversation = messages
      .filter((entry) => entry.content.trim().length > 0)
      .map((entry) => `${entry.role === 'assistant' ? 'Care Guide' : 'You'}: ${entry.content.trim()}`)
      .join('\n\n');

    if (!conversation) {
      scheduleShareFeedback('Start a conversation to share the session.');
      return;
    }

    try {
      if (navigator.share) {
        await navigator.share({
          title: 'Health Companion Conversation',
          text: conversation,
        });
        scheduleShareFeedback('Conversation shared successfully.');
      } else {
        await navigator.clipboard.writeText(conversation);
        scheduleShareFeedback('Conversation copied to clipboard.');
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('Share error', err);
        scheduleShareFeedback('Unable to share conversation.');
      }
    }
  }, [messages, scheduleShareFeedback]);

  const sidebarClasses = useMemo(
    () =>
      clsx(
        // Mobile-first: Full width on mobile, fixed width on desktop
        'fixed inset-y-0 left-0 z-40 flex w-full flex-col gap-3 border-r border-white/10 bg-slate-900/95 px-3 py-4 shadow-[0_0_60px_rgba(16,185,129,0.18)] transition-transform duration-300 backdrop-blur-xl',
        'sm:w-72 sm:px-4 sm:py-6 sm:gap-4',
        'md:gap-6 md:px-6',
        'lg:z-30 lg:bg-slate-900/50 lg:shadow-none lg:w-72',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
      ),
    [isSidebarOpen]
  );

  const mainLayoutClasses = useMemo(
    () =>
      clsx(
        'flex min-h-screen flex-col transition-[margin] duration-300',
        'w-full overflow-x-hidden', // Prevent horizontal scroll
        isSidebarOpen ? 'lg:ml-72' : 'lg:ml-16',
        'px-0 sm:px-0'
      ),
    [isSidebarOpen]
  );

  const bottomBarClasses = useMemo(
    () =>
      clsx(
        'fixed bottom-0 left-0 right-0 z-40 px-3 pb-4 pt-2.5',
        'sm:px-4 sm:pb-5 sm:pt-3',
        'lg:px-10 lg:pb-6 lg:pt-3',
        'transition-[left] duration-300 w-full max-w-full overflow-x-hidden',
        // Hide on mobile when sidebar is open, always show on desktop
        isSidebarOpen ? 'hidden lg:block lg:left-72' : 'block lg:left-16'
      ),
    [isSidebarOpen]
  );

  const collapseRailClasses = useMemo(
    () =>
      clsx(
        'fixed inset-y-0 left-0 z-30 hidden w-16 flex-col items-center justify-between border-r border-white/10 bg-slate-900/60 px-2 py-6 shadow-[0_0_40px_rgba(16,185,129,0.18)] transition-transform duration-300 backdrop-blur-xl lg:flex',
        isSidebarOpen ? '-translate-x-full opacity-0 pointer-events-none' : 'translate-x-0 opacity-100'
      ),
    [isSidebarOpen]
  );

  const transcribeAudio = useCallback(async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'voice-note.webm');

      const response = await apiClient.post('/stt', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const text: string = response.data.text;
      if (text) {
        setInputValue(text);
        await handleSend(text);
      }
    } catch (err) {
      console.error('Transcription error', err);
      setError(
        'Speech recognition did not succeed. You can continue by typing your question.'
      );
    }
  }, [handleSend]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }
    const media = window.matchMedia('(min-width: 1024px)');
    const handleChange = () => {
      setIsDesktop(media.matches);
      setIsSidebarOpen(media.matches);
    };
    handleChange();
    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, []);

  // Show proper loading screen when redirecting due to auth failure
  if (isRedirecting) {
    return <QuickLoader />;
  }

  // Don't render anything until auth check is complete
  // If we have initialSessionId, render the full layout immediately (auth check happens in background)
  // This ensures the loading animation shows in the proper context, not on a blank screen
  if (!isAuthChecked && !initialSessionId) {
    return <QuickLoader />;
  }

  // Handle welcome screen completion
  const handleWelcomeComplete = () => {
    setShowWelcome(false);
  };

  const startRecording = async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices) {
      setError('Microphone access is not available in this environment.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        await transcribeAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone error', err);
      setError('Could not access the microphone. Please check browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    updateActivity(); // Update activity on key press
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  };

  const selectedPlaceholder = currentLanguage.placeholder;

  const handleOpenProfileModal = () => {
    setShowPreferences(false);
    setShowProfile(true);
  };

  const handleDeleteSession = async (sessionId: string) => {
    // Open confirmation modal
    setDeleteConfirmModal({ isOpen: true, sessionId });
  };

  const confirmDeleteSession = async () => {
    const sessionId = deleteConfirmModal.sessionId;
    if (!sessionId) return;

    try {
      await apiClient.delete(`/session/${sessionId}`);
      
      // Remove from local state
      setChatSessions((prev) => prev.filter((s) => s.id !== sessionId));
      
      // Clear browser cache for this customer's sessions
      if (customerId) {
        try {
          const cacheKey = `chat_sessions_${customerId}`;
          localStorage.removeItem(cacheKey);
        } catch (err) {
          console.warn('Error clearing browser cache:', err);
        }
      }
      
      // If this was the active session, clear it
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
        setHasInteracted(false);
      }
    } catch (err: any) {
      console.error('Error deleting session:', err);
      setError('Failed to delete chat session');
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    // Hash the session ID for URL and navigate to session route
    const { hashSessionId } = await import('../utils/sessionHash');
    const hashedId = await hashSessionId(sessionId);
    router.push(`/${hashedId}`);
  };

  return (
    <>
      {showWelcome && <WelcomeScreen onComplete={handleWelcomeComplete} />}
      <SearchChatsModal
        isOpen={showSearchChats}
        onClose={() => setShowSearchChats(false)}
        onSelectSession={handleSelectSession}
        customerId={customerId}
      />
      <ConfirmDeleteModal
        isOpen={deleteConfirmModal.isOpen}
        onClose={() => setDeleteConfirmModal({ isOpen: false, sessionId: null })}
        onConfirm={confirmDeleteSession}
      />
      <div className="relative min-h-screen overflow-hidden bg-slate-900 text-slate-100">
        {/* Consistent background matching landing page - brighter and more visible */}
        <div className="pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_15%_20%,rgba(16,185,129,0.40),transparent_55%),radial-gradient(circle_at_85%_15%,rgba(34,197,94,0.38),transparent_55%),radial-gradient(circle_at_50%_100%,rgba(16,185,129,0.35),transparent_60%),radial-gradient(circle_at_20%_90%,rgba(34,197,94,0.32),transparent_55%)]" />
        <div className="pointer-events-none absolute top-[-8rem] left-[-6rem] h-72 w-72 rounded-full bg-emerald-500/45 opacity-70 mix-blend-screen blur-3xl" />
        <div className="pointer-events-none absolute top-[-4rem] right-[-4rem] h-64 w-64 rounded-full bg-green-500/40 opacity-70 mix-blend-screen blur-3xl" />
        <div className="pointer-events-none absolute bottom-[-6rem] right-[-10rem] h-80 w-80 rounded-full bg-teal-500/45 opacity-70 mix-blend-screen blur-3xl" />
        <div className="pointer-events-none absolute bottom-[-8rem] left-[-8rem] h-72 w-72 rounded-full bg-emerald-500/40 opacity-70 mix-blend-screen blur-3xl" />
        <div className="relative z-10">
      <aside
        className={sidebarClasses}
        aria-label="Primary navigation"
        aria-hidden={!isSidebarOpen && isDesktop}
        id="primary-navigation"
        data-overlay={isSidebarOpen && !isDesktop}
      >
        <div className="flex items-center gap-2 pt-12 sm:pt-0 sm:flex">
          <span className="flex-shrink-0 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 p-1.5 text-white shadow-[0_0_25px_rgba(16,185,129,0.45)] sm:p-2">
            <Sparkle className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden />
          </span>
          <div className="flex-1 min-w-0 overflow-hidden">
            <p className="mt-0.5 sm:mt-0 text-[0.6rem] sm:text-xs font-semibold uppercase tracking-[0.28em] sm:tracking-[0.32em] text-emerald-300/80 whitespace-normal break-words leading-tight">
              Wellness mode
            </p>
            <p className="text-xs sm:text-sm md:text-base font-semibold text-white whitespace-normal break-words leading-tight truncate">
              Care Console
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsSidebarOpen(false)}
            className="flex-shrink-0 rounded-full border border-white/20 p-2 min-h-[44px] min-w-[44px] flex items-center justify-center text-slate-400 transition hover:border-white/40 hover:bg-slate-800/50 hover:text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden />
          </button>
        </div>

        <div className="flex-1 flex flex-col min-h-0 pt-8 sm:pt-4">
          <div className="flex-shrink-0">
            <button
              type="button"
              onClick={() => {
                router.push('/');
              }}
              className="flex w-full items-center gap-2.5 rounded-lg border border-white/10 bg-slate-800/50 px-3 py-3 min-h-[44px] text-xs sm:text-sm font-medium text-slate-200 transition hover:border-emerald-400/50 hover:bg-slate-800/70 hover:text-white mb-2 sm:mb-1"
            >
              <Plus className="h-4 w-4 flex-shrink-0" />
              <span className="truncate">New chat</span>
            </button>

            <button
              type="button"
              onClick={() => setShowSearchChats(true)}
              className="flex w-full items-center gap-2.5 rounded-lg border border-white/10 bg-slate-800/50 px-3 py-3 min-h-[44px] text-xs sm:text-sm font-medium text-slate-200 transition hover:border-emerald-400/50 hover:bg-slate-800/70 hover:text-white mb-4 sm:mb-5"
            >
              <Search className="h-4 w-4 flex-shrink-0" />
              <span className="truncate">Search chats</span>
            </button>
          </div>

          <div className="flex-1 flex flex-col min-h-0 pt-2">
            <p className="mb-2 px-2 sm:px-3 text-[0.65rem] sm:text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 flex-shrink-0">Chats</p>
            <div className="overflow-y-auto overflow-x-hidden space-y-1 max-h-[280px] sm:max-h-[320px] scrollbar-hide px-1 sm:px-0">
              {sessionsLoading ? (
                <div className="px-3">
                  <LoadingSkeleton variant="chatHistory" count={3} />
                </div>
              ) : chatSessions.length === 0 ? (
                <div className="rounded-lg px-3 py-2 text-sm text-slate-300">
                  No chat history yet
                </div>
              ) : (
                chatSessions.map((session) => {
                  const formatDate = (dateString: string) => {
                    const date = new Date(dateString);
                    const now = new Date();
                    // Calculate difference in milliseconds (works correctly with UTC timestamps)
                    const diffMs = now.getTime() - date.getTime();
                    const diffMins = Math.floor(diffMs / 60000);
                    const diffHours = Math.floor(diffMs / 3600000);
                    const diffDays = Math.floor(diffMs / 86400000);

                    if (diffMins < 1) return 'Just now';
                    if (diffMins < 60) return `${diffMins}m ago`;
                    if (diffHours < 24) return `${diffHours}h ago`;
                    if (diffDays < 7) return `${diffDays}d ago`;
                    // Format date in IST timezone
                    return date.toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata" });
                  };

                  const isActive = currentSessionId === session.id;
                  const sessionTitle = session.firstMessage 
                    ? (session.firstMessage.length > 40 
                        ? session.firstMessage.substring(0, 40) + '...' 
                        : session.firstMessage)
                    : 'New conversation';

                  return (
                    <div
                      key={session.id}
                      className={clsx(
                        'group relative flex items-center gap-2 rounded-lg transition overflow-hidden w-full',
                        isActive
                          ? 'bg-emerald-500/20 border border-emerald-400/30'
                          : 'border border-transparent hover:bg-slate-800/50'
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => handleSelectSession(session.id)}
                        className={clsx(
                          'flex-1 rounded-lg px-2.5 sm:px-3 py-2.5 min-h-[44px] text-left text-xs sm:text-sm transition overflow-hidden',
                          isActive
                            ? 'text-emerald-200'
                            : 'text-slate-300 hover:text-white'
                        )}
                      >
                        <div className="flex items-start justify-between gap-2 w-full">
                          <div className="flex-1 min-w-0 overflow-hidden">
                            <p className="text-[0.65rem] sm:text-xs text-slate-400 mb-1 truncate">
                              {formatDate(session.lastActivityAt || session.createdAt)}
                            </p>
                            <p className="font-medium truncate text-xs sm:text-sm leading-tight">
                              {sessionTitle}
                            </p>
                            {session.language && (
                              <p className="text-[0.65rem] sm:text-xs text-emerald-400/70 mt-1 truncate">
                                {session.language.toUpperCase()}
                              </p>
                            )}
                          </div>
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSession(session.id);
                        }}
                        className={clsx(
                          'flex-shrink-0 rounded-lg p-2 min-h-[44px] min-w-[44px] flex items-center justify-center transition opacity-0 group-hover:opacity-100',
                          'text-slate-400 hover:text-red-400 hover:bg-red-500/10',
                          isActive && 'opacity-100'
                        )}
                        aria-label="Delete session"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {error && !hasInteracted && (
            <div className="flex-shrink-0 pt-2">
              <ErrorCallout message={error} onDismiss={handleDismissError} />
            </div>
          )}
        </div>

        <div className="flex-shrink-0 mt-auto border-t border-white/10 pt-3 sm:pt-4 pb-4 sm:pb-0">
          <div className="flex items-center gap-2.5 sm:gap-3 px-2 sm:px-3 py-2">
            <div className="flex h-8 w-8 sm:h-9 sm:w-9 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-xs font-semibold text-white">
              <User className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </div>
            <div className="flex-1 min-w-0 overflow-hidden">
              <p className="text-xs sm:text-sm font-medium text-white truncate">
                {userDisplayName}
              </p>
              <p className="text-[0.65rem] sm:text-xs text-slate-400">Free</p>
            </div>
          </div>
          <button
            type="button"
            onClick={async () => {
              try {
                // Call backend logout endpoint to revoke refresh token and clear cookies
                await apiClient.post('/auth/logout');
              } catch (error) {
                // Log error but continue with logout even if backend call fails
                console.warn('Logout API call failed, continuing with local logout:', error);
              } finally {
                // Clear all auth-related data and redirect to landing
                clearAuth();
                router.push('/landing');
              }
            }}
            className="mt-2 flex w-full items-center gap-2.5 sm:gap-3 rounded-lg border border-white/10 bg-slate-800/50 px-3 py-3 min-h-[44px] text-xs sm:text-sm font-medium text-slate-200 transition hover:border-red-400/50 hover:bg-slate-800/70 hover:text-red-200"
          >
            <LogOut className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">Logout</span>
          </button>
        </div>
      </aside>

      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className={collapseRailClasses} aria-hidden={isSidebarOpen}>
            <button
                type="button"
          onClick={() => setIsSidebarOpen(true)}
          className="flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-slate-900/70 text-white shadow-[0_0_35px_rgba(16,185,129,0.3)] transition hover:border-emerald-400/70 hover:text-emerald-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
              >
          <Sparkle className="h-5 w-5 text-emerald-300" aria-hidden />
            </button>
              <button
                type="button"
          onClick={() => setIsSidebarOpen(true)}
          className="flex flex-col items-center gap-1 text-xs font-semibold uppercase tracking-[0.32em] text-emerald-300"
        >
          <Menu className="h-4 w-4" aria-hidden />
          Open
              </button>
      </div>

      <div className={mainLayoutClasses}>
        <header className={clsx(
          "fixed top-0 z-[100] flex items-center justify-between border-b border-white/10 bg-slate-900/95 backdrop-blur-xl px-2.5 py-2.5 shadow-[0_25px_60px_rgba(15,23,42,0.75)] transition-[left] duration-300",
          "sm:px-3 sm:py-3",
          "md:px-4 md:py-4",
          "lg:px-6",
          "xl:px-10",
          isSidebarOpen ? 'lg:left-72' : 'lg:left-16',
          'left-0 right-0 lg:right-0 w-full max-w-full overflow-x-hidden'
        )}>
          <div className="flex items-center gap-1.5 sm:gap-2 md:gap-3 min-w-0 flex-1">
          <button
                type="button"
              onClick={() => setIsSidebarOpen(true)}
              aria-expanded={isSidebarOpen}
              aria-controls="primary-navigation"
              className="inline-flex items-center justify-center gap-1 rounded-full border border-white/10 bg-slate-900/70 px-2 py-2 min-h-[44px] min-w-[44px] text-xs font-semibold text-slate-200 shadow-[0_0_25px_rgba(16,185,129,0.18)] transition hover:border-emerald-400/70 hover:text-emerald-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 sm:gap-1.5 sm:px-2.5 sm:py-2 sm:text-sm lg:hidden"
            >
              <Menu className="h-4 w-4 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
              <span className="hidden xs:inline text-xs">Menu</span>
          </button>
              <div className="min-w-0 flex-1">
              <p className="hidden text-[0.6rem] font-semibold uppercase tracking-[0.28em] text-emerald-300/75 sm:block sm:text-xs sm:tracking-[0.32em]">Live care session</p>
              <h1 className="text-sm sm:text-base md:text-lg lg:text-xl font-semibold text-white truncate">
                <span className="sm:hidden">WellNess AI</span>
                <span className="hidden sm:inline">WellNess Health Companion</span>
              </h1>
            </div>
              </div>
              <div className="flex flex-col items-end gap-1 sm:flex-row sm:items-center sm:gap-1.5 md:gap-2 lg:gap-3 flex-shrink-0">
                <div className="flex items-center gap-1 sm:gap-1.5 md:gap-2 lg:gap-3 flex-wrap justify-end">
                  <button
                    type="button"
                    onClick={() => setShowPreferences(true)}
                    className="inline-flex items-center justify-center gap-1 rounded-full border border-white/10 bg-slate-900/70 px-2 py-2 min-h-[44px] text-[0.65rem] font-semibold text-slate-100 shadow-[0_0_25px_rgba(16,185,129,0.18)] transition hover:border-emerald-400/70 hover:text-emerald-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 sm:gap-1.5 sm:px-2.5 sm:py-2 sm:text-xs"
                    title="Session preferences"
                  >
                    <Settings className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                    <span className="hidden sm:inline">Preferences</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowSafety(true)}
                    className="inline-flex items-center justify-center gap-1 rounded-full border border-white/10 bg-slate-900/70 px-2 py-2 min-h-[44px] text-[0.65rem] font-semibold text-slate-100 shadow-[0_0_25px_rgba(34,197,94,0.18)] transition hover:border-green-400/70 hover:text-green-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-300 sm:gap-1.5 sm:px-2.5 sm:py-2 sm:text-xs"
                    title="Safety guidance"
                  >
                    <HeartPulse className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                    <span className="hidden sm:inline">Safety</span>
                  </button>
                  {/* Share button removed per request */}
                  <button
                    type="button"
                    onClick={toggleNarration}
                    className={clsx(
                      "inline-flex items-center justify-center gap-1 rounded-full border px-2 py-2 min-h-[44px] text-[0.65rem] font-semibold shadow-[0_0_25px_rgba(16,185,129,0.18)] transition sm:gap-1.5 sm:px-2.5 sm:py-2 sm:text-xs",
                      narrationEnabled
                        ? "border-emerald-400/60 bg-slate-900/70 text-emerald-100 hover:border-emerald-300/80"
                        : "border-white/10 bg-slate-900/70 text-slate-100 hover:border-white/20"
                    )}
                    title={narrationEnabled ? "Narration: On" : "Narration: Off"}
                    aria-pressed={narrationEnabled}
                  >
                    {narrationEnabled ? (
                      <Volume2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                    ) : (
                      <VolumeX className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                    )}
                    <span className="hidden sm:inline">{narrationEnabled ? "Narration On" : "Narration Off"}</span>
                  </button>
                  <button
                    type="button"
                    onClick={stopNarration}
                    className="inline-flex items-center justify-center gap-1 rounded-full border border-white/10 bg-slate-900/70 px-2 py-2 min-h-[44px] text-[0.65rem] font-semibold text-slate-100 shadow-[0_0_25px_rgba(16,185,129,0.18)] transition hover:border-red-300/70 hover:text-red-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-300 sm:gap-1.5 sm:px-2.5 sm:py-2 sm:text-xs"
                    title="Stop narration"
                  >
                    <X className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                    <span className="hidden sm:inline">Stop</span>
                  </button>
                  {/* Online status chip removed per request */}
                </div>
                {shareFeedback && (
                  <p className="text-[0.65rem] sm:text-xs text-emerald-200/80 truncate max-w-[120px] sm:max-w-none" aria-live="polite">
                    {shareFeedback}
                  </p>
                )}
              </div>
        </header>

        <main className="flex-1 px-2.5 sm:px-3 md:px-4 lg:px-6 xl:px-10 pb-24 sm:pb-28 md:pb-32 pt-16 sm:pt-20 md:pt-24 lg:pt-28 w-full max-w-full overflow-x-hidden">
          <div className="mx-auto flex h-full max-w-4xl flex-col gap-3 sm:gap-4 md:gap-6 w-full">
            {messages.length === 0 && !initialSessionId && !isLoading && !isLoadingSession && (
              <section className="relative overflow-hidden rounded-xl sm:rounded-2xl border border-white/10 bg-slate-900/60 px-3 py-4 shadow-[0_35px_90px_rgba(15,23,42,0.65)] backdrop-blur-xl sm:px-4 sm:py-5 md:rounded-2xl md:px-5 md:py-6 lg:px-6 xl:px-8 w-full max-w-full">
                <div
                  className="absolute inset-y-0 right-0 w-[55%] opacity-60 blur-3xl bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500"
                  aria-hidden
                />
                <div className="relative flex flex-col gap-3 sm:gap-4 md:gap-5">
                  <div className="flex items-center gap-1.5 sm:gap-2 text-[0.6rem] sm:text-[0.65rem] font-semibold uppercase tracking-[0.28em] sm:tracking-[0.32em] text-emerald-300/80">
                    <span className="flex h-1.5 w-1.5 sm:h-2 sm:w-2 rounded-full bg-emerald-400 flex-shrink-0" aria-hidden />
                    <span>Ready when you are</span>
                  </div>
                  <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl font-bold text-white leading-tight">
                    How can I care for you today?
                  </h2>
                  <p className="max-w-3xl text-sm sm:text-xs md:text-sm lg:text-base leading-relaxed text-slate-200">
                    Share what's on your mind—symptoms you're noticing, questions about self-care, or worries about emergencies. I'll
                    help you navigate next steps with calm, clinically aligned guidance.
                  </p>
                  <div className="w-full max-w-full">
                    <TopicSuggestions
                      onSuggestionSelect={(prompt) => {
                        void handleSend(prompt);
                      }}
                    />
                  </div>
                  <div className="flex items-start gap-2 sm:gap-3 rounded-xl sm:rounded-2xl border border-emerald-400/40 bg-gradient-to-r from-emerald-500/20 via-green-500/10 to-teal-500/20 px-3 py-2.5 sm:px-4 sm:py-3 text-emerald-100 shadow-[0_18px_45px_rgba(16,185,129,0.18)]">
                    <span className="mt-0.5 sm:mt-1 flex h-2.5 w-2.5 sm:h-3 sm:w-3 rounded-full bg-white/80 flex-shrink-0" aria-hidden />
                    <p className="text-xs sm:text-sm leading-relaxed text-emerald-50">
                      I'm a virtual companion for everyday care—not a substitute for emergency services or licensed clinicians. If you
                      feel unsafe or notice severe symptoms, please seek urgent medical attention immediately.
                    </p>
                  </div>
                </div>
              </section>
            )}

            {(messages.length > 0 || initialSessionId || isLoadingSession) && (
            <section className="relative overflow-hidden flex-1 rounded-[28px] border border-white/10 bg-slate-900/55 shadow-[0_35px_90px_rgba(15,23,42,0.65)] backdrop-blur-xl">
              <div
                className="absolute inset-y-0 right-0 w-[45%] opacity-60 blur-3xl bg-gradient-to-br from-teal-500 via-green-500 to-emerald-500"
                aria-hidden
              />
              <div className="relative flex h-full flex-col">
                <div
                  ref={scrollContainerRef}
                  className="flex-1 overflow-y-auto px-3 pt-12 pb-4 sm:px-5 sm:pt-16 lg:px-6 lg:pt-20"
                  aria-live="polite"
                  aria-busy={isLoading || isLoadingSession}
                >
                  {(isLoadingSession || (initialSessionId && messages.length === 0 && !isLoading)) && (
                    <div className="px-1 sm:px-2 lg:px-3">
                      <LoadingSkeleton variant="message" count={2} />
                    </div>
                  )}
                  <div
                    className="mx-auto flex w-full flex-col gap-4 px-1 pt-4 sm:px-2 sm:pt-6 lg:max-w-3xl lg:px-3 lg:pt-8"
                    role="list"
                    aria-live="polite"
                  >
        {messages.length > 0 && messages.map((message, index) => (
                  <div key={message.id} className="space-y-4">
                    <ChatMessage 
                      message={message} 
                      index={index} 
                      language={lang}
                      onFeedback={async (messageId, feedback) => {
                        try {
                          const response = await fetch(`${API_BASE}/message/${messageId}/feedback`, {
                            method: 'POST',
                            headers: {
                              'Content-Type': 'application/json',
                            },
                            credentials: 'include',
                            body: JSON.stringify({ feedback }),
                          });
                          if (!response.ok) {
                            console.warn('Failed to submit feedback');
                          }
                        } catch (error) {
                          console.warn('Error submitting feedback:', error);
                        }
                      }}
                    />

                    {message.safety?.red_flag && (
                      <div className="rounded-3xl border border-red-500/50 bg-red-500/10 p-5 text-red-200 shadow-[0_25px_70px_rgba(220,38,38,0.35)]">
                        <div className="flex items-start gap-3">
                          <AlertTriangle className="h-6 w-6 flex-shrink-0 text-red-300" />
                          <div className="space-y-3">
                            <div>
                              <h3 className="flex items-center gap-2 text-base font-bold text-white">
                                <span role="img" aria-hidden>
                                  ⚠️
                        </span>
                                Seek immediate medical care
                    </h3>
                              <p className="mt-1 text-sm text-red-200/80">
                                    Your symptoms may signal an urgent concern. If you feel unsafe right now, contact emergency services.
                              </p>
                            </div>
                            {message.facts
                              ?.find((fact: any) => fact.type === 'red_flags')
                              ?.data?.map((flag: any, idx: number) => (
                                <div
                                  key={`${flag.symptom}-${idx}`}
                                  className="rounded-2xl border border-red-500/40 bg-slate-950/60 p-3 text-sm text-red-200"
                                >
                                  <strong>{flag.symptom}</strong>: {flag.conditions.join(', ')}
                          </div>
                        ))}
                    <button
                      onClick={() => window.open('tel:108')}
                              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-red-500 px-4 py-2 font-semibold text-white shadow-[0_10px_40px_rgba(220,38,38,0.4)] transition hover:bg-red-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-300"
                    >
                              <Phone className="h-4 w-4" />
                              Call Emergency (108)
                    </button>
                  </div>
                </div>
              </div>
            )}

            {message.facts && message.facts.length > 0 && !message.safety?.red_flag && (
                      <div className="rounded-3xl border border-white/10 bg-slate-950/60 p-5 text-sm text-slate-100 shadow-[0_25px_60px_rgba(15,23,42,0.55)]">
                            <h4 className="text-sm font-semibold uppercase tracking-[0.32em] text-emerald-200">Additional insights</h4>
                        <div className="mt-3 space-y-3">
                          {message.facts.map((fact: any, factIndex: number) => {
                            if (!fact?.data || fact.data.length === 0) return null;

                            if (fact.type === 'contraindications') {
                              return (
                                <div
                                  key={`fact-${fact.type}-${factIndex}`}
                                  className="rounded-2xl border border-red-400/40 bg-red-500/10 p-3"
                                >
                                      <p className="font-semibold text-red-200">Things to avoid for safety</p>
                                  <ul className="mt-2 space-y-1 text-sm text-red-100/90">
                                    {fact.data.map((group: any, idx: number) => (
                                      <li key={`${group.condition}-${idx}`}>
                                            <strong>{group.condition}:</strong> {group.avoid.join(', ')}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              );
                            }

                            if (fact.type === 'safe_actions') {
                              return (
                                <div
                                  key={`fact-${fact.type}-${factIndex}`}
                                  className="rounded-2xl border border-emerald-400/40 bg-emerald-500/10 p-3"
                                >
                                      <p className="font-semibold text-emerald-200">Generally safe self-care ideas</p>
                                  <ul className="mt-2 space-y-1 text-sm text-emerald-100/90">
                                    {fact.data.map((group: any, idx: number) => (
                                      <li key={`${group.condition}-${idx}`}>
                                            <strong>{group.condition}:</strong> {group.actions.join(', ')}
                            </li>
                          ))}
                        </ul>
                      </div>
                              );
                            }

                            if (fact.type === 'providers') {
                              return (
                                <div
                                  key={`fact-${fact.type}-${factIndex}`}
                                  className="rounded-2xl border border-teal-400/40 bg-teal-500/10 p-3"
                                >
                                      <p className="font-semibold text-teal-200">Providers you might consider</p>
                                  <ul className="mt-2 space-y-1 text-sm text-teal-100/90">
                                    {fact.data.map((provider: any, idx: number) => (
                                      <li key={`${provider.provider}-${idx}`}>
                                        <strong>{provider.provider}</strong>
                                            {provider.mode ? ` - ${provider.mode}` : ''}
                                            {provider.phone ? ` - ${provider.phone}` : ''}
                            </li>
                          ))}
                        </ul>
                      </div>
                              );
                            }

                            if (fact.type === 'mental_health_crisis') {
                              return (
                                <div
                                  key={`fact-${fact.type}-${factIndex}`}
                                      className="rounded-2xl border border-sky-400/40 bg-sky-500/10 p-3"
                                    >
                                      <p className="font-semibold text-sky-200">Mental health first aid</p>
                                      <ul className="mt-2 space-y-1 text-sm text-sky-100/90">
                                    {fact.data.actions?.map((action: string, idx: number) => (
                                      <li key={`${action}-${idx}`}>{action}</li>
                                        )) || null}
                                  </ul>
                                </div>
                              );
                            }

                            if (fact.type === 'pregnancy_alert') {
                              return (
                                <div
                                  key={`fact-${fact.type}-${factIndex}`}
                                      className="rounded-2xl border border-green-400/40 bg-green-500/10 p-3"
                                    >
                                      <p className="font-semibold text-green-200">Pregnancy considerations</p>
                                      <ul className="mt-2 space-y-1 text-sm text-green-100/90">
                                        {Array.isArray(fact.data.guidance)
                                          ? fact.data.guidance.map((item: string, idx: number) => (
                                              <li key={`${item}-${idx}`}>{item}</li>
                                            ))
                                          : null}
                                  </ul>
                                </div>
                              );
                            }

                            return null;
                          })}
                        </div>
              </div>
            )}
          </div>
        ))}
                    {error && !isLoading && (
                      <div className="mt-2">
                        <ErrorCallout message={error} onDismiss={handleDismissError} />
                      </div>
                    )}
        <div ref={messagesEndRef} />
                  </div>
                </div>
              </div>
            </section>
            )}
          </div>
        </main>
      </div>

        <div className={bottomBarClasses} style={{ pointerEvents: 'none' }}>
          <form
            className="mx-auto flex w-full max-w-4xl flex-wrap items-end gap-2 rounded-xl sm:rounded-2xl border border-white/10 bg-slate-900/70 px-2.5 py-2.5 shadow-[0_28px_80px_rgba(16,185,129,0.25)] backdrop-blur-xl sm:flex-nowrap sm:gap-3 sm:rounded-[32px] sm:px-3 sm:py-3 md:px-4 md:py-4 lg:px-6 max-w-full overflow-x-hidden"
            style={{ pointerEvents: 'auto' }}
            onSubmit={(event) => {
              event.preventDefault();
              void handleSend();
            }}
          >
            

            <div className="relative flex-1 min-w-0">
              <textarea
                value={inputValue}
                onChange={(event) => {
                  setInputValue(event.target.value);
                  updateActivity(); // Update activity on typing
                }}
                onKeyDown={(event) => {
                  updateActivity(); // Update activity on key press
                  handleKeyDown(event);
                }}
                placeholder={selectedPlaceholder}
                rows={2}
                className="min-h-[56px] w-full resize-none rounded-xl border border-white/10 bg-transparent px-3 py-2.5 text-sm leading-relaxed text-slate-100 shadow-inner shadow-black/20 transition placeholder:text-slate-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400/80 sm:min-h-[64px] sm:rounded-2xl sm:px-4 sm:py-3 sm:text-base sm:rows-3"
                aria-label="Write your question"
                disabled={isLoading}
              />
              <span className="pointer-events-none absolute bottom-2 right-3 text-[0.65rem] text-slate-500 sm:bottom-3 sm:right-4 sm:text-xs">
                Shift + Enter for new line
              </span>
            </div>

            <button
              type="submit"
              className="flex h-12 w-12 sm:h-14 sm:w-14 flex-shrink-0 items-center justify-center rounded-full border border-transparent bg-gradient-to-br from-green-500 via-emerald-500 to-teal-500 text-white shadow-[0_18px_45px_rgba(16,185,129,0.35)] transition hover:scale-[1.05] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 min-h-[48px] min-w-[48px]"
              disabled={isLoading}
              aria-label="Send message"
            >
              <SendHorizonal className={clsx('h-5 w-5 sm:h-5 sm:w-5', isLoading ? 'animate-pulse' : '')} aria-hidden />
            </button>
          </form>
        </div>

      {showPreferences && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-3 sm:px-4 py-4 sm:py-8 backdrop-blur-sm overflow-y-auto">
          <section
            className="relative w-full max-w-2xl overflow-hidden rounded-2xl sm:rounded-3xl border border-white/10 bg-slate-900/70 p-4 sm:p-6 md:p-8 shadow-[0_35px_90px_rgba(15,23,42,0.65)] backdrop-blur-xl my-auto max-h-[90vh] overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-label="Session preferences"
          >
            <div
              className="absolute inset-0 -z-10 opacity-30 blur-3xl"
              style={{ background: 'radial-gradient(circle at 20% 20%, rgba(16,185,129,0.3), transparent 60%), radial-gradient(circle at 80% 20%, rgba(34,197,94,0.25), transparent 55%)' }}
              aria-hidden
            />
            <button
              onClick={() => setShowPreferences(false)}
              className="absolute right-5 top-5 rounded-full border border-white/10 bg-slate-950/70 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.3em] text-slate-300 transition hover:border-emerald-400/60 hover:bg-slate-900/80 hover:text-emerald-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
              aria-label="Close session preferences"
            >
              Close
            </button>
            <header>
              <h2 className="text-2xl font-bold text-white">Session preferences</h2>
              <p className="mt-2 text-sm text-slate-300">
                Adjust how the assistant responds and update your health profile for more tailored guidance.
              </p>
            </header>

            <div className="mt-6 space-y-6">
              <ProfileCard
                loading={profileLoading}
                name={profileName}
                avatarColor={avatarColor}
                stats={profileStats}
                onEdit={handleOpenProfileModal}
              />

              <div className="space-y-3 rounded-2xl border border-white/10 bg-slate-950/60 p-5 shadow-[0_18px_45px_rgba(15,23,42,0.55)]">
                <label
                  htmlFor="language-preferences"
                  className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-300/80"
                >
                  Language
                </label>
                <select
                  id="language-preferences"
                  value={lang}
                  onChange={(event) => setLang(event.target.value as LangCode)}
                  className="w-full rounded-2xl border border-white/10 bg-slate-900/70 px-4 py-2 text-sm text-slate-100 shadow-inner shadow-black/20 focus:border-emerald-400/60 focus:outline-none focus:ring-4 focus:ring-emerald-500/20"
                >
                  {LANGUAGE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value} className="bg-slate-900">
                      {option.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-400">
                  Switching the language updates the assistant's replies and placeholder prompts.
                </p>
                <button
                  onClick={handleOpenProfileModal}
                  className="mt-3 rounded-2xl border border-emerald-400/40 bg-gradient-to-r from-emerald-500/20 via-green-500/15 to-teal-500/20 px-4 py-2 text-sm font-semibold text-emerald-200 transition hover:border-emerald-400/60 hover:from-emerald-500/30 hover:via-green-500/25 hover:to-teal-500/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
                >
                  Edit health profile
                </button>
              </div>
            </div>
          </section>
        </div>
      )}

      {showSafety && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-3 sm:px-4 py-4 sm:py-8 backdrop-blur-sm overflow-y-auto">
          <section
            className="relative w-full max-w-xl overflow-hidden rounded-2xl sm:rounded-3xl border border-white/10 bg-slate-900/70 p-4 sm:p-6 md:p-8 shadow-[0_35px_90px_rgba(15,23,42,0.65)] backdrop-blur-xl my-auto max-h-[90vh] overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-label="Safety guidance"
          >
            <div
              className="absolute inset-0 -z-10 opacity-30 blur-3xl"
              style={{ background: 'radial-gradient(circle at 20% 20%, rgba(16,185,129,0.3), transparent 60%), radial-gradient(circle at 80% 20%, rgba(34,197,94,0.25), transparent 55%)' }}
              aria-hidden
            />
            <button
              onClick={() => setShowSafety(false)}
              className="absolute right-5 top-5 rounded-full border border-white/10 bg-slate-950/70 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.3em] text-slate-300 transition hover:border-emerald-400/60 hover:bg-slate-900/80 hover:text-emerald-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
              aria-label="Close safety guidance"
            >
              Close
            </button>
            <header className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/30 via-green-500/25 to-teal-500/30 text-emerald-200 shadow-[0_0_20px_rgba(16,185,129,0.4)]">
                <HeartPulse className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">Emergency guidance</h2>
                <p className="text-xs uppercase tracking-[0.3em] text-emerald-300/80">Stay prepared</p>
              </div>
            </header>

            <div className="mt-6 space-y-4 text-sm leading-relaxed text-slate-300">
              <p>
                This assistant can highlight red flags, but it cannot diagnose or provide emergency care. Contact local services
                immediately if you notice:
              </p>
              <ul className="list-disc space-y-2 pl-5 text-slate-200">
                <li>Chest pain, shortness of breath, or sudden weakness.</li>
                <li>Severe bleeding, confusion, or loss of consciousness.</li>
                <li>Worsening symptoms after self-care guidance.</li>
              </ul>
              <div className="rounded-2xl border border-emerald-400/40 bg-gradient-to-r from-emerald-500/20 via-green-500/15 to-teal-500/20 p-4 text-emerald-100 shadow-[0_18px_45px_rgba(16,185,129,0.18)]">
                <p className="font-semibold text-emerald-50">
                  Call your local emergency number (India: 108) or visit the nearest emergency department for urgent concerns.
                </p>
              </div>
              <button
                onClick={() => window.open('tel:108')}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 via-green-500 to-teal-500 px-4 py-3 font-semibold text-white shadow-[0_18px_45px_rgba(16,185,129,0.35)] transition hover:scale-[1.02] hover:shadow-[0_25px_60px_rgba(16,185,129,0.45)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300"
              >
                <Phone className="h-5 w-5" />
                Call Emergency (108)
              </button>
            </div>
          </section>
        </div>
      )}

      {showProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-3 sm:px-4 py-4 sm:py-8 backdrop-blur-sm overflow-y-auto">
          <div className="relative w-full max-w-lg overflow-hidden rounded-2xl sm:rounded-3xl border border-white/10 bg-slate-900/70 p-4 sm:p-6 md:p-8 shadow-[0_35px_90px_rgba(15,23,42,0.65)] backdrop-blur-xl my-auto max-h-[90vh] overflow-y-auto">
            <div
              className="absolute inset-0 -z-10 opacity-30 blur-3xl"
              style={{ background: 'radial-gradient(circle at 20% 20%, rgba(16,185,129,0.3), transparent 60%), radial-gradient(circle at 80% 20%, rgba(34,197,94,0.25), transparent 55%)' }}
              aria-hidden
            />
            <button
              onClick={() => setShowProfile(false)}
              className="absolute right-5 top-5 rounded-full border border-white/10 bg-slate-950/70 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.3em] text-slate-300 transition hover:border-emerald-400/60 hover:bg-slate-900/80 hover:text-emerald-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
              aria-label="Close profile modal"
            >
              Close
            </button>
            <h2 className="text-2xl font-bold text-white">Health profile</h2>
            <p className="mt-2 text-sm text-slate-300">
              Update basic details so I can tailor contextual guidance. Your information stays on this device.
            </p>

            <div className="mt-4 sm:mt-6 space-y-3 sm:space-y-4">
              <label className="flex items-center gap-2.5 sm:gap-3 rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/60 px-3 sm:px-4 py-3 min-h-[44px] text-sm text-slate-200 shadow-[0_12px_30px_rgba(15,23,42,0.45)] transition hover:border-emerald-400/30 hover:shadow-[0_18px_45px_rgba(16,185,129,0.18)]">
                <input
                  type="checkbox"
                  checked={profile.diabetes}
                  onChange={(event) => setProfile((prev) => ({ ...prev, diabetes: event.target.checked }))}
                  className="h-5 w-5 sm:h-5 sm:w-5 rounded border-white/20 bg-slate-800 text-emerald-500 focus:ring-emerald-400/50 flex-shrink-0"
                />
                <span className="text-sm sm:text-base">I have diabetes</span>
              </label>

              <label className="flex items-center gap-2.5 sm:gap-3 rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/60 px-3 sm:px-4 py-3 min-h-[44px] text-sm text-slate-200 shadow-[0_12px_30px_rgba(15,23,42,0.45)] transition hover:border-emerald-400/30 hover:shadow-[0_18px_45px_rgba(16,185,129,0.18)]">
                <input
                  type="checkbox"
                  checked={profile.hypertension}
                  onChange={(event) => setProfile((prev) => ({ ...prev, hypertension: event.target.checked }))}
                  className="h-5 w-5 sm:h-5 sm:w-5 rounded border-white/20 bg-slate-800 text-emerald-500 focus:ring-emerald-400/50 flex-shrink-0"
                />
                <span className="text-sm sm:text-base">I have hypertension</span>
              </label>

              {(profile.sex === 'female' || profile.sex === undefined || profile.sex === 'other') && (
                <label className="flex items-center gap-2.5 sm:gap-3 rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/60 px-3 sm:px-4 py-3 min-h-[44px] text-sm text-slate-200 shadow-[0_12px_30px_rgba(15,23,42,0.45)] transition hover:border-emerald-400/30 hover:shadow-[0_18px_45px_rgba(16,185,129,0.18)]">
                  <input
                    type="checkbox"
                      checked={profile.pregnancy}
                      onChange={(event) => setProfile((prev) => ({ ...prev, pregnancy: event.target.checked }))}
                      className="h-5 w-5 sm:h-5 sm:w-5 rounded border-white/20 bg-slate-800 text-emerald-500 focus:ring-emerald-400/50 flex-shrink-0"
                    />
                  <span className="text-sm sm:text-base">I am currently pregnant</span>
                </label>
              )}

              <div className="grid grid-cols-1 gap-3 sm:gap-4 sm:grid-cols-2">
                <label className="space-y-2 text-sm text-slate-300">
                  <span className="block font-semibold text-emerald-300/80 text-xs sm:text-sm">Age (years)</span>
                  <input
                    type="number"
                    min={0}
                    value={profile.age ?? ''}
                    onChange={(event) =>
                      setProfile((prev) => ({
                        ...prev,
                        age: event.target.value ? Number(event.target.value) : undefined,
                      }))
                    }
                    className="w-full rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/60 px-3 sm:px-4 py-2.5 sm:py-2 min-h-[44px] text-sm sm:text-base text-slate-100 shadow-inner shadow-black/20 focus:border-emerald-400/60 focus:outline-none focus:ring-4 focus:ring-emerald-500/20"
                  />
              </label>

                <label className="space-y-2 text-sm text-slate-300">
                  <span className="block font-semibold text-emerald-300/80 text-xs sm:text-sm">Sex</span>
                  <select
                    value={profile.sex ?? ''}
                    onChange={(event) =>
                      setProfile((prev) => ({
                        ...prev,
                        sex: event.target.value ? (event.target.value as SexOption) : undefined,
                        pregnancy: event.target.value === 'female' ? prev.pregnancy : false,
                      }))
                    }
                    className="w-full rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/60 px-3 sm:px-4 py-2.5 sm:py-2 min-h-[44px] text-sm sm:text-base text-slate-100 shadow-inner shadow-black/20 focus:border-emerald-400/60 focus:outline-none focus:ring-4 focus:ring-emerald-500/20"
                  >
                    <option value="" className="bg-slate-900">Select</option>
                    <option value="male" className="bg-slate-900">Male</option>
                    <option value="female" className="bg-slate-900">Female</option>
                    <option value="other" className="bg-slate-900">Other / Prefer not to say</option>
                  </select>
                </label>
              </div>

              <label className="space-y-2 text-sm text-slate-300">
                <span className="block font-semibold text-emerald-300/80 text-xs sm:text-sm">City (optional)</span>
                <input
                  type="text"
                  value={profile.city ?? ''}
                  onChange={(event) => setProfile((prev) => ({ ...prev, city: event.target.value }))}
                  placeholder="e.g., Mumbai"
                  className="w-full rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/60 px-3 sm:px-4 py-2.5 sm:py-2 min-h-[44px] text-sm sm:text-base text-slate-100 shadow-inner shadow-black/20 focus:border-emerald-400/60 focus:outline-none focus:ring-4 focus:ring-emerald-500/20"
                />
              </label>
            </div>

            <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row justify-end gap-2.5 sm:gap-3">
              <button
                onClick={() => setShowProfile(false)}
                className="w-full sm:w-auto rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 min-h-[44px] text-sm font-semibold text-slate-300 transition hover:border-white/20 hover:bg-slate-900/80 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-400"
              >
                Cancel
              </button>
            <button
              onClick={() => setShowProfile(false)}
                className="w-full sm:w-auto rounded-xl sm:rounded-2xl bg-gradient-to-r from-emerald-500 via-green-500 to-teal-500 px-4 py-3 min-h-[44px] text-sm font-semibold text-white shadow-[0_10px_30px_rgba(16,185,129,0.35)] transition hover:scale-[1.02] hover:shadow-[0_15px_40px_rgba(16,185,129,0.45)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
            >
                Save profile
            </button>
            </div>
          </div>
        </div>
      )}
      </div>
      </div>
    </>
  );
}

