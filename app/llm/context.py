# app/llm/context.py
"""
LLM call context management using contextvars.
Provides a way to pass tracking information (module_name, user_id, conversation_id)
through the call stack without modifying function signatures.
"""

from contextvars import ContextVar
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMCallContext:
    """Context information for an LLM call."""

    request_id: str  # Unique identifier for this LLM request
    module_name: str  # Name of the module making the call
    user_id: Optional[str] = None  # User ID (if available)
    conversation_id: Optional[str] = None  # Conversation ID (if available)


# Context variable for the current LLM call
_llm_context: ContextVar[Optional[LLMCallContext]] = ContextVar(
    "llm_context", default=None
)


def set_llm_context(
    module_name: str,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> LLMCallContext:
    """
    Set the context for the current LLM call.

    Args:
        module_name: Name of the module making the LLM call
        user_id: User ID (if available)
        conversation_id: Conversation ID (if available)

    Returns:
        The created LLMCallContext instance
    """
    ctx = LLMCallContext(
        request_id=str(uuid.uuid4()),
        module_name=module_name,
        user_id=user_id,
        conversation_id=conversation_id,
    )
    _llm_context.set(ctx)
    logger.debug(
        "LLM context SET: module=%s, user_id=%s, conv_id=%s",
        module_name,
        user_id,
        conversation_id[:8] if conversation_id else None,
    )
    return ctx


def get_llm_context() -> Optional[LLMCallContext]:
    """
    Get the current LLM call context.

    Returns:
        The current LLMCallContext or None if not set
    """
    ctx = _llm_context.get()
    if ctx:
        logger.debug(
            "LLM context GET: module=%s, user_id=%s, conv_id=%s",
            ctx.module_name,
            ctx.user_id,
            ctx.conversation_id[:8] if ctx.conversation_id else None,
        )
    else:
        logger.debug("LLM context GET: no context set")
    return ctx


def clear_llm_context() -> None:
    """Clear the current LLM call context."""
    _llm_context.set(None)


@contextmanager
def llm_context(
    module_name: str,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
):
    """
    Context manager for LLM call context.
    Automatically sets and clears the context.

    Usage:
        with llm_context("intent_detector", user_id="user123"):
            response = await llm.ainvoke(messages)

    Args:
        module_name: Name of the module making the LLM call
        user_id: User ID (if available)
        conversation_id: Conversation ID (if available)

    Yields:
        The created LLMCallContext instance
    """
    ctx = set_llm_context(module_name, user_id, conversation_id)
    try:
        yield ctx
    finally:
        clear_llm_context()
