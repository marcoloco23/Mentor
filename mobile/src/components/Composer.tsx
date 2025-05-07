import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Platform, useColorScheme, Animated } from 'react-native';
import { TextInput, IconButton, useTheme as usePaperTheme } from 'react-native-paper';
import { getTheme } from '../utils/theme';
import AudioRecorder from './AudioRecorder';

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
  const paperTheme = usePaperTheme();
  const isIOS = Platform.OS === 'ios';
  
  // Animation for send button appearance
  const sendButtonOpacity = useRef(new Animated.Value(value.trim() ? 1 : 0)).current;
  
  // Update animation when value changes
  useEffect(() => {
    Animated.timing(sendButtonOpacity, {
      toValue: value.trim() ? 1 : 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  }, [value]);

  const handleTranscribe = (transcription: string) => {
    onChangeText(value ? `${value} ${transcription}` : transcription);
  };

  return (
    <View style={[
      styles.container,
      {
        backgroundColor: isIOS ? theme.backgroundSecondary : theme.background,
        paddingBottom: isIOS ? 30 : 12,
      }
    ]}>
      <View style={[
        styles.inputRow,
        {
          backgroundColor: theme.background,
          borderRadius: 28,
          marginHorizontal: 8,
          marginBottom: isIOS ? 0 : 4,
          paddingVertical: isIOS ? 4 : 0,
          shadowColor: '#000',
          shadowOpacity: isIOS ? 0.12 : 0.06,
          shadowRadius: isIOS ? 10 : 4,
          shadowOffset: { width: 0, height: isIOS ? 4 : 1 },
          elevation: 3,
        },
      ]}>
        <TextInput
          style={[
            styles.input,
            {
              backgroundColor: 'transparent',
              color: theme.text,
              paddingVertical: isIOS ? 12 : 10,
              paddingHorizontal: 16,
              marginRight: 0,
              maxHeight: MAX_HEIGHT,
              minHeight: isIOS ? 48 : LINE_HEIGHT * 2,
              fontSize: isIOS ? 17 : 17,
            },
          ]}
          value={value}
          onChangeText={onChangeText}
          placeholder="Ask your mentor…"
          placeholderTextColor={theme.textSecondary}
          multiline
          blurOnSubmit={false}
          onSubmitEditing={Platform.OS !== 'web' ? onSend : undefined}
          onKeyPress={onKeyPress}
          editable={!disabled}
        />
        
        <View style={styles.actionsContainer}>
          <View style={styles.audioRecorderWrapper}>
            <AudioRecorder onTranscribe={handleTranscribe} disabled={typing || disabled} />
          </View>
          
          <Animated.View 
            pointerEvents={value.trim() ? 'auto' : 'none'}
            style={{ 
              opacity: sendButtonOpacity,
              width: 44,
              height: 44,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <IconButton
              icon="send-circle"
              disabled={!value.trim() || typing || disabled}
              onPress={onSend}
              size={32}
              accessibilityLabel="Send message"
              style={[
                styles.sendButton,
                { backgroundColor: value.trim() && !disabled ? paperTheme.colors.primary : theme.border },
              ]}
              iconColor={value.trim() && !disabled ? '#fff' : theme.textSecondary}
            />
          </Animated.View>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  input: {
    flex: 1,
    lineHeight: Platform.OS === 'ios' ? 22 : 22,
    paddingHorizontal: 0,
    borderWidth: 0,
    outlineWidth: 0,
  },
  actionsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: Platform.OS === 'ios' ? 8 : 6,
    paddingBottom: Platform.OS === 'ios' ? 6 : 4,
    height: '100%',
  },
  audioRecorderWrapper: {
    width: 60,
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButton: {
    margin: 0,
    borderRadius: 22,
    width: 44,
    height: 44,
  }
});

export default Composer; 