import { Ionicons } from '@expo/vector-icons';
import { Lexend_400Regular, Lexend_600SemiBold, Lexend_700Bold, useFonts } from '@expo-google-fonts/lexend';
import { PlayfairDisplay_600SemiBold } from '@expo-google-fonts/playfair-display';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useRef, useState } from 'react';
import { AppState, Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from './src/api';
import Home from './src/screens/Home';
import NextSkill from './src/screens/NextSkill';
import Pathway from './src/screens/Pathway';
import Profile from './src/screens/Profile';
import ProgressScreen from './src/screens/ProgressScreen';
import Settings from './src/screens/Settings';
import Welcome from './src/screens/Welcome';
import { Body, Loading, PrismLine, TAB_BAR_HEIGHT, colors, focusVisible, fonts, styles as ui } from './src/ui';

const USER_KEY = 'skillpath.user_id';
type Tab = 'home' | 'next' | 'pathway' | 'progress' | 'settings';
type IconName = keyof typeof Ionicons.glyphMap;
// Floating "island" navigation: five destinations, outline icons; the active one sits on a soft gold pill.
const TABS: { key: Tab; label: string; icon: IconName; iconOn: IconName }[] = [
  { key: 'home', label: 'Home', icon: 'home-outline', iconOn: 'home' },
  { key: 'next', label: 'Next skill', icon: 'compass-outline', iconOn: 'compass' },
  { key: 'pathway', label: 'Pathway', icon: 'map-outline', iconOn: 'map' },
  { key: 'progress', label: 'Progress', icon: 'trophy-outline', iconOn: 'trophy' },
  { key: 'settings', label: 'Settings', icon: 'settings-outline', iconOn: 'settings' },
];

export default function App() {
  useFonts({ Lexend_400Regular, Lexend_600SemiBold, Lexend_700Bold, PlayfairDisplay_600SemiBold }); // system font until loaded; never blocks
  const [ready, setReady] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [tab, setTab] = useState<Tab>('home');
  const [nudge, setNudge] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const appState = useRef(AppState.currentState);

  // Web: tell the browser the page is dark (form controls, scrollbars) and colour its UI to match.
  useEffect(() => {
    if (Platform.OS !== 'web' || typeof document === 'undefined') return;
    document.documentElement.style.colorScheme = 'dark';
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) { meta = document.createElement('meta'); meta.setAttribute('name', 'theme-color'); document.head.appendChild(meta); }
    meta.setAttribute('content', colors.bg);
  }, []);

  // Restore the pseudonymous ID; drop it if the server no longer knows it (e.g. data deleted).
  useEffect(() => {
    (async () => {
      let id: string | null = null;
      try { id = await AsyncStorage.getItem(USER_KEY); } catch { id = null; }
      if (id) {
        try {
          await api.myData(id);
        } catch (e) {
          if ((e as Error).message === 'User not found') { await AsyncStorage.removeItem(USER_KEY); id = null; }
        }
      }
      setUserId(id);
      setReady(true);
    })();
  }, []);

  // Session events + nudge check. The nudge is checked BEFORE session_start updates last activity (DD7).
  useEffect(() => {
    if (!userId) return;
    const begin = async () => {
      try {
        const n = await api.nudge(userId);
        if (n.nudge) setNudge(n.message);
      } catch { /* offline: no nudge */ }
      api.event(userId, 'session_start');
    };
    begin();
    const sub = AppState.addEventListener('change', (next) => {
      if (appState.current === 'active' && next.match(/inactive|background/)) api.event(userId, 'session_end');
      if (appState.current.match(/inactive|background/) && next === 'active') begin();
      appState.current = next;
    });
    return () => sub.remove();
  }, [userId]);

  async function onCreated(id: string) {
    try { await AsyncStorage.setItem(USER_KEY, id); } catch { /* storage unavailable: session only */ }
    setUserId(id);
    setEditingProfile(true);
  }

  async function onDeleted() {
    try { await AsyncStorage.removeItem(USER_KEY); } catch { /* ignore */ }
    setUserId(null);
    setTab('home');
    setEditingProfile(false);
    setNudge('');
  }

  function go(t: Tab) {
    setEditingProfile(false);
    setTab(t);
    setRefreshKey((k) => k + 1);
  }

  let content: React.ReactNode;
  if (!ready) content = <Loading />;
  else if (!userId) content = <Welcome onDone={onCreated} />;
  else if (editingProfile) content = <Profile userId={userId} onDone={() => go('next')} onCancel={() => go(tab)} />;
  else if (tab === 'home') content = <Home key={refreshKey} userId={userId} go={go} onEditProfile={() => setEditingProfile(true)} />;
  else if (tab === 'next') content = <NextSkill key={refreshKey} userId={userId} onAdopted={() => go('pathway')} onEditProfile={() => setEditingProfile(true)} />;
  else if (tab === 'pathway') content = <Pathway key={refreshKey} userId={userId} onGoToNextSkill={() => go('next')} />;
  else if (tab === 'progress') content = <ProgressScreen key={refreshKey} userId={userId} />;
  else content = <Settings userId={userId} onDeleted={onDeleted} onEditProfile={() => setEditingProfile(true)} />;

  const signedIn = ready && !!userId;

  return (
    <View style={s.root}>
      <StatusBar style="light" />
      <View style={s.header}>
        <Pressable accessibilityRole="button" accessibilityLabel="SkillPath home" disabled={!signedIn}
                   onPress={() => go('home')} style={{ flexDirection: 'row', alignItems: 'center' }}>
          <View style={s.logo}><Ionicons name="trail-sign-outline" size={18} color={colors.primary} /></View>
          <Text style={s.brand}>SkillPath</Text>
        </Pressable>
        {signedIn && tab !== 'home' && !editingProfile ? (
          <Pressable accessibilityRole="button" accessibilityLabel="Go to home" onPress={() => go('home')}
                     style={(st) => [s.headerBtn, focusVisible(st)]}>
            <Ionicons name="home-outline" size={20} color={colors.primary} />
          </Pressable>
        ) : null}
      </View>
      {nudge !== '' && userId && (
        <Pressable
          accessibilityRole="button"
          accessibilityHint="Opens your pathway"
          onPress={() => { api.event(userId, 'notification_opened'); setNudge(''); go('pathway'); }}
          style={[ui.banner, { marginHorizontal: 16, marginTop: 10, marginBottom: 0, flexDirection: 'row', alignItems: 'center' }]}
        >
          <Ionicons name="notifications" size={20} color={colors.warnText} style={{ marginRight: 10 }} />
          <View style={{ flex: 1 }}>
            <Body style={{ marginBottom: 0, fontFamily: fonts.semibold }}>{nudge}</Body>
            <Text style={ui.small}>Tap to continue</Text>
          </View>
        </Pressable>
      )}
      <View style={{ flex: 1 }}>{content}</View>
      {signedIn && (
        <View style={s.tabs} accessibilityRole="tablist">
          {TABS.map((t) => {
            const on = tab === t.key && !editingProfile;
            return (
              <Pressable key={t.key} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={t.label}
                         onPress={() => go(t.key)} style={(st) => [s.tab, focusVisible(st)]}>
                <View style={[s.tabIcon, on && s.tabIconOn]}>
                  <Ionicons name={t.icon} size={22} color={on ? colors.primary : colors.faint} />
                </View>
                <Text style={[s.tabText, on && { color: colors.primary, fontFamily: fonts.semibold }]}>{t.label}</Text>
                {on ? <PrismLine height={2} style={{ width: 22, marginTop: 3 }} /> : <View style={{ height: 2, marginTop: 3 }} />}
              </Pressable>
            );
          })}
        </View>
      )}
      {Platform.OS === 'web' ? <View style={s.grain} pointerEvents="none" /> : null}
    </View>
  );
}

