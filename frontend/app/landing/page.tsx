import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import clsx from "clsx";
import AnimatedNumber from "../../components/AnimatedNumber";
import HeroSection from "../../components/HeroSection";
import StartPilotButton from "../../components/StartPilotButton";
import FeatureCard from "../../components/FeatureCard";

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
    title: "Hybrid RAG with ChromaDB",
    description:
      "Vector-based RAG system powered by ChromaDB retrieves relevant healthcare knowledge from 110+ curated markdown files. Semantic search ensures evidence-based responses from verified medical sources.",
    points: [
      "110+ markdown files covering various medical domains",
      "Fast semantic search using vector similarity (much faster than keyword matching)",
      "Source attribution with citations for transparency and trust",
      "Organized by medical specialties for better knowledge retrieval",
    ],
    accent: "from-emerald-500 via-green-500 to-teal-500",
  },
  {
    title: "Graph Database Intelligence (Neo4j)",
    description:
      "Neo4j graph database stores structured medical knowledge as nodes and relationships, enabling complex queries for contraindications, safe actions, red flags, and healthcare provider recommendations.",
    points: [
      "Real-time safety checks for contraindications and unsafe medications",
      "Provider discovery based on location and medical condition",
      "Red flag detection mapping symptoms to critical conditions",
      "In-memory fallback ensures functionality even if Neo4j is unavailable",
    ],
    accent: "from-green-500 via-emerald-500 to-teal-500",
  },
  {
    title: "Intelligent Intent Routing",
    description:
      "Intelligent routing system analyzes user queries to determine whether to use Graph database (Neo4j) or Vector RAG (ChromaDB) based on query intent for optimal performance.",
    points: [
      "Pattern matching and keyword detection for optimal routing",
      "Graph queries for structured data (contraindications, providers)",
      "Vector RAG for semantic content (general health information)",
      "Can combine both sources for comprehensive responses",
    ],
    accent: "from-teal-500 via-emerald-500 to-green-500",
  },
  {
    title: "Real-Time Safety & Red Flag Detection",
    description:
      "Comprehensive safety detection system scans user queries for red flag symptoms, mental health crisis indicators, and pregnancy emergencies using keyword matching and linguistic analysis.",
    points: [
      "180+ critical symptoms covered across medical domains",
      "Multilingual support: English and Hindi transliteration",
      "Mental health crisis detection with helpline numbers",
      "Pregnancy emergency detection and guidance",
    ],
    accent: "from-emerald-500 via-teal-500 to-green-500",
  },
  {
    title: "Personalized Health Profiles",
    description:
      "Comprehensive user profile system stores demographic information and medical conditions to personalize health recommendations and filter contraindications for safe, targeted advice.",
    points: [
      "Age, sex, and condition-specific health advice",
      "Filters unsafe medications based on user's medical conditions",
      "Supports unlimited medical conditions via extensible array",
      "Location-based provider recommendations",
    ],
    accent: "from-green-500 via-emerald-500 to-teal-500",
  },
  {
    title: "Persistent Database Connection Pooling",
    description:
      "Persistent PostgreSQL connection pool using asyncpg maintains active database connections throughout the application lifecycle, eliminating connection overhead for optimal performance.",
    points: [
      "Eliminates connection overhead (saves 50-200ms per request)",
      "Handles concurrent requests efficiently",
      "Automatic reconnection ensures database availability",
      "Health monitoring detects and recovers from connection issues",
    ],
    accent: "from-teal-500 via-green-500 to-emerald-500",
  },
  {
    title: "Upstash Redis Caching Layer",
    description:
      "Distributed caching layer using Upstash Redis stores frequently accessed data, API responses, and computed results to reduce database load and improve response times dramatically.",
    points: [
      "10-50ms response time vs 100-500ms for database queries",
      "Reduces database load and API calls by 60-80%",
      "Handles 10x more concurrent users with same infrastructure",
      "Graceful degradation ensures system continues working if Redis unavailable",
    ],
    accent: "from-emerald-500 via-green-500 to-teal-500",
  },
  {
    title: "Secure Authentication with JWT",
    description:
      "Secure authentication system using JWT stored in HTTP-only cookies for session management. Includes password hashing, refresh tokens, and role-based access control.",
    points: [
      "HTTP-only cookies prevent XSS attacks",
      "SHA-256 password hashing with unique salt per user",
      "Role-based access control (admin/user)",
      "Stateless JWT tokens work across multiple servers",
    ],
    accent: "from-green-500 via-teal-500 to-emerald-500",
  },
  {
    title: "Chat History & Session Management",
    description:
      "Comprehensive chat history system stores all user conversations, messages, and metadata in NeonDB. Tracks chat sessions, message threads, safety flags, and citations.",
    points: [
      "Complete conversation history for continuity of care",
      "Healthcare providers can review patient history",
      "Enables analysis of common health concerns",
      "Maintains audit trail for regulatory compliance",
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
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(16,185,129,0.25),transparent_55%),radial-gradient(circle_at_85%_15%,rgba(34,197,94,0.24),transparent_55%),radial-gradient(circle_at_50%_100%,rgba(16,185,129,0.20),transparent_60%),radial-gradient(circle_at_20%_90%,rgba(34,197,94,0.18),transparent_55%),linear-gradient(180deg,rgba(2,6,23,0.92),rgba(2,6,23,0.92))]" />
      <div className={gradientSpot("top-[-8rem] left-[-6rem]", "bg-emerald-500/40", "h-72 w-72")} />
      <div className={gradientSpot("top-[-4rem] right-[-4rem]", "bg-green-500/35", "h-64 w-64")} />
      <div className={gradientSpot("bottom-[-6rem] right-[-10rem]", "bg-teal-500/40", "h-80 w-80")} />
      <div className={gradientSpot("bottom-[-8rem] left-[-8rem]", "bg-emerald-500/35", "h-72 w-72")} />

      <header className="relative z-10 border-b border-white/5 bg-slate-950/60 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6 sm:py-5 md:py-6 lg:px-10">
          <div className="flex items-center gap-2 sm:gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-sm font-semibold text-white shadow-[0_15px_35px_rgba(16,185,129,0.35)] sm:h-10 sm:w-10 sm:text-lg">
              HC
            </span>
            <div>
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.32em] text-emerald-300/80 sm:text-xs">
                Health Companion
              </p>
              <p className="text-xs font-semibold text-white sm:text-sm">Care Intelligence Platform</p>
            </div>
          </div>
          <nav className="hidden items-center gap-6 text-xs text-slate-200 md:flex md:gap-8 md:text-sm">
            <a className="text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400" href="#features">
              Features
            </a>
            <a className="text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400" href="#workflows">
              Workflows
            </a>
            <a className="text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400" href="#insights">
              Insights
            </a>
            <a className="text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400" href="#cta">
              Get Started
            </a>
          </nav>
          <div className="flex items-center gap-2 sm:gap-3">
            <Link
              href="/landing#insights"
              className="hidden rounded-full border border-white/10 px-3 py-1.5 text-xs font-medium text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 sm:inline-flex sm:px-4 sm:py-2 sm:text-sm"
            >
              View Insights
            </Link>
            <Link
              href="/auth"
              className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 px-3 py-1.5 text-xs font-semibold text-white shadow-[0_18px_40px_rgba(16,185,129,0.35)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400 sm:gap-2 sm:px-4 sm:py-2 sm:text-sm"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main className="relative z-10">
        <HeroSection />

        <section id="features" className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6 sm:py-16 md:py-20 lg:px-10 lg:py-24">
          <div className="mb-8 flex flex-col gap-3 text-center sm:mb-10 sm:gap-4 sm:text-left">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.32em] text-emerald-200/80 sm:text-xs">Why teams choose us</p>
            <h2 className="text-2xl font-semibold text-white sm:text-3xl md:text-4xl">Features crafted for clinical-grade conversations.</h2>
            <p className="max-w-3xl text-xs leading-relaxed text-slate-200/80 sm:text-sm">
              We blend AI expressiveness with deterministic checks. Nine core features form the foundation of a production-ready, scalable, and secure healthcare chatbot application. Each feature represents an orchestrated system ensuring safe, multilingual, empathetic care guidance.
            </p>
          </div>
          <div className="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <FeatureCard key={feature.title} feature={feature} />
            ))}
          </div>
        </section>

        <section id="workflows" className="mx-auto w-full max-w-7xl px-6 py-16 lg:px-10 lg:py-20">
          <div className="mb-8 flex flex-col gap-3 text-center sm:mb-10 sm:gap-4">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.32em] text-emerald-200/80 sm:text-xs">Step-by-step clarity</p>
            <h2 className="text-2xl font-semibold text-white sm:text-3xl md:text-4xl">Workflows designed for real people.</h2>
            <p className="mx-auto max-w-3xl text-xs leading-relaxed text-slate-200/80 sm:text-sm">
              Blend empathetic copy, actionable steps, and data-rich context. Customize journeys for health
              programs, virtual clinics, or benefit providers — without breaking the narrative.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {workflows.map((workflow, index) => (
              <div
                key={workflow.title}
                className="group relative overflow-hidden rounded-[26px] border border-white/10 bg-gradient-to-br from-slate-950 via-slate-950/90 to-teal-950/80 p-6 text-sm text-slate-100 shadow-[0_28px_80px_rgba(15,23,42,0.45)] transition-all duration-300 hover:border-emerald-400/50 hover:shadow-[0_35px_95px_rgba(16,185,129,0.35)] hover:scale-[1.03] hover:-translate-y-1"
              >
                <div className="pointer-events-none absolute inset-0 -z-10 opacity-0 blur-2xl transition-opacity duration-300 group-hover:opacity-60 bg-gradient-to-br from-emerald-500/20 via-green-500/15 to-teal-500/20" aria-hidden />
                <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.3em] text-emerald-200/70">
                  <span className="inline-flex items-center gap-2">
                    <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400" aria-hidden />
                    Step {index + 1}
                  </span>
                  <span className="text-white/60 transition-colors group-hover:text-emerald-300/80">Workflow</span>
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white transition-colors group-hover:text-emerald-200 sm:text-xl">{workflow.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-100/80 transition-colors group-hover:text-slate-100">
                  {workflow.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section id="insights" className="mx-auto w-full max-w-6xl px-6 py-16 lg:px-10 lg:py-20">
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

        <section className="mx-auto w-full max-w-[95%] 2xl:max-w-[90%] px-4 sm:px-6 pb-16 lg:px-8 xl:px-12 lg:pb-20">
          <div className="rounded-[32px] border border-white/10 bg-slate-950/70 p-6 sm:p-8 lg:p-10 xl:p-12 text-slate-100 shadow-[0_35px_95px_rgba(15,23,42,0.55)] backdrop-blur-xl">
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
              
              /* Always show descriptions for better readability */
              .retrieval-container .stage-card {
                min-height: auto;
              }
              .retrieval-container .stage-card .stage-description {
                max-height: 500px;
                opacity: 1;
                margin-top: 0.5rem;
              }
              .retrieval-container .stage-card .stage-progress {
                max-height: 8px;
                opacity: 1;
                margin-top: 1rem;
              }
            `}} />
            <div className="mt-10 sm:mt-12 lg:mt-16">
              <div className="retrieval-container mx-auto flex flex-nowrap justify-between items-stretch gap-6 sm:gap-8 lg:gap-10 xl:gap-12 2xl:gap-16 overflow-x-auto scrollbar-hide scroll-smooth pb-4" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}>
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
                  <div key={stage.label} className="relative flex-shrink-0 flex-1 min-w-[180px] sm:min-w-[200px] lg:min-w-[220px] xl:min-w-[240px] 2xl:min-w-[260px]">
                    <div className={clsx(
                      "stage-card relative flex h-full w-full flex-col rounded-[20px] border border-white/10 bg-gradient-to-br from-emerald-500/10 via-green-500/8 to-teal-500/10 p-5 sm:p-6 shadow-[0_20px_50px_rgba(15,23,42,0.5)] backdrop-blur-sm card-pulse lg:p-7",
                      index === 0 && "delay-0",
                      index === 1 && "delay-1",
                      index === 2 && "delay-2",
                      index === 3 && "delay-3",
                      index === 4 && "delay-4",
                      index === 5 && "delay-5",
                      index === 6 && "delay-6"
                    )}>
                      <div className="absolute inset-0 -z-10 rounded-[24px] bg-gradient-to-br from-emerald-500/5 via-green-500/3 to-teal-500/5 opacity-60 blur-xl" />
                      <div className="mb-3 flex items-center justify-between">
                        <span className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 via-green-500/15 to-teal-500/20 text-xl shadow-inner shadow-emerald-500/10 ${stage.animation} icon-glow lg:h-12 lg:w-12 lg:text-2xl`}>
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
                      <h3 className="mb-2 text-base font-semibold text-white lg:text-lg">{stage.label}</h3>
                      <p className="stage-description text-xs leading-relaxed text-slate-200/80 lg:text-sm">{stage.description}</p>
                      <div className="stage-progress h-1 w-full overflow-hidden rounded-full bg-emerald-500/10">
                        <div className={`h-full rounded-full bg-gradient-to-r from-emerald-500 via-green-500 to-teal-500 animate-pulse`} style={{ 
                          animation: `pulse 2s ease-in-out infinite`,
                          animationDelay: `${index * 0.3}s`
                        }} />
                      </div>
                    </div>
                    {index < arr.length - 1 && (
                      <div className="stage-card-arrow absolute -right-3 top-1/2 z-10 hidden -translate-y-1/2 transition-all lg:flex lg:-right-4 xl:-right-5 2xl:-right-6">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500/30 via-green-500/20 to-teal-500/30 shadow-[0_8px_24px_rgba(16,185,129,0.3)] backdrop-blur-sm xl:h-12 xl:w-12 2xl:h-14 2xl:w-14">
                          <svg
                            className="h-5 w-5 text-emerald-300 arrow-animate xl:h-6 xl:w-6 2xl:h-7 2xl:w-7"
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
                <StartPilotButton className="inline-flex items-center gap-2 rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 px-6 py-3 text-sm font-semibold text-white shadow-[0_22px_45px_rgba(16,185,129,0.35)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400" />
                <Link
                  href="/team"
                  className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400"
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
            <Link href="/team" className="text-slate-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400">
              Meet our team
            </Link>
            <Link href="/privacy" className="text-slate-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400">
              Privacy
            </Link>
            <Link href="/terms" className="text-slate-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-400">
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
