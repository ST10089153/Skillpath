import React, { useEffect, useState } from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { Text, View } from 'react-native';

import { api, Progress } from '../api';
import { Body, Card, EmptyState, ErrorText, Loading, PRISM, ProgressBar, Screen, SectionLabel, Title, colors, fonts, styles } from '../ui';

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
          <Card bezel>
            <SectionLabel>Current pathway</SectionLabel>
            <Text style={styles.h2}>{labels[prog.skill] ?? prog.skill}</Text>
            <ProgressBar value={prog.modules_completed} total={total} />
            <Body muted style={styles.numeric}>{prog.modules_completed} of {total} modules ({pct}%)</Body>
            {prog.next_milestone_message ? <Body>{prog.next_milestone_message}</Body> : null}
          </Card>

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
              // A reached milestone is ringed with split light; one still to come is a quiet hairline circle.
              return got ? (
                <LinearGradient key={b} colors={PRISM} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                                accessibilityLabel={`${b} reached`}
                                style={{ width: 96, height: 96, borderRadius: 48, padding: 2, marginRight: 12, marginBottom: 8,
                                         ...({ boxShadow: '0 0 26px rgba(108,200,255,0.22), 0 0 30px rgba(240,123,208,0.18)' } as object) }}>
                  <View style={{ flex: 1, borderRadius: 46, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center' }}>{face}</View>
                </LinearGradient>
              ) : (
                <View key={b} accessibilityLabel={`${b} not reached yet`}
                      style={{ width: 96, height: 96, borderRadius: 48, marginRight: 12, marginBottom: 8, alignItems: 'center', justifyContent: 'center',
                               borderWidth: 1, borderColor: colors.hairline }}>
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
