// SkillPath UI kit: the route map, in the "Ocean night" palette.
// The design idea comes from the subject itself: SkillPath plots a path between jobs, so a pathway is a line with six
// stops, milestones are interchanges, the current step is "you are here", and the recommendation branches to the
// occupations it serves. Visual language after markusfourie.dev (design only, not content or colours): a deep base,
// big condensed uppercase display type, pill buttons, softly rounded panels and large numerals.
// Type: Bebas Neue (display), Outfit (text; uppercase letter-spaced for labels and readouts). Both free Google Fonts.
// Colour: deep teal ground, aqua for actions, coral for the route line and numerals, sand only for "you are here".
// Every text/background pair meets WCAG AA (lowest 7.5:1 for text); motion is minimal and skipped under reduce-motion.
import { Ionicons } from '@expo/vector-icons';
import React, { ReactNode, useEffect, useRef } from 'react';
import { Animated, Easing, Platform, Pressable, ScrollView, StyleSheet, Text, View, ViewStyle } from 'react-native';

import { PRISM, useReducedMotion } from './fx';

export { PRISM, useReducedMotion };

export const colors = {
  bg: '#0B1A1E',          // deep teal
  card: '#12262B',        // raised panel
  cardDeep: '#081417',
  text: '#EEF6F5',        // 16.2:1 on the ground
  muted: '#A9C3C5',       // 9.6:1
  faint: '#8FAEB1',       // 7.5:1
  border: 'rgba(238,246,245,0.09)',
  hairline: 'rgba(238,246,245,0.20)',
  line: '#FF8A6B',        // coral: the route line and numerals, 7.7:1
  track: '#6F8E92',       // the part of the line not yet travelled
  primary: '#5FD3C6',     // aqua: buttons and links, 9.8:1
  primaryDark: '#45B8AB',
  primaryText: '#0B1A1E', // text on aqua, 9.8:1
  here: '#F2D49B',        // sand: "you are here" only, 12.4:1
  accent: '#163038',
  onAccent: '#EEF6F5',
  olive: '#6E6E46',
  success: '#5FD3C6',
  successBg: 'rgba(95,211,198,0.10)',
  warnBg: 'rgba(242,212,155,0.10)',
  warnText: '#F2D49B',
  danger: '#FF7A85',      // 7.1:1
  dangerSolid: '#FF7A85',
  dangerBg: 'rgba(255,122,133,0.10)',
};

export const fonts = {
  display: 'BebasNeue_400Regular',
  mono: 'Outfit_600SemiBold',     // readouts and labels: set uppercase and letter-spaced in the styles below
  regular: 'Outfit_400Regular',
  semibold: 'Outfit_600SemiBold',
  bold: 'Outfit_700Bold',
};

export const DISCLAIMER =
  'AI-generated suggestion based on published labour-market literature. Not professional career or financial advice.';

export const TAB_BAR_HEIGHT = 64;

const WEB = Platform.OS === 'web';
const NATIVE_DRIVER = !WEB;
export const EASE = Easing.bezier(0.32, 0.72, 0, 1);

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

/** Short fade-in for a screen's content; instant under reduce-motion. */
function FadeIn({ children }: { children: ReactNode }) {
  const reduced = useReducedMotion();
  const a = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (reduced) { a.setValue(1); return; }
    Animated.timing(a, { toValue: 1, duration: 280, easing: EASE, useNativeDriver: NATIVE_DRIVER }).start();
  }, [a, reduced]);
  return <Animated.View style={{ opacity: a }}>{children}</Animated.View>;
}

/** Pressable that dips slightly while pressed and shows a keyboard focus ring. */
export function PressableScale({ children, style, onPress, disabled, ...a11y }: {
  children: ReactNode; style?: object; onPress: () => void; disabled?: boolean;
  accessibilityRole?: 'button' | 'tab' | 'checkbox' | 'radio' | 'link'; accessibilityLabel?: string; accessibilityHint?: string;
  accessibilityState?: object;
}) {
  return (
    <Pressable {...a11y} disabled={disabled} onPress={onPress}
               style={(state) => [style, (state as { pressed?: boolean }).pressed ? { opacity: 0.8, transform: [{ translateY: 1 }] } : null,
                                  (state as { hovered?: boolean }).hovered ? { opacity: 0.92 } : null, focusVisible(state)]}>
      {children}
    </Pressable>
  );
}

