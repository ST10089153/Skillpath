import React, { useCallback, useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, Recommendation, SkillInfo } from '../api';
import { Branches, ofoCode } from '../route';
import { Body, Button, ErrorText, Eyebrow, Grid, Hero, Loading, Panel, ProgressBar, Screen, SectionLabel, TextLink, TicketRow, colors, fonts, styles, useWide } from '../ui';

export default function NextSkill({ userId, onAdopted, onEditProfile }: {
  userId: string; onAdopted: () => void; onEditProfile: () => void;
}) {
  const wide = useWide();
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
        <Hero eyebrow="No recommendation yet" title="We need more to go on">
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

  const facts = (
    <View style={{ borderTopWidth: 1, borderTopColor: colors.hairline, marginBottom: 6 }}>
      {info?.category ? <TicketRow label="Category" value={info.category} /> : null}
      <TicketRow label="Steps" value="6 short steps · 5 to 10 min each · free resources" />
      {info?.how_to_show ? <TicketRow label="Show it by" value={info.how_to_show} /> : null}
      {info?.demand_evidence ? <TicketRow label="Demand" value={info.demand_evidence} /> : null}
      {rec.income_displayed !== '' ? <TicketRow label="Income" value={rec.income_displayed} /> : null}
    </View>
  );
  const missing = (
    <>
      <SectionLabel right={`${branches.length} nearest jobs`}>What's missing?</SectionLabel>
      <Text style={[styles.numeric, { fontSize: 12, color: colors.faint, marginBottom: 4 }]}>
        {`THIS SKILL LEADS TO ${branches.length === 1 ? 'THIS JOB' : 'THESE JOBS'}`}
      </Text>
      <Branches branches={branches} />
    </>
  );
  const why = (
    <>
      <SectionLabel>Why this skill?</SectionLabel>
      <Body>{rec.explanation}</Body>
    </>
  );
  const actions = (
    <>
      <ErrorText error={error} />
      {note !== '' && <View style={styles.banner}><Body style={{ marginBottom: 0 }}>{note}</Body></View>}
      <View style={{ marginTop: 8 }}>
        <Button label="Accept and start" disabled={busy} onPress={() => run(() => api.accept(userId), onAdopted)} />
      </View>

      {rec.alternatives.length > 0 && (
        <>
          <SectionLabel right={String(rec.alternatives.length)}>Alternatives</SectionLabel>
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
    </>
  );

  if (wide) {
    return (
      <Screen>
        {/* The decision: what the skill is, with the choice right beside it */}
        <Panel style={{ padding: 40 }}>
          <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
            <View style={{ flex: 1, minWidth: 0, paddingRight: 48 }}>
              <Eyebrow>YOUR NEXT SKILL · RECOMMENDED FOR YOU</Eyebrow>
              <Text style={[styles.heroTitle, styles.heroTitleWide]} accessibilityRole="header">{name}</Text>
              {info?.description ? <Body muted style={{ fontSize: 20, lineHeight: 30 }}>{info.description}</Body> : null}
              <Text style={[styles.numeric, { fontSize: 13, color: colors.muted, marginTop: 8 }]}>
                {`${info?.category ? `${info.category.toUpperCase()} · ` : ''}6 SHORT STEPS · 5 TO 10 MIN EACH · FREE RESOURCES`}
              </Text>
            </View>
            <View style={{ width: 360 }}>
              <Button label="Accept and start" disabled={busy} onPress={() => run(() => api.accept(userId), onAdopted)} />
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 6 }}>
                <View style={{ marginRight: 24 }}>
                  <TextLink label="Not now" onPress={() => run(async () => setNote((await api.defer(userId)).message))} />
                </View>
                <TextLink label="Edit my skills" onPress={onEditProfile} />
              </View>
              <ErrorText error={error} />
              {note !== '' && <View style={[styles.banner, { marginTop: 8 }]}><Body style={{ marginBottom: 0 }}>{note}</Body></View>}
            </View>
          </View>
        </Panel>

        {/* What it leads to: one card per nearest job, how close you are and what is still missing */}
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 36, marginBottom: 14 }}>
          <Text style={[styles.h2, { fontSize: 34, lineHeight: 36, marginBottom: 0 }]}>What's missing?</Text>
          <Text style={[styles.sectionLabel, { fontSize: 13, alignSelf: 'flex-end' }]}>
            {`THIS SKILL LEADS TO ${branches.length} NEAREST ${branches.length === 1 ? 'JOB' : 'JOBS'}`}
          </Text>
        </View>
        <Grid cols={Math.min(3, Math.max(1, branches.length))}>
          {branches.map((b) => <JobCard key={b.key} job={b} />)}
        </Grid>

        <Grid cols={2} style={{ marginTop: 20 }}>
          <Panel label="Why this skill?">
            <Body>{rec.explanation}</Body>
          </Panel>
          <Panel label="The facts">
            <View>
              {info?.how_to_show ? <TicketRow label="Show it by" value={info.how_to_show} /> : null}
              {info?.demand_evidence ? <TicketRow label="Demand" value={info.demand_evidence} /> : null}
              {rec.income_displayed !== '' ? <TicketRow label="Income" value={rec.income_displayed} last /> : null}
            </View>
          </Panel>
        </Grid>

        {rec.alternatives.length > 0 && (
          <Panel label="Or choose another skill" right={String(rec.alternatives.length)} style={{ marginTop: 20 }}>
            <Grid cols={3} gap={12}>
              {rec.alternatives.map((a) => (
                <Button key={a} label={`Choose ${label(a)}`} variant="tonal" disabled={busy}
                        onPress={() => run(() => api.swap(userId, a), onAdopted)} />
              ))}
            </Grid>
          </Panel>
        )}
      </Screen>
    );
  }

  return (
    <Screen>
      <Hero eyebrow="YOUR NEXT SKILL · RECOMMENDED FOR YOU" title={name}>
        {info?.description ? <Body muted>{info.description}</Body> : null}
      </Hero>
      {facts}{missing}{why}{actions}
    </Screen>
  );
}

type Job = { key: string; title: string; code: string; held: number; total: number;
             missing: { label: string; isThis: boolean }[]; source: string };

/** Wide screens: one nearest job, how much of it you already have, and the skills still missing. */
function JobCard({ job }: { job: Job }) {
  return (
    <Panel>
      <Text style={[styles.h2, { fontSize: 30, lineHeight: 32 }]}>{job.title}</Text>
      <Text style={[styles.numeric, { fontSize: 12, color: colors.faint }]}>{job.code || 'OFO code not recorded'}</Text>
      <ProgressBar value={job.held} total={job.total} />
      <Text style={[styles.numeric, { fontSize: 13, color: colors.muted, marginBottom: 12 }]}>{`YOU HAVE ${job.held} OF ${job.total} SKILLS`}</Text>
      <Text style={[styles.sectionLabel, { marginBottom: 8 }]}>Still to learn</Text>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 8 }}>
        {job.missing.map((m) => (
          <View key={m.label} style={[styles.chip, { minHeight: 34, paddingHorizontal: 12 },
                                      m.isThis && { borderColor: colors.here, backgroundColor: colors.warnBg }]}>
            <Text style={{ fontSize: 14, fontFamily: m.isThis ? fonts.semibold : fonts.regular, color: m.isThis ? colors.here : colors.text }}>
              {m.isThis ? `${m.label} (recommended)` : m.label}
            </Text>
          </View>
        ))}
      </View>
      <Text style={styles.small}>{job.source}</Text>
    </Panel>
  );
}
