from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class LLMType(str, Enum):
    FAST = "fast"
    NORMAL = "normal"


class LLMProfileConfig(BaseModel):

    base_url: Optional[str] = "https://api.siliconflow.cn/v1"
    api_key: Optional[str] = None

    model_names: list[str] = Field(
        default_factory=lambda: ["deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"]
    )

    temperature: float = 1.0
    max_tokens: int = 131072


    def pick_default_model(self) -> str:
        return self.model_names[0]


class FastLLMConfig(LLMProfileConfig):
    """Fast LLM 配置（更偏向低延迟/低成本）。"""


class NormalLLMConfig(LLMProfileConfig):
    """普通 LLM 配置（更偏向质量/通用）。"""


class LLMConfig(BaseModel):
    """分层 LLM 配置：fast/normal 两类。"""

    fast: FastLLMConfig = Field(default_factory=FastLLMConfig)
    normal: NormalLLMConfig = Field(default_factory=NormalLLMConfig)

    default_type: LLMType = LLMType.NORMAL

    def get_profile(self, llm_type: LLMType | str | None) -> LLMProfileConfig:
        if llm_type is None:
            llm_type = self.default_type
        if isinstance(llm_type, str):
            llm_type = LLMType(llm_type)
        return self.fast if llm_type == LLMType.FAST else self.normal
