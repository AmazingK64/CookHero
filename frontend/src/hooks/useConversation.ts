// src/hooks/useConversation.ts
/**
 * Custom hook for managing conversation state
 */

import { useState, useCallback, useRef } from 'react';
import type { Message, IntentInfo, Source } from '../types';
import { streamConversation } from '../services/api';

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

export function useConversation() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);

    // Add user message
    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Create assistant message placeholder
    const assistantMessageId = generateId();
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      let currentContent = '';
      let currentIntent: IntentInfo | undefined;
      let currentSources: Source[] = [];
      let currentThinking: string[] = [];

      for await (const event of streamConversation({
        message: content,
        conversation_id: conversationId,
      })) {
        switch (event.type) {
          case 'intent':
            currentIntent = event.data as IntentInfo;
            setMessages(prev =>
              prev.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, intent: currentIntent }
                  : msg
              )
            );
            break;

          case 'thinking':
            {
              const thought = event.content || (typeof event.data === 'string' ? event.data : '');
              if (thought) {
                currentThinking = [...currentThinking, thought];
                setMessages(prev =>
                  prev.map(msg =>
                    msg.id === assistantMessageId
                      ? { ...msg, thinking: currentThinking }
                      : msg
                  )
                );
              }
            }
            break;

          case 'text':
            currentContent += event.content || '';
            setMessages(prev =>
              prev.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, content: currentContent }
                  : msg
              )
            );
            break;

          case 'sources':
            currentSources = event.data as Source[];
            setMessages(prev =>
              prev.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, sources: currentSources }
                  : msg
              )
            );
            break;

          case 'done':
            if (event.conversation_id) {
              setConversationId(event.conversation_id);
            }
            setMessages(prev =>
              prev.map(msg =>
                msg.id === assistantMessageId
                  ? { ...msg, isStreaming: false }
                  : msg
              )
            );
            break;
        }
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
      
      // Remove the failed assistant message
      setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isLoading]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(undefined);
    setError(null);
  }, []);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    
    // Mark any streaming messages as complete
    setMessages(prev =>
      prev.map(msg =>
        msg.isStreaming ? { ...msg, isStreaming: false } : msg
      )
    );
  }, []);

  return {
    messages,
    conversationId,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    stopGeneration,
  };
}
