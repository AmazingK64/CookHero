# app/conversation/__init__.py
"""
Conversation module for CookHero.
Handles conversation flow, intent detection, query rewriting, and LLM orchestration.

Note: ContextManager has been moved to app.context module.
"""

from app.conversation.intent import IntentDetectionResult, IntentDetector, QueryIntent
from app.conversation.llm_orchestrator import LLMOrchestrator
from app.conversation.models import Conversation, Message
from app.conversation.query_rewriter import QueryRewriter
from app.conversation.repository import conversation_repository

__all__ = [
    "Conversation",
    "IntentDetectionResult",
    "IntentDetector",
    "LLMOrchestrator",
    "Message",
    "QueryIntent",
    "QueryRewriter",
    "conversation_repository",
]
