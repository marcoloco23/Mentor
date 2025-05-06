import axios from 'axios';
import EventSource from 'react-native-sse';
import { getApiBaseUrl } from '../utils/apiBaseUrl';

/**
 * Type definition for chat request payload.
 */
export interface ChatRequest {
  message: string;
  thread_id?: string;
  test_mode?: boolean;
  user_id?: string;
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

const API_BASE_URL = getApiBaseUrl();

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
  // Remove user_id if it's "default" to let backend use its default
  if (payload.user_id === "default") {
    const { user_id, ...cleanPayload } = payload;
    payload = cleanPayload;
  }

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

/**
 * Gets chat log history from the backend.
 * @param userId Optional user ID to retrieve specific user's chat logs
 * @returns Array of chat log messages
 */
export async function getChatLog(userId?: string): Promise<ChatLogMessage[]> {
  // Don't append user_id param if it's "default" or undefined
  const url = userId && userId !== "default"
    ? `${API_BASE_URL}/chatlog?user_id=${encodeURIComponent(userId)}`
    : `${API_BASE_URL}/chatlog`;
  const res = await axios.get<ChatLogMessage[]>(url);
  return res.data;
}
