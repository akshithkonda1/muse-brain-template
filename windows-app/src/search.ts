// search.ts — local ML search, ported from ml/search.py.
//
// Same math as the Python baseline and the Swift app: BM25 (primary)
// + TF-IDF cosine (second signal), greedy topic clusters, Jaccard +
// cosine duplicates. Stdlib JS only. No network, no API, no model.

import {BRAIN, NoteData} from './brain';

const STOPWORDS = new Set(
  ('a an the and or of to in on for with is are was were be by at as it its ' +
    'this that these those from into over under after before not no nor but ' +
    'if then than so such can could will would should he she they we you i ' +
    'his her their our your my me him them us what which who whom when where ' +
    'why how all any both each few more most other some such only own same ' +
    'too very just also').split(' '),
);

export function tokenize(text: string): string[] {
  const cleaned = text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/\[\[([^\]|#]+)(?:#[^\]]*)?(?:\|[^\]]*)?\]\]/g, (_m, g1: string) =>
      ' ' + g1.replace(/-/g, ' ') + ' ',
    )
    .replace(/[#*`>\[\]()|_]/g, ' ');
  return (cleaned.toLowerCase().match(/[a-z0-9']+/g) ?? []).filter(
    w => !STOPWORDS.has(w) && w.length > 1,
  );
}

export class Index {
  private docs: NoteData[];
  private idf: Record<string, number> = {};
  private avgdl = 0;
  private tfidf: Record<string, Record<string, number>> = {};
  private counts: Record<string, Record<string, number>> = {};
  private docLen: Record<string, number> = {};
  private k1 = 1.5;
  private b = 0.75;

  constructor(docs: NoteData[]) {
    this.docs = docs;
    const df: Record<string, number> = {};
    for (const doc of docs) {
      const c: Record<string, number> = {};
      for (const t of tokenize(doc.text)) {
        c[t] = (c[t] ?? 0) + 1;
      }
      this.counts[doc.stem] = c;
      this.docLen[doc.stem] = Object.values(c).reduce((a, x) => a + x, 0);
      for (const term of Object.keys(c)) {
        df[term] = (df[term] ?? 0) + 1;
      }
    }
    const n = Math.max(docs.length, 1);
    for (const [term, d] of Object.entries(df)) {
      this.idf[term] = Math.log((n - d + 0.5) / (d + 0.5) + 1);
    }
    this.avgdl =
      docs.length === 0
        ? 0
        : Object.values(this.docLen).reduce((a, x) => a + x, 0) / docs.length;
    for (const doc of docs) {
      const vec: Record<string, number> = {};
      for (const [term, tf] of Object.entries(this.counts[doc.stem])) {
        vec[term] = (1 + Math.log(tf)) * (this.idf[term] ?? 0);
      }
      const norm = Math.sqrt(
        Object.values(vec).reduce((a, v) => a + v * v, 0),
      );
      this.tfidf[doc.stem] =
        norm > 0
          ? Object.fromEntries(Object.entries(vec).map(([t, v]) => [t, v / norm]))
          : vec;
    }
  }

  private cosine(a: Record<string, number>, b: Record<string, number>): number {
    let sum = 0;
    const [small, large] = Object.keys(a).length <= Object.keys(b).length ? [a, b] : [b, a];
    for (const [term, v] of Object.entries(small)) {
      sum += v * (large[term] ?? 0);
    }
    return sum;
  }

  search(
    query: string,
    top = 8,
  ): {note: NoteData; score: number; bm25: number; cosine: number}[] {
    const qterms = tokenize(query);
    if (qterms.length === 0) {
      return [];
    }
    const qcounts: Record<string, number> = {};
    for (const t of qterms) {
      qcounts[t] = (qcounts[t] ?? 0) + 1;
    }
    const qvec: Record<string, number> = {};
    for (const [term, tf] of Object.entries(qcounts)) {
      if (term in this.idf) {
        qvec[term] = (1 + Math.log(tf)) * this.idf[term];
      }
    }
    const qnorm = Math.sqrt(Object.values(qvec).reduce((a, v) => a + v * v, 0));
    if (qnorm > 0) {
      for (const t of Object.keys(qvec)) {
        qvec[t] /= qnorm;
      }
    }
    const out: {note: NoteData; score: number; bm25: number; cosine: number}[] = [];
    for (const doc of this.docs) {
      let bm25 = 0;
      const dl = this.docLen[doc.stem] ?? 1;
      for (const term of new Set(qterms)) {
        const tf = this.counts[doc.stem]?.[term] ?? 0;
        if (tf === 0 || !(term in this.idf)) {
          continue;
        }
        const denom =
          tf + this.k1 * (1 - this.b + (this.b * dl) / Math.max(this.avgdl, 1));
        bm25 += this.idf[term] * ((tf * (this.k1 + 1)) / denom);
      }
      const cos = this.cosine(qvec, this.tfidf[doc.stem] ?? {});
      const score = bm25 + cos;
      if (score > 0) {
        out.push({note: doc, score, bm25, cosine: cos});
      }
    }
    return out.sort((x, y) => y.score - x.score).slice(0, top);
  }

  related(stem: string, top = 5): {note: NoteData; cosine: number}[] {
    const target = this.tfidf[stem];
    if (!target) {
      return [];
    }
    return this.docs
      .filter(d => d.stem !== stem)
      .map(d => ({note: d, cosine: this.cosine(target, this.tfidf[d.stem] ?? {})}))
      .filter(r => r.cosine > 0)
      .sort((x, y) => y.cosine - x.cosine)
      .slice(0, top);
  }
}

export const SEARCH_INDEX = new Index(BRAIN.notes);
