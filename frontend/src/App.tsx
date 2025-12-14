// src/App.tsx
/**
 * Main App component for CookHero
 */

import { Header, ChatWindow, ChatInput, ConversationList } from './components';
import { useConversation } from './hooks/useConversation';

function App() {
  const {
    messages,
    conversationId,
    conversations,
    isLoading,
    error,
    sendMessage,
    selectConversation,
    clearMessages,
  } = useConversation();

  return (
    <div className="flex h-screen bg-gray-50">
      <div className="flex-shrink-0">
        <ConversationList
          conversations={conversations}
          activeId={conversationId}
          onSelect={selectConversation}
        />
      </div>

      <div className="flex-1 flex flex-col">
        <Header onClear={clearMessages} conversationId={conversationId} />
        
        <main className="flex-1 flex flex-col overflow-hidden max-w-4xl w-full mx-auto">
          {error && (
            <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              ⚠️ {error}
            </div>
          )}
          
          <ChatWindow messages={messages} isLoading={isLoading} />
          
          <ChatInput
            onSend={sendMessage}
            disabled={isLoading}
            placeholder="问我任何烹饪相关的问题..."
          />
        </main>
      </div>
    </div>
  );
}

export default App;
