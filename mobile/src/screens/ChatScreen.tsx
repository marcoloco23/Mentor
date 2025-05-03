// ChatScreen.tsx
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Pressable,
  useColorScheme,
  SafeAreaView,
} from 'react-native';
import { TextInput, IconButton, Text, Switch } from 'react-native-paper';
import { streamMessage, getChatLog, ChatLogMessage } from '../api/mentorApi';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'typing';
  text: string;
  ts?: number;
}

const ChatScreen: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [isTestMode, setIsTestMode] = useState(true);

  const flatListRef = useRef<FlatList>(null);
  const scheme = useColorScheme();

  /*────────────────── helpers ──────────────────*/
  const scrollToEnd = () =>
    flatListRef.current?.scrollToOffset({ offset: 0, animated: true });

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
        // Optionally handle error
      }
    })();
  }, []);

  /*────────────────── send & stream ──────────────────*/
  const doSend = async () => {
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
    // Works only on web; native iOS/Android ignore shiftKey anyway
    if (
      Platform.OS === 'web' &&
      e.nativeEvent.key === 'Enter' &&
      !e.nativeEvent.shiftKey
    ) {
      e.preventDefault?.();
      doSend();
    }
  };

  /*────────────────── render ──────────────────*/
  const renderItem = ({ item }: { item: Message }) => {
    const isUser = item.role === 'user';
    const bubbleStyle = [
      styles.bubble,
      isUser ? styles.userBubble : styles.botBubble,
      scheme === 'dark' && styles[`bubble${isUser ? 'User' : 'Bot'}Dark`],
    ];
    const textStyle = [
      isUser ? styles.userText : styles.botText,
      scheme === 'dark' && (isUser ? styles.bubbleUserDarkText : styles.bubbleBotDarkText),
    ];

    return (
      <Pressable
        onLongPress={() => item.ts && alert(new Date(item.ts).toLocaleString())}
        onPress={() =>
          navigator.clipboard && navigator.clipboard.writeText(item.text)
        }
        style={{ alignSelf: isUser ? 'flex-end' : 'flex-start', maxWidth: '80%' }}
      >
        <View style={bubbleStyle}>
          <Text selectable style={textStyle}>
            {item.text}
          </Text>
        </View>
      </Pressable>
    );
  };

  /*────────────────── UI ──────────────────*/
  return (
    <SafeAreaView style={[styles.root, scheme === 'dark' && styles.rootDark]}>
      {/* Test-mode toggle */}
      <View style={styles.toggleRow}>
        <Text style={styles.toggleLabel}>Test Mode</Text>
        <Switch value={isTestMode} onValueChange={setIsTestMode} />
        <Text style={styles.toggleState}>{isTestMode ? 'ON' : 'OFF'}</Text>
      </View>

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={80}
      >
        <FlatList
          ref={flatListRef}
          data={[...messages].reverse()}
          inverted
          keyExtractor={(m) => m.id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
        />

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Ask your mentor…"
            multiline
            blurOnSubmit={false}
            onSubmitEditing={Platform.OS !== 'web' ? doSend : undefined}
            onKeyPress={handleKeyPress}
          />
          <IconButton
            icon="send"
            disabled={!input.trim() || typing}
            onPress={doSend}
            size={28}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

/*────────────────── styles ──────────────────*/
const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#F5F7FA' },
  rootDark: { backgroundColor: '#181A20' },
  flex: { flex: 1 },
  list: { padding: 12, gap: 6 },

  toggleRow: { flexDirection: 'row', alignItems: 'center', padding: 10 },
  toggleLabel: { marginRight: 6, fontWeight: '500' },
  toggleState: { marginLeft: 6, opacity: 0.7 },

  bubble: {
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 12,
    marginVertical: 2,
    shadowColor: '#000',
    shadowOpacity: 0.07,
    shadowRadius: 2,
    elevation: 1,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.04)',
  },
  userBubble: { backgroundColor: '#E6F0FF', alignSelf: 'flex-end', borderColor: '#B3C6FF' },
  botBubble: { backgroundColor: '#F5F5F7', alignSelf: 'flex-start', borderColor: '#E0E0E0' },
  bubbleUserDark: { backgroundColor: '#223366', borderColor: '#3A4A6B' },
  bubbleBotDark: { backgroundColor: '#23272F', borderColor: '#353A45' },

  userText: { color: '#1A237E', fontSize: 17, lineHeight: 22, fontWeight: '500' },
  botText: { color: '#222', fontSize: 17, lineHeight: 22 },
  bubbleUserDarkText: { color: '#fff' },
  bubbleBotDarkText: { color: '#F5F5F7' },

  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: 'transparent',
  },
  input: { flex: 1, backgroundColor: 'transparent', paddingHorizontal: 0 },
});

export default ChatScreen;