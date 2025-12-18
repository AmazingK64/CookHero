/**
 * Chat-related type definitions
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  intent?: IntentInfo | string;
  isStreaming?: boolean;
  thinking?: string[];
}

export interface Source {
  type: string;
  info: string;
  title?: string;
  url?: string;
  category?: string;
}

export interface IntentInfo {
  need_rag: boolean;
  intent: string;
  reason: string;
}

export interface ConversationSummary {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview?: string | null;
}

export interface Conversation {
  id: string;
  messages: Message[];
  createdAt: Date;
}

// Streaming state for conversation caching
export interface StreamingState {
  conversationId: string;
  messages: Message[];
  isStreaming: boolean;
  tempId?: string;
}
