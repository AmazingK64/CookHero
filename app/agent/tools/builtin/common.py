"""
内置 Tool 集合

提供一些常用的内置 Tool 示例。
"""

import math
from datetime import datetime
from typing import Any

from app.agent.tools.base import BaseTool
from app.agent.types import ToolResult
from app.agent.registry import AgentRegistry


class CalculatorTool(BaseTool):
    """
    计算器 Tool。

    支持基本的数学运算。
    """

    name = "calculator"
    description = "执行数学计算。支持加减乘除、幂运算、三角函数等。"
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式，如 '2 + 3 * 4' 或 'math.sqrt(16)'",
            }
        },
        "required": ["expression"],
    }

    async def execute(self, expression: str = "", **kwargs) -> ToolResult:
        """执行数学计算。"""
        if not expression:
            return ToolResult(success=False, error="Expression is required")

        try:
            # 安全的数学运算环境
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "math": math,
            }

            result = eval(expression, {"__builtins__": {}}, safe_dict)

            return ToolResult(
                success=True, data={"expression": expression, "result": result}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Calculation failed: {str(e)}")


class DateTimeTool(BaseTool):
    """
    日期时间 Tool。

    获取当前日期时间或进行日期计算。
    """

    name = "datetime"
    description = "获取当前日期时间信息。"
    parameters = {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "日期时间格式，如 '%Y-%m-%d %H:%M:%S'",
                "default": "%Y-%m-%d %H:%M:%S",
            },
            "timezone": {
                "type": "string",
                "description": "时区，如 'Asia/Shanghai'",
                "default": "UTC",
            },
        },
        "required": [],
    }

    async def execute(
        self, format: str = "%Y-%m-%d %H:%M:%S", timezone: str = "UTC", **kwargs
    ) -> ToolResult:
        """获取当前日期时间。"""
        try:
            now = datetime.now()
            formatted = now.strftime(format)

            return ToolResult(
                success=True,
                data={
                    "datetime": formatted,
                    "timestamp": now.timestamp(),
                    "year": now.year,
                    "month": now.month,
                    "day": now.day,
                    "weekday": now.strftime("%A"),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get datetime: {str(e)}")


class TextProcessorTool(BaseTool):
    """
    文本处理 Tool。

    提供文本处理功能。
    """

    name = "text_processor"
    description = "处理文本：统计字数、提取关键信息等。"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "要处理的文本"},
            "operation": {
                "type": "string",
                "description": "操作类型：count_words, count_chars, to_upper, to_lower, reverse",
                "enum": [
                    "count_words",
                    "count_chars",
                    "to_upper",
                    "to_lower",
                    "reverse",
                ],
            },
        },
        "required": ["text", "operation"],
    }

    async def execute(
        self, text: str = "", operation: str = "count_chars", **kwargs
    ) -> ToolResult:
        """处理文本。"""
        if not text:
            return ToolResult(success=False, error="Text is required")

        try:
            result: Any = None

            if operation == "count_words":
                result = {"word_count": len(text.split())}
            elif operation == "count_chars":
                result = {
                    "char_count": len(text),
                    "char_count_no_spaces": len(text.replace(" ", "")),
                }
            elif operation == "to_upper":
                result = {"text": text.upper()}
            elif operation == "to_lower":
                result = {"text": text.lower()}
            elif operation == "reverse":
                result = {"text": text[::-1]}
            else:
                return ToolResult(
                    success=False, error=f"Unknown operation: {operation}"
                )

            return ToolResult(success=True, data=result)

        except Exception as e:
            return ToolResult(success=False, error=f"Text processing failed: {str(e)}")


def register_builtin_tools():
    """注册所有内置 Tools。"""
    AgentRegistry.register_tool(CalculatorTool())
    AgentRegistry.register_tool(DateTimeTool())
    AgentRegistry.register_tool(TextProcessorTool())
