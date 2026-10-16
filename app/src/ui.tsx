// SkillPath UI kit. Editorial dark style after the free "MNTN" Figma Community template, keeping the navy/gold
// palette of the researcher's Skillpath-ui design: flat deep-navy surfaces with hairline borders, serif display
// headings (Playfair Display), small letter-spaced gold eyebrows led by a rule, outline controls, 2 px corners.
// Depth: raised blocks with subtle navy gradients, layered soft shadows and a top highlight; gold-gradient primary
// buttons. Motion: cards fade and rise in, pressables sink slightly, progress fills smoothly; all motion is
// skipped when the device's reduce-motion setting is on.
// Fonts are free Google Fonts bundled with the app (system font until loaded). Every text/background pair
// meets WCAG AA (4.5:1 or better).
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import React, { ReactNode, useEffect, useRef, useState } from 'react';
import {
  AccessibilityInfo, ActivityIndicator, Animated, Easing, Platform, Pressable, ScrollView, StyleSheet, Text, View, ViewStyle,
} from 'react-native';

export const colors = {
  bg: '#0B1D26',
  card: '#10262F',
  cardDeep: '#081820',
  text: '#FFFFFF',
  muted: '#A9B6BD',
  faint: '#9AA8AF',
  border: 'rgba(255,255,255,0.12)',
  hairline: 'rgba(255,255,255,0.22)',
  primary: '#FBD784',     // gold
  primaryDark: '#E9C46A',
  primaryText: '#0B1D26',
  accent: '#13303B',      // quiet raised surface
  onAccent: '#FFFFFF',
  olive: '#6E6E46',
  success: '#9CCB8A',
  successBg: 'rgba(156,203,138,0.10)',
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

const NATIVE_DRIVER = Platform.OS !== 'web';

const depth = Platform.select({
  web: { boxShadow: '0 24px 48px -18px rgba(0,0,0,0.65), 0 4px 10px rgba(0,0,0,0.30)' } as object,
  default: { shadowColor: '#000', shadowOpacity: 0.45, shadowRadius: 18, shadowOffset: { width: 0, height: 12 }, elevation: 8 },
});
const goldGlow = Platform.select({
  web: { boxShadow: '0 10px 28px -8px rgba(251,215,132,0.45)' } as object,
  default: { shadowColor: '#FBD784', shadowOpacity: 0.35, shadowRadius: 14, shadowOffset: { width: 0, height: 6 }, elevation: 6 },
});

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

/** Fade-and-rise entrance (420 ms); instant when reduce-motion is on. */
function useEntrance() {
  const a = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    let done = false;
    AccessibilityInfo.isReduceMotionEnabled()
      .catch(() => false)
      .then((reduced) => {
        if (done) return;
        if (reduced) a.setValue(1);
        else Animated.timing(a, { toValue: 1, duration: 420, easing: Easing.out(Easing.cubic), useNativeDriver: NATIVE_DRIVER }).start();
      });
    return () => { done = true; };
  }, [a]);
  return { opacity: a, transform: [{ translateY: a.interpolate({ inputRange: [0, 1], outputRange: [14, 0] }) }] };
}

/** Pressable that sinks slightly while pressed. */
export function PressableScale({ children, style, onPress, disabled, ...a11y }: {
  children: ReactNode; style?: object; onPress: () => void; disabled?: boolean;
  accessibilityRole?: 'button'; accessibilityLabel?: string; accessibilityHint?: string; accessibilityState?: object;
}) {
  const scale = useRef(new Animated.Value(1)).current;
  const to = (v: number) => Animated.spring(scale, { toValue: v, speed: 40, bounciness: 0, useNativeDriver: NATIVE_DRIVER }).start();
  return (
    <Pressable {...a11y} disabled={disabled} onPress={onPress} onPressIn={() => to(0.97)} onPressOut={() => to(1)} style={style}>
      <Animated.View style={{ transform: [{ scale }] }}>{children}</Animated.View>
    </Pressable>
  );
}

export const fonts = {
  display: 'PlayfairDisplay_600SemiBold',
  regular: 'Lexend_400Regular',
  semibold: 'Lexend_600SemiBold',
  bold: 'Lexend_700Bold',
};

export const DISCLAIMER =
  'AI-generated suggestion based on published labour-market literature. Not professional career or financial advice.';

export const TAB_BAR_HEIGHT = 68;

export function Screen({ children }: { children: ReactNode }) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent} keyboardShouldPersistTaps="handled">
      <View style={styles.inner}>{children}</View>
    </ScrollView>
  );
}

