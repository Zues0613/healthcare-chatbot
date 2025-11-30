"use client";

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import clsx from "clsx";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import "katex/dist/katex.min.css";
import { Check, Copy, ExternalLink, ChevronDown, ChevronUp, Play, Pause, Square, ThumbsUp, ThumbsDown } from "lucide-react";
interface CodeBlockProps {
  className?: string;
  children?: React.ReactNode;
}

interface MarkdownCodeProps extends React.HTMLAttributes<HTMLElement> {
  inline?: boolean;
  node?: unknown;
}

const CodeBlock = ({ className, children }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<number | null>(null);
  const language = useMemo(() => {
    if (!className) return "";
    const match = /language-(\w+)/.exec(className);
    return match ? match[1] : "";
  }, [className]);

  const handleCopy = useCallback(() => {
    const text = typeof children === "string" ? children : String(children ?? "");
    void navigator.clipboard.writeText(text.trim());
    setCopied(true);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = window.setTimeout(() => setCopied(false), 2400);
  }, [children]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, []);

  return (
    <div className="group relative mt-4 overflow-hidden rounded-2xl border border-white/10 bg-slate-950/80 shadow-[0_18px_45px_rgba(15,23,42,0.55)]">
      <div className="flex items-center justify-between border-b border-white/10 bg-slate-900/70 px-4 py-2 text-xs uppercase tracking-[0.32em] text-slate-400">
        <span>{language || "Code"}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="rounded-full border border-white/10 px-3 py-1 text-[0.65rem] font-semibold tracking-[0.28em] text-slate-300 transition group-hover:border-emerald-300/60 group-hover:text-emerald-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={oneDark}
        customStyle={{
          margin: 0,
          padding: "1.25rem 1.5rem",
          background: "transparent",
        }}
        wrapLongLines
      >
        {String(children ?? "").replace(/\n$/, "")}
      </SyntaxHighlighter>
    </div>
  );
};

export type ChatRole = "user" | "assistant";

export interface Citation {
  source?: string;
  topic?: string;
  url?: string;
  id?: string;
}

export interface ChatMessageModel {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  citations?: Citation[];
  userFeedback?: 'positive' | 'negative'; // Feedback from the user
}

const roleStyles: Record<ChatRole, string> = {
  user:
    "border border-transparent bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-white shadow-[0_25px_70px_rgba(16,185,129,0.30)]",
  assistant:
    "border border-white/10 bg-slate-950/70 backdrop-blur text-slate-100 shadow-[0_30px_85px_rgba(15,23,42,0.55)]",
};

const alignment: Record<ChatRole, string> = {
  user: "items-end justify-end",
  assistant: "items-start justify-start",
};

const avatarStyles: Record<ChatRole, string> = {
  user:
    "bg-gradient-to-br from-green-500/80 via-emerald-500/90 to-teal-500 shadow-[0_10px_30px_rgba(16,185,129,0.45)] text-white",
  assistant:
    "bg-slate-900/80 backdrop-blur border border-white/10 text-emerald-200 shadow-[0_12px_35px_rgba(15,23,42,0.45)]",
};

const avatarLabel: Record<ChatRole, string> = {
  user: "You",
  assistant: "Care Guide",
};

interface ChatMessageProps {
  message: ChatMessageModel;
  index: number;
  language?: string; // Language code for narration
  onFeedback?: (messageId: string, feedback: 'positive' | 'negative') => void; // Callback for feedback
}

