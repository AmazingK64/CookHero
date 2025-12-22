from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol, Sequence
from langchain_core.runnables import Runnable
from langchain_core.outputs import ChatResult
from typing import Any, AsyncIterator, List, Union
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from app.config.llm_config import LLMConfig, LLMProfileConfig, LLMType


class ModelSelectionStrategy(Protocol):
    def choose(self, model_names: Sequence[str]) -> str: ...


@dataclass(frozen=True)
class RandomChoiceStrategy:
    def choose(self, model_names: Sequence[str]) -> str:
        if not model_names:
            raise ValueError("model_names cannot be empty")
        return random.choice(list(model_names))


@dataclass
class ChatOpenAIProvider:
    llm_config: LLMConfig
    selector: ModelSelectionStrategy = RandomChoiceStrategy()

    def profile(self, llm_type: LLMType | str | None) -> LLMProfileConfig:
        return self.llm_config.get_profile(llm_type)

    def choose_model(self, llm_type: LLMType | str | None) -> str:
        profile = self.profile(llm_type)
        return self.selector.choose(profile.model_names)

    def create_base_llm(
        self,
        llm_type: LLMType | str | None,
        *,
        streaming: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatOpenAI:
        profile = self.profile(llm_type)
        return ChatOpenAI(
            model=profile.pick_default_model(),
            api_key=profile.api_key,  # type: ignore
            base_url=profile.base_url,
            temperature=profile.temperature if temperature is None else temperature,
            max_completion_tokens=profile.max_tokens if max_tokens is None else max_tokens,
            streaming=streaming,
            **kwargs,
        )

    def bind_for_call(self, llm: ChatOpenAI, llm_type: LLMType | str | None) -> ChatOpenAI:
        model = self.choose_model(llm_type)
        return llm.bind(model=model) # type: ignore


class DynamicChatInvoker:
    """
    A wrapper to dynamically bind ChatOpenAI model before each call.
    """

    def __init__(
        self,
        provider: ChatOpenAIProvider,
        llm_type: LLMType | str | None,
        base_llm: ChatOpenAI,
    ):
        self._provider = provider
        self._llm_type = llm_type
        self._base_llm = base_llm

    def _bind(self) -> ChatOpenAI:
        return self._provider.bind_for_call(self._base_llm, self._llm_type)

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        return self._bind().invoke(*args, **kwargs)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        return await self._bind().ainvoke(*args, **kwargs)

    def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        return self._bind().astream(*args, **kwargs)
