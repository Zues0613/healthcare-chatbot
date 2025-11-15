import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service | Health Companion",
  description:
    "Health Companion Terms of Service - Read our terms and conditions for using our AI-powered health assistance platform.",
};

export default function TermsPage() {
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
          <h1 className="mb-6 text-4xl font-semibold text-white">Terms of Service</h1>
          <p className="mb-8 text-sm text-slate-300/80">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>

          <div className="space-y-8 text-sm leading-relaxed text-slate-200/80">
            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">1. Acceptance of Terms</h2>
              <p>
                By accessing and using Health Companion ("the Service"), you accept and agree to be bound by the terms 
                and provision of this agreement. If you do not agree to these Terms of Service, please do not use our Service.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">2. Description of Service</h2>
              <p>
                Health Companion is an AI-powered health information and guidance platform that provides:
              </p>
              <ul className="ml-6 mt-4 list-disc space-y-2">
                <li>General health information and educational content</li>
                <li>Multilingual support for health-related queries</li>
                <li>Personalized responses based on your health profile</li>
                <li>Safety detection and red-flag symptom identification</li>
                <li>Chat history and session management</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">3. Medical Disclaimer</h2>
              <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-6 text-amber-200/90">
                <p className="font-semibold mb-2">⚠️ Important Medical Disclaimer</p>
                <p>
                  Health Companion is NOT a medical service, does NOT provide medical advice, diagnosis, or treatment, 
                  and is NOT a substitute for professional medical care. The information provided by our AI assistant 
                  is for educational and informational purposes only.
                </p>
                <p className="mt-4">
                  <strong>You should:</strong>
                </p>
                <ul className="ml-6 mt-2 list-disc space-y-1">
                  <li>Always consult qualified healthcare professionals for medical advice</li>
                  <li>Seek immediate medical attention for emergencies</li>
                  <li>Not rely solely on this Service for health decisions</li>
                  <li>Use professional judgment when interpreting AI-generated responses</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">4. User Responsibilities</h2>
              <p>You agree to:</p>
              <ul className="ml-6 mt-4 list-disc space-y-2">
                <li>Provide accurate and truthful health information</li>
                <li>Use the Service responsibly and in good faith</li>
                <li>Not use the Service for emergency medical situations</li>
                <li>Maintain the confidentiality of your account credentials</li>
                <li>Comply with all applicable laws and regulations</li>
                <li>Not attempt to reverse engineer or compromise the Service</li>
                <li>Respect the intellectual property rights of Health Companion</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">5. Account Registration</h2>
              <p>
                To use certain features, you must register for an account. You agree to:
              </p>
              <ul className="ml-6 mt-4 list-disc space-y-2">
                <li>Provide accurate, current, and complete information</li>
                <li>Maintain and update your information as necessary</li>
                <li>Keep your password secure and confidential</li>
                <li>Notify us immediately of any unauthorized access</li>
                <li>Accept responsibility for all activities under your account</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">6. Limitation of Liability</h2>
              <p>
                To the fullest extent permitted by law, Health Companion shall not be liable for any indirect, 
                incidental, special, consequential, or punitive damages, or any loss of profits or revenues, 
                whether incurred directly or indirectly, or any loss of data, use, goodwill, or other intangible 
                losses resulting from your use of the Service.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">7. Service Availability</h2>
              <p>
                We strive to maintain Service availability but do not guarantee uninterrupted access. The Service 
                may be temporarily unavailable due to maintenance, updates, technical issues, or circumstances 
                beyond our control. We are not liable for any inconvenience or loss resulting from Service unavailability.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">8. Intellectual Property</h2>
              <p>
                The Service, including its original content, features, functionality, AI models, and design, is owned 
                by Health Companion and protected by international copyright, trademark, patent, trade secret, and 
                other intellectual property laws. You may not reproduce, distribute, modify, or create derivative works 
                without our express written permission.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">9. Privacy and Data</h2>
              <p>
                Your use of the Service is also governed by our Privacy Policy. By using the Service, you consent 
                to the collection and use of information as described in our Privacy Policy. We take the protection 
                of your health information seriously and implement appropriate security measures.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">10. Termination</h2>
              <p>
                We reserve the right to terminate or suspend your account and access to the Service immediately, 
                without prior notice, for any breach of these Terms of Service. You may also terminate your account 
                at any time by contacting us or using account deletion features.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">11. Changes to Terms</h2>
              <p>
                We reserve the right to modify these Terms of Service at any time. We will notify users of any 
                material changes by posting the updated terms on this page and updating the "Last updated" date. 
                Your continued use of the Service after changes become effective constitutes acceptance of the 
                modified terms.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">12. Governing Law</h2>
              <p>
                These Terms of Service shall be governed by and construed in accordance with applicable laws, 
                without regard to conflict of law provisions. Any disputes arising from these terms or your use 
                of the Service shall be subject to the exclusive jurisdiction of competent courts.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-xl font-semibold text-white">13. Contact Information</h2>
              <p>
                If you have questions about these Terms of Service, please contact us at:
              </p>
              <p className="mt-2">
                <strong>Email:</strong> legal@healthcompanion.ai<br />
                <strong>Address:</strong> Health Companion Legal Team
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

