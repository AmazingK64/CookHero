// src/components/ChatWindow.tsx
/**
 * Main chat window component
 */

import { useEffect, useRef } from 'react';
import { ChefHat, Sparkles, BookOpen, Lightbulb, UtensilsCrossed } from 'lucide-react';
import type { Message } from '../types';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  onSuggestionClick?: (text: string) => void;
}

export function ChatWindow({ messages, isLoading, onSuggestionClick }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className={`flex-1 p-4 md:p-6 scroll-smooth bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-950 ${messages.length === 0 ? 'overflow-y-hidden' : 'overflow-y-auto'}`}>
      {messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400 animate-in fade-in duration-500">
          {/* Hero Section */}
          <div className="relative mb-8">
            <div className="w-24 h-24 bg-gradient-to-br from-orange-400 to-orange-500 rounded-2xl flex items-center justify-center shadow-lg">
              <ChefHat className="w-12 h-12 text-white" />
            </div>
            <div className="absolute -bottom-1 -right-1 w-8 h-8 bg-gradient-to-br from-blue-400 to-blue-500 rounded-lg flex items-center justify-center shadow-sm">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
          </div>
          
          <h2 className="text-3xl font-bold mb-2 text-gray-800 dark:text-gray-100">
            Welcome to CookHero
          </h2>
          {/* <p className="text-center max-w-md mb-10 text-gray-600 dark:text-gray-400">
            Your AI-powered cooking assistant. I can help you find recipes, provide cooking tips, and suggest dishes based on ingredients you have.
          </p> */}
          
          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-3xl mb-8">
            <FeatureCard 
              icon={<BookOpen className="w-5 h-5" />}
              title="Recipe Search"
              description="Find detailed cooking instructions"
            />
            <FeatureCard 
              icon={<Lightbulb className="w-5 h-5" />}
              title="Cooking Tips"
              description="Learn professional techniques"
            />
            <FeatureCard 
              icon={<UtensilsCrossed className="w-5 h-5" />}
              title="Ingredient Match"
              description="Discover dishes you can make"
            />
          </div>
          
          {/* Suggestion Chips */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
            <SuggestionChip text="红烧肉怎么做？" emoji="🥩" onClick={onSuggestionClick} />
            <SuggestionChip text="鸡蛋和西红柿能做什么？" emoji="🥚" onClick={onSuggestionClick} />
            <SuggestionChip text="推荐一道健康晚餐" emoji="🥗" onClick={onSuggestionClick} />
            <SuggestionChip text="如何让炒菜更香？" emoji="✨" onClick={onSuggestionClick} />
          </div>
        </div>
      ) : (
        <div className="max-w-3xl mx-auto w-full">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {/* Loading indicator */}
          {isLoading && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
             <div className="flex gap-4 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-400 to-orange-500 flex items-center justify-center shrink-0 shadow-sm">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                </div>
                <div className="space-y-2 pt-2">
                   <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                     <span className="animate-pulse">CookHero is thinking...</span>
                   </div>
                </div>
             </div>
          )}
        </div>
      )}
      <div ref={messagesEndRef} className="h-4" />
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-center shadow-sm">
      <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center mx-auto mb-3 text-orange-500">
        {icon}
      </div>
      <h3 className="font-medium text-gray-800 dark:text-gray-100 mb-1">{title}</h3>
      <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>
    </div>
  );
}

function SuggestionChip({ text, emoji, onClick }: { text: string; emoji: string; onClick?: (text: string) => void }) {
  return (
    <button
      className="flex items-center gap-3 px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-left hover:border-orange-300 dark:hover:border-orange-700 hover:shadow-md transition-all duration-200 text-gray-700 dark:text-gray-300 group"
      onClick={() => onClick?.(text)}
    >
      <span className="text-xl group-hover:scale-110 transition-transform">{emoji}</span>
      <span>{text}</span>
    </button>
  );
}

