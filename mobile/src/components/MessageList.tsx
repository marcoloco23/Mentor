import React, { RefObject } from 'react';
import { StyleSheet, useColorScheme, Keyboard, GestureResponderHandlers } from 'react-native';
import { KeyboardAwareFlatList } from 'react-native-keyboard-aware-scroll-view';
import ChatBubble, { Message } from './ChatBubble';

/**
 * Props for MessageList component.
 */
export interface MessageListProps {
  messages: Message[];
  flatListRef?: RefObject<any>;
  onBubblePress?: (message: Message) => void;
  onBubbleLongPress?: (message: Message) => void;
  panHandlers?: GestureResponderHandlers;
}

/**
 * Renders a list of chat messages using ChatBubble components.
 */
const MessageList: React.FC<MessageListProps> = ({
  messages,
  flatListRef,
  onBubblePress,
  onBubbleLongPress,
  panHandlers,
}) => {
  const scheme = useColorScheme();

  return (
    <KeyboardAwareFlatList
      ref={flatListRef}
      data={[...messages].reverse()}
      inverted
      keyExtractor={(m) => m.id}
      renderItem={({ item }) => (
        <ChatBubble
          message={item}
          onPress={onBubblePress}
          onLongPress={onBubbleLongPress}
        />
      )}
      contentContainerStyle={[
        styles.list,
        scheme === 'dark' && styles.listDark,
      ]}
      extraHeight={80}
      {...(panHandlers || {})}
    />
  );
};

const styles = StyleSheet.create({
  list: { padding: 12, gap: 6 },
  listDark: {}, // Extend for dark mode if needed
});

export default MessageList; 