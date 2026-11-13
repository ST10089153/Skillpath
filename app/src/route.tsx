// Route-map components: the pathway drawn as a line with stops, milestones as interchanges, and the recommended
// skill branching to the occupations it serves. Built from plain Views so they render the same on web and phone.
// Marker shape and a text label always carry the state too, so nothing relies on colour alone.
import React, { ReactNode } from 'react';
import { Text, View } from 'react-native';

import { colors, fonts, styles } from './ui';

export type StopState = 'done' | 'here' | 'next';

const GUTTER = 44;
const LINE_W = 4;

/** Station marker: filled = passed, gold ring = you are here, hollow = still to come; interchanges are capsules. */
function Marker({ state, interchange }: { state: StopState; interchange?: boolean }) {
  const stroke = state === 'here' ? colors.here : state === 'done' ? colors.line : colors.track;
  const fill = state === 'done' ? colors.line : colors.bg;
  if (interchange) {
    return (
      <View style={{ width: 30, height: 18, borderRadius: 9, borderWidth: 3, borderColor: state === 'here' ? colors.here : colors.text,
                     backgroundColor: state === 'done' ? colors.line : colors.bg }} />
    );
  }
  if (state === 'here') {
    return (
      <View style={{ width: 24, height: 24, borderRadius: 12, borderWidth: 3, borderColor: stroke, backgroundColor: colors.bg,
                     alignItems: 'center', justifyContent: 'center' }}>
        <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: colors.here }} />
      </View>
    );
  }
  return <View style={{ width: 16, height: 16, borderRadius: 8, borderWidth: 3, borderColor: stroke, backgroundColor: fill }} />;
}

export interface Stop {
  key: string;
  number: number;
  title: string;
  meta?: string;
  state: StopState;
  interchange?: string;   // e.g. "Milestone MS1"
  children?: ReactNode;
}

/** The pathway as a vertical route. The line is coloured up to "you are here" and shown as track after it. */
export function RouteStops({ stops }: { stops: Stop[] }) {
  return (
    <View accessibilityRole="list">
      {stops.map((s, i) => {
        const first = i === 0;
        const last = i === stops.length - 1;
        const above = s.state !== 'next' ? colors.line : colors.track;
        const below = s.state === 'done' ? colors.line : colors.track;
        const stateText = s.state === 'done' ? 'passed' : s.state === 'here' ? 'you are here' : 'to come';
        return (
          <View key={s.key} style={{ flexDirection: 'row' }} accessibilityLabel={`Stop ${s.number}, ${s.title}, ${stateText}`}>
            <View style={{ width: GUTTER, alignItems: 'center' }}>
              <View style={{ width: LINE_W, height: 14, backgroundColor: first ? 'transparent' : above }} />
              <Marker state={s.state} interchange={!!s.interchange} />
              <View style={{ width: LINE_W, flex: 1, minHeight: 18, backgroundColor: last ? 'transparent' : below,
                             opacity: s.state === 'done' ? 1 : 0.55 }} />
            </View>
            <View style={{ flex: 1, paddingTop: 8, paddingBottom: last ? 0 : 22, paddingLeft: 6 }}>
              <Text style={[styles.numeric, { fontSize: 12, color: s.state === 'here' ? colors.here : colors.faint, letterSpacing: 1 }]}>
                {`STOP ${String(s.number).padStart(2, '0')}${s.meta ? ` · ${s.meta}` : ''}${s.state === 'here' ? ' · YOU ARE HERE' : ''}`}
              </Text>
              <Text style={[styles.h2, { fontSize: s.state === 'here' ? 24 : 19, lineHeight: s.state === 'here' ? 30 : 25, marginTop: 4,
                                         color: s.state === 'next' ? colors.muted : colors.text }]}>
                {s.title}
              </Text>
              {s.interchange ? (
                <Text style={[styles.numeric, { fontSize: 12, color: s.state === 'done' ? colors.line : colors.faint, marginBottom: 4 }]}>
                  {`INTERCHANGE · ${s.interchange.toUpperCase()}${s.state === 'done' ? ' REACHED' : ''}`}
                </Text>
              ) : null}
              {s.children}
            </View>
          </View>
        );
      })}
    </View>
  );
}

