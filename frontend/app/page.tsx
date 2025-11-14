'use client';

import clsx from 'clsx';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import {
  AlertTriangle,
  Check,
  Download,
  HeartPulse,
  History,
  Menu,
  Mic,
  Phone,
  Plus,
  Search,
  SendHorizonal,
  Settings,
  Share2,
  Sparkle,
  X,
} from 'lucide-react';
import ChatMessage, { type ChatMessageModel } from '../components/ChatMessage';
import LoadingSkeleton from '../components/LoadingSkeleton';
import ErrorCallout from '../components/ErrorCallout';
import ProfileCard from '../components/ProfileCard';
import TopicSuggestions from '../components/TopicSuggestions';
import { TOPIC_CATEGORIES } from '../data/topics';
import { CalendarDays, Heart, MapPin, Stethoscope } from 'lucide-react';

type LangCode = 'en' | 'hi' | 'ta' | 'te' | 'kn' | 'ml';
type SexOption = 'male' | 'female' | 'other';

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, '') ?? 'http://localhost:8000';

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

interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatEntry[];
}

const HISTORY_STORAGE_KEY = 'wellness-care-sessions.v1';

const cloneEntries = (entries: ChatEntry[]): ChatEntry[] =>
  entries.map((entry) => ({ ...entry }));

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

