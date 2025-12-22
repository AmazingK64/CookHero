# from __future__ import annotations

# import random
# from dataclasses import dataclass
# from typing import Any, AsyncIterator, Protocol, Sequence
# from langchain_core.runnables import Runnable
# from langchain_core.outputs import ChatResult
# from typing import Any, AsyncIterator, List, Union
# from langchain_core.messages import BaseMessage
# from langchain_openai import ChatOpenAI

# from app.config.llm_config import LLMConfig, LLMProfileConfig, LLMType


# class ModelSelectionStrategy(Protocol):
#     def choose(self, model_names: Sequence[str]) -> str: ...


# @dataclass(frozen=True)
# class RandomChoiceStrategy:
#     def choose(self, model_names: Sequence[str]) -> str:
#         if not model_names:
#             raise ValueError("model_names cannot be empty")
#         return random.choice(list(model_names))


# @dataclass
# class ChatOpenAIProvider:
#     llm_config: LLMConfig
#     selector: ModelSelectionStrategy = RandomChoiceStrategy()

#     def profile(self, llm_type: LLMType | str | None) -> LLMProfileConfig:
#         return self.llm_config.get_profile(llm_type)

#     def choose_model(self, llm_type: LLMType | str | None) -> str:
#         profile = self.profile(llm_type)
#         return self.selector.choose(profile.model_names)

#     def create_base_llm(
#         self,
#         llm_type: LLMType | str | None,
#         *,
#         streaming: bool = False,
#         temperature: float | None = None,
#         max_tokens: int | None = None,
#         **kwargs: Any,
#     ) -> ChatOpenAI:
#         profile = self.profile(llm_type)
#         return ChatOpenAI(
#             model=profile.pick_default_model(),
#             api_key=profile.api_key,  # type: ignore
#             base_url=profile.base_url,
#             temperature=profile.temperature if temperature is None else temperature,
#             max_completion_tokens=profile.max_tokens if max_tokens is None else max_tokens,
#             streaming=streaming,
#             **kwargs,
#         )

#     def bind_for_call(self, llm: ChatOpenAI, llm_type: LLMType | str | None) -> ChatOpenAI:
#         model = self.choose_model(llm_type)
#         return llm.bind(model=model) # type: ignore


# class DynamicChatInvoker:
#     """
#     A wrapper to dynamically bind ChatOpenAI model before each call.
#     """

#     def __init__(
#         self,
#         provider: ChatOpenAIProvider,
#         llm_type: LLMType | str | None,
#         base_llm: ChatOpenAI,
#     ):
#         self._provider = provider
#         self._llm_type = llm_type
#         self._base_llm = base_llm

#     def _bind(self) -> ChatOpenAI:
#         return self._provider.bind_for_call(self._base_llm, self._llm_type)

#     def invoke(self, *args: Any, **kwargs: Any) -> Any:
#         return self._bind().invoke(*args, **kwargs)

#     async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
#         return await self._bind().ainvoke(*args, **kwargs)

#     def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
#         return self._bind().astream(*args, **kwargs)

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
    Supports tool binding and other ChatOpenAI methods.
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
        self._bound_tools: list[Any] = []  # Store bound tools
        self._tool_choice: Any = None  # Store tool_choice parameter

    def _bind(self) -> ChatOpenAI:
        """Bind model and tools dynamically."""
        llm = self._provider.bind_for_call(self._base_llm, self._llm_type)
        
        # If tools were bound, apply them
        if self._bound_tools:
            bind_kwargs: dict[str, Any] = {"tools": self._bound_tools}
            if self._tool_choice is not None:
                bind_kwargs["tool_choice"] = self._tool_choice
            llm = llm.bind(**bind_kwargs)  # type: ignore
        
        return llm

    def bind_tools(
        self,
        tools: Sequence[Any],
        *,
        tool_choice: Any = None,
        **kwargs: Any,
    ) -> "DynamicChatInvoker":
        """
        Bind tools to the invoker. Returns a new instance with tools bound.
        
        Args:
            tools: Sequence of tools to bind
            tool_choice: Optional tool choice parameter
            **kwargs: Additional binding parameters
            
        Returns:
            New DynamicChatInvoker instance with tools bound
        """
        # Create a new instance to maintain immutability
        new_invoker = DynamicChatInvoker(
            self._provider,
            self._llm_type,
            self._base_llm,
        )
        new_invoker._bound_tools = list(tools)
        new_invoker._tool_choice = tool_choice
        return new_invoker

    def bind(self, **kwargs: Any) -> "DynamicChatInvoker":
        """
        Generic bind method for other parameters.
        
        Args:
            **kwargs: Parameters to bind to the base LLM
            
        Returns:
            New DynamicChatInvoker instance with parameters bound
        """
        new_base_llm = self._base_llm.bind(**kwargs)  # type: ignore
        new_invoker = DynamicChatInvoker(
            self._provider,
            self._llm_type,
            new_base_llm,
        )
        new_invoker._bound_tools = self._bound_tools.copy()
        new_invoker._tool_choice = self._tool_choice
        return new_invoker

    def invoke(self, *args: Any, **kwargs: Any) -> Any:
        """Invoke the LLM with dynamic model binding."""
        return self._bind().invoke(*args, **kwargs)

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        """Async invoke the LLM with dynamic model binding."""
        return await self._bind().ainvoke(*args, **kwargs)

    def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        """Stream responses from the LLM with dynamic model binding."""
        return self._bind().astream(*args, **kwargs)

    def stream(self, *args: Any, **kwargs: Any) -> Any:
        """Sync stream responses from the LLM with dynamic model binding."""
        return self._bind().stream(*args, **kwargs)

    def batch(self, *args: Any, **kwargs: Any) -> Any:
        """Batch process multiple inputs."""
        return self._bind().batch(*args, **kwargs)

    async def abatch(self, *args: Any, **kwargs: Any) -> Any:
        """Async batch process multiple inputs."""
        return await self._bind().abatch(*args, **kwargs)

    def with_structured_output(self, *args: Any, **kwargs: Any) -> Any:
        """Enable structured output mode."""
        return self._bind().with_structured_output(*args, **kwargs)

    @property
    def base_llm(self) -> ChatOpenAI:
        """Access the underlying base LLM."""
        return self._base_llm