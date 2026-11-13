import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, Progress } from '../api';
import { MilestoneRows, RouteStrip } from '../route';
import { Body, Columns, EmptyState, ErrorText, Loading, ProgressBar, Screen, SectionLabel, Title, colors, fonts, styles, useWide } from '../ui';

const MODULES_PER_MILESTONE = 3; // mirrors skillpath/config.py (display only)

export default function ProgressScreen({ userId }: { userId: string }) {
  const wide = useWide();
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
  const nextMs = prog.completed ? 0 : (Math.floor(prog.modules_completed / MODULES_PER_MILESTONE) + 1) * MODULES_PER_MILESTONE;
  const badges = Array.from({ length: Math.floor(total / MODULES_PER_MILESTONE) }, (_, i) => `MS${i + 1}`);

  return (
    <Screen>
      <Title>Your progress</Title>
      {prog.status !== 'adopted' ? (
        <EmptyState icon="trophy-outline" title="No pathway yet">
          <Body muted>Accept a recommended skill under Next skill and your steps and milestones will show here.</Body>
        </EmptyState>
      ) : (
        (() => {
          const current = (<>
          <View>
            <SectionLabel>Current pathway</SectionLabel>
            <Text style={styles.h2}>{labels[prog.skill] ?? prog.skill}</Text>
            <ProgressBar value={prog.modules_completed} total={total} />
            {wide ? (
              <View style={{ marginTop: 14, marginBottom: 6 }}>
                <RouteStrip total={total} done={prog.modules_completed}
                            here={prog.completed ? null : (prog.current_module?.index ?? prog.modules_completed + 1)}
                            interchanges={Array.from({ length: Math.floor(total / MODULES_PER_MILESTONE) }, (_, i) => (i + 1) * MODULES_PER_MILESTONE)} />
              </View>
            ) : null}
            <Body muted style={styles.numeric}>{prog.modules_completed} of {total} steps ({pct}%)</Body>
            {nextMs ? <Body>{`${nextMs - prog.modules_completed} short ${nextMs - prog.modules_completed === 1 ? 'step' : 'steps'} to milestone MS${nextMs / MODULES_PER_MILESTONE}. A 5 to 10 minute session gets you closer.`}</Body> : null}
          </View>

          </>);
          const milestones = (<>
          <SectionLabel>Milestones</SectionLabel>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 12 }}>
            {badges.map((b) => {
              const got = prog.milestones.includes(b);
              const face = (
                <>
                  <Text style={{ fontSize: 24, fontFamily: fonts.display, color: got ? colors.primary : colors.muted }}>{b}</Text>
                  <Text style={{ fontSize: 11, letterSpacing: 1.2, textTransform: 'uppercase', fontFamily: fonts.mono, color: got ? colors.primary : colors.faint }}>{got ? 'Reached' : `${MODULES_PER_MILESTONE} steps`}</Text>
                </>
              );
              // Milestones are interchanges on the route: a capsule marker, filled in the route colour once reached.
              return (
                <View key={b} accessibilityLabel={`${b} ${got ? 'reached' : 'not reached yet'}`}
                      style={{ alignItems: 'center', marginRight: 28, marginBottom: 8 }}>
                  <View style={{ width: 44, height: 24, borderRadius: 12, borderWidth: 4, borderColor: got ? colors.text : colors.track,
                                 backgroundColor: got ? colors.line : colors.bg, marginBottom: 10 }} />
                  {face}
                </View>
              );
            })}
          </View>

          </>);
          const status = (<>
          {prog.message !== '' && (
            <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{prog.message}</Body></View>
          )}
          {prog.difficulty !== null && <Body muted>Current difficulty: level {prog.difficulty} of 5</Body>}
          </>);
          return wide
            ? <Columns main={<>{current}{status}</>} side={<>
                <SectionLabel>Milestones</SectionLabel>
                <MilestoneRows total={total} done={prog.modules_completed} reached={prog.milestones} per={MODULES_PER_MILESTONE} />
              </>} />
            : <>{current}{milestones}{status}</>;
        })()
      )}
    </Screen>
  );
}
