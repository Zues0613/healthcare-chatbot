import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import clsx from "clsx";
import AnimatedNumber from "../../components/AnimatedNumber";
import HeroSection from "../../components/HeroSection";

export const metadata: Metadata = {
  title: "Health Companion | Intelligent Care Guidance",
  description:
    "Explore the future of accessible care with our AI assistant. Discover features, workflows, and insights built to empower healthier journeys.",
};

const gradientSpot = (
  position: string,
  color: string,
  size: string,
  blur = "blur-3xl"
) =>
  clsx(
    "pointer-events-none absolute rounded-full opacity-70 mix-blend-screen",
    position,
    color,
    size,
    blur
  );

const features = [
  {
    title: "Red-flag Intelligence",
    description:
      "Extensive rule graphs, streaming heuristics, and linguistic fallbacks catch emergent risks in English or transliterated scripts before they escalate.",
    points: [
      "98.2% safety coverage across cardiology, neuro, pediatrics, and OB",
      "Real-time hand-offs to clinicians with contextual transcripts",
      "Covers 180+ critical symptoms and lifestyle risk factors",
    ],
    accent: "from-emerald-500 via-green-500 to-teal-500",
  },
  {
    title: "Knowledge Fusion",
    description:
      "Hybrid retrieval blends Chroma vector search, Neo4j reasoning, and curated care guides to answer responsibly every time.",
    points: [
      "1,120 YAML+markdown care protocols indexed",
      "Chroma DB 92.7% top-3 semantic recall with BM25 fallback",
      "Neo4j fallback enriches RAG with contraindications and provider graphs",
    ],
    accent: "from-green-500 via-emerald-500 to-teal-500",
  },
  {
    title: "Care Team Command",
    description:
      "Export transcripts, broadcast follow-ups, and trigger automated care plans without leaving the assistant interface.",
    points: [
      "Automated summaries and task lists for clinical threads",
      "Localized reminders with SMS / email hooks",
      "Deployed in 12 languages with 3 dialect fallbacks",
    ],
    accent: "from-teal-500 via-emerald-500 to-green-500",
  },
];

const workflows = [
  {
    title: "Symptom Companion",
    description:
      "Guide users through nuanced symptom check-ins with clarifying questions, reassurance, and evidence-based watch-outs.",
  },
  {
    title: "Care Navigation",
    description:
      "Highlight nearby clinics, remote visit options, and specialized resources that match urgency and preference.",
  },
  {
    title: "Medication Moments",
    description:
      "Surface contraindications, dosing reminders, and supportive self-care tips framed in everyday language.",
  },
];

const techStack = [
  {
    name: "Next.js + React",
    details:
      "Modern SSR/ISR experience with streaming UI, suspense states, and optimistic input surfaces for live care sessions.",
  },
  {
    name: "LangChain + Open Router",
    details:
      "Guardrailed LLM orchestration with prompt templates, system safety, and model failovers tuned for clinical empathy.",
  },
  {
    name: "Chroma DB",
    details:
      "Dense retrieval over 1.1K medical briefs and protocol sheets, 92.7% top-3 semantic recall with BM25 hybrid rerank.",
  },
  {
    name: "Neo4j Fallback",
    details:
      "Knowledge graph of contraindications, providers, and red-flag rules powering deterministic answers when LLMs defer.",
  },
  {
    name: "Audio Stack",
    details:
      "Whisper multilingual STT, ElevenLabs + gTTS TTS, and noise suppression tuned for remote consultations.",
  },
];