export function Screen({ children }: { children: ReactNode }) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent} keyboardShouldPersistTaps="handled">
      <View style={styles.inner}><FadeIn>{children}</FadeIn></View>
    </ScrollView>
  );
}

/** Small mono readout above a headline, e.g. "Next stop". No decorative rule. */
export function Eyebrow({ children, color = colors.muted }: { children: ReactNode; color?: string }) {
  return <Text style={[styles.eyebrow, { color }]}>{children}</Text>;
}

export function Title({ children, sub }: { children: ReactNode; sub?: string }) {
  return (
    <View style={{ marginTop: 10, marginBottom: 20 }}>
      <Text style={styles.title} accessibilityRole="header">{children}</Text>
      {sub ? <Text style={[styles.body, { color: colors.muted, marginBottom: 0, marginTop: 6 }]}>{sub}</Text> : null}
    </View>
  );
}

/** Timetable-style section head: a full-width rule with a mono label under it. */
export function SectionLabel({ children, right }: { children: ReactNode; right?: string }) {
  return (
    <View style={styles.sectionHead}>
      <Text style={styles.sectionLabel}>{children}</Text>
      {right ? <Text style={styles.sectionLabel}>{right}</Text> : null}
    </View>
  );
}

export function Body({ children, muted, style }: { children: ReactNode; muted?: boolean; style?: object }) {
  return <Text style={[styles.body, muted && { color: colors.muted }, style]}>{children}</Text>;
}

/** A plain block with a thin border. Use sparingly: most content sits on the page between rules. */
export function Card({ children, style }: { children: ReactNode; style?: ViewStyle | ViewStyle[] | object; animate?: boolean; bezel?: boolean }) {
  return <View style={[styles.cardInner, { marginBottom: 16 }, style]}>{children}</View>;
}

/** Opening headline for a screen: a mono readout, a large serif headline and one line of copy. No box. */
export function Hero({ eyebrow, title, children }: {
  icon?: keyof typeof Ionicons.glyphMap; eyebrow?: string; title: string; children?: ReactNode;
}) {
  return (
    <View style={styles.hero}>
      {eyebrow ? <Eyebrow>{eyebrow}</Eyebrow> : null}
      <Text style={styles.heroTitle} accessibilityRole="header">{title}</Text>
      {children}
    </View>
  );
}

/** Large stop number ("04") set in the display face. */
export function BigNumber({ n }: { n: number }) {
  return <Text style={styles.bigNumber} accessibilityElementsHidden importantForAccessibility="no">{String(n).padStart(2, '0')}</Text>;
}

type Variant = 'primary' | 'secondary' | 'tonal' | 'danger';

/**
 * Ticket-style button: label on the left, an arrow (or the given icon) on the right. The primary button is solid
 * gold; the others are outlined. One primary action per screen.
 */
