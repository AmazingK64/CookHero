import logging
from typing import List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import LLMProviderConfig, settings

logger = logging.getLogger(__name__)

HISTORY_REWRITE_PROMPT_TEMPLATE = """
<|system|>
你是 CookHero 的「检索查询重写器」，负责将用户的当前问题结合对话历史，重写为**完整、独立、自然、适合菜谱与烹饪知识库检索的一句话查询**。
你的输出将直接用于语义检索，因此必须**准确、明确、无歧义**。

【重写原则（必须遵守）】

1. **消解指代**
- 将“它 / 这个 / 那个 / 第一个 / 上一道”等指代词替换为具体菜品、食材或对象
- 对象必须来自对话历史，禁止猜测

2. **补全必要上下文**
- 若当前问题无法独立理解，需补充前文中**直接相关且必要**的信息
- 只补充与“做什么 / 怎么做 / 推荐什么”直接相关的内容

3. **保持自然语言**
- 输出必须是完整、通顺的一句话
- 使用自然问句或陈述句
- 禁止关键词堆砌、列表、标签

4. **语义扩展（仅限抽象概念）**
- 可将抽象偏好转写为明确含义：
  - “清淡” → “口味清淡、不油腻”
  - “荤素搭配” → “既有肉类又有蔬菜的菜品”
- 不得引入新的具体条件

5. **严格禁止幻觉**
- 未出现的信息一律不得添加
- 不要擅自加入“简单 / 快速 / 健康 / 低脂 / 辣”等描述

6. **模糊问题的安全澄清**
- 若问题本身过于模糊（如“我饿了”“吃点啥”）
- 重写为**不设限、不假设**的通用请求

【示例（仅用于理解规则，不要照抄）】

示例1（指代消解）  
    对话历史：  
    User: 推荐几道鸡胸肉的做法  
    Assistant: 可以试试鸡胸肉沙拉、黑椒鸡胸肉、鸡胸肉炒蔬菜  
    当前问题：第二个怎么做  
    → 黑椒鸡胸肉的详细做法是什么？

示例2（承接追问）  
    对话历史：  
    User: 红烧肉怎么做  
    Assistant: 需要小火慢炖  
    当前问题：要炖多久  
    → 红烧肉一般需要炖多长时间？

示例3（模糊问题）  
对话历史：无  
当前问题：我饿了  
→ 你能推荐一些可以在家制作的菜谱吗？

示例4（抽象偏好扩展）  
对话历史：无  
当前问题：推荐点清淡的菜  
→ 有哪些口味清淡、不油腻的菜品？

【输出要求（强约束）】

- 只输出 **1 句** 重写后的查询
- 禁止前缀、后缀、解释、Markdown、换行
- 不要重复“根据对话历史”“请问”等多余话语

<|user|>
【对话历史】
{history}

【当前问题】
{query}
<|assistant|>
"""

HISTORY_REWRITE_PROMPT = ChatPromptTemplate.from_template(HISTORY_REWRITE_PROMPT_TEMPLATE)


class QueryRewriter:
    """History-aware query rewriting for conversation-driven retrieval."""

    def __init__(self, llm_config: LLMProviderConfig | None = None):
        self.llm_config = llm_config or settings.llm
        if not self.llm_config.api_key:
            raise ValueError("LLM API key must be provided for query rewriting.")

        self.rewrite_llm = ChatOpenAI(
            model=self.llm_config.model_name,
            temperature=0.0,
            max_tokens=self.llm_config.max_tokens,  # type: ignore
            api_key=self.llm_config.api_key,  # type: ignore
            base_url=self.llm_config.base_url,
        )

    def rewrite_with_history(
        self, current_query: str, history_text: str
    ) -> str:
        if not history_text.strip():
            return current_query

        try:
            chain = HISTORY_REWRITE_PROMPT | self.rewrite_llm | StrOutputParser()
            rewritten = (
                chain.invoke({"history": history_text, "query": current_query}).strip()
            )

            if rewritten and rewritten != current_query:
                logger.info(
                    "query rewrite: '%s' -> '%s'",
                    current_query[:80],
                    rewritten[:80],
                )
                return rewritten

        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to rewrite query with history: %s", exc)

        return current_query
