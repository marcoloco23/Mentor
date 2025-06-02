import React, { RefObject } from 'react';
import { StyleSheet, useColorScheme, Keyboard, GestureResponderHandlers, View } from 'react-native';
import { KeyboardAwareFlatList } from 'react-native-keyboard-aware-scroll-view';
import { ActivityIndicator, Text } from 'react-native-paper';
import ChatBubble, { Message } from './ChatBubble';
import { getTheme } from '../utils/theme';

/**
 * Props for MessageList component.
 */
export interface MessageListProps {
  messages: Message[];
  flatListRef?: RefObject<any>;
  onBubblePress?: (message: Message) => void;
  onBubbleLongPress?: (message: Message) => void;
  panHandlers?: GestureResponderHandlers;
  onLoadMore?: () => void;
  loadingMore?: boolean;
  hasMoreMessages?: boolean;
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
  onLoadMore,
  loadingMore = false,
  hasMoreMessages = true,
}) => {
  const scheme = useColorScheme();
  const theme = getTheme(scheme);

  const renderFooter = () => {
    if (loadingMore) {
      return (
        <View style={styles.loadingFooter}>
          <ActivityIndicator size="small" color={theme.primary} />
        </View>
      );
    }
    
    return null;
  };

  const handleEndReached = () => {
    if (hasMoreMessages && !loadingMore && onLoadMore) {
      onLoadMore();
    }
  };

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
      onEndReached={handleEndReached}
      onEndReachedThreshold={0.3}
      ListFooterComponent={renderFooter}
      {...(panHandlers || {})}
    />
  );
};

const styles = StyleSheet.create({
  list: { padding: 12, gap: 6 },
  listDark: {}, // Extend for dark mode if needed
  loadingFooter: {
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default MessageList; 