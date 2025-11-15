"use client";

import { useMemo, useState } from "react";
import clsx from "clsx";
import { Search, Sparkles } from "lucide-react";
import { TOPIC_CATEGORIES, type TopicCategory, type TopicSuggestion } from "../data/topics";

interface TopicSuggestionsProps {
  onSuggestionSelect: (prompt: string) => void;
  onAfterSelect?: () => void;
}

interface PreparedCategory extends TopicCategory {
  matches: number;
}

function matchScore(text: string, query: string): number {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) return 0;
  const haystack = text.toLowerCase();
  let score = 0;
  normalizedQuery
    .split(/\s+/)
    .filter(Boolean)
    .forEach((token) => {
      if (haystack.includes(token)) {
        score += 1;
      }
    });
  return score;
}

const iconMap: Record<string, string> = {
  "alert-triangle": "⚠️",
  heart: "❤️",
  activity: "🩺",
  shield: "🛡️",
  users: "👥",
};

export default function TopicSuggestions({ onSuggestionSelect, onAfterSelect }: TopicSuggestionsProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeCategoryId, setActiveCategoryId] = useState<string>(TOPIC_CATEGORIES[0]?.id ?? "");

  const { categories, suggestions } = useMemo(() => {
    const preparedCategories: PreparedCategory[] = TOPIC_CATEGORIES.map((category) => {
      const match = matchScore(`${category.title} ${category.description}`, searchTerm);
      return { ...category, matches: match };
    });

    preparedCategories.sort((a, b) => {
      if (a.matches === b.matches) {
        return a.title.localeCompare(b.title);
      }
      return b.matches - a.matches;
    });

    const baseCategory = preparedCategories.find((category) => category.id === activeCategoryId) ?? preparedCategories[0];
    const normalizedTerm = searchTerm.trim().toLowerCase();
    const flattenedSuggestions = (normalizedTerm
      ? preparedCategories
          .flatMap((category) =>
            category.suggestions.map((suggestion) => ({
              category,
              suggestion,
              score:
                matchScore(`${suggestion.prompt} ${(suggestion.tags ?? []).join(" ")}`, normalizedTerm) +
                matchScore(`${category.title} ${category.description}`, normalizedTerm) * 0.5,
            }))
          )
          .filter((item) => item.score > 0)
          .sort((a, b) => {
            if (b.score === a.score) {
              return a.suggestion.prompt.localeCompare(b.suggestion.prompt);
            }
            return b.score - a.score;
          })
          .slice(0, 12)
      : baseCategory.suggestions.map((suggestion) => ({
          category: baseCategory,
          suggestion,
          score: 0,
        })));

    return {
      categories: preparedCategories,
      suggestions: flattenedSuggestions,
    };
  }, [activeCategoryId, searchTerm]);

  const handleSelect = (item: TopicSuggestion) => {
    onSuggestionSelect(item.prompt);
    onAfterSelect?.();
  };

  const hasSearchTerm = Boolean(searchTerm && searchTerm.trim().length > 0);

  return (
    <section className="space-y-4" aria-label="Topic suggestions">
      {!hasSearchTerm ? (
        <>
          <header className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-300/70">Browse topics</p>
            <h3 className="text-lg font-semibold text-white">Get started quickly</h3>
            <p className="text-sm text-slate-300">
              Explore popular questions or search for specific symptoms, conditions, or self-care goals.
            </p>
          </header>

          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search topics, e.g. headache, diabetes, stress"
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-10 py-2 text-sm text-slate-100 shadow-inner shadow-black/20 transition focus:border-emerald-300/60 focus:outline-none focus:ring-4 focus:ring-emerald-500/15"
              aria-label="Search care topics"
            />
          </div>

          <div className="flex flex-wrap gap-2 justify-center" role="list">
            {categories.map((category) => {
              const isActive = category.id === activeCategoryId;
              const fallbackIcon = iconMap[category.icon] ?? "✨";
              return (
                <button
                  key={category.id}
                  type="button"
                  role="listitem"
                  onClick={() => {
                    setActiveCategoryId(category.id);
                    setSearchTerm("");
                  }}
                  className={clsx(
                    "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
                    isActive
                      ? "border-emerald-400/70 bg-emerald-500/20 text-emerald-100 focus-visible:outline-emerald-300"
                      : "border-white/10 bg-slate-900/60 text-slate-200 hover:border-emerald-300/50 hover:text-emerald-100 focus-visible:outline-emerald-200"
                  )}
                >
                  <span aria-hidden>{fallbackIcon}</span>
                  {category.title}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap gap-2 justify-center" role="list">
            {suggestions.length === 0 ? (
              <div className="w-full rounded-2xl border border-white/10 bg-slate-900/60 p-4 text-sm text-slate-300">
                No suggestions available.
              </div>
            ) : (
              suggestions.map(({ category, suggestion }) => (
                <button
                  key={suggestion.id}
                  type="button"
                  role="listitem"
                  onClick={() => handleSelect(suggestion)}
                  className="group relative inline-flex flex-col items-start gap-2 rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-left shadow-[0_8px_25px_rgba(15,23,42,0.35)] transition-all hover:border-emerald-400/50 hover:bg-slate-900/80 hover:shadow-[0_12px_35px_rgba(16,185,129,0.25)] hover:scale-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 max-w-xs"
                >
                  <div className="flex items-center gap-2 w-full">
                    <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-sm">
                      {iconMap[category.icon] ?? "✨"}
                    </span>
                    <p className="text-[0.65rem] uppercase tracking-[0.2em] text-emerald-300/70 truncate flex-1">
                      {category.title}
                    </p>
                  </div>
                  <p className="text-xs font-semibold text-slate-100 leading-tight line-clamp-2">
                    {suggestion.prompt}
                  </p>
                  {suggestion.tags && suggestion.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 w-full">
                      {suggestion.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="inline-flex items-center rounded-full border border-emerald-200/30 bg-emerald-500/10 px-2 py-0.5 text-[0.65rem] text-emerald-200/90">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Sparkles className="h-3 w-3 text-emerald-300" aria-hidden />
                  </div>
                </button>
              ))
            )}
          </div>
        </>
      ) : (
        <>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => {
                setSearchTerm(event.target.value);
              }}
              placeholder="Search topics, e.g. headache, diabetes, stress"
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-10 py-2 text-sm text-slate-100 shadow-inner shadow-black/20 transition focus:border-emerald-300/60 focus:outline-none focus:ring-4 focus:ring-emerald-500/15"
              aria-label="Search care topics"
            />
          </div>

          <div className="flex flex-wrap gap-2 justify-center" role="list">
            {suggestions.length === 0 ? (
              <div className="w-full rounded-2xl border border-white/10 bg-slate-900/60 p-4 text-sm text-slate-300">
                No quick prompts found. Try a different keyword like "cough" or "nutrition".
              </div>
            ) : (
              suggestions.map(({ category, suggestion }) => (
                <button
                  key={suggestion.id}
                  type="button"
                  role="listitem"
                  onClick={() => handleSelect(suggestion)}
                  className="group relative inline-flex flex-col items-start gap-2 rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-left shadow-[0_8px_25px_rgba(15,23,42,0.35)] transition-all hover:border-emerald-400/50 hover:bg-slate-900/80 hover:shadow-[0_12px_35px_rgba(16,185,129,0.25)] hover:scale-[1.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 max-w-xs"
                >
                  <div className="flex items-center gap-2 w-full">
                    <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-sm">
                      {iconMap[category.icon] ?? "✨"}
                    </span>
                    <p className="text-[0.65rem] uppercase tracking-[0.2em] text-emerald-300/70 truncate flex-1">
                      {category.title}
                    </p>
                  </div>
                  <p className="text-xs font-semibold text-slate-100 leading-tight line-clamp-2">
                    {suggestion.prompt}
                  </p>
                  {suggestion.tags && suggestion.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 w-full">
                      {suggestion.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="inline-flex items-center rounded-full border border-emerald-200/30 bg-emerald-500/10 px-2 py-0.5 text-[0.65rem] text-emerald-200/90">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Sparkles className="h-3 w-3 text-emerald-300" aria-hidden />
                  </div>
                </button>
              ))
            )}
          </div>
        </>
      )}
    </section>
  );
}
