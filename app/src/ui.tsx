// SkillPath UI kit. Visual language from the researcher's Figma dashboard (Skillpath-ui): deep navy gradient
// surfaces, gold primary actions, steel-blue and olive tags, 6 px corners, Lexend type (free, Google Fonts;
// designed for reading fluency). Every text/background pair meets WCAG AA (4.5:1 or better).
import { Ionicons } from '@expo/vector-icons';
import React, { ReactNode } from 'react';
import { ActivityIndicator, Platform, Pressable, ScrollView, StyleSheet, Text, View, ViewStyle } from 'react-native';

export const colors = {
  bg: '#071A3D',
  card: '#0D3769',
  cardDeep: '#001F41',
  text: '#FFFFFF',
  muted: '#AEB9E1',
  faint: '#9AA7D3',
  border: 'rgba(174,185,225,0.22)',
  primary: '#EBC952',     // gold
  primaryDark: '#FED43D',
  primaryText: '#0B1739',
  accent: '#2C5587',      // steel-blue container
  onAccent: '#FFFFFF',
  olive: '#6E6E46',
  success: '#72B951',
  successBg: 'rgba(114,185,81,0.18)',
  warnBg: '#6E6E46',
  warnText: '#FFFFFF',
  danger: '#FF8A8A',
  dangerSolid: '#B42318',
  dangerBg: 'rgba(249,110,110,0.16)',
};

export const fonts = {
  regular: 'Lexend_400Regular',
  semibold: 'Lexend_600SemiBold',
  bold: 'Lexend_700Bold',
};

export const DISCLAIMER =
  'AI-generated suggestion based on published labour-market literature. Not professional career or financial advice.';

export const TAB_BAR_HEIGHT = 68;

const shadow = Platform.select({
  web: { boxShadow: '0 10px 30px rgba(0,8,30,0.45)' } as object,
  default: { shadowColor: '#000814', shadowOpacity: 0.45, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 6 },
});
// Navy gradient of the design's cards (web); native falls back to the solid card colour.
const gradient = (from: string, to: string) =>
  Platform.select({ web: { backgroundImage: `linear-gradient(160deg, ${from} 0%, ${to} 100%)` } as object, default: {} });

export function Screen({ children }: { children: ReactNode }) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent} keyboardShouldPersistTaps="handled">
      <View style={styles.inner}>{children}</View>
    </ScrollView>
  );
}

export function Title({ children, sub }: { children: ReactNode; sub?: string }) {
  return (
    <View style={{ marginTop: 6, marginBottom: 14 }}>
      <Text style={styles.title} accessibilityRole="header">{children}</Text>
      {sub ? <Text style={[styles.body, { color: colors.muted, marginBottom: 0 }]}>{sub}</Text> : null}
    </View>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return <Text style={styles.sectionLabel}>{children}</Text>;
}

export function Body({ children, muted, style }: { children: ReactNode; muted?: boolean; style?: object }) {
  return <Text style={[styles.body, muted && { color: colors.muted }, style]}>{children}</Text>;
}

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle | ViewStyle[] | object }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Hero({ icon, eyebrow, title, children }: {
  icon?: keyof typeof Ionicons.glyphMap; eyebrow?: string; title: string; children?: ReactNode;
}) {
  return (
    <View style={styles.hero}>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
        {icon ? <Ionicons name={icon} size={20} color={colors.primary} style={{ marginRight: 8 }} /> : null}
        {eyebrow ? <Text style={styles.heroEyebrow}>{eyebrow}</Text> : null}
      </View>
      <Text style={styles.heroTitle} accessibilityRole="header">{title}</Text>
      {children}
    </View>
  );
}

type Variant = 'primary' | 'secondary' | 'tonal' | 'danger';

export function Button({ label, onPress, variant = 'primary', disabled, hint, icon }: {
  label: string; onPress: () => void; variant?: Variant; disabled?: boolean; hint?: string;
  icon?: keyof typeof Ionicons.glyphMap;
}) {
  const v = { primary: styles.btnPrimary, secondary: styles.btnSecondary, tonal: styles.btnTonal, danger: styles.btnDanger }[variant];
  const fg = variant === 'secondary' ? colors.primary : variant === 'tonal' ? colors.onAccent : variant === 'danger' ? '#FFFFFF' : colors.primaryText;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={hint}
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.btn, v, (disabled || pressed) && { opacity: disabled ? 0.45 : 0.85 }]}
    >
      {icon ? <Ionicons name={icon} size={18} color={fg} style={{ marginRight: 8 }} /> : null}
      <Text style={[styles.btnText, { color: fg }]}>{label}</Text>
    </Pressable>
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
  return (
    <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: total, now: value }} style={styles.progressTrack}>
      <View style={[styles.progressFill, { width: `${pct}%` }]} />
    </View>
  );
}

