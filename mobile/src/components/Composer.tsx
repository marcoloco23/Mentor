import React from 'react';
import { View, StyleSheet, Platform, useColorScheme } from 'react-native';
import { TextInput, IconButton } from 'react-native-paper';
import { getTheme } from '../utils/theme';

/**
 * Props for Composer component.
 */
export interface ComposerProps {
  value: string;
  onChangeText: (text: string) => void;
  onSend: () => void;
  disabled?: boolean;
  typing?: boolean;
  onKeyPress?: (e: any) => void;
}

/**
 * Renders the chat input row with TextInput and send button.
 * Auto-grows up to 6 lines, then becomes scrollable internally.
 */
const MAX_LINES = 6;
const LINE_HEIGHT = 22; // match style
const MAX_HEIGHT = MAX_LINES * LINE_HEIGHT + 16; // padding fudge

const Composer: React.FC<ComposerProps> = ({
  value,
  onChangeText,
  onSend,
  disabled = false,
  typing = false,
  onKeyPress,
}) => {
  const scheme = useColorScheme();
  const theme = getTheme(scheme);

  return (
    <View style={[
      styles.inputRow,
      {
        backgroundColor: theme.backgroundSecondary,
        borderRadius: 24,
        borderWidth: 1,
        borderColor: theme.border,
        shadowColor: '#000',
        shadowOpacity: 0.06,
        shadowRadius: 4,
        elevation: 2,
        margin: 8,
        marginBottom: Platform.OS === 'ios' ? 12 : 4,
      },
    ]}>
      <TextInput
        style={[
          styles.input,
          {
            backgroundColor: theme.background,
            borderRadius: 18,
            borderWidth: 0,
            color: theme.text,
            paddingVertical: 8,
            paddingHorizontal: 14,
            marginRight: 4,
            maxHeight: MAX_HEIGHT,
            minHeight: LINE_HEIGHT * 2,
          },
        ]}
        value={value}
        onChangeText={onChangeText}
        placeholder="Ask your mentor…"
        placeholderTextColor={theme.text}
        multiline
        blurOnSubmit={false}
        onSubmitEditing={Platform.OS !== 'web' ? onSend : undefined}
        onKeyPress={onKeyPress}
        accessible
        accessibilityLabel="Message input"
        allowFontScaling={true}
      />
      <IconButton
        icon="send"
        disabled={!value.trim() || typing || disabled}
        onPress={onSend}
        size={28}
        accessibilityLabel="Send message"
        style={{ backgroundColor: 'transparent', marginLeft: 2 }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    fontSize: 17,
    lineHeight: 22,
    backgroundColor: 'transparent',
    paddingHorizontal: 0,
  },
});

export default Composer; 