/** The whole pathway in one line, for the home screen: six stations, interchanges at the milestones. */
export function RouteStrip({ total, done, here, interchanges }: {
  total: number; done: number; here: number | null; interchanges: number[];
}) {
  return (
    <View accessible accessibilityLabel={`${done} of ${total} stops passed`} style={{ marginVertical: 18 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        {Array.from({ length: total }, (_, i) => {
          const n = i + 1;
          const state: StopState = n <= done ? 'done' : n === here ? 'here' : 'next';
          return (
            <React.Fragment key={n}>
              {i > 0 && <View style={{ flex: 1, height: LINE_W, backgroundColor: n <= done || n === here ? colors.line : colors.track,
                                       opacity: n <= done || n === here ? 1 : 0.55 }} />}
              <Marker state={state} interchange={interchanges.includes(n)} />
            </React.Fragment>
          );
        })}
      </View>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
        {Array.from({ length: total }, (_, i) => (
          <Text key={i} style={[styles.numeric, { fontSize: 11, color: i + 1 === here ? colors.here : colors.faint }]}>
            {String(i + 1).padStart(2, '0')}
          </Text>
        ))}
      </View>
    </View>
  );
}

export interface Branch {
  key: string;
  title: string;
  code?: string;          // e.g. "OFO 2021-251101"
  held: number;
  total: number;
  missing: { label: string; isThis: boolean }[];
  source?: string;
}

/** The recommended skill as a junction: one branch line to each nearby occupation, with what is still missing. */
export function Branches({ branches }: { branches: Branch[] }) {
  return (
    <View accessibilityRole="list">
      {branches.map((b, i) => {
        const last = i === branches.length - 1;
        return (
          <View key={b.key} style={{ flexDirection: 'row' }}>
            <View style={{ width: GUTTER, alignItems: 'center' }}>
              {/* trunk */}
              <View style={{ position: 'absolute', left: GUTTER / 2 - LINE_W / 2, top: 0, bottom: last ? undefined : 0,
                             height: last ? 22 : undefined, width: LINE_W, backgroundColor: colors.line }} />
              {/* spur to this station */}
              <View style={{ position: 'absolute', left: GUTTER / 2, top: 20, width: GUTTER / 2 + 4, height: LINE_W, backgroundColor: colors.line }} />
            </View>
            <View style={{ flex: 1, paddingLeft: 10, paddingBottom: last ? 0 : 20 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12 }}>
                <View style={{ width: 14, height: 14, borderRadius: 7, borderWidth: 3, borderColor: colors.line, backgroundColor: colors.bg, marginRight: 10 }} />
                <Text style={{ fontFamily: fonts.semibold, fontSize: 17, color: colors.text, flex: 1 }}>{b.title}</Text>
              </View>
              <Text style={[styles.numeric, { fontSize: 12, color: colors.faint, marginTop: 4, marginLeft: 24 }]}>
                {`${b.code ? `${b.code} · ` : ''}YOU HAVE ${b.held} OF ${b.total}`}
              </Text>
              {b.missing.length > 0 && (
                <Text style={[styles.body, { fontSize: 15, lineHeight: 23, marginLeft: 24, marginTop: 6, marginBottom: 0, color: colors.muted }]}>
                  {'Still to learn: '}
                  {b.missing.map((m, j) => (
                    <Text key={m.label} style={m.isThis ? { color: colors.here, fontFamily: fonts.semibold } : undefined}>
                      {m.label}{m.isThis ? ' (this stop)' : ''}{j < b.missing.length - 1 ? ' · ' : ''}
                    </Text>
                  ))}
                </Text>
              )}
              {b.source ? <Text style={[styles.small, { marginLeft: 24, marginTop: 6 }]}>{b.source}</Text> : null}
            </View>
          </View>
        );
      })}
    </View>
  );
}

/** "OFO 2021-251101" from a DHET source string, if present. */
export function ofoCode(source: string | undefined): string {
  const m = /OFO\s*(\d{4}-\d{6})/.exec(source ?? '');
  return m ? `OFO ${m[1]}` : '';
}