export function Pill({ label, tone = 'accent', icon }: { label: string; tone?: 'accent' | 'success' | 'warn'; icon?: keyof typeof Ionicons.glyphMap }) {
  const bg = tone === 'success' ? colors.successBg : tone === 'warn' ? colors.warnBg : colors.accent;
  const fg = tone === 'success' ? colors.success : tone === 'warn' ? colors.warnText : colors.onAccent;
  return (
    <View style={[styles.pill, { backgroundColor: bg }]}>
      {icon ? <Ionicons name={icon} size={14} color={fg} style={{ marginRight: 4 }} /> : null}
      <Text style={{ color: fg, fontSize: 13, fontFamily: fonts.semibold }}>{label}</Text>
    </View>
  );
}

export function Loading() {
  return <ActivityIndicator size="large" color={colors.primary} style={{ marginVertical: 32 }} />;
}

export function ErrorText({ error }: { error: string }) {
  if (!error) return null;
  return (
    <View style={[styles.banner, { backgroundColor: colors.dangerBg }]} accessibilityLiveRegion="polite">
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
      <Text style={[styles.small, { marginLeft: 6 }]}>Level {level}/5</Text>
    </View>
  );
}

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  screenContent: { padding: 16, paddingBottom: TAB_BAR_HEIGHT + 32 },
  inner: { width: '100%', maxWidth: 560, alignSelf: 'center' },
  title: { fontSize: 28, fontFamily: fonts.bold, color: colors.text, letterSpacing: -0.4 },
  h2: { fontSize: 18, fontFamily: fonts.semibold, color: colors.text, marginBottom: 6 },
  sectionLabel: { fontSize: 13, fontFamily: fonts.semibold, color: colors.muted, textTransform: 'uppercase', letterSpacing: 0.8, marginTop: 8, marginBottom: 8 },
  body: { fontSize: 16, lineHeight: 24, color: colors.text, marginBottom: 8, fontFamily: fonts.regular },
  small: { fontSize: 13, color: colors.faint, fontFamily: fonts.regular },
  card: { backgroundColor: colors.card, borderRadius: 6, padding: 18, marginBottom: 14, borderWidth: 1, borderColor: colors.border,
          ...gradient(colors.card, colors.cardDeep), ...shadow },
  hero: { backgroundColor: '#1A2561', borderRadius: 6, padding: 22, marginBottom: 16, borderLeftWidth: 4, borderLeftColor: colors.primary,
          ...gradient('#2C5587', '#1A2561'), ...shadow },
  heroEyebrow: { color: colors.primary, fontSize: 13, fontFamily: fonts.semibold, textTransform: 'uppercase', letterSpacing: 0.8 },
  heroTitle: { color: '#FFFFFF', fontSize: 26, fontFamily: fonts.bold, letterSpacing: -0.3, marginBottom: 6 },
  btn: { minHeight: 52, borderRadius: 6, paddingHorizontal: 20, justifyContent: 'center', alignItems: 'center', flexDirection: 'row', marginVertical: 6 },
  btnPrimary: { backgroundColor: colors.primary },
  btnSecondary: { backgroundColor: 'transparent', borderWidth: 1.5, borderColor: colors.primary },
  btnTonal: { backgroundColor: colors.accent },
  btnDanger: { backgroundColor: colors.dangerSolid },
  btnText: { fontSize: 16, fontFamily: fonts.semibold },
  checkRow: { flexDirection: 'row', alignItems: 'center', minHeight: 52, paddingVertical: 8 },
  checkBox: { width: 28, height: 28, borderRadius: 4, borderWidth: 2, borderColor: colors.primary, marginRight: 12, alignItems: 'center', justifyContent: 'center' },
  checkBoxOn: { backgroundColor: colors.primary },
  error: { color: colors.danger, fontSize: 15, marginVertical: 8, fontFamily: fonts.regular },
  dot: { width: 12, height: 12, borderRadius: 6, borderWidth: 1.5, borderColor: colors.primary, marginRight: 4 },
  dotOn: { backgroundColor: colors.primary },
  input: { minHeight: 52, borderWidth: 1, borderColor: '#8A8F9D', borderRadius: 4, paddingHorizontal: 16, fontSize: 16,
           backgroundColor: 'rgba(11,23,57,0.55)', color: colors.text, fontFamily: fonts.regular },
  chip: { borderWidth: 1, borderColor: colors.border, backgroundColor: colors.accent, borderRadius: 4, paddingHorizontal: 14, minHeight: 40, justifyContent: 'center', marginRight: 8, marginBottom: 8 },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  banner: { backgroundColor: colors.warnBg, borderRadius: 6, padding: 14, marginBottom: 12 },
  pill: { flexDirection: 'row', alignItems: 'center', borderRadius: 4, paddingHorizontal: 10, paddingVertical: 5, marginRight: 6, marginBottom: 6, alignSelf: 'flex-start' },
  progressTrack: { height: 10, backgroundColor: 'rgba(174,185,225,0.18)', borderRadius: 5, overflow: 'hidden', marginVertical: 10 },
  progressFill: { height: '100%', backgroundColor: colors.success, borderRadius: 5 },
});
