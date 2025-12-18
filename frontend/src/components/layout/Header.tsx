/**
 * Header Component
 * Top navigation bar with app branding
 */

import { APP_NAME, APP_EMOJI } from '../../constants';

export interface HeaderProps {
  onClear: () => void;
  conversationId?: string;
}

export function Header({ onClear, conversationId }: HeaderProps) {
  const handleCopyId = () => {
    if (conversationId) {
      navigator.clipboard.writeText(conversationId);
    }
  };

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="flex items-center gap-3">
        <span className="text-3xl">{APP_EMOJI}</span>
        <div>
          <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100">
            {APP_NAME}
          </h1>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            你的智能烹饪助手
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {conversationId && (
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
            <span className="font-mono break-all max-w-[120px] truncate">
              {conversationId}
            </span>
            <button
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              onClick={handleCopyId}
              title="复制会话 ID"
              aria-label="Copy conversation ID"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5h9m-9 4h9m-9 4h9m-9 4h6m-9 0h.01M6 5h.01M6 9h.01M6 13h.01"
                />
              </svg>
            </button>
          </div>
        )}

        <button
          onClick={onClear}
          className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          title="开始新对话"
          aria-label="Start new conversation"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          <span className="hidden sm:inline">新对话</span>
        </button>
      </div>
    </header>
  );
}
