# app/context/memory.py
"""
长期记忆管理 - Long-term Memory

基于向量存储的长期记忆系统，支持：
- 对话历史存储和检索
- 用户偏好的向量化表示
- 语义搜索历史交互

TODO 阶段二：引入 Neo4j 图谱，实现实体关系存储
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """单条记忆"""
    memory_id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # 内容
    content: str = Field(..., description="记忆内容")
    content_type: str = Field(default="conversation", description="类型：conversation/plan/feedback")
    
    # 元数据（用于过滤）
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # 向量（由 embedding 模型生成）
    embedding: Optional[List[float]] = None
    
    # 重要性分数（用于记忆筛选）
    importance: float = Field(default=0.5, ge=0, le=1)


class LongTermMemory:
    """
    长期记忆管理器
    
    阶段一实现：基于内存的简单存储
    阶段二实现：对接 Milvus 向量存储 + Neo4j 图谱
    
    核心功能：
    1. 存储对话记忆（带向量）
    2. 语义检索相关记忆
    3. 记忆重要性评估和遗忘
    """
    
    def __init__(self, user_id: str, embedding_model=None):
        """
        Args:
            user_id: 用户ID
            embedding_model: 嵌入模型，需实现 embed_query(text) -> List[float]
        """
        self.user_id = user_id
        self.embedding_model = embedding_model
        self._memories: List[MemoryEntry] = []
        self._memory_counter = 0
    
    def add_memory(
        self,
        content: str,
        content_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
    ) -> MemoryEntry:
        """
        添加一条新记忆
        
        Args:
            content: 记忆内容
            content_type: 内容类型
            metadata: 元数据
            importance: 重要性 0-1
        """
        self._memory_counter += 1
        
        # 生成向量嵌入
        embedding = None
        if self.embedding_model:
            try:
                embedding = self.embedding_model.embed_query(content)
            except Exception:
                pass  # 嵌入失败时继续，不阻塞
        
        memory = MemoryEntry(
            memory_id=f"mem_{self.user_id}_{self._memory_counter}",
            user_id=self.user_id,
            content=content,
            content_type=content_type,
            metadata=metadata or {},
            embedding=embedding,
            importance=importance,
        )
        self._memories.append(memory)
        return memory
    
    def add_conversation(
        self,
        user_message: str,
        assistant_response: str,
        session_id: Optional[str] = None,
    ) -> MemoryEntry:
        """添加对话记忆"""
        content = f"用户: {user_message}\n助手: {assistant_response}"
        return self.add_memory(
            content=content,
            content_type="conversation",
            metadata={"session_id": session_id} if session_id else {},
            importance=0.5,
        )
    
    def add_plan_memory(
        self,
        plan_type: str,
        plan_summary: str,
        plan_id: str,
    ) -> MemoryEntry:
        """添加计划相关的记忆"""
        return self.add_memory(
            content=f"[{plan_type}计划] {plan_summary}",
            content_type="plan",
            metadata={"plan_type": plan_type, "plan_id": plan_id},
            importance=0.8,  # 计划记忆更重要
        )
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        content_type: Optional[str] = None,
        min_importance: float = 0.0,
    ) -> List[MemoryEntry]:
        """
        语义搜索相关记忆
        
        Args:
            query: 查询文本
            top_k: 返回数量
            content_type: 过滤内容类型
            min_importance: 最小重要性阈值
        """
        # 过滤
        candidates = self._memories
        if content_type:
            candidates = [m for m in candidates if m.content_type == content_type]
        if min_importance > 0:
            candidates = [m for m in candidates if m.importance >= min_importance]
        
        if not candidates:
            return []
        
        # 如果有嵌入模型，做向量检索
        if self.embedding_model:
            try:
                query_embedding = self.embedding_model.embed_query(query)
                scored = []
                for m in candidates:
                    if m.embedding:
                        score = self._cosine_similarity(query_embedding, m.embedding)
                        scored.append((m, score))
                
                scored.sort(key=lambda x: x[1], reverse=True)
                return [m for m, _ in scored[:top_k]]
            except Exception:
                pass
        
        # 降级：基于关键词的简单匹配
        query_lower = query.lower()
        scored = []
        for m in candidates:
            # 简单的词重叠计算
            overlap = sum(1 for word in query_lower.split() if word in m.content.lower())
            scored.append((m, overlap))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, score in scored[:top_k] if score > 0]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_recent(self, limit: int = 10, content_type: Optional[str] = None) -> List[MemoryEntry]:
        """获取最近的记忆"""
        candidates = self._memories
        if content_type:
            candidates = [m for m in candidates if m.content_type == content_type]
        
        return sorted(candidates, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    def get_context_for_agent(self, query: str, max_entries: int = 5) -> str:
        """
        获取可注入 Agent 的记忆上下文
        
        返回格式化的字符串，包含相关历史记忆
        """
        relevant_memories = self.search(query, top_k=max_entries)
        
        if not relevant_memories:
            return ""
        
        lines = ["[相关历史记忆]"]
        for m in relevant_memories:
            time_str = m.timestamp.strftime("%Y-%m-%d")
            lines.append(f"- [{time_str}] {m.content[:200]}...")  # 截断过长内容
        
        return "\n".join(lines)
    
    def forget_old_memories(self, keep_count: int = 1000, keep_important: bool = True):
        """
        遗忘旧记忆（保持记忆库大小可控）
        
        保留策略：
        1. 保留高重要性记忆
        2. 保留最近的记忆
        """
        if len(self._memories) <= keep_count:
            return
        
        if keep_important:
            # 分离重要记忆
            important = [m for m in self._memories if m.importance >= 0.7]
            normal = [m for m in self._memories if m.importance < 0.7]
            
            # 对普通记忆按时间排序，保留最新的
            normal.sort(key=lambda m: m.timestamp, reverse=True)
            keep_normal_count = max(0, keep_count - len(important))
            
            self._memories = important + normal[:keep_normal_count]
        else:
            # 简单按时间保留
            self._memories.sort(key=lambda m: m.timestamp, reverse=True)
            self._memories = self._memories[:keep_count]
    
    def to_list(self) -> List[Dict]:
        """导出所有记忆（用于持久化）"""
        return [m.model_dump() for m in self._memories]
    
    def load_from_list(self, memories: List[Dict]):
        """从列表加载记忆（从持久化恢复）"""
        self._memories = [MemoryEntry(**m) for m in memories]
        self._memory_counter = len(self._memories)
    
    @property
    def count(self) -> int:
        """记忆总数"""
        return len(self._memories)
