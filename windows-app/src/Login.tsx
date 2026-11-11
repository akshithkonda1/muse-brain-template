// Login.tsx — the sign-in screen for the Muse Brain Windows app.
//
// Your Muse Brain is a digital copy of your information: after you
// sign in, it builds an interactive memory map from your notes and
// lets you see what Muse knows about you. The login is the door
// into *your* copy — nobody else's.
//
// Honest limitation, stated in the UI and in docs/login.md: there
// is NO public Meta / Muse sign-in endpoint for a local brain yet.
// "Sign in with Muse" is therefore a clearly-labelled placeholder —
// it explains that, sends nothing anywhere, and collects no
// password. The working sign-in is "Continue locally" as the
// profile bundled with this app.
// Session-only in v1: no persistent store is bundled, so closing
// the app ends the session. There is no passcode step in the
// Windows build yet — the screen says so plainly.

import React, {useState} from 'react';
import {StyleSheet, Text, TouchableOpacity, View} from 'react-native';
import type {ProfileData} from './brain';

export function LoginScreen({
  profile,
  colors,
  onSignIn,
}: {
  profile: ProfileData;
  colors: {
    bg: string;
    surface: string;
    text: string;
    secondary: string;
    accent: string;
    border: string;
  };
  onSignIn: () => void;
}) {
  const [showMuseNotice, setShowMuseNotice] = useState(false);
  return (
    <View
      style={[
        styles.root,
        {backgroundColor: colors.bg},
      ]}>
      <View
        style={[
          styles.card,
          {backgroundColor: colors.surface, borderColor: colors.border},
        ]}>
        <Text style={[styles.eyebrow, {color: colors.accent}]}>
          Muse Brain · Your digital copy
        </Text>
        <Text style={[styles.title, {color: colors.text}]}>
          Sign in to your Muse Brain.
        </Text>
        <Text style={[styles.lead, {color: colors.secondary}]}>
          {profile.demo
            ? 'A demo digital copy — generic example notes only, nothing personal. Sign in to explore what Muse knows in this example brain.'
            : 'Your information, as an interactive memory map — what Muse knows about you, with the sources to check it.'}
        </Text>
        <TouchableOpacity
          style={[styles.primaryBtn, {backgroundColor: colors.accent}]}
          onPress={onSignIn}>
          <Text style={styles.primaryText}>
            {profile.demo
              ? 'Try the demo — continue locally'
              : `Continue locally as ${profile.display_name}`}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.secondaryBtn, {borderColor: colors.border}]}
          onPress={() => setShowMuseNotice(true)}>
          <Text style={{color: colors.text}}>Sign in with Muse</Text>
        </TouchableOpacity>
        {showMuseNotice && (
          <Text style={[styles.notice, {color: colors.secondary}]}>
            Sign in with Muse is coming soon. Muse is Meta's personal AI
            agent, and there is no public Muse / Meta sign-in endpoint
            for a local brain yet — so this button cannot log you in
            today, and it will not collect a password or send anything
            anywhere. It will connect for real when Meta publishes one.
            For now, continue locally above.
          </Text>
        )}
        <Text style={[styles.privacy, {color: colors.secondary}]}>
          🔒 Everything stays on this device. No account is created, no
          notes leave this device, no password is sent anywhere.
          Closing the app ends the session — the Windows build does not
          store a passcode yet.
          {profile.demo ? ' Demo: this copy holds only generic example notes.' : ''}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24},
  card: {
    maxWidth: 520,
    width: '100%',
    borderWidth: 1,
    borderRadius: 20,
    padding: 28,
  },
  eyebrow: {fontSize: 11, fontWeight: '700', letterSpacing: 1},
  title: {fontSize: 30, fontWeight: '700', marginTop: 6, marginBottom: 8},
  lead: {fontSize: 15, lineHeight: 22, marginBottom: 18},
  primaryBtn: {
    borderRadius: 12,
    paddingVertical: 13,
    alignItems: 'center',
    marginVertical: 5,
  },
  primaryText: {color: '#ffffff', fontSize: 16, fontWeight: '700'},
  secondaryBtn: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    marginVertical: 5,
  },
  notice: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 10,
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
  },
  privacy: {fontSize: 12, lineHeight: 18, marginTop: 14},
});
