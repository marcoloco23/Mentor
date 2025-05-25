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
  const pulseAnim = React.useRef(new Animated.Value(1)).current;

  // Animated values for icon cross-fade
  const micOpacity = React.useRef(new Animated.Value(1)).current;
  const stopOpacity = React.useRef(new Animated.Value(0)).current;

  // Expo Audio hook - using default HIGH_QUALITY preset
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

  // Animate icon cross-fade
  useEffect(() => {
    Animated.parallel([
      Animated.timing(micOpacity, {
        toValue: isRecording ? 0 : 1,
        duration: 180,
        useNativeDriver: true,
      }),
      Animated.timing(stopOpacity, {
        toValue: isRecording ? 1 : 0,
        duration: 180,
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

  const buttonSize = 48;

  if (permissionGranted === null) {
    return <ActivityIndicator animating={true} color={theme.colors.primary} />;
  }

  return (
    <View style={[styles.container, { flexDirection: 'column' }]}>
      <TouchableOpacity
        onPress={handlePress}
        disabled={!!disabled || !!isLoading || permissionGranted === false}
        style={styles.touchableArea}
        activeOpacity={0.6}
        hitSlop={{ top: 15, bottom: 15, left: 15, right: 15 }}
        accessibilityRole="button"
        accessibilityLabel={isRecording ? "Stop recording" : "Start recording"}
      >
        <Animated.View
          style={[
            styles.buttonContainer,
            {
              backgroundColor: isRecording ? 'rgba(255, 59, 48, 0.1)' : 'transparent',
              width: buttonSize,
              height: buttonSize,
              borderRadius: buttonSize / 2,
              position: 'relative',
              overflow: 'hidden',
              justifyContent: 'center',
              alignItems: 'center',
            }
          ]}
        >
          {/* Microphone Icon */}
          <Animated.View
            style={[
              styles.iconAbsolute,
              { opacity: micOpacity }
            ]}
            pointerEvents={isRecording ? 'none' : 'auto'}
          >
            <MaterialCommunityIcons name="microphone" size={28} color={theme.colors.primary} />
          </Animated.View>
          {/* Stop Icon */}
          <Animated.View
            style={[
              styles.iconAbsolute,
              { opacity: stopOpacity }
            ]}
            pointerEvents={isRecording ? 'auto' : 'none'}
          >
            <MaterialCommunityIcons name="stop-circle" size={28} color={theme.colors.error} />
          </Animated.View>
          {isLoading && (
            <View style={styles.loadingOverlay} pointerEvents="none">
              <ActivityIndicator animating={true} size={36} color={theme.colors.primary} style={{ opacity: 0.85 }} />
            </View>
          )}
        </Animated.View>
      </TouchableOpacity>
      {isRecording && (
        <Text style={[styles.timerText, { color: theme.colors.error }]}> {formatTime(recordingDuration)} </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
  },
  touchableArea: {
    width: 60,
    height: 60,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  buttonContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  iconAbsolute: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timerText: {
    marginTop: 6,
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  loadingContainer: {
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0,0,0,0.18)',
    borderRadius: 999,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
});

export default AudioRecorder; 