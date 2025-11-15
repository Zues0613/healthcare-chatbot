'use client';

import { useEffect, useState, useRef } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import QuickLoader from './QuickLoader';

export default function NavigationLoader() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const prevPathRef = useRef<string>('');
  const isInitialMountRef = useRef(true);
  const loadingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Intercept link clicks to show loader immediately (both entering and exiting)
  useEffect(() => {
    const handleLinkClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      // Check for both regular links and Next.js Link components
      const link = target.closest('a[href]') as HTMLAnchorElement;
      
      if (link && link.href) {
        try {
          const url = new URL(link.href);
          const currentUrl = new URL(window.location.href);
          
          // Skip hash links (same page navigation)
          if (url.hash && url.pathname === currentUrl.pathname) {
            return;
          }
          
          // Only show loader for internal navigation (different pathname)
          if (url.origin === currentUrl.origin && url.pathname !== currentUrl.pathname) {
            // Don't show if navigating to main page from auth (welcome screen will handle it)
            // But allow it if coming from landing page (for "Start a pilot" button)
            const isToMainFromAuth = url.pathname === '/' && 
                                   currentUrl.pathname === '/auth' &&
                                   (document.referrer.includes('/auth') || 
                                    sessionStorage.getItem('justLoggedIn') === 'true');
            
            if (!isToMainFromAuth) {
              // Show loader immediately when link is clicked (for Get Started, Start a pilot, etc.)
              setLoading(true);
              
              // Clear any existing timer
              if (loadingTimerRef.current) {
                clearTimeout(loadingTimerRef.current);
              }
              
              // Set timer to hide loader after navigation (1.5-2 seconds = 1750ms)
              loadingTimerRef.current = setTimeout(() => {
                setLoading(false);
                loadingTimerRef.current = null;
              }, 1750);
            }
          }
        } catch (err) {
          // Invalid URL, ignore
        }
      }
    };

    // Use capture phase to catch all link clicks early (before Next.js handles them)
    // This ensures we catch Next.js Link components too
    document.addEventListener('click', handleLinkClick, true);
    return () => document.removeEventListener('click', handleLinkClick, true);
  }, []);

  // Handle pathname changes (for programmatic navigation and page entry)
  useEffect(() => {
    const currentPath = pathname + searchParams.toString();
    
    // Skip loading on initial mount
    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      prevPathRef.current = currentPath;
      return;
    }

    // Don't show loader if coming from auth (welcome screen will handle it)
    const isFromAuth = typeof window !== 'undefined' && (
      document.referrer.includes('/auth') || 
      sessionStorage.getItem('justLoggedIn') === 'true'
    );
    
    // Show loader for any path change (except from auth)
    // This handles both entering and exiting pages
    if (currentPath !== prevPathRef.current && !isFromAuth) {
      // Show loader immediately when path changes
      setLoading(true);
      prevPathRef.current = currentPath;
      
      // Clear any existing timer
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
      
      // Hide loader after navigation completes (1.5-2 seconds = 1750ms)
      loadingTimerRef.current = setTimeout(() => {
        setLoading(false);
        loadingTimerRef.current = null;
      }, 1750);
    } else {
      prevPathRef.current = currentPath;
    }

    return () => {
      if (loadingTimerRef.current) {
        clearTimeout(loadingTimerRef.current);
      }
    };
  }, [pathname, searchParams]);

  if (!loading) return null;

  return <QuickLoader />;
}

