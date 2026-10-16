// SkillPath UI kit. Editorial dark style (after the free "MNTN" Figma Community template) on the navy/gold palette
// of the researcher's Skillpath-ui design, refined with the redesign-existing-projects and high-end-visual-design
// skills (Leonxlnx/taste-skill) and Vercel's Web Interface Guidelines:
//  - one accent (gold); shadows tinted with the navy ground, never pure black; ambient light + grain on web
//  - type that avoids the usual AI defaults: Gloock (sharp, high-contrast serif) for display, Syne Mono for labels
//    and readouts, Lexend (designed for reading fluency) for body; tabular figures, balanced headline wraps
//  - "double-bezel" surfaces for key blocks (outer tray + inner core with a top highlight); radii vary by level
//  - pill buttons with a trailing icon "island"; hover, press and visible keyboard-focus states on every control
//  - staggered fade-and-rise entrances on a custom spring-like curve; skeleton loading; all motion is skipped
//    when the device's reduce-motion setting is on
// Hero art: a slowly turning glass bloom (GlassBloom.tsx) behind a fade, after the researcher's references.
// Prism: light split into a spectrum marks only the key moments (the bloom's edges, the
// primary button's rim, progress fill, reached milestones, the active tab). Decorative only: text never carries
// the spectrum, and the active-tab shimmer stops under reduce-motion.
// Fonts are free Google Fonts bundled with the app (system font until loaded). Every text/background pair
// meets WCAG AA (4.5:1 or better).
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import React, { createContext, ReactNode, useContext, useEffect, useRef, useState } from 'react';
import {
  AccessibilityInfo, Animated, Easing, Platform, Pressable, ScrollView, StyleSheet, Text, View, ViewStyle,
} from 'react-native';

import { PRISM, useReducedMotion } from './fx';
import GlassBloom from './GlassBloom';

export { PRISM, useReducedMotion };

export const colors = {
  bg: '#0B1D26',
  card: '#10262F',
  cardDeep: '#081820',
  text: '#FFFFFF',
  muted: '#A9B6BD',
  faint: '#9AA8AF',
  border: 'rgba(255,255,255,0.10)',
  hairline: 'rgba(255,255,255,0.22)',
  primary: '#FBD784',     // the single accent: gold
  primaryDark: '#E9C46A',
  primaryText: '#0B1D26',
  accent: '#13303B',      // quiet raised surface
  onAccent: '#FFFFFF',
  olive: '#6E6E46',
  success: '#FBD784',     // success uses the accent too (one accent colour)
  successBg: 'rgba(251,215,132,0.08)',
  warnBg: 'rgba(251,215,132,0.10)',
  warnText: '#FBD784',
  danger: '#FF8A8A',
  dangerSolid: '#FF8A8A',
  dangerBg: 'rgba(255,138,138,0.10)',
};

// Gradients for raised surfaces (top-left lighter, as if lit from above).
export const surfaces = {
  card: ['#17343F', '#0E232C'] as const,
  hero: ['#1B3A47', '#0B1D26'] as const,
  gold: ['#FCE3A4', '#E9C46A'] as const,
};

export const fonts = {
  display: 'Gloock_400Regular',
  mono: 'SyneMono_400Regular',
  regular: 'Lexend_400Regular',
  semibold: 'Lexend_600SemiBold',
  bold: 'Lexend_700Bold',
};

export const DISCLAIMER =
  'AI-generated suggestion based on published labour-market literature. Not professional career or financial advice.';

export const TAB_BAR_HEIGHT = 68;

const WEB = Platform.OS === 'web';
const NATIVE_DRIVER = !WEB;
/** Heavy, settling curve used for every entrance and transition. */
export const EASE = Easing.bezier(0.32, 0.72, 0, 1);

