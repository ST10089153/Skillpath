// Glass bloom: the hero's decorative visual, after the researcher's references (iridescent glass flowers on black).
// Two layers of translucent petals with fine mesh lines, prismatic edges and a warm inner light. It turns slowly and
// "breathes"; both stop under reduce-motion. Purely decorative: hidden from screen readers and never under text
// contrast-critical areas (it sits to the right of the hero, behind a fade).
import React, { useEffect, useRef } from 'react';
import { Animated, Easing, Platform, View } from 'react-native';
import Svg, { Defs, G, LinearGradient, Path, RadialGradient, Stop } from 'react-native-svg';

import { PRISM, useReducedMotion } from './fx';

const NATIVE_DRIVER = Platform.OS !== 'web';

/** A petal pointing up from the centre (0,0) to (0,-r), half-width w. */
function petal(r: number, w: number) {
  return `M0,0 C${w},${-r * 0.32} ${w * 0.95},${-r * 0.86} 0,${-r} C${-w * 0.95},${-r * 0.86} ${-w},${-r * 0.32} 0,0 Z`;
}

/** Fine lines running from the centre to the tip across the petal, like the dotted mesh in the references. */
function mesh(r: number, w: number, n: number) {
  const lines: string[] = [];
  for (let i = 1; i < n; i++) {
    const f = -1 + (2 * i) / n;
    lines.push(`M0,0 C${w * f},${-r * 0.32} ${w * 0.95 * f},${-r * 0.86} 0,${-r}`);
  }
  return lines.join(' ');
}

function Layer({ r, w, count, offset, fill, edge, meshOpacity }: {
  r: number; w: number; count: number; offset: number; fill: string; edge: string; meshOpacity: number;
}) {
  return (
    <>
      {Array.from({ length: count }, (_, i) => (
        <G key={i} rotation={offset + (360 / count) * i}>
          <Path d={petal(r, w)} fill={fill} stroke={edge} strokeWidth={0.9} strokeOpacity={0.8} />
          <Path d={mesh(r, w, 9)} fill="none" stroke="#DDF4FF" strokeOpacity={meshOpacity} strokeWidth={0.5} strokeDasharray="1.2 2.4" />
        </G>
      ))}
    </>
  );
}

export default function GlassBloom({ size = 230 }: { size?: number }) {
  const reduced = useReducedMotion();
  const spin = useRef(new Animated.Value(0)).current;
  const breathe = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (reduced) { spin.setValue(0); breathe.setValue(0.5); return; }
    const s = Animated.loop(Animated.timing(spin, { toValue: 1, duration: 90000, easing: Easing.linear, useNativeDriver: NATIVE_DRIVER }));
    const b = Animated.loop(Animated.sequence([
      Animated.timing(breathe, { toValue: 1, duration: 4200, easing: Easing.inOut(Easing.sin), useNativeDriver: NATIVE_DRIVER }),
      Animated.timing(breathe, { toValue: 0, duration: 4200, easing: Easing.inOut(Easing.sin), useNativeDriver: NATIVE_DRIVER }),
    ]));
    s.start(); b.start();
    return () => { s.stop(); b.stop(); };
  }, [reduced, spin, breathe]);

  const rotate = spin.interpolate({ inputRange: [0, 1], outputRange: ['0deg', '360deg'] });
  const scale = breathe.interpolate({ inputRange: [0, 1], outputRange: [0.96, 1.04] });
  const half = size / 2;

  const art = (id: string) => (
    <Svg width={size} height={size} viewBox={`${-half} ${-half} ${size} ${size}`}>
      <Defs>
        <LinearGradient id={`edge${id}`} x1="0" y1="0" x2="1" y2="1">
          {PRISM.map((c, i) => <Stop key={c} offset={i / (PRISM.length - 1)} stopColor={c} stopOpacity={0.9} />)}
        </LinearGradient>
        {/* Glass: bright where the petal meets the light at its base, clearer through the middle, lilac at the lip. */}
        <LinearGradient id={`glass${id}`} x1="0" y1="1" x2="0" y2="0">
          <Stop offset="0" stopColor="#FFFFFF" stopOpacity={0.55} />
          <Stop offset="0.45" stopColor="#BFE6FF" stopOpacity={0.16} />
          <Stop offset="1" stopColor="#E9D8FF" stopOpacity={0.40} />
        </LinearGradient>
        <RadialGradient id={`core${id}`} cx="0" cy="0" r={half * 0.55} gradientUnits="userSpaceOnUse">
          <Stop offset="0" stopColor="#FFC27A" stopOpacity={0.95} />
          <Stop offset="0.35" stopColor="#FF8A5C" stopOpacity={0.45} />
          <Stop offset="1" stopColor="#FF8A5C" stopOpacity={0} />
        </RadialGradient>
      </Defs>
      <Path d={`M${-half},0 a${half},${half} 0 1,0 ${size},0 a${half},${half} 0 1,0 ${-size},0`} fill={`url(#core${id})`} opacity={0.55} />
      <Layer r={half * 0.92} w={half * 0.36} count={6} offset={0} fill={`url(#glass${id})`} edge={`url(#edge${id})`} meshOpacity={0.35} />
      <Layer r={half * 0.62} w={half * 0.26} count={6} offset={30} fill={`url(#glass${id})`} edge={`url(#edge${id})`} meshOpacity={0.5} />
      <Path d="M-10,0 a10,10 0 1,0 20,0 a10,10 0 1,0 -20,0" fill={`url(#core${id})`} />
    </Svg>
  );

  return (
    <View pointerEvents="none" accessibilityElementsHidden importantForAccessibility="no-hide-descendants"
          style={{ width: size, height: size }}>
      <Animated.View style={{ width: size, height: size, transform: [{ rotate }, { scale }] }}>
        {/* Web: a blurred copy underneath gives the glass its glow. */}
        {Platform.OS === 'web' ? (
          <View style={{ position: 'absolute', opacity: 0.7, ...({ filter: 'blur(12px)' } as object) }}>{art('g')}</View>
        ) : null}
        {art('s')}
      </Animated.View>
    </View>
  );
}
