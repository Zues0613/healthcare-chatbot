'use client';

import Link from 'next/link';
import LightRays from './LightRays';

export default function HeroSection() {
  return (
    <section className="relative mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16 lg:flex-row lg:items-center lg:gap-16 lg:px-10 lg:py-24 overflow-hidden">
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
      <div className="relative z-10 flex-1 space-y-8">
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-sm font-semibold text-emerald-200 shadow-[0_12px_35px_rgba(16,185,129,0.25)]">
          <span className="inline-flex h-2.5 w-2.5 animate-pulse rounded-full bg-emerald-300" aria-hidden />
          Always-on Care Navigation
        </div>
        <div className="space-y-5">
          <h1 className="text-4xl font-semibold text-white sm:text-5xl lg:text-6xl">
            One-click clarity for complex health journeys.
          </h1>
          <p className="max-w-2xl text-lg leading-relaxed text-slate-200">
            From symptom triage to warm hand-offs, Health Companion blends compassionate dialogue with
            clinical guardrails. Discover a canvas where glowing analytics, guided workflows, and real-world
            care converge in seconds.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <Link
            href="/auth"
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 px-6 py-3 text-sm font-semibold text-white shadow-[0_22px_45px_rgba(16,185,129,0.35)] transition hover:scale-[1.04]"
          >
            Get Started
          </Link>
          <Link
            href="#insights"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 px-6 py-3 text-sm font-semibold text-slate-100 transition hover:border-white/25 hover:text-white"
          >
            Explore Insights
          </Link>
        </div>
      </div>
      <div className="relative z-10 flex-1 rounded-[32px] border border-white/10 bg-white/5 shadow-[0_30px_90px_rgba(15,23,42,0.55)] backdrop-blur-xl overflow-hidden">
        <div className="h-full flex flex-col p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold uppercase tracking-[0.32em] text-emerald-200/90">
              Live safety pulse
            </p>
            <span className="inline-flex items-center gap-2 text-xs text-slate-200">
              <span className="inline-flex h-2 w-2 animate-ping rounded-full bg-emerald-300" aria-hidden />
              Monitoring
            </span>
          </div>

          {/* Guardrails Card */}
          <div className="rounded-3xl border border-white/10 bg-white/10 p-6 text-slate-100 shadow-inner shadow-emerald-500/10">
            <p className="text-xs uppercase tracking-[0.32em] text-emerald-100/80">Guardrails</p>
            <h3 className="mt-2 text-2xl font-semibold text-white">Red-flag intercept</h3>
            <p className="mt-3 text-sm leading-relaxed text-slate-100/70">
              98% of emergencies flagged before hand-off. Visualize trending symptom signals and confidence
              scores to keep every conversation safe.
            </p>
            <div className="mt-6">
              <div className="flex items-end gap-3">
                {[65, 82, 74, 91].map((value, index) => (
                  <div key={index} className="flex flex-1 flex-col items-center gap-2">
                    <div className="flex w-3 rounded-full bg-emerald-400/30">
                      <div
                        aria-hidden
                        className="mx-auto w-full rounded-full bg-gradient-to-b from-emerald-200 to-emerald-500"
                        style={{ height: `${value}%` }}
                      />
                    </div>
                    <span className="text-[0.6rem] font-semibold uppercase tracking-[0.32em] text-emerald-200/80">
                      wk{index + 1}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Care Loops Card */}
          <div className="rounded-3xl border border-white/10 bg-white/10 p-6 text-slate-100 shadow-inner shadow-emerald-500/10">
            <p className="text-xs uppercase tracking-[0.32em] text-teal-200/80">Care loops</p>
            <h3 className="mt-2 text-xl font-semibold text-white">Return visit readiness</h3>
            <p className="mt-3 text-sm leading-relaxed text-slate-100/70">
              Track adherence, surface nudge moments, and hand off escalations to clinical teams with
              complete context.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

