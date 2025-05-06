import React, { useEffect, useState } from 'react';
import { View, Pressable, StyleSheet, useColorScheme, Platform } from 'react-native';
import { Text } from 'react-native-paper';
import Animated, { FadeInUp } from 'react-native-reanimated';
import { getTheme } from '../utils/theme';
import * as Haptics from 'expo-haptics';
import * as Clipboard from 'expo-clipboard';

/**
 * Message interface for chat bubbles.
 */
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'typing';
  text: string;
  ts?: number;
}

/**
 * Props for ChatBubble component.
 */
export interface ChatBubbleProps {
  message: Message;
  onPress?: (message: Message) => void;
  onLongPress?: (message: Message) => void;
}

/**
 * Renders a single chat message bubble with theming and accessibility support.
 * Allows native text selection via the `selectable` prop on the Text component.
 */
const ChatBubble: React.FC<ChatBubbleProps> = ({ message, onPress, onLongPress }) => {
  const scheme = useColorScheme();
  const theme = getTheme(scheme);
  const isUser = message.role === 'user';

  useEffect(() => {
    if (message.role === 'user' || message.role === 'assistant') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  }, []);

  const bubbleStyle = [
    styles.bubble,
    {
      backgroundColor: isUser ? theme.bubbleUser : theme.bubbleAssistant,
      borderColor: isUser ? theme.bubbleUserBorder : theme.bubbleAssistantBorder,
    },
  ];
  const textStyle = [
    styles.text,
    {
      color: isUser ? theme.textSecondary : theme.text,
    },
    scheme === 'dark' && {
      color: isUser ? theme.bubbleUserDarkText : theme.bubbleAssistantDarkText,
    },
    isUser && styles.userText,
  ];
  const containerStyle = [
    isUser ? styles.bubbleUserContainer : styles.bubbleAssistantContainer,
  ];

  return (
    <Animated.View entering={FadeInUp.duration(250)}>
      <Pressable
        accessible
        accessibilityLabel={`Chat message: ${message.text}`}
        onPress={() => onPress && onPress(message)}
        onLongPress={() => onLongPress && onLongPress(message)}
        style={containerStyle}
      >
        <View style={bubbleStyle}>
          {/* The Text is selectable, allowing users to select/copy text using the native system toolbar. */}
          <Text selectable style={textStyle} allowFontScaling={true}>
            {message.text}
          </Text>
        </View>
      </Pressable>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
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
  },
  text: {
    fontSize: 17,
    lineHeight: 22,
  },
  userText: {
    fontWeight: '500',
  },
  bubbleUserContainer: { alignSelf: 'flex-end', maxWidth: '80%' },
  bubbleAssistantContainer: { alignSelf: 'flex-start', maxWidth: '80%' },
});

export default ChatBubble; 