const dataHighlights = [
  {
    title: "Chroma Coverage",
    value: "92.7%",
    description: "Top-3 recall across 1,120 markdown protocols, refreshed nightly with YAML front-matter validation.",
  },
  {
    title: "Neo4j Advantages",
    value: "Graph",
    description: "Fallback graph answers sub-second: contraindications, personalized safety nets, and provider networks.",
  },
  {
    title: "Markdown Library",
    value: "1.1K",
    description: "Curated condition briefs, red-flag playbooks, triage scripts, and lifestyle counselling assets.",
  },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(16,185,129,0.25),transparent_55%),radial-gradient(circle_at_85%_15%,rgba(34,197,94,0.24),transparent_55%),linear-gradient(180deg,rgba(2,6,23,0.92),rgba(2,6,23,0.97))]" />
      <div className={gradientSpot("top-[-8rem] left-[-6rem]", "bg-emerald-500/40", "h-72 w-72")} />
      <div className={gradientSpot("top-[-4rem] right-[-4rem]", "bg-green-500/35", "h-64 w-64")} />
      <div className={gradientSpot("bottom-[-6rem] right-[-10rem]", "bg-teal-500/30", "h-80 w-80")} />

      <header className="relative z-10 border-b border-white/5 bg-slate-950/60 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6 lg:px-10">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-lg font-semibold text-white shadow-[0_15px_35px_rgba(16,185,129,0.35)]">
              HC
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-300/80">
                Health Companion
              </p>
              <p className="text-sm font-semibold text-white">Care Intelligence Platform</p>
            </div>
          </div>
          <nav className="hidden items-center gap-8 text-sm text-slate-200 sm:flex">
            <a className="hover:text-white" href="#features">
              Features
            </a>
            <a className="hover:text-white" href="#workflows">
              Workflows
            </a>
            <a className="hover:text-white" href="#insights">
              Insights
            </a>
            <a className="hover:text-white" href="#cta">
              Get Started
            </a>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href="/landing#insights"
              className="hidden rounded-full border border-white/10 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-white/30 hover:text-white sm:inline-flex"
            >
              View Insights
            </Link>
            <Link
              href="/auth"
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 px-4 py-2 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(16,185,129,0.35)] transition hover:scale-[1.03]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="relative z-10">
        <HeroSection />

        <section id="features" className="mx-auto w-full max-w-6xl px-6 py-16 lg:px-10 lg:py-20">
          <div className="mb-10 flex flex-col gap-4 text-center sm:text-left">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-200/80">Why teams choose us</p>
            <h2 className="text-3xl font-semibold text-white sm:text-4xl">Features crafted for clinical-grade conversations.</h2>
            <p className="max-w-3xl text-sm leading-relaxed text-slate-200/80">
              We blend AI expressiveness with deterministic checks. Every tile below represents an orchestrated system
              – not a lone model – ensuring safe, multi-lingual, empathetic care guidance.
            </p>
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            {features.map((feature) => (
              <article
                key={feature.title}
                className="relative flex h-full flex-col overflow-hidden rounded-[28px] border border-white/10 bg-slate-950/70 p-6 shadow-[0_30px_85px_rgba(15,23,42,0.55)] backdrop-blur-xl"
              >
                <div
                  className={clsx(
                    "pointer-events-none absolute inset-0 -z-10 opacity-60 blur-3xl",
                    `bg-gradient-to-br ${feature.accent}`
                  )}
                  aria-hidden
                />
                <h3 className="text-xl font-semibold text-white">{feature.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-200/80">{feature.description}</p>
                <ul className="mt-5 space-y-3 text-sm text-slate-100/80">
                  {feature.points.map((point) => (
                    <li key={point} className="flex items-start gap-2">
                      <span className="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-white/60" aria-hidden />
                      <span>{point}</span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section id="workflows" className="mx-auto w-full max-w-6xl px-6 py-16 lg:px-10 lg:py-20">
          <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
            <div className="space-y-8 rounded-[32px] border border-white/10 bg-gradient-to-br from-teal-900/60 via-slate-950/80 to-slate-950/90 p-8 shadow-[0_35px_95px_rgba(15,23,42,0.6)] backdrop-blur-2xl">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-200/80">
                Step-by-step clarity
              </p>
              <div className="space-y-4">
                <h2 className="text-3xl font-semibold text-white sm:text-4xl">Workflows designed for real people.</h2>
                <p className="max-w-2xl text-sm leading-relaxed text-slate-200/85">
                  Blend empathetic copy, actionable steps, and data-rich context. Customize journeys for health
                  programs, virtual clinics, or benefit providers — without breaking the narrative.
                </p>
              </div>
              <div className="grid gap-4">
                {workflows.map((workflow, index) => (
                  <div
                    key={workflow.title}
                    className="group rounded-[26px] border border-white/10 bg-gradient-to-br from-slate-950 via-slate-950/90 to-teal-950/80 p-5 text-sm text-slate-100 shadow-[0_28px_80px_rgba(15,23,42,0.45)] transition hover:border-emerald-400/50 hover:shadow-[0_35px_95px_rgba(16,185,129,0.35)]"
                  >
                    <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.3em] text-emerald-200/70">
                      <span className="inline-flex items-center gap-2">
                        <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400" aria-hidden />
                        Step {index + 1}
                      </span>
                      <span className="text-white/60">Workflow</span>
                    </div>
                    <h3 className="mt-3 text-lg font-semibold text-white">{workflow.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-100/80">
                      {workflow.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            <div id="insights" className="space-y-6">
              <div className="flex h-full flex-col gap-6 rounded-[32px] border border-white/10 bg-gradient-to-br from-teal-900/40 via-slate-950/80 to-slate-950/95 p-6 text-slate-100 shadow-[0_30px_90px_rgba(15,23,42,0.55)] backdrop-blur-2xl">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-200/80">
                    Insight Studio
                  </p>
                  <span className="text-xs text-slate-300">Live sync</span>
                </div>
                <h3 className="mt-4 text-xl font-semibold text-white">Every conversation, richly explained.</h3>
                <div className="space-y-5 text-sm leading-relaxed text-slate-200/80">
                  <p>
                    Powered by a transparent pipeline, every interaction becomes part of a continuous care story. We
                    capture the full exchange, highlight safety actions, and surface why certain guidance was
                    delivered.
                  </p>
                  <div className="rounded-[24px] border border-white/10 bg-slate-950/60 p-5 shadow-[0_25px_70px_rgba(15,23,42,0.45)]">
                    <p className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-200/70">
                      Transcript timeline
                    </p>
                    <ul className="mt-3 space-y-3 text-sm text-slate-100/75">
                      <li className="flex items-start gap-2">
                        <span className="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-emerald-300" aria-hidden />
                        <span>
                          Auto-summaries and tags categorize each message by symptom, risk level, and follow-up.
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-green-300" aria-hidden />
                        <span>
                          Escalation insights explain why hand-offs were triggered and what data informed the decision.
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="mt-1 inline-flex h-1.5 w-1.5 rounded-full bg-teal-300" aria-hidden />
                        <span>
                          Export utilities package transcripts, medical facts, and resources for clinical collaborators.
                        </span>
                      </li>
                    </ul>
                  </div>
                  <div className="grid gap-3 text-xs uppercase tracking-[0.28em] text-slate-200/70">
                    <div className="flex justify-between rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3">
                      <span>Response Clarity</span>
                      <span>92%</span>
                    </div>
                    <div className="flex justify-between rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3">
                      <span>Safety Guardrails</span>
                      <span>98%</span>
                    </div>
                    <div className="flex justify-between rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3">
                      <span>Human Hand-offs</span>
                      <span>1-click</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto w-full max-w-6xl px-6 pb-16 lg:px-10 lg:pb-20">
          <div className="rounded-[30px] border border-white/10 bg-white/5 p-8 shadow-[0_35px_95px_rgba(15,23,42,0.55)] backdrop-blur-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-200/80">Technology Stack</p>
            <h2 className="mt-3 text-3xl font-semibold text-white sm:text-4xl">Infrastructure you can trust.</h2>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-200/80">
              From retrieval orchestration to graph fallbacks, every layer is tuned for empathy, accuracy, and speed.
              Here’s how the system comes together.
            </p>
            <div className="mt-8 grid gap-4 lg:grid-cols-2">
              {techStack.map((item) => (
                <div
                  key={item.name}
                  className="rounded-[22px] border border-white/10 bg-slate-950/60 p-5 text-sm text-slate-100 shadow-[0_25px_70px_rgba(15,23,42,0.45)]"
                >
                  <p className="text-sm font-semibold text-white">{item.name}</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-100/75">{item.details}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto w-full max-w-6xl px-6 pb-16 lg:px-10 lg:pb-20">
          <div className="grid gap-6 lg:grid-cols-3">
            {dataHighlights.map((highlight) => (
              <div
                key={highlight.title}
                className="rounded-[26px] border border-white/10 bg-slate-950/65 p-6 text-slate-100 shadow-[0_28px_80px_rgba(15,23,42,0.5)]"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-200/80">
                  {highlight.title}
                </p>
                <p className="mt-3 text-4xl font-semibold text-white">
                  <AnimatedNumber value={highlight.value} duration={2000} />
                </p>
                <p className="mt-4 text-sm leading-relaxed text-slate-200/80">
                  {highlight.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto w-full max-w-6xl px-6 pb-16 lg:px-10 lg:pb-20">
          <div className="rounded-[32px] border border-white/10 bg-slate-950/70 p-8 text-slate-100 shadow-[0_35px_95px_rgba(15,23,42,0.55)] backdrop-blur-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-200/80">
              Retrieval orchestration
            </p>
            <h2 className="mt-3 text-3xl font-semibold text-white sm:text-4xl">
              How every answer takes shape.
            </h2>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-200/80">
              A transparent, multilingual pipeline keeps humans in the loop while preserving speed and empathy. Every query is automatically detected, translated, processed, and localized—peek under the hood.
            </p>
            <style dangerouslySetInnerHTML={{__html: `
              @keyframes bounce-in {
                0%, 100% { transform: translateY(0) scale(1); }
                50% { transform: translateY(-8px) scale(1.05); }
              }
              @keyframes rotate-pulse {
                0% { transform: rotate(0deg) scale(1); }
                25% { transform: rotate(-10deg) scale(1.1); }
                50% { transform: rotate(0deg) scale(1); }
                75% { transform: rotate(10deg) scale(1.1); }
                100% { transform: rotate(0deg) scale(1); }
              }
              @keyframes pulse-glow {
                0%, 100% { 
                  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3), inset 0 0 20px rgba(16, 185, 129, 0.1);
                  transform: scale(1);
                }
                50% { 
                  box-shadow: 0 0 35px rgba(16, 185, 129, 0.6), inset 0 0 30px rgba(16, 185, 129, 0.2);
                  transform: scale(1.08);
                }
              }
              @keyframes shake {
                0%, 100% { transform: translateX(0) rotate(0deg); }
                10% { transform: translateX(-2px) rotate(-2deg); }
                20% { transform: translateX(2px) rotate(2deg); }
                30% { transform: translateX(-2px) rotate(-2deg); }
                40% { transform: translateX(2px) rotate(2deg); }
                50% { transform: translateX(0) rotate(0deg); }
              }
              @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-12px); }
              }
              @keyframes arrow-slide {
                0% { transform: translateX(-4px); opacity: 0.6; }
                50% { transform: translateX(4px); opacity: 1; }
                100% { transform: translateX(-4px); opacity: 0.6; }
              }
              @keyframes icon-glow {
                0%, 100% { filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.4)); }
                50% { filter: drop-shadow(0 0 16px rgba(16, 185, 129, 0.8)) drop-shadow(0 0 24px rgba(34, 197, 94, 0.4)); }
              }
              @keyframes card-pulse {
                0%, 100% { 
                  border-color: rgba(255, 255, 255, 0.1);
                  box-shadow: 0 25px 60px rgba(15, 23, 42, 0.5);
                }
                50% { 
                  border-color: rgba(16, 185, 129, 0.4);
                  box-shadow: 0 30px 75px rgba(16, 185, 129, 0.25), 0 0 40px rgba(16, 185, 129, 0.1);
                }
              }
              .icon-bounce { animation: bounce-in 2s ease-in-out infinite; }
              .icon-rotate { animation: rotate-pulse 3s ease-in-out infinite; }
              .icon-pulse { animation: pulse-glow 2.5s ease-in-out infinite; }
              .icon-shake { animation: shake 4s ease-in-out infinite; }
              .icon-float { animation: float 3s ease-in-out infinite; }
              .arrow-animate { animation: arrow-slide 1.5s ease-in-out infinite; }
              .icon-glow { animation: icon-glow 2s ease-in-out infinite; }
              .card-pulse { animation: card-pulse 4s ease-in-out infinite; }
              .delay-0 { animation-delay: 0s; }
              .delay-1 { animation-delay: 0.4s; }
              .delay-2 { animation-delay: 0.8s; }
              .delay-3 { animation-delay: 1.2s; }
              .delay-4 { animation-delay: 1.6s; }
              .delay-5 { animation-delay: 2s; }
              .delay-6 { animation-delay: 2.4s; }
              
              /* Hover expand/collapse styles */
              .retrieval-container .stage-card {
                transition: all 0.3s ease;
                min-height: 140px;
              }
              .retrieval-container .stage-card .stage-description {
                max-height: 0;
                opacity: 0;
                overflow: hidden;
                transition: max-height 0.3s ease, opacity 0.3s ease, margin 0.3s ease;
                margin-top: 0;
              }
              .retrieval-container .stage-card .stage-progress {
                max-height: 0;
                opacity: 0;
                overflow: hidden;
                transition: max-height 0.3s ease, opacity 0.3s ease, margin 0.3s ease;
                margin-top: 0;
              }
              /* When hovering container, shrink non-hovered cards */
              .retrieval-container:has(.stage-card:hover) .stage-card:not(:hover) {
                min-height: 120px;
                transform: scale(0.95);
              }
              /* Expand hovered card */
              .retrieval-container .stage-card:hover {
                min-height: auto;
                transform: scale(1.05);
                z-index: 10;
              }
              .retrieval-container .stage-card:hover .stage-description {
                max-height: 500px;
                opacity: 1;
                margin-top: 0.5rem;
              }
              .retrieval-container .stage-card:hover .stage-progress {
                max-height: 8px;
                opacity: 1;
                margin-top: 1rem;
              }
              /* When no card is hovered, all can be slightly larger */
              .retrieval-container:not(:has(.stage-card:hover)) .stage-card {
                min-height: 140px;
              }
              /* Diminish arrows when hovering on any card */
              .retrieval-container:has(.stage-card:hover) .stage-card-arrow {
                opacity: 0.25;
                transform: scale(0.65);
                transition: opacity 0.3s ease, transform 0.3s ease;
              }
              /* Completely hide arrows when a card is hovered to avoid content obstruction */
              .retrieval-container .stage-card:hover .stage-card-arrow {
                opacity: 0.15;
                transform: scale(0.5);
              }
            `}} />
            <div className="mt-8">
              <div className="retrieval-container mx-auto grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
                {[
                  { 
                    label: "User text", 
                    description: "Typed or voice captured, normalized and ready for processing.",
                    icon: "📥",
                    animation: "icon-bounce delay-0"
                  },
                  { 
                    label: "Detect and translate", 
                    description: "Using gpt 4.1, the app detects the incoming language and automatically translates it into English.",
                    icon: "/chatgpt-seeklogo.png",
                    isImage: true,
                    animation: "icon-pulse delay-1"
                  },
                  { 
                    label: "ChromaDB", 
                    description: "Vector retrieval across 1,120 medical briefs and playbooks.",
                    icon: "/chroma-seeklogo.png",
                    isImage: true,
                    animation: "icon-pulse delay-2"
                  },
                  { 
                    label: "Neo4j (with fallback)", 
                    description: "Graph fallback inserts contraindications, providers, and safety edges.",
                    icon: "/neo4j-seeklogo.png",
                    isImage: true,
                    animation: "icon-rotate delay-3"
                  },
                  { 
                    label: "Final reasoning → English", 
                    description: "GPT-4.1-mini gives clear step-by-step reasoning and delivers the final answer in English.",
                    icon: "/chatgpt-seeklogo.png",
                    isImage: true,
                    animation: "icon-shake delay-4"
                  },
                  { 
                    label: "Translate to User's Language", 
                    description: "GPT-4.1-mini delivers the response in the user's preferred language while keeping the meaning intact.",
                    icon: "/chatgpt-seeklogo.png",
                    isImage: true,
                    animation: "icon-float delay-5"
                  },
                  { 
                    label: "Response", 
                    description: "Localized output, red-flag alerts, and optional escalation hooks.",
                    icon: "💬",
                    animation: "icon-float delay-6"
                  },
                ].map((stage, index, arr) => (
                  <div key={stage.label} className="relative">
                    <div className={clsx(
                      "stage-card relative flex h-full flex-col rounded-[20px] border border-white/10 bg-gradient-to-br from-emerald-500/10 via-green-500/8 to-teal-500/10 p-4 shadow-[0_20px_50px_rgba(15,23,42,0.5)] backdrop-blur-sm transition-all hover:border-emerald-400/50 hover:shadow-[0_30px_80px_rgba(16,185,129,0.35)] card-pulse lg:p-5",
                      index === 0 && "delay-0",
                      index === 1 && "delay-1",
                      index === 2 && "delay-2",
                      index === 3 && "delay-3",
                      index === 4 && "delay-4",
                      index === 5 && "delay-5",
                      index === 6 && "delay-6"
                    )}>
                      <div className="absolute inset-0 -z-10 rounded-[24px] bg-gradient-to-br from-emerald-500/5 via-green-500/3 to-teal-500/5 opacity-0 blur-xl transition-opacity hover:opacity-100" />
                      <div className="mb-3 flex items-center justify-between">
                        <span className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 via-green-500/15 to-teal-500/20 text-xl shadow-inner shadow-emerald-500/10 transition-transform hover:scale-110 ${stage.animation} icon-glow lg:h-12 lg:w-12 lg:text-2xl`}>
                          {stage.isImage ? (
                            <Image 
                              src={stage.icon} 
                              alt={stage.label}
                              width={40}
                              height={40}
                              className="object-contain h-8 w-8 lg:h-10 lg:w-10"
                            />
                          ) : (
                            stage.icon
                          )}
                        </span>
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500/20 text-xs font-bold text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.3)] animate-pulse lg:h-7 lg:w-7">
                          {index + 1}
                        </span>
                      </div>
                      <h3 className="mb-2 text-base font-semibold text-white transition-colors hover:text-emerald-300 lg:text-lg">{stage.label}</h3>
                      <p className="stage-description text-xs leading-relaxed text-slate-200/80 lg:text-sm">{stage.description}</p>
                      <div className="stage-progress h-1 w-full overflow-hidden rounded-full bg-emerald-500/10">
                        <div className={`h-full rounded-full bg-gradient-to-r from-emerald-500 via-green-500 to-teal-500 animate-pulse`} style={{ 
                          animation: `pulse 2s ease-in-out infinite`,
                          animationDelay: `${index * 0.3}s`
                        }} />
                      </div>
                    </div>
                    {index < arr.length - 1 && (
                      <div className="stage-card-arrow absolute -right-2 top-1/2 z-10 hidden -translate-y-1/2 transition-all xl:flex xl:-right-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/30 via-green-500/20 to-teal-500/30 shadow-[0_8px_24px_rgba(16,185,129,0.3)] backdrop-blur-sm xl:h-10 xl:w-10">
                          <svg
                            className="h-4 w-4 text-emerald-300 arrow-animate xl:h-5 xl:w-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2.5}
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section
          id="cta"
          className="mx-auto mb-24 w-full max-w-6xl px-6 lg:px-10"
        >
          <div className="relative overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-slate-900/80 via-slate-950 to-slate-900/90 px-6 py-12 shadow-[0_40px_110px_rgba(15,23,42,0.65)] backdrop-blur-xl sm:px-10">
            <div
              className="pointer-events-none absolute inset-0 -z-10 opacity-70 blur-3xl"
              aria-hidden
              style={{ background: "radial-gradient(circle at 20% 20%, rgba(16,185,129,0.4), transparent 60%), radial-gradient(circle at 80% 20%, rgba(34,197,94,0.35), transparent 55%)" }}
            />
            <div className="flex flex-col gap-8 text-center sm:text-left sm:pr-10">
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-200/80">
                Built for teams who care deeply
              </p>
              <h2 className="text-3xl font-semibold text-white sm:text-4xl">
                Ready to launch your next era of compassionate care?
              </h2>
              <p className="text-sm leading-relaxed text-slate-200/80">
                Partner with us to unlock a custom deployment, design collaborative workflows, and deliver
                round-the-clock guidance that feels human.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-4 sm:justify-start">
                <Link
                  href="/"
                  className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 px-6 py-3 text-sm font-semibold text-white shadow-[0_22px_45px_rgba(16,185,129,0.35)] transition hover:scale-[1.05]"
                >
                  Start a pilot
                </Link>
                <Link
                  href="mailto:hello@healthcompanion.ai"
                  className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-white/30 hover:text-white"
                >
                  Talk to our team
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-white/5 bg-slate-950/80 py-8 text-sm text-slate-400">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center justify-between gap-4 px-6 sm:flex-row lg:px-10">
          <p>© {new Date().getFullYear()} Health Companion. Crafted with care and safety in mind.</p>
          <div className="flex items-center gap-4">
            <Link href="/privacy" className="hover:text-white">
              Privacy
            </Link>
            <Link href="/terms" className="hover:text-white">
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
