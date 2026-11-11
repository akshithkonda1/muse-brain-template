// App.tsx — the Muse Brain window on React Native Windows.
//
// Three panes: sidebar (search / tags / clusters / attention),
// memory-map graph, and the note reader. Search is BM25 with a
// TF-IDF cosine second signal — the same math as ml/search.py and
// the Swift app. Everything is local: the brain ships as a bundled
// snapshot (src/brain-data.json) generated from the Markdown files.

import React, {useMemo, useRef, useState} from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  useWindowDimensions,
} from 'react-native';
import {BRAIN, NOTE_BY_STEM, TAG_COUNTS, TOTAL_LINKS, CLUSTER_COLORS, PROFILE, KNOWS} from './brain';
import {LoginScreen} from './Login';
import {KnowsView} from './KnowsView';
import {SEARCH_INDEX} from './search';
import {GraphView} from './GraphView';
import {MarkdownView} from './markdown';

/* Shared palette (docs/design-system.md) — same tokens as the web
 * dashboard and the Mac app. Warm paper light, ink dark, violet accent. */
const LIGHT = {
  bg: '#F6F5F1',
  surface: '#FFFFFF',
  surface2: '#EFEDE8',
  text: '#17141F',
  secondary: '#6F6A7E',
  accent: '#6C4CF1',
  border: '#E3E0D9',
  codeBg: '#EFEDE8',
  chipBg: '#EFEDE8',
};

const DARK = {
  bg: '#0C0B10',
  surface: '#16151D',
  surface2: '#1F1E28',
  text: '#F4F2FA',
  secondary: '#A19CB6',
  accent: '#9B7FF5',
  border: '#2B2938',
  codeBg: '#1F1E28',
  chipBg: '#1F1E28',
};

