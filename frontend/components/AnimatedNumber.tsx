'use client';

import { useEffect, useState, useRef } from 'react';

interface AnimatedNumberProps {
  value: string; // e.g., "92.7%", "1.1K", "Graph"
  duration?: number; // Animation duration in ms
}

export default function AnimatedNumber({ value, duration = 2000 }: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState<string>('0');
  const [hasAnimated, setHasAnimated] = useState(false);
  const elementRef = useRef<HTMLSpanElement>(null);

  // Parse the value to extract number and suffix
  const parseValue = (val: string): { number: number; suffix: string; isPercentage: boolean } => {
    // Check if it's a percentage
    if (val.includes('%')) {
      const num = parseFloat(val.replace('%', ''));
      return { number: num, suffix: '%', isPercentage: true };
    }
    // Check if it's a K value (e.g., "1.1K")
    if (val.toUpperCase().includes('K')) {
      const num = parseFloat(val.replace(/[Kk]/g, ''));
      return { number: num, suffix: 'K', isPercentage: false };
    }
    // Check if it's just a number
    const num = parseFloat(val);
    if (!isNaN(num)) {
      return { number: num, suffix: '', isPercentage: false };
    }
    // If it's not a number (like "Graph"), return as is
    return { number: 0, suffix: val, isPercentage: false };
  };

  useEffect(() => {
    const element = elementRef.current;
    if (!element || hasAnimated) return;

    const parsed = parseValue(value);
    
    // If it's not a number (like "Graph"), just show it
    if (parsed.suffix === value && parsed.number === 0) {
      setDisplayValue(value);
      setHasAnimated(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated) {
            setHasAnimated(true);
            
            const startTime = Date.now();
            const startValue = 0;
            const endValue = parsed.number;
            const suffix = parsed.suffix;
            const isPercentage = parsed.isPercentage;

            const animate = () => {
              const now = Date.now();
              const elapsed = now - startTime;
              const progress = Math.min(elapsed / duration, 1);
              
              // Easing function for smooth animation
              const easeOutQuart = 1 - Math.pow(1 - progress, 4);
              
              const currentValue = startValue + (endValue - startValue) * easeOutQuart;
              
              // Format the number based on type
              let formatted: string;
              if (isPercentage) {
                formatted = currentValue.toFixed(1) + suffix;
              } else if (suffix === 'K') {
                formatted = currentValue.toFixed(1) + suffix;
              } else {
                formatted = Math.round(currentValue).toString() + suffix;
              }
              
              setDisplayValue(formatted);

              if (progress < 1) {
                requestAnimationFrame(animate);
              } else {
                // Ensure final value is exact
                if (isPercentage) {
                  setDisplayValue(endValue.toFixed(1) + suffix);
                } else if (suffix === 'K') {
                  setDisplayValue(endValue.toFixed(1) + suffix);
                } else {
                  setDisplayValue(endValue.toString() + suffix);
                }
              }
            };

            animate();
          }
        });
      },
      { threshold: 0.3 } // Trigger when 30% of element is visible
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [value, duration, hasAnimated]);

  return <span ref={elementRef}>{displayValue}</span>;
}

