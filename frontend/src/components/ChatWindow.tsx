// src/components/ChatWindow.tsx
/**
 * Main chat window component
 */

import { useEffect, useRef } from 'react';
import type { Message } from '../types';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
}

export function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-2">
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <div className="text-6xl mb-4">🍳</div>
          <h2 className="text-xl font-semibold mb-2">欢迎来到 CookHero!</h2>
          <p className="text-center max-w-md">
            我是你的智能烹饪助手，可以帮你查找菜谱、提供烹饪技巧，或者根据你手边的食材推荐美味佳肴。
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            <SuggestionChip text="红烧肉怎么做？" />
            <SuggestionChip text="有鸡蛋能做什么？" />
            <SuggestionChip text="今晚吃什么？" />
            <SuggestionChip text="如何让炒菜更香？" />
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && messages[messages.length - 1]?.role === 'user' && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2 text-gray-500">
                  <span className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </span>
                  <span className="text-sm">正在思考...</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}

// Suggestion chip component
function SuggestionChip({ text }: { text: string }) {
  return (
    <button
      className="px-4 py-2 bg-orange-50 text-orange-600 rounded-full text-sm hover:bg-orange-100 transition-colors"
      onClick={() => {
        // This will be handled by the parent component in a real implementation
        // For now, we just show the suggestion
        const input = document.querySelector('textarea');
        if (input) {
          input.value = text;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.focus();
        }
      }}
    >
      {text}
    </button>
  );
}