// Shadows carry the navy hue of the ground (redesign skill: tinted, single light source from above).
const depth = Platform.select({
  web: { boxShadow: '0 28px 56px -24px rgba(1,10,16,0.85), 0 6px 14px -6px rgba(1,10,16,0.6)' } as object,
  default: { shadowColor: '#010A10', shadowOpacity: 0.55, shadowRadius: 18, shadowOffset: { width: 0, height: 12 }, elevation: 8 },
});
const goldGlow = Platform.select({
  web: { boxShadow: '0 12px 30px -12px rgba(108,200,255,0.40), 0 14px 34px -14px rgba(240,123,208,0.38), 0 8px 22px -10px rgba(251,215,132,0.45)' } as object,
  default: { shadowColor: '#FBD784', shadowOpacity: 0.35, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 6 },
});
const focusRing = WEB ? ({ outlineStyle: 'solid', outlineWidth: 2, outlineColor: '#FBD784', outlineOffset: 3 } as object) : {};
const balance = WEB ? ({ textWrap: 'balance' } as object) : {};

// :focus-visible for React Native Web: show the focus ring only while the user navigates by keyboard.
let keyboardMode = false;
if (WEB && typeof window !== 'undefined') {
  window.addEventListener('keydown', (e) => { if (e.key === 'Tab' || e.key.startsWith('Arrow')) keyboardMode = true; }, true);
  window.addEventListener('pointerdown', () => { keyboardMode = false; }, true);
}
/** Style for a Pressable's state: a gold ring when focused from the keyboard. */
export const focusVisible = (state: unknown) => ((state as { focused?: boolean }).focused && keyboardMode ? focusRing : null);

// Each <Screen> numbers the blocks inside it so they cascade in one after another.
const Stagger = createContext<{ next: () => number } | null>(null);

/** Fade-and-rise entrance, staggered by position on the screen; instant when reduce-motion is on. */
function useEntrance() {
  const stagger = useContext(Stagger);
  const order = useRef<number | null>(null);
  if (order.current === null) order.current = stagger ? stagger.next() : 0;
  const a = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    let done = false;
    AccessibilityInfo.isReduceMotionEnabled()
      .catch(() => false)
      .then((reduced) => {
        if (done) return;
        if (reduced) a.setValue(1);
        else Animated.timing(a, { toValue: 1, duration: 650, delay: Math.min(order.current! * 70, 420), easing: EASE,
                                  useNativeDriver: NATIVE_DRIVER }).start();
      });
    return () => { done = true; };
  }, [a]);
  return { opacity: a, transform: [{ translateY: a.interpolate({ inputRange: [0, 1], outputRange: [18, 0] }) }] };
}

/** Pressable that sinks slightly while pressed, lifts on hover (web) and shows a gold focus ring. */
export function PressableScale({ children, style, onPress, disabled, onHover, ...a11y }: {
  children: ReactNode; style?: object; onPress: () => void; disabled?: boolean; onHover?: (h: boolean) => void;
  accessibilityRole?: 'button' | 'tab' | 'checkbox' | 'radio'; accessibilityLabel?: string; accessibilityHint?: string;
  accessibilityState?: object;
}) {
  const scale = useRef(new Animated.Value(1)).current;
  const to = (v: number) => Animated.spring(scale, { toValue: v, speed: 40, bounciness: 0, useNativeDriver: NATIVE_DRIVER }).start();
  return (
    <Pressable {...a11y} disabled={disabled} onPress={onPress}
               onPressIn={() => to(0.97)} onPressOut={() => to(1)}
               onHoverIn={() => { to(1.01); onHover?.(true); }} onHoverOut={() => { to(1); onHover?.(false); }}
               style={(state) => [style, focusVisible(state)]}>
      <Animated.View style={{ transform: [{ scale }] }}>{children}</Animated.View>
    </Pressable>
  );
}

/** A thin line of split light. `shimmer` slowly drifts the spectrum along it (static under reduce-motion). */
export function PrismLine({ height = 2, shimmer = true, style }: { height?: number; shimmer?: boolean; style?: object }) {
  const reduced = useReducedMotion();
  const [w, setW] = useState(0);
  const x = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (!w || reduced || !shimmer) { x.setValue(0); return; }
    const loop = Animated.loop(Animated.timing(x, { toValue: -w, duration: 7000, easing: Easing.linear, useNativeDriver: NATIVE_DRIVER }));
    loop.start();
    return () => loop.stop();
  }, [w, reduced, shimmer, x]);
  const band = [...PRISM, PRISM[0]] as unknown as typeof PRISM; // close the loop so the drift is seamless
  return (
    <View pointerEvents="none" onLayout={(e) => setW(e.nativeEvent.layout.width)}
          style={[{ height, overflow: 'hidden', borderRadius: height }, style]}>
      {w > 0 && (
        <Animated.View style={{ width: w * 2, height, flexDirection: 'row', transform: [{ translateX: x }] }}>
          <LinearGradient colors={band} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ width: w, height }} />
          <LinearGradient colors={band} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ width: w, height }} />
        </Animated.View>
      )}
    </View>
  );
}

