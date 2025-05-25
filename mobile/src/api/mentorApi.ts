import axios from 'axios';
import EventSource from 'react-native-sse';
import { getApiBaseUrl } from '../utils/apiBaseUrl';

/**
 * Type definition for chat request payload.
 */
export interface ChatRequest {
  message: string;
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

export interface TranscriptionResponse {
  model: string;
  language?: string | null;
  transcription: string;
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

/**
 * Sends audio data to the backend for transcription.
 * @param formData FormData object containing the audio file.
 * @param model Optional model to use for transcription (defaults to gpt-4o-transcribe with fallback to whisper-1)
 * @returns TranscriptionResponse from the backend.
 */
export async function transcribeAudio(
  formData: FormData,
  model: string = 'gpt-4o-transcribe'
): Promise<TranscriptionResponse> {
  // Add model parameter to the request
  const url = new URL(`${API_BASE_URL}/transcribe_audio`);
  url.searchParams.append('model', model);

  try {
    const response = await fetch(url.toString(), {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorDetail;
      try {
        const errorData = JSON.parse(errorText);
        errorDetail = errorData.detail || errorText;
      } catch (e) {
        errorDetail = errorText;
      }
      throw new Error(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
    }

    return await response.json() as TranscriptionResponse;
  } catch (error) {
    console.error('Transcription failed:', error);
    throw error;
  }
}
