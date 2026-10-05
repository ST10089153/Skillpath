import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, Progress } from '../api';
import { Body, Card, ErrorText, Loading, Screen, Title, colors, styles } from '../ui';

const MODULES_PER_MILESTONE = 3; // mirrors skillpath/config.py (display only)

export default function ProgressScreen({ userId }: { userId: string }) {
  const [prog, setProg] = useState<Progress | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.progress(userId).then(setProg).catch((e) => setError(e.message));
  }, [userId]);

  if (!prog) return <Screen>{error ? <ErrorText error={error} /> : <Loading />}</Screen>;

  const total = prog.total_modules || 6;
  const pct = Math.round((prog.modules_completed / total) * 100);
  const badges = Array.from({ length: Math.floor(total / MODULES_PER_MILESTONE) }, (_, i) => `MS${i + 1}`);

  return (
    <Screen>
      <Title>Your progress</Title>
      {prog.status !== 'adopted' ? (
        <Body>Start a pathway to see your progress here.</Body>
      ) : (
        <>
          <Card>
            <Text style={styles.h2}>{prog.skill}</Text>
            <View
              accessibilityRole="progressbar"
              accessibilityValue={{ min: 0, max: total, now: prog.modules_completed }}
              style={{ height: 18, backgroundColor: colors.accent, borderRadius: 9, overflow: 'hidden', marginVertical: 8 }}
            >
              <View style={{ width: `${pct}%`, height: '100%', backgroundColor: colors.primary }} />
            </View>
            <Body muted>{prog.modules_completed} of {total} modules ({pct}%)</Body>
            {prog.next_milestone_message ? <Body>{prog.next_milestone_message}</Body> : null}
          </Card>

          <Text style={styles.h2}>Milestones</Text>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 12 }}>
            {badges.map((b) => {
              const got = prog.milestones.includes(b);
              return (
                <View
                  key={b}
                  accessibilityLabel={`${b} ${got ? 'reached' : 'not reached yet'}`}
                  style={{ width: 96, height: 96, borderRadius: 48, marginRight: 12, marginBottom: 8, alignItems: 'center', justifyContent: 'center',
                           backgroundColor: got ? colors.success : colors.card, borderWidth: 2, borderColor: got ? colors.success : colors.border }}
                >
                  <Text style={{ fontSize: 22, fontWeight: '800', color: got ? '#fff' : colors.muted }}>{b}</Text>
                  <Text style={{ fontSize: 13, color: got ? '#fff' : colors.muted }}>{got ? 'Reached' : `${MODULES_PER_MILESTONE} modules`}</Text>
                </View>
              );
            })}
          </View>

          {prog.message !== '' && (
            <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{prog.message}</Body></View>
          )}
          {prog.difficulty !== null && <Body muted>Current difficulty: level {prog.difficulty} of 5</Body>}
        </>
      )}
    </Screen>
  );
}