export function Screen({ children }: { children: ReactNode }) {
  const counter = useRef(0);
  const value = useRef({ next: () => counter.current++ }).current;
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent} keyboardShouldPersistTaps="handled">
      <Stagger.Provider value={value}>
        <View style={styles.inner}>{children}</View>
      </Stagger.Provider>
    </ScrollView>
  );
}

/** Small gold, letter-spaced label led by a short rule. */
export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 10 }}>
      <View style={{ width: 28, height: 1.5, backgroundColor: colors.primary, marginRight: 10 }} />
      <Text style={styles.eyebrow}>{children}</Text>
    </View>
  );
}

export function Title({ children, sub }: { children: ReactNode; sub?: string }) {
  return (
    <View style={{ marginTop: 10, marginBottom: 20 }}>
      <Text style={styles.title} accessibilityRole="header">{children}</Text>
      {sub ? <Text style={[styles.body, { color: colors.muted, marginBottom: 0, marginTop: 6 }]}>{sub}</Text> : null}
    </View>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return <View style={{ marginTop: 12 }}><Eyebrow>{children}</Eyebrow></View>;
}

export function Body({ children, muted, style }: { children: ReactNode; muted?: boolean; style?: object }) {
  return <Text style={[styles.body, muted && { color: colors.muted }, style]}>{children}</Text>;
}

/** Raised block. `bezel` nests it in an outer tray (double-bezel) for the most important block on a screen. */
export function Card({ children, style, animate = true, bezel = false }: {
  children: ReactNode; style?: ViewStyle | ViewStyle[] | object; animate?: boolean; bezel?: boolean;
}) {
  const entrance = useEntrance();
  const core = (
    <LinearGradient colors={surfaces.card} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                    style={[styles.cardInner, bezel && { borderRadius: 12, overflow: 'hidden' }, style]}>
      {children}
    </LinearGradient>
  );
  return (
    <Animated.View style={[bezel ? styles.bezel : styles.cardShell, animate ? entrance : null]}>
      {core}
    </Animated.View>
  );
}

/** Page-opening block: eyebrow, large serif headline and standfirst inside a double-bezel tray. */
export function Hero({ eyebrow, title, children }: {
  icon?: keyof typeof Ionicons.glyphMap; eyebrow?: string; title: string; children?: ReactNode;
}) {
  const entrance = useEntrance();
  return (
    <Animated.View style={[styles.bezel, { marginBottom: 24 }, entrance]}>
      <LinearGradient colors={surfaces.hero} start={{ x: 1, y: 0 }} end={{ x: 0, y: 1 }} style={styles.hero}>
        <View style={styles.heroGlow} pointerEvents="none" />
        <View style={styles.bloom} pointerEvents="none"><GlassBloom size={250} /></View>
        {/* Fade keeps the text side of the hero calm so copy stays at full contrast over the bloom. */}
        <LinearGradient pointerEvents="none" colors={['rgba(18,40,50,0.97)', 'rgba(18,40,50,0.88)', 'rgba(18,40,50,0)']}
                        locations={[0, 0.58, 0.98]} start={{ x: 0, y: 0.5 }} end={{ x: 1, y: 0.5 }} style={StyleSheet.absoluteFill} />
        {eyebrow ? <Eyebrow>{eyebrow}</Eyebrow> : null}
        <Text style={styles.heroTitle} accessibilityRole="header">{title}</Text>
        {children}
      </LinearGradient>
    </Animated.View>
  );
}

/** Large faded index number ("01") used beside numbered steps. */
export function BigNumber({ n }: { n: number }) {
  return <Text style={styles.bigNumber} accessibilityElementsHidden importantForAccessibility="no">{String(n).padStart(2, '0')}</Text>;
}

type Variant = 'primary' | 'secondary' | 'tonal' | 'danger';

/**
 * Pill button. The primary button carries its icon in a trailing circle (button-in-button) that nudges forward
 * on hover; other variants show a leading icon.
 */
export function Button({ label, onPress, variant = 'primary', disabled, hint, icon }: {
  label: string; onPress: () => void; variant?: Variant; disabled?: boolean; hint?: string;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  const [hover, setHover] = useState(false);
  const v = { primary: null, secondary: styles.btnSecondary, tonal: styles.btnTonal, danger: styles.btnDanger }[variant];
  const fg = variant === 'primary' ? colors.primaryText : variant === 'secondary' ? colors.primary
    : variant === 'danger' ? colors.danger : colors.text;
  const primary = variant === 'primary';
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={hint}
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      onPress={onPress}
      onHover={setHover}
      style={[{ marginVertical: 6, borderRadius: 999 }, primary && !disabled ? goldGlow : null, disabled ? { opacity: 0.45 } : null]}
    >
      {primary ? (
        <LinearGradient colors={PRISM} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.prismRim}>
          <LinearGradient colors={surfaces.gold} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.btn, styles.btnPrimary]}>
            <Text style={[styles.btnText, { color: fg, flex: 1, textAlign: 'center' }]}>{label}</Text>
            <View style={[styles.btnIsland, hover && { transform: [{ translateX: 3 }] }]}>
              <Ionicons name={icon ?? 'arrow-forward'} size={16} color={colors.primaryText} />
            </View>
          </LinearGradient>
        </LinearGradient>
      ) : (
        <View style={[styles.btn, v, hover && { backgroundColor: 'rgba(255,255,255,0.04)' }]}>
          {icon ? <Ionicons name={icon} size={16} color={fg} style={{ marginRight: 10 }} /> : null}
          <Text style={[styles.btnText, { color: fg }]}>{label}</Text>
        </View>
      )}
    </PressableScale>
  );
}

