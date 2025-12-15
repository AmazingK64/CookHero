from typing import Dict, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.conversation.models import Conversation


class ContextManager:
    """Builds and trims conversation context for LLM consumption."""

    def __init__(
        self,
        system_prompt: str,
        chat_history_limit: int = 1000,
        history_pairs_limit: int = 1000,
        history_text_max_len: int = 400,
    ):
        self.system_prompt = system_prompt 
        self.chat_history_limit = chat_history_limit
        self.history_pairs_limit = history_pairs_limit
        self.history_text_max_len = history_text_max_len

    def build_llm_messages(
        self,
        conversation: Conversation,
        extra_system_prompt: Optional[str] = None,
    ) -> List[BaseMessage]:
        messages: List[BaseMessage] = [SystemMessage(content=self.system_prompt)]
        recent_messages = conversation.messages[-self.chat_history_limit :]
        for msg in recent_messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                messages.append(AIMessage(content=msg.content))
        if extra_system_prompt:
            messages.append(SystemMessage(content=extra_system_prompt))
        return messages

    def build_history_pairs(
        self, conversation: Conversation, limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        recent_messages = conversation.messages[-(limit or self.history_pairs_limit) :]
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent_messages
        ]

    def build_history_text(
        self,
        conversation: Conversation,
        limit: Optional[int] = None,
        empty_placeholder: str = "(无历史对话)",
    ) -> str:
        pairs = self.build_history_pairs(conversation, limit=limit)
        if not pairs:
            return empty_placeholder

        history_parts: List[str] = []
        for msg in pairs:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if len(content) > self.history_text_max_len:
                content = content[: self.history_text_max_len] + "..."
            history_parts.append(f"{role}: {content}")
        return "\n".join(history_parts)

    def trim_history(self, conversation: Conversation, max_messages: int) -> None:
        if max_messages and len(conversation.messages) > max_messages:
            conversation.messages = conversation.messages[-max_messages:]
