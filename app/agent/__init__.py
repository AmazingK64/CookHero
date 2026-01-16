"""
Agent 模块

独立的对话处理系统，与现有 ConversationService 完全分离。
"""

from app.agent.types import (
    AgentChunk,
    AgentChunkType,
    AgentConfig,
    AgentContext,
    AgentMessage,
    AgentSession,
    SkillMeta,
    ToolCallInfo,
    ToolResult,
    ToolResultInfo,
    TraceStep,
)
from app.agent.base import BaseAgent, DefaultAgent
from app.agent.registry import AgentRegistry, register_agent, register_tool
from app.agent.service import AgentService, agent_service
from app.agent.context import (
    AgentContextBuilder,
    AgentContextCompressor,
    agent_context_builder,
    agent_context_compressor,
)
from app.agent.tools.base import BaseTool, MCPTool, ToolExecutor
from app.agent.skills.base import BaseSkill, FileSkill, InlineSkill, SkillLoader


def setup_agent_module():
    """
    初始化 Agent 模块。

    注册内置 Agent、Tool 和 Skill。
    应在应用启动时调用。
    """
    # 注册内置 Tools
    from app.agent.tools.builtin.common import register_builtin_tools

    register_builtin_tools()

    # 注册内置 Skills
    from app.agent.skills.builtin.common import register_builtin_skills

    register_builtin_skills()

    # 注册默认 Agent
    _register_default_agent()


def _register_default_agent():
    """注册默认 Agent。"""
    default_config = AgentConfig(
        name="default",
        description="通用助手 Agent，可以进行对话、使用工具完成任务。",
        system_prompt="""你是一个智能助手，可以帮助用户完成各种任务。

## 你的能力
1. 进行自然对话，回答问题
2. 使用工具完成具体任务（如计算、获取时间等）
3. 运用专业技能提供建议（如写作、代码审查等）

## 工作原则
1. 友好、专业地与用户交流
2. 仔细理解用户需求，必要时追问确认
3. 合理使用工具来完成任务
4. 给出清晰、有帮助的回答

## 使用工具的时机
- 当需要进行计算时，使用 calculator 工具
- 当需要获取当前时间时，使用 datetime 工具
- 当需要处理文本时，使用 text_processor 工具

请根据用户的问题，决定是直接回答还是使用工具。""",
        tools=["calculator", "datetime", "text_processor"],
        skills=["writing_assistant", "code_review", "problem_solving"],
        max_iterations=10,
    )

    AgentRegistry.register_agent(DefaultAgent, default_config)


__all__ = [
    # Types
    "AgentChunk",
    "AgentChunkType",
    "AgentConfig",
    "AgentContext",
    "AgentMessage",
    "AgentSession",
    "SkillMeta",
    "ToolCallInfo",
    "ToolResult",
    "ToolResultInfo",
    "TraceStep",
    # Base classes
    "BaseAgent",
    "DefaultAgent",
    "BaseTool",
    "MCPTool",
    "ToolExecutor",
    "BaseSkill",
    "FileSkill",
    "InlineSkill",
    "SkillLoader",
    # Registry
    "AgentRegistry",
    "register_agent",
    "register_tool",
    # Service
    "AgentService",
    "agent_service",
    # Context
    "AgentContextBuilder",
    "AgentContextCompressor",
    "agent_context_builder",
    "agent_context_compressor",
    # Setup
    "setup_agent_module",
]
