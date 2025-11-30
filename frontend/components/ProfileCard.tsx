"use client";

import { useMemo } from "react";
import clsx from "clsx";

interface ProfileStat {
  label: string;
  value: string;
  icon?: React.ReactNode;
  highlights?: string[];
}

interface ProfileCardProps {
  loading: boolean;
  name: string;
  avatarColor?: "teal" | "mint" | "blue";
  stats: ProfileStat[];
  onEdit?: () => void;
}

const gradientMap: Record<string, string> = {
  teal: "from-emerald-500 via-green-500 to-teal-500",
  mint: "from-green-500 via-emerald-500 to-teal-500",
  blue: "from-teal-500 via-green-500 to-emerald-500",
};

export default function ProfileCard({
  loading,
  name,
  avatarColor = "teal",
  stats,
  onEdit,
}: ProfileCardProps) {
  const gradient = useMemo(
    () => gradientMap[avatarColor] ?? gradientMap.teal,
    [avatarColor]
  );

  if (loading) {
    return (
      <div
        className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/60 p-6 shadow-[0_18px_45px_rgba(15,23,42,0.55)] backdrop-blur animate-pulse"
        aria-busy="true"
        aria-live="polite"
      >
        <div className="h-4 w-1/2 rounded-full bg-emerald-500/30" />
        <div className="flex gap-3">
          <div className="h-10 w-10 rounded-full bg-emerald-500/30" />
          <div className="flex-1 space-y-2">
            <div className="h-4 w-1/3 rounded-full bg-emerald-500/30" />
            <div className="h-4 w-2/3 rounded-full bg-emerald-500/30" />
          </div>
        </div>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <div className="h-4 rounded-full bg-emerald-500/30" />
          <div className="h-4 rounded-full bg-emerald-500/30" />
          <div className="h-4 rounded-full bg-emerald-500/30" />
          <div className="h-4 rounded-full bg-emerald-500/30" />
        </div>
      </div>
    );
  }

  return (
    <section
      className="relative overflow-hidden rounded-2xl sm:rounded-3xl border border-white/10 bg-slate-950/60 p-4 sm:p-5 md:p-6 shadow-[0_25px_60px_rgba(15,23,42,0.55)] backdrop-blur transition"
      aria-label="Profile summary"
    >
      <div
        className={clsx(
          "absolute inset-y-0 right-0 w-[45%] opacity-30 blur-3xl",
          `bg-gradient-to-br ${gradient}`
        )}
        aria-hidden
      />
      <div className="relative flex items-center gap-3 sm:gap-4 border-b border-white/10 pb-4 sm:pb-5">
        <div
          className={clsx(
            "flex h-10 w-10 sm:h-12 sm:w-12 items-center justify-center rounded-full text-base sm:text-lg font-semibold text-white shadow-[0_10px_30px_rgba(16,185,129,0.35)] flex-shrink-0",
            `bg-gradient-to-br ${gradient}`
          )}
          aria-hidden
        >
          {name.slice(0, 1).toUpperCase()}
        </div>
        <div className="flex flex-1 flex-col min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[0.65rem] sm:text-xs font-semibold uppercase tracking-[0.3em] sm:tracking-[0.35em] text-emerald-300/80 truncate">
              Health profile
            </p>
            {onEdit && (
              <button
                onClick={onEdit}
                className="rounded-full border border-emerald-400/40 bg-gradient-to-r from-emerald-500/20 via-green-500/15 to-teal-500/20 px-2.5 sm:px-3.5 py-1.5 sm:py-1 min-h-[44px] text-[0.65rem] sm:text-[11px] font-semibold uppercase tracking-[0.28em] sm:tracking-[0.3em] text-emerald-200 transition hover:border-emerald-400/60 hover:from-emerald-500/30 hover:via-green-500/25 hover:to-teal-500/30 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 flex-shrink-0"
              >
                Update
              </button>
            )}
          </div>
          <h2 className="mt-1 text-base sm:text-lg font-semibold text-white truncate">{name}</h2>
        </div>
      </div>

      <dl className="relative mt-4 sm:mt-5 grid gap-2.5 sm:gap-3 grid-cols-1 sm:grid-cols-2">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="flex h-full flex-col gap-2 rounded-xl sm:rounded-2xl border border-white/10 bg-slate-900/60 px-3 sm:px-4 py-2.5 sm:py-3 shadow-[0_12px_30px_rgba(15,23,42,0.45)] transition hover:border-emerald-400/30 hover:shadow-[0_18px_45px_rgba(16,185,129,0.18)]"
          >
            <dt className="flex items-center gap-1.5 sm:gap-2 text-[0.65rem] sm:text-[11px] font-semibold uppercase tracking-[0.3em] sm:tracking-[0.35em] text-emerald-300/70">
              {stat.icon && (
                <span className="flex h-6 w-6 sm:h-7 sm:w-7 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/20 via-green-500/15 to-teal-500/20 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.2)] flex-shrink-0">
                  {stat.icon}
                </span>
              )}
              <span className="truncate">{stat.label}</span>
            </dt>
            <dd className="text-xs sm:text-sm font-semibold text-slate-200 break-words">
              {stat.highlights && stat.highlights.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {stat.highlights.map((highlight) => (
                    <span
                      key={highlight}
                      className="rounded-full bg-gradient-to-r from-emerald-500/20 via-green-500/15 to-teal-500/20 border border-emerald-400/30 px-2.5 py-1 text-xs font-medium text-emerald-200 shadow-[0_0_10px_rgba(16,185,129,0.15)]"
                    >
                      {highlight}
                    </span>
                  ))}
                </div>
              ) : (
                stat.value
              )}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

