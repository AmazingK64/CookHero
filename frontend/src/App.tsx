// src/App.tsx
import { useEffect, useState, useCallback, useRef } from 'react';
import type { ReactElement } from 'react';
import { BarChart3, BookOpen, Menu, LogOut, MessageSquare } from 'lucide-react';
import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ChatWindow, ChatInput, Sidebar, KnowledgePanel } from './components';
import { useTheme, useAuth, useConversationContext } from './contexts';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import EvaluationPage from './pages/Evaluation';

/**
 * Chat view component - handles both new chat and existing conversation
 */
function ChatView() {
  const { id: urlConversationId } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const {
    messages,
    conversationId,
    isLoading,
    isStreaming,
    error,
    sendMessage,
    selectConversation,
    stopGeneration,
  } = useConversationContext();

  const [suggestionText, setSuggestionText] = useState<string>('');
  
  // Track if we've done initial sync to avoid re-triggering on subsequent renders
  const initialSyncDone = useRef(false);

  // Sync URL conversation ID with hook state on mount or when URL changes
  // This handles page refresh and direct URL access
  useEffect(() => {
    // Only sync from URL to state, not the other way around
    // MainLayout.handleSelectConversation handles navigation when user clicks
    if (urlConversationId && urlConversationId !== conversationId) {
      selectConversation(urlConversationId);
    }
    initialSyncDone.current = true;
  }, [urlConversationId]); // Only depend on URL changes, not conversationId

  // Update URL when a NEW conversation is created (temp -> real ID)
  // This only triggers when sending the first message creates a new conversation
  useEffect(() => {
    if (
      initialSyncDone.current &&
      conversationId &&
      !conversationId.startsWith('temp-') &&
      !urlConversationId // Only update URL if we're on /chat (no ID in URL yet)
    ) {
      navigate(`/chat/${conversationId}`, { replace: true });
    }
  }, [conversationId, urlConversationId, navigate]);

  const handleSuggestionClick = (text: string) => {
    setSuggestionText(text);
  };

  const handleSuggestionConsumed = () => {
    setSuggestionText('');
  };

  return (
    <>
      {error && (
        <div className="absolute top-4 left-4 right-4 z-10 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 text-sm">
          ⚠️ {error}
        </div>
      )}
      
      <ChatWindow messages={messages} isLoading={isLoading} onSuggestionClick={handleSuggestionClick} />
      
      <div className="p-4 max-w-4xl w-full mx-auto">
        <ChatInput
          onSend={sendMessage}
          onCancel={stopGeneration}
          disabled={isLoading}
          isStreaming={isStreaming}
          placeholder="Ask CookHero anything about cooking..."
          externalValue={suggestionText}
          onExternalValueConsumed={handleSuggestionConsumed}
        />
        <div className="text-center text-xs text-gray-400 mt-2">
          CookHero can make mistakes. Consider checking important information.
        </div>
      </div>
    </>
  );
}

/**
 * Main layout component with sidebar
 */
