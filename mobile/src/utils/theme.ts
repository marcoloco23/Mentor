import { ColorSchemeName } from 'react-native';

/**
 * Semantic color palette for light and dark (OLED) themes.
 */
export const lightTheme = {
  background: '#F5F7FA',
  backgroundSecondary: '#F5F5F7',
  text: '#222',
  textSecondary: '#1A237E',
  primary: '#007AFF', // Apple blue
  bubbleUser: '#E6F0FF',
  bubbleAssistant: '#F5F5F7',
  bubbleUserBorder: '#B3C6FF',
  bubbleAssistantBorder: '#E0E0E0',
  bubbleUserDarkText: '#fff',
  bubbleAssistantDarkText: '#F5F5F7',
  toggleBackground: '#E6F0FF',
  border: 'rgba(0,0,0,0.04)',
};

export const darkTheme = {
  background: '#000', // OLED black
  backgroundSecondary: '#23272F',
  text: '#F5F5F7',
  textSecondary: '#fff',
  primary: '#0A84FF', // Apple blue (dark mode)
  bubbleUser: '#223366',
  bubbleAssistant: '#23272F',
  bubbleUserBorder: '#3A4A6B',
  bubbleAssistantBorder: '#353A45',
  bubbleUserDarkText: '#fff',
  bubbleAssistantDarkText: '#F5F5F7',
  toggleBackground: '#223366',
  border: '#222',
};

/**
 * Returns the theme object for the given color scheme.
 */
export function getTheme(scheme: ColorSchemeName) {
  return scheme === 'dark' ? darkTheme : lightTheme;
} 