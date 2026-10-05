import React, { useCallback, useEffect, useState } from 'react';
import { Linking, Text, View } from 'react-native';

import { api, moduleContent, ModuleLibrary, Progress } from '../api';
import { Body, Button, Card, Difficulty, ErrorText, Loading, Screen, Title, colors, styles } from '../ui';

export default function Pathway({ userId, onGoToNextSkill }: { userId: string; onGoToNextSkill: () => void }) {
  const [prog, setProg] = useState<Progress | null>(null);
  const [lib, setLib] = useState<ModuleLibrary | null>(null);
  const [flash, setFlash] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api.progress(userId).then(setProg).catch((e) => setError(e.message));
    api.modules().then(setLib).catch(() => setLib(null));
  }, [userId]);
  useEffect(load, [load]);

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
      <Title>Pathway: {prog.skill}</Title>
      <Body muted>{prog.modules_completed} of {prog.total_modules} modules done</Body>
      {flash !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{flash}</Body></View>}
      <ErrorText error={error} />
      {prog.modules.map((m, i) => {
        const c = moduleContent(lib, prog.skill, i);
        const current = prog.current_module?.module_id === m.module_id;
        const difficulty = current && prog.current_module ? prog.current_module.difficulty : m.difficulty;
        const minutes = current && prog.current_module ? prog.current_module.minutes : m.minutes;
        return (
          <Card key={m.module_id} style={current ? { borderColor: colors.primary, borderWidth: 2 } : m.done ? { backgroundColor: colors.successBg } : undefined}>
            <Text style={styles.small}>Module {i + 1} · about {minutes} min {m.done ? '· ✓ Done' : ''}</Text>
            <Text style={[styles.h2, { marginTop: 4 }]}>{c.title}</Text>
            <Difficulty level={difficulty} />
            {(current || m.done) && <Body style={{ marginTop: 8 }}>{c.description}</Body>}
            {current && c.resource_url !== '' && (
              <Button label="Open resource" variant="secondary" onPress={() => Linking.openURL(c.resource_url)} />
            )}
            {current && (
              <View style={{ marginTop: 4 }}>
                <Button label="I completed this" disabled={busy} onPress={() => report(m.module_id, true)} />
                <Button label="I struggled with this" variant="secondary" disabled={busy} onPress={() => report(m.module_id, false)} />
              </View>
            )}
          </Card>
        );
      })}
      {prog.completed && <Card style={{ backgroundColor: colors.successBg }}><Body>You've finished this pathway. Well done!</Body></Card>}
    </Screen>
  );
}
