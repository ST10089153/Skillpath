import React, { useCallback, useEffect, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { api, Recommendation, SkillInfo } from '../api';
import { Body, Button, Card, ErrorText, Loading, Screen, Title, colors, styles } from '../ui';

export default function NextSkill({ userId, onAdopted, onEditProfile }: {
  userId: string; onAdopted: () => void; onEditProfile: () => void;
}) {
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [info, setInfo] = useState<SkillInfo | null>(null);
  const [why, setWhy] = useState(false);
  const [showAlts, setShowAlts] = useState(false);
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setError('');
    api.recommendation(userId).then(setRec).catch((e) => setError(e.message));
  }, [userId]);

  useEffect(load, [load]);
  useEffect(() => {
    if (rec?.recommended_skill) api.skill(rec.recommended_skill).then(setInfo).catch(() => setInfo(null));
  }, [rec?.recommended_skill]);

  async function run(fn: () => Promise<unknown>, after?: () => void) {
    setBusy(true);
    setError('');
    try {
      await fn();
      after?.();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!rec) return <Screen>{error ? <ErrorText error={error} /> : <Loading />}</Screen>;

  if (!rec.recommended_skill) {
    return (
      <Screen>
        <Title>Your next skill</Title>
        <Card><Body>{rec.explanation}</Body></Card>
        <Button label="Edit my skills" onPress={onEditProfile} />
      </Screen>
    );
  }

  return (
    <Screen>
      <Title>Your next skill</Title>
      <Card style={{ borderColor: colors.primary, borderWidth: 2 }}>
        <Text style={[styles.small, { textTransform: 'uppercase', letterSpacing: 1 }]}>Recommended for you</Text>
        <Text style={{ fontSize: 32, fontWeight: '800', color: colors.text, marginVertical: 8 }} accessibilityRole="header">
          {rec.recommended_skill}
        </Text>
        {info?.description ? <Body>{info.description}</Body> : null}
        {info && info.occupations.length > 0 && (
          <Body muted>Asked for by: {info.occupations.join(', ')}</Body>
        )}
        <Body muted>Six short steps, 5 to 10 minutes each, using free resources.</Body>
        {rec.income_displayed !== '' && (
          <View style={{ backgroundColor: colors.accent, borderRadius: 8, padding: 10, marginTop: 4 }}>
            <Text style={styles.small}>Income information</Text>
            <Body style={{ marginBottom: 0 }}>{rec.income_displayed}</Body>
          </View>
        )}
      </Card>

      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded: why }}
        onPress={() => setWhy(!why)}
        style={[styles.card, { minHeight: 52 }]}
      >
        <Text style={styles.h2}>{why ? '▾' : '▸'} Why this skill?</Text>
        {why && (
          <View>
            <Body>{rec.explanation}</Body>
            {rec.nearest_occupations.map((o) => (
              <View key={o.occupation} style={{ marginTop: 6 }}>
                <Body style={{ fontWeight: '600', marginBottom: 2 }}>{o.occupation}</Body>
                <Body muted style={{ marginBottom: 2 }}>You have {o.skills_held} of {o.skills_total} skills</Body>
                <Text style={styles.small}>Source: {o.source || 'not recorded'}</Text>
              </View>
            ))}
          </View>
        )}
      </Pressable>

      <ErrorText error={error} />
      {note !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{note}</Body></View>}
      <Button label="Accept and start" disabled={busy} onPress={() => run(() => api.accept(userId), onAdopted)} />
      <Button label={showAlts ? 'Hide alternatives' : 'Show alternatives'} variant="secondary" onPress={() => setShowAlts(!showAlts)} />
      {showAlts && (
        <Card>
          <Text style={styles.h2}>Other good next steps</Text>
          {rec.alternatives.length === 0 && <Body muted>No alternatives for this profile.</Body>}
          {rec.alternatives.map((a) => (
            <Button key={a} label={`Choose ${a}`} variant="secondary" disabled={busy}
                    onPress={() => run(() => api.swap(userId, a), onAdopted)} />
          ))}
        </Card>
      )}
      <Button label="Not now" variant="secondary" disabled={busy}
              onPress={() => run(async () => setNote((await api.defer(userId)).message))} />
      <Button label="Edit my skills" variant="secondary" onPress={onEditProfile} />
    </Screen>
  );
}
