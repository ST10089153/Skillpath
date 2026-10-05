import React, { useEffect, useMemo, useState } from 'react';
import { Pressable, Text, TextInput, View } from 'react-native';

import { api, Competency } from '../api';
import { Body, Button, Card, ErrorText, Loading, Screen, Title, colors, styles } from '../ui';

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
      <Text style={{ fontSize: 16, color: on ? colors.primaryText : colors.primary }}>{on ? `✓ ${label}` : label}</Text>
    </Pressable>
  );
}

export default function Profile({ userId, onDone }: { userId: string; onDone: () => void }) {
  const [groups, setGroups] = useState<{ occupation: string; skills: string[] }[] | null>(null);
  const [all, setAll] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [level, setLevel] = useState<Competency | null>(null);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.event(userId, 'assessment_started');
    api.vocabulary()
      .then((v) => { setGroups(v.occupations); setAll(v.skills); })
      .catch((e) => setError(e.message));
  }, [userId]);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? all.filter((s) => s.includes(q)) : [];
  }, [query, all]);

  const toggle = (s: string) =>
    setSelected((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));

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
      <Title>Your skills</Title>
      <Body>Select the skills you already have. Search, or browse by occupation.</Body>
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
            {selected.map((s) => <Chip key={s} label={s} on onPress={() => toggle(s)} />)}
          </View>
        </Card>
      )}

      {!groups && !error && <Loading />}
      {query.trim() !== '' ? (
        <Card>
          <Text style={styles.h2}>Results</Text>
          {matches.length === 0 && <Body muted>No skills match "{query}".</Body>}
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {matches.map((s) => <Chip key={s} label={s} on={selected.includes(s)} onPress={() => toggle(s)} />)}
          </View>
        </Card>
      ) : (
        groups?.map((g) => (
          <Card key={g.occupation}>
            <Text style={styles.h2}>{g.occupation}</Text>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
              {g.skills.map((s) => <Chip key={s} label={s} on={selected.includes(s)} onPress={() => toggle(s)} />)}
            </View>
          </Card>
        ))
      )}

      <Title>How confident are you?</Title>
      {LEVELS.map((l) => (
        <Pressable
          key={l.value}
          accessibilityRole="radio"
          accessibilityState={{ selected: level === l.value }}
          onPress={() => setLevel(l.value)}
          style={[styles.card, { borderWidth: 2 }, level === l.value && { borderColor: colors.primary, backgroundColor: colors.accent }]}
        >
          <Text style={styles.h2}>{level === l.value ? '◉ ' : '○ '}{l.label}</Text>
          <Body muted>{l.detail}</Body>
        </Pressable>
      ))}

      <ErrorText error={error} />
      <Button label={busy ? 'Saving…' : 'Find my next skill'} onPress={save} disabled={!level || busy} />
      {selected.length === 0 && <Body muted>Tip: add at least one skill so SkillPath can make a suggestion.</Body>}
    </Screen>
  );
}
