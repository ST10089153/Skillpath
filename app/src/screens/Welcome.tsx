import React, { useState } from 'react';
import { Text } from 'react-native';

import { api } from '../api';
import { Body, Button, Card, Checkbox, DISCLAIMER, ErrorText, Screen, Title, styles } from '../ui';

export default function Welcome({ onDone }: { onDone: (userId: string) => void }) {
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

  return (
    <Screen>
      <Title>Welcome to SkillPath</Title>
      <Body>
        SkillPath looks at the skills you already have (you can upload your CV or pick them yourself),
        shows what is missing for jobs close to your profile, and suggests the one skill to start with. You then
        get six short steps (5 to 10 minutes each) using free learning resources, with milestones to mark your
        progress.
      </Body>

      <Card>
        <Text style={styles.h2}>What we store</Text>
        <Body>• A random ID (like U3F9A1C). We never ask for your name, email or phone number.</Body>
        <Body>• The skills you select, your self-rating, and your progress through the lessons.</Body>
        <Body>• If you upload a CV, it is read once by SkillPath's own built-in AI to suggest skills. It is never sent to outside AI services and is not saved.</Body>
        <Body>• When you use the app (for example, finishing a lesson), so we can study how SkillPath works.</Body>
        <Body>Your data stays on the research computer, and no tracking or analytics services are used. You can view or delete your data at any time in Settings.</Body>
      </Card>

      <Card>
        <Text style={styles.h2}>Research prototype</Text>
        <Body>SkillPath is a prototype built for an Honours research study at The Independent Institute of Education. It may contain mistakes.</Body>
        <Body muted>{DISCLAIMER}</Body>
      </Card>

      <Checkbox
        checked={consent}
        onChange={setConsent}
        label="I understand what SkillPath stores and I agree to take part."
      />
      <Checkbox checked={adult} onChange={setAdult} label="I confirm that I am 18 years or older." />
      <ErrorText error={error} />
      <Button label={busy ? 'Starting…' : 'Start'} onPress={start} disabled={!consent || !adult || busy} />
    </Screen>
  );
}