export default function App() {
  const [query, setQuery] = useState('');
  const [selectedStem, setSelectedStem] = useState<string | null>(null);
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());
  const [focusCluster, setFocusCluster] = useState<number | null>(null);
  const [showSuggest, setShowSuggest] = useState(false);
  const [dark, setDark] = useState(false);
  // Login gate (docs/login.md): session-only in v1 — closing the
  // app ends the session. "Sign in with Muse" is an honest
  // placeholder until Meta publishes a sign-in endpoint.
  const [signedIn, setSignedIn] = useState(false);
  const [view, setView] = useState<'map' | 'knows'>('map');
  const {width} = useWindowDimensions();
  const narrow = width < 1000;
  const searchRef = useRef<TextInput>(null);
  const colors = dark ? DARK : LIGHT;

  const hits = useMemo(
    () => (query.trim() ? SEARCH_INDEX.search(query) : []),
    [query],
  );

  const visibleNotes = useMemo(() => {
    if (hits.length > 0) {
      return hits.map(h => h.note);
    }
    if (activeTags.size > 0) {
      return BRAIN.notes.filter(n =>
        n.tags.some(t => activeTags.has(t)),
      );
    }
    return BRAIN.notes;
  }, [hits, activeTags]);

  const selected = selectedStem ? NOTE_BY_STEM[selectedStem] : null;
  const related = selected ? SEARCH_INDEX.related(selected.stem) : [];

  const toggleTag = (tag: string) => {
    setActiveTags(prev => {
      const next = new Set(prev);
      if (next.has(tag)) {
        next.delete(tag);
      } else {
        next.add(tag);
      }
      return next;
    });
  };

  const sidebar = (
    <ScrollView
      style={[
        styles.sidebar,
        {backgroundColor: colors.surface, borderColor: colors.border},
      ]}>
      <Text style={[styles.sectionTitle, {color: colors.text}]}>
        Search — BM25, offline
      </Text>
      <TextInput
        ref={searchRef}
        value={query}
        onChangeText={setQuery}
        placeholder="Search the brain…"
        placeholderTextColor={colors.secondary}
        autoFocus
        onSubmitEditing={() => {
          if (hits[0]) {
            setSelectedStem(hits[0].note.stem);
          }
        }}
        style={[
          styles.searchBox,
          {
            color: colors.text,
            borderColor: colors.border,
            backgroundColor: colors.bg,
          },
        ]}
      />
      {hits.map(h => (
        <TouchableOpacity
          key={h.note.stem}
          onPress={() => setSelectedStem(h.note.stem)}
          style={styles.hitRow}>
          <Text style={[styles.hitTitle, {color: colors.text}]}>
            {h.note.title}
          </Text>
          <Text style={[styles.hitMeta, {color: colors.secondary}]}>
            BM25 {h.score.toFixed(2)}
          </Text>
        </TouchableOpacity>
      ))}

      <Text style={[styles.sectionTitle, {color: colors.text}]}>Brain</Text>
      <Text style={[styles.stat, {color: colors.secondary}]}>
        {BRAIN.notes.length} notes · {TOTAL_LINKS} links ·{' '}
        {BRAIN.clusters.length} clusters · {BRAIN.orphans.length} orphans
      </Text>
      <Text style={[styles.stat, {color: colors.secondary}]}>
        Snapshot {BRAIN.generated.slice(0, 10)} · re-run{' '}
        <Text style={{fontWeight: '700'}}>npm run brain-data</Text> after
        editing notes
      </Text>

      <Text style={[styles.sectionTitle, {color: colors.text}]}>Tags</Text>
      <View style={styles.chips}>
        {Object.entries(TAG_COUNTS)
          .sort((a, b) => b[1] - a[1])
          .map(([tag, count]) => {
            const active = activeTags.has(tag);
            return (
              <TouchableOpacity
                key={tag}
                onPress={() => toggleTag(tag)}
                style={[
                  styles.chip,
                  {
                    backgroundColor: active ? colors.accent : colors.chipBg,
                    borderColor: colors.border,
                  },
                ]}>
                <Text
                  style={{
                    color: active ? '#ffffff' : colors.text,
                    fontSize: 12,
                  }}>
                  #{tag} · {count}
                </Text>
              </TouchableOpacity>
            );
          })}
      </View>

      <Text style={[styles.sectionTitle, {color: colors.text}]}>
        Hubs — start here
      </Text>
      {(BRAIN.hubs ?? []).map(h => (
        <TouchableOpacity
          key={h.stem}
          onPress={() => setSelectedStem(h.stem)}
          style={styles.clusterRow}>
          <Text style={[styles.clusterLabel, {color: colors.text}]}>
            {h.title}
          </Text>
          <Text style={[styles.clusterMembers, {color: colors.secondary}]}>
            {h.degree} links
          </Text>
        </TouchableOpacity>
      ))}

      <Text style={[styles.sectionTitle, {color: colors.text}]}>
        Clusters
      </Text>
      {BRAIN.clusters.map((c, i) => (
        <TouchableOpacity
          key={c.label}
          onPress={() => {
            setActiveTags(new Set());
            setFocusCluster(focusCluster === i ? null : i);
            if (c.members[0]) {
              setSelectedStem(c.members[0]);
            }
          }}
          style={[
            styles.clusterRow,
            {opacity: focusCluster !== null && focusCluster !== i ? 0.45 : 1},
          ]}>
          <Text style={[styles.clusterLabel, {color: colors.text}]}>
            <Text style={{color: CLUSTER_COLORS[i % CLUSTER_COLORS.length]}}>
              ●{' '}
            </Text>
            {c.label}
          </Text>
          <Text style={[styles.clusterMembers, {color: colors.secondary}]}>
            {c.members.join(', ')}
          </Text>
        </TouchableOpacity>
      ))}

      <Text style={[styles.sectionTitle, {color: colors.text}]}>
        Needs attention
      </Text>
      {BRAIN.orphans.length > 0 && (
        <Text style={[styles.attention, {color: colors.secondary}]}>
          Orphans ({BRAIN.orphans.length}): {BRAIN.orphans.join(', ')}
        </Text>
      )}
      {BRAIN.stale.length > 0 && (
        <Text style={[styles.attention, {color: colors.secondary}]}>
          Stale, 90+ days ({BRAIN.stale.length}): {BRAIN.stale.join(', ')}
        </Text>
      )}
      {BRAIN.suggestions.length > 0 && (
        <Text style={[styles.attention, {color: colors.secondary}]}>
          Link suggestions ({BRAIN.suggestions.length}):{' '}
          {BRAIN.suggestions
            .slice(0, 5)
            .map(s => `${s.a} ↔ ${s.b}`)
            .join('; ')}
        </Text>
      )}
      {BRAIN.duplicates.length > 0 && (
        <Text style={[styles.attention, {color: colors.secondary}]}>
          Duplicates ({BRAIN.duplicates.length}):{' '}
          {BRAIN.duplicates.map(d => `${d.a} ~ ${d.b}`).join('; ')}
        </Text>
      )}
      {BRAIN.orphans.length === 0 &&
        BRAIN.stale.length === 0 &&
        BRAIN.suggestions.length === 0 && (
          <Text style={[styles.attention, {color: colors.secondary}]}>
            Nothing needs attention.
          </Text>
        )}
    </ScrollView>
  );

  const reader = (
    <ScrollView
      style={[
        styles.reader,
        {backgroundColor: colors.surface, borderColor: colors.border},
      ]}>
      {selected ? (
        <>
          <Text style={[styles.noteTitle, {color: colors.text}]}>
            {selected.title}
          </Text>
          <Text style={[styles.noteMeta, {color: colors.secondary}]}>
            {selected.stem}.md · {selected.tags.map(t => `#${t}`).join(' ')}
            {' · '}
            {selected.links.length} links out · {selected.incoming.length} in
          </Text>
          <MarkdownView
            text={selected.text}
            colors={{
              text: colors.text,
              secondary: colors.secondary,
              accent: colors.accent,
              codeBg: colors.codeBg,
            }}
            onOpenNote={setSelectedStem}
          />
          <Text style={[styles.sectionTitle, {color: colors.text}]}>
            What Muse knows — sources
          </Text>
          {(() => {
            const kt = KNOWS.topics.find(t => t.stem === selected.stem);
            if (!kt) return null;
            return kt.sources.length > 0 ? (
              <Text style={{fontSize: 13, color: colors.secondary, lineHeight: 19}}>
                Sources: {kt.sources.join(' · ')}
              </Text>
            ) : (
              <Text style={{fontSize: 13, fontWeight: '700', color: '#B45309'}}>
                No source on file — check before trusting.
              </Text>
            );
          })()}
          {related.length > 0 && (
            <>
              <Text style={[styles.sectionTitle, {color: colors.text}]}>
                Related
              </Text>
              {related.map(r => (
                <TouchableOpacity
                  key={r.note.stem}
                  onPress={() => setSelectedStem(r.note.stem)}>
                  <Text style={{color: colors.accent, paddingVertical: 2}}>
                    {r.note.title} ({r.cosine.toFixed(2)})
                  </Text>
                </TouchableOpacity>
              ))}
            </>
          )}
        </>
      ) : (
        <>
          <Text style={[styles.noteTitle, {color: colors.text}]}>
            Welcome to Muse Brain
          </Text>
          <Text style={[styles.welcome, {color: colors.secondary}]}>
            Pick a note from the graph, the search box, or a list.
            Everything here is local — the notes, the search index, and
            the graph all come from the Markdown brain bundled with this
            app. No network, no account, no server.
          </Text>
          <Text style={[styles.welcome, {color: colors.secondary}]}>
            Start with search (ranked by BM25, the same index the Python
            ml/search.py tool uses), or explore a cluster on the left.
          </Text>
        </>
      )}
    </ScrollView>
  );

  if (!signedIn) {
    return <LoginScreen profile={PROFILE} colors={colors} onSignIn={() => setSignedIn(true)} />;
  }

  return (
    <View style={[styles.root, {backgroundColor: colors.bg}]}>
      <View
        style={[
          styles.header,
          {backgroundColor: colors.surface, borderColor: colors.border},
        ]}>
        <Text style={[styles.appTitle, {color: colors.text}]}>
          Muse Brain
        </Text>
        <Text style={[styles.appSub, {color: colors.secondary}]}>
          Memory map · {visibleNotes.length} notes · local · offline
        </Text>
        <View style={{flex: 1}} />
        <TouchableOpacity
          style={[
            styles.themeBtn,
            {borderColor: colors.border},
            showSuggest ? {backgroundColor: colors.accent} : null,
          ]}
          onPress={() => setShowSuggest(s => !s)}>
          <Text style={{color: showSuggest ? '#ffffff' : colors.text}}>
            {showSuggest ? '↔ Suggestions on' : '↔ Suggestions'}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.themeBtn, {borderColor: colors.border, backgroundColor: view === 'knows' ? colors.accent : undefined}]}
          onPress={() => setView(view === 'knows' ? 'map' : 'knows')}>
          <Text style={{color: view === 'knows' ? '#ffffff' : colors.text}}>
            {view === 'knows' ? '✦ What Muse knows' : '✦ Knows'}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.themeBtn, {borderColor: colors.border}]}
          onPress={() => setSignedIn(false)}>
          <Text style={{color: colors.text}}>Sign out</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.themeBtn, {borderColor: colors.border}]}
          onPress={() => setDark(d => !d)}>
          <Text style={{color: colors.text}}>
            {dark ? '☀ Light' : '◐ Dark'}
          </Text>
        </TouchableOpacity>
      </View>
      <View
        style={[
          styles.body,
          {flexDirection: narrow ? 'column' : 'row'},
        ]}>
        {sidebar}
        {view === 'knows' ? (
          <View
            style={[
              styles.graphPane,
              {backgroundColor: colors.surface, borderColor: colors.border},
            ]}>
            <KnowsView
              colors={{
                surface: colors.surface,
                text: colors.text,
                secondary: colors.secondary,
                accent: colors.accent,
                border: colors.border,
                chipBg: colors.chipBg,
              }}
              onOpen={stem => {
                setSelectedStem(stem);
                setView('map');
              }}
            />
          </View>
        ) : (
        <View
          style={[
            styles.graphPane,
            {backgroundColor: colors.surface, borderColor: colors.border},
          ]}>
          <Text style={[styles.sectionTitle, {color: colors.text}]}>
            Memory map
          </Text>
          <GraphView
            selectedStem={selectedStem}
            onSelect={setSelectedStem}
            dark={dark}
            focusCluster={focusCluster}
            showSuggest={showSuggest}
          />
          <Text style={[styles.legend, {color: colors.secondary}]}>
            {BRAIN.clusters.slice(0, 4).map(c => c.label.split(',')[0]).join(' · ')}
            {' · '}ring = hub (6+) · dashed = quiet note
          </Text>
        </View>
        )}
        {reader}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {flex: 1},
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    gap: 12,
  },
  appTitle: {fontSize: 20, fontWeight: '700'},
  appSub: {fontSize: 13},
  themeBtn: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  body: {flex: 1, gap: 0},
  sidebar: {width: 300, borderRightWidth: 1, padding: 12},
  graphPane: {flex: 1, borderRightWidth: 1, padding: 12, minHeight: 320},
  reader: {width: 400, padding: 16},
  sectionTitle: {fontSize: 13, fontWeight: '700', marginTop: 14, marginBottom: 6},
  searchBox: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 14,
  },
  hitRow: {paddingVertical: 6, borderBottomWidth: 0},
  hitTitle: {fontSize: 14, fontWeight: '600'},
  hitMeta: {fontSize: 12},
  stat: {fontSize: 13, lineHeight: 19, marginBottom: 4},
  chips: {flexDirection: 'row', flexWrap: 'wrap', gap: 6},
  chip: {borderWidth: 1, borderRadius: 999, paddingHorizontal: 9, paddingVertical: 4},
  clusterRow: {paddingVertical: 5},
  clusterLabel: {fontSize: 13, fontWeight: '600'},
  clusterMembers: {fontSize: 12, lineHeight: 17},
  attention: {fontSize: 12, lineHeight: 18, marginBottom: 4},
  legend: {fontSize: 12, marginTop: 8},
  noteTitle: {fontSize: 26, fontWeight: '700', marginBottom: 4},
  noteMeta: {fontSize: 12, marginBottom: 12},
  welcome: {fontSize: 15, lineHeight: 22, marginBottom: 10},
});
