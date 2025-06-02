import React, { useEffect, useState } from 'react';
import { View, Pressable, StyleSheet, useColorScheme, Platform } from 'react-native';
import { Text } from 'react-native-paper';
import Animated, { FadeInUp } from 'react-native-reanimated';
import { getTheme } from '../utils/theme';
import * as Haptics from 'expo-haptics';
import * as Clipboard from 'expo-clipboard';
import Markdown from 'react-native-markdown-display';

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
 * Supports markdown formatting for message text.
 */
const ChatBubble: React.FC<ChatBubbleProps> = ({ message, onPress, onLongPress }) => {
  const scheme = useColorScheme();
  const theme = getTheme(scheme);
  const isUser = message.role === 'user';

  // Note: Automatic haptic feedback on message render was removed for performance reasons.
  // Haptic feedback is now handled by specific user interactions (onPress/onLongPress) instead.

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

  // Configure markdown styles based on current theme
  const markdownStyles = {
    body: {
      color: textStyle.find((style) => style && typeof style === 'object' && 'color' in style)?.color || theme.text,
      fontSize: styles.text.fontSize,
      lineHeight: styles.text.lineHeight,
      fontWeight: (isUser ? '500' : 'normal') as 'normal' | 'bold' | '500',
    },
    // Add styling for specific markdown elements
    strong: {
      fontWeight: 'bold' as const,
    },
    em: {
      fontStyle: 'italic' as const,
    },
    heading1: {
      fontSize: styles.text.fontSize * 1.5,
      fontWeight: 'bold' as const,
      marginTop: 10,
      marginBottom: 5,
    },
    heading2: {
      fontSize: styles.text.fontSize * 1.3,
      fontWeight: 'bold' as const,
      marginTop: 8,
      marginBottom: 4,
    },
    heading3: {
      fontSize: styles.text.fontSize * 1.1,
      fontWeight: 'bold' as const,
      marginTop: 6,
      marginBottom: 3,
    },
    code_block: {
      backgroundColor: scheme === 'dark' ? '#2d2d2d' : '#f5f5f5',
      padding: 10,
      borderRadius: 5,
      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    },
    code_inline: {
      backgroundColor: scheme === 'dark' ? '#2d2d2d' : '#f5f5f5',
      padding: 2,
      borderRadius: 3,
      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    },
    bullet_list: {
      marginLeft: 10,
    },
    ordered_list: {
      marginLeft: 10,
    },
  };

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
          {message.role === 'typing' ? (
            <Text selectable style={textStyle} allowFontScaling={true}>
              {message.text}
            </Text>
          ) : (
            <Markdown 
              style={markdownStyles}
            >
              {message.text}
            </Markdown>
          )}
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