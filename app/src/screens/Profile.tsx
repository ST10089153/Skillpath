import { Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, Text, TextInput, View } from 'react-native';

import { api, Competency, DetectedSkill } from '../api';
import { Body, Button, Card, ErrorText, Loading, Screen, SectionLabel, Title, colors, styles } from '../ui';

const LEVELS: { value: Competency; label: string; detail: string }[] = [
  { value: 'limited', label: 'Just starting', detail: "I'm new to most of this and have had little chance to use these skills." },
  { value: 'foundational', label: 'I know the basics', detail: "I've learnt the basics and used some of these skills." },
  { value: 'moderate', label: 'Fairly confident', detail: "I'm comfortable with several of these skills and use them regularly." },
];

function Chip({ label, on, onPress }: { label: string; on: boolean; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityState={{ checked: on }}
      accessibilityLabel={label}
      onPress={onPress}
      style={[styles.chip, on && styles.chipOn]}
    >
      <Text style={{ fontSize: 16, color: on ? colors.primaryText : colors.text }}>{on ? `✓ ${label}` : label}</Text>
    </Pressable>
  );
}

export default function Profile({ userId, onDone, onCancel }: { userId: string; onDone: () => void; onCancel?: () => void }) {
  const [groups, setGroups] = useState<{ category: string; skills: string[] }[] | null>(null);
  const [labels, setLabels] = useState<Record<string, string>>({});
  const [open, setOpen] = useState<string | null>(null);
  const [all, setAll] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [level, setLevel] = useState<Competency | null>(null);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [detected, setDetected] = useState<DetectedSkill[] | null>(null);
  const [cvBusy, setCvBusy] = useState(false);
  const [cvNote, setCvNote] = useState('');

  useEffect(() => {
    api.event(userId, 'assessment_started');
    api.vocabulary()
      .then((v) => { setGroups(v.categories); setAll(v.skills); setLabels(v.labels ?? {}); })
      .catch((e) => setError(e.message));
  }, [userId]);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? all.filter((s) => s.includes(q) || (labels[s] ?? '').toLowerCase().includes(q)) : [];
  }, [query, all]);

  const label = (s: string) => labels[s] ?? s;
  const toggle = (s: string) =>
    setSelected((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));

  async function uploadCv() {
    setError('');
    setCvNote('');
    const pick = await DocumentPicker.getDocumentAsync({
      type: ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'],
      copyToCacheDirectory: true,
    });
    if (pick.canceled || !pick.assets?.length) return;
    const a = pick.assets[0];
    setCvBusy(true);
    try {
      const r = await api.extractCv({ uri: a.uri, name: a.name, mimeType: a.mimeType, file: a.file });
      setDetected(r.skills);
      setCvNote(r.message);
      // Detected skills are pre-selected; the user can untick any that are wrong (DD6).
      setSelected((cur) => [...cur, ...r.skills.map((d) => d.skill).filter((s) => !cur.includes(s))]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCvBusy(false);
    }
  }

  async function save() {
    if (!level) return;
    setBusy(true);
    setError('');
    try {
      await api.saveProfile(userId, selected, level);
      onDone();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen>
      {onCancel ? (
        <Pressable accessibilityRole="button" accessibilityLabel="Back" onPress={onCancel}
                   style={{ flexDirection: 'row', alignItems: 'center', minHeight: 44, alignSelf: 'flex-start' }}>
          <Ionicons name="chevron-back" size={22} color={colors.primary} />
          <Text style={{ color: colors.primary, fontSize: 16, fontFamily: 'Outfit_600SemiBold' }}>Back</Text>
        </Pressable>
      ) : null}
      <Title sub="Upload your CV or choose the skills you already have.">Your skills</Title>
      <Card style={{ borderLeftWidth: 4, borderLeftColor: colors.primary }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
          <Ionicons name="document-text" size={22} color={colors.onAccent} style={{ marginRight: 8 }} />
          <Text style={[styles.h2, { marginBottom: 0 }]}>Start with your CV (optional)</Text>
        </View>
        <Body>SkillPath's built-in AI reads your CV and suggests the skills it finds. Your CV is processed by
          SkillPath's own server, is never sent to outside AI services, and is not saved.</Body>
        <Button label={cvBusy ? 'Reading your CV…' : 'Upload your CV'} hint="PDF, Word or text file"
                variant="primary" icon="cloud-upload-outline" disabled={cvBusy} onPress={uploadCv} />
        <Text style={[styles.small, { marginBottom: 8 }]}>{cvBusy ? 'The first time takes about 20 seconds.' : 'PDF, Word or text file.'}</Text>
        {cvNote !== '' && <Body muted>{cvNote}</Body>}
        {detected && detected.length > 0 && (
          <View>
            <Body style={{ fontWeight: '600' }}>Found {detected.length} skills. Untick any that are not right:</Body>
            {detected.map((d) => (
              <Pressable key={d.skill} accessibilityRole="checkbox" accessibilityState={{ checked: selected.includes(d.skill) }}
                         onPress={() => toggle(d.skill)}
                         style={{ flexDirection: 'row', backgroundColor: colors.cardDeep, borderRadius: 6, padding: 12, marginBottom: 8, minHeight: 48 }}>
                <Ionicons name={selected.includes(d.skill) ? 'checkbox' : 'square-outline'} size={24} color={colors.primary} style={{ marginRight: 10 }} />
                <View style={{ flex: 1 }}>
                  <Text style={{ fontSize: 16, fontFamily: 'Outfit_600SemiBold', color: colors.text }}>{label(d.skill)}</Text>
                  <Text style={[styles.small, { color: colors.primary, fontFamily: 'Outfit_600SemiBold' }]}>
                    {d.method === 'exact' ? 'Named in your CV' : `${Math.round(d.score * 100)}% match`}
                  </Text>
                  <Text style={styles.small} numberOfLines={2}>From your CV: "{d.evidence}"</Text>
                </View>
              </Pressable>
            ))}
          </View>
        )}
      </Card>

      <SectionLabel>Add or remove skills</SectionLabel>
      <TextInput
        style={styles.input}
        placeholder="Search skills"
        value={query}
        onChangeText={setQuery}
        accessibilityLabel="Search skills"
        autoCorrect={false}
        autoCapitalize="none"
      />
      <View style={{ height: 12 }} />

      {selected.length > 0 && (
        <Card style={{ backgroundColor: colors.accent }}>
          <Text style={styles.h2}>Selected ({selected.length})</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {selected.map((s) => <Chip key={s} label={label(s)} on onPress={() => toggle(s)} />)}
          </View>
        </Card>
      )}

      {!groups && !error && <Loading />}
      {query.trim() !== '' ? (
        <Card>
          <Text style={styles.h2}>Results</Text>
          {matches.length === 0 && <Body muted>No skills match "{query}".</Body>}
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {matches.map((s) => <Chip key={s} label={label(s)} on={selected.includes(s)} onPress={() => toggle(s)} />)}
          </View>
        </Card>
      ) : (
        groups?.map((g) => {
          const isOpen = open === g.category;
          const count = g.skills.filter((x) => selected.includes(x)).length;
          return (
            <View key={g.category} style={[styles.card, { padding: 0, overflow: 'hidden' }]}>
              <Pressable
                accessibilityRole="button"
                accessibilityState={{ expanded: isOpen }}
                accessibilityLabel={`${g.category}, ${g.skills.length} skills${count ? `, ${count} selected` : ''}`}
                onPress={() => setOpen(isOpen ? null : g.category)}
                style={{ flexDirection: 'row', alignItems: 'center', minHeight: 56, paddingHorizontal: 16 }}
              >
                <Text style={[styles.h2, { flex: 1, marginBottom: 0 }]}>{g.category}</Text>
                {count > 0 && <Text style={[styles.small, { color: colors.primary, marginRight: 8 }]}>{count} selected</Text>}
                <Text style={{ fontSize: 18, color: colors.muted }}>{isOpen ? '▴' : '▾'}</Text>
              </Pressable>
              {isOpen && (
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 16, paddingBottom: 8 }}>
                  {g.skills.map((x) => <Chip key={x} label={label(x)} on={selected.includes(x)} onPress={() => toggle(x)} />)}
                </View>
              )}
            </View>
          );
        })
      )}

      <SectionLabel>How confident are you?</SectionLabel>
      {LEVELS.map((l) => (
        <Pressable
          key={l.value}
          accessibilityRole="radio"
          accessibilityState={{ selected: level === l.value }}
          onPress={() => setLevel(l.value)}
          style={[styles.card, { borderWidth: 2 }, level === l.value && { borderColor: colors.primary, backgroundColor: colors.accent }]}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Ionicons name={level === l.value ? 'radio-button-on' : 'radio-button-off'} size={22} color={colors.primary} style={{ marginRight: 8 }} />
            <Text style={[styles.h2, { marginBottom: 0 }]}>{l.label}</Text>
          </View>
          <Body muted>{l.detail}</Body>
        </Pressable>
      ))}

      <ErrorText error={error} />
      <Button label={busy ? 'Saving…' : 'Find my next skill'} icon="arrow-forward" onPress={save} disabled={!level || busy} />
      {selected.length === 0 && <Body muted>Tip: add at least one skill so SkillPath can make a suggestion.</Body>}
    </Screen>
  );
}
