'use client';

import clsx from 'clsx';

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
  return (
    <article
      className="group relative flex h-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-slate-950/70 p-4 shadow-[0_30px_85px_rgba(15,23,42,0.55)] backdrop-blur-xl transition-all hover:border-emerald-400/30 hover:shadow-[0_35px_95px_rgba(16,185,129,0.25)] sm:rounded-3xl sm:p-5 md:rounded-[28px] md:p-6"
    >
      <div
        className={clsx(
          "pointer-events-none absolute inset-0 -z-10 opacity-60 blur-3xl transition-opacity duration-300 group-hover:opacity-80",
          `bg-gradient-to-br ${feature.accent}`
        )}
        aria-hidden
      />
      <h3 className="text-lg font-semibold text-white sm:text-xl">{feature.title}</h3>
      
      <p className="mt-2 text-xs leading-relaxed text-slate-200/80 sm:mt-3 sm:text-sm line-clamp-3 group-hover:line-clamp-none transition-all duration-300">
        {feature.description}
      </p>
      
      {/* Points - hidden by default, shown on hover/touch */}
      {feature.points.length > 0 && (
        <div className="mt-4 space-y-2 opacity-0 max-h-0 overflow-hidden transition-all duration-300 group-hover:opacity-100 group-hover:max-h-[1000px] sm:mt-5 sm:space-y-3">
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
      
      {/* Hint indicator - shown when not hovered */}
      <div className="mt-3 text-xs text-emerald-400/60 transition-opacity duration-300 group-hover:opacity-0">
        <span className="sm:hidden">Tap to view details</span>
        <span className="hidden sm:inline">Hover to view details</span>
      </div>
    </article>
  );
}

