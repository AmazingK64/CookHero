# app/rag/pipeline/metadata_filter.py
"""
LLM-driven metadata expression generator.
Combines the user query, available metadata values, and Milvus reference docs
to produce a ready-to-use boolean expression string for the vector store `expr` field.
"""
import logging
import re
from pathlib import Path
from typing import Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


FILTER_EXPRESSION_PROMPT = ChatPromptTemplate.from_template(
"""
<|system|>
你是 CookHero 的「Milvus 元数据过滤表达式生成器」，负责根据用户查询生成一个**可直接用于 Milvus `expr` 参数的布尔过滤表达式**。

你的目标是：**只在“明确且有把握”的情况下使用元数据过滤**，否则宁可不加过滤。

【核心原则（最重要）】

- 元数据过滤是**精确约束**，不是语义补全
- 只有当用户意图中**明确表达了可映射到元数据字段的条件**时，才生成过滤表达式
- 若条件不明确、歧义较大、或可能误伤召回，必须返回 `NONE`

【可使用的字段（严格限制）】

你**只能**使用以下 metadata 字段：
- category
- dish_name
- difficulty
禁止使用任何未列出的字段。

 **所有对应的取值必须严格来自【可用元数据取值】部分，禁止任何形式的猜测或扩展。**

【字段使用规范】

1. **category**
- 仅在用户明确指定菜系 / 菜品大类时使用
- 示例：川菜、家常菜、凉菜
- 不要从“场景”或“口味”中推断 category

2. **dish_name**
- 仅在用户明确提及具体菜名时使用
- 可以使用 `LIKE` / `ILIKE` 进行模糊匹配
- 不要从食材或描述中猜测菜名

3. **difficulty**
- 这是一个**高风险字段**
- 只有在用户直接提到“简单 / 新手 / 难 / 复杂”等难度要求时才允许使用
- 否则一律不要使用 difficulty

【逻辑运算规则】

- 使用 `AND / OR / NOT`
- 仅在**每个条件都高度确定**时才使用 `AND`
- 若多个条件存在不确定性，优先只保留最明确的一个
- 必要时使用括号明确优先级

【输出规则（强约束）】

- 输出必须是 **一行、纯文本、可执行的 Milvus 过滤表达式**
- 输出的属性和值必须严格匹配【可用元数据取值】部分
- 禁止任何解释、注释、前后缀或 Markdown
- 如果无法确定任何过滤条件，返回：`NONE`

【Milvus 过滤表达式参考】
{reference_material}

【可用元数据取值】
{metadata_schema}

<|user|>
用户查询：{query}
<|assistant|>
"""
)


REFERENCE_DIR = Path(__file__).resolve().parent / "reference"
REFERENCE_FILES = ("operators.md",)


class MetadataFilterExtractor:
    def __init__(self, model_name: str, max_tokens: int, api_key: str, base_url: str | None = None):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0,
            max_tokens=max_tokens,  # type: ignore
            api_key=api_key,
            base_url=base_url or None,
        )
        self.reference_material = self._load_reference_material()

    def build_filter_expression(self, query: str, metadata_catalog: Dict[str, Dict[str, List[str]]]) -> str | None:
        if not metadata_catalog:
            return None

        metadata_schema = self._summarize_metadata(metadata_catalog)
        prompt = FILTER_EXPRESSION_PROMPT.format(
            metadata_schema=metadata_schema,
            reference_material=self.reference_material,
            query=query,
        )
        try:
            response = self.llm.invoke(prompt)
            raw = response.content
            if not isinstance(raw, str):
                logger.warning("LLM response is not string, casting to str.")
                raw = str(raw)

            expression = self._clean_expression(raw)
            logger.info("Generated metadata expression: %s", expression or "NONE")
            return expression
        except Exception as exc:
            logger.warning("Metadata expression generation failed: %s", exc)
            return None

    def _load_reference_material(self) -> str:
        sections: List[str] = []
        for filename in REFERENCE_FILES:
            path = REFERENCE_DIR / filename
            try:
                sections.append(path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                logger.warning("Reference file not found: %s", path)
            except Exception as exc:
                logger.warning("Failed to read reference file %s: %s", path, exc)
        return "\n\n".join(sections)

    @staticmethod
    def _summarize_metadata(metadata_catalog: Dict[str, Dict[str, List[str]]]) -> str:
        lines = []
        for source, metadata in metadata_catalog.items():
            lines.append(f"来源: {source}")
            for key, values in metadata.items():
                sample = "、".join(values)
                lines.append(f"- {key} (共{len(values)}个): {sample}")
        return "\n".join(lines)

    @staticmethod
    def _clean_expression(raw_text: str) -> str | None:
        text = raw_text.strip()
        fence_pattern = r"```(?:[a-zA-Z0-9_+-]+)?\s*([\s\S]*?)```"
        match = re.search(fence_pattern, text)
        if match:
            text = match.group(1).strip()

        if text.startswith("\"") and text.endswith("\"") and len(text) >= 2:
            text = text[1:-1].strip()

        if text.upper() == "NONE" or not text:
            return None

        return text

