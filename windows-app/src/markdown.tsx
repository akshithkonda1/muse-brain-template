// markdown.tsx — a tiny Markdown renderer to React Native Text.
//
// Headings, bold/italic, `code`, code fences, bullets, and [[links]]
// (pressable, navigates inside the app). No dependency, no WebView,
// works offline. Not a full Markdown engine — good enough for notes.

import React from 'react';
import {Text, View, StyleSheet} from 'react-native';

export interface MdColors {
  text: string;
  secondary: string;
  accent: string;
  codeBg: string;
}

type InlinePart =
  | {kind: 'text'; text: string}
  | {kind: 'bold'; text: string}
  | {kind: 'italic'; text: string}
  | {kind: 'code'; text: string}
  | {kind: 'link'; text: string; stem: string};

/** Split one line's inline markup into parts. */
function inlineParts(line: string): InlinePart[] {
  const parts: InlinePart[] = [];
  const re =
    /\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[\[([^\]|#]+)(?:#[^\]]*)?(?:\|[^\]]*)?\]\]/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(line)) !== null) {
    if (m.index > last) {
      parts.push({kind: 'text', text: line.slice(last, m.index)});
    }
    if (m[1] !== undefined) {
      parts.push({kind: 'bold', text: m[1]});
    } else if (m[2] !== undefined) {
      parts.push({kind: 'italic', text: m[2]});
    } else if (m[3] !== undefined) {
      parts.push({kind: 'code', text: m[3]});
    } else if (m[4] !== undefined) {
      const target = m[4].trim();
      parts.push({
        kind: 'link',
        text: target,
        stem: target.toLowerCase().replace(/ /g, '-'),
      });
    }
    last = m.index + m[0].length;
  }
  if (last < line.length) {
    parts.push({kind: 'text', text: line.slice(last)});
  }
  return parts;
}

export function MarkdownView({
  text,
  colors,
  onOpenNote,
}: {
  text: string;
  colors: MdColors;
  onOpenNote: (stem: string) => void;
}) {
  const lines = text.split('\n');
  const blocks: React.ReactNode[] = [];
  let inFence = false;
  let fence: string[] = [];
  let key = 0;

  const renderInline = (line: string, style: object) => (
    <Text style={style}>
      {inlineParts(line).map((p, i) => {
        switch (p.kind) {
          case 'bold':
            return (
              <Text key={i} style={{fontWeight: '700'}}>
                {p.text}
              </Text>
            );
          case 'italic':
            return (
              <Text key={i} style={{fontStyle: 'italic'}}>
                {p.text}
              </Text>
            );
          case 'code':
            return (
              <Text
                key={i}
                style={{fontFamily: 'Consolas', backgroundColor: colors.codeBg}}>
                {p.text}
              </Text>
            );
          case 'link':
            return (
              <Text
                key={i}
                style={{color: colors.accent, textDecorationLine: 'underline'}}
                onPress={() => onOpenNote(p.stem)}>
                {p.text}
              </Text>
            );
          default:
            return <Text key={i}>{p.text}</Text>;
        }
      })}
    </Text>
  );

  for (const line of lines) {
    key += 1;
    if (line.trimStart().startsWith('```')) {
      if (inFence) {
        blocks.push(
          <View
            key={key}
            style={[styles.codeBlock, {backgroundColor: colors.codeBg}]}>
            <Text style={{fontFamily: 'Consolas', color: colors.text}}>
              {fence.join('\n')}
            </Text>
          </View>,
        );
        fence = [];
        inFence = false;
      } else {
        inFence = true;
      }
      continue;
    }
    if (inFence) {
      fence.push(line);
      continue;
    }
    const h1 = line.match(/^# (.+)/);
    const h2 = line.match(/^## (.+)/);
    const h3 = line.match(/^### (.+)/);
    const bullet = line.match(/^[-*] (.+)/);
    const numbered = line.match(/^\d+\. (.+)/);
    if (h1) {
      blocks.push(
        <View key={key}>
          {renderInline(h1[1], [styles.h1, {color: colors.text}])}
        </View>,
      );
    } else if (h2) {
      blocks.push(
        <View key={key}>
          {renderInline(h2[1], [styles.h2, {color: colors.text}])}
        </View>,
      );
    } else if (h3) {
      blocks.push(
        <View key={key}>
          {renderInline(h3[1], [styles.h3, {color: colors.text}])}
        </View>,
      );
    } else if (bullet || numbered) {
      const body = (bullet ?? numbered)![1];
      blocks.push(
        <View key={key} style={styles.bulletRow}>
          <Text style={{color: colors.secondary}}>
            {bullet ? '•  ' : '–  '}
          </Text>
          {renderInline(body, [styles.body, {color: colors.text}])}
        </View>,
      );
    } else if (line.trim() === '') {
      blocks.push(<View key={key} style={{height: 8}} />);
    } else {
      blocks.push(
        <View key={key}>
          {renderInline(line, [styles.body, {color: colors.text}])}
        </View>,
      );
    }
  }
  return <View>{blocks}</View>;
}

const styles = StyleSheet.create({
  h1: {fontSize: 26, fontWeight: '700', marginTop: 8, marginBottom: 6},
  h2: {fontSize: 20, fontWeight: '700', marginTop: 10, marginBottom: 4},
  h3: {fontSize: 16, fontWeight: '700', marginTop: 8, marginBottom: 2},
  body: {fontSize: 15, lineHeight: 22},
  bulletRow: {flexDirection: 'row', marginLeft: 8},
  codeBlock: {padding: 10, borderRadius: 6, marginVertical: 6},
});
