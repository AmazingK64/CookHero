/**
 * Tool Selector Component - Refactored
 * 
 * Tools 和 MCP 分离为两个独立的方框：
 * - Tools 方框：仅展示纯 Built-in Tools 列表
 * - MCP 方框：先展示 MCP Server 列表，点击后展示其二级菜单（该 Server 的所有 tools）
 */

import { useState, useEffect, useCallback, useRef, memo, useMemo } from 'react';
import { ChevronDown, ChevronUp, Wrench, Globe, Check, X, Server } from 'lucide-react';
import type { ToolInfo } from '../../types';
import { getAvailableTools } from '../../services/api/agent';

export interface ToolSelectorProps {
  token?: string;
  selectedTools: string[];
  onSelectionChange: (tools: string[]) => void;
  disabled?: boolean;
}

// Memoized tool chip component
const ToolChip = memo(function ToolChip({ 
  tool, 
  isSelected, 
  onToggle, 
  disabled 
}: {
  tool: ToolInfo;
  isSelected: boolean;
  onToggle: () => void;
  disabled?: boolean;
}) {
  // 对于 MCP 工具，去除前缀显示更短的名称
  const displayName = tool.type === 'mcp' 
    ? tool.name.replace(/^mcp_\w+_/, '')
    : tool.name;

  return (
    <button
      onClick={onToggle}
      disabled={disabled}
      title={tool.description}
      className={`
        flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs
        transition-colors duration-150
        ${disabled
          ? 'opacity-50 cursor-not-allowed'
          : 'cursor-pointer'
        }
        ${isSelected
          ? 'bg-purple-500 text-white'
          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
        }
      `}
    >
      {isSelected && <Check className="w-3 h-3" />}
      <span>{displayName}</span>
    </button>
  );
});

// MCP Server section with expandable tool list
const MCPServerCard = memo(function MCPServerCard({
  serverName,
  tools,
  selectedTools,
  onToggleTool,
  onToggleAll,
  disabled,
  isExpanded,
  onToggleExpand,
}: {
  serverName: string;
  tools: ToolInfo[];
  selectedTools: string[];
  onToggleTool: (name: string) => void;
  onToggleAll: (serverName: string, select: boolean) => void;
  disabled?: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
}) {
  const serverTools = tools.filter(t => t.source === serverName);
  const selectedCount = serverTools.filter(t => selectedTools.includes(t.name)).length;
  const allSelected = selectedCount === serverTools.length && serverTools.length > 0;

  return (
    <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
      {/* Server header */}
      <div 
        className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-700/50 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
        onClick={onToggleExpand}
      >
        <Server className="w-3.5 h-3.5 text-blue-500" />
        <span className="text-xs font-medium text-gray-700 dark:text-gray-300 flex-1">
          {serverName}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {selectedCount}/{serverTools.length}
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleAll(serverName, !allSelected);
          }}
          disabled={disabled}
          className={`
            px-2 py-0.5 text-xs rounded transition-colors
            ${allSelected
              ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
              : 'bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-400'
            }
            hover:bg-blue-200 dark:hover:bg-blue-900/50
          `}
        >
          {allSelected ? 'Deselect All' : 'Select All'}
        </button>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </div>

      {/* Expanded tool list */}
      {isExpanded && (
        <div className="p-2 flex flex-wrap gap-1.5 bg-gray-100 dark:bg-gray-800">
          {serverTools.map(tool => (
            <ToolChip
              key={tool.name}
              tool={tool}
              isSelected={selectedTools.includes(tool.name)}
              onToggle={() => onToggleTool(tool.name)}
              disabled={disabled}
            />
          ))}
          {serverTools.length === 0 && (
            <span className="text-xs text-gray-400">No tools available</span>
          )}
        </div>
      )}
    </div>
  );
});