export function Button({ label, onPress, variant = 'primary', disabled, hint, icon }: {
  label: string; onPress: () => void; variant?: Variant; disabled?: boolean; hint?: string;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  const v = { primary: styles.btnPrimary, secondary: styles.btnSecondary, tonal: styles.btnTonal, danger: styles.btnDanger }[variant];
  const fg = variant === 'primary' ? colors.primaryText : variant === 'secondary' ? colors.primary
    : variant === 'danger' ? colors.danger : colors.text;
  return (
    <PressableScale accessibilityRole="button" accessibilityLabel={label} accessibilityHint={hint}
                    accessibilityState={{ disabled: !!disabled }} disabled={disabled} onPress={onPress}
                    style={[{ marginVertical: 5, borderRadius: 4 }, disabled ? { opacity: 0.45 } : null]}>
      <View style={[styles.btn, v]}>
        <Text style={[styles.btnText, { color: fg }]}>{label}</Text>
        <Ionicons name={icon ?? 'arrow-forward'} size={18} color={fg} />
      </View>
    </PressableScale>
  );
}

/** Plain text action ("Not now", "Edit my skills"), for secondary choices that do not need a box. */
export function TextLink({ label, onPress, hint }: { label: string; onPress: () => void; hint?: string }) {
  return (
    <PressableScale accessibilityRole="button" accessibilityLabel={label} accessibilityHint={hint} onPress={onPress}
                    style={{ minHeight: 44, justifyContent: 'center', alignSelf: 'flex-start', borderRadius: 4 }}>
      <Text style={styles.textLink}>{label}</Text>
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

/** Progress as a short route: travelled line in the route colour, the rest as track. */
export function ProgressBar({ value, total }: { value: number; total: number }) {
  const pct = total ? Math.round((value / total) * 100) : 0;
  return (
    <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: total, now: value }} style={styles.progressTrack}>
      <View style={[styles.progressFill, { width: `${pct}%` }]} />
    </View>
  );
}

/** A small tag. Kept for skill lists; avoid using it as decoration. */
export function Pill({ label, tone = 'accent', icon }: { label: string; tone?: 'accent' | 'success' | 'warn'; icon?: keyof typeof Ionicons.glyphMap }) {
  const fg = tone === 'accent' ? colors.text : colors.primary;
  const border = tone === 'accent' ? colors.hairline : colors.primary;
  return (
    <View style={[styles.pill, { borderColor: border }]}>
      {icon ? <Ionicons name={icon} size={13} color={fg} style={{ marginRight: 6 }} /> : null}
      <Text style={{ color: fg, fontSize: 13, fontFamily: fonts.regular }}>{label}</Text>
    </View>
  );
}

/** Loading placeholder shaped like the screen (static blocks; no spinner). */
export function Loading() {
  const bar = (w: string | number, h = 14, mb = 12) => <View style={[styles.skeleton, { width: w as number, height: h, marginBottom: mb }]} />;
  return (
    <View accessibilityRole="progressbar" accessibilityLabel="Loading" style={{ marginTop: 16 }}>
      {bar('30%', 12, 14)}
      {bar('80%', 34, 24)}
      {bar('100%', 1, 18)}
      {bar('90%')}
      {bar('70%')}
      {bar('50%', 14, 0)}
    </View>
  );
}

/** Composed empty state: icon, title and a line of guidance instead of a blank screen. */
export function EmptyState({ icon, title, children }: { icon: keyof typeof Ionicons.glyphMap; title: string; children?: ReactNode }) {
  return (
    <View style={{ paddingVertical: 20 }}>
      <Ionicons name={icon} size={28} color={colors.line} style={{ marginBottom: 12 }} />
      <Text style={styles.h2}>{title}</Text>
      {children}
    </View>
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

/** A label/value row in the mono face, like a line on a ticket. */
export function TicketRow({ label, value, last }: { label: string; value: ReactNode; last?: boolean }) {
  return (
    <View style={[styles.ticketRow, last && { borderBottomWidth: 0 }]}>
      <Text style={styles.ticketLabel}>{label}</Text>
      <View style={{ flex: 1 }}>{typeof value === 'string' ? <Text style={styles.ticketValue}>{value}</Text> : value}</View>
    </View>
  );
}

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  screenContent: { padding: 20, paddingBottom: 40 },
  inner: { width: '100%', maxWidth: 560, alignSelf: 'center' },
  title: { fontSize: 46, lineHeight: 46, fontFamily: fonts.display, color: colors.text, letterSpacing: 0.6, paddingTop: 4, ...balance },
  h2: { fontSize: 28, lineHeight: 30, fontFamily: fonts.display, color: colors.text, letterSpacing: 0.5, marginBottom: 6, paddingTop: 2, ...balance },
  eyebrow: { fontSize: 12, fontFamily: fonts.mono, letterSpacing: 2.4, textTransform: 'uppercase', marginBottom: 10 },
  sectionHead: { flexDirection: 'row', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: colors.hairline,
                 paddingTop: 10, marginTop: 22, marginBottom: 12 },
  sectionLabel: { fontSize: 12, fontFamily: fonts.mono, color: colors.muted, textTransform: 'uppercase', letterSpacing: 2.4 },
  body: { fontSize: 16, lineHeight: 25, color: colors.text, marginBottom: 8, fontFamily: fonts.regular },
  small: { fontSize: 13, lineHeight: 19, color: colors.faint, fontFamily: fonts.regular },
  numeric: { fontFamily: fonts.mono, fontVariant: ['tabular-nums'], letterSpacing: 1.2, textTransform: 'uppercase' },
  cardInner: { backgroundColor: colors.card, borderRadius: 22, padding: 20, borderWidth: 1, borderColor: colors.border },
  card: { backgroundColor: colors.card, borderRadius: 22, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: colors.border },
  hero: { paddingTop: 12, paddingBottom: 8, marginBottom: 8 },
  heroEyebrow: { color: colors.line, fontSize: 12, fontFamily: fonts.mono, letterSpacing: 2.4, textTransform: 'uppercase' },
  heroTitle: { color: colors.text, fontSize: 60, lineHeight: 58, fontFamily: fonts.display, marginBottom: 12, letterSpacing: 0.8, paddingTop: 6, ...balance },
  bigNumber: { fontSize: 56, lineHeight: 56, fontFamily: fonts.display, color: colors.line, paddingTop: 4 },
  btn: { minHeight: 54, borderRadius: 999, paddingHorizontal: 24, alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between' },
  btnPrimary: { backgroundColor: colors.primary },
  btnSecondary: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.primary },
  btnTonal: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.hairline },
  btnDanger: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.danger },
  btnText: { fontSize: 16, fontFamily: fonts.semibold, flex: 1, marginRight: 12, letterSpacing: 0.2 },
  textLink: { fontSize: 15, fontFamily: fonts.semibold, color: colors.primary, textDecorationLine: 'underline' },
  checkRow: { flexDirection: 'row', alignItems: 'center', minHeight: 52, paddingVertical: 8, borderRadius: 4 },
  checkBox: { width: 26, height: 26, borderRadius: 8, borderWidth: 1.5, borderColor: colors.primary, marginRight: 12, alignItems: 'center', justifyContent: 'center' },
  checkBoxOn: { backgroundColor: colors.primary },
  error: { color: colors.danger, fontSize: 15, marginVertical: 8, fontFamily: fonts.regular },
  dot: { width: 9, height: 9, borderRadius: 5, borderWidth: 1, borderColor: colors.track, marginRight: 5 },
  dotOn: { backgroundColor: colors.line, borderColor: colors.line },
  input: { minHeight: 52, borderWidth: 0, borderBottomWidth: 1, borderColor: colors.hairline, borderRadius: 0, paddingHorizontal: 4, fontSize: 16,
           backgroundColor: 'transparent', color: colors.text, fontFamily: fonts.regular },
  chip: { borderWidth: 1, borderColor: colors.hairline, backgroundColor: 'transparent', borderRadius: 999, paddingHorizontal: 14, minHeight: 40, justifyContent: 'center', marginRight: 8, marginBottom: 8 },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  banner: { backgroundColor: colors.card, borderRadius: 16, borderLeftWidth: 3, borderLeftColor: colors.line, paddingLeft: 16, paddingRight: 14, paddingVertical: 12, marginBottom: 14 },
  pill: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 999, paddingHorizontal: 9, paddingVertical: 4, marginRight: 6, marginBottom: 6, alignSelf: 'flex-start' },
  progressTrack: { height: 6, borderRadius: 3, backgroundColor: 'rgba(124,144,151,0.35)', overflow: 'hidden', marginVertical: 12 },
  progressFill: { height: '100%', borderRadius: 3, backgroundColor: colors.line },
  skeleton: { backgroundColor: 'rgba(238,246,245,0.07)', borderRadius: 8 },
  ticketRow: { flexDirection: 'row', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.border },
  ticketLabel: { width: 108, fontSize: 11, lineHeight: 20, fontFamily: fonts.mono, color: colors.faint, textTransform: 'uppercase', letterSpacing: 1.8 },
  ticketValue: { fontSize: 15, lineHeight: 22, fontFamily: fonts.regular, color: colors.text },
});
