'use client';

const AUTH_TOKEN_KEY = 'health_companion_auth';
const AUTH_USER_KEY = 'health_companion_user';
const AUTH_LAST_ACTIVITY_KEY = 'health_companion_last_activity';

// Token expires if no activity for 12 hours (43200000 milliseconds)
const INACTIVITY_EXPIRY_MS = 12 * 60 * 60 * 1000; // 12 hours in milliseconds

export interface AuthUser {
  email: string;
  fullName: string;
  createdAt: string;
}

export function setAuth(user: AuthUser): void {
  if (typeof window === 'undefined') return;
  const now = Date.now();
  
  localStorage.setItem(AUTH_TOKEN_KEY, 'authenticated');
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  localStorage.setItem(AUTH_LAST_ACTIVITY_KEY, now.toString());
}

export function clearAuth(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  localStorage.removeItem(AUTH_LAST_ACTIVITY_KEY);
}

export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  
  // Check if auth token exists
  const authToken = localStorage.getItem(AUTH_TOKEN_KEY);
  if (authToken !== 'authenticated') return false;
  
  // Check if user has been inactive for 12 hours (activity-based expiration only)
  const lastActivityStr = localStorage.getItem(AUTH_LAST_ACTIVITY_KEY);
  if (!lastActivityStr) {
    // No activity tracked, treat as expired
    clearAuth();
    return false;
  }
  
  const lastActivity = parseInt(lastActivityStr, 10);
  const now = Date.now();
  const timeSinceActivity = now - lastActivity;
  
  if (timeSinceActivity >= INACTIVITY_EXPIRY_MS) {
    // No activity for 12 hours, expire token
    clearAuth();
    return false;
  }
  
  return true;
}

export function getAuthUser(): AuthUser | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem(AUTH_USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr) as AuthUser;
  } catch {
    return null;
  }
}

export function getLastActivityTime(): number | null {
  if (typeof window === 'undefined') return null;
  const activityStr = localStorage.getItem(AUTH_LAST_ACTIVITY_KEY);
  if (!activityStr) return null;
  try {
    return parseInt(activityStr, 10);
  } catch {
    return null;
  }
}

export function isTokenExpired(): boolean {
  if (typeof window === 'undefined') return true;
  return !isAuthenticated();
}

/**
 * Update last activity timestamp
 * Call this on user interactions (clicks, typing, API calls, etc.)
 */
export function updateActivity(): void {
  if (typeof window === 'undefined') return;
  const now = Date.now();
  localStorage.setItem(AUTH_LAST_ACTIVITY_KEY, now.toString());
}

