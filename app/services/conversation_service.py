import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config_loader import DefaultRAGConfig
from app.rag.pipeline.intent_detector import IntentDetector, QueryIntent
from app.rag.rag_service import rag_service_instance

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    sources: Optional[List[Dict]] = None  # RAG sources if any
    intent: Optional[str] = None  # Detected intent


@dataclass
class Conversation:
    """Represents a conversation session."""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# In-memory conversation store (replace with Redis/DB for production)
_conversations: Dict[str, Conversation] = {}


SYSTEM_PROMPT = """你是 CookHero，一位友好、专业且富有耐心的烹饪助手。

**你的能力：**
1. 帮助用户查找菜谱和烹饪方法
2. 提供烹饪技巧和建议
3. 根据用户手边的食材推荐菜品
4. 解答各种厨房和烹饪相关的问题

**交互风格：**
- 始终保持友好、鼓励的语气
- 回答要简洁但信息丰富
- 使用 Markdown 格式让回答更易读
- 如果用户的问题不够明确，主动询问以获取更多信息

**注意事项：**
- 当涉及食谱查询时，你会自动从知识库中检索相关信息
- 如果知识库中没有找到相关信息，你可以基于通用烹饪知识回答
- 始终优先推荐健康、安全的烹饪方法
"""


class ConversationService:
    """
    Manages conversations with LLM and RAG integration.
    """
    
    def __init__(self):
        """Initialize the conversation service."""
        self.config = DefaultRAGConfig
        
        # Initialize LLM for general conversation
        self.llm = ChatOpenAI(
            model=self.config.llm.model_name,
            temperature=self.config.llm.temperature,
            max_completion_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key,  # type: ignore
            base_url=self.config.llm.base_url,
            streaming=True
        )
        
        # Initialize intent detector
        self.intent_detector = IntentDetector(
            model_name=self.config.llm.model_name,
            api_key=self.config.llm.api_key,  # type: ignore
            base_url=self.config.llm.base_url
        )
        
        logger.info("ConversationService initialized.")
    
    def get_or_create_conversation(self, conversation_id: Optional[str] = None) -> Conversation:
        """Get existing conversation or create a new one."""
        if conversation_id and conversation_id in _conversations:
            return _conversations[conversation_id]
        
        new_id = conversation_id or str(uuid.uuid4())
        conversation = Conversation(id=new_id)
        _conversations[new_id] = conversation
        return conversation
    
    def _build_chat_history(self, conversation: Conversation, limit: int = 10):
        """Build chat history for LLM context."""
        from langchain_core.messages import BaseMessage
        messages: List[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
        
        # Get last N messages for context
        recent_messages = conversation.messages[-limit:]
        
        for msg in recent_messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        
        return messages
    
    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message and generate a response.
        
        Yields SSE-formatted events:
        - {"type": "intent", "data": {...}} - Detected intent
        - {"type": "text", "content": "..."} - Text chunk
        - {"type": "sources", "data": [...]} - RAG sources (if any)
        - {"type": "done", "conversation_id": "..."} - Completion signal
        """
        conversation = self.get_or_create_conversation(conversation_id)
        
        # Add user message to history
        user_message = Message(role="user", content=message)
        conversation.messages.append(user_message)
        conversation.updated_at = datetime.now()
        
        # Detect intent
        need_rag, intent, reason = self.intent_detector.detect(message)
        
        # Yield intent information
        yield f"data: {json.dumps({'type': 'intent', 'data': {'need_rag': need_rag, 'intent': intent.value, 'reason': reason}})}\n\n"
        
        sources = []
        full_response = ""
        
        if need_rag:
            # Use RAG pipeline
            logger.info(f"Using RAG for query: {message}")
            
            try:
                # Get RAG response (streaming)
                response_generator = rag_service_instance.ask(message, stream=True)
                
                async for chunk in self._wrap_sync_generator(response_generator):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
                
                # TODO: Extract actual sources from RAG pipeline
                # For now, we indicate RAG was used
                sources = [{"type": "rag", "info": "Retrieved from CookHero knowledge base"}]
                
            except Exception as e:
                logger.error(f"RAG error: {e}", exc_info=True)
                # Fallback to direct LLM
                async for chunk in self._direct_llm_response(conversation, message):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        else:
            # Direct LLM conversation
            logger.info(f"Using direct LLM for query: {message}")
            async for chunk in self._direct_llm_response(conversation, message):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
        
        # Add assistant response to history
        assistant_message = Message(
            role="assistant",
            content=full_response,
            sources=sources if sources else None,
            intent=intent.value
        )
        conversation.messages.append(assistant_message)
        
        # Yield sources if any
        if sources:
            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
        
        # Yield completion signal
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation.id})}\n\n"
    
    async def _direct_llm_response(
        self,
        conversation: Conversation,
        current_message: str
    ) -> AsyncGenerator[str, None]:
        """Generate a direct LLM response without RAG."""
        chat_history = self._build_chat_history(conversation)
        chat_history.append(HumanMessage(content=current_message))
        
        async for chunk in self.llm.astream(chat_history):
            if chunk.content:
                yield str(chunk.content)
    
    async def _wrap_sync_generator(self, sync_gen):
        """Wrap a synchronous generator as async."""
        import asyncio
        
        def get_next():
            try:
                return next(sync_gen), False
            except StopIteration:
                return None, True
        
        loop = asyncio.get_event_loop()
        while True:
            result, done = await loop.run_in_executor(None, get_next)
            if done:
                break
            if result:
                yield result
    
    def get_conversation_history(self, conversation_id: str) -> Optional[List[Dict]]:
        """Get conversation history."""
        if conversation_id not in _conversations:
            return None
        
        conversation = _conversations[conversation_id]
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sources": msg.sources,
                "intent": msg.intent
            }
            for msg in conversation.messages
        ]
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation."""
        if conversation_id in _conversations:
            del _conversations[conversation_id]
            return True
        return False


# Singleton instance
conversation_service = ConversationService()
