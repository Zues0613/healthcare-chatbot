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
import { Check, Copy, ExternalLink } from "lucide-react";
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
          className="rounded-full border border-white/10 px-3 py-1 text-[0.65rem] font-semibold tracking-[0.28em] text-slate-300 transition group-hover:border-pink-300/60 group-hover:text-pink-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
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
}

const roleStyles: Record<ChatRole, string> = {
  user:
    "border border-transparent bg-gradient-to-br from-pink-500 via-fuchsia-500 to-purple-500 text-white shadow-[0_25px_70px_rgba(236,72,153,0.30)]",
  assistant:
    "border border-white/10 bg-slate-950/70 backdrop-blur text-slate-100 shadow-[0_30px_85px_rgba(15,23,42,0.55)]",
};

const alignment: Record<ChatRole, string> = {
  user: "items-end justify-end",
  assistant: "items-start justify-start",
};

const avatarStyles: Record<ChatRole, string> = {
  user:
    "bg-gradient-to-br from-fuchsia-500/80 via-pink-500/90 to-purple-500 shadow-[0_10px_30px_rgba(236,72,153,0.45)] text-white",
  assistant:
    "bg-slate-900/80 backdrop-blur border border-white/10 text-pink-200 shadow-[0_12px_35px_rgba(15,23,42,0.45)]",
};

const avatarLabel: Record<ChatRole, string> = {
  user: "You",
  assistant: "Care Guide",
};

interface ChatMessageProps {
  message: ChatMessageModel;
  index: number;
  isHighlighted?: boolean;
}

