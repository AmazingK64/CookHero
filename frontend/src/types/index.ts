// src/types/index.ts
/**
 * Type definitions for CookHero frontend
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
  intent?: IntentInfo;
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

export interface ConversationRequest {
  message: string;
  conversation_id?: string;
  stream?: boolean;
}

export interface SSEEvent {
  type: 'intent' | 'thinking' | 'text' | 'sources' | 'done';
  content?: string;
  data?: IntentInfo | Source[] | string;
  conversation_id?: string;
}

export interface Conversation {
  id: string;
  messages: Message[];
  createdAt: Date;
}
