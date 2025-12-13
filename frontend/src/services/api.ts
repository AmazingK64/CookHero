// src/services/api.ts
/**
 * API service for communicating with CookHero backend
 */

import type { ConversationRequest, SSEEvent } from '../types';

const API_BASE = '/api/v1';

/**
 * Send a message and receive streaming response
 */
export async function* streamConversation(
  request: ConversationRequest
): AsyncGenerator<SSEEvent> {
  const response = await fetch(`${API_BASE}/conversation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...request,
      stream: true,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      // Process complete SSE events
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data as SSEEvent;
          } catch (e) {
            console.warn('Failed to parse SSE event:', line);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Get conversation history
 */
export async function getConversationHistory(conversationId: string) {
  const response = await fetch(`${API_BASE}/conversation/${conversationId}`);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}

/**
 * Clear a conversation
 */
export async function clearConversation(conversationId: string) {
  const response = await fetch(`${API_BASE}/conversation/${conversationId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
}