function ChatMessage({ message, index, isHighlighted = false }: ChatMessageProps) {
  const [formattedTime, setFormattedTime] = useState<string>("");
  const [copiedCitationKey, setCopiedCitationKey] = useState<string | null>(null);
  const citationCopyTimeoutRef = useRef<number | null>(null);

  const markdownComponents: Components = useMemo(() => ({
    a: ({ children, className, ...props }) => (
      <a
        className={clsx(
          "font-semibold text-pink-200 underline decoration-pink-200/30 underline-offset-4 transition hover:text-pink-100",
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
          "[&_a]:text-pink-200 [&_a:hover]:text-pink-100 marker:text-pink-300",
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
          "my-4 border-l-4 border-pink-400/60 bg-white/5 px-4 py-2 italic text-pink-100/90",
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
              "rounded bg-white/10 px-1.5 py-0.5 font-medium text-pink-100",
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
            "w-full border-collapse text-sm text-slate-100 [&_th]:bg-white/5 [&_th]:text-left [&_th]:font-semibold [&_th]:uppercase [&_th]:tracking-[0.2em] [&_th]:text-pink-200/80 [&_td]:border-t [&_td]:border-white/10 [&_td]:px-4 [&_td]:py-3 [&_th]:px-4 [&_th]:py-3",
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
          "mb-2 mt-4 text-base font-semibold uppercase tracking-[0.28em] text-pink-200",
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
      const value = new Intl.DateTimeFormat("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      }).format(new Date(message.timestamp));
      setFormattedTime(value);
    } catch (error) {
      setFormattedTime(message.timestamp);
    }
  }, [message.timestamp]);

  useEffect(() => {
    return () => {
      if (citationCopyTimeoutRef.current) {
        clearTimeout(citationCopyTimeoutRef.current);
      }
    };
  }, []);

  return (
    <article
      className={clsx(
        "flex w-full gap-3 sm:gap-4",
        alignment[message.role],
        message.role === "assistant" ? "animate-fadeUp" : ""
      )}
      aria-live="polite"
      role="listitem"
      data-message-role={message.role}
      data-message-id={message.id}
      data-testid={`chat-message-${index}`}
    >
      {message.role === "assistant" && (
        <div
          aria-hidden
          className={clsx(
            "mt-1 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl text-xs font-semibold uppercase tracking-[0.3em]",
            avatarStyles.assistant
          )}
        >
          AI
        </div>
      )}
      <div
        className={clsx(
          "relative max-w-[90%] rounded-[26px] px-5 py-4 md:px-6 md:py-5 transition-all outline-none focus-visible:ring-4 focus-visible:ring-pink-400/40",
          roleStyles[message.role],
          message.role === "assistant"
            ? "[&::before]:pointer-events-none [&::before]:absolute [&::before]:inset-0 [&::before]:-mt-10 [&::before]:rounded-[32px] [&::before]:bg-gradient-to-br [&::before]:from-pink-500/10 [&::before]:to-transparent [&::before]:opacity-0 [&::before]:transition-opacity hover:[&::before]:opacity-100"
            : "",
          isHighlighted ? "ring-2 ring-pink-300/70 shadow-[0_0_45px_rgba(236,72,153,0.45)]" : ""
        )}
        tabIndex={0}
      >
        <header className="mb-3 flex items-center justify-between text-xs uppercase tracking-[0.32em]">
          <span
            className={clsx(
              "flex items-center gap-2 font-semibold",
              message.role === "assistant" ? "text-pink-200/80" : "text-white/80"
            )}
          >
            {message.role === "assistant" && (
              <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-pink-300" aria-hidden />
            )}
            {avatarLabel[message.role]}
          </span>
          <time
            className={clsx(
              "font-medium",
              message.role === "assistant" ? "text-pink-200/70" : "text-white/70"
            )}
            dateTime={message.timestamp}
            suppressHydrationWarning
          >
            {formattedTime || ""}
          </time>
        </header>
        <div
          className={clsx(
            "prose prose-sm md:prose-base max-w-none break-words leading-relaxed",
            message.role === "user"
              ? "prose-invert text-white [&_a]:text-pink-200"
              : "prose-invert text-slate-100 [&_code]:rounded [&_code]:bg-white/10 [&_code]:px-1.5 [&_code]:py-0.5 [&_a]:text-pink-200 [&_a:hover]:text-pink-100"
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

        {message.citations && message.citations.length > 0 && (
          <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-100 shadow-[0_18px_45px_rgba(15,23,42,0.55)]">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.32em] text-pink-200/80">
              Sources
            </p>
            <div className="space-y-3">
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
                    className="rounded-xl border border-white/10 bg-slate-900/70 p-4 shadow-[0_12px_30px_rgba(15,23,42,0.45)]"
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="space-y-1">
                        <p className="font-semibold text-slate-100">{headline}</p>
                        {supporting.length > 0 && (
                          <p className="text-xs text-slate-400">{supporting.join(' • ')}</p>
                        )}
                        {citation.url && !supporting.includes(citation.url) && (
                          <p className="text-xs text-slate-500">{citation.url}</p>
                        )}
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleCopyCitation(citation, idx)}
                          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/70 px-3 py-1.5 text-xs font-semibold text-slate-100 transition hover:border-pink-300/60 hover:text-pink-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
                        >
                          {copiedCitationKey === key ? (
                            <Check className="h-4 w-4" aria-hidden />
                          ) : (
                            <Copy className="h-4 w-4" aria-hidden />
                          )}
                          {copiedCitationKey === key ? 'Copied' : 'Copy notes'}
                        </button>
                        {citation.url && (
                          <a
                            href={citation.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 rounded-full border border-transparent bg-gradient-to-r from-pink-500 via-fuchsia-500 to-purple-500 px-3 py-1.5 text-xs font-semibold text-white shadow-[0_10px_30px_rgba(236,72,153,0.35)] transition hover:scale-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pink-300"
                          >
                            <ExternalLink className="h-4 w-4" aria-hidden />
                            Open
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
      {message.role === "user" && (
        <div
          aria-hidden
          className={clsx(
            "mt-1 flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl text-xs font-semibold uppercase tracking-[0.3em]",
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