export function Checkbox({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <Pressable accessibilityRole="checkbox" accessibilityState={{ checked }} onPress={() => onChange(!checked)}
               style={(s) => [styles.checkRow, focusVisible(s)]}>
      <View style={[styles.checkBox, checked && styles.checkBoxOn]}>
        {checked && <Ionicons name="checkmark" size={18} color={colors.primaryText} />}
      </View>
      <Text style={[styles.body, { flex: 1, marginBottom: 0 }]}>{label}</Text>
    </Pressable>
  );
}

export function ProgressBar({ value, total }: { value: number; total: number }) {
  const pct = total ? Math.round((value / total) * 100) : 0;
  const reduced = useReducedMotion();
  const w = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (reduced) w.setValue(pct);
    else Animated.timing(w, { toValue: pct, duration: 900, delay: 200, easing: EASE, useNativeDriver: false }).start();
  }, [pct, reduced, w]);
  const width = w.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] });
  return (
    <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: total, now: value }} style={styles.progressTrack}>
      <Animated.View style={[styles.progressFill, { width }]}>
        <LinearGradient colors={PRISM} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ flex: 1 }} />
      </Animated.View>
    </View>
  );
}

export function Pill({ label, tone = 'accent', icon }: { label: string; tone?: 'accent' | 'success' | 'warn'; icon?: keyof typeof Ionicons.glyphMap }) {
  const fg = tone === 'accent' ? colors.text : colors.primary;
  const border = tone === 'accent' ? colors.hairline : colors.primary;
  return (
    <View style={[styles.pill, { borderColor: border }, tone !== 'accent' && { backgroundColor: colors.successBg }]}>
      {icon ? <Ionicons name={icon} size={13} color={fg} style={{ marginRight: 6 }} /> : null}
      <Text style={{ color: fg, fontSize: 13, fontFamily: fonts.regular }}>{label}</Text>
    </View>
  );
}