export function ToolSelector({
  token,
  selectedTools,
  onSelectionChange,
  disabled = false,
}: ToolSelectorProps) {
  const [isToolsExpanded, setIsToolsExpanded] = useState(false);
  const [isMCPExpanded, setIsMCPExpanded] = useState(false);
  const [tools, setTools] = useState<ToolInfo[]>([]);
  const [mcpServers, setMcpServers] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedMCPServers, setExpandedMCPServers] = useState<Set<string>>(new Set());
  
  const hasInitialized = useRef(false);
  const previousToolsRef = useRef<ToolInfo[]>([]);

  // Load available tools
  const loadTools = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await getAvailableTools(token);
      setTools(response.tools);
      setMcpServers(response.mcp_servers);

      // Initialize selection with all tools only if this is first load
      if (!hasInitialized.current && response.tools.length > 0) {
        onSelectionChange(response.tools.map(t => t.name));
        hasInitialized.current = true;
      }
      
      previousToolsRef.current = response.tools;
    } catch (err) {
      console.error('Failed to load tools:', err);
      setError(err instanceof Error ? err.message : 'Failed to load tools');
    } finally {
      setIsLoading(false);
    }
  }, [token, onSelectionChange]);

  useEffect(() => {
    loadTools();
  }, [loadTools]);

  const handleToggleTool = useCallback((toolName: string) => {
    if (disabled) return;

    if (selectedTools.includes(toolName)) {
      onSelectionChange(selectedTools.filter(t => t !== toolName));
    } else {
      onSelectionChange([...selectedTools, toolName]);
    }
  }, [disabled, selectedTools, onSelectionChange]);

  const handleSelectAllBuiltin = useCallback(() => {
    if (disabled) return;
    const builtinNames = tools.filter(t => t.type === 'builtin').map(t => t.name);
    const mcpNames = selectedTools.filter(t => tools.find(tool => tool.name === t)?.type === 'mcp');
    onSelectionChange([...mcpNames, ...builtinNames]);
  }, [disabled, tools, selectedTools, onSelectionChange]);

  const handleClearAllBuiltin = useCallback(() => {
    if (disabled) return;
    const mcpNames = selectedTools.filter(t => tools.find(tool => tool.name === t)?.type === 'mcp');
    onSelectionChange(mcpNames);
  }, [disabled, tools, selectedTools, onSelectionChange]);

  const handleToggleMCPServer = useCallback((serverName: string, select: boolean) => {
    if (disabled) return;
    
    const serverTools = tools.filter(t => t.source === serverName).map(t => t.name);
    
    if (select) {
      const newSelection = [...selectedTools];
      serverTools.forEach(name => {
        if (!newSelection.includes(name)) {
          newSelection.push(name);
        }
      });
      onSelectionChange(newSelection);
    } else {
      onSelectionChange(selectedTools.filter(t => !serverTools.includes(t)));
    }
  }, [disabled, tools, selectedTools, onSelectionChange]);

  const handleToggleExpandMCPServer = useCallback((serverName: string) => {
    setExpandedMCPServers(prev => {
      const next = new Set(prev);
      if (next.has(serverName)) {
        next.delete(serverName);
      } else {
        next.add(serverName);
      }
      return next;
    });
  }, []);

  // Memoize grouped tools
  const { builtinTools, mcpTools } = useMemo(() => ({
    builtinTools: tools.filter(t => t.type === 'builtin'),
    mcpTools: tools.filter(t => t.type === 'mcp'),
  }), [tools]);

  const builtinSelectedCount = builtinTools.filter(t => selectedTools.includes(t.name)).length;
  const mcpSelectedCount = mcpTools.filter(t => selectedTools.includes(t.name)).length;

  return (
    <div className="mb-2">
      {/* ========== Header Row ========== */}
      <div className="flex items-center gap-3 mb-2">
        {/* Tools Header */}
        <button
          onClick={() => {
            setIsToolsExpanded(!isToolsExpanded);
            if (!isToolsExpanded) setIsMCPExpanded(false);
          }}
          disabled={isLoading}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg text-sm
            transition-colors duration-150 whitespace-nowrap
            ${isLoading
              ? 'text-gray-400 cursor-not-allowed'
              : isToolsExpanded
                ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200'
                : 'text-gray-700 dark:text-gray-300 hover:bg-purple-50 dark:hover:bg-purple-900/20'
            }
          `}
        >
          <Wrench className="w-4 h-4 text-purple-500" />
          <span className="font-medium">Tools</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            ({builtinSelectedCount}/{builtinTools.length})
          </span>
          {isToolsExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {/* MCP Header */}
        {mcpServers.length > 0 && (
          <button
            onClick={() => {
              setIsMCPExpanded(!isMCPExpanded);
              if (!isMCPExpanded) setIsToolsExpanded(false);
            }}
            disabled={isLoading}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg text-sm
              transition-colors duration-150 whitespace-nowrap
              ${isLoading
                ? 'text-gray-400 cursor-not-allowed'
                : isMCPExpanded
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/20'
              }
            `}
          >
            <Globe className="w-4 h-4 text-blue-500" />
            <span className="font-medium">MCP</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              ({mcpSelectedCount}/{mcpTools.length})
            </span>
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {mcpServers.length} server{mcpServers.length > 1 ? 's' : ''}
            </span>
            {isMCPExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* ========== Single Expanded Panel ========== */}
      {(isToolsExpanded || isMCPExpanded) && (
        <div className="bg-gray-50/50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-600">
          {/* Tools Expanded Panel */}
          {isToolsExpanded && (
            <div className="p-3">
              {isLoading ? (
                <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-2">
                  Loading tools...
                </div>
              ) : error ? (
                <div className="text-sm text-red-500 text-center py-2">
                  {error}
                </div>
              ) : builtinTools.length > 0 ? (
                <>
                  {/* Quick actions for builtin tools */}
                  <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-200 dark:border-gray-600">
                    <button
                      onClick={handleSelectAllBuiltin}
                      disabled={disabled}
                      className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors"
                    >
                      <Check className="w-3 h-3" />
                      Select All
                    </button>
                    <button
                      onClick={handleClearAllBuiltin}
                      disabled={disabled}
                      className="flex items-center gap-1 px-2 py-1 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      <X className="w-3 h-3" />
                      Clear All
                    </button>
                  </div>

                  {/* Builtin tools list */}
                  <div className="flex flex-wrap gap-2">
                    {builtinTools.map(tool => (
                      <ToolChip
                        key={tool.name}
                        tool={tool}
                        isSelected={selectedTools.includes(tool.name)}
                        onToggle={() => handleToggleTool(tool.name)}
                        disabled={disabled}
                      />
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-2">
                  No built-in tools available
                </div>
              )}
            </div>
          )}

          {/* MCP Expanded Panel */}
          {isMCPExpanded && (
            <div className="p-3 space-y-2">
              {mcpServers.map(server => (
                <MCPServerCard
                  key={server}
                  serverName={server}
                  tools={mcpTools}
                  selectedTools={selectedTools}
                  onToggleTool={handleToggleTool}
                  onToggleAll={handleToggleMCPServer}
                  disabled={disabled}
                  isExpanded={expandedMCPServers.has(server)}
                  onToggleExpand={() => handleToggleExpandMCPServer(server)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
