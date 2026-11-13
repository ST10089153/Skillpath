import React, { useEffect, useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { Text, View } from 'react-native';

import { api, API_URL } from '../api';
import { DEMO } from '../demo';
import { Body, Button, Card, DISCLAIMER, ErrorText, Screen, Title, colors, styles } from '../ui';

const RULE = 'Reminders come only while a pathway is open (a recommendation, "Not now" or an unfinished pathway), '
  + 'after two days without activity, at most once a day, and stop after three unopened until you return.';

export default function Settings({ userId, onDeleted, onEditProfile, onCheckNudge }: {
  userId: string; onDeleted: () => void; onEditProfile: () => void; onCheckNudge: () => Promise<boolean>;
}) {
  const [arm, setArm] = useState<'A' | 'B' | ''>('');
  const [demoNote, setDemoNote] = useState('');
  useEffect(() => {
    if (!DEMO) return;
    api.myData(userId).then((d) => setArm(((d as { user?: { arm?: 'A' | 'B' } }).user?.arm) ?? '')).catch(() => undefined);
  }, [userId]);

  async function switchArm(next: 'A' | 'B') {
    setError('');
    try {
      await api.demoArm(userId, next);
      setArm(next);
      setDemoNote(next === 'A' ? 'Version A: open Next skill to see the income estimate and its source.'
                               : 'Version B: Next skill now shows no income. The recommendation itself is unchanged.');
    } catch (e) { setError((e as Error).message); }
  }

  async function simulateInactive() {
    setError('');
    try {
      const r = await api.demoInactive(userId, 2);
      const shown = await onCheckNudge();
      setDemoNote(shown
        ? `${r.days_inactive} days without activity: the reminder is now shown at the top of the screen.`
        : `${r.days_inactive} days without activity, but no reminder is due. ${RULE}`);
    } catch (e) { setError((e as Error).message); }
  }

  async function checkAgain() {
    setError('');
    const shown = await onCheckNudge();
    setDemoNote(shown ? 'A reminder is due and is shown at the top of the screen.' : `No reminder now. ${RULE}`);
  }
  const [data, setData] = useState<string>('');
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState('');

  async function view() {
    setError('');
    try {
      setData(JSON.stringify(await api.myData(userId), null, 2));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function del() {
    setError('');
    try {
      await api.deleteMe(userId);
      onDeleted();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <Screen>
      <Title>Settings</Title>
      <Card>
        <Text style={styles.h2}>Your ID</Text>
        <Body>{userId}</Body>
        <Body muted>This random ID is the only thing that links your data. No name, email or phone number is stored.</Body>
      </Card>

      <Button label="Edit my skills" icon="create-outline" variant="tonal" onPress={onEditProfile} />
      <Button label={data ? 'Refresh my data' : 'View my data'} icon="eye-outline" variant="tonal" onPress={view} />
      {data !== '' && (
        <Card><Text style={{ fontFamily: 'monospace', fontSize: 13, color: colors.text }} selectable>{data}</Text></Card>
      )}

      <Card>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
          <Ionicons name="trash-outline" size={22} color={colors.danger} style={{ marginRight: 8 }} />
          <Text style={[styles.h2, { marginBottom: 0 }]}>Delete my data</Text>
        </View>
        <Body>This permanently removes your profile, pathway and activity records from SkillPath.</Body>
        {!confirming ? (
          <Button label="Delete my data" icon="trash-outline" variant="danger" onPress={() => setConfirming(true)} />
        ) : (
          <>
            <Body style={{ fontFamily: 'Outfit_600SemiBold' }}>Are you sure? This cannot be undone.</Body>
            <Button label="Yes, delete everything" variant="danger" onPress={del} />
            <Button label="Cancel" variant="secondary" onPress={() => setConfirming(false)} />
          </>
        )}
      </Card>
      <ErrorText error={error} />

      {DEMO ? (
        <Card>
          <Text style={styles.h2}>For markers</Text>
          <Body muted>Demo-only tools to see two behaviours described in the report without waiting days.</Body>
          <Text style={[styles.numeric, { fontSize: 12, color: colors.faint, marginTop: 6, marginBottom: 4 }]}>
            {`INCOME VERSION (DD9) · NOW ${arm === 'A' ? 'A, INCOME SHOWN' : arm === 'B' ? 'B, INCOME HIDDEN' : '…'}`}
          </Text>
          <Button label="Use version A (income shown)" variant={arm === 'A' ? 'secondary' : 'tonal'} icon="cash-outline"
                  onPress={() => switchArm('A')} />
          <Button label="Use version B (income hidden)" variant={arm === 'B' ? 'secondary' : 'tonal'} icon="eye-off-outline"
                  onPress={() => switchArm('B')} />
          <Text style={[styles.numeric, { fontSize: 12, color: colors.faint, marginTop: 10, marginBottom: 4 }]}>REMINDERS (DD7)</Text>
          <Button label="Simulate two days without activity" variant="tonal" icon="time-outline" onPress={simulateInactive} />
          <Button label="Check for a reminder again today" variant="tonal" icon="refresh" onPress={checkAgain} />
          {demoNote !== '' && <View style={[styles.banner, { marginTop: 8, marginBottom: 0 }]}><Body style={{ marginBottom: 0 }}>{demoNote}</Body></View>}
        </Card>
      ) : null}

      <Card>
        <Text style={styles.h2}>About</Text>
        <Body>SkillPath is a research prototype for an Honours study at The Independent Institute of Education.</Body>
        <Body muted>{DISCLAIMER}</Body>
        <Text style={styles.small}>Server: {API_URL}</Text>
      </Card>
    </Screen>
  );
}
