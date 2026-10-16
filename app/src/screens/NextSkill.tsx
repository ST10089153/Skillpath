import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, Recommendation, SkillInfo } from '../api';
import { Branches, ofoCode } from '../route';
import { Body, Button, ErrorText, Hero, Loading, Screen, SectionLabel, TextLink, TicketRow, colors, styles } from '../ui';

export default function NextSkill({ userId, onAdopted, onEditProfile }: {
  userId: string; onAdopted: () => void; onEditProfile: () => void;
}) {
  const [rec, setRec] = useState<Recommendation | null>(null);
  const [info, setInfo] = useState<SkillInfo | null>(null);
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
        <Hero eyebrow="No stop found" title="We need more to go on">
          <Body>{rec.explanation}</Body>
        </Hero>
        <Button label="Edit my skills" onPress={onEditProfile} />
      </Screen>
    );
  }

  const name = info?.label ?? label(rec.recommended_skill);
  const branches = rec.nearest_occupations.map((o) => ({
    key: o.occupation,
    title: o.occupation,
    code: ofoCode(o.source),
    held: o.skills_held,
    total: o.skills_total,
    missing: o.skills_missing.map((m) => ({ label: label(m), isThis: m === rec.recommended_skill })),
    source: o.source ? `Source: ${o.source}` : 'Source: not recorded',
  }));

  return (
    <Screen>
      <Hero eyebrow="NEXT STOP · RECOMMENDED FOR YOU" title={name}>
        {info?.description ? <Body muted>{info.description}</Body> : null}
      </Hero>

      <View style={{ borderTopWidth: 1, borderTopColor: colors.hairline, marginBottom: 6 }}>
        {info?.category ? <TicketRow label="Line" value={info.category} /> : null}
        <TicketRow label="Stops" value="6 short steps · 5 to 10 min each · free resources" />
        {info?.how_to_show ? <TicketRow label="Show it by" value={info.how_to_show} /> : null}
        {info?.demand_evidence ? <TicketRow label="Demand" value={info.demand_evidence} /> : null}
        {rec.income_displayed !== '' ? <TicketRow label="Income" value={rec.income_displayed} /> : null}
      </View>

      <SectionLabel right={`${branches.length} nearest jobs`}>What's missing?</SectionLabel>
      <Text style={[styles.numeric, { fontSize: 12, color: colors.faint, marginBottom: 4 }]}>
        {`THIS STOP LEADS TO ${branches.length === 1 ? 'THIS JOB' : 'THESE JOBS'}`}
      </Text>
      <Branches branches={branches} />

      <SectionLabel>Why this skill?</SectionLabel>
      <Body>{rec.explanation}</Body>

      <ErrorText error={error} />
      {note !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{note}</Body></View>}
      <View style={{ marginTop: 8 }}>
        <Button label="Accept and start" disabled={busy} onPress={() => run(() => api.accept(userId), onAdopted)} />
      </View>

      {rec.alternatives.length > 0 && (
        <>
          <SectionLabel right={String(rec.alternatives.length)}>Other routes</SectionLabel>
          {rec.alternatives.map((a) => (
            <Button key={a} label={`Choose ${label(a)}`} variant="tonal" disabled={busy}
                    onPress={() => run(() => api.swap(userId, a), onAdopted)} />
          ))}
        </>
      )}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 10 }}>
        <View style={{ marginRight: 24 }}>
          <TextLink label="Not now" onPress={() => run(async () => setNote((await api.defer(userId)).message))} />
        </View>
        <TextLink label="Edit my skills" onPress={onEditProfile} />
      </View>
    </Screen>
  );
}
