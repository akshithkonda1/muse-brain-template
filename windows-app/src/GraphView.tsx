// GraphView.tsx — the premium memory-map graph for React Native Windows.
//
// SVG nodes = notes, lines = [[wiki-links]]. Drag the background to
// pan, tap a node to read it, zoom with the +/- buttons. Colour is
// cluster colour (docs/design-system.md): the same eight hues, in the
// same rank order, as the web dashboard and the Mac app. Node size =
// connections; a ring marks a hub (6+). Cluster hulls show each
// cluster's territory; dashed amber rings are quiet notes (no links
// yet) — invitations, not errors. Positions come from the bundled
// brain-data.json (cluster-aware force layout from scan.py).

import React, {useMemo, useRef, useState} from 'react';
import {PanResponder, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import Svg, {Circle, Line, G, Polygon, Text as SvgText} from 'react-native-svg';
import {
  BRAIN,
  NOTE_BY_STEM,
  CLUSTER_COLORS,
  clusterColorFor,
  degreeOf,
} from './brain';

type Pt = [number, number];

function hull(points: Pt[], pad: number): Pt[] {
  const pts = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (pts.length < 3) {
    return pts;
  }
  const cross = (o: Pt, a: Pt, b: Pt) =>
    (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower: Pt[] = [];
  for (const p of pts) {
    while (
      lower.length >= 2 &&
      cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0
    ) {
      lower.pop();
    }
    lower.push(p);
  }
  const upper: Pt[] = [];
  for (let i = pts.length - 1; i >= 0; i--) {
    const p = pts[i];
    while (
      upper.length >= 2 &&
      cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0
    ) {
      upper.pop();
    }
    upper.push(p);
  }
  lower.pop();
  upper.pop();
  const h = lower.concat(upper);
  const cx = h.reduce((s, p) => s + p[0], 0) / h.length;
  const cy = h.reduce((s, p) => s + p[1], 0) / h.length;
  return h.map(([x, y]) => {
    const dx = x - cx;
    const dy = y - cy;
    const d = Math.hypot(dx, dy) || 1;
    return [x + (dx / d) * pad, y + (dy / d) * pad] as Pt;
  });
}

export function GraphView({
  selectedStem,
  onSelect,
  dark,
  focusCluster,
  showSuggest,
}: {
  selectedStem: string | null;
  onSelect: (stem: string) => void;
  dark: boolean;
  focusCluster: number | null;
  showSuggest: boolean;
}) {
  const [pan, setPan] = useState({x: 0, y: 0});
  const [scale, setScale] = useState(1);
  const panRef = useRef({x: 0, y: 0});
  const dragRef = useRef<{stem: string; moved: boolean} | null>(null);

  const panResponder = useMemo(
    () =>
      PanResponder.create({
        onStartShouldSetPanResponder: () => true,
        onMoveShouldSetPanResponder: () => true,
        onPanResponderGrant: evt => {
          // Hit-test: nearest node within 18px of the press?
          const {locationX, locationY} = evt.nativeEvent;
          const cx = 400, cy = 260;
          let best: {stem: string; dist: number} | null = null;
          for (const note of BRAIN.notes) {
            const pos = BRAIN.positions[note.stem];
            if (!pos) {
              continue;
            }
            const px = (pos[0] - cx) * scale + panRef.current.x;
            const py = (pos[1] - cy) * scale + panRef.current.y;
            const d = Math.hypot(locationX - px, locationY - py);
            if (d < 18 && (!best || d < best.dist)) {
              best = {stem: note.stem, dist: d};
            }
          }
          dragRef.current = best ? {stem: best.stem, moved: false} : null;
        },
        onPanResponderMove: (evt, gesture) => {
          if (dragRef.current) {
            dragRef.current.moved = true;
          } else {
            setPan({
              x: panRef.current.x + gesture.dx,
              y: panRef.current.y + gesture.dy,
            });
          }
        },
        onPanResponderRelease: (_evt, gesture) => {
          if (dragRef.current && !dragRef.current.moved) {
            onSelect(dragRef.current.stem); // it was a tap
          } else if (!dragRef.current) {
            panRef.current = {
              x: panRef.current.x + gesture.dx,
              y: panRef.current.y + gesture.dy,
            };
          }
          dragRef.current = null;
        },
      }),
    [scale, onSelect],
  );

  const edges = useMemo(() => {
    const out: {a: [number, number]; b: [number, number]; key: string}[] = [];
    for (const note of BRAIN.notes) {
      const a = BRAIN.positions[note.stem];
      if (!a) {
        continue;
      }
      for (const target of note.links) {
        const b = BRAIN.positions[target];
        if (b && target !== note.stem) {
          out.push({a, b, key: note.stem + '->' + target});
        }
      }
    }
    return out;
  }, []);

  const isDim = (stem: string) =>
    focusCluster !== null &&
    !(BRAIN.clusters[focusCluster]?.members.includes(stem) ?? false);

  const stroke = dark ? '#A19CB6' : '#6F6A7E';
  return (
    <View style={styles.container}>
      <View style={styles.toolbar}>
        <TouchableOpacity
          style={styles.zoomBtn}
          onPress={() => setScale(s => Math.min(3, s * 1.25))}>
          <Text style={styles.zoomText}>+</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.zoomBtn}
          onPress={() => setScale(s => Math.max(0.4, s / 1.25))}>
          <Text style={styles.zoomText}>−</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.zoomBtn}
          onPress={() => {
            setScale(1);
            setPan({x: 0, y: 0});
            panRef.current = {x: 0, y: 0};
          }}>
          <Text style={styles.zoomText}>Reset</Text>
        </TouchableOpacity>
        <Text style={[styles.hint, {color: stroke}]}>
          Drag to pan · tap a node to read it · dashed = quiet note
        </Text>
      </View>
      <View style={{flex: 1}} {...panResponder.panHandlers}>
        <Svg width="100%" height="100%" viewBox="0 0 800 560">
          <G
            transform={`translate(${pan.x + 400 * (1 - scale)}, ${
              pan.y + 260 * (1 - scale)
            }) scale(${scale})`}>
            {[...BRAIN.clusters]
              .map((c, i) => ({c, i}))
              .sort((a, b) => b.c.members.length - a.c.members.length)
              .map(({c, i}) => {
                const pts = c.members
                  .map(m => BRAIN.positions[m])
                  .filter((p): p is [number, number] => Boolean(p));
                if (pts.length < 3) {
                  return null;
                }
                const col = CLUSTER_COLORS[i % CLUSTER_COLORS.length];
                const h = hull(pts, 26);
                const top = h.reduce((a, p) => (p[1] < a[1] ? p : a), h[0]);
                return (
                  <G
                    key={'hull-' + c.label}
                    opacity={focusCluster !== null && focusCluster !== i ? 0.15 : 1}>
                    <Polygon
                      points={h.map(p => p.map(v => v.toFixed(1)).join(',')).join(' ')}
                      fill={col}
                      fillOpacity={0.07}
                      stroke={col}
                      strokeOpacity={0.45}
                      strokeWidth={1.4}
                      strokeDasharray="6 4"
                    />
                    <SvgText
                      x={top[0]}
                      y={top[1] - 8}
                      fontSize={11}
                      fontWeight="700"
                      fill={col}
                      textAnchor="middle">
                      {c.label.toUpperCase()}
                    </SvgText>
                  </G>
                );
              })}
            {showSuggest &&
              BRAIN.suggestions.map(s => {
                const a = BRAIN.positions[s.a];
                const b = BRAIN.positions[s.b];
                if (!a || !b) {
                  return null;
                }
                return (
                  <Line
                    key={'suggest-' + s.a + '-' + s.b}
                    x1={a[0]}
                    y1={a[1]}
                    x2={b[0]}
                    y2={b[1]}
                    stroke="#7C5CFF"
                    strokeOpacity={0.65}
                    strokeWidth={1.2}
                    strokeDasharray="4 3"
                  />
                );
              })}
            {edges.map(e => (
              <Line
                key={e.key}
                x1={e.a[0]}
                y1={e.a[1]}
                x2={e.b[0]}
                y2={e.b[1]}
                stroke={stroke}
                strokeOpacity={isDim(e.key.split('->')[0]) ? 0.06 : 0.35}
                strokeWidth={1}
              />
            ))}
            {BRAIN.notes.map(note => {
              const pos = BRAIN.positions[note.stem];
              if (!pos) {
                return null;
              }
              const isOrphan = BRAIN.orphans.includes(note.stem);
              const isSelected = note.stem === selectedStem;
              const deg = degreeOf(note.stem);
              const r = 8 + Math.min(8, deg);
              const col = clusterColorFor(note.stem, note.tags);
              const label =
                note.title.length > 22
                  ? note.title.slice(0, 21) + '…'
                  : note.title;
              return (
                <G
                  key={note.stem}
                  opacity={isDim(note.stem) ? 0.18 : 1}>
                  {deg >= 6 && (
                    <Circle
                      cx={pos[0]}
                      cy={pos[1]}
                      r={r + 4.5}
                      fill="none"
                      stroke={col}
                      strokeOpacity={0.55}
                      strokeWidth={1.4}
                    />
                  )}
                  {isSelected && (
                    <Circle
                      cx={pos[0]}
                      cy={pos[1]}
                      r={r + 7}
                      fill="none"
                      stroke="#7C5CFF"
                      strokeOpacity={0.35}
                      strokeWidth={5}
                    />
                  )}
                  <Circle
                    cx={pos[0]}
                    cy={pos[1]}
                    r={r}
                    fill={isOrphan ? 'none' : col}
                    stroke={isOrphan ? '#f59e0b' : isSelected ? '#7C5CFF' : 'none'}
                    strokeWidth={isOrphan || isSelected ? 2 : 0}
                    strokeDasharray={isOrphan ? '3 2' : undefined}
                    onPress={() => onSelect(note.stem)}
                  />
                  {isSelected && (
                    <Circle
                      cx={pos[0]}
                      cy={pos[1]}
                      r={r}
                      fill="none"
                      stroke="#7C5CFF"
                      strokeWidth={2.5}
                    />
                  )}
                  {/* Labels: selected node only — even the hub labels
                      collide in the centre, because the hubs are all
                      linked to each other. Names live in the sidebar. */}
                  {isSelected && (
                    <SvgText
                      x={pos[0] + r + 7}
                      y={pos[1] + 4}
                      fontSize={11}
                      fontWeight="600"
                      fill={dark ? '#F4F2FA' : '#17141F'}>
                      {label}
                    </SvgText>
                  )}
                  <Circle
                    cx={pos[0]}
                    cy={pos[1]}
                    r={r + 8}
                    fill="transparent"
                    onPress={() => onSelect(note.stem)}
                  />
                </G>
              );
            })}
          </G>
        </Svg>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {flex: 1},
  toolbar: {flexDirection: 'row', alignItems: 'center', padding: 6, gap: 6},
  zoomBtn: {
    borderWidth: 1,
    borderColor: '#9ca3af',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  zoomText: {fontSize: 15, fontWeight: '600'},
  hint: {fontSize: 12, marginLeft: 6},
});
