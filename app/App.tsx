import { Ionicons } from '@expo/vector-icons';
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
import { Body, Loading, TAB_BAR_HEIGHT, colors, styles as ui } from './src/ui';

const USER_KEY = 'skillpath.user_id';
type Tab = 'home' | 'next' | 'pathway' | 'progress' | 'settings';
type IconName = keyof typeof Ionicons.glyphMap;
// Material 3 navigation bar: five destinations, icon + label, active destination in a tonal pill.
const TABS: { key: Tab; label: string; icon: IconName; iconOn: IconName }[] = [
  { key: 'home', label: 'Home', icon: 'home-outline', iconOn: 'home' },
  { key: 'next', label: 'Next skill', icon: 'compass-outline', iconOn: 'compass' },
  { key: 'pathway', label: 'Pathway', icon: 'map-outline', iconOn: 'map' },
  { key: 'progress', label: 'Progress', icon: 'trophy-outline', iconOn: 'trophy' },
  { key: 'settings', label: 'Settings', icon: 'settings-outline', iconOn: 'settings' },
];

export default function App() {
  const [ready, setReady] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [tab, setTab] = useState<Tab>('home');
  const [nudge, setNudge] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const appState = useRef(AppState.currentState);

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
      <StatusBar style="dark" />
      <View style={s.header}>
        <Pressable accessibilityRole="button" accessibilityLabel="SkillPath home" disabled={!signedIn}
                   onPress={() => go('home')} style={{ flexDirection: 'row', alignItems: 'center' }}>
          <View style={s.logo}><Ionicons name="trail-sign" size={18} color="#fff" /></View>
          <Text style={s.brand}>SkillPath</Text>
        </Pressable>
        {signedIn && tab !== 'home' && !editingProfile ? (
          <Pressable accessibilityRole="button" accessibilityLabel="Go to home" onPress={() => go('home')} style={s.headerBtn}>
            <Ionicons name="home-outline" size={22} color={colors.primary} />
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
            <Body style={{ marginBottom: 0, fontWeight: '600' }}>{nudge}</Body>
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
                         onPress={() => go(t.key)} style={s.tab}>
                <View style={[s.tabIcon, on && s.tabIconOn]}>
                  <Ionicons name={on ? t.iconOn : t.icon} size={22} color={on ? colors.onAccent : colors.faint} />
                </View>
                <Text style={[s.tabText, on && { color: colors.text, fontWeight: '700' }]}>{t.label}</Text>
              </Pressable>
            );
          })}
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  // Fill the viewport on web so the navigation bar stays pinned to the bottom of the screen.
  root: { flex: 1, backgroundColor: colors.bg, paddingTop: Platform.OS === 'web' ? 0 : 36,
          ...(Platform.OS === 'web' ? { height: '100vh' as unknown as number, overflow: 'hidden' as const } : {}) },
  header: { paddingHorizontal: 16, paddingVertical: 12, backgroundColor: colors.card, borderBottomWidth: 1, borderColor: colors.border,
            flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  logo: { width: 30, height: 30, borderRadius: 10, backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center', marginRight: 10 },
  brand: { fontSize: 19, fontWeight: '800', color: colors.text, letterSpacing: -0.3 },
  headerBtn: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.accent },
  tabs: { flexDirection: 'row', height: TAB_BAR_HEIGHT + (Platform.OS === 'ios' ? 18 : 0), paddingBottom: Platform.OS === 'ios' ? 18 : 0,
          backgroundColor: colors.card, borderTopWidth: 1, borderColor: colors.border },
  tab: { flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: 56 },
  tabIcon: { width: 56, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center', marginBottom: 2 },
  tabIconOn: { backgroundColor: colors.accent },
  tabText: { fontSize: 12, color: colors.faint },
});
