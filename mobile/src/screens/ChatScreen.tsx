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
import { Text, Switch, Button, Menu, Divider, TextInput, Modal, Portal, Avatar, IconButton } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { streamMessage, getChatLog, ChatLogMessage } from '../api/mentorApi';
import MessageList from '../components/MessageList';
import Composer from '../components/Composer';
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
  const [userMenuVisible, setUserMenuVisible] = useState(false);
  const [customUserDialogVisible, setCustomUserDialogVisible] = useState(false);
  const [customUserId, setCustomUserId] = useState('');

  const flatListRef = useRef<any>(null);
  const scheme = useColorScheme();
  const theme = getTheme(scheme);
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

  const switchUser = (newUserId: string) => {
    if (newUserId !== userId) {
      setUserId(newUserId);
      setMessages([]);
    }
    setUserMenuVisible(false);
  };

  const handleCustomUserSubmit = () => {
    if (customUserId.trim()) {
      switchUser(customUserId.trim());
      setCustomUserId('');
      setCustomUserDialogVisible(false);
    }
  };

  const getUserProfile = (id: string) => {
    return USER_PROFILES[id as keyof typeof USER_PROFILES] || { name: id, avatar: '👤' };
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
      {/* Enhanced header row with user profile and test mode */}
      <View style={[styles.headerRow, { backgroundColor: theme.toggleBackground }]}>
        <View style={styles.userSelector}>
          <Menu
            visible={userMenuVisible}
            onDismiss={() => setUserMenuVisible(false)}
            anchor={
              <TouchableOpacity 
                onPress={() => setUserMenuVisible(true)}
                style={styles.userButton}
              >
                <View style={styles.userProfile}>
                  <Text style={[styles.userAvatar, { color: theme.text }]}>
                    {getUserProfile(userId).avatar}
                  </Text>
                  <View style={styles.userInfo}>
                    <Text style={[styles.userName, { color: theme.text }]}>
                      {getUserProfile(userId).name}
                    </Text>
                    <Text style={[styles.userIdText, { color: theme.textSecondary }]}>
                      ID: {userId}
                    </Text>
                  </View>
                  <IconButton 
                    icon="chevron-down" 
                    size={20} 
                    iconColor={theme.textSecondary}
                  />
                </View>
              </TouchableOpacity>
            }
          >
            {Object.entries(USER_PROFILES).map(([id, profile]) => (
              <Menu.Item
                key={id}
                onPress={() => switchUser(id)}
                title={profile.name}
                leadingIcon={() => (
                  <Text style={styles.menuAvatar}>{profile.avatar}</Text>
                )}
                style={userId === id ? styles.activeMenuItem : undefined}
                titleStyle={userId === id ? styles.activeMenuItemText : undefined}
              />
            ))}
            <Divider style={styles.menuDivider} />
            <Menu.Item 
              onPress={() => {
                setUserMenuVisible(false);
                setCustomUserDialogVisible(true);
              }} 
              title="Custom User ID..." 
              leadingIcon="account-plus-outline"
            />
          </Menu>
        </View>

        <View style={styles.testModeToggle}>
          <Text style={[styles.toggleLabel, { color: theme.textSecondary }]}>Test Mode</Text>
          <Switch
            value={isTestMode}
            onValueChange={setIsTestMode}
            accessibilityLabel="Toggle test mode"
            accessible
          />
          <Text style={[styles.toggleState, { color: theme.text }]}>{isTestMode ? 'ON' : 'OFF'}</Text>
        </View>
      </View>

      <Portal>
        <Modal
          visible={customUserDialogVisible}
          onDismiss={() => setCustomUserDialogVisible(false)}
          contentContainerStyle={[styles.modalContent, { backgroundColor: theme.background }]}
        >
          <Text style={[styles.modalTitle, { color: theme.text }]}>Enter Custom User ID</Text>
          <TextInput
            value={customUserId}
            onChangeText={setCustomUserId}
            mode="outlined"
            style={styles.modalInput}
            autoFocus
            returnKeyType="done"
            onSubmitEditing={handleCustomUserSubmit}
            placeholder="Enter a unique identifier"
            right={<TextInput.Icon icon="account-check" />}
          />
          <View style={styles.modalButtons}>
            <Button onPress={() => setCustomUserDialogVisible(false)}>Cancel</Button>
            <Button 
              onPress={handleCustomUserSubmit} 
              mode="contained" 
              disabled={!customUserId.trim()}
            >
              Switch
            </Button>
          </View>
        </Modal>
      </Portal>

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
    padding: 12,
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  userSelector: {
    flex: 1,
  },
  userButton: {
    paddingVertical: 4,
    paddingHorizontal: 4,
  },
  userProfile: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userAvatar: {
    fontSize: 24,
    marginRight: 8,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  userIdText: {
    fontSize: 12,
    opacity: 0.7,
  },
  menuAvatar: {
    fontSize: 20,
    width: 24,
  },
  activeMenuItem: {
    backgroundColor: 'rgba(0,0,0,0.05)',
  },
  activeMenuItemText: {
    fontWeight: 'bold',
  },
  menuDivider: {
    marginVertical: 8,
  },
  testModeToggle: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  toggleRow: { flexDirection: 'row', alignItems: 'center', padding: 10 },
  toggleLabel: { marginRight: 6, fontWeight: '500' },
  toggleState: { marginLeft: 6, opacity: 0.7 },
  modalContent: {
    padding: 20,
    margin: 20,
    borderRadius: 10,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  modalInput: {
    marginBottom: 16,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
});

export default ChatScreen;