import { chatReducer, addMsg, replaceTyping } from './chatReducer';
import type { Message } from '../components/ChatBubble';

describe('chatReducer', () => {
  const base: Message[] = [
    { id: '1-u', role: 'user', text: 'Hi' },
    { id: '2-a', role: 'assistant', text: 'Hello!' },
    { id: 'typing', role: 'typing', text: '...' },
  ];

  it('adds a message and keeps max 200', () => {
    let state: Message[] = [];
    for (let i = 0; i < 205; ++i) {
      state = chatReducer(state, addMsg({ id: `${i}`, role: 'user', text: `msg${i}` }));
    }
    expect(state.length).toBe(200);
    expect(state[0].id).toBe('5');
    expect(state[199].id).toBe('204');
  });

  it('replaces typing message text', () => {
    const state = chatReducer(base, replaceTyping('typing...'));
    expect(state.find((m) => m.role === 'typing')?.text).toBe('typing...');
  });

  it('does not change messages if no typing present', () => {
    const noTyping = base.filter((m) => m.role !== 'typing');
    const state = chatReducer(noTyping, replaceTyping('should not appear'));
    expect(state).toEqual(noTyping);
  });

  it('addMsg action creator returns correct action', () => {
    const msg: Message = { id: 'x', role: 'user', text: 'foo' };
    expect(addMsg(msg)).toEqual({ type: 'add', message: msg });
  });

  it('replaceTyping action creator returns correct action', () => {
    expect(replaceTyping('bar')).toEqual({ type: 'replaceTyping', text: 'bar' });
  });
}); 