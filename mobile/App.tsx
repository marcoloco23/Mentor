import React from 'react';
import { Provider as PaperProvider } from 'react-native-paper';
import ChatScreen from './src/screens/ChatScreen';

/**
 * Main entry point for Ted mobile app.
 */
export default function App() {
  return (
    <PaperProvider>
      <ChatScreen />
    </PaperProvider>
  );
}
