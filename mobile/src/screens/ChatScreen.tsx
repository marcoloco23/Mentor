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
  TouchableOpacity,
} from 'react-native';
import { Text, IconButton } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { streamMessage, getChatLog, ChatLogMessage } from '../api/mentorApi';
import MessageList from '../components/MessageList';
import Composer from '../components/Composer';
import Sidebar from '../components/Sidebar';
import type { Message } from '../components/ChatBubble';
import { getTheme } from '../utils/theme';
import * as Haptics from 'expo-haptics';
import * as Clipboard from 'expo-clipboard';

// User profiles with avatars and display names
const USER_PROFILES = {
  default: { name: 'Default User', avatar: '👤' },
  user1: { name: 'Alice', avatar: '👩‍💼' },
  user2: { name: 'Bob', avatar: '👨‍💻' },
  user3: { name: 'Charlie', avatar: '🧑‍🔬' },
};

// Initial message to send when starting a new chat with no history
const INITIAL_MESSAGE = "I'm here for you. Whenever you're ready, we'll begin.";

const ChatScreen: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [isTestMode, setIsTestMode] = useState(true);
  const [userId, setUserId] = useState<string>('default');
  const [sidebarVisible, setSidebarVisible] = useState(false);
  const [themeMode, setThemeMode] = useState<'system' | 'light' | 'dark'>('system');

  const flatListRef = useRef<any>(null);
  const systemScheme = useColorScheme();
  
  // Determine effective theme based on mode selection
  const effectiveScheme = themeMode === 'system' ? systemScheme : themeMode;
  const theme = getTheme(effectiveScheme);
  const insets = useSafeAreaInsets();

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
    loadChatLog();
  }, [userId]);

  const loadChatLog = async () => {
    try {
      const log: ChatLogMessage[] = await getChatLog(userId);
      setMessages(
        log.map((m, i) => ({
          id: `${i}-${m.role}`,
          role: m.role,
          text: m.content,
          ts: new Date(m.timestamp).getTime(),
        }))
      );
      
      // If there are no messages for this user, send an initial message to start the conversation
      if (log.length === 0) {
        setTimeout(() => {
          sendInitialMessage();
        }, 500); // Small delay for better UX
      }
    } catch (e) {
      console.error('Failed to fetch chat log:', e);
      alert('Failed to fetch chat log: ' + e);
    }
  };

  const sendInitialMessage = async () => {
    if (typing) return;
    
    addMsg({ id: 'typing', role: 'typing', text: '...', ts: Date.now() });
    setTyping(true);
    
    // Simulate typing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setMessages((prev) =>
      prev.map((m) =>
        m.role === 'typing'
          ? { id: Date.now() + '-a', role: 'assistant', text: INITIAL_MESSAGE, ts: Date.now() }
          : m,
      ),
    );
    
    setTyping(false);
  };

  const handleUserChange = (newUserId: string) => {
    if (newUserId !== userId) {
      setUserId(newUserId);
      setMessages([]);
    }
    setSidebarVisible(false);
  };

  const handleSidebarToggle = async () => {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setSidebarVisible(!sidebarVisible);
  };

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
      await streamMessage({ 
        message: text, 
        test_mode: isTestMode,
        user_id: userId 
      }, (chunk) => {
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

  /*────────────────── attachment handling ──────────────────*/
  const handleAttachment = () => {
    // Placeholder for attachment functionality
    // This could open a file picker, image gallery, etc.
    alert('Attachment functionality can be implemented here');
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
    <View style={[styles.root, { backgroundColor: theme.background, paddingTop: insets.top }]}>
      {/* Clean minimal header with just hamburger menu */}
      <View style={[styles.headerRow, { backgroundColor: theme.background, borderBottomColor: theme.border + '15' }]}>
        <TouchableOpacity
          onPress={handleSidebarToggle}
          style={styles.menuButton}
          activeOpacity={0.6}
        >
          <IconButton 
            icon="menu" 
            size={24} 
            iconColor={theme.text}
            style={styles.menuIcon}
          />
        </TouchableOpacity>
        
        <View style={styles.headerCenter}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Ted
          </Text>
          {isTestMode && (
            <View style={[styles.testBadge, { backgroundColor: theme.primary + '20' }]}>
              <Text style={[styles.testBadgeText, { color: theme.primary }]}>
                TEST
              </Text>
            </View>
          )}
        </View>
        
        <View style={styles.headerRight} />
      </View>

      {/* Sidebar */}
      <Sidebar
        visible={sidebarVisible}
        onClose={() => setSidebarVisible(false)}
        userId={userId}
        onUserChange={handleUserChange}
        isTestMode={isTestMode}
        onTestModeChange={setIsTestMode}
        themeMode={themeMode}
        onThemeModeChange={setThemeMode}
        effectiveScheme={effectiveScheme}
      />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
      >
        <View style={[styles.flex, { paddingBottom: insets.bottom }]} {...panResponder.panHandlers}>
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
            onAttachment={handleAttachment}
          />
        </View>
      </KeyboardAvoidingView>
    </View>
  );
};

const styles = StyleSheet.create({
  root: { flex: 1 },
  flex: { flex: 1 },
  headerRow: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingHorizontal: 4,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    minHeight: 56,
  },
  menuButton: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  menuIcon: {
    margin: 0,
  },
  headerCenter: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: -0.3,
  },
  testBadge: {
    marginLeft: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  testBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  headerRight: {
    width: 48,
  },
});

export default ChatScreen;