/** Skeleton placeholder shaped like the content that is loading (gently pulsing unless reduce-motion is on). */
export function Loading() {
  const reduced = useReducedMotion();
  const pulse = useRef(new Animated.Value(0.5)).current;
  useEffect(() => {
    if (reduced) return;
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(pulse, { toValue: 1, duration: 700, easing: EASE, useNativeDriver: NATIVE_DRIVER }),
      Animated.timing(pulse, { toValue: 0.5, duration: 700, easing: EASE, useNativeDriver: NATIVE_DRIVER }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [pulse, reduced]);
  const bar = (w: string | number, h = 14, mb = 12) => <View style={[styles.skeleton, { width: w as number, height: h, marginBottom: mb }]} />;
  return (
    <Animated.View accessibilityRole="progressbar" accessibilityLabel="Loading" style={{ opacity: pulse, marginTop: 12 }}>
      {bar('40%', 12, 16)}
      {bar('85%', 34, 20)}
      <View style={[styles.cardInner, { marginBottom: 18 }]}>
        {bar('30%', 10, 14)}
        {bar('70%', 20, 16)}
        {bar('100%', 4, 18)}
        {bar('90%')}
        {bar('60%', 14, 0)}
      </View>
    </Animated.View>
  );
}

/** Composed empty state: icon, title and a line of guidance instead of a blank screen. */
export function EmptyState({ icon, title, children }: { icon: keyof typeof Ionicons.glyphMap; title: string; children?: ReactNode }) {
  return (
    <Card>
      <Ionicons name={icon} size={28} color={colors.primary} style={{ marginBottom: 12 }} />
      <Text style={styles.h2}>{title}</Text>
      {children}
    </Card>
  );
}

export function ErrorText({ error }: { error: string }) {
  if (!error) return null;
  return (
    <View style={[styles.banner, { borderLeftColor: colors.danger }]} accessibilityLiveRegion="polite">
      <Text style={{ color: colors.danger, fontSize: 15, fontFamily: fonts.regular }}>{error}</Text>
    </View>
  );
}

export function Difficulty({ level }: { level: number }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 4 }} accessibilityLabel={`Difficulty ${level} of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <View key={i} style={[styles.dot, i <= level && styles.dotOn]} />
      ))}
      <Text style={[styles.small, styles.numeric, { marginLeft: 8 }]}>Level {level}/5</Text>
    </View>
  );
}

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: 'transparent' },
  screenContent: { padding: 20, paddingBottom: 40 },
  inner: { width: '100%', maxWidth: 560, alignSelf: 'center' },
  title: { fontSize: 34, lineHeight: 42, fontFamily: fonts.display, color: colors.text, letterSpacing: -0.4, ...balance },
  h2: { fontSize: 21, lineHeight: 28, fontFamily: fonts.display, color: colors.text, marginBottom: 6, ...balance },
  eyebrow: { fontSize: 12, fontFamily: fonts.mono, color: colors.primary, textTransform: 'uppercase', letterSpacing: 2.2 },
  sectionLabel: { fontSize: 12, fontFamily: fonts.mono, color: colors.primary, textTransform: 'uppercase', letterSpacing: 2.2, marginTop: 8, marginBottom: 8 },
  body: { fontSize: 16, lineHeight: 26, color: colors.text, marginBottom: 8, fontFamily: fonts.regular },
  small: { fontSize: 13, lineHeight: 19, color: colors.faint, fontFamily: fonts.regular },
  // Readouts (counts, levels, durations) in the mono face.
  numeric: { fontFamily: fonts.mono, fontVariant: ['tabular-nums'], letterSpacing: 0.3 },
  cardShell: { marginBottom: 18, borderRadius: 10, ...depth },
  cardInner: { backgroundColor: colors.card, borderRadius: 10, padding: 20, borderWidth: 1, borderColor: colors.border,
               borderTopColor: 'rgba(255,255,255,0.16)' },
  // Double-bezel: an outer tray with a hairline and padding; the core sits inside with a smaller radius.
  bezel: { marginBottom: 18, padding: 5, borderRadius: 17, backgroundColor: 'rgba(255,255,255,0.03)', borderWidth: 1,
           borderColor: 'rgba(255,255,255,0.08)', ...depth },
  // Standalone raised block for pressables and lists that do not use <Card>.
  card: { backgroundColor: colors.card, borderRadius: 10, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: colors.border,
          borderTopColor: 'rgba(255,255,255,0.16)', ...depth,
          ...(WEB ? ({ backgroundImage: 'linear-gradient(135deg, #17343F 0%, #0E232C 100%)' } as object) : {}) },
  hero: { borderRadius: 12, padding: 22, paddingTop: 24, overflow: 'hidden', borderWidth: 1, borderColor: colors.border,
          borderTopColor: 'rgba(255,255,255,0.18)' },
  heroEyebrow: { color: colors.primary, fontSize: 12, fontFamily: fonts.mono, textTransform: 'uppercase', letterSpacing: 2.2 },
  heroTitle: { color: colors.text, fontSize: 38, lineHeight: 46, fontFamily: fonts.display, marginBottom: 10, letterSpacing: -0.6, ...balance },
  // Soft gold light in the top-right corner of the hero.
  heroGlow: { position: 'absolute', top: -90, right: -70, width: 220, height: 220, borderRadius: 110,
              backgroundColor: 'rgba(251,215,132,0.10)',
              ...(WEB ? ({ filter: 'blur(30px)' } as object) : {}) },
  prismRim: { borderRadius: 999, padding: 1.5 },
  bloom: { position: 'absolute', top: -78, right: -112, opacity: 0.95 },
  bigNumber: { fontSize: 56, lineHeight: 60, fontFamily: fonts.display, color: 'rgba(255,255,255,0.14)', fontVariant: ['lining-nums'], marginTop: -6, marginBottom: 4 },
  btn: { minHeight: 52, borderRadius: 999, paddingHorizontal: 22, justifyContent: 'center', alignItems: 'center', flexDirection: 'row' },
  btnPrimary: { paddingLeft: 22, paddingRight: 7 },
  btnIsland: { width: 38, height: 38, borderRadius: 19, backgroundColor: 'rgba(11,29,38,0.12)', alignItems: 'center', justifyContent: 'center',
               marginLeft: 12, ...(WEB ? ({ transitionProperty: 'transform', transitionDuration: '300ms',
                                             transitionTimingFunction: 'cubic-bezier(0.32,0.72,0,1)' } as object) : {}) },
  btnSecondary: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.primary },
  btnTonal: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.hairline },
  btnDanger: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.danger },
  btnText: { fontSize: 15, fontFamily: fonts.semibold, letterSpacing: 0.2 },
  checkRow: { flexDirection: 'row', alignItems: 'center', minHeight: 52, paddingVertical: 8, borderRadius: 6 },
  checkBox: { width: 26, height: 26, borderRadius: 6, borderWidth: 1.5, borderColor: colors.primary, marginRight: 12, alignItems: 'center', justifyContent: 'center' },
  checkBoxOn: { backgroundColor: colors.primary },
  error: { color: colors.danger, fontSize: 15, marginVertical: 8, fontFamily: fonts.regular },
  dot: { width: 10, height: 10, borderRadius: 5, borderWidth: 1, borderColor: colors.primary, marginRight: 5 },
  dotOn: { backgroundColor: colors.primary },
  input: { minHeight: 52, borderWidth: 0, borderBottomWidth: 1, borderColor: colors.hairline, borderRadius: 0, paddingHorizontal: 4, fontSize: 16,
           backgroundColor: 'transparent', color: colors.text, fontFamily: fonts.regular },
  chip: { borderWidth: 1, borderColor: colors.hairline, backgroundColor: 'transparent', borderRadius: 999, paddingHorizontal: 16, minHeight: 40, justifyContent: 'center', marginRight: 8, marginBottom: 8 },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  banner: { backgroundColor: colors.card, borderLeftWidth: 2, borderLeftColor: colors.primary, borderRadius: 6, padding: 14, marginBottom: 12 },
  pill: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 6, paddingHorizontal: 10, paddingVertical: 5, marginRight: 6, marginBottom: 6, alignSelf: 'flex-start' },
  progressTrack: { height: 4, borderRadius: 2, backgroundColor: colors.hairline, overflow: 'hidden', marginVertical: 12 },
  progressFill: { height: '100%', borderRadius: 2, overflow: 'hidden' },
  skeleton: { backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: 6 },
});
