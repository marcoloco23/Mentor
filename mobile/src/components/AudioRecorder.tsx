import React, { useEffect, useState } from 'react';
import { View, StyleSheet, Alert, Platform, TouchableOpacity, Animated } from 'react-native';
import { Text, ActivityIndicator, useTheme } from 'react-native-paper';
import { useAudioRecorder, RecordingPresets, AudioModule } from 'expo-audio';
import MaterialCommunityIcons from 'react-native-vector-icons/MaterialCommunityIcons';
import { transcribeAudio, TranscriptionResponse } from '../api/mentorApi';

interface AudioRecorderProps {
  onTranscribe: (transcription: string) => void;
  disabled?: boolean;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ onTranscribe, disabled = false }) => {
  const theme = useTheme();
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [permissionGranted, setPermissionGranted] = useState<boolean | null>(null);
  
  // Enhanced animations
  const pulseAnim = React.useRef(new Animated.Value(1)).current;
  const scaleAnim = React.useRef(new Animated.Value(1)).current;
  const rippleAnim = React.useRef(new Animated.Value(0)).current;
  const micOpacity = React.useRef(new Animated.Value(1)).current;
  const stopOpacity = React.useRef(new Animated.Value(0)).current;

  // Expo Audio hook
  const audioRecorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  // Permission check on mount
  useEffect(() => {
    (async () => {
      const status = await AudioModule.requestRecordingPermissionsAsync();
      setPermissionGranted(status.granted);
      if (!status.granted) {
        Alert.alert('Permission to access microphone was denied');
      }
    })();
  }, []);

  // Timer for recording duration
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null;
    if (isRecording) {
      timer = setInterval(() => setRecordingDuration((d) => d + 1), 1000);
    } else {
      setRecordingDuration(0);
      if (timer) clearInterval(timer);
    }
    return () => { if (timer) clearInterval(timer); };
  }, [isRecording]);

  // Enhanced recording animations
  useEffect(() => {
    if (isRecording) {
      // Start subtle pulsing animation
      const pulseAnimation = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.05,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );

      pulseAnimation.start();

      return () => {
        pulseAnimation.stop();
      };
    } else {
      pulseAnim.setValue(1);
      rippleAnim.setValue(0);
    }
  }, [isRecording]);

  // Animate icon cross-fade with improved timing
  useEffect(() => {
    Animated.parallel([
      Animated.timing(micOpacity, {
        toValue: isRecording ? 0 : 1,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(stopOpacity, {
        toValue: isRecording ? 1 : 0,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: isRecording ? 0.95 : 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, [isRecording]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startRecording = async () => {
    try {
      setIsLoading(true);
      await audioRecorder.prepareToRecordAsync();
      await audioRecorder.record();
      setIsRecording(true);
    } catch (err: any) {
      Alert.alert('Error', 'Could not start recording: ' + (err?.message || err));
    } finally {
      setIsLoading(false);
    }
  };

  const stopRecording = async () => {
    try {
      setIsLoading(true);
      await audioRecorder.stop();
      setIsRecording(false);
      
      if (audioRecorder.uri) {
        const formData = new FormData();
        
        // Determine the actual file format based on platform and URI
        let filename = audioRecorder.uri.split('/').pop() || 'audio.m4a';
        let mimeType = 'audio/mp4'; // Default for M4A
        
        if (Platform.OS === 'web') {
          // Web typically records in WebM format
          mimeType = 'audio/webm';
          filename = 'audio.webm'; // Always use .webm for web recordings
        } else {
          // Mobile platforms (iOS/Android) - typically M4A
          if (filename.endsWith('.m4a') || filename.endsWith('.mp4')) {
            mimeType = 'audio/mp4';
            filename = filename.replace(/\.[^.]+$/, '.m4a');
          } else if (filename.endsWith('.wav')) {
            mimeType = 'audio/wav';
          } else if (filename.endsWith('.mp3')) {
            mimeType = 'audio/mpeg';
          } else {
            // Default to M4A for mobile - ensure proper extension
            mimeType = 'audio/mp4';
            filename = 'audio.m4a';
          }
        }

        console.log(`Preparing to transcribe: ${filename} (${mimeType}) from URI: ${audioRecorder.uri}`);

        if (Platform.OS === 'web') {
          // For web, fetch the blob with correct MIME type
          const response = await fetch(audioRecorder.uri);
          const blob = await response.blob();
          // Create a new blob with the correct MIME type to ensure consistency
          const correctedBlob = new Blob([blob], { type: mimeType });
          formData.append('file', correctedBlob, filename);
        } else {
          // For mobile platforms
          formData.append('file', {
            uri: audioRecorder.uri,
            type: mimeType,
            name: filename,
          } as any);
        }

        const response: TranscriptionResponse = await transcribeAudio(
          formData,
          // Use whisper-1 directly for WebM files since they have known issues with gpt-4o-transcribe
          mimeType === 'audio/webm' ? 'whisper-1' : 'gpt-4o-transcribe'
        );
        onTranscribe(response.transcription || '');
      }
    } catch (err: any) {
      console.error('Transcription error:', err);
      Alert.alert('Error', 'Could not stop or transcribe recording: ' + (err?.message || err));
    } finally {
      setIsLoading(false);
    }
  };

  const handlePress = () => {
    if (disabled || isLoading || permissionGranted === false) return;
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  if (permissionGranted === null) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator animating={true} color={theme.colors.primary} size="small" />
      </View>
    );
  }

  const buttonSize = 32;

  return (
    <View style={styles.container}>
      <TouchableOpacity
        onPress={handlePress}
        disabled={!!disabled || !!isLoading || permissionGranted === false}
        style={[
          styles.touchableArea,
          {
            opacity: disabled || permissionGranted === false ? 0.4 : 1,
          }
        ]}
        activeOpacity={0.7}
        accessibilityRole="button"
        accessibilityLabel={isRecording ? "Stop recording" : "Start recording"}
      >
        <Animated.View
          style={[
            styles.buttonContainer,
            {
              width: buttonSize,
              height: buttonSize,
              borderRadius: buttonSize / 2,
              backgroundColor: isRecording 
                ? theme.colors.errorContainer
                : 'transparent',
              transform: [
                { scale: scaleAnim },
                { scale: pulseAnim },
              ],
            }
          ]}
        >
          {/* Microphone Icon */}
          <Animated.View
            style={[
              styles.iconContainer,
              { opacity: micOpacity }
            ]}
          >
            <MaterialCommunityIcons 
              name="microphone" 
              size={18} 
              color={disabled ? theme.colors.outline : theme.colors.primary} 
            />
          </Animated.View>

          {/* Recording Icon */}
          <Animated.View
            style={[
              styles.iconContainer,
              { opacity: stopOpacity }
            ]}
          >
            <MaterialCommunityIcons 
              name="stop" 
              size={16} 
              color={theme.colors.error} 
            />
          </Animated.View>

          {/* Loading overlay */}
          {isLoading && (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator 
                animating={true} 
                size="small" 
                color={theme.colors.primary} 
              />
            </View>
          )}
        </Animated.View>
      </TouchableOpacity>

      {/* Compact recording indicator */}
      {isRecording && (
        <View style={[styles.recordingIndicator, { backgroundColor: theme.colors.errorContainer }]}>
          <Animated.View 
            style={[
              styles.recordingDot,
              {
                opacity: pulseAnim.interpolate({
                  inputRange: [1, 1.05],
                  outputRange: [0.7, 1],
                }),
              }
            ]} 
          />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  loadingContainer: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  touchableArea: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  buttonContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  iconContainer: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordingIndicator: {
    position: 'absolute',
    top: 2,
    right: 2,
    width: 8,
    height: 8,
    borderRadius: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#f44336',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderRadius: 999,
  },
});

export default AudioRecorder; 