export default function Home() {
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [lang, setLang] = useState<LangCode>('en');
  const [showProfile, setShowProfile] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showSafety, setShowSafety] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isDesktop, setIsDesktop] = useState(false);
  const [profile, setProfile] = useState<Profile>(defaultProfile);
  const [profileLoading, setProfileLoading] = useState(true);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const shareFeedbackTimeoutRef = useRef<number | null>(null);

  const [shareFeedback, setShareFeedback] = useState<string | null>(null);

  const createSession = useCallback((): ChatSession => {
    const timestamp = formatTimestamp();
    return {
      id: createId(),
      title: 'New care session',
      createdAt: timestamp,
      updatedAt: timestamp,
      messages: [],
    };
  }, []);

  const deriveSessionTitle = useCallback((entries: ChatEntry[], fallback = 'New care session') => {
    const firstUser =
      entries.find((entry) => entry.role === 'user' && entry.content && entry.content.trim().length > 0) ?? null;
    if (!firstUser) {
      return fallback;
    }
    const normalized = firstUser.content.replace(/\s+/g, ' ').trim();
    return normalized.length > 56 ? `${normalized.slice(0, 56)}…` : normalized;
  }, []);

  const quickSuggestionPrompts = useMemo(() => {
    return TOPIC_CATEGORIES.flatMap((category) => category.suggestions.map((suggestion) => suggestion.prompt)).slice(0, 6);
  }, []);

  const currentLanguage =
    LANGUAGE_OPTIONS.find((option) => option.value === lang) ?? LANGUAGE_OPTIONS[0];

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
    if (typeof window === 'undefined') {
      return;
    }
    try {
      const stored = window.localStorage.getItem(HISTORY_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as ChatSession[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          const nextSessions = parsed.map((session) => ({
            ...session,
            messages: session.messages ? cloneEntries(session.messages) : [],
          }));
          setSessions(nextSessions);
          setActiveSessionId(nextSessions[0].id);
          setMessages(cloneEntries(nextSessions[0].messages ?? []));
          setHasInteracted(nextSessions[0].messages?.some((entry) => entry.role === 'assistant') ?? false);
        } else {
          const session = createSession();
          setSessions([session]);
          setActiveSessionId(session.id);
        }
      } else {
        const session = createSession();
        setSessions([session]);
        setActiveSessionId(session.id);
      }
    } catch (loadError) {
      console.warn('Unable to load saved sessions', loadError);
      const session = createSession();
      setSessions([session]);
      setActiveSessionId(session.id);
    } finally {
      setSearchQuery('');
      setTimeout(() => setIsHydrated(true), 0);
    }
  }, [createSession]);

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

  useEffect(() => {
    if (!isHydrated || !activeSessionId) {
      return;
    }
    setSessions((prevSessions) => {
      const timestamp = formatTimestamp();
      let found = false;
      const updated = prevSessions.map((session) => {
        if (session.id === activeSessionId) {
          found = true;
          return {
            ...session,
            title: deriveSessionTitle(messages, session.title),
            updatedAt: timestamp,
            messages: cloneEntries(messages),
          };
        }
        return session;
      });

      if (!found) {
        updated.push({
          id: activeSessionId,
          title: deriveSessionTitle(messages),
          createdAt: timestamp,
          updatedAt: timestamp,
          messages: cloneEntries(messages),
        });
      }

      updated.sort(
        (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
      );

      if (typeof window !== 'undefined') {
        window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
      }

      return updated;
    });
  }, [messages, activeSessionId, isHydrated, deriveSessionTitle]);

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

  const handleSend = async (overrides?: string) => {
    const messageText = (overrides ?? inputValue).trim();
    if (!messageText || isLoading) return;

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
      const response = await axios.post(`${API_BASE}/chat`, {
        text: messageText,
        lang,
        profile,
      });

      const assistantMessage: ChatEntry = {
        id: createId(),
        role: 'assistant',
        content: response.data.answer,
        timestamp: formatTimestamp(),
        citations: response.data.citations,
        facts: response.data.facts,
        safety: response.data.safety,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(response.data.answer);
        utterance.lang = LANGUAGE_SPEECH_MAP[lang] ?? 'en-US';
        utterance.rate = 0.92;
        window.speechSynthesis.speak(utterance);
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

  const transcribeAudio = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'voice-note.webm');

      const response = await axios.post(`${API_BASE}/stt`, formData, {
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
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
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

  const handleQuickPrompt = useCallback(
    (prompt: string) => {
      void handleSend(prompt);
    },
    [handleSend]
  );

  const handleNewSession = useCallback(() => {
    const session = createSession();
    setSessions((prev) => {
      const next = [session, ...prev];
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(next));
      }
      return next;
    });
    setActiveSessionId(session.id);
    setMessages([]);
    setHasInteracted(false);
    setError(null);
    setSearchQuery('');
    if (!isDesktop) {
      setIsSidebarOpen(false);
      setIsHistoryExpanded(false);
    }
  }, [createSession, isDesktop]);

  const handleSelectSession = useCallback(
    (sessionId: string) => {
      const session = sessions.find((entry) => entry.id === sessionId);
      if (!session) {
        return;
      }
      setActiveSessionId(sessionId);
      setMessages(cloneEntries(session.messages ?? []));
      setHasInteracted(session.messages?.some((entry) => entry.role === 'assistant') ?? false);
      setError(null);
      setSearchQuery('');
      if (!isDesktop) {
        setIsSidebarOpen(false);
        setIsHistoryExpanded(false);
      }
    },
    [sessions, isDesktop]
  );

  const handleExportConversation = useCallback(() => {
    if (messages.length === 0) {
      scheduleShareFeedback('No conversation to export yet.');
      return;
    }
    try {
      const payload = {
        sessionId: activeSessionId,
        exportedAt: formatTimestamp(),
        profileSnapshot: profile,
        messages,
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: 'application/json',
      });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      anchor.href = url;
      anchor.download = `wellness-session-${timestamp}.json`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      scheduleShareFeedback('Conversation exported.');
    } catch (exportError) {
      console.error('Export error', exportError);
      scheduleShareFeedback('Unable to export conversation.');
    }
  }, [messages, activeSessionId, profile, scheduleShareFeedback]);

  const toggleHistory = useCallback(() => {
    setIsHistoryExpanded((prev) => !prev);
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
          title: 'WellNess care session',
          text: conversation,
        });
        scheduleShareFeedback('Sharing sheet opened.');
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(conversation);
        scheduleShareFeedback('Conversation copied to clipboard.');
      } else {
        scheduleShareFeedback('Sharing is not supported in this browser.');
      }
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        scheduleShareFeedback('Share cancelled.');
      } else {
        console.error('Share error', error);
        scheduleShareFeedback('Unable to share right now.');
      }
    }
  }, [messages, scheduleShareFeedback]);

  const sidebarClasses = useMemo(
    () =>
      clsx(
        'fixed inset-y-0 left-0 z-40 flex w-72 flex-col gap-6 overflow-y-auto border-r border-white/10 bg-slate-900/60 px-6 py-8 shadow-[0_0_60px_rgba(236,72,153,0.18)] transition-transform duration-300 backdrop-blur-xl lg:z-30 lg:bg-slate-900/50 lg:shadow-none',
        isSidebarOpen ? 'translate-x-0 lg:translate-x-0' : '-translate-x-full lg:-translate-x-full'
      ),
    [isSidebarOpen]
  );

  const mainLayoutClasses = useMemo(
    () =>
      clsx(
        'flex min-h-screen flex-col transition-[margin] duration-300',
        isSidebarOpen ? 'lg:ml-72' : 'lg:ml-16',
        'px-0 sm:px-0'
      ),
    [isSidebarOpen]
  );

  const bottomBarClasses = useMemo(
    () =>
      clsx(
        'fixed bottom-0 left-0 right-0 z-40 px-4 pb-6 pt-3 sm:px-6 lg:px-10 transition-[left] duration-300',
        isSidebarOpen ? 'lg:left-72' : 'lg:left-16'
      ),
    [isSidebarOpen]
  );

  const collapseRailClasses = useMemo(
    () =>
      clsx(
        'fixed inset-y-0 left-0 z-30 hidden w-16 flex-col items-center justify-between border-r border-white/10 bg-slate-900/60 px-2 py-6 shadow-[0_0_40px_rgba(236,72,153,0.18)] transition-transform duration-300 backdrop-blur-xl lg:flex',
        isSidebarOpen ? '-translate-x-full opacity-0 pointer-events-none' : 'translate-x-0 opacity-100'
      ),
    [isSidebarOpen]
  );

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? null,
    [sessions, activeSessionId]
  );

  const normalizedSearch = searchQuery.trim().toLowerCase();

  const filteredMessages = useMemo(() => {
    if (!normalizedSearch) {
      return messages;
    }
    return messages.filter((entry) => entry.content.toLowerCase().includes(normalizedSearch));
  }, [messages, normalizedSearch]);

  const highlightedIds = useMemo(() => {
    if (!normalizedSearch) {
      return new Set<string>();
    }
    return new Set(filteredMessages.map((entry) => entry.id));
  }, [filteredMessages, normalizedSearch]);


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

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_15%,rgba(236,72,153,0.55),transparent_55%),radial-gradient(circle_at_85%_5%,rgba(124,58,237,0.4),transparent_55%),linear-gradient(180deg,rgba(2,6,23,0.92),rgba(2,6,23,0.95))]" />
      <div className="relative z-10">
      <aside
        className={sidebarClasses}
        aria-label="Primary navigation"
        aria-hidden={!isSidebarOpen && isDesktop}
        id="primary-navigation"
        data-overlay={isSidebarOpen && !isDesktop}
      >
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-gradient-to-br from-pink-500 via-fuchsia-500 to-purple-500 p-2 text-white shadow-[0_0_25px_rgba(236,72,153,0.45)]">
            <Sparkle className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-pink-300/80">Wellness mode</p>
            <p className="text-base font-semibold text-white">Care Console</p>
          </div>
        </div>

        <div className="space-y-5 pt-6">
          <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-5 shadow-[0_25px_60px_rgba(236,72,153,0.12)]">
            <p className="text-sm font-semibold text-white/90">Welcome back</p>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">
              I'm ready whenever you need help planning next steps or spotting red flags.
            </p>
          </div>

          {error && !hasInteracted && (
            <ErrorCallout message={error} onDismiss={handleDismissError} />
          )}

          <nav className="flex flex-col gap-3" aria-label="Quick actions">
            <button
            type="button"
              onClick={() => {
                setIsSidebarOpen(false);
                setShowPreferences(true);
              }}
              className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-900/65 px-5 py-4 text-left shadow-[0_20px_45px_rgba(236,72,153,0.12)] transition hover:border-pink-400/60 hover:bg-slate-900/80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-400/70"
            >
              <span className="flex items-center gap-3 text-slate-100">
                <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-pink-500 via-fuchsia-500 to-purple-500 text-white shadow-[0_0_15px_rgba(236,72,153,0.35)]">
                  <Settings className="h-4 w-4" />
                </span>
                <span className="text-sm font-semibold leading-tight">Session preferences</span>
            </span>
              <span className="text-xs uppercase tracking-[0.32em] text-pink-300/70">Open</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setIsSidebarOpen(false);
                setShowSafety(true);
              }}
              className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-900/65 px-5 py-4 text-left shadow-[0_20px_45px_rgba(124,58,237,0.18)] transition hover:border-violet-400/60 hover:bg-slate-900/80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-400/70"
            >
              <span className="flex items-center gap-3 text-slate-100">
                <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500 via-fuchsia-500 to-pink-500 text-white shadow-[0_0_15px_rgba(167,139,250,0.35)]">
                  <HeartPulse className="h-4 w-4" />
                </span>
                <span className="text-sm font-semibold leading-tight">Safety guidance</span>
            </span>
              <span className="text-xs uppercase tracking-[0.32em] text-violet-300/70">Open</span>
            </button>
          </nav>

          <TopicSuggestions
            onSuggestionSelect={(prompt) => {
              void handleSend(prompt);
            }}
            onAfterSelect={() => {
              if (!isDesktop) {
                setIsSidebarOpen(false);
              }
            }}
          />
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
          className="flex h-14 w-14 items-center justify-center rounded-full border border-white/10 bg-slate-900/70 text-white shadow-[0_0_35px_rgba(236,72,153,0.3)] transition hover:border-pink-400/70 hover:text-pink-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-400"
              >
          <Sparkle className="h-5 w-5 text-pink-300" aria-hidden />
            </button>
              <button
                type="button"
          onClick={() => setIsSidebarOpen(true)}
          className="flex flex-col items-center gap-1 text-xs font-semibold uppercase tracking-[0.32em] text-pink-300"
        >
          <Menu className="h-4 w-4" aria-hidden />
          Open
              </button>
      </div>

      <div className={mainLayoutClasses}>
        <header className="flex items-center justify-between border-b border-white/10 bg-slate-900/60 px-4 py-4 shadow-[0_25px_60px_rgba(15,23,42,0.55)] backdrop-blur-lg sm:px-6 lg:px-10">
          <div className="flex items-center gap-3">
          <button
                type="button"
              onClick={() => setIsSidebarOpen(true)}
              aria-expanded={isSidebarOpen}
              aria-controls="primary-navigation"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-900/70 px-3 py-2 text-sm font-semibold text-slate-200 shadow-[0_0_25px_rgba(236,72,153,0.18)] transition hover:border-pink-400/70 hover:text-pink-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-400 lg:hidden"
            >
              <Menu className="h-4 w-4" aria-hidden />
              <span>Menu</span>
          </button>
              <div>
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-pink-300/75">Live care session</p>
              <h1 className="text-lg font-semibold text-white sm:text-xl">WellNess Health Companion</h1>
            </div>
              </div>
              <div className="flex flex-col items-end gap-2 sm:flex-row sm:items-center sm:gap-3">
                <div className="flex items-center gap-2 sm:gap-3">
                  <button
                    type="button"
                    onClick={handleShareConversation}
                    className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-900/70 px-3 py-2 text-xs font-semibold text-slate-100 shadow-[0_0_25px_rgba(236,72,153,0.18)] transition hover:border-pink-300/70 hover:text-pink-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
                  >
                    <Share2 className="h-4 w-4" aria-hidden />
                    Share
                  </button>
                  <div className="flex items-center gap-2 rounded-full border border-pink-400/40 bg-gradient-to-r from-pink-500 via-fuchsia-500 to-purple-500 px-4 py-1 text-sm font-medium text-white shadow-[0_0_25px_rgba(236,72,153,0.35)]">
                    <span className="flex h-2.5 w-2.5 animate-pulse rounded-full bg-white" />
                    Online
                  </div>
                </div>
                {shareFeedback && (
                  <p className="text-xs text-pink-200/80" aria-live="polite">
                    {shareFeedback}
                  </p>
                )}
              </div>
        </header>

        <main className="flex-1 px-4 pb-32 pt-6 sm:px-6 lg:px-10">
          <div className="mx-auto flex h-full max-w-4xl flex-col gap-6">
            <section className="relative overflow-hidden rounded-[30px] border border-white/10 bg-slate-900/60 px-5 py-6 shadow-[0_35px_90px_rgba(15,23,42,0.65)] backdrop-blur-xl sm:px-6 lg:px-8">
              <div
                className="absolute inset-y-0 right-0 w-[55%] opacity-60 blur-3xl bg-gradient-to-br from-pink-500 via-fuchsia-500 to-purple-500"
                aria-hidden
              />
              <div className="relative flex flex-col gap-5">
                <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.32em] text-pink-300/80">
                  <span className="flex h-2 w-2 rounded-full bg-pink-400" aria-hidden />
                  Ready when you are
                </div>
                <h2 className="text-3xl font-bold text-white sm:text-4xl lg:text-5xl">
                  How can I care for you today?
                </h2>
                <p className="max-w-3xl text-sm leading-relaxed text-slate-200 sm:text-base">
                  Share what’s on your mind—symptoms you’re noticing, questions about self-care, or worries about emergencies. I’ll
                  help you navigate next steps with calm, clinically aligned guidance.
                </p>
                <div className="flex flex-wrap gap-2 text-sm text-slate-200">
                  {quickSuggestionPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => handleQuickPrompt(prompt)}
                      className="rounded-2xl border border-white/10 bg-slate-900/60 px-4 py-3 text-left shadow-[0_18px_45px_rgba(236,72,153,0.12)] transition hover:border-pink-300/60 hover:text-pink-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
                <div className="flex items-start gap-3 rounded-2xl border border-pink-400/40 bg-gradient-to-r from-pink-500/20 via-fuchsia-500/10 to-purple-500/20 px-4 py-3 text-pink-100 shadow-[0_18px_45px_rgba(236,72,153,0.18)]">
                  <span className="mt-1 flex h-3 w-3 rounded-full bg-white/80" aria-hidden />
                  <p className="text-xs leading-relaxed text-pink-50 sm:text-sm">
                    I’m a virtual companion for everyday care—not a substitute for emergency services or licensed clinicians. If you
                    feel unsafe or notice severe symptoms, please seek urgent medical attention immediately.
                  </p>
                </div>
              </div>
            </section>

            <section className="relative overflow-hidden flex-1 rounded-[28px] border border-white/10 bg-slate-900/55 shadow-[0_35px_90px_rgba(15,23,42,0.65)] backdrop-blur-xl">
              <div
                className="absolute inset-y-0 right-0 w-[45%] opacity-60 blur-3xl bg-gradient-to-br from-purple-500 via-fuchsia-500 to-pink-500"
                aria-hidden
              />
              <div className="relative flex h-full flex-col">
                <div
                  ref={scrollContainerRef}
                  className="flex-1 overflow-y-auto px-3 py-4 sm:px-5 lg:px-6"
                  aria-live="polite"
                  aria-busy={isLoading}
                >
                  <div
                    className="mx-auto flex w-full flex-col gap-4 px-1 sm:px-2 lg:max-w-3xl lg:px-3"
                    role="list"
                    aria-live="polite"
                  >

        {messages.map((message, index) => (
                  <div key={message.id} className="space-y-4">
                    <ChatMessage message={message} index={index} />

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
                            <h4 className="text-sm font-semibold uppercase tracking-[0.32em] text-pink-200">Additional insights</h4>
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
                                  className="rounded-2xl border border-violet-400/40 bg-violet-500/10 p-3"
                                >
                                      <p className="font-semibold text-violet-200">Providers you might consider</p>
                                  <ul className="mt-2 space-y-1 text-sm text-violet-100/90">
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
                                      className="rounded-2xl border border-fuchsia-400/40 bg-fuchsia-500/10 p-3"
                                    >
                                      <p className="font-semibold text-fuchsia-200">Pregnancy considerations</p>
                                      <ul className="mt-2 space-y-1 text-sm text-fuchsia-100/90">
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
        {isLoading && (
                      <div className="space-y-4">
                        <LoadingSkeleton count={1} />
                      </div>
                    )}
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
          </div>
        </main>
      </div>

        <div className={bottomBarClasses} style={{ pointerEvents: 'none' }}>
          <form
            className="mx-auto flex w-full max-w-4xl flex-wrap items-center gap-4 rounded-[32px] border border-white/10 bg-slate-900/70 px-4 py-4 shadow-[0_28px_80px_rgba(236,72,153,0.25)] backdrop-blur-xl sm:flex-nowrap sm:px-6"
            style={{ pointerEvents: 'auto' }}
            onSubmit={(event) => {
              event.preventDefault();
              void handleSend();
            }}
          >
            <button
              type="button"
              onClick={() => {
                if (isRecording) {
                  stopRecording();
                } else {
                  void startRecording();
                }
              }}
              className={clsx(
                'flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-full text-sm font-semibold shadow-[0_18px_45px_rgba(236,72,153,0.35)] transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
                isRecording
                  ? 'border border-red-400/60 bg-red-500 text-white focus-visible:outline-red-300'
                  : 'border border-transparent bg-gradient-to-br from-pink-500 via-fuchsia-500 to-purple-500 text-white hover:scale-[1.03] focus-visible:outline-pink-300'
              )}
              aria-pressed={isRecording}
              aria-label={isRecording ? 'Stop recording' : 'Start voice recording'}
            >
              {isRecording ? (
                <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.3em]">
                  <span className="inline-flex h-2.5 w-2.5 animate-pulse rounded-full bg-white" aria-hidden />
                  REC
                </span>
              ) : (
                <Mic className="h-5 w-5" />
              )}
            </button>

            <div className="relative flex-1">
              <textarea
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={selectedPlaceholder}
                rows={3}
                className="min-h-[80px] w-full resize-none rounded-2xl border border-white/10 bg-transparent px-4 py-3 text-sm leading-relaxed text-slate-100 shadow-inner shadow-black/20 transition placeholder:text-slate-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-400/80"
                aria-label="Write your question"
                disabled={isLoading}
              />
              <span className="pointer-events-none absolute bottom-3 right-4 text-xs text-slate-500">
                Shift + Enter for new line
              </span>
            </div>

            <button
              type="submit"
              className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-full border border-transparent bg-gradient-to-br from-fuchsia-500 via-pink-500 to-purple-500 text-white shadow-[0_18px_45px_rgba(236,72,153,0.35)] transition hover:scale-[1.05] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
              disabled={isLoading}
              aria-label="Send message"
            >
              <SendHorizonal className={clsx('h-5 w-5', isLoading ? 'animate-pulse' : '')} aria-hidden />
            </button>
          </form>
        </div>

      {showPreferences && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4 py-8 backdrop-blur-sm">
          <section
            className="relative w-full max-w-2xl rounded-3xl border border-white/60 bg-white/95 p-8 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-label="Session preferences"
          >
            <button
              onClick={() => setShowPreferences(false)}
              className="absolute right-5 top-5 rounded-full border border-slate-200 px-2 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 transition hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ocean-200"
              aria-label="Close session preferences"
            >
              Close
            </button>
            <header>
              <h2 className="text-2xl font-bold text-slate-800">Session preferences</h2>
              <p className="mt-2 text-sm text-slate-600">
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

              <div className="space-y-3 rounded-2xl border border-ocean-100 bg-white/80 p-5 shadow-sm">
                <label
                  htmlFor="language-preferences"
                  className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400"
                >
                  Language
                </label>
                <select
                  id="language-preferences"
                  value={lang}
                  onChange={(event) => setLang(event.target.value as LangCode)}
                  className="rounded-2xl border border-ocean-100 bg-white px-4 py-2 text-sm text-slate-700 shadow focus:border-ocean-300 focus:outline-none focus:ring-4 focus:ring-ocean-200/40"
                >
                  {LANGUAGE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-500">
                  Switching the language updates the assistant's replies and placeholder prompts.
                </p>
          <button
                  onClick={handleOpenProfileModal}
                  className="rounded-2xl border border-ocean-100 px-4 py-2 text-sm font-semibold text-ocean-700 transition hover:bg-ocean-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ocean-200"
          >
                  Edit health profile
          </button>
        </div>
      </div>
          </section>
        </div>
      )}

      {showSafety && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4 py-8 backdrop-blur-sm">
          <section
            className="relative w-full max-w-xl rounded-3xl border border-white/60 bg-white/95 p-8 shadow-2xl"
            role="dialog"
            aria-modal="true"
            aria-label="Safety guidance"
          >
            <button
              onClick={() => setShowSafety(false)}
              className="absolute right-5 top-5 rounded-full border border-slate-200 px-2 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 transition hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-mint-200"
              aria-label="Close safety guidance"
            >
              Close
            </button>
            <header className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-mint-100 text-mint-700">
                <HeartPulse className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-800">Emergency guidance</h2>
                <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Stay prepared</p>
              </div>
            </header>

            <div className="mt-6 space-y-4 text-sm leading-relaxed text-slate-600">
              <p>
                This assistant can highlight red flags, but it cannot diagnose or provide emergency care. Contact local services
                immediately if you notice:
              </p>
              <ul className="list-disc space-y-2 pl-5">
                <li>Chest pain, shortness of breath, or sudden weakness.</li>
                <li>Severe bleeding, confusion, or loss of consciousness.</li>
                <li>Worsening symptoms after self-care guidance.</li>
              </ul>
              <p className="rounded-2xl border border-mint-200 bg-mint-50/70 p-4 text-mint-800">
                Call your local emergency number (India: 108) or visit the nearest emergency department for urgent concerns.
              </p>
              <button
                onClick={() => window.open('tel:108')}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-mint-500 px-4 py-2 font-semibold text-white shadow transition hover:bg-mint-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-mint-200"
              >
                <Phone className="h-4 w-4" />
                Call Emergency (108)
              </button>
            </div>
          </section>
        </div>
      )}

      {showProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4 py-8 backdrop-blur-sm">
          <div className="relative w-full max-w-lg rounded-3xl border border-white/60 bg-white/90 p-8 shadow-2xl">
            <button
              onClick={() => setShowProfile(false)}
              className="absolute right-5 top-5 rounded-full border border-slate-200 px-2 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-slate-500 transition hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ocean-200"
              aria-label="Close profile modal"
            >
              Close
            </button>
            <h2 className="text-2xl font-bold text-slate-800">Health profile</h2>
            <p className="mt-2 text-sm text-slate-600">
              Update basic details so I can tailor contextual guidance. Your information stays on this device.
            </p>

            <div className="mt-6 space-y-4">
              <label className="flex items-center gap-3 rounded-2xl border border-ocean-100 bg-white/80 px-4 py-3 text-sm text-slate-700 shadow-sm transition hover:border-ocean-200">
                <input
                  type="checkbox"
                  checked={profile.diabetes}
                  onChange={(event) => setProfile((prev) => ({ ...prev, diabetes: event.target.checked }))}
                  className="h-5 w-5 rounded border-ocean-200 text-ocean-500 focus:ring-ocean-300"
                />
                I have diabetes
              </label>

              <label className="flex items-center gap-3 rounded-2xl border border-ocean-100 bg-white/80 px-4 py-3 text-sm text-slate-700 shadow-sm transition hover:border-ocean-200">
                <input
                  type="checkbox"
                  checked={profile.hypertension}
                  onChange={(event) => setProfile((prev) => ({ ...prev, hypertension: event.target.checked }))}
                  className="h-5 w-5 rounded border-ocean-200 text-ocean-500 focus:ring-ocean-300"
                />
                I have hypertension
              </label>

              {(profile.sex === 'female' || profile.sex === undefined || profile.sex === 'other') && (
                <label className="flex items-center gap-3 rounded-2xl border border-ocean-100 bg-white/80 px-4 py-3 text-sm text-slate-700 shadow-sm transition hover:border-ocean-200">
                <input
                  type="checkbox"
                    checked={profile.pregnancy}
                    onChange={(event) => setProfile((prev) => ({ ...prev, pregnancy: event.target.checked }))}
                    className="h-5 w-5 rounded border-ocean-200 text-ocean-500 focus:ring-ocean-300"
                  />
                  I am currently pregnant
                </label>
              )}

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <label className="space-y-2 text-sm text-slate-600">
                  <span className="block font-semibold text-slate-500">Age (years)</span>
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
                    className="w-full rounded-2xl border border-ocean-100 bg-white/80 px-4 py-2 text-slate-700 shadow-sm focus:border-ocean-300 focus:outline-none focus:ring-4 focus:ring-ocean-200/50"
                  />
              </label>

                <label className="space-y-2 text-sm text-slate-600">
                  <span className="block font-semibold text-slate-500">Sex</span>
                  <select
                    value={profile.sex ?? ''}
                    onChange={(event) =>
                      setProfile((prev) => ({
                        ...prev,
                        sex: event.target.value ? (event.target.value as SexOption) : undefined,
                        pregnancy: event.target.value === 'female' ? prev.pregnancy : false,
                      }))
                    }
                    className="w-full rounded-2xl border border-ocean-100 bg-white/80 px-4 py-2 text-slate-700 shadow-sm focus:border-ocean-300 focus:outline-none focus:ring-4 focus:ring-ocean-200/50"
                  >
                    <option value="">Select</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other / Prefer not to say</option>
                  </select>
                </label>
              </div>

              <label className="space-y-2 text-sm text-slate-600">
                <span className="block font-semibold text-slate-500">City (optional)</span>
                <input
                  type="text"
                  value={profile.city ?? ''}
                  onChange={(event) => setProfile((prev) => ({ ...prev, city: event.target.value }))}
                  placeholder="e.g., Mumbai"
                  className="w-full rounded-2xl border border-ocean-100 bg-white/80 px-4 py-2 text-slate-700 shadow-sm focus:border-ocean-300 focus:outline-none focus:ring-4 focus:ring-ocean-200/50"
                />
              </label>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowProfile(false)}
                className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-300"
              >
                Cancel
              </button>
            <button
              onClick={() => setShowProfile(false)}
                className="rounded-2xl bg-ocean-500 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-ocean-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ocean-300"
            >
                Save profile
            </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

