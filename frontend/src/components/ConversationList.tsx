import type { ConversationSummary } from '../types';

interface ConversationListProps {
  conversations: ConversationSummary[];
  activeId?: string;
  onSelect: (id: string) => void;
}

export function ConversationList({ conversations, activeId, onSelect }: ConversationListProps) {
  return (
    <aside className="w-72 border-r border-gray-200 bg-white flex flex-col">
      <div className="px-4 py-3 border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-700">会话列表</h2>
        <p className="text-xs text-gray-500">点击切换不同会话</p>
      </div>
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-sm text-gray-500">暂无历史会话</div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {conversations.map((conv) => {
              const isActive = conv.id === activeId;
              const updated = new Date(conv.updated_at).toLocaleString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit',
              });
              return (
                <li key={conv.id}>
                  <button
                    onClick={() => onSelect(conv.id)}
                    className={`w-full text-left px-4 py-3 transition-colors ${
                      isActive ? 'bg-orange-50 border-l-2 border-orange-500' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-mono text-gray-700 break-all">{conv.id}</span>
                      <span className="text-[11px] text-gray-400 whitespace-nowrap">{updated}</span>
                    </div>
                    {conv.last_message_preview && (
                      <p className="mt-1 text-xs text-gray-500 line-clamp-2">
                        {conv.last_message_preview}
                      </p>
                    )}
                    <div className="mt-2 text-[11px] text-gray-400">{conv.message_count} 条消息</div>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
