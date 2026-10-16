import { Ionicons } from '@expo/vector-icons';
import React, { useEffect, useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { api, Progress } from '../api';
import { Body, Button, Card, Hero, Loading, Pill, ProgressBar, Screen, SectionLabel, colors, fonts, styles } from '../ui';

type Go = 'next' | 'pathway' | 'progress' | 'settings';

function Action({ icon, label, onPress }: { icon: keyof typeof Ionicons.glyphMap; label: string; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={label} onPress={onPress}
               style={({ pressed }) => [styles.card, { flexBasis: '47%', flexGrow: 1, marginRight: 8, alignItems: 'flex-start', opacity: pressed ? 0.85 : 1 }]}>
      <Ionicons name={icon} size={22} color={colors.primary} style={{ marginBottom: 14 }} />
      <Text style={{ fontSize: 15, fontFamily: fonts.semibold, color: colors.text }}>{label}</Text>
      <Ionicons name="arrow-forward" size={16} color={colors.faint} style={{ marginTop: 8 }} />
    </Pressable>
  );
}

export default function Home({ userId, go, onEditProfile }: { userId: string; go: (t: Go) => void; onEditProfile: () => void }) {
  const [skills, setSkills] = useState<string[] | null>(null);
  const [prog, setProg] = useState<Progress | null>(null);
  const [labels, setLabels] = useState<Record<string, string>>({});

  useEffect(() => {
    api.myData(userId).then((d) => {
      const u = (d as { user?: { current_skills?: string } }).user;
      setSkills((u?.current_skills || '').split(';').map((s) => s.trim()).filter(Boolean));
    }).catch(() => setSkills([]));
    api.progress(userId).then(setProg).catch(() => setProg(null));
    api.vocabulary().then((v) => setLabels(v.labels ?? {})).catch(() => undefined);
  }, [userId]);

  if (skills === null) return <Screen><Loading /></Screen>;
  const adopted = prog?.status === 'adopted';
  const label = (s: string) => labels[s.toLowerCase()] ?? s;

  return (
    <Screen>
      <Hero icon="sparkles" eyebrow="SkillPath" title="Welcome back">
        <Text style={{ color: colors.muted, fontSize: 16, lineHeight: 26, fontFamily: fonts.regular }}>
          {adopted ? `You're building ${label(prog!.skill)}. Keep going.` : skills.length ? 'Your next skill is ready to explore.' : 'Start by telling SkillPath what you can already do.'}
        </Text>
      </Hero>

      {!skills.length ? (
        <Card>
          <Text style={styles.h2}>Add your skills</Text>
          <Body muted>Upload your CV or pick skills from a list. It takes about two minutes.</Body>
          <Button label="Add my skills" icon="add-circle-outline" onPress={onEditProfile} />
        </Card>
      ) : adopted && prog ? (
        <Card>
          <SectionLabel>Your pathway</SectionLabel>
          <Text style={styles.h2}>{label(prog.skill)}</Text>
          <ProgressBar value={prog.modules_completed} total={prog.total_modules} />
          <Body muted>{prog.modules_completed} of {prog.total_modules} steps done{prog.completed ? ' · complete!' : ''}</Body>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: 4 }}>
            {['MS1', 'MS2'].map((m) => (
              <Pill key={m} label={prog.milestones.includes(m) ? `${m} reached` : `${m} to go`}
                    tone={prog.milestones.includes(m) ? 'success' : 'accent'} icon={prog.milestones.includes(m) ? 'trophy' : 'flag-outline'} />
            ))}
          </View>
          <Button label={prog.completed ? 'See my progress' : `Continue step ${(prog.current_module?.index ?? prog.modules_completed + 1)}`}
                  icon="play" onPress={() => go(prog.completed ? 'progress' : 'pathway')} />
        </Card>
      ) : (
        <Card>
          <SectionLabel>Next step</SectionLabel>
          <Text style={styles.h2}>Your next skill is ready</Text>
          <Body muted>See the one skill that brings you closest to jobs that match your profile.</Body>
          <Button label="See my next skill" icon="compass" onPress={() => go('next')} />
        </Card>
      )}

      <SectionLabel>Quick actions</SectionLabel>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginRight: -8 }}>
        <Action icon="create-outline" label="Edit my skills" onPress={onEditProfile} />
        <Action icon="compass-outline" label="Next skill" onPress={() => go('next')} />
        <Action icon="trophy-outline" label="My progress" onPress={() => go('progress')} />
        <Action icon="shield-checkmark-outline" label="Privacy & my data" onPress={() => go('settings')} />
      </View>

      {skills.length > 0 && (
        <Card>
          <SectionLabel>Your skills ({skills.length})</SectionLabel>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
            {skills.slice(0, 12).map((s) => <Pill key={s} label={label(s)} />)}
          </View>
        </Card>
      )}
    </Screen>
  );
}
