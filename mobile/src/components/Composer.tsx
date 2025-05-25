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
        paddingBottom: isIOS ? 24 : 8,
      }
    ]}>
      <View style={[
        styles.inputRow,
        {
          backgroundColor: theme.backgroundSecondary,
          borderRadius: 24,
          marginHorizontal: 12,
          marginBottom: isIOS ? 0 : 4,
          paddingVertical: 0,
          paddingHorizontal: 8,
          shadowColor: '#000',
          shadowOpacity: 0.08,
          shadowRadius: 8,
          shadowOffset: { width: 0, height: 2 },
          elevation: 2,
        },
      ]}>
        <TextInput
          style={[
            styles.input,
            {
              backgroundColor: 'transparent',
              color: theme.text,
              paddingVertical: isIOS ? 10 : 8,
              paddingHorizontal: 0,
              marginRight: 0,
              maxHeight: MAX_HEIGHT,
              minHeight: isIOS ? 44 : LINE_HEIGHT * 2,
              fontSize: 17,
            },
          ]}
          value={value}
          onChangeText={onChangeText}
          placeholder="Talk to me…"
          placeholderTextColor={theme.textSecondary}
          multiline
          blurOnSubmit={false}
          onSubmitEditing={Platform.OS !== 'web' ? onSend : undefined}
          onKeyPress={onKeyPress}
          editable={!disabled}
          mode="flat"
          underlineColor="transparent"
          activeUnderlineColor="transparent"
          accessibilityLabel="Message input field"
          accessibilityRole="text"
          selectionColor={theme.textSecondary}
        />
        
        <View style={styles.actionsContainer}>
          <View style={styles.audioRecorderWrapper}>
            <AudioRecorder 
              onTranscribe={handleTranscribe} 
              disabled={typing || disabled} 
            />
          </View>
          
          <Animated.View 
            pointerEvents={value.trim() ? 'auto' : 'none'}
            style={{ 
              opacity: sendButtonOpacity,
              width: 44,
              height: 44,
              justifyContent: 'center',
              alignItems: 'center',
              marginLeft: 2,
            }}
          >
            <IconButton
              icon="send-circle"
              disabled={!value.trim() || typing || disabled}
              onPress={onSend}
              size={32}
              accessibilityLabel="Send message"
              accessibilityRole="button"
              style={[
                styles.sendButton,
                { backgroundColor: value.trim() && !disabled ? paperTheme.colors.primary : theme.border },
                ...(value.trim() && !disabled ? [styles.sendButtonActive] : []),
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
    alignItems: 'center',
  },
  input: {
    flex: 1,
    lineHeight: Platform.OS === 'ios' ? 22 : 22,
    paddingHorizontal: 0,
    borderWidth: 0,
    outlineWidth: 0,
    backgroundColor: 'transparent',
    borderColor: 'transparent',
    borderRadius: 18,
  },
  actionsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingRight: 4,
    paddingBottom: 0,
    height: 60,
  },
  audioRecorderWrapper: {
    width: 48,
    height: 48,
    minWidth: 44,
    minHeight: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButton: {
    margin: 0,
    borderRadius: 22,
    width: 44,
    height: 44,
    minWidth: 44,
    minHeight: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonActive: {
    shadowColor: '#000',
    shadowOpacity: 0.12,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
});

export default Composer; 