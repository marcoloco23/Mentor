import type { Message } from '../components/ChatBubble';

export type ChatAction =
  | { type: 'add'; message: Message }
  | { type: 'replaceTyping'; text: string };

/**
 * Pure reducer for chat message state.
 */
export function chatReducer(state: Message[], action: ChatAction): Message[] {
  switch (action.type) {
    case 'add':
      return [...state, action.message].slice(-200);
    case 'replaceTyping':
      return state.map((m) =>
        m.role === 'typing' ? { ...m, text: action.text } : m
      );
    default:
      return state;
  }
}

// Action creators
export const addMsg = (message: Message): ChatAction => ({ type: 'add', message });
export const replaceTyping = (text: string): ChatAction => ({ type: 'replaceTyping', text }); 