// src/components/MessageBubble.tsx
/**
 * Message bubble component for displaying chat messages
 */

import type { Message } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-orange-500 text-white'
            : 'bg-gray-100 text-gray-800'
        }`}
      >
        {/* Intent indicator for assistant messages */}
        {!isUser && message.intent && (
          <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
            {message.intent.need_rag ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
                知识库检索
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                </svg>
                直接回复
              </span>
            )}
          </div>
        )}

        {/* Thinking process */}
        {!isUser && message.thinking && message.thinking.length > 0 && (
          <div className="mb-3 text-xs text-gray-500">
            <p className="font-semibold text-gray-600 mb-1">🤔 思考过程</p>
            <ul className="space-y-1">
              {message.thinking.map((step, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-orange-500">{index + 1}.</span>
                  <span className="flex-1 leading-relaxed">{step}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Message content */}
        <div className={isUser ? '' : 'prose prose-sm max-w-none'}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <>
              <MarkdownRenderer content={message.content} />
              {message.isStreaming && (
                <span className="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse" />
              )}
            </>
          )}
        </div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-1">📚 参考来源：</p>
            <ul className="text-xs text-gray-600">
              {message.sources.map((source, index) => (
                <li key={index} className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-orange-400 rounded-full" />
                  {source.info}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs mt-2 ${isUser ? 'text-orange-200' : 'text-gray-400'}`}>
          {message.timestamp.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}
