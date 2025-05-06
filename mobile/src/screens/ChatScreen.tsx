// ChatScreen.tsx
import React, { useState, useRef, useEffect, RefObject } from 'react';
import {
  View,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  useColorScheme,
  SafeAreaView,
  FlatList,
  Keyboard,
  PanResponder,
  GestureResponderEvent,
  PanResponderGestureState,
} from 'react-native';
import { Text, Switch } from 'react-native-paper';
import { streamMessage, getChatLog, ChatLogMessage } from '../api/mentorApi';
import MessageList from '../components/MessageList';
import Composer from '../components/Composer';
import type { Message } from '../components/ChatBubble';
import { getTheme } from '../utils/theme';
import * as Haptics from 'expo-haptics';
import * as Clipboard from 'expo-clipboard';

const ChatScreen: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [isTestMode, setIsTestMode] = useState(true);

  const flatListRef = useRef<any>(null);
  const scheme = useColorScheme();
  const theme = getTheme(scheme);

  /*────────────────── helpers ──────────────────*/
  const scrollToEnd = () => {
    if (flatListRef.current && flatListRef.current.scrollToIndex) {
      flatListRef.current.scrollToIndex({ index: 0, animated: true });
    }
  };

  const addMsg = (msg: Message) =>
    setMessages((prev) => [...prev, msg].slice(-200));

  const replaceTyping = (txt: string) =>
    setMessages((prev) =>
      prev.map((m) => (m.role === 'typing' ? { ...m, text: txt } : m)),
    );

  useEffect(scrollToEnd, [messages]);

  useEffect(() => {
    (async () => {
      try {
        const log: ChatLogMessage[] = await getChatLog();
        setMessages(
          log.map((m, i) => ({
            id: `${i}-${m.role}`,
            role: m.role,
            text: m.content,
            ts: new Date(m.timestamp).getTime(),
          }))
        );
      } catch (e) {
        console.error('Failed to fetch chat log:', e);
        alert('Failed to fetch chat log: ' + e);
      }
    })();
  }, []);

  /*────────────────── send & stream ──────────────────*/
  const doSend = async () => {
    Keyboard.dismiss();
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const text = input.trim();
    if (!text || typing) return;

    setInput('');
    addMsg({ id: Date.now() + '-u', role: 'user', text, ts: Date.now() });
    addMsg({ id: 'typing', role: 'typing', text: '...', ts: Date.now() });
    setTyping(true);

    let streamed = '';
    try {
      await streamMessage({ message: text, test_mode: isTestMode }, (chunk) => {
        streamed += chunk;
        replaceTyping(streamed);
      });

      setMessages((prev) =>
        prev.map((m) =>
          m.role === 'typing'
            ? { id: Date.now() + '-a', role: 'assistant', text: streamed, ts: Date.now() }
            : m,
        ),
      );
    } catch {
      replaceTyping('❌  Error: could not reach server.');
    } finally {
      setTyping(false);
    }
  };

  /*────────────────── key-handling (web) ──────────────────*/
  const handleKeyPress = (e: any) => {
    if (
      Platform.OS === 'web' &&
      e.nativeEvent.key === 'Enter' &&
      !e.nativeEvent.shiftKey
    ) {
      e.preventDefault?.();
      doSend();
    }
  };

  /*────────────────── UI ──────────────────*/
  // PanResponder for gesture-based keyboard dismissal
  const panResponder = PanResponder.create({
    onMoveShouldSetPanResponder: (
      _evt: GestureResponderEvent,
      gestureState: PanResponderGestureState
    ) => {
      // Only set responder if user is dragging down
      return gestureState.dy > 10;
    },
    onPanResponderMove: () => {},
    onPanResponderRelease: (
      _evt: GestureResponderEvent,
      gestureState: PanResponderGestureState
    ) => {
      if (gestureState.dy > 10) {
        Keyboard.dismiss();
      }
    },
  });

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: theme.background }]}>
      {/* Test-mode toggle */}
      <View style={[styles.toggleRow, { backgroundColor: theme.toggleBackground }]} accessible accessibilityRole="switch">
        <Text style={[styles.toggleLabel, { color: theme.textSecondary }]}>Test Mode</Text>
        <Switch
          value={isTestMode}
          onValueChange={setIsTestMode}
          accessibilityLabel="Toggle test mode"
          accessible
        />
        <Text style={[styles.toggleState, { color: theme.text }]}>{isTestMode ? 'ON' : 'OFF'}</Text>
      </View>

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={20}
      >
        <View style={styles.flex} {...panResponder.panHandlers}>
          <MessageList
            messages={messages}
            flatListRef={flatListRef}
            onBubblePress={(msg) => {
              if (Platform.OS === 'web' && navigator.clipboard) {
                navigator.clipboard.writeText(msg.text);
              } else {
                Clipboard.setStringAsync(msg.text);
              }
            }}
            onBubbleLongPress={async (msg) => {
              await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              if (Platform.OS === 'web' && navigator.clipboard) {
                navigator.clipboard.writeText(msg.text);
              } else {
                await Clipboard.setStringAsync(msg.text);
              }
            }}
          />
          <Composer
            value={input}
            onChangeText={setInput}
            onSend={doSend}
            disabled={typing}
            typing={typing}
            onKeyPress={handleKeyPress}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  root: { flex: 1 },
  flex: { flex: 1 },
  toggleRow: { flexDirection: 'row', alignItems: 'center', padding: 10 },
  toggleLabel: { marginRight: 6, fontWeight: '500' },
  toggleState: { marginLeft: 6, opacity: 0.7 },
});

export default ChatScreen;