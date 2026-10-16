import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, Progress } from '../api';
import { Body, EmptyState, ErrorText, Loading, ProgressBar, Screen, SectionLabel, Title, colors, fonts, styles } from '../ui';

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
        <EmptyState icon="trophy-outline" title="No pathway yet">
          <Body muted>Accept a recommended skill under Next skill and your steps and milestones will show here.</Body>
        </EmptyState>
      ) : (
        <>
          <View>
            <SectionLabel>Current pathway</SectionLabel>
            <Text style={styles.h2}>{labels[prog.skill] ?? prog.skill}</Text>
            <ProgressBar value={prog.modules_completed} total={total} />
            <Body muted style={styles.numeric}>{prog.modules_completed} of {total} modules ({pct}%)</Body>
            {prog.next_milestone_message ? <Body>{prog.next_milestone_message}</Body> : null}
          </View>

          <SectionLabel>Milestones</SectionLabel>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 12 }}>
            {badges.map((b) => {
              const got = prog.milestones.includes(b);
              const face = (
                <>
                  <Text style={{ fontSize: 24, fontFamily: fonts.display, color: got ? colors.primary : colors.muted }}>{b}</Text>
                  <Text style={{ fontSize: 11, letterSpacing: 1.2, textTransform: 'uppercase', fontFamily: fonts.mono, color: got ? colors.primary : colors.faint }}>{got ? 'Reached' : `${MODULES_PER_MILESTONE} modules`}</Text>
                </>
              );
              // Milestones are interchanges on the route: a capsule marker, filled in the route colour once reached.
              return (
                <View key={b} accessibilityLabel={`${b} ${got ? 'reached' : 'not reached yet'}`}
                      style={{ alignItems: 'center', marginRight: 28, marginBottom: 8 }}>
                  <View style={{ width: 44, height: 24, borderRadius: 12, borderWidth: 4, borderColor: got ? '#FFFFFF' : colors.track,
                                 backgroundColor: got ? colors.line : colors.bg, marginBottom: 10 }} />
                  {face}
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
