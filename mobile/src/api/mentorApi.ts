import axios from 'axios';
import EventSource from 'react-native-sse';

/**
 * Type definition for chat request payload.
 */
export interface ChatRequest {
  message: string;
  thread_id?: string;
  test_mode?: boolean;
}

/**
 * Type definition for chat response payload.
 */
export interface ChatResponse {
  response: string;
  data?: unknown;
}

export interface ChatLogMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

const API_BASE_URL = 'http://localhost:8000'; // Update as needed

/**
 * Sends a message to the Mentor backend chat endpoint.
 * @param payload ChatRequest object
 * @returns ChatResponse from backend
 */
export async function sendMessage(payload: ChatRequest): Promise<ChatResponse> {
  const res = await axios.post<ChatResponse>(`${API_BASE_URL}/chat`, payload);
  return res.data;
}

/**
 * Streams a message to the Mentor backend using SSE and calls onChunk for each chunk.
 * @param payload ChatRequest object
 * @param onChunk Callback for each streamed chunk
 */
export async function streamMessage(
  payload: ChatRequest,
  onChunk: (chunk: string) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const es = new EventSource(`${API_BASE_URL}/chat/stream`, {
      pollingInterval: 0, // true server-push
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
      body: JSON.stringify(payload),
    });

    es.addEventListener('message', (event: any) => {
      const raw = event.data as string;
      const chunk = JSON.parse(raw); // decode to preserve leading spaces
      if (chunk === '[END]') {
        es.close();
        resolve();
      } else {
        onChunk(chunk);
      }
    });

    es.addEventListener('error', (err: any) => {
      es.close();
      reject(err);
    });
  });
}

export async function getChatLog(): Promise<ChatLogMessage[]> {
  const res = await axios.get<ChatLogMessage[]>(`${API_BASE_URL}/chatlog`);
  return res.data;
}
