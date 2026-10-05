import AsyncStorage from '@react-native-async-storage/async-storage';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useRef, useState } from 'react';
import { AppState, Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { api } from './src/api';
import NextSkill from './src/screens/NextSkill';
import Pathway from './src/screens/Pathway';
import Profile from './src/screens/Profile';
import ProgressScreen from './src/screens/ProgressScreen';
import Settings from './src/screens/Settings';
import Welcome from './src/screens/Welcome';
import { Body, Loading, colors, styles as ui } from './src/ui';

const USER_KEY = 'skillpath.user_id';
type Tab = 'next' | 'pathway' | 'progress' | 'settings';
const TABS: { key: Tab; label: string }[] = [
  { key: 'next', label: 'Next skill' },
  { key: 'pathway', label: 'Pathway' },
  { key: 'progress', label: 'Progress' },
  { key: 'settings', label: 'Settings' },
];

export default function App() {
  const [ready, setReady] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [tab, setTab] = useState<Tab>('next');
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
    setTab('next');
    setNudge('');
  }

  function go(t: Tab) {
    setTab(t);
    setRefreshKey((k) => k + 1);
  }

  let content: React.ReactNode;
  if (!ready) content = <Loading />;
  else if (!userId) content = <Welcome onDone={onCreated} />;
  else if (editingProfile) content = <Profile userId={userId} onDone={() => { setEditingProfile(false); go('next'); }} />;
  else if (tab === 'next') content = <NextSkill key={refreshKey} userId={userId} onAdopted={() => go('pathway')} onEditProfile={() => setEditingProfile(true)} />;
  else if (tab === 'pathway') content = <Pathway key={refreshKey} userId={userId} onGoToNextSkill={() => go('next')} />;
  else if (tab === 'progress') content = <ProgressScreen key={refreshKey} userId={userId} />;
  else content = <Settings userId={userId} onDeleted={onDeleted} onEditProfile={() => setEditingProfile(true)} />;

  const showTabs = ready && !!userId && !editingProfile;

  return (
    <View style={s.root}>
      <StatusBar style="dark" />
      <View style={s.header}>
        <Text style={s.brand} accessibilityRole="header">SkillPath</Text>
      </View>
      {nudge !== '' && userId && (
        <Pressable
          accessibilityRole="button"
          accessibilityHint="Opens your pathway"
          onPress={() => { api.event(userId, 'notification_opened'); setNudge(''); setEditingProfile(false); go('pathway'); }}
          style={[ui.banner, { marginHorizontal: 16, marginTop: 8, marginBottom: 0 }]}
        >
          <Body style={{ marginBottom: 0, fontWeight: '600' }}>{nudge}</Body>
          <Text style={ui.small}>Tap to continue</Text>
        </Pressable>
      )}
      <View style={{ flex: 1 }}>{content}</View>
      {showTabs && (
        <View style={s.tabs} accessibilityRole="tablist">
          {TABS.map((t) => (
            <Pressable
              key={t.key}
              accessibilityRole="tab"
              accessibilityState={{ selected: tab === t.key }}
              onPress={() => go(t.key)}
              style={[s.tab, tab === t.key && s.tabOn]}
            >
              <Text style={[s.tabText, tab === t.key && { color: colors.primary, fontWeight: '700' }]}>{t.label}</Text>
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg, paddingTop: Platform.OS === 'web' ? 0 : 36 },
  header: { paddingHorizontal: 16, paddingVertical: 10, backgroundColor: colors.card, borderBottomWidth: 1, borderColor: colors.border },
  brand: { fontSize: 20, fontWeight: '800', color: colors.primary },
  tabs: { flexDirection: 'row', borderTopWidth: 1, borderColor: colors.border, backgroundColor: colors.card, paddingBottom: Platform.OS === 'ios' ? 20 : 0 },
  tab: { flex: 1, minHeight: 56, alignItems: 'center', justifyContent: 'center', borderTopWidth: 3, borderColor: 'transparent' },
  tabOn: { borderColor: colors.primary },
  tabText: { fontSize: 15, color: colors.muted },
});
