import React, { useCallback, useEffect, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { api, Recommendation, SkillInfo } from '../api';
import { Body, Button, Card, ErrorText, Hero, Loading, Pill, Screen, Title, colors, styles } from '../ui';

export default function NextSkill({ userId, onAdopted, onEditProfile }: {
  userId: string; onAdopted: () => void; onEditProfile: () => void;
}) {
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [info, setInfo] = useState<SkillInfo | null>(null);
  const [why, setWhy] = useState(false);
  const [showAlts, setShowAlts] = useState(false);
  const [gaps, setGaps] = useState(false);
  const [labels, setLabels] = useState<Record<string, string>>({});
  const label = (x: string) => labels[x] ?? x;
  useEffect(() => { api.vocabulary().then((v) => setLabels(v.labels ?? {})).catch(() => undefined); }, []);
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
      <Hero icon="compass" eyebrow="Recommended for you" title={info?.label ?? rec.recommended_skill}>
        {info?.category ? <Text style={{ color: colors.primary, fontSize: 14, fontWeight: '600', marginBottom: 6 }}>{info.category}</Text> : null}
        {info?.description ? <Text style={{ color: colors.muted, fontSize: 16, lineHeight: 23 }}>{info.description}</Text> : null}
      </Hero>
      <Card>
        {info && info.occupations.length > 0 && (
          <Body muted>Asked for by: {info.occupations.join(', ')}</Body>
        )}
        {info?.how_to_show ? <Body><Text style={{ fontWeight: '700' }}>How you will show it: </Text>{info.how_to_show}</Body> : null}
        {info?.demand_evidence ? <Body muted>Why it is in demand: {info.demand_evidence}</Body> : null}
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          <Pill icon="layers-outline" label="6 short steps" />
          <Pill icon="time-outline" label="5-10 min each" />
          <Pill icon="pricetag-outline" label="Free resources" tone="success" />
        </View>
        {rec.income_displayed !== '' && (
          <View style={{ backgroundColor: colors.warnBg, borderRadius: 6, padding: 12, marginTop: 8 }}>
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

      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded: gaps }}
        onPress={() => setGaps(!gaps)}
        style={[styles.card, { minHeight: 52 }]}
      >
        <Text style={styles.h2}>{gaps ? '▾' : '▸'} What's missing?</Text>
        {gaps && rec.nearest_occupations.map((o) => (
          <View key={o.occupation} style={{ marginTop: 8 }}>
            <Body style={{ fontWeight: '600', marginBottom: 2 }}>
              {o.occupation}: you have {o.skills_held} of {o.skills_total}
            </Body>
            <Body muted style={{ marginBottom: 2 }}>Still to learn ({o.skills_missing.length}):</Body>
            <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
              {o.skills_missing.map((m) => (m === rec.recommended_skill
                ? <Pill key={m} icon="star" tone="success" label={`${label(m)} · start here`} />
                : <Pill key={m} label={label(m)} />))}
            </View>
          </View>
        ))}
      </Pressable>

      <ErrorText error={error} />
      {note !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{note}</Body></View>}
      <Button label="Accept and start" icon="play" disabled={busy} onPress={() => run(() => api.accept(userId), onAdopted)} />
      <Button label={showAlts ? 'Hide alternatives' : 'Show alternatives'} variant="secondary" onPress={() => setShowAlts(!showAlts)} />
      {showAlts && (
        <Card>
          <Text style={styles.h2}>Other good next steps</Text>
          {rec.alternatives.length === 0 && <Body muted>No alternatives for this profile.</Body>}
          {rec.alternatives.map((a) => (
            <Button key={a} label={`Choose ${label(a)}`} variant="secondary" disabled={busy}
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
