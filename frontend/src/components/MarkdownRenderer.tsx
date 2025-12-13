// src/components/MarkdownRenderer.tsx
/**
 * Simple Markdown renderer component
 */

import { useMemo } from 'react';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const htmlContent = useMemo(() => {
    if (!content) return '';
    
    let html = content;
    
    // Escape HTML
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    
    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2 class="text-xl font-semibold mt-4 mb-2">$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>');
    
    // Bold and italic
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold">$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    
    // Code blocks
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, 
      '<pre class="bg-gray-800 text-gray-100 p-3 rounded-lg overflow-x-auto my-2"><code>$2</code></pre>');
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, 
      '<code class="bg-gray-200 text-gray-800 px-1.5 py-0.5 rounded text-sm">$1</code>');
    
    // Unordered lists
    html = html.replace(/^[\-\*] (.+)$/gm, '<li class="ml-4 list-disc">$1</li>');
    
    // Ordered lists
    html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>');
    
    // Wrap consecutive list items
    html = html.replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul class="my-2">$&</ul>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, 
      '<a href="$2" class="text-orange-600 hover:underline" target="_blank" rel="noopener">$1</a>');
    
    // Line breaks (but not inside code blocks or lists)
    html = html.replace(/\n\n/g, '</p><p class="my-2">');
    html = html.replace(/\n(?!<)/g, '<br/>');
    
    // Wrap in paragraph if not already wrapped
    if (!html.startsWith('<')) {
      html = `<p class="my-2">${html}</p>`;
    }
    
    return html;
  }, [content]);

  return (
    <div 
      className="markdown-content"
      dangerouslySetInnerHTML={{ __html: htmlContent }} 
    />
  );
}
