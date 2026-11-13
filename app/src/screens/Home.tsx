import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { api, moduleContent, ModuleLibrary, Progress, SkillInfo } from '../api';
import { RouteStrip } from '../route';
import { Body, Button, Columns, Eyebrow, Hero, Loading, Screen, SectionLabel, TextLink, colors, styles } from '../ui';

type Go = 'next' | 'pathway' | 'progress' | 'settings';

const MODULES_PER_MILESTONE = 3; // mirrors skillpath/config.py (display only)

export default function Home({ userId, go, onEditProfile }: { userId: string; go: (t: Go) => void; onEditProfile: () => void }) {
  const [skills, setSkills] = useState<string[] | null>(null);
  const [prog, setProg] = useState<Progress | null>(null);
  const [labels, setLabels] = useState<Record<string, string>>({});
  const [lib, setLib] = useState<ModuleLibrary | null>(null);
  const [info, setInfo] = useState<SkillInfo | null>(null);

  useEffect(() => {
    api.myData(userId).then((d) => {
      const u = (d as { user?: { current_skills?: string } }).user;
      setSkills((u?.current_skills || '').split(';').map((s) => s.trim()).filter(Boolean));
    }).catch(() => setSkills([]));
    api.progress(userId).then(setProg).catch(() => setProg(null));
    api.vocabulary().then((v) => setLabels(v.labels ?? {})).catch(() => undefined);
    api.modules().then(setLib).catch(() => setLib(null));
  }, [userId]);
  useEffect(() => {
    if (prog?.skill) api.skill(prog.skill).then(setInfo).catch(() => setInfo(null));
  }, [prog?.skill]);

  if (skills === null) return <Screen><Loading /></Screen>;
  const label = (s: string) => labels[s.toLowerCase()] ?? s;
  const adopted = prog?.status === 'adopted';

  // No skills yet: the first job is to say where you are starting from.
  if (!skills.length) {
    return (
      <Screen>
        <Hero eyebrow="No starting point yet" title="Where are you starting from?">
          <Body muted>Upload your CV or pick the skills you already have. It takes about two minutes.</Body>
        </Hero>
        <Button label="Add my skills" onPress={onEditProfile} />
      </Screen>
    );
  }

  // Skills but no pathway: point to the recommendation.
  if (!adopted || !prog) {
    return (
      <Screen>
        <Hero eyebrow="No pathway yet" title="Find your next skill">
          <Body muted>SkillPath looks at the {skills.length} skills you have and finds the one skill that brings you closest to jobs near your profile.</Body>
        </Hero>
        <Columns main={<Button label="See my next skill" onPress={() => go('next')} />}
                 side={<SkillsList skills={skills} label={label} onEdit={onEditProfile} />} />
      </Screen>
    );
  }

  const total = prog.total_modules;
  const here = prog.completed ? null : (prog.current_module?.index ?? prog.modules_completed + 1); // index is 1-based
  const interchanges = Array.from({ length: Math.floor(total / MODULES_PER_MILESTONE) }, (_, i) => (i + 1) * MODULES_PER_MILESTONE);
  const nextInterchange = interchanges.find((n) => n > prog.modules_completed);
  const skillName = info?.label ?? label(prog.skill);
  const current = here ? moduleContent(lib, skillName, here - 1, info?.esco_url ?? '', info?.how_to_show ?? '') : null;

  return (
    <Screen>
      <Hero eyebrow={prog.completed ? 'Pathway complete' : 'You are here'}
            title={prog.completed ? `All ${total} steps done` : `Step ${here} of ${total}`}>
        <Body muted>{`Your pathway: ${skillName}.`}</Body>
      </Hero>

      <Columns main={<>
      <RouteStrip total={total} done={prog.modules_completed} here={here} interchanges={interchanges} />

      {nextInterchange ? (
        <Text style={[styles.numeric, { fontSize: 13, color: colors.muted, marginBottom: 18 }]}>
          {`${nextInterchange - prog.modules_completed} ${nextInterchange - prog.modules_completed === 1 ? 'step' : 'steps'} to milestone MS${nextInterchange / MODULES_PER_MILESTONE}`}
        </Text>
      ) : null}

      {current ? (
        <View style={styles.cardInner}>
          <Eyebrow color={colors.primary}>{`STEP ${String(here).padStart(2, '0')} · ABOUT ${prog.current_module?.minutes ?? 6} MIN`}</Eyebrow>
          <Text style={[styles.h2, { marginBottom: 12 }]}>{current.title}</Text>
          <Button label={`Continue step ${here}`} onPress={() => go('pathway')} />
        </View>
      ) : (
        <Button label="See my progress" onPress={() => go('progress')} />
      )}
      </>} side={<SkillsList skills={skills} label={label} onEdit={onEditProfile} />} />
    </Screen>
  );
}

function SkillsList({ skills, label, onEdit }: { skills: string[]; label: (s: string) => string; onEdit: () => void }) {
  return (
    <>
      <SectionLabel right={String(skills.length)}>Skills you have</SectionLabel>
      <Body muted>{skills.map(label).join(' · ')}</Body>
      <TextLink label="Edit my skills" onPress={onEdit} />
    </>
  );
}
