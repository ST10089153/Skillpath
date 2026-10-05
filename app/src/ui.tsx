import React, { ReactNode } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View, ViewStyle } from 'react-native';

export const colors = {
  bg: '#F7F8FA',
  card: '#FFFFFF',
  text: '#1B1F24',
  muted: '#4A5462',
  border: '#D5DAE1',
  primary: '#1F5FAD',
  primaryText: '#FFFFFF',
  accent: '#E8F0FB',
  success: '#1E7A46',
  successBg: '#E7F5EC',
  warnBg: '#FFF6E0',
  danger: '#B42318',
};

export const DISCLAIMER =
  'AI-generated suggestion based on published labour-market literature. Not professional career or financial advice.';

export function Screen({ children }: { children: ReactNode }) {
  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.screenContent} keyboardShouldPersistTaps="handled">
      <View style={styles.inner}>{children}</View>
    </ScrollView>
  );
}

export function Title({ children }: { children: ReactNode }) {
  return <Text style={styles.title} accessibilityRole="header">{children}</Text>;
}

export function Body({ children, muted, style }: { children: ReactNode; muted?: boolean; style?: object }) {
  return <Text style={[styles.body, muted && { color: colors.muted }, style]}>{children}</Text>;
}

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

type Variant = 'primary' | 'secondary' | 'danger';

export function Button({ label, onPress, variant = 'primary', disabled, hint }: {
  label: string; onPress: () => void; variant?: Variant; disabled?: boolean; hint?: string;
}) {
  const v = variant === 'primary' ? styles.btnPrimary : variant === 'danger' ? styles.btnDanger : styles.btnSecondary;
  const t = variant === 'secondary' ? { color: colors.primary } : { color: colors.primaryText };
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={hint}
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.btn, v, (disabled || pressed) && { opacity: disabled ? 0.45 : 0.8 }]}
    >
      <Text style={[styles.btnText, t]}>{label}</Text>
    </Pressable>
  );
}

export function Checkbox({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityState={{ checked }}
      onPress={() => onChange(!checked)}
      style={styles.checkRow}
    >
      <View style={[styles.checkBox, checked && styles.checkBoxOn]}>
        {checked && <Text style={styles.checkMark}>✓</Text>}
      </View>
      <Text style={[styles.body, { flex: 1 }]}>{label}</Text>
    </Pressable>
  );
}

export function Loading() {
  return <ActivityIndicator size="large" color={colors.primary} style={{ marginVertical: 32 }} />;
}

export function ErrorText({ error }: { error: string }) {
  if (!error) return null;
  return <Text style={styles.error} accessibilityLiveRegion="polite">{error}</Text>;
}

export function Difficulty({ level }: { level: number }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center' }} accessibilityLabel={`Difficulty ${level} of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <View key={i} style={[styles.dot, i <= level && styles.dotOn]} />
      ))}
      <Text style={[styles.small, { marginLeft: 6 }]}>Level {level}/5</Text>
    </View>
  );
}

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  screenContent: { padding: 16, paddingBottom: 32 },
  inner: { width: '100%', maxWidth: 560, alignSelf: 'center' },
  title: { fontSize: 26, fontWeight: '700', color: colors.text, marginBottom: 12, marginTop: 8 },
  h2: { fontSize: 19, fontWeight: '700', color: colors.text, marginBottom: 6 },
  body: { fontSize: 17, lineHeight: 25, color: colors.text, marginBottom: 8 },
  small: { fontSize: 14, color: colors.muted },
  card: { backgroundColor: colors.card, borderRadius: 12, borderWidth: 1, borderColor: colors.border, padding: 16, marginBottom: 12 },
  btn: { minHeight: 52, borderRadius: 10, paddingHorizontal: 18, justifyContent: 'center', alignItems: 'center', marginVertical: 6 },
  btnPrimary: { backgroundColor: colors.primary },
  btnSecondary: { backgroundColor: colors.card, borderWidth: 2, borderColor: colors.primary },
  btnDanger: { backgroundColor: colors.danger },
  btnText: { fontSize: 17, fontWeight: '600' },
  checkRow: { flexDirection: 'row', alignItems: 'flex-start', minHeight: 48, paddingVertical: 8 },
  checkBox: { width: 28, height: 28, borderRadius: 6, borderWidth: 2, borderColor: colors.primary, marginRight: 12, marginTop: 1, alignItems: 'center', justifyContent: 'center' },
  checkBoxOn: { backgroundColor: colors.primary },
  checkMark: { color: '#fff', fontSize: 18, fontWeight: '700' },
  error: { color: colors.danger, fontSize: 16, marginVertical: 8 },
  dot: { width: 12, height: 12, borderRadius: 6, borderWidth: 1.5, borderColor: colors.primary, marginRight: 4 },
  dotOn: { backgroundColor: colors.primary },
  input: { minHeight: 52, borderWidth: 1.5, borderColor: colors.border, borderRadius: 10, paddingHorizontal: 14, fontSize: 17, backgroundColor: colors.card, color: colors.text },
  chip: { borderWidth: 1.5, borderColor: colors.primary, borderRadius: 22, paddingHorizontal: 14, minHeight: 44, justifyContent: 'center', marginRight: 8, marginBottom: 8 },
  chipOn: { backgroundColor: colors.primary },
  banner: { backgroundColor: colors.warnBg, borderRadius: 10, padding: 14, marginBottom: 12 },
});
