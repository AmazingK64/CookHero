from typing import AsyncGenerator, List

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from app.config import LLMProviderConfig, settings


class LLMOrchestrator:
    """Handles LLM invocation and streaming responses."""

    def __init__(self, llm_config: LLMProviderConfig | None = None):
        self.llm_config = llm_config or settings.llm
        self.llm = ChatOpenAI(
            model=self.llm_config.model_name,
            temperature=self.llm_config.temperature,
            max_completion_tokens=self.llm_config.max_tokens,
            api_key=self.llm_config.api_key,  # type: ignore
            base_url=self.llm_config.base_url,
            streaming=True,
        )

    async def stream(
        self, messages: List[BaseMessage]
    ) -> AsyncGenerator[str, None]:
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield str(chunk.content)
