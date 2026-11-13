import React, { useState } from 'react';
import { Text, View } from 'react-native';

import { api } from '../api';
import { DEMO, DEMO_PRIVACY } from '../demo';
import { Body, Button, Checkbox, DISCLAIMER, ErrorText, Grid, Hero, Panel, Screen, SectionLabel, colors, fonts, styles, useWide } from '../ui';

const STORED = [
  'A random ID (like U3F9A1C). We never ask for your name, email or phone number.',
  'The skills you select, your self-rating, and your progress through the lessons.',
  "If you upload a CV, it is read once by SkillPath's own built-in AI to suggest skills. It is never sent to outside AI services and is not saved.",
  DEMO
    ? 'What you do in the app (for example, finishing a lesson), so the demo works as it does in the study.'
    : 'When you use the app (for example, finishing a lesson), so we can study how SkillPath works.',
];
const PRIVACY = DEMO ? DEMO_PRIVACY
  : 'Your data stays on the research computer, and no tracking or analytics services are used. You can view or delete your data at any time in Settings.';
const INTRO = 'SkillPath looks at the skills you already have (you can upload your CV or pick them yourself), shows what is '
  + 'missing for jobs close to your profile, and suggests the one skill to start with. You then get six short steps (5 to 10 '
  + 'minutes each) using free learning resources, with milestones to mark your progress.';
const ABOUT = 'SkillPath is a prototype built for an Honours research study at The Independent Institute of Education. It may contain mistakes.';

// Wide screens: the three parts of SkillPath, in the order the user meets them.
const HOW = [
  { n: '01', title: 'Tell us your skills', text: "Upload your CV or pick the skills you already have. SkillPath's own AI suggests skills from your CV and you confirm them." },
  { n: '02', title: 'Get your next skill', text: 'One skill that brings you closest to jobs near your profile, with what is missing for each job and why.' },
  { n: '03', title: 'Six short steps', text: 'Steps of 5 to 10 minutes with free learning resources, and a milestone every three steps.' },
];

export default function Welcome({ onDone, notice = '' }: { onDone: (userId: string) => void; notice?: string }) {
  const wide = useWide();
  const [consent, setConsent] = useState(false);
  const [adult, setAdult] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function start() {
    setBusy(true);
    setError('');
    try {
      const u = await api.createUser();
      onDone(u.user_id);
    } catch (e) {
      setError(`Could not connect to SkillPath. ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  const banner = notice !== '' && (
    <View style={[styles.banner, { marginTop: 4 }]} accessibilityRole="alert">
      <Body style={{ marginBottom: 0 }}>{notice}</Body>
    </View>
  );
  const agree = (
    <>
      <Checkbox
        checked={consent}
        onChange={setConsent}
        label={DEMO ? 'I understand what this demo stores.' : 'I understand what SkillPath stores and I agree to take part.'}
      />
      <Checkbox checked={adult} onChange={setAdult} label="I confirm that I am 18 years or older." />
      <ErrorText error={error} />
      <Button label={busy ? 'Starting…' : 'Start'} icon="arrow-forward" onPress={start} disabled={!consent || !adult || busy} />
    </>
  );

  if (wide) {
    return (
      <Screen>
        {banner}
        <Hero eyebrow="RESEARCH PROTOTYPE" title="Find your next skill">
          <Text style={{ color: colors.muted, fontSize: 20, lineHeight: 31, maxWidth: 760 }}>{INTRO}</Text>
        </Hero>
        <Grid cols={3}>
          {HOW.map((h) => (
            <Panel key={h.n}>
              <Text style={{ fontFamily: fonts.display, fontSize: 48, lineHeight: 48, color: colors.line, paddingTop: 4 }}>{h.n}</Text>
              <Text style={[styles.h2, { marginTop: 10 }]}>{h.title}</Text>
              <Body muted style={{ marginBottom: 0 }}>{h.text}</Body>
            </Panel>
          ))}
        </Grid>
        <Panel label="Before you start" style={{ marginTop: 20 }}>
          <View style={{ flexDirection: 'row', alignItems: 'flex-start' }}>
            <View style={{ flex: 6, minWidth: 0 }}>
              <Text style={[styles.h2, { marginBottom: 12 }]}>What we store</Text>
              {STORED.map((t) => <Body key={t}>{`• ${t}`}</Body>)}
              <Body muted>{PRIVACY}</Body>
            </View>
            <View style={{ width: 56 }} />
            <View style={{ flex: 5, minWidth: 0 }}>
              <Text style={[styles.h2, { marginBottom: 6 }]}>Your consent</Text>
              {agree}
            </View>
          </View>
        </Panel>
        <Text style={[styles.small, { marginTop: 18, maxWidth: 900 }]}>{ABOUT} {DISCLAIMER}</Text>
      </Screen>
    );
  }

  return (
    <Screen>
      {banner}
      <Hero eyebrow="RESEARCH PROTOTYPE" title="Find your next skill">
        <Text style={{ color: colors.muted, fontSize: 16, lineHeight: 23 }}>{INTRO}</Text>
      </Hero>

      <SectionLabel>What we store</SectionLabel>
      {STORED.map((t) => <Body key={t}>{`• ${t}`}</Body>)}
      <Body>{PRIVACY}</Body>

      <SectionLabel>Research prototype</SectionLabel>
      <Body>{ABOUT}</Body>
      <Body muted>{DISCLAIMER}</Body>
      <View style={{ height: 12 }} />
      {agree}
    </Screen>
  );
}