function ChatMessage({ message, index, language = 'en', onFeedback }: ChatMessageProps) {
  const [formattedTime, setFormattedTime] = useState<string>("");
  const [copiedCitationKey, setCopiedCitationKey] = useState<string | null>(null);
  const [sourcesExpanded, setSourcesExpanded] = useState<boolean>(false);
  const citationCopyTimeoutRef = useRef<number | null>(null);
  const [narrationState, setNarrationState] = useState<'idle' | 'playing' | 'paused'>('idle');
  const [copied, setCopied] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<'positive' | 'negative' | null>(message.userFeedback || null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Sync feedback state with message prop when it changes (e.g., after reload)
  useEffect(() => {
    if (message.userFeedback !== feedbackGiven) {
      setFeedbackGiven(message.userFeedback || null);
    }
  }, [message.userFeedback]);

  const markdownComponents: Components = useMemo(() => ({
    a: ({ children, className, ...props }) => (
      <a
        className={clsx(
          "font-semibold text-emerald-200 underline decoration-emerald-200/30 underline-offset-4 transition hover:text-emerald-100",
          className
        )}
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
    ),
    li: ({ children, className, ...props }) => (
      <li
        className={clsx(
          "[&_a]:text-emerald-200 [&_a:hover]:text-emerald-100 marker:text-emerald-300",
          className
        )}
        {...props}
      >
        {children}
      </li>
    ),
    ul: ({ children, className, ...props }) => (
      <ul
        className={clsx(
          "my-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-100",
          className
        )}
        {...props}
      >
        {children}
      </ul>
    ),
    ol: ({ children, className, ...props }) => (
      <ol
        className={clsx(
          "my-3 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-100",
          className
        )}
        {...props}
      >
        {children}
      </ol>
    ),
    blockquote: ({ children, className, ...props }) => (
      <blockquote
        className={clsx(
          "my-4 border-l-4 border-emerald-400/60 bg-white/5 px-4 py-2 italic text-emerald-100/90",
          className
        )}
        {...props}
      >
        {children}
      </blockquote>
    ),
    code: ({ children, className, inline, ...props }: MarkdownCodeProps) => {
      if (inline) {
        return (
          <code
            className={clsx(
              "rounded bg-white/10 px-1.5 py-0.5 font-medium text-emerald-100",
              className
            )}
            {...props}
          >
            {children}
          </code>
        );
      }

      return <CodeBlock className={className}>{children}</CodeBlock>;
    },
    table: ({ children, className, ...props }) => (
      <div className="my-4 overflow-x-auto rounded-2xl border border-white/10 bg-slate-950/70">
        <table
          className={clsx(
            "w-full border-collapse text-sm text-slate-100 [&_th]:bg-white/5 [&_th]:text-left [&_th]:font-semibold [&_th]:uppercase [&_th]:tracking-[0.2em] [&_th]:text-emerald-200/80 [&_td]:border-t [&_td]:border-white/10 [&_td]:px-4 [&_td]:py-3 [&_th]:px-4 [&_th]:py-3",
            className
          )}
          {...props}
        >
          {children}
        </table>
      </div>
    ),
    h1: ({ children, className, ...props }) => (
      <h1
        className={clsx(
          "mb-4 mt-6 text-2xl font-black tracking-tight text-white sm:text-3xl",
          className
        )}
        {...props}
      >
        {children}
      </h1>
    ),
    h2: ({ children, className, ...props }) => (
      <h2
        className={clsx(
          "mb-3 mt-5 text-xl font-bold tracking-tight text-white sm:text-2xl",
          className
        )}
        {...props}
      >
        {children}
      </h2>
    ),
    h3: ({ children, className, ...props }) => (
      <h3
        className={clsx(
          "mb-2 mt-4 text-lg font-semibold tracking-tight text-white sm:text-xl",
          className
        )}
        {...props}
      >
        {children}
      </h3>
    ),
    h4: ({ children, className, ...props }) => (
      <h4
        className={clsx(
          "mb-2 mt-4 text-base font-semibold uppercase tracking-[0.28em] text-emerald-200",
          className
        )}
        {...props}
      >
        {children}
      </h4>
    ),
    p: ({ children, className, ...props }) => (
      <p
        className={clsx(
          "my-3 leading-relaxed text-slate-100 [&:first-child]:mt-0 [&:last-child]:mb-0",
          className
        )}
        {...props}
      >
        {children}
      </p>
    ),
    hr: (props) => (
      <hr
        className="my-6 border-t border-white/10"
        {...props}
      />
    ),
    strong: ({ children, className, ...props }) => (
      <strong
        className={clsx(
          "font-semibold text-white",
          className
        )}
        {...props}
      >
        {children}
      </strong>
    ),
  }), []);

  const handleCopyCitation = useCallback(async (citation: Citation, idx: number) => {
    const key = citation.id ?? `citation-${idx}`;
    const title = citation.topic ?? citation.source ?? `Source ${idx + 1}`;
    const detailLines: string[] = [];

    if (citation.topic && citation.source) {
      detailLines.push(`Source: ${citation.source}`);
    } else if (!citation.topic && citation.source) {
      detailLines.push(`Source: ${citation.source}`);
    }

    if (citation.id) {
      detailLines.push(`Reference ID: ${citation.id}`);
    }

    if (citation.url) {
      detailLines.push(`URL: ${citation.url}`);
    }

    const payload = [title, ...detailLines].join("\n");

    try {
      if (!navigator.clipboard) {
        throw new Error("Clipboard not supported");
      }
      await navigator.clipboard.writeText(payload);
      if (citationCopyTimeoutRef.current) {
        clearTimeout(citationCopyTimeoutRef.current);
      }
      setCopiedCitationKey(key);
      citationCopyTimeoutRef.current = window.setTimeout(() => {
        setCopiedCitationKey(null);
        citationCopyTimeoutRef.current = null;
      }, 2400);
    } catch (error) {
      console.warn("Failed to copy citation", error);
      setCopiedCitationKey(null);
    }
  }, []);

  useEffect(() => {
    try {
      // Parse timestamp - ensure it's treated as UTC if it's an ISO string
      const timestamp = message.timestamp;
      
      // Create Date object - JavaScript automatically handles ISO strings with timezone
      // If timestamp is ISO format (e.g., "2025-01-20T17:22:00.000Z"), it will be parsed as UTC
      const date = new Date(timestamp);
      
      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.warn('Invalid timestamp:', timestamp);
        setFormattedTime(timestamp);
        return;
      }
      
      // Format in IST timezone (UTC+5:30)
      const value = new Intl.DateTimeFormat("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
        timeZone: "Asia/Kolkata", // IST timezone
      }).format(date);
      
      setFormattedTime(value);
    } catch (error) {
      console.error('Error formatting timestamp:', error, message.timestamp);
      setFormattedTime(message.timestamp);
    }
  }, [message.timestamp]);

  useEffect(() => {
    return () => {
      if (citationCopyTimeoutRef.current) {
        clearTimeout(citationCopyTimeoutRef.current);
      }
      // Cleanup narration on unmount
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Narration handlers
  const handleNarrationPlay = useCallback(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window) || message.role !== 'assistant') return;
    
    if (narrationState === 'paused') {
      window.speechSynthesis.resume();
      setNarrationState('playing');
    } else {
      const utterance = new SpeechSynthesisUtterance(message.content);
      const langMap: Record<string, string> = {
        'en': 'en-US',
        'hi': 'hi-IN',
        'ta': 'ta-IN',
        'te': 'te-IN',
        'kn': 'kn-IN',
        'ml': 'ml-IN',
      };
      utterance.lang = langMap[language] || 'en-US';
      utterance.rate = 0.92;
      
      utterance.onend = () => setNarrationState('idle');
      utterance.onerror = () => setNarrationState('idle');
      
      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
      setNarrationState('playing');
    }
  }, [message.content, message.role, language, narrationState]);

  const handleNarrationPause = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window && narrationState === 'playing') {
      window.speechSynthesis.pause();
      setNarrationState('paused');
    }
  }, [narrationState]);

  const handleNarrationStop = useCallback(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setNarrationState('idle');
      utteranceRef.current = null;
    }
  }, []);

  // Copy handler - copies rendered content (not markdown)
  const handleCopyRendered = useCallback(async () => {
    if (!contentRef.current) return;
    
    // Get text content from the rendered markdown
    const textContent = contentRef.current.innerText || contentRef.current.textContent || '';
    
    try {
      await navigator.clipboard.writeText(textContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.warn('Failed to copy:', error);
    }
  }, []);

  // Feedback handlers
  const handleFeedback = useCallback((feedback: 'positive' | 'negative') => {
    setFeedbackGiven(feedback);
    if (onFeedback) {
      onFeedback(message.id, feedback);
    }
  }, [message.id, onFeedback]);

  return (
    <article
      className={clsx(
        "flex w-full gap-2 sm:gap-3 md:gap-4 max-w-full overflow-x-hidden",
        alignment[message.role],
        message.role === "assistant" ? "animate-fadeUp" : ""
      )}
      aria-live="polite"
      role="listitem"
      data-message-role={message.role}
      data-testid={`chat-message-${index}`}
    >
      {message.role === "assistant" && (
        <div
          aria-hidden
          className={clsx(
            "mt-1 flex h-8 w-8 sm:h-10 sm:w-10 flex-shrink-0 items-center justify-center rounded-xl sm:rounded-2xl text-[0.65rem] sm:text-xs font-semibold uppercase tracking-[0.28em] sm:tracking-[0.3em]",
            avatarStyles.assistant
          )}
        >
          AI
        </div>
      )}
      <div
        className={clsx(
          "relative max-w-[85%] sm:max-w-[90%] rounded-xl sm:rounded-2xl md:rounded-[26px] px-3 py-3 sm:px-4 sm:py-4 md:px-5 md:py-4 lg:px-6 lg:py-5 transition-all outline-none focus-visible:ring-4 focus-visible:ring-emerald-400/40",
          roleStyles[message.role],
          message.role === "assistant"
            ? "[&::before]:pointer-events-none [&::before]:absolute [&::before]:inset-0 [&::before]:-mt-10 [&::before]:rounded-[32px] [&::before]:bg-gradient-to-br [&::before]:from-emerald-500/10 [&::before]:to-transparent [&::before]:opacity-0 [&::before]:transition-opacity hover:[&::before]:opacity-100"
            : ""
        )}
        tabIndex={0}
      >
        <header className="mb-2 sm:mb-3 md:mb-4 flex items-center justify-between text-[0.65rem] sm:text-xs uppercase tracking-[0.28em] sm:tracking-[0.32em] gap-2">
          <span
            className={clsx(
              "flex items-center gap-1.5 sm:gap-2 font-semibold truncate min-w-0",
              message.role === "assistant" ? "text-emerald-200/80" : "text-white/80"
            )}
          >
            {message.role === "assistant" && (
              <span className="inline-flex h-1.5 w-1.5 sm:h-2 sm:w-2 animate-pulse rounded-full bg-emerald-300 flex-shrink-0" aria-hidden />
            )}
            <span className="truncate">{avatarLabel[message.role]}</span>
          </span>
          <time
            className={clsx(
              "font-medium flex-shrink-0 text-[0.65rem] sm:text-xs",
              message.role === "assistant" ? "text-emerald-200/70" : "text-white/70"
            )}
            dateTime={message.timestamp}
            suppressHydrationWarning
          >
            {formattedTime || ""}
          </time>
        </header>
        <div
          ref={contentRef}
          className={clsx(
            "prose prose-sm sm:prose-base md:prose-lg max-w-none break-words leading-relaxed text-sm sm:text-base",
            message.role === "user"
              ? "prose-invert text-white [&_a]:text-emerald-200 [&_p]:text-sm sm:[&_p]:text-base"
              : "prose-invert text-slate-100 [&_code]:rounded [&_code]:bg-white/10 [&_code]:px-1.5 [&_code]:py-0.5 [&_a]:text-emerald-200 [&_a:hover]:text-emerald-100 [&_p]:text-sm sm:[&_p]:text-base"
          )}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm as any, remarkMath as any]}
            rehypePlugins={[rehypeKatex as any]}
            components={markdownComponents}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {message.citations && Array.isArray(message.citations) && message.citations.length > 0 && (
          <div className="mt-3 sm:mt-4 rounded-xl sm:rounded-2xl border border-white/10 bg-slate-950/60 text-sm text-slate-100 shadow-[0_18px_45px_rgba(15,23,42,0.55)]">
            <button
              type="button"
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
              className="w-full flex items-center justify-between p-3 sm:p-4 text-left transition hover:bg-slate-900/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 rounded-t-xl sm:rounded-t-2xl min-h-[44px]"
              aria-expanded={sourcesExpanded}
              aria-controls={`sources-content-${index}`}
            >
              <p className="text-[0.65rem] sm:text-xs font-semibold uppercase tracking-[0.28em] sm:tracking-[0.32em] text-emerald-200/80">
                Sources ({message.citations.length})
              </p>
              {sourcesExpanded ? (
                <ChevronUp className="h-4 w-4 text-emerald-200/80 flex-shrink-0" aria-hidden />
              ) : (
                <ChevronDown className="h-4 w-4 text-emerald-200/80 flex-shrink-0" aria-hidden />
              )}
            </button>
            {sourcesExpanded && (
              <div id={`sources-content-${index}`} className="px-3 sm:px-4 pb-3 sm:pb-4 space-y-2 sm:space-y-3">
                {message.citations.map((citation, idx) => {
                  const key = citation.id ?? `citation-${idx}`;
                  const headline = citation.topic ?? citation.source ?? `Reference ${idx + 1}`;
                  const supporting: string[] = [];
                  if (citation.topic && citation.source) {
                    supporting.push(citation.source);
                  }
                  if (!citation.topic && citation.source) {
                    supporting.push(citation.source);
                  }
                  if (citation.id) {
                    supporting.push(`ID: ${citation.id}`);
                  }

                  return (
                    <div
                      key={key}
                      className="rounded-lg sm:rounded-xl border border-white/10 bg-slate-900/70 p-3 sm:p-4 shadow-[0_12px_30px_rgba(15,23,42,0.45)]"
                    >
                      <div className="flex flex-col gap-2 sm:gap-3">
                        <div className="space-y-1 min-w-0">
                          <p className="font-semibold text-sm sm:text-base text-slate-100 break-words">{headline}</p>
                          {supporting.length > 0 && (
                            <p className="text-xs text-slate-400 break-words">{supporting.join(' • ')}</p>
                          )}
                          {citation.url && !supporting.includes(citation.url) && (
                            <p className="text-xs text-slate-500 break-all">{citation.url}</p>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            type="button"
                            onClick={() => handleCopyCitation(citation, idx)}
                            className="inline-flex items-center gap-1.5 sm:gap-2 rounded-full border border-white/10 bg-slate-950/70 px-2.5 sm:px-3 py-2 min-h-[44px] text-xs font-semibold text-slate-100 transition hover:border-emerald-300/60 hover:text-emerald-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300"
                          >
                            {copiedCitationKey === key ? (
                              <Check className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                            ) : (
                              <Copy className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                            )}
                            <span className="hidden xs:inline">{copiedCitationKey === key ? 'Copied' : 'Copy notes'}</span>
                            <span className="xs:hidden">{copiedCitationKey === key ? '✓' : 'Copy'}</span>
                          </button>
                          {citation.url && (
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 sm:gap-2 rounded-full border border-transparent bg-gradient-to-r from-emerald-500 via-green-500 to-teal-500 px-2.5 sm:px-3 py-2 min-h-[44px] text-xs font-semibold text-white shadow-[0_10px_30px_rgba(16,185,129,0.35)] transition hover:scale-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300"
                            >
                              <ExternalLink className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" aria-hidden />
                              <span>Open</span>
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Action buttons for assistant messages - below sources section */}
        {message.role === "assistant" && (
          <div className="mt-3 sm:mt-4 flex items-center gap-1.5 sm:gap-2 flex-wrap">
            {/* Narration controls */}
            {typeof window !== 'undefined' && 'speechSynthesis' in window && (
              <div className="flex items-center gap-0.5 sm:gap-1 rounded-full border border-white/10 bg-slate-950/60 p-0.5 sm:p-1">
                {narrationState === 'playing' ? (
                  <button
                    type="button"
                    onClick={handleNarrationPause}
                    className="p-2 sm:p-1.5 rounded-full hover:bg-slate-900/70 transition text-emerald-200 hover:text-emerald-100 min-h-[44px] min-w-[44px] flex items-center justify-center"
                    title="Pause narration"
                    aria-label="Pause narration"
                  >
                    <Pause className="h-4 w-4 sm:h-4 sm:w-4" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={handleNarrationPlay}
                    className="p-2 sm:p-1.5 rounded-full hover:bg-slate-900/70 transition text-emerald-200 hover:text-emerald-100 min-h-[44px] min-w-[44px] flex items-center justify-center"
                    title="Play narration"
                    aria-label="Play narration"
                  >
                    <Play className="h-4 w-4 sm:h-4 sm:w-4" />
                  </button>
                )}
                {narrationState !== 'idle' && (
                  <button
                    type="button"
                    onClick={handleNarrationStop}
                    className="p-2 sm:p-1.5 rounded-full hover:bg-slate-900/70 transition text-emerald-200 hover:text-emerald-100 min-h-[44px] min-w-[44px] flex items-center justify-center"
                    title="Stop narration"
                    aria-label="Stop narration"
                  >
                    <Square className="h-4 w-4 sm:h-4 sm:w-4" />
                  </button>
                )}
              </div>
            )}

            {/* Feedback buttons */}
            <div className="flex items-center gap-0.5 sm:gap-1 rounded-full border border-white/10 bg-slate-950/60 p-0.5 sm:p-1">
              <button
                type="button"
                onClick={() => handleFeedback('positive')}
                className={clsx(
                  "p-2 sm:p-1.5 rounded-full transition min-h-[44px] min-w-[44px] flex items-center justify-center",
                  feedbackGiven === 'positive'
                    ? "bg-emerald-500/20 text-emerald-300"
                    : "hover:bg-slate-900/70 text-slate-300 hover:text-emerald-200"
                )}
                title="Helpful"
                aria-label="Mark as helpful"
              >
                <ThumbsUp className="h-4 w-4 sm:h-4 sm:w-4" />
              </button>
              <button
                type="button"
                onClick={() => handleFeedback('negative')}
                className={clsx(
                  "p-2 sm:p-1.5 rounded-full transition min-h-[44px] min-w-[44px] flex items-center justify-center",
                  feedbackGiven === 'negative'
                    ? "bg-red-500/20 text-red-300"
                    : "hover:bg-slate-900/70 text-slate-300 hover:text-red-200"
                )}
                title="Not helpful"
                aria-label="Mark as not helpful"
              >
                <ThumbsDown className="h-4 w-4 sm:h-4 sm:w-4" />
              </button>
            </div>

            {/* Copy button */}
            <button
              type="button"
              onClick={handleCopyRendered}
              className={clsx(
                "p-2 sm:p-1.5 rounded-full border border-white/10 bg-slate-950/60 transition min-h-[44px] min-w-[44px] flex items-center justify-center",
                copied
                  ? "bg-emerald-500/20 text-emerald-300"
                  : "hover:bg-slate-900/70 text-slate-300 hover:text-emerald-200"
              )}
              title="Copy response"
              aria-label="Copy response"
            >
              {copied ? <Check className="h-4 w-4 sm:h-4 sm:w-4" /> : <Copy className="h-4 w-4 sm:h-4 sm:w-4" />}
            </button>
          </div>
        )}
      </div>
      {message.role === "user" && (
        <div
          aria-hidden
          className={clsx(
            "mt-1 flex h-8 w-8 sm:h-10 sm:w-10 flex-shrink-0 items-center justify-center rounded-xl sm:rounded-2xl text-[0.65rem] sm:text-xs font-semibold uppercase tracking-[0.28em] sm:tracking-[0.3em]",
            avatarStyles.user
          )}
        >
          You
        </div>
      )}
    </article>
  );
}

export default memo(ChatMessage);

