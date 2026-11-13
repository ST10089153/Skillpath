import React, { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { Text, View } from 'react-native';

import { api, API_URL } from '../api';
import { Body, Button, Card, DISCLAIMER, ErrorText, Screen, Title, colors, styles } from '../ui';

export default function Settings({ userId, onDeleted, onEditProfile }: {
  userId: string; onDeleted: () => void; onEditProfile: () => void;
}) {
  const [data, setData] = useState<string>('');
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState('');

  async function view() {
    setError('');
    try {
      setData(JSON.stringify(await api.myData(userId), null, 2));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function del() {
    setError('');
    try {
      await api.deleteMe(userId);
      onDeleted();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <Screen>
      <Title>Settings</Title>
      <Card>
        <Text style={styles.h2}>Your ID</Text>
        <Body>{userId}</Body>
        <Body muted>This random ID is the only thing that links your data. No name, email or phone number is stored.</Body>
      </Card>

      <Button label="Edit my skills" icon="create-outline" variant="tonal" onPress={onEditProfile} />
      <Button label={data ? 'Refresh my data' : 'View my data'} icon="eye-outline" variant="tonal" onPress={view} />
      {data !== '' && (
        <Card><Text style={{ fontFamily: 'monospace', fontSize: 13, color: colors.text }} selectable>{data}</Text></Card>
      )}

      <Card>
        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 6 }}>
          <Ionicons name="trash-outline" size={22} color={colors.danger} style={{ marginRight: 8 }} />
          <Text style={[styles.h2, { marginBottom: 0 }]}>Delete my data</Text>
        </View>
        <Body>This permanently removes your profile, pathway and activity records from SkillPath.</Body>
        {!confirming ? (
          <Button label="Delete my data" icon="trash-outline" variant="danger" onPress={() => setConfirming(true)} />
        ) : (
          <>
            <Body style={{ fontFamily: 'Outfit_600SemiBold' }}>Are you sure? This cannot be undone.</Body>
            <Button label="Yes, delete everything" variant="danger" onPress={del} />
            <Button label="Cancel" variant="secondary" onPress={() => setConfirming(false)} />
          </>
        )}
      </Card>
      <ErrorText error={error} />

      <Card>
        <Text style={styles.h2}>About</Text>
        <Body>SkillPath is a research prototype for an Honours study at The Independent Institute of Education.</Body>
        <Body muted>{DISCLAIMER}</Body>
        <Text style={styles.small}>Server: {API_URL}</Text>
      </Card>
    </Screen>
  );
}
