import React, { useCallback, useEffect, useState } from 'react';
import { Linking, Text, View } from 'react-native';

import { api, moduleContent, ModuleLibrary, Progress, SkillInfo } from '../api';
import { RouteStops, Stop } from '../route';
import { Body, Button, Difficulty, ErrorText, Hero, Loading, Screen, colors, styles } from '../ui';

const MODULES_PER_MILESTONE = 3; // mirrors skillpath/config.py (display only)

export default function Pathway({ userId, onGoToNextSkill }: { userId: string; onGoToNextSkill: () => void }) {
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
      setFlash(r.message || (passed ? 'Stop passed. On to the next one.' : 'Thanks for telling us. Try this stop again when you are ready.'));
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
        <Hero eyebrow="No line yet" title="Your route will appear here">
          <Body muted>Accept a recommended skill and its six stops will be laid out on this screen.</Body>
        </Hero>
        <Button label="See my next stop" onPress={onGoToNextSkill} />
      </Screen>
    );
  }

  const skillName = info?.label ?? prog.skill;
  const stops: Stop[] = prog.modules.map((m, i) => {
    const c = moduleContent(lib, skillName, i, info?.esco_url ?? '', info?.how_to_show ?? '');
    const here = prog.current_module?.module_id === m.module_id;
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
      children: here ? (
        <View style={{ marginTop: 6 }}>
          <Difficulty level={difficulty} />
          <Body style={{ marginTop: 10 }}>{c.description}</Body>
          {i === 0 && info?.description ? (
            <View style={{ borderLeftWidth: 3, borderLeftColor: colors.track, paddingLeft: 12, marginVertical: 6 }}>
              <Text style={[styles.numeric, { fontSize: 12, color: colors.faint }]}>WHAT IT MEANS</Text>
              <Body style={{ marginBottom: 0 }}>{info.description}</Body>
            </View>
          ) : null}
          {c.resource_url !== '' && (
            <Button label={c.resource_label} icon="open-outline" variant="secondary" hint="Opens an external website"
                    onPress={() => Linking.openURL(c.resource_url)} />
          )}
          <Button label="I completed this" icon="checkmark" disabled={busy} onPress={() => report(m.module_id, true)} />
          <Button label="I struggled with this" icon="refresh" variant="tonal" disabled={busy} onPress={() => report(m.module_id, false)} />
        </View>
      ) : undefined,
    };
  });

  return (
    <Screen>
      <Hero eyebrow={`${skillName.toUpperCase()} LINE`} title={prog.completed ? 'End of the line' : 'Your route'}>
        <Text style={[styles.numeric, { fontSize: 13, color: colors.muted }]}>
          {`${prog.modules_completed} OF ${prog.total_modules} STOPS PASSED · ABOUT ${prog.modules.reduce((t, m) => t + m.minutes, 0)} MIN IN TOTAL`}
        </Text>
      </Hero>
      {flash !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{flash}</Body></View>}
      <ErrorText error={error} />
      <View style={{ marginTop: 10 }}><RouteStops stops={stops} /></View>
      {prog.completed && (
        <View style={[styles.banner, { marginTop: 18 }]}>
          <Body style={{ marginBottom: 0 }}>You've reached the end of this line. Well done.</Body>
        </View>
      )}
    </Screen>
  );
}
