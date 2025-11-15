'use client';

import { useEffect, useState } from 'react';

interface WelcomeScreenProps {
  onComplete: () => void;
}

export default function WelcomeScreen({ onComplete }: WelcomeScreenProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [animationComplete, setAnimationComplete] = useState(false);

  useEffect(() => {
    // Wait for Lottie animation to load and play (show for 4 seconds)
    const timer = setTimeout(() => {
      setAnimationComplete(true);
    }, 4000); // Show animation for 4 seconds

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (animationComplete) {
      // Fade out animation
      const fadeTimer = setTimeout(() => {
        setIsVisible(false);
        // Call onComplete after fade out completes
        setTimeout(() => {
          onComplete();
        }, 600);
      }, 600);

      return () => clearTimeout(fadeTimer);
    }
  }, [animationComplete, onComplete]);

  return (
    <div
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950 transition-opacity duration-500 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {/* Background gradient */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(16,185,129,0.25),transparent_55%),radial-gradient(circle_at_85%_15%,rgba(34,197,94,0.24),transparent_55%),linear-gradient(180deg,rgba(2,6,23,0.92),rgba(2,6,23,0.97))]" />
      
      {/* Lottie Animation */}
      <div className="relative z-10 flex h-[400px] w-full max-w-md items-center justify-center">
        <iframe
          src="https://lottie.host/embed/69db2fef-793d-4e48-8034-e5cebe66dec9/Kz7csFK40D.lottie"
          className="h-full w-full border-0"
          title="Welcome Animation"
          allow="autoplay"
        />
      </div>

      {/* Welcome Text */}
      <div className="relative z-10 mt-8 text-center">
        <h1 className="mb-2 text-3xl font-semibold text-white sm:text-4xl">
          Welcome to Health Companion
        </h1>
        <p className="text-lg text-slate-300/80">
          Your AI-powered health assistant is ready to help
        </p>
      </div>

      {/* Loading indicator */}
      {animationComplete && (
        <div className="relative z-10 mt-8">
          <div className="flex items-center gap-2 text-sm text-emerald-300/80">
            <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            <span>Loading your dashboard...</span>
          </div>
        </div>
      )}
    </div>
  );
}

