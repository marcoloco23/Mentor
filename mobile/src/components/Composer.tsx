import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Platform, useColorScheme, Animated, TouchableOpacity, TextInput } from 'react-native';
import { useTheme as usePaperTheme } from 'react-native-paper';
import { getTheme } from '../utils/theme';
import AudioRecorder from './AudioRecorder';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';

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
  onAttachment?: () => void;
}

/**
 * Renders the chat input row with TextInput and send button.
 * Auto-grows up to 6 lines, then becomes scrollable internally.
 */
const MAX_LINES = 6;
const LINE_HEIGHT = 22;
const MAX_HEIGHT = MAX_LINES * LINE_HEIGHT + 24; // Added padding

const Composer: React.FC<ComposerProps> = ({
  value,
  onChangeText,
  onSend,
  disabled = false,
  typing = false,
  onKeyPress,
  onAttachment,
}) => {
  const scheme = useColorScheme();
  const theme = getTheme(scheme);
  const paperTheme = usePaperTheme();
  const isIOS = Platform.OS === 'ios';
  
  // Enhanced animations
  const sendButtonScale = useRef(new Animated.Value(value.trim() ? 1 : 0.8)).current;
  const sendButtonOpacity = useRef(new Animated.Value(value.trim() ? 1 : 0)).current;
  const attachmentOpacity = useRef(new Animated.Value(value.trim() ? 0 : 1)).current;
  
  // Update animations when value changes
  useEffect(() => {
    const hasText = value.trim().length > 0;
    
    Animated.parallel([
      Animated.spring(sendButtonScale, {
        toValue: hasText ? 1 : 0.8,
        useNativeDriver: true,
        tension: 300,
        friction: 10,
      }),
      Animated.timing(sendButtonOpacity, {
        toValue: hasText ? 1 : 0,
        duration: 250,
        useNativeDriver: true,
      }),
      Animated.timing(attachmentOpacity, {
        toValue: hasText ? 0 : 1,
        duration: 250,
        useNativeDriver: true,
      }),
    ]).start();
  }, [value]);

  const handleTranscribe = (transcription: string) => {
    onChangeText(value ? `${value} ${transcription}` : transcription);
  };

  const handleSend = () => {
    if (value.trim() && !disabled && !typing) {
      // Add subtle haptic feedback only on successful send
      if (Platform.OS !== 'web') {
        try {
          const Haptics = require('expo-haptics');
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        } catch (e) {
          // Haptics not available
        }
      }
      onSend();
    }
  };

  const handleAttachment = () => {
    if (!disabled && !typing && onAttachment) {
      // Only add haptic feedback when actually opening attachment
      if (Platform.OS !== 'web') {
        try {
          const Haptics = require('expo-haptics');
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        } catch (e) {
          // Haptics not available
        }
      }
      onAttachment();
    }
  };

  return (
    <View style={[
      styles.container,
      {
        backgroundColor: isIOS ? theme.backgroundSecondary : theme.background,
        paddingBottom: isIOS ? 8 : 8,
        paddingTop: 4,
      }
    ]}>
      <Animated.View style={[
        styles.inputRow,
        {
          backgroundColor: theme.backgroundSecondary,
          borderRadius: 24,
          marginHorizontal: 12,
          paddingVertical: 4,
          paddingHorizontal: 4,
          shadowColor: '#000',
          shadowOpacity: Platform.OS === 'ios' ? 0.03 : 0.06,
          shadowRadius: 6,
          shadowOffset: { width: 0, height: 1 },
          elevation: 1,
          borderWidth: 1,
          borderColor: theme.border + '10',
        },
      ]}>
        {/* Left side actions */}
        <View style={styles.leftActions}>
          {/* Attachment Button */}
          <Animated.View
            style={[
              styles.attachmentContainer,
              { opacity: attachmentOpacity }
            ]}
            pointerEvents={value.trim() ? 'none' : 'auto'}
          >
            <TouchableOpacity
              onPress={handleAttachment}
              disabled={!onAttachment || disabled || typing}
              style={styles.attachmentButton}
              activeOpacity={0.6}
            >
              <MaterialCommunityIcons
                name="paperclip"
                size={18}
                color={theme.textSecondary}
              />
            </TouchableOpacity>
          </Animated.View>
        </View>

        {/* Text Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={[
              styles.input,
              {
                color: theme.text,
                maxHeight: MAX_HEIGHT,
              },
            ]}
            value={value}
            onChangeText={onChangeText}
            placeholder="Message…"
            placeholderTextColor={theme.textSecondary}
            multiline={true}
            blurOnSubmit={false}
            onSubmitEditing={Platform.OS !== 'web' ? handleSend : undefined}
            onKeyPress={onKeyPress}
            editable={!disabled}
            accessibilityLabel="Message input field"
            accessibilityRole="text"
            selectionColor={paperTheme.colors.primary}
            cursorColor={paperTheme.colors.primary}
            scrollEnabled={true}
            autoCorrect={true}
            autoCapitalize="sentences"
            keyboardType="default"
            returnKeyType="default"
            textAlignVertical={Platform.OS === 'android' ? 'top' : 'center'}
          />
        </View>
        
        {/* Right side actions */}
        <View style={styles.rightActions}>
          {/* Audio Recorder */}
          <View style={styles.audioRecorderWrapper}>
            <AudioRecorder 
              onTranscribe={handleTranscribe} 
              disabled={typing || disabled} 
            />
          </View>
          
          {/* Send Button */}
          <Animated.View 
            style={[
              styles.sendButtonContainer,
              {
                opacity: sendButtonOpacity,
                transform: [{ scale: sendButtonScale }],
              }
            ]}
            pointerEvents={value.trim() ? 'auto' : 'none'}
          >
            <TouchableOpacity
              onPress={handleSend}
              disabled={!value.trim() || typing || disabled}
              style={[
                styles.sendButton,
                {
                  backgroundColor: value.trim() && !disabled && !typing 
                    ? paperTheme.colors.primary 
                    : theme.border,
                  shadowColor: value.trim() && !disabled && !typing 
                    ? paperTheme.colors.primary 
                    : 'transparent',
                  shadowOpacity: 0.15,
                  shadowRadius: 3,
                  shadowOffset: { width: 0, height: 1 },
                  elevation: value.trim() && !disabled && !typing ? 1 : 0,
                }
              ]}
              activeOpacity={0.8}
            >
              <MaterialCommunityIcons
                name="send"
                size={16}
                color={value.trim() && !disabled && !typing ? '#ffffff' : theme.textSecondary}
                style={{
                  transform: [{ rotate: '-35deg' }],
                  marginLeft: 1,
                  marginTop: -1,
                }}
              />
            </TouchableOpacity>
          </Animated.View>
        </View>
      </Animated.View>
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
    minHeight: 52,
    paddingVertical: 4,
  },
  leftActions: {
    justifyContent: 'center',
    alignItems: 'center',
    paddingLeft: 4,
  },
  attachmentContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  attachmentButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
  },
  inputContainer: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  input: {
    fontFamily: Platform.OS === 'ios' ? 'SF Pro Text' : 'Roboto',
    fontSize: 16,
    fontWeight: '400',
    lineHeight: Platform.OS === 'ios' ? 22 : 22,
    minHeight: Platform.OS === 'ios' ? 44 : 42,
    paddingVertical: Platform.OS === 'ios' ? 12 : 10,
    paddingHorizontal: 12,
    backgroundColor: 'transparent',
    borderWidth: 0,
    outlineWidth: 0,
  },
  rightActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingRight: 4,
  },
  audioRecorderWrapper: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default Composer; 