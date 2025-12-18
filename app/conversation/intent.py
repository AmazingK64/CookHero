import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import LLMProviderConfig, settings

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Enum representing the detected intent of a user query."""
    RECIPE_SEARCH = "recipe_search"
    COOKING_TIPS = "cooking_tips"
    INGREDIENT_INFO = "ingredient_info"
    GENERAL_CHAT = "general_chat"
    RECOMMENDATION = "recommendation"


@dataclass
class IntentDetectionResult:
    """Structured intent detection result with room for future extensions."""

    need_rag: bool
    intent: QueryIntent
    reason: str
    raw: dict


INTENT_DETECTION_PROMPT_TEMPLATE = """
<|system|>
你是 CookHero 的「用户意图识别与检索决策模块」，专门用于判断**是否需要查询烹饪知识库（RAG）**，并给出准确的意图分类。你的判断必须结合：
- 用户的【当前问题】
- 已压缩/整理后的【对话历史上下文】
你的目标不是泛化分类，而是**为“是否检索菜谱与烹饪知识”做决策**。

【核心决策原则（最重要）】

只有当**当前问题需要依赖具体菜谱、做法步骤、烹饪技巧或可执行方案**时，才将 need_rag 设为 true。

如果仅是：
- 观点性、解释性、确认性
- 闲聊或情绪回应
- 与“如何做菜”无直接关系
则 need_rag 必须为 false。

【need_rag = true 的典型情况】

满足以下任一情况即可：
1. **菜谱 / 做法查询**
   - 明确询问某道菜怎么做、步骤、火候、时间
   - “X 怎么做”“做 X 需要什么”
2. **基于食材 / 条件的可执行建议**
   - “有 A、B、C 能做什么菜”
   - “减脂期间晚餐推荐做什么”
3. **烹饪技巧与操作问题**
   - 处理方法、口味调整、失败补救
   - 时间、温度、器具、流程相关问题
4. **承接式问题（需结合上下文）**
   - 使用指代或省略：“这个怎么做”“第二种呢”
   - 基于之前推荐继续追问细节

【need_rag = false 的典型情况】

1. **非烹饪知识库范围的问题**
   - 营养学、历史文化、来源介绍
   - 食材百科但不涉及“如何烹饪”
2. **纯对话或流程控制**
   - 闲聊、感谢、寒暄
   - “好的”“明白了”“继续”
3. **确认 / 澄清 / 选择类问题**
   - “这个可以吗？”
   - “就用第一个方案”
4. **与烹饪无关的内容**

【intent 分类说明】

intent 用于语义标签，除了general_chat外均表示需要 RAG 支持（即 need_rag 为 true）：
- recipe_search  
  查询具体菜品、完整做法、步骤流程
- cooking_tips  
  烹饪技巧、经验、火候、调味、失败处理
- ingredient_info  
  食材相关问题（处理方式才算 RAG；营养/来源不算）
- recommendation  
  菜品推荐、菜单搭配、场景化建议
- general_chat  
  闲聊、确认、情绪回应、非任务性对话

【输出要求（非常重要）】

- 你**必须且只能**输出一个 JSON 对象
- 不要使用 Markdown
- 不要添加任何解释性文字
- JSON 必须可被直接解析

输出格式：
{{"need_rag": true/false, "intent": "intent_type", "reason": "简短、明确的判断理由"}}

<|user|>
【对话历史】
{history}

【当前问题】
{query}
<|assistant|>
"""

INTENT_DETECTION_PROMPT = ChatPromptTemplate.from_template(INTENT_DETECTION_PROMPT_TEMPLATE)


class IntentDetector:
    """
    Detects user intent to determine if RAG retrieval is needed.
    """

    def __init__(
        self,
        llm_config: LLMProviderConfig | None = None,
        max_tokens: int = 256,
    ):
        """Initialize the intent detector with global or overridden LLM config."""
        self.llm_config = llm_config or settings.llm
        self.llm = ChatOpenAI(
            model=self.llm_config.model_name,
            temperature=0.0,  # Deterministic for classification
            max_completion_tokens=max_tokens,
            api_key=self.llm_config.api_key,  # type: ignore
            base_url=self.llm_config.base_url,
        )
        self.chain = INTENT_DETECTION_PROMPT | self.llm | StrOutputParser()
        logger.info("IntentDetector initialized")

    def detect(
        self,
        query: str,
        history_text: Optional[str] = None,
    ) -> IntentDetectionResult:
        """Detect if the query needs RAG retrieval with history awareness.

        Args:
            query: Latest user query.
            history_text: Pre-formatted history text (already concatenated by ContextManager).
        """
        history_str = history_text

        try:
            response = self.chain.invoke({"query": query, "history": history_str})
            content = response.strip()

            if content.startswith("```"):
                content = content.strip("```").strip()
                if content.startswith("json"):
                    content = content[4:].strip()

            result = json.loads(content)
            need_rag = result.get("need_rag", True)
            intent_str = result.get("intent", "general_chat")
            reason = result.get("reason", "")

            intent_map = {
                "recipe_search": QueryIntent.RECIPE_SEARCH,
                "cooking_tips": QueryIntent.COOKING_TIPS,
                "ingredient_info": QueryIntent.INGREDIENT_INFO,
                "recommendation": QueryIntent.RECOMMENDATION,
                "general_chat": QueryIntent.GENERAL_CHAT,
            }
            intent = intent_map.get(intent_str, QueryIntent.GENERAL_CHAT)

            return IntentDetectionResult(
                need_rag=need_rag,
                intent=intent,
                reason=reason,
                raw=result,
            )

        except Exception as exc:
            logger.warning(
                "Intent detection failed: %s. Defaulting to non-RAG mode.", exc
            )
            return IntentDetectionResult(
                need_rag=False,
                intent=QueryIntent.GENERAL_CHAT,
                reason="Detection failed, using default",
                raw={},
            )
