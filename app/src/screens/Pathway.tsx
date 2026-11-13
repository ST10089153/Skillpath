import React, { useCallback, useEffect, useState } from 'react';
import { Linking, Platform, Text, View } from 'react-native';

import { api, moduleContent, ModuleContent, ModuleLibrary, Progress, SkillInfo } from '../api';
import { MilestoneRows, RouteStops, Stop } from '../route';
import { Body, Button, Difficulty, ErrorText, Eyebrow, Grid, Hero, Loading, Panel, Screen, colors, styles, useWide } from '../ui';

const MODULES_PER_MILESTONE = 3; // mirrors skillpath/config.py (display only)

export default function Pathway({ userId, onGoToNextSkill }: { userId: string; onGoToNextSkill: () => void }) {
  const wide = useWide();
  const [prog, setProg] = useState<Progress | null>(null);
  const [lib, setLib] = useState<ModuleLibrary | null>(null);
  const [info, setInfo] = useState<SkillInfo | null>(null);
  const [flash, setFlash] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.progress(userId).then(setProg).catch((e) => setError(e.message));
    api.modules().then(setLib).catch(() => setLib(null));
  }, [userId]);
  useEffect(load, [load]);
  useEffect(() => {
    if (prog?.skill) api.skill(prog.skill).then(setInfo).catch(() => setInfo(null));
  }, [prog?.skill]);

  async function report(moduleId: string, passed: boolean) {
    setBusy(true);
    setError('');
    try {
      const r = await api.result(userId, moduleId, passed);
      setProg(r.progress);
      setFlash(r.message || (passed ? 'Step done. On to the next one.' : 'Thanks for telling us. Try this step again when you are ready.'));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!prog) return <Screen>{error ? <ErrorText error={error} /> : <Loading />}</Screen>;
  if (prog.status !== 'adopted') {
    return (
      <Screen>
        <Hero eyebrow="No pathway yet" title="Your pathway will appear here">
          <Body muted>Accept a recommended skill and its six steps will be laid out on this screen.</Body>
        </Hero>
        <View style={wide ? { maxWidth: 420 } : undefined}><Button label="See my next skill" onPress={onGoToNextSkill} /></View>
      </Screen>
    );
  }

  const skillName = info?.label ?? prog.skill;
  const content = (i: number) => moduleContent(lib, skillName, i, info?.esco_url ?? '', info?.how_to_show ?? '');
  const hereIndex = prog.modules.findIndex((m) => m.module_id === prog.current_module?.module_id);
  const stopFor = (withDetail: boolean) => prog.modules.map((m, i): Stop => {
    const c = content(i);
    const here = i === hereIndex;
    const difficulty = here && prog.current_module ? prog.current_module.difficulty : m.difficulty;
    const minutes = here && prog.current_module ? prog.current_module.minutes : m.minutes;
    const n = i + 1;
    return {
      key: m.module_id,
      number: n,
      title: c.title,
      meta: `${minutes} MIN · LEVEL ${difficulty}/5`,
      state: m.done ? 'done' : here ? 'here' : 'next',
      interchange: n % MODULES_PER_MILESTONE === 0 ? `Milestone MS${n / MODULES_PER_MILESTONE}` : undefined,
      children: here && withDetail ? (
        <View style={{ marginTop: 6 }}>
          <StepDetail c={c} first={i === 0} info={info} difficulty={difficulty} busy={busy}
                      onDone={() => report(m.module_id, true)} onStruggle={() => report(m.module_id, false)} />
        </View>
      ) : undefined,
    };
  });
  const totalMinutes = prog.modules.reduce((t, m) => t + m.minutes, 0);
  const readout = `${prog.modules_completed} OF ${prog.total_modules} STEPS DONE · ABOUT ${totalMinutes} MIN IN TOTAL`;
  const flashBanner = flash !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{flash}</Body></View>;
  const doneBanner = prog.completed && (
    <View style={[styles.banner, { marginTop: 18 }]}>
      <Body style={{ marginBottom: 0 }}>You've completed this pathway. Well done.</Body>
    </View>
  );

  if (wide) {
    const cur = hereIndex >= 0 ? prog.modules[hereIndex] : null;
    const curDifficulty = prog.current_module?.difficulty ?? cur?.difficulty ?? 1;
    const curMinutes = prog.current_module?.minutes ?? cur?.minutes ?? 6;
    return (
      <Screen>
        <Hero eyebrow={`YOUR PATHWAY · ${skillName.toUpperCase()}`} title={prog.completed ? 'Pathway complete' : 'Six steps'}>
          <Text style={[styles.numeric, { fontSize: 14, color: colors.muted }]}>{readout}</Text>
        </Hero>
        {flashBanner}
        <ErrorText error={error} />
        {/* Course layout: the route of all six steps on the left, the step you are on in full on the right */}
        <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
          <View style={[{ width: 380 }, Platform.OS === 'web' ? ({ position: 'sticky', top: 8 } as object) : null]}>
            <Panel label="The route" right={`${prog.modules_completed} / ${prog.total_modules}`}>
              <RouteStops stops={stopFor(false)} />
            </Panel>
          </View>
          <View style={{ width: 24 }} />
          <View style={{ flex: 1, minWidth: 0 }}>
            {cur ? (
              <Panel style={{ padding: 40 }}>
                <Eyebrow color={colors.here}>{`STEP ${String(hereIndex + 1).padStart(2, '0')} OF ${prog.total_modules} · ${curMinutes} MIN · YOU ARE HERE`}</Eyebrow>
                <Text style={[styles.title, styles.titleWide, { fontSize: 60, lineHeight: 60, marginBottom: 14 }]} accessibilityRole="header">
                  {content(hereIndex).title}
                </Text>
                <StepDetail c={content(hereIndex)} first={hereIndex === 0} info={info} difficulty={curDifficulty} busy={busy} large
                            onDone={() => report(cur.module_id, true)} onStruggle={() => report(cur.module_id, false)} />
              </Panel>
            ) : doneBanner}
            <Grid cols={2} style={{ marginTop: 20 }}>
              {info?.how_to_show ? (
                <Panel label="At the end, show it by">
                  <Body style={{ marginBottom: 0 }}>{info.how_to_show}</Body>
                </Panel>
              ) : null}
              <Panel label="Milestones">
                <MilestoneRows total={prog.total_modules} done={prog.modules_completed} reached={prog.milestones} per={MODULES_PER_MILESTONE} />
              </Panel>
            </Grid>
            <Body muted style={{ marginTop: 16 }}>Mark a step done when you finish it. If a step feels hard twice in a row,
              SkillPath adds an easier one that builds the same skill. Each step is one level harder at most.</Body>
          </View>
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <Hero eyebrow={`YOUR PATHWAY · ${skillName.toUpperCase()}`} title={prog.completed ? 'Pathway complete' : 'Six steps'}>
        <Text style={[styles.numeric, { fontSize: 13, color: colors.muted }]}>{readout}</Text>
      </Hero>
      {flashBanner}
      <ErrorText error={error} />
      <View style={{ marginTop: 10 }}><RouteStops stops={stopFor(true)} /></View>
      {doneBanner}
    </Screen>
  );
}

/** The step you are on: difficulty, what to do, the free resource and the two answers. */
function StepDetail({ c, first, info, difficulty, busy, large, onDone, onStruggle }: {
  c: ModuleContent; first: boolean; info: SkillInfo | null; difficulty: number; busy: boolean; large?: boolean;
  onDone: () => void; onStruggle: () => void;
}) {
  const done = <Button label="I completed this" icon="checkmark" disabled={busy} onPress={onDone} />;
  const struggled = <Button label="I struggled with this" icon="refresh" variant="tonal" disabled={busy} onPress={onStruggle} />;
  return (
    <>
      <Difficulty level={difficulty} />
      <Body style={{ marginTop: 10 }}>{c.description}</Body>
      {first && info?.description ? (
        <View style={{ borderLeftWidth: 3, borderLeftColor: colors.track, paddingLeft: 12, marginVertical: 6 }}>
          <Text style={[styles.numeric, { fontSize: 12, color: colors.faint }]}>WHAT IT MEANS</Text>
          <Body style={{ marginBottom: 0 }}>{info.description}</Body>
        </View>
      ) : null}
      {c.resource_url !== '' && (
        <View style={large ? { maxWidth: 520 } : undefined}>
          <Button label={c.resource_label} icon="open-outline" variant="secondary" hint="Opens an external website"
                  onPress={() => Linking.openURL(c.resource_url)} />
        </View>
      )}
      {large ? <View style={{ marginTop: 14 }}><Grid cols={2} gap={12}>{done}{struggled}</Grid></View> : <>{done}{struggled}</>}
    </>
  );
}