/** Small gold, letter-spaced label led by a short rule ("—— A HIKING GUIDE"). */
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
    <View style={{ marginTop: 10, marginBottom: 18 }}>
      <Text style={styles.title} accessibilityRole="header">{children}</Text>
      {sub ? <Text style={[styles.body, { color: colors.muted, marginBottom: 0, marginTop: 6 }]}>{sub}</Text> : null}
    </View>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return <View style={{ marginTop: 8 }}><Eyebrow>{children}</Eyebrow></View>;
}

export function Body({ children, muted, style }: { children: ReactNode; muted?: boolean; style?: object }) {
  return <Text style={[styles.body, muted && { color: colors.muted }, style]}>{children}</Text>;
}

export function Card({ children, style, animate = true }: { children: ReactNode; style?: ViewStyle | ViewStyle[] | object; animate?: boolean }) {
  const entrance = useEntrance();
  return (
    <Animated.View style={[styles.cardShell, animate ? entrance : null]}>
      <LinearGradient colors={surfaces.card} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.cardInner, style]}>
        {children}
      </LinearGradient>
    </Animated.View>
  );
}

/** Page-opening block: eyebrow, large serif headline and standfirst; no filled box. */
export function Hero({ eyebrow, title, children }: {
  icon?: keyof typeof Ionicons.glyphMap; eyebrow?: string; title: string; children?: ReactNode;
}) {
  const entrance = useEntrance();
  return (
    <Animated.View style={[styles.heroShell, entrance]}>
      <LinearGradient colors={surfaces.hero} start={{ x: 1, y: 0 }} end={{ x: 0, y: 1 }} style={styles.hero}>
        <View style={styles.heroGlow} pointerEvents="none" />
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

export function Button({ label, onPress, variant = 'primary', disabled, hint, icon }: {
  label: string; onPress: () => void; variant?: Variant; disabled?: boolean; hint?: string;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  const v = { primary: styles.btnPrimary, secondary: styles.btnSecondary, tonal: styles.btnTonal, danger: styles.btnDanger }[variant];
  const fg = variant === 'primary' ? colors.primaryText : variant === 'secondary' ? colors.primary
    : variant === 'danger' ? colors.danger : colors.text;
  const inner = (
    <>
      {icon ? <Ionicons name={icon} size={16} color={fg} style={{ marginRight: 10 }} /> : null}
      <Text style={[styles.btnText, { color: fg }]}>{label}</Text>
    </>
  );
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={hint}
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      onPress={onPress}
      style={[{ marginVertical: 6, borderRadius: 4 }, variant === 'primary' && !disabled ? goldGlow : null, disabled ? { opacity: 0.45 } : null]}
    >
      {variant === 'primary' ? (
        <LinearGradient colors={surfaces.gold} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.btn}>{inner}</LinearGradient>
      ) : (
        <View style={[styles.btn, v]}>{inner}</View>
      )}
    </PressableScale>
  );
}

export function Checkbox({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <Pressable accessibilityRole="checkbox" accessibilityState={{ checked }} onPress={() => onChange(!checked)} style={styles.checkRow}>
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
    else Animated.timing(w, { toValue: pct, duration: 700, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
  }, [pct, reduced, w]);
  const width = w.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] });
  return (
    <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: total, now: value }} style={styles.progressTrack}>
      <Animated.View style={[styles.progressFill, { width }]}>
        <LinearGradient colors={surfaces.gold} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ flex: 1 }} />
      </Animated.View>
    </View>
  );
}

export function Pill({ label, tone = 'accent', icon }: { label: string; tone?: 'accent' | 'success' | 'warn'; icon?: keyof typeof Ionicons.glyphMap }) {
  const fg = tone === 'success' ? colors.primary : tone === 'warn' ? colors.warnText : colors.text;
  const border = tone === 'accent' ? colors.hairline : colors.primary;
  return (
    <View style={[styles.pill, { borderColor: border }]}>
      {icon ? <Ionicons name={icon} size={13} color={fg} style={{ marginRight: 6 }} /> : null}
      <Text style={{ color: fg, fontSize: 13, fontFamily: fonts.regular }}>{label}</Text>
    </View>
  );
}

