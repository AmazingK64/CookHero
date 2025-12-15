import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Message:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    sources: Optional[List[Dict]] = None
    intent: Optional[str] = None
    thinking: Optional[List[str]] = None


@dataclass
class Conversation:
    """Represents a conversation session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_history(self) -> list[dict]:
        """Return serialized history for API responses."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sources": msg.sources,
                "intent": msg.intent,
                "thinking": msg.thinking,
            }
            for msg in self.messages
        ]
