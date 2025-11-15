'use client';

import type { ReactNode } from 'react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { Check, Loader2, ShieldCheck, Sparkles, XCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { setAuth, type AuthUser } from '../../utils/auth';
import { apiClient, API_BASE } from '../../utils/api';

type ToastVariant = 'success' | 'error' | 'info';

interface ToastMessage {
  id: string;
  message: string;
  variant: ToastVariant;
}

const createId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

const softPalette = {
  background: 'bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950',
  card: 'bg-white/90 backdrop-blur-lg border border-white/70',
  accent: 'from-emerald-400 via-green-400 to-teal-500',
  focus: 'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-300',
  textPrimary: 'text-slate-800',
  textSecondary: 'text-slate-500',
};

const passwordStrengthLabels = ['Very Weak', 'Weak', 'Okay', 'Strong', 'Excellent'];

function scorePassword(password: string): number {
  let score = 0;
  if (!password) return score;
  const lengthScore = Math.min(3, Math.floor(password.length / 4));
  score += lengthScore;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  return Math.min(score, 5);
}

export default function AuthExperience() {
  const router = useRouter();
  const [mode, setMode] = useState<'signup' | 'login'>('signup');
  const [loading, setLoading] = useState(false);
  const [signUpForm, setSignUpForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
    remember: true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const toastTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const signUpButtonRef = useRef<HTMLButtonElement | null>(null);
  const signUpScrollTriggered = useRef(false);

  const passwordScore = useMemo(() => scorePassword(signUpForm.password), [signUpForm.password]);

  const addToast = useCallback((message: string, variant: ToastVariant = 'info') => {
    const id = createId();
    setToasts((prev) => [...prev, { id, message, variant }]);
    const timer = setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
      delete toastTimers.current[id];
    }, 3200);
    toastTimers.current[id] = timer;
  }, []);

  useEffect(() => () => {
    Object.values(toastTimers.current).forEach((timer) => clearTimeout(timer));
    toastTimers.current = {};
  }, []);

  useEffect(() => {
    if (mode !== 'signup') {
      signUpScrollTriggered.current = false;
      return;
    }
    const { fullName, email, password, confirmPassword } = signUpForm;
    const ready = fullName && email && password && confirmPassword;
    if (ready && !signUpScrollTriggered.current) {
      signUpScrollTriggered.current = true;
      signUpButtonRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [mode, signUpForm]);

  const validateEmail = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

  const handleModeSwitch = (nextMode: 'signup' | 'login') => {
    setErrors({});
    setMode(nextMode);
  };

  const handleSignUpChange = (field: keyof typeof signUpForm, value: string) => {
    setSignUpForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const handleLoginChange = (field: keyof typeof loginForm, value: string | boolean) => {
    setLoginForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const validateSignUp = () => {
    const nextErrors: Record<string, string> = {};
    if (!signUpForm.fullName.trim()) {
      nextErrors.fullName = 'Please share your name so we can greet you properly.';
    }
    if (!validateEmail(signUpForm.email)) {
      nextErrors.email = 'We need a valid email to keep you informed.';
    }
    if (signUpForm.password.length < 8) {
      nextErrors.password = 'Choose a password that is at least 8 characters long.';
    }
    if (signUpForm.password !== signUpForm.confirmPassword) {
      nextErrors.confirmPassword = 'Passwords must match before we continue.';
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const validateLogin = () => {
    const nextErrors: Record<string, string> = {};
    if (!validateEmail(loginForm.email)) {
      nextErrors.email = 'Please provide the email you registered with.';
    }
    if (!loginForm.password) {
      nextErrors.password = 'Your password is required to continue.';
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSignUpSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (loading) return;
    if (!validateSignUp()) {
      addToast('Please review the highlighted fields.', 'error');
      return;
    }
    setLoading(true);
    
    try {
      // Call backend registration API
      const response = await apiClient.post(`${API_BASE}/auth/register`, {
        email: signUpForm.email,
        password: signUpForm.password,
        age: undefined,
        sex: undefined,
        diabetes: false,
        hypertension: false,
        pregnancy: false,
        city: undefined,
      });
      
      // Set authentication state with user data from backend
      const user: AuthUser = {
        email: response.data.email,
        fullName: signUpForm.fullName || response.data.email.split('@')[0],
        createdAt: response.data.createdAt || new Date().toISOString(),
      };
      setAuth(user);
      
      addToast('Welcome aboard! Your profile is ready.', 'success');
      setSignUpForm({ fullName: '', email: '', password: '', confirmPassword: '' });
      
      // Set flag to show welcome screen BEFORE redirect
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('justLoggedIn', 'true');
      }
      
      // Redirect to main chat interface
      setTimeout(() => {
        router.push('/');
      }, 500);
    } catch (error: any) {
      console.error('Registration error:', error);
      const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.';
      addToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (loading) return;
    if (!validateLogin()) {
      addToast("Let's double-check your credentials.", 'error');
      return;
    }
    setLoading(true);
    
    try {
      // Call backend login API
      const response = await apiClient.post(`${API_BASE}/auth/login`, {
        email: loginForm.email,
        password: loginForm.password,
      });
      
      // Set authentication state with user data from backend
      const user: AuthUser = {
        email: response.data.email,
        fullName: response.data.email.split('@')[0], // Fallback name from email
        createdAt: response.data.createdAt || new Date().toISOString(),
      };
      setAuth(user);
      
      addToast('You are safely signed in. How can we support you today?', 'success');
      setLoginForm((prev) => ({ ...prev, password: '' }));
      
      // Set flag to show welcome screen BEFORE redirect
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('justLoggedIn', 'true');
      }
      
      // Redirect to main chat interface
      setTimeout(() => {
        router.push('/');
      }, 500);
    } catch (error: any) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.detail || 'Invalid email or password. Please try again.';
      addToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const renderToastIcon = (variant: ToastVariant) => {
    if (variant === 'success') return <Check className="h-4 w-4" aria-hidden />;
    if (variant === 'error') return <XCircle className="h-4 w-4" aria-hidden />;
    return <Sparkles className="h-4 w-4" aria-hidden />;
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_15%,rgba(16,185,129,0.55),transparent_55%),radial-gradient(circle_at_85%_5%,rgba(34,197,94,0.4),transparent_55%),linear-gradient(180deg,rgba(2,6,23,0.92),rgba(2,6,23,0.95))]" />
      <div className="relative z-10 px-4 py-10 sm:px-8 md:px-12 lg:px-16">
        <div className="mx-auto flex w-full max-w-5xl flex-col items-center gap-10">
        <header className="flex w-full flex-col items-center gap-3 text-center">
          <div className="flex items-center gap-3 rounded-full border border-white/20 bg-white/10 px-5 py-2 text-sm font-semibold uppercase tracking-[0.32em] text-teal-100 shadow-lg shadow-teal-500/10">
            <ShieldCheck className="h-4 w-4" aria-hidden />
            SafeCare Companion
          </div>
          <div className="space-y-3">
            <h1 className="text-3xl font-semibold text-white sm:text-4xl md:text-5xl">Welcome to your trusted care partner</h1>
            <p className="max-w-2xl text-sm text-slate-300 sm:text-base">
              Create a secure account or return to continue your personalised health guidance. We combine empathetic support with clinical accuracy—always on your side.
            </p>
          </div>
        </header>

        <main className="relative w-full">
          <div className="relative overflow-hidden rounded-3xl border border-white/20 bg-white/10 shadow-[0_35px_120px_rgba(15,23,42,0.55)]">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.12),_transparent_55%),radial-gradient(circle_at_bottom,_rgba(34,197,94,0.12),_transparent_55%)]" aria-hidden />
            <div className="relative grid gap-0 md:grid-cols-2">
              <section className="hidden md:flex flex-col justify-between border-r border-white/10 bg-white/10 p-10 text-slate-100">
                <div className="space-y-6">
                  <p className="text-sm uppercase tracking-[0.28em] text-teal-100/80">Why people choose us</p>
                  <ul className="space-y-4 text-sm text-slate-200">
                    <li className="flex items-start gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 via-green-400 to-teal-500 text-slate-900 shadow-lg shadow-emerald-500/30">
                        <Sparkles className="h-4 w-4" aria-hidden />
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-white">Whole-person support</h3>
                        <p className="text-sm text-slate-200/80">Blend symptom guidance, prevention tips, and empathy—anytime you need us.</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-green-400 via-emerald-400 to-teal-400 text-slate-900 shadow-lg shadow-green-500/30">
                        <ShieldCheck className="h-4 w-4" aria-hidden />
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-white">Secure by design</h3>
                        <p className="text-sm text-slate-200/80">Enterprise-grade safety and privacy, purpose-built for healthcare experiences.</p>
                      </div>
                    </li>
                    <li className="flex items-start gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 via-green-400 to-teal-500 text-slate-900 shadow-lg shadow-emerald-500/30">
                        <Check className="h-4 w-4" aria-hidden />
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-white">Care that grows with you</h3>
                        <p className="text-sm text-slate-200/80">Personalised journeys with multilingual support, ready for your next question.</p>
                      </div>
                    </li>
                  </ul>
                </div>
                <footer className="hidden text-left text-xs text-slate-300/80 md:block">
                  Health information is shared securely and stays private.
                </footer>
              </section>

              <section className="relative flex w-full flex-col bg-slate-900/80 px-6 py-8 sm:px-8 md:px-10 md:py-12">
                <div className="mb-6 flex items-center justify-between text-slate-200">
                  <div className="flex items-center gap-2 rounded-full border border-white/10 bg-slate-900/60 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.28em] text-teal-200/80">
                    <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-emerald-300" aria-hidden />
                    {mode === 'signup' ? 'Create account' : 'Welcome back'}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleModeSwitch(mode === 'signup' ? 'login' : 'signup')}
                    className="text-xs font-semibold text-teal-200 transition hover:text-white"
                  >
                    {mode === 'signup' ? 'Have an account? Log in' : "Need an account? Let's sign up"}
                  </button>
                </div>

                <div className="relative min-h-[520px] overflow-y-auto overflow-x-hidden">
                  <div
                    className={clsx(
                      'absolute inset-0 transition-all duration-500 ease-out',
                      mode === 'signup'
                        ? 'translate-x-0 opacity-100'
                        : 'pointer-events-none translate-x-6 opacity-0'
                    )}
                  >
                    <form className="space-y-6" onSubmit={handleSignUpSubmit} noValidate>
                      <div className="space-y-5">
                        <FloatingField
                          id="signup-fullName"
                          label="Full Name"
                          value={signUpForm.fullName}
                          onChange={(value) => handleSignUpChange('fullName', value)}
                          placeholder="Your full name"
                          error={errors.fullName}
                        />
                        <FloatingField
                          id="signup-email"
                          label="Email address"
                          type="email"
                          value={signUpForm.email}
                          onChange={(value) => handleSignUpChange('email', value)}
                          placeholder="name@example.com"
                          error={errors.email}
                        />
                        <div className="space-y-3">
                          <FloatingField
                            id="signup-password"
                            label="Create password"
                            type="password"
                            value={signUpForm.password}
                            onChange={(value) => handleSignUpChange('password', value)}
                            placeholder="Enter a secure password"
                            error={errors.password}
                          />
                          <PasswordStrengthBar score={passwordScore} password={signUpForm.password} />
                        </div>
                        <FloatingField
                          id="signup-confirm"
                          label="Confirm password"
                          type="password"
                          value={signUpForm.confirmPassword}
                          onChange={(value) => handleSignUpChange('confirmPassword', value)}
                          placeholder="Re-enter your password"
                          error={errors.confirmPassword}
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={loading}
                        className={clsx(
                          'group relative flex w-full items-center justify-center gap-3 rounded-lg bg-gradient-to-r px-8 py-5 text-lg font-bold text-white shadow-lg shadow-emerald-500/40 transition hover:scale-[1.01] hover:shadow-xl hover:shadow-emerald-500/50 disabled:cursor-not-allowed disabled:opacity-60',
                          'from-emerald-500 via-green-500 to-teal-500'
                        )}
                        ref={signUpButtonRef}
                      >
                        {loading ? (
                          <>
                            <Loader2 className="h-6 w-6 animate-spin" aria-hidden />
                            <span>Signing up...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-6 w-6" aria-hidden />
                            <span>Sign up</span>
                          </>
                        )}
                      </button>
                    </form>
                  </div>

                  <div
                    className={clsx(
                      'absolute inset-0 transition-all duration-500 ease-out',
                      mode === 'login'
                        ? 'translate-x-0 opacity-100'
                        : 'pointer-events-none -translate-x-6 opacity-0'
                    )}
                  >
                    <form className="space-y-6" onSubmit={handleLoginSubmit} noValidate>
                      <FloatingField
                        id="login-email"
                        label="Email address"
                        type="email"
                        value={loginForm.email}
                        onChange={(value) => handleLoginChange('email', value)}
                        placeholder="name@example.com"
                        error={errors.email}
                      />
                      <FloatingField
                        id="login-password"
                        label="Password"
                        type="password"
                        value={loginForm.password}
                        onChange={(value) => handleLoginChange('password', value)}
                        placeholder="Your secure password"
                        error={errors.password}
                      />

                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <label className="flex items-center gap-3 text-sm text-slate-200">
                          <input
                            type="checkbox"
                            checked={loginForm.remember}
                            onChange={(event) => handleLoginChange('remember', event.target.checked)}
                            className="h-4 w-4 rounded border-slate-500 bg-transparent text-emerald-400 focus:ring-emerald-300"
                          />
                          Remember me on this device
                        </label>
                        <button
                          type="button"
                          className="text-sm font-semibold text-emerald-200 transition hover:text-white"
                        >
                          Forgot password?
                        </button>
                      </div>

                      <button
                        type="submit"
                        disabled={loading}
                        className={clsx(
                          'group relative mt-6 flex w-full items-center justify-center gap-3 rounded-lg bg-gradient-to-r px-8 py-5 text-lg font-bold text-white shadow-lg shadow-emerald-500/40 transition hover:scale-[1.01] hover:shadow-xl hover:shadow-emerald-500/50 disabled:cursor-not-allowed disabled:opacity-60',
                          'from-emerald-500 via-green-500 to-teal-500'
                        )}
                      >
                        {loading ? (
                          <>
                            <Loader2 className="h-6 w-6 animate-spin" aria-hidden />
                            <span>Signing in...</span>
                          </>
                        ) : (
                          <>
                            <ShieldCheck className="h-6 w-6" aria-hidden />
                            <span>Sign in</span>
                          </>
                        )}
                      </button>
                    </form>
                  </div>
                </div>

                <div className="mt-8 flex flex-col items-center gap-2 text-center">
                  <p className="text-xs text-slate-400">Your information is encrypted and stays confidential.</p>
                  <div className="text-sm text-slate-200">
                    {mode === 'signup' ? (
                      <>
                        Already have an account?{' '}
                        <button
                          type="button"
                          onClick={() => handleModeSwitch('login')}
                          className="font-semibold text-teal-200 transition hover:text-white"
                        >
                          Log in
                        </button>
                      </>
                    ) : (
                      <>
                        Don’t have an account?{' '}
                        <button
                          type="button"
                          onClick={() => handleModeSwitch('signup')}
                          className="font-semibold text-teal-200 transition hover:text-white"
                        >
                          Sign up
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </section>
            </div>
          </div>
        </main>
        </div>
      </div>

      <ToastContainer toasts={toasts} renderIcon={renderToastIcon} />
    </div>
  );
}

interface FloatingFieldProps {
  id: string;
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  type?: string;
  error?: string;
}

function FloatingField({ id, label, value, placeholder, onChange, type = 'text', error }: FloatingFieldProps) {
  const hasValue = value.length > 0;
  const describedBy = error ? `${id}-error` : undefined;

  return (
    <div className="space-y-2">
      <div className="relative">
        <input
          id={id}
          type={type}
          value={value}
          placeholder=" "
          onChange={(event) => onChange(event.target.value)}
          className={clsx(
            'peer block w-full rounded-2xl border bg-white/80 px-4 py-3 text-sm font-medium text-slate-900 shadow-inner shadow-black/10 transition-all duration-200 placeholder-transparent',
            'focus:border-teal-400 focus:bg-white focus:shadow-lg focus:shadow-teal-500/15 focus:outline-none focus:ring-4 focus:ring-teal-200/40',
            error ? 'border-rose-300 ring-rose-200/40 focus:border-rose-400 focus:ring-rose-200/50' : 'border-slate-200'
          )}
          aria-describedby={describedBy}
          aria-invalid={Boolean(error)}
        />
        <label
          htmlFor={id}
          className={clsx(
            'pointer-events-none absolute left-4 top-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 transition-all duration-200',
            'peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-[0.7rem] peer-placeholder-shown:uppercase peer-placeholder-shown:tracking-[0.25em] peer-placeholder-shown:text-slate-400/80',
            hasValue && '-translate-y-2 text-[0.6rem] text-teal-500',
            'peer-focus:-translate-y-2 peer-focus:text-[0.6rem] peer-focus:text-teal-400'
          )}
        >
          {label}
        </label>
      </div>
      <div className="min-h-[20px]">
        {error ? (
          <p id={describedBy} className="flex items-center gap-2 text-xs font-medium text-rose-200">
            <XCircle className="h-3.5 w-3.5" aria-hidden />
            {error}
          </p>
        ) : (
          hasValue && (
            <p className="flex items-center gap-2 text-xs font-medium text-emerald-200">
              <Check className="h-3.5 w-3.5" aria-hidden />
              Looks great!
            </p>
          )
        )}
      </div>
    </div>
  );
}

interface PasswordStrengthBarProps {
  score: number;
  password: string;
}

function PasswordStrengthBar({ score, password }: PasswordStrengthBarProps) {
  const segments = 5;
  const activeSegments = Math.min(score, segments);
  const label = password ? passwordStrengthLabels[Math.max(0, score - 1)] ?? 'Very Weak' : 'Start typing to check strength';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-300">
        <span>Password strength</span>
        <span className="font-semibold text-teal-200/80">{label}</span>
      </div>
      <div className="flex gap-1">
        {Array.from({ length: segments }).map((_, index) => (
          <span
            key={`segment-${index}`}
            className={clsx(
              'h-2 flex-1 rounded-full transition-all duration-200',
              index < activeSegments
                ? index >= 3
                  ? 'bg-gradient-to-r from-emerald-300 via-green-300 to-teal-300'
                  : 'bg-gradient-to-r from-amber-300 via-orange-300 to-rose-300'
                : 'bg-slate-600'
            )}
          />
        ))}
      </div>
    </div>
  );
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  renderIcon: (variant: ToastVariant) => ReactNode;
}

function ToastContainer({ toasts, renderIcon }: ToastContainerProps) {
  return (
    <div className="pointer-events-none fixed inset-x-4 bottom-6 z-50 mx-auto flex max-w-md flex-col gap-3 sm:inset-x-auto sm:right-6 sm:top-6 sm:bottom-auto">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={clsx(
            'pointer-events-auto flex items-center gap-3 rounded-2xl border border-white/20 bg-white/90 px-4 py-3 text-sm font-medium shadow-lg shadow-slate-900/30 backdrop-blur',
            toast.variant === 'success' && 'text-emerald-700',
            toast.variant === 'error' && 'text-rose-700',
            toast.variant === 'info' && 'text-emerald-700'
          )}
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 via-green-400 to-teal-500 text-white shadow-lg shadow-emerald-400/30">
            {renderIcon(toast.variant)}
          </span>
          <p className="flex-1 text-left text-sm leading-relaxed">{toast.message}</p>
        </div>
      ))}
    </div>
  );
}
