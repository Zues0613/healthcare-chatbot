import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy | Health Companion",
  description:
    "Health Companion Privacy Policy - Learn how we protect your health information and respect your privacy.",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(16,185,129,0.25),transparent_55%),radial-gradient(circle_at_85%_15%,rgba(34,197,94,0.24),transparent_55%),linear-gradient(180deg,rgba(2,6,23,0.92),rgba(2,6,23,0.97))]" />
      
      <header className="relative z-10 border-b border-white/5 bg-slate-950/60 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6 lg:px-10">
          <Link href="/landing" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 via-green-500 to-teal-500 text-lg font-semibold text-white shadow-[0_15px_35px_rgba(16,185,129,0.35)]">
              HC
            </span>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.32em] text-emerald-300/80">
                Health Companion
              </p>
              <p className="text-sm font-semibold text-white">Care Intelligence Platform</p>
            </div>
          </Link>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-4xl px-6 py-16 lg:px-10">
        <div className="rounded-[32px] border border-white/10 bg-slate-950/70 p-8 shadow-[0_35px_95px_rgba(15,23,42,0.55)] backdrop-blur-xl lg:p-12">
          <h1 className="mb-6 text-4xl font-semibold text-white">Privacy Policy</h1>
          <p className="mb-8 text-sm text-slate-300/80">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>

          <div className="space-y-8 text-sm leading-relaxed text-slate-200/80">
            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">1. Introduction</h2>
              <p>
                Health Companion ("we," "our," or "us") is committed to protecting your privacy and health information. 
                This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use 
                our AI-powered health assistance platform.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">2. Information We Collect</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-emerald-300">Health Information</h3>
                  <ul className="ml-6 list-disc space-y-2">
                    <li>Symptoms and health concerns you share during conversations</li>
                    <li>Health profile data including age, medical conditions, and medications</li>
                    <li>Chat history and session data for personalized responses</li>
                  </ul>
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-emerald-300">Account Information</h3>
                  <ul className="ml-6 list-disc space-y-2">
                    <li>Email address and password (hashed and encrypted)</li>
                    <li>Profile preferences and settings</li>
                    <li>Language preferences for multilingual support</li>
                  </ul>
                </div>
                <div>
                  <h3 className="mb-2 text-lg font-semibold text-emerald-300">Technical Information</h3>
                  <ul className="ml-6 list-disc space-y-2">
                    <li>Device information and browser type</li>
                    <li>IP address and usage patterns</li>
                    <li>Session timestamps and interaction logs</li>
                  </ul>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">3. How We Use Your Information</h2>
              <ul className="ml-6 list-disc space-y-2">
                <li>To provide personalized health guidance and information</li>
                <li>To improve our AI models and response accuracy</li>
                <li>To detect safety concerns and red-flag symptoms</li>
                <li>To maintain chat history for continuity of care</li>
                <li>To send important updates and notifications</li>
                <li>To comply with legal obligations and protect user safety</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">4. Data Security</h2>
              <p>
                We implement industry-standard security measures to protect your health information:
              </p>
              <ul className="ml-6 mt-4 list-disc space-y-2">
                <li>End-to-end encryption for sensitive data transmission</li>
                <li>Secure password hashing using SHA-256 algorithms</li>
                <li>Regular security audits and vulnerability assessments</li>
                <li>Access controls and authentication mechanisms</li>
                <li>Secure database storage with connection pooling</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">5. Data Sharing and Disclosure</h2>
              <p>We do not sell your health information. We may share data only in the following circumstances:</p>
              <ul className="ml-6 mt-4 list-disc space-y-2">
                <li>When required by law or legal process</li>
                <li>To protect user safety or prevent harm</li>
                <li>With your explicit consent for specific purposes</li>
                <li>With service providers who maintain confidentiality agreements</li>
                <li>In anonymized, aggregated form for research and improvement</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">6. Your Rights</h2>
              <p>You have the right to:</p>
              <ul className="ml-6 mt-4 list-disc space-y-2">
                <li>Access and review your health information</li>
                <li>Request corrections to inaccurate data</li>
                <li>Delete your account and associated data</li>
                <li>Export your chat history and profile data</li>
                <li>Opt-out of certain data collection practices</li>
                <li>Request information about how your data is used</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">7. Medical Disclaimer</h2>
              <p className="text-amber-300/90">
                <strong>Important:</strong> Health Companion is not a substitute for professional medical advice, 
                diagnosis, or treatment. Always seek the advice of qualified healthcare providers with any questions 
                you may have regarding a medical condition. Never disregard professional medical advice or delay in 
                seeking it because of information provided by this service.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">8. Changes to This Policy</h2>
              <p>
                We may update this Privacy Policy from time to time. We will notify you of any material changes 
                by posting the new policy on this page and updating the "Last updated" date. Your continued use 
                of the service after changes become effective constitutes acceptance of the updated policy.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">9. Contact Us</h2>
              <p>
                If you have questions about this Privacy Policy or our data practices, please contact us at:
              </p>
              <p className="mt-2">
                <strong>Email:</strong> privacy@healthcompanion.ai<br />
                <strong>Address:</strong> Health Companion Privacy Team
              </p>
            </section>
          </div>

          <div className="mt-12 border-t border-white/10 pt-8">
            <Link
              href="/landing"
              className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-white/30 hover:text-white"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
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

