import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, Progress } from '../api';
import { RouteStrip } from '../route';
import { Body, EmptyState, ErrorText, Grid, Loading, Panel, ProgressBar, Screen, SectionLabel, Stat, Title, colors, fonts, styles, useWide } from '../ui';

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
  const toGo = nextMs - prog.modules_completed;
  const nudgeLine = nextMs
    ? `${toGo} short ${toGo === 1 ? 'step' : 'steps'} to milestone MS${nextMs / MODULES_PER_MILESTONE}. A 5 to 10 minute session gets you closer.`
    : '';
  const skillName = labels[prog.skill] ?? prog.skill;

  if (prog.status !== 'adopted') {
    return (
      <Screen>
        <Title>Your progress</Title>
        <EmptyState icon="trophy-outline" title="No pathway yet">
          <Body muted>Accept a recommended skill under Next skill and your steps and milestones will show here.</Body>
        </EmptyState>
      </Screen>
    );
  }

  if (wide) {
    const here = prog.completed ? null : (prog.current_module?.index ?? prog.modules_completed + 1);
    const ends = badges.map((_, i) => (i + 1) * MODULES_PER_MILESTONE);
    return (
      <Screen>
        <Title>Your progress</Title>
        <Grid cols={4}>
          <Stat label="Steps done" value={`${prog.modules_completed} / ${total}`} sub={`${pct}% of the pathway`} />
          <Stat label="Next milestone" value={nextMs ? `MS${nextMs / MODULES_PER_MILESTONE}` : 'All done'} color={colors.line}
                sub={nextMs ? `${toGo} ${toGo === 1 ? 'step' : 'steps'} to go` : 'Every milestone reached'} />
          <Stat label="Milestones" value={`${prog.milestones.length} / ${badges.length}`} sub="One every three steps" />
          <Stat label="Difficulty" value={prog.difficulty !== null ? `${prog.difficulty} / 5` : '–'} sub="Level of the current step" />
        </Grid>

        <Panel label="Current pathway" style={{ marginTop: 20, padding: 36 }}>
          <Text style={[styles.h2, { fontSize: 40, lineHeight: 42 }]}>{skillName}</Text>
          <View style={{ marginTop: 18 }}>
            <RouteStrip total={total} done={prog.modules_completed} here={here} interchanges={ends} />
          </View>
          {nudgeLine ? <Body style={{ marginTop: 6, marginBottom: 0 }}>{nudgeLine}</Body> : null}
        </Panel>

        {prog.message !== '' && (
          <View style={[styles.banner, { marginTop: 20, marginBottom: 0 }]}><Body style={{ marginBottom: 0 }}>{prog.message}</Body></View>
        )}

        <Grid cols={badges.length || 1} style={{ marginTop: 20 }}>
          {ends.map((n) => {
            const name = `MS${n / MODULES_PER_MILESTONE}`;
            const got = prog.milestones.includes(name);
            const left = n - prog.modules_completed;
            return (
              <Panel key={name} label={`Milestone ${name.slice(2)}`}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }} accessibilityLabel={`${name} ${got ? 'reached' : 'not reached yet'}`}>
                  <View style={{ width: 64, height: 34, borderRadius: 17, borderWidth: 5, marginRight: 20,
                                 borderColor: got ? colors.text : colors.track, backgroundColor: got ? colors.line : colors.bg }} />
                  <View>
                    <Text style={{ fontFamily: fonts.display, fontSize: 52, lineHeight: 52, color: got ? colors.primary : colors.text, paddingTop: 4 }}>{name}</Text>
                    <Text style={[styles.numeric, { fontSize: 13, color: got ? colors.primary : colors.faint }]}>
                      {got ? `REACHED · AFTER STEP ${n}` : `AFTER STEP ${n} · ${left} ${left === 1 ? 'STEP' : 'STEPS'} TO GO`}
                    </Text>
                  </View>
                </View>
              </Panel>
            );
          })}
        </Grid>
      </Screen>
    );
  }

  return (
    <Screen>
      <Title>Your progress</Title>
      <View>
        <SectionLabel>Current pathway</SectionLabel>
        <Text style={styles.h2}>{skillName}</Text>
        <ProgressBar value={prog.modules_completed} total={total} />
        <Body muted style={styles.numeric}>{prog.modules_completed} of {total} steps ({pct}%)</Body>
        {nudgeLine ? <Body>{nudgeLine}</Body> : null}
      </View>

      <SectionLabel>Milestones</SectionLabel>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 12 }}>
        {badges.map((b) => {
          const got = prog.milestones.includes(b);
          // Milestones are interchanges on the route: a capsule marker, filled in the route colour once reached.
          return (
            <View key={b} accessibilityLabel={`${b} ${got ? 'reached' : 'not reached yet'}`}
                  style={{ alignItems: 'center', marginRight: 28, marginBottom: 8 }}>
              <View style={{ width: 44, height: 24, borderRadius: 12, borderWidth: 4, borderColor: got ? colors.text : colors.track,
                             backgroundColor: got ? colors.line : colors.bg, marginBottom: 10 }} />
              <Text style={{ fontSize: 24, fontFamily: fonts.display, color: got ? colors.primary : colors.muted }}>{b}</Text>
              <Text style={{ fontSize: 11, letterSpacing: 1.2, textTransform: 'uppercase', fontFamily: fonts.mono, color: got ? colors.primary : colors.faint }}>{got ? 'Reached' : `${MODULES_PER_MILESTONE} steps`}</Text>
            </View>
          );
        })}
      </View>

      {prog.message !== '' && (
        <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{prog.message}</Body></View>
      )}
      {prog.difficulty !== null && <Body muted>Current difficulty: level {prog.difficulty} of 5</Body>}
    </Screen>
  );
}
