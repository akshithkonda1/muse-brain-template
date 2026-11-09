// GraphView.tsx — the memory-map graph for React Native Windows.
//
// SVG nodes = notes, lines = [[wiki-links]]. Drag the background to
// pan, tap a node to read it, zoom with the +/- buttons. Node colour
// = first tag; dashed ring = orphan. Positions come from the bundled
// brain-data.json (seeded force layout from scan.py).

import React, {useMemo, useRef, useState} from 'react';
import {PanResponder, StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import Svg, {Circle, Line, G, Text as SvgText} from 'react-native-svg';
import {BRAIN, NOTE_BY_STEM} from './brain';

const TAG_COLORS = [
  '#7c3aed', '#0d9488', '#ea580c', '#16a34a', '#92400e',
  '#2563eb', '#db2777', '#0891b2', '#059669', '#6b7280',
];

function colorFor(tags: string[]): string {
  const key = tags[0] ?? 'notes';
  let h = 0;
  for (let i = 0; i < key.length; i++) {
    h = (h * 31 + key.charCodeAt(i)) >>> 0;
  }
  return TAG_COLORS[h % TAG_COLORS.length];
}

export function GraphView({
  selectedStem,
  onSelect,
  dark,
}: {
  selectedStem: string | null;
  onSelect: (stem: string) => void;
  dark: boolean;
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

  const stroke = dark ? '#9ca3af' : '#6b7280';
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
          Drag to pan · tap a node to read it · dashed = orphan
        </Text>
      </View>
      <View style={{flex: 1}} {...panResponder.panHandlers}>
        <Svg width="100%" height="100%" viewBox="0 0 800 520">
          <G
            transform={`translate(${pan.x + 400 * (1 - scale)}, ${
              pan.y + 260 * (1 - scale)
            }) scale(${scale})`}>
            {edges.map(e => (
              <Line
                key={e.key}
                x1={e.a[0]}
                y1={e.a[1]}
                x2={e.b[0]}
                y2={e.b[1]}
                stroke={stroke}
                strokeOpacity={0.45}
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
              const r = 7 + Math.min(6, note.incoming.length);
              const label =
                note.title.length > 22
                  ? note.title.slice(0, 21) + '…'
                  : note.title;
              return (
                <G key={note.stem}>
                  <Circle
                    cx={pos[0]}
                    cy={pos[1]}
                    r={r}
                    fill={isOrphan ? 'none' : colorFor(note.tags)}
                    stroke={isOrphan ? '#f59e0b' : 'none'}
                    strokeWidth={isOrphan ? 2 : 0}
                    strokeDasharray={isOrphan ? '4 3' : undefined}
                    onPress={() => onSelect(note.stem)}
                  />
                  {isSelected && (
                    <Circle
                      cx={pos[0]}
                      cy={pos[1]}
                      r={r + 4}
                      fill="none"
                      stroke="#7c3aed"
                      strokeWidth={2.5}
                    />
                  )}
                  <SvgText
                    x={pos[0] + r + 5}
                    y={pos[1] + 4}
                    fontSize={11}
                    fill={dark ? '#e5e7eb' : '#111827'}>
                    {label}
                  </SvgText>
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
