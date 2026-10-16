import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, Progress } from '../api';
import { Body, Card, ErrorText, Loading, ProgressBar, Screen, SectionLabel, Title, colors, fonts, styles } from '../ui';

const MODULES_PER_MILESTONE = 3; // mirrors skillpath/config.py (display only)

export default function ProgressScreen({ userId }: { userId: string }) {
  const [prog, setProg] = useState<Progress | null>(null);
  const [error, setError] = useState('');
  const [labels, setLabels] = useState<Record<string, string>>({});
  useEffect(() => { api.vocabulary().then((v) => setLabels(v.labels ?? {})).catch(() => undefined); }, []);

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
            <SectionLabel>Current pathway</SectionLabel>
            <Text style={styles.h2}>{labels[prog.skill] ?? prog.skill}</Text>
            <ProgressBar value={prog.modules_completed} total={total} />
            <Body muted>{prog.modules_completed} of {total} modules ({pct}%)</Body>
            {prog.next_milestone_message ? <Body>{prog.next_milestone_message}</Body> : null}
          </Card>

          <SectionLabel>Milestones</SectionLabel>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 12 }}>
            {badges.map((b) => {
              const got = prog.milestones.includes(b);
              return (
                <View
                  key={b}
                  accessibilityLabel={`${b} ${got ? 'reached' : 'not reached yet'}`}
                  style={{ width: 96, height: 96, borderRadius: 48, marginRight: 12, marginBottom: 8, alignItems: 'center', justifyContent: 'center',
                           backgroundColor: got ? 'rgba(251,215,132,0.06)' : 'transparent', borderWidth: got ? 1.5 : 1, borderColor: got ? colors.primary : colors.hairline,
                           ...(got ? ({ boxShadow: '0 0 24px rgba(251,215,132,0.30), inset 0 0 18px rgba(251,215,132,0.10)' } as object) : {}) }}
                >
                  <Text style={{ fontSize: 24, fontFamily: fonts.display, color: got ? colors.primary : colors.muted }}>{b}</Text>
                  <Text style={{ fontSize: 11, letterSpacing: 1.5, textTransform: 'uppercase', fontFamily: fonts.regular, color: got ? colors.primary : colors.faint }}>{got ? 'Reached' : `${MODULES_PER_MILESTONE} modules`}</Text>
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
