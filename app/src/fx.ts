// Shared visual-effect primitives used by the UI kit and the glass bloom.
import { useEffect, useState } from 'react';
import { AccessibilityInfo } from 'react-native';

// Spectrum tuned for a dark navy ground (saturated enough to read as prismatic light, not neon).
export const PRISM = ['#FF7A7A', '#FFB36B', '#FBD784', '#8BE3A8', '#6CC8FF', '#9D8CFF', '#F07BD0'] as const;

/** True when the user asked the OS to reduce motion. */
export function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then(setReduced).catch(() => undefined);
    const sub = AccessibilityInfo.addEventListener?.('reduceMotionChanged', setReduced);
    return () => sub?.remove?.();
  }, []);
  return reduced;
}
