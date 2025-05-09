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

  const isInExpoGo = Constants.executionEnvironment === 'storeClient';
  
  if (isInExpoGo) {
    return 'https://e52f-77-11-86-217.ngrok-free.app';
  }

  return 'http://192.168.4.160:8000';
} 