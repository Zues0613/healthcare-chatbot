'use client';

import Link from 'next/link';
import LightRays from './LightRays';

export default function HeroSection() {
  return (
    <section className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-3 py-8 sm:gap-8 sm:px-4 sm:py-12 md:gap-10 md:px-6 md:py-16 lg:flex-row lg:items-center lg:gap-12 lg:px-10 lg:py-20 xl:py-24 overflow-hidden max-w-full">
      {/* LightRays Animation Background - covers entire section */}
      <div className="absolute inset-0 z-0">
        <LightRays
          raysOrigin="top-center"
          raysColor="#00ffff"
          raysSpeed={1.5}
          lightSpread={0.8}
          rayLength={1.2}
          followMouse={true}
          mouseInfluence={0.1}
          noiseAmount={0.1}
          distortion={0.05}
        />
      </div>
      
      {/* Content with relative z-index to appear above animation */}
      <div className="relative z-10 flex-1 space-y-4 sm:space-y-5 md:space-y-6 lg:space-y-8 min-w-0">
        <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-1.5 text-[0.65rem] font-semibold text-emerald-200 shadow-[0_12px_35px_rgba(16,185,129,0.25)] sm:gap-2 sm:px-3 sm:py-2 sm:text-xs md:text-sm">
          <span className="inline-flex h-1.5 w-1.5 sm:h-2 sm:w-2 md:h-2.5 md:w-2.5 animate-pulse rounded-full bg-emerald-300 flex-shrink-0" aria-hidden />
          <span className="whitespace-nowrap">Always-on Care Navigation</span>
        </div>
        <div className="space-y-3 sm:space-y-4 md:space-y-5">
          <h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl xl:text-5xl 2xl:text-6xl font-semibold text-white leading-tight">
            One-click clarity for complex health journeys.
          </h1>
          <p className="max-w-2xl text-sm sm:text-base md:text-lg leading-relaxed text-slate-200">
            From symptom triage to warm hand-offs, Health Companion blends compassionate dialogue with
            clinical guardrails. Discover a canvas where glowing analytics, guided workflows, and real-world
            care converge in seconds.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2.5 sm:gap-3 md:gap-4">
          <Link
            href="/auth"
            className="inline-flex items-center justify-center gap-1.5 sm:gap-2 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 px-4 py-2.5 min-h-[44px] text-xs font-semibold text-white shadow-[0_22px_45px_rgba(16,185,129,0.35)] transition hover:scale-[1.04] sm:px-5 sm:py-3 sm:text-sm"
          >
            Get Started
          </Link>
          <Link
            href="#insights"
            className="inline-flex items-center justify-center gap-1.5 sm:gap-2 rounded-full border border-white/10 px-4 py-2.5 min-h-[44px] text-xs font-semibold text-slate-100 transition hover:border-white/25 hover:text-white sm:px-5 sm:py-3 sm:text-sm"
          >
            Explore Insights
          </Link>
        </div>
      </div>
      <div className="relative z-10 flex-1 rounded-xl sm:rounded-2xl border border-white/10 bg-white/5 shadow-[0_30px_90px_rgba(15,23,42,0.55)] backdrop-blur-xl overflow-hidden md:rounded-3xl lg:rounded-[32px] mt-4 sm:mt-0">
        <div className="h-full flex flex-col p-3 space-y-3 sm:p-4 sm:space-y-4 md:p-5 md:space-y-5 lg:p-6 lg:space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <p className="text-[0.6rem] sm:text-[0.65rem] md:text-xs font-semibold uppercase tracking-[0.28em] sm:tracking-[0.32em] text-emerald-200/90">
              Live safety pulse
            </p>
            <span className="inline-flex items-center gap-1 sm:gap-1.5 md:gap-2 text-[0.6rem] sm:text-[0.65rem] md:text-xs text-slate-200">
              <span className="inline-flex h-1.5 w-1.5 sm:h-2 sm:w-2 animate-ping rounded-full bg-emerald-300 flex-shrink-0" aria-hidden />
              <span>Monitoring</span>
            </span>
          </div>

          {/* Guardrails Card */}
          <div className="rounded-xl sm:rounded-2xl border border-white/10 bg-white/10 p-3 text-slate-100 shadow-inner shadow-emerald-500/10 md:rounded-3xl sm:p-4 md:p-5 lg:p-6">
            <p className="text-[0.6rem] sm:text-[0.65rem] md:text-xs uppercase tracking-[0.28em] sm:tracking-[0.32em] text-emerald-100/80">Guardrails</p>
            <h3 className="mt-1.5 text-base sm:text-lg md:text-xl lg:text-2xl font-semibold text-white leading-tight">Red-flag intercept</h3>
            <p className="mt-2 text-xs sm:text-sm leading-relaxed text-slate-100/70">
              98% of emergencies flagged before hand-off. Visualize trending symptom signals and confidence
              scores to keep every conversation safe.
            </p>
            <div className="mt-3 sm:mt-4 md:mt-6">
              <div className="flex items-end gap-1.5 sm:gap-2 md:gap-3">
                {[65, 82, 74, 91].map((value, index) => (
                  <div key={index} className="flex flex-1 flex-col items-center gap-1 sm:gap-1.5 md:gap-2">
                    <div className="flex w-2 sm:w-2.5 md:w-3 rounded-full bg-emerald-400/30">
                      <div
                        aria-hidden
                        className="mx-auto w-full rounded-full bg-gradient-to-b from-emerald-200 to-emerald-500"
                        style={{ height: `${value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Care Loops Card */}
          <div className="rounded-xl sm:rounded-2xl border border-white/10 bg-white/10 p-3 text-slate-100 shadow-inner shadow-emerald-500/10 md:rounded-3xl sm:p-4 md:p-5 lg:p-6">
            <p className="text-[0.6rem] sm:text-[0.65rem] md:text-xs uppercase tracking-[0.28em] sm:tracking-[0.32em] text-teal-200/80">Care loops</p>
            <h3 className="mt-1.5 text-sm sm:text-base md:text-lg lg:text-xl font-semibold text-white leading-tight">Return visit readiness</h3>
            <p className="mt-2 text-xs sm:text-sm leading-relaxed text-slate-100/70">
              Track adherence, surface nudge moments, and hand off escalations to clinical teams with
              complete context.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

