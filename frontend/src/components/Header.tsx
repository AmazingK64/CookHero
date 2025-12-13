// src/components/Header.tsx
/**
 * Header component with app branding and actions
 */

interface HeaderProps {
  onClear: () => void;
  conversationId?: string;
}

export function Header({ onClear, conversationId }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="text-3xl">🍳</span>
        <div>
          <h1 className="text-xl font-bold text-gray-800">CookHero</h1>
          <p className="text-xs text-gray-500">你的智能烹饪助手</p>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        {conversationId && (
          <span className="text-xs text-gray-400 hidden sm:block">
            会话: {conversationId.slice(0, 8)}...
          </span>
        )}
        
        <button
          onClick={onClear}
          className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
          title="开始新对话"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span className="hidden sm:inline">新对话</span>
        </button>
      </div>
    </header>
  );
}
