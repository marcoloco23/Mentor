import { Platform } from 'react-native';

/**
 * Returns the correct API base URL depending on the platform.
 * - On web: uses localhost.
 * - On mobile: uses the local network IP address of the dev machine.
 *
 * @returns {string} The base URL for API requests.
 */
export function getApiBaseUrl(): string {
  if (Platform.OS === 'web') {
    return 'http://localhost:8000';
  }
  // Replace with your actual local IP address
  return 'http://192.168.178.121:8000';
} 