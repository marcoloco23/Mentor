import { Platform } from 'react-native';
import Constants from 'expo-constants';

/**
 * Returns the correct API base URL depending on the platform and connection type.
 * - On web: uses localhost
 * - On mobile with tunnel: uses ngrok URL
 * - On mobile with LAN: uses local network IP
 *
 * @returns {string} The base URL for API requests.
 */
export function getApiBaseUrl(): string {
  if (Platform.OS === 'web') {
    return 'http://localhost:8000';
  }

  // const isInExpoGo = Constants.executionEnvironment === 'storeClient';
  
  // if (isInExpoGo) {
  //   return 'https://84df-2a02-3100-1a88-7b00-4157-e806-e712-b4a0.ngrok-free.app';
  // }

  // Call ipconfig getifaddr en0 
  return 'http://192.168.178.46:8000';
} 