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
        let filename = audioRecorder.uri.split('/').pop() || 'audio.m4a';
        let type = 'audio/mp4';
        if (filename.endsWith('.mp3')) type = 'audio/mpeg';
        else if (filename.endsWith('.wav')) type = 'audio/wav';
        else if (filename.endsWith('.webm')) type = 'audio/webm';

        if (Platform.OS === 'web') {
          // For web, fetch the blob and force .wav extension and no explicit MIME type
          const response = await fetch(audioRecorder.uri);
          const blob = await response.blob();
          formData.append('file', blob, 'audio.wav');
        } else {
          formData.append('file', {
            uri: audioRecorder.uri,
            type,
            name: filename,
          } as any);
        }

        const response: TranscriptionResponse = await transcribeAudio(formData);
        onTranscribe(response.transcription || '');
      }
    } catch (err: any) {
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

  const iconName = isRecording ? 'stop-circle' : 'microphone';
  const iconColor = isRecording ? theme.colors.error : theme.colors.primary;
  const buttonSize = 48;

  if (permissionGranted === null) {
    return <ActivityIndicator animating={true} color={theme.colors.primary} />;
  }

  return (
    <View style={styles.container}>
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
            }
          ]}
        >
          <MaterialCommunityIcons name={iconName} size={28} color={iconColor} />
        </Animated.View>
      </TouchableOpacity>
      {isRecording && (
        <Text style={[styles.timerText, { color: theme.colors.error }]}> {formatTime(recordingDuration)} </Text>
      )}
      {isLoading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator animating={true} size="small" color={theme.colors.primary} />
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
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
  },
  timerText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '500',
  },
  loadingContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
});

export default AudioRecorder; 