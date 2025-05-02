import axios from 'axios';

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
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.body) throw new Error('No response body');
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let lines = buffer.split('\n\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const chunk = line.replace('data: ', '');
        if (chunk === '[END]') return;
        onChunk(chunk);
      }
    }
  }
}
