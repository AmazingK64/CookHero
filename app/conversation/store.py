import uuid
from typing import Dict, List, Optional

from app.conversation.models import Conversation, Message


class ConversationStore:
    """In-memory store for conversations (swap with DB/Redis in production)."""

    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}

    def get_or_create(self, conversation_id: Optional[str] = None) -> Conversation:
        if conversation_id and conversation_id in self._conversations:
            return self._conversations[conversation_id]

        conv_id = conversation_id or str(uuid.uuid4())
        conversation = Conversation(id=conv_id)
        self._conversations[conv_id] = conversation
        return conversation

    def add_message(
        self,
        conversation: Conversation,
        message: Message,
        max_messages: Optional[int] = None,
    ) -> None:
        conversation.messages.append(message)
        conversation.updated_at = message.timestamp
        if max_messages and len(conversation.messages) > max_messages:
            conversation.messages = conversation.messages[-max_messages:]

    def get_history(self, conversation_id: str) -> Optional[list[dict]]:
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return None
        return conversation.to_history()

    def clear(self, conversation_id: str) -> bool:
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False

    def list_conversations(self) -> List[dict]:
        result = []
        for conv in self._conversations.values():
            result.append(
                {
                    "id": conv.id,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages),
                    "last_message_preview": (
                        conv.messages[-1].content[:80] if conv.messages else ""
                    ),
                }
            )
        return sorted(result, key=lambda x: x["updated_at"], reverse=True)


conversation_store = ConversationStore()
