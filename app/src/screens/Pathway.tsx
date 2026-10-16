import React, { useCallback, useEffect, useState } from 'react';
import { Linking, Text, View } from 'react-native';

import { api, moduleContent, ModuleLibrary, Progress, SkillInfo } from '../api';
import { BigNumber, Body, Button, Card, Difficulty, ErrorText, Loading, Screen, Title, colors, styles } from '../ui';

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
      setFlash(r.message || (passed ? 'Nice work. On to the next one.' : 'Thanks for letting us know. Try this step again when you are ready.'));
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
        <Title>Your pathway</Title>
        <Body>You haven't started a pathway yet.</Body>
        <Button label="See my next skill" onPress={onGoToNextSkill} />
      </Screen>
    );
  }

  return (
    <Screen>
      <Title>Pathway: {info?.label ?? prog.skill}</Title>
      <Body muted>{prog.modules_completed} of {prog.total_modules} modules done</Body>
      {flash !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{flash}</Body></View>}
      <ErrorText error={error} />
      {prog.modules.map((m, i) => {
        const c = moduleContent(lib, info?.label ?? prog.skill, i, info?.esco_url ?? '', info?.how_to_show ?? '');
        const current = prog.current_module?.module_id === m.module_id;
        const difficulty = current && prog.current_module ? prog.current_module.difficulty : m.difficulty;
        const minutes = current && prog.current_module ? prog.current_module.minutes : m.minutes;
        return (
          <Card key={m.module_id} style={current ? { borderColor: colors.primary } : m.done ? { opacity: 0.75 } : undefined}>
            <BigNumber n={i + 1} />
            <Text style={styles.small}>Module {i + 1} · about {minutes} min {m.done ? '· ✓ Done' : ''}</Text>
            <Text style={[styles.h2, { marginTop: 4 }]}>{c.title}</Text>
            <Difficulty level={difficulty} />
            {(current || m.done) && <Body style={{ marginTop: 8 }}>{c.description}</Body>}
            {i === 0 && (current || m.done) && info?.description ? (
              <View style={{ borderLeftWidth: 2, borderLeftColor: colors.primary, paddingLeft: 14, paddingVertical: 4, marginVertical: 8 }}>
                <Text style={styles.small}>What it means</Text>
                <Body style={{ marginBottom: 0 }}>{info.description}</Body>
              </View>
            ) : null}
            {(current || m.done) && c.resource_url !== '' && (
              <Button label={`${c.resource_label} ↗`} variant="secondary" hint="Opens an external website"
                      onPress={() => Linking.openURL(c.resource_url)} />
            )}
            {current && (
              <View style={{ marginTop: 4 }}>
                <Button label="I completed this" icon="checkmark-circle-outline" disabled={busy} onPress={() => report(m.module_id, true)} />
                <Button label="I struggled with this" icon="help-buoy-outline" variant="secondary" disabled={busy} onPress={() => report(m.module_id, false)} />
              </View>
            )}
          </Card>
        );
      })}
      {prog.completed && <Card style={{ borderColor: colors.primary }}><Body>You've finished this pathway. Well done.</Body></Card>}
    </Screen>
  );
}
