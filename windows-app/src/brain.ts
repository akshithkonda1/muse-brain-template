// brain.ts — the brain's data, as bundled by scripts/generate-brain-data.py.
//
// The Markdown files are the source of truth; `brain-data.json` is a
// generated snapshot of them (same role as dashboard.html's embedded
// data). Re-run `npm run brain-data` after editing notes, before
// building the .exe. Nothing here touches the network.

import brainData from './brain-data.json';

export interface NoteData {
  stem: string;
  title: string;
  tags: string[];
  links: string[];
  text: string;
  area: string;
  mtime: number;
  incoming: string[];
}

export interface ClusterData {
  label: string;
  members: string[];
}

export interface SuggestionData {
  a: string;
  b: string;
  cosine: number;
  shared_tags: string[];
}

export interface DuplicateData {
  a: string;
  b: string;
  kind: string;
  score: number;
}

export interface HubData {
  stem: string;
  title: string;
  degree: number;
}

export interface BrainData {
  generated: string;
  source: string;
  notes: NoteData[];
  positions: Record<string, [number, number]>;
  clusters: ClusterData[];
  clusterColors: string[];
  clusterIndex: Record<string, number>;
  hubs: HubData[];
  suggestions: SuggestionData[];
  orphans: string[];
  broken: [string, string][];
  stale: string[];
  duplicates: DuplicateData[];
}

export const BRAIN: BrainData = brainData as unknown as BrainData;

export const NOTE_BY_STEM: Record<string, NoteData> = Object.fromEntries(
  BRAIN.notes.map(n => [n.stem, n]),
);

export const TAG_COUNTS: Record<string, number> = (() => {
  const counts: Record<string, number> = {};
  for (const note of BRAIN.notes) {
    for (const tag of note.tags) {
      counts[tag] = (counts[tag] ?? 0) + 1;
    }
  }
  return counts;
})();

export const TOTAL_LINKS = BRAIN.notes.reduce((s, n) => s + n.links.length, 0);

/** Shared cluster palette (docs/design-system.md) — same order as the
 *  dashboard and the Mac app. Colour is cluster rank, largest first. */
export const CLUSTER_COLORS: string[] = BRAIN.clusterColors ?? [
  '#7C5CFF', '#14B8A6', '#F59E0B', '#F43F5E',
  '#0EA5E9', '#10B981', '#F97316', '#6366F1',
];

export function clusterColorFor(stem: string, tags: string[]): string {
  const ci = (BRAIN.clusterIndex ?? {})[stem];
  if (ci !== undefined) {
    return CLUSTER_COLORS[ci % CLUSTER_COLORS.length];
  }
  const sortedTags = [...new Set(BRAIN.notes.flatMap(n => n.tags))].sort();
  const idx = Math.max(0, sortedTags.indexOf(tags[0] ?? 'notes'));
  return CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
}

export function degreeOf(stem: string): number {
  const note = NOTE_BY_STEM[stem];
  return (note ? note.links.length : 0) + (note ? note.incoming.length : 0);
}
