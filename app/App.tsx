import { Ionicons } from '@expo/vector-icons';
import { BebasNeue_400Regular } from '@expo-google-fonts/bebas-neue';
import { Outfit_400Regular, Outfit_600SemiBold, Outfit_700Bold, useFonts } from '@expo-google-fonts/outfit';
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
import { Body, Loading, TAB_BAR_HEIGHT, colors, focusVisible, fonts, styles as ui } from './src/ui';

const USER_KEY = 'skillpath.user_id';
type Tab = 'home' | 'next' | 'pathway' | 'progress' | 'settings';
type IconName = keyof typeof Ionicons.glyphMap;
// Bottom navigation: five destinations; the active one is marked by a short route-coloured bar, like a station board.
const TABS: { key: Tab; label: string; icon: IconName; iconOn: IconName }[] = [
  { key: 'home', label: 'Home', icon: 'home-outline', iconOn: 'home' },
  { key: 'next', label: 'Next skill', icon: 'compass-outline', iconOn: 'compass' },
  { key: 'pathway', label: 'Pathway', icon: 'map-outline', iconOn: 'map' },
  { key: 'progress', label: 'Progress', icon: 'trophy-outline', iconOn: 'trophy' },
  { key: 'settings', label: 'Settings', icon: 'settings-outline', iconOn: 'settings' },
];

export default function App() {
  useFonts({ Outfit_400Regular, Outfit_600SemiBold, Outfit_700Bold, BebasNeue_400Regular }); // system font until loaded; never blocks
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

  // Nudge check, shared with the demo's marker tools. Returns whether a reminder was shown.
  async function checkNudge(): Promise<boolean> {
    if (!userId) return false;
    try {
      const n = await api.nudge(userId);
      // The engine's text says "modules"; the app and report call them steps.
      if (n.nudge) setNudge(n.message.replace(/\bmodules\b/g, 'steps').replace(/\bmodule\b/g, 'step'));
      return n.nudge;
    } catch { return false; /* offline: no nudge */ }
  }

  // Session events + nudge check. The nudge is checked BEFORE session_start updates last activity (DD7).
  useEffect(() => {
    if (!userId) return;
    const begin = async () => {
      await checkNudge();
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
  else content = <Settings userId={userId} onDeleted={onDeleted} onEditProfile={() => setEditingProfile(true)} onCheckNudge={checkNudge} />;

  const signedIn = ready && !!userId;

  return (
    <View style={s.root}>
      <StatusBar style="light" />
      <View style={s.header}>
        <Pressable accessibilityRole="button" accessibilityLabel="SkillPath home" disabled={!signedIn}
                   onPress={() => go('home')} style={{ flexDirection: 'row', alignItems: 'center' }}>
          <View style={s.logo} />
          <Text style={s.brand}>SkillPath</Text>
        </Pressable>
        {signedIn && tab !== 'home' && !editingProfile ? (
          <Pressable accessibilityRole="button" accessibilityLabel="Go to home" onPress={() => go('home')}
                     style={(st) => [s.headerBtn, focusVisible(st)]}>
            <Ionicons name="home-outline" size={20} color={colors.text} />
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
              <Pressable key={t.key} accessibilityRole="tab" accessibilityState={{ selected: on }} aria-selected={on} accessibilityLabel={t.label}
                         onPress={() => go(t.key)} style={(st) => [s.tab, focusVisible(st)]}>
                <View style={[s.tabIcon, on && s.tabIconOn]}>
                  <Ionicons name={t.icon} size={22} color={on ? colors.text : colors.faint} />
                </View>
                <Text style={[s.tabText, on && { color: colors.text }]}>{t.label}</Text>
              </Pressable>
            );
          })}
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  // Fill the dynamic viewport on web (100dvh avoids the iOS Safari jump) so the navigation stays pinned.
  root: { flex: 1, backgroundColor: colors.bg, paddingTop: Platform.OS === 'web' ? 0 : 36,
          ...(Platform.OS === 'web' ? ({ height: '100dvh', overflow: 'hidden' } as object) : {}) },
  demo: { paddingHorizontal: 16, paddingVertical: 6, borderBottomWidth: 1, borderColor: colors.border, backgroundColor: colors.cardDeep },
  demoText: { fontSize: 12, color: colors.primary, fontFamily: fonts.mono, textAlign: 'center' },
  header: { paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderColor: colors.border,
            flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  logo: { width: 30, height: 30, borderRadius: 15, borderWidth: 4, borderColor: colors.line, marginRight: 10 },
  brand: { fontSize: 30, lineHeight: 32, fontFamily: fonts.display, color: colors.text, letterSpacing: 1, paddingTop: 3 },
  headerBtn: { width: 44, height: 44, borderRadius: 4, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: colors.hairline },
  tabs: { flexDirection: 'row', height: TAB_BAR_HEIGHT + (Platform.OS === 'ios' ? 18 : 0), paddingBottom: Platform.OS === 'ios' ? 18 : 0,
          backgroundColor: colors.cardDeep, borderTopWidth: 1, borderColor: colors.hairline },
  tab: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 56 },
  tabIcon: { width: 40, height: 30, borderTopWidth: 3, borderTopColor: 'transparent', paddingTop: 4, alignItems: 'center', justifyContent: 'center', marginBottom: 2 },
  tabIconOn: { borderTopColor: colors.line },
  tabText: { fontSize: 11, color: colors.faint, fontFamily: fonts.mono, letterSpacing: 0.5 },
});