export function Loading() {
  return <ActivityIndicator size="large" color={colors.primary} style={{ marginVertical: 32 }} />;
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
      <Text style={[styles.small, { marginLeft: 8 }]}>Level {level}/5</Text>
    </View>
  );
}

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  screenContent: { padding: 20, paddingBottom: TAB_BAR_HEIGHT + 32 },
  inner: { width: '100%', maxWidth: 560, alignSelf: 'center' },
  title: { fontSize: 34, lineHeight: 42, fontFamily: fonts.display, color: colors.text },
  h2: { fontSize: 21, lineHeight: 28, fontFamily: fonts.display, color: colors.text, marginBottom: 6 },
  eyebrow: { fontSize: 12, fontFamily: fonts.semibold, color: colors.primary, textTransform: 'uppercase', letterSpacing: 3 },
  sectionLabel: { fontSize: 12, fontFamily: fonts.semibold, color: colors.primary, textTransform: 'uppercase', letterSpacing: 3, marginTop: 8, marginBottom: 8 },
  body: { fontSize: 16, lineHeight: 26, color: colors.text, marginBottom: 8, fontFamily: fonts.regular },
  small: { fontSize: 13, lineHeight: 19, color: colors.faint, fontFamily: fonts.regular },
  cardShell: { marginBottom: 18, borderRadius: 4, ...depth },
  cardInner: { backgroundColor: colors.card, borderRadius: 4, padding: 20, borderWidth: 1, borderColor: colors.border,
               borderTopColor: 'rgba(255,255,255,0.16)' },
  // Standalone raised block for pressables and lists that do not use <Card>.
  card: { backgroundColor: colors.card, borderRadius: 4, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: colors.border,
          borderTopColor: 'rgba(255,255,255,0.16)', ...depth,
          ...(Platform.OS === 'web' ? ({ backgroundImage: 'linear-gradient(135deg, #17343F 0%, #0E232C 100%)' } as object) : {}) },
  heroShell: { marginBottom: 22, borderRadius: 4, ...depth },
  hero: { borderRadius: 4, padding: 22, paddingTop: 24, overflow: 'hidden', borderWidth: 1, borderColor: colors.border,
          borderTopColor: 'rgba(255,255,255,0.18)' },
  // Soft gold light in the top-right corner of the hero.
  heroGlow: { position: 'absolute', top: -90, right: -70, width: 220, height: 220, borderRadius: 110,
              backgroundColor: 'rgba(251,215,132,0.10)',
              ...(Platform.OS === 'web' ? ({ filter: 'blur(30px)' } as object) : {}) },
  heroEyebrow: { color: colors.primary, fontSize: 12, fontFamily: fonts.semibold, textTransform: 'uppercase', letterSpacing: 3 },
  heroTitle: { color: colors.text, fontSize: 38, lineHeight: 46, fontFamily: fonts.display, marginBottom: 10 },
  bigNumber: { fontSize: 56, lineHeight: 60, fontFamily: fonts.display, color: 'rgba(255,255,255,0.14)', fontVariant: ['lining-nums'], marginTop: -6, marginBottom: 4 },
  btn: { minHeight: 52, borderRadius: 4, paddingHorizontal: 22, justifyContent: 'center', alignItems: 'center', flexDirection: 'row' },
  btnPrimary: { backgroundColor: colors.primary },
  btnSecondary: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.primary },
  btnTonal: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.hairline },
  btnDanger: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.danger },
  btnText: { fontSize: 13, fontFamily: fonts.semibold, textTransform: 'uppercase', letterSpacing: 1.2 },
  checkRow: { flexDirection: 'row', alignItems: 'center', minHeight: 52, paddingVertical: 8 },
  checkBox: { width: 26, height: 26, borderRadius: 2, borderWidth: 1.5, borderColor: colors.primary, marginRight: 12, alignItems: 'center', justifyContent: 'center' },
  checkBoxOn: { backgroundColor: colors.primary },
  error: { color: colors.danger, fontSize: 15, marginVertical: 8, fontFamily: fonts.regular },
  dot: { width: 10, height: 10, borderRadius: 5, borderWidth: 1, borderColor: colors.primary, marginRight: 5 },
  dotOn: { backgroundColor: colors.primary },
  input: { minHeight: 52, borderWidth: 0, borderBottomWidth: 1, borderColor: colors.hairline, borderRadius: 0, paddingHorizontal: 4, fontSize: 16,
           backgroundColor: 'transparent', color: colors.text, fontFamily: fonts.regular },
  chip: { borderWidth: 1, borderColor: colors.hairline, backgroundColor: 'transparent', borderRadius: 2, paddingHorizontal: 14, minHeight: 40, justifyContent: 'center', marginRight: 8, marginBottom: 8 },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  banner: { backgroundColor: colors.card, borderLeftWidth: 2, borderLeftColor: colors.primary, borderRadius: 0, padding: 14, marginBottom: 12 },
  pill: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 2, paddingHorizontal: 10, paddingVertical: 5, marginRight: 6, marginBottom: 6, alignSelf: 'flex-start' },
  progressTrack: { height: 4, borderRadius: 2, backgroundColor: colors.hairline, overflow: 'hidden', marginVertical: 12 },
  progressFill: { height: '100%', borderRadius: 2, overflow: 'hidden' },
});
