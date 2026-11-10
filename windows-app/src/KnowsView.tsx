// KnowsView.tsx — "What Muse knows": the digital copy, by area.
//
// After sign-in, this is the view that shows what Muse knows about
// you: every topic is a real note, with its one-line summary and
// its source trail. Tap a topic to read the note. A topic with no
// source says so — check before trusting. Data comes from the
// generated brain snapshot (brain-data.json), built by
// windows-app/scripts/generate-brain-data.py from the Markdown
// files. Nothing here touches the network.

import React, {useMemo, useState} from 'react';
import {ScrollView, Text, TextInput, TouchableOpacity, View} from 'react-native';
import {KNOWS} from './brain';

export function KnowsView({
  colors,
  onOpen,
}: {
  colors: {
    surface: string;
    text: string;
    secondary: string;
    accent: string;
    border: string;
    chipBg: string;
  };
  onOpen: (stem: string) => void;
}) {
  const [area, setArea] = useState<string | null>(null);
  const [filter, setFilter] = useState('');
  const topics = useMemo(() => {
    let list = KNOWS.topics;
    if (area) {
      list = list.filter(t => t.area_tag === area);
    }
    const q = filter.trim().toLowerCase();
    if (q) {
      list = list.filter(t =>
        `${t.title} ${t.excerpt} ${t.tags.join(' ')}`.toLowerCase().includes(q),
      );
    }
    return list;
  }, [area, filter]);
  const cov = KNOWS.coverage;
  return (
    <ScrollView style={{flex: 1, padding: 12}}>
      <Text style={{fontSize: 11, fontWeight: '700', color: colors.accent}}>
        WHAT MUSE KNOWS
      </Text>
      <Text style={{fontSize: 18, fontWeight: '700', color: colors.text, marginTop: 4}}>
        Your digital copy, by area
      </Text>
      <Text style={{fontSize: 13, color: colors.secondary, marginTop: 4, lineHeight: 19}}>
        {cov.total} topics · {cov.with_source} with a source trail ·{' '}
        {cov.source_needed} marked [source needed] · {cov.quiet} quiet notes.
        Every topic is a real note — tap one to read it.
      </Text>
      <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10}}>
        {KNOWS.areas.map(a => (
          <TouchableOpacity
            key={a.tag}
            onPress={() => setArea(area === a.tag ? null : a.tag)}
            style={{
              borderWidth: 1,
              borderColor: colors.border,
              borderRadius: 999,
              paddingHorizontal: 10,
              paddingVertical: 5,
              backgroundColor: area === a.tag ? colors.accent : colors.chipBg,
            }}>
            <Text style={{color: area === a.tag ? '#ffffff' : colors.text, fontSize: 12}}>
              {a.label} · {a.count}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <TextInput
        value={filter}
        onChangeText={setFilter}
        placeholder="Filter what Muse knows…"
        placeholderTextColor={colors.secondary}
        style={{
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 999,
          paddingHorizontal: 12,
          paddingVertical: 8,
          marginTop: 10,
          color: colors.text,
        }}
      />
      {topics.map(t => (
        <TouchableOpacity
          key={t.stem}
          onPress={() => onOpen(t.stem)}
          style={{
            borderTopWidth: 1,
            borderColor: colors.border,
            paddingVertical: 10,
            marginTop: 6,
          }}>
          <Text style={{fontSize: 15, fontWeight: '700', color: colors.text}}>
            {t.title}
          </Text>
          <Text style={{fontSize: 13, color: colors.secondary, lineHeight: 19, marginTop: 2}}>
            {t.excerpt}
          </Text>
          <Text style={{fontSize: 12, color: colors.secondary, marginTop: 2}}>
            {t.tags.map(x => `#${x}`).join(' ')} · {t.degree} connections
            {t.cluster ? ` · ${t.cluster.label}` : ''}
          </Text>
          {t.sources.length > 0 ? (
            <Text style={{fontSize: 12, color: colors.secondary, marginTop: 2}}>
              Sources: {t.sources.join(' · ')}
            </Text>
          ) : (
            <Text style={{fontSize: 12, fontWeight: '700', color: '#B45309', marginTop: 2}}>
              No source on file — check before trusting.
            </Text>
          )}
        </TouchableOpacity>
      ))}
      {topics.length === 0 && (
        <Text style={{color: colors.secondary, marginTop: 12}}>
          Nothing matches — try a different word, or clear the area filter.
        </Text>
      )}
    </ScrollView>
  );
}