const s = StyleSheet.create({
  // Fill the dynamic viewport on web (100dvh avoids the iOS Safari jump) so the navigation stays pinned; an ambient
  // gold/teal light sits behind everything.
  root: { flex: 1, backgroundColor: colors.bg, paddingTop: Platform.OS === 'web' ? 0 : 36,
          ...(Platform.OS === 'web' ? ({ height: '100dvh', overflow: 'hidden',
            backgroundImage: 'radial-gradient(700px 420px at 100% -8%, rgba(251,215,132,0.09), transparent 62%), '
              + 'radial-gradient(640px 520px at -12% 108%, rgba(40,110,130,0.16), transparent 60%)' } as object) : {}) },
  // Fixed film grain over the whole app (web only, never intercepts touches).
  grain: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, opacity: 0.05,
           ...(Platform.OS === 'web' ? ({ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")" } as object) : {}) },
  header: { paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderColor: colors.border,
            flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  logo: { width: 32, height: 32, borderRadius: 9, borderWidth: 1, borderColor: colors.primary, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  brand: { fontSize: 22, fontFamily: fonts.display, color: colors.text, letterSpacing: -0.3 },
  headerBtn: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: colors.hairline },
  tabs: { flexDirection: 'row', height: TAB_BAR_HEIGHT, marginHorizontal: 12, marginBottom: Platform.OS === 'ios' ? 26 : 12, borderRadius: 24,
          backgroundColor: 'rgba(8,24,32,0.88)', borderWidth: 1, borderColor: 'rgba(255,255,255,0.10)', borderTopColor: 'rgba(255,255,255,0.16)',
          ...(Platform.OS === 'web'
            ? ({ boxShadow: '0 22px 44px -18px rgba(1,10,16,0.9), 0 4px 12px rgba(1,10,16,0.5)', backdropFilter: 'blur(16px)' } as object)
            : { shadowColor: '#010A10', shadowOpacity: 0.6, shadowRadius: 18, shadowOffset: { width: 0, height: 10 }, elevation: 12 }) },
  tab: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 56, borderRadius: 20 },
  tabIcon: { width: 52, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center', marginBottom: 2 },
  tabIconOn: { backgroundColor: 'rgba(251,215,132,0.14)' },
  tabText: { fontSize: 11, color: colors.faint, fontFamily: fonts.regular, letterSpacing: 0.5 },
});