function MainLayout({ children }: { children: React.ReactNode }) {
  const { username, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const {
    conversationId,
    conversations,
    totalConversations,
    hasMoreConversations,
    selectConversation,
    clearMessages,
    removeConversation,
    renameConversation,
    loadMoreConversations,
  } = useConversationContext();

  const { isDark, toggleTheme } = useTheme();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Determine current view from pathname
  const isKnowledgeView = location.pathname === '/knowledge';
  const isEvaluationView = location.pathname === '/evaluation';

  const handleNewChat = useCallback(() => {
    clearMessages();
    navigate('/chat');
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  }, [clearMessages, navigate]);

  const handleSelectConversation = useCallback((id: string) => {
    selectConversation(id);
    navigate(`/chat/${id}`);
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false);
    }
  }, [selectConversation, navigate]);

  const handleLogout = useCallback(() => {
    logout();
    navigate('/login');
  }, [logout, navigate]);

  const toggleMainView = useCallback(() => {
    if (isKnowledgeView || isEvaluationView) {
      // Return to chat - if there's a current conversation, go to it
      if (conversationId && !conversationId.startsWith('temp-')) {
        navigate(`/chat/${conversationId}`);
      } else {
        navigate('/chat');
      }
    } else {
      navigate('/knowledge');
    }
  }, [isKnowledgeView, isEvaluationView, conversationId, navigate]);

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors duration-200">
      <Sidebar
        isOpen={isSidebarOpen}
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        conversations={conversations}
        totalConversations={totalConversations}
        hasMoreConversations={hasMoreConversations}
        onLoadMoreConversations={loadMoreConversations}
        currentConversationId={conversationId || null}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={removeConversation}
        onRenameConversation={renameConversation}
        isDark={isDark}
        toggleTheme={toggleTheme}
      />

      <div className="flex-1 flex flex-col h-full relative">
        <header className="h-14 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm flex items-center px-4 justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 -ml-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              title={isSidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
            >
              <Menu className="w-5 h-5" />
            </button>
            {/* <div className="flex items-center gap-2">
              <span className="text-2xl">🍳</span>
              <h1 className="font-bold text-gray-800 dark:text-gray-100">CookHero</h1>
            </div> */}
          </div>
          <div className="flex items-center gap-1.5 sm:gap-3 text-xs text-gray-600 dark:text-gray-300 overflow-hidden">
            {!isKnowledgeView && !isEvaluationView && conversationId && (
              <span className="hidden sm:inline font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded truncate" title={conversationId}>
                ID: {conversationId}
              </span>
            )}
            <button
              onClick={() => navigate('/evaluation')}
              className={`flex items-center gap-1 px-2 sm:px-3 py-1 rounded-full border transition-colors shrink-0 ${
                isEvaluationView
                  ? 'border-orange-400 bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-200 dark:border-orange-600'
                  : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span className="hidden sm:inline">评估</span>
            </button>
            <button
              onClick={toggleMainView}
              className={`flex items-center gap-1 px-2 sm:px-3 py-1 rounded-full border transition-colors shrink-0 ${
                isKnowledgeView
                  ? 'border-orange-400 bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-200 dark:border-orange-600'
                  : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {isKnowledgeView ? (
                <>
                  <MessageSquare className="w-4 h-4" />
                  <span className="hidden sm:inline">返回对话</span>
                </>
              ) : (
                <>
                  <BookOpen className="w-4 h-4" />
                  <span className="hidden sm:inline">知识库</span>
                </>
              )}
            </button>
            {username && (
              <div className="flex items-center gap-1 sm:gap-2 bg-gray-100 dark:bg-gray-800 px-2 sm:px-3 py-1 rounded-full shrink-0">
                <span className="font-semibold hidden sm:inline">{username}</span>
                <button
                  onClick={handleLogout}
                  className="text-gray-500 hover:text-gray-800 dark:hover:text-gray-100 flex items-center gap-1"
                  title="Log out"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden md:inline">Logout</span>
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 flex flex-col overflow-hidden relative bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-950">
          {children}
        </main>
      </div>
    </div>
  );
}

function RequireAuth({ children }: { children: ReactElement }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

function App() {
  return (
    <Routes>
      {/* Protected routes with main layout */}
      <Route
        path="/chat"
        element={
          <RequireAuth>
            <MainLayout>
              <ChatView />
            </MainLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/chat/:id"
        element={
          <RequireAuth>
            <MainLayout>
              <ChatView />
            </MainLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/knowledge"
        element={
          <RequireAuth>
            <MainLayout>
              <KnowledgePanel />
            </MainLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/evaluation"
        element={
          <RequireAuth>
            <MainLayout>
              <EvaluationPage />
            </MainLayout>
          </RequireAuth>
        }
      />
      {/* Auth routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      {/* Default redirect to chat */}
      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}

export default App;
