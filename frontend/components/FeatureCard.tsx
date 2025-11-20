'use client';

import clsx from 'clsx';
import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Feature {
  title: string;
  description: string;
  points: string[];
  accent: string;
}

interface FeatureCardProps {
  feature: Feature;
}

export default function FeatureCard({ feature }: FeatureCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <article
      className="relative flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-slate-950/70 p-4 shadow-[0_30px_85px_rgba(15,23,42,0.55)] backdrop-blur-xl transition-all sm:rounded-3xl sm:p-5 md:rounded-[28px] md:p-6"
    >
      <div
        className={clsx(
          "pointer-events-none absolute inset-0 -z-10 opacity-60 blur-3xl transition-opacity duration-300",
          isExpanded && "opacity-80",
          `bg-gradient-to-br ${feature.accent}`
        )}
        aria-hidden
      />
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="text-left w-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
        aria-expanded={isExpanded}
        aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${feature.title} details`}
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-lg font-semibold text-white sm:text-xl flex-1">{feature.title}</h3>
          {feature.points.length > 0 && (
            <div className="flex-shrink-0 mt-1">
              {isExpanded ? (
                <ChevronUp className="h-5 w-5 text-emerald-400" aria-hidden />
              ) : (
                <ChevronDown className="h-5 w-5 text-emerald-400" aria-hidden />
              )}
            </div>
          )}
        </div>
      </button>
      
      <p className={clsx(
        "mt-2 text-xs leading-relaxed text-slate-200/80 sm:mt-3 sm:text-sm transition-all duration-300",
        isExpanded ? "" : "line-clamp-3"
      )}>
        {feature.description}
      </p>
      
      {/* Points - expandable/collapsible */}
      {feature.points.length > 0 && (
        <div className={clsx(
          "mt-4 space-y-2 overflow-hidden transition-all duration-300 sm:mt-5 sm:space-y-3",
          isExpanded ? "opacity-100 max-h-[1000px]" : "opacity-0 max-h-0"
        )}>
          <ul className="text-xs text-slate-100/80 sm:text-sm">
            {feature.points.map((point, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-white/60 flex-shrink-0" aria-hidden />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Click indicator */}
      {feature.points.length > 0 && !isExpanded && (
        <div className="mt-3 text-xs text-emerald-400/60 flex items-center gap-1">
          <span>Click to {isExpanded ? 'collapse' : 'expand'} details</span>
        </div>
      )}
    </article>
  );
}

