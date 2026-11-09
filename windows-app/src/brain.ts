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

export interface BrainData {
  generated: string;
  source: string;
  notes: NoteData[];
  positions: Record<string, [number, number]>;
  clusters: ClusterData[];
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
