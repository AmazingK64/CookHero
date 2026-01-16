"""
Agent 模块单元测试

测试 Agent 模块的核心功能。
"""

import asyncio
import json
import pytest
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch


# 测试辅助函数
def run_async(coro):
    """在同步测试中运行异步函数。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestAgentTypes:
    """测试类型定义。"""

    def test_agent_config_creation(self):
        """测试 AgentConfig 创建。"""
        from app.agent.types import AgentConfig

        config = AgentConfig(
            name="test_agent",
            description="A test agent",
            system_prompt="You are a test agent.",
            tools=["tool1", "tool2"],
            skills=["skill1"],
            max_iterations=5,
        )

        assert config.name == "test_agent"
        assert config.description == "A test agent"
        assert len(config.tools) == 2
        assert len(config.skills) == 1
        assert config.max_iterations == 5

    def test_agent_context_creation(self):
        """测试 AgentContext 创建。"""
        from app.agent.types import AgentContext

        context = AgentContext(
            system_prompt="You are helpful.",
            user_profile="Developer",
            current_message="Hello",
        )

        assert context.system_prompt == "You are helpful."
        assert context.user_profile == "Developer"
        assert context.current_message == "Hello"
        assert context.recent_messages == []

    def test_tool_result_creation(self):
        """测试 ToolResult 创建。"""
        from app.agent.types import ToolResult

        success_result = ToolResult(success=True, data={"value": 42})
        assert success_result.success is True
        assert success_result.data["value"] == 42
        assert success_result.error is None

        error_result = ToolResult(success=False, error="Something went wrong")
        assert error_result.success is False
        assert error_result.error == "Something went wrong"

    def test_agent_chunk_types(self):
        """测试 AgentChunk 类型。"""
        from app.agent.types import AgentChunk, AgentChunkType

        content_chunk = AgentChunk(type=AgentChunkType.CONTENT, data="Hello")
        assert content_chunk.type == AgentChunkType.CONTENT
        assert content_chunk.data == "Hello"

        tool_chunk = AgentChunk(
            type=AgentChunkType.TOOL_CALL, data={"name": "calculator", "args": {}}
        )
        assert tool_chunk.type == AgentChunkType.TOOL_CALL


class TestToolBase:
    """测试 Tool 基类。"""

    def test_tool_creation(self):
        """测试 Tool 创建。"""
        from app.agent.tools.base import BaseTool
        from app.agent.types import ToolResult

        class TestTool(BaseTool):
            name = "test_tool"
            description = "A test tool"
            parameters = {
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"],
            }

            async def execute(self, input: str = "", **kwargs) -> ToolResult:
                return ToolResult(success=True, data={"echo": input})

        tool = TestTool()
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"

    def test_tool_to_openai_schema(self):
        """测试转换为 OpenAI schema。"""
        from app.agent.tools.base import BaseTool
        from app.agent.types import ToolResult

        class TestTool(BaseTool):
            name = "my_tool"
            description = "My tool description"
            parameters = {"type": "object", "properties": {}}

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult(success=True, data={})

        tool = TestTool()
        schema = tool.to_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "my_tool"
        assert schema["function"]["description"] == "My tool description"

    def test_tool_parse_arguments(self):
        """测试参数解析。"""
        from app.agent.tools.base import BaseTool
        from app.agent.types import ToolResult

        class TestTool(BaseTool):
            name = "test"
            description = "test"

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult(success=True, data={})

        tool = TestTool()

        # 解析 JSON 字符串
        args = tool.parse_arguments('{"key": "value"}')
        assert args == {"key": "value"}

        # 解析字典
        args = tool.parse_arguments({"key": "value"})
        assert args == {"key": "value"}

        # 解析无效 JSON
        args = tool.parse_arguments("invalid json")
        assert args == {}

    def test_tool_safe_execute(self):
        """测试安全执行。"""
        from app.agent.tools.base import BaseTool
        from app.agent.types import ToolResult

        class FailingTool(BaseTool):
            name = "failing"
            description = "A tool that fails"

            async def execute(self, **kwargs) -> ToolResult:
                raise ValueError("Intentional error")

        tool = FailingTool()
        result = run_async(tool.safe_execute())

        assert result.success is False
        assert "Intentional error" in result.error # type: ignore


class TestBuiltinTools:
    """测试内置 Tools。"""

    def test_calculator_tool(self):
        """测试计算器 Tool。"""
        from app.agent.tools.builtin.common import CalculatorTool

        tool = CalculatorTool()

        # 基本计算
        result = run_async(tool.execute(expression="2 + 3 * 4"))
        assert result.success is True
        assert result.data["result"] == 14

        # 使用 math 函数
        result = run_async(tool.execute(expression="math.sqrt(16)"))
        assert result.success is True
        assert result.data["result"] == 4.0

        # 空表达式
        result = run_async(tool.execute(expression=""))
        assert result.success is False

        # 无效表达式
        result = run_async(tool.execute(expression="invalid"))
        assert result.success is False

    def test_datetime_tool(self):
        """测试日期时间 Tool。"""
        from app.agent.tools.builtin.common import DateTimeTool

        tool = DateTimeTool()
        result = run_async(tool.execute())

        assert result.success is True
        assert "datetime" in result.data
        assert "year" in result.data
        assert "month" in result.data
        assert "day" in result.data

    def test_text_processor_tool(self):
        """测试文本处理 Tool。"""
        from app.agent.tools.builtin.common import TextProcessorTool

        tool = TextProcessorTool()

        # 统计字符
        result = run_async(tool.execute(text="hello world", operation="count_chars"))
        assert result.success is True
        assert result.data["char_count"] == 11

        # 统计单词
        result = run_async(tool.execute(text="hello world", operation="count_words"))
        assert result.success is True
        assert result.data["word_count"] == 2

        # 转大写
        result = run_async(tool.execute(text="hello", operation="to_upper"))
        assert result.success is True
        assert result.data["text"] == "HELLO"

        # 反转
        result = run_async(tool.execute(text="hello", operation="reverse"))
        assert result.success is True
        assert result.data["text"] == "olleh"


class TestSkillBase:
    """测试 Skill 基类。"""

    def test_inline_skill_creation(self):
        """测试 InlineSkill 创建。"""
        from app.agent.skills.base import InlineSkill

        skill = InlineSkill(
            name="test_skill",
            description="A test skill",
            prompt="This is the skill prompt.",
            keywords=["test", "demo"],
        )

        assert skill.name == "test_skill"
        assert skill.description == "A test skill"
        assert skill.get_prompt() == "This is the skill prompt."
        assert "test" in skill.meta.keywords

    def test_skill_to_dict(self):
        """测试转换为字典。"""
        from app.agent.skills.base import InlineSkill

        skill = InlineSkill(
            name="my_skill",
            description="My skill",
            prompt="Prompt content",
        )

        data = skill.to_dict()
        assert data["name"] == "my_skill"
        assert data["description"] == "My skill"


class TestRegistry:
    """测试 Registry 注册中心。"""

    def setup_method(self):
        """每个测试前清空注册。"""
        from app.agent.registry import AgentRegistry

        AgentRegistry.clear_all()

    def test_register_and_get_tool(self):
        """测试注册和获取 Tool。"""
        from app.agent.registry import AgentRegistry
        from app.agent.tools.base import BaseTool
        from app.agent.types import ToolResult

        class TestTool(BaseTool):
            name = "test_registry_tool"
            description = "Test tool"

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult(success=True, data={})

        tool = TestTool()
        AgentRegistry.register_tool(tool)

        assert AgentRegistry.has_tool("test_registry_tool")
        retrieved = AgentRegistry.get_tool("test_registry_tool")
        assert retrieved is tool
        assert "test_registry_tool" in AgentRegistry.list_tools()

    def test_register_and_get_skill(self):
        """测试注册和获取 Skill。"""
        from app.agent.registry import AgentRegistry
        from app.agent.skills.base import InlineSkill

        skill = InlineSkill(
            name="test_registry_skill",
            description="Test skill",
            prompt="Test prompt",
        )
        AgentRegistry.register_skill(skill)

        assert AgentRegistry.has_skill("test_registry_skill")
        retrieved = AgentRegistry.get_skill("test_registry_skill")
        assert retrieved is skill
        assert "test_registry_skill" in AgentRegistry.list_skills()

    def test_register_and_get_agent(self):
        """测试注册和获取 Agent。"""
        from app.agent.registry import AgentRegistry
        from app.agent.base import BaseAgent
        from app.agent.types import AgentConfig

        class TestAgent(BaseAgent):
            pass

        config = AgentConfig(
            name="test_registry_agent",
            description="Test agent",
            system_prompt="Test prompt",
        )

        AgentRegistry.register_agent(TestAgent, config)

        assert AgentRegistry.has_agent("test_registry_agent")
        agent = AgentRegistry.get_agent("test_registry_agent")
        assert isinstance(agent, TestAgent)
        assert agent.name == "test_registry_agent"

    def test_get_tool_schemas(self):
        """测试获取 Tool schemas。"""
        from app.agent.registry import AgentRegistry
        from app.agent.tools.base import BaseTool
        from app.agent.types import ToolResult

        class Tool1(BaseTool):
            name = "tool1"
            description = "Tool 1"

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult(success=True, data={})

        class Tool2(BaseTool):
            name = "tool2"
            description = "Tool 2"

            async def execute(self, **kwargs) -> ToolResult:
                return ToolResult(success=True, data={})

        AgentRegistry.register_tool(Tool1())
        AgentRegistry.register_tool(Tool2())

        # 获取所有
        schemas = AgentRegistry.get_tool_schemas()
        assert len(schemas) == 2

        # 获取指定
        schemas = AgentRegistry.get_tool_schemas(["tool1"])
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "tool1"

    def test_get_stats(self):
        """测试获取统计信息。"""
        from app.agent.registry import AgentRegistry

        stats = AgentRegistry.get_stats()
        assert "agents" in stats
        assert "tools" in stats
        assert "skills" in stats


class TestToolExecutor:
    """测试 Tool 执行器。"""

    def test_executor_execute(self):
        """测试执行器执行 Tool。"""
        from app.agent.tools.base import BaseTool, ToolExecutor
        from app.agent.types import ToolResult

        class EchoTool(BaseTool):
            name = "echo"
            description = "Echo tool"

            async def execute(self, message: str = "", **kwargs) -> ToolResult:
                return ToolResult(success=True, data={"echo": message})

        executor = ToolExecutor({"echo": EchoTool()})

        result = run_async(executor.execute("echo", {"message": "hello"}))
        assert result.success is True
        assert result.data["echo"] == "hello"

    def test_executor_tool_not_found(self):
        """测试执行不存在的 Tool。"""
        from app.agent.tools.base import ToolExecutor

        executor = ToolExecutor({})
        result = run_async(executor.execute("nonexistent", {}))

        assert result.success is False
        assert "not found" in result.error # type: ignore


class TestContextBuilder:
    """测试上下文构建器。"""

    def test_build_messages(self):
        """测试构建消息列表。"""
        from app.agent.context import AgentContextBuilder
        from app.agent.types import AgentContext

        builder = AgentContextBuilder()

        context = AgentContext(
            system_prompt="You are a helpful assistant.",
            user_profile="Software developer",
            user_instruction="Be concise",
            history_summary="Previous discussion about Python.",
            recent_messages=[
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
            ],
            current_message="How are you?",
            available_skills=[{"name": "coding", "description": "Coding help"}],
        )

        messages = builder.build_messages(context)

        # 应该有: system, history_summary, 2 recent, current
        assert len(messages) >= 4

        # 检查 system 消息包含用户信息
        system_content = messages[0]["content"]
        assert "Software developer" in system_content
        assert "Be concise" in system_content

        # 检查 history summary
        history_msg = [m for m in messages if "历史对话摘要" in m.get("content", "")]
        assert len(history_msg) == 1

        # 检查当前消息
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "How are you?"


class TestAgentSetup:
    """测试模块初始化。"""

    def setup_method(self):
        """清空注册。"""
        from app.agent.registry import AgentRegistry

        AgentRegistry.clear_all()

    def test_setup_registers_default_agent(self):
        """测试初始化注册默认 Agent。"""
        from app.agent import setup_agent_module
        from app.agent.registry import AgentRegistry

        setup_agent_module()

        assert AgentRegistry.has_agent("default")
        agent = AgentRegistry.get_agent("default")
        assert agent.name == "default"

    def test_setup_registers_builtin_tools(self):
        """测试初始化注册内置 Tools。"""
        from app.agent import setup_agent_module
        from app.agent.registry import AgentRegistry

        setup_agent_module()

        assert AgentRegistry.has_tool("calculator")
        assert AgentRegistry.has_tool("datetime")
        assert AgentRegistry.has_tool("text_processor")

    def test_setup_registers_builtin_skills(self):
        """测试初始化注册内置 Skills。"""
        from app.agent import setup_agent_module
        from app.agent.registry import AgentRegistry

        setup_agent_module()

        assert AgentRegistry.has_skill("writing_assistant")
        assert AgentRegistry.has_skill("code_review")
        assert AgentRegistry.has_skill("problem_solving")


class TestAgentBase:
    """测试 BaseAgent 类。"""

    def test_agent_initialization(self):
        """测试 Agent 初始化。"""
        from app.agent.base import DefaultAgent
        from app.agent.types import AgentConfig

        config = AgentConfig(
            name="test_base",
            description="Test agent",
            system_prompt="You are a test agent.",
            tools=["calculator"],
            skills=["code_review"],
            max_iterations=5,
        )

        agent = DefaultAgent(config)

        assert agent.name == "test_base"
        assert agent.max_iterations == 5
        assert "calculator" in agent.tools
        assert "code_review" in agent.skills


class TestDatabaseModels:
    """测试数据库模型。"""

    def test_agent_session_model_to_dict(self):
        """测试 AgentSessionModel.to_dict()。"""
        from app.agent.database.models import AgentSessionModel
        from datetime import datetime
        import uuid

        session = AgentSessionModel()
        session.id = uuid.uuid4()
        session.user_id = "test_user"
        session.agent_name = "default"
        session.created_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.compressed_summary = None
        session.compressed_count = 0
        session.messages = []

        data = session.to_dict()

        assert "id" in data
        assert data["user_id"] == "test_user"
        assert data["agent_name"] == "default"
        assert data["message_count"] == 0

    def test_agent_message_model_to_dict(self):
        """测试 AgentMessageModel.to_dict()。"""
        from app.agent.database.models import AgentMessageModel
        from datetime import datetime
        import uuid

        message = AgentMessageModel()
        message.id = uuid.uuid4()
        message.session_id = uuid.uuid4()
        message.role = "user"
        message.content = "Hello"
        message.created_at = datetime.utcnow()
        message.trace = None
        message.tool_calls = None

        data = message.to_dict()

        assert "id" in data
        assert data["role"] == "user"
        assert data["content"] == "Hello"


class TestSkillPromptLoading:
    """测试 Skill prompt 加载。"""

    def test_inline_skill_prompt_already_loaded(self):
        """测试内联 Skill 已加载状态。"""
        from app.agent.skills.base import InlineSkill

        skill = InlineSkill(
            name="test",
            description="Test",
            prompt="Test prompt content",
        )

        # 内联 Skill 应该已经加载
        assert skill._loaded is True
        assert skill.get_prompt() == "Test prompt content"

    def test_skill_meta_keywords(self):
        """测试 Skill 关键词。"""
        from app.agent.skills.base import InlineSkill

        skill = InlineSkill(
            name="test",
            description="Test",
            prompt="Content",
            keywords=["python", "coding"],
        )

        assert "python" in skill.meta.keywords
        assert "coding" in skill.meta.keywords


class TestAgentChunkTypes:
    """测试 AgentChunk 类型处理。"""

    def test_all_chunk_types_exist(self):
        """测试所有 chunk 类型存在。"""
        from app.agent.types import AgentChunkType

        assert hasattr(AgentChunkType, "CONTENT")
        assert hasattr(AgentChunkType, "TRACE")
        assert hasattr(AgentChunkType, "TOOL_CALL")
        assert hasattr(AgentChunkType, "TOOL_RESULT")
        assert hasattr(AgentChunkType, "SKILL_LOAD")
        assert hasattr(AgentChunkType, "ERROR")
        assert hasattr(AgentChunkType, "DONE")

    def test_trace_step_dataclass(self):
        """测试 TraceStep 数据类。"""
        from app.agent.types import TraceStep
        from dataclasses import asdict

        step = TraceStep(
            iteration=0,
            action="tool_call",
            tool_calls=[{"name": "calculator", "arguments": {}}],
        )

        data = asdict(step)

        assert data["iteration"] == 0
        assert data["action"] == "tool_call"
        assert len(data["tool_calls"]) == 1


class TestMCPTool:
    """测试 MCP Tool。"""

    def test_mcp_tool_creation(self):
        """测试 MCPTool 创建。"""
        from app.agent.tools.base import MCPTool

        tool = MCPTool(
            name="mcp_test",
            description="Test MCP tool",
            mcp_endpoint="http://localhost:8080",
            mcp_tool_name="remote_tool",
        )

        assert tool.name == "mcp_test"
        assert tool.mcp_endpoint == "http://localhost:8080"

    def test_mcp_tool_execute_not_implemented(self):
        """测试 MCP Tool 执行（未实现）。"""
        from app.agent.tools.base import MCPTool

        tool = MCPTool(
            name="mcp_test",
            description="Test",
            mcp_endpoint="http://localhost:8080",
            mcp_tool_name="remote",
        )

        result = run_async(tool.execute(param="value"))

        assert result.success is False
        assert "not implemented" in result.error.lower() # type: ignore


class TestAgentAPIEndpoints:
    """测试 Agent API 端点。"""

    def test_agent_chat_request_validation(self):
        """测试 AgentChatRequest 验证。"""
        from app.api.v1.endpoints.agent import AgentChatRequest

        # 有效请求
        req = AgentChatRequest(message="Hello", agent_name="default")
        assert req.message == "Hello"
        assert req.agent_name == "default"
        assert req.stream is True

        # 空消息应失败
        with pytest.raises(ValueError):
            AgentChatRequest(message="")

        with pytest.raises(ValueError):
            AgentChatRequest(message="   ")

    def test_agent_session_response_model(self):
        """测试 AgentSessionResponse 模型。"""
        from app.api.v1.endpoints.agent import AgentSessionResponse

        resp = AgentSessionResponse(
            id="test-id",
            user_id="user-1",
            agent_name="default",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            message_count=5,
        )

        assert resp.id == "test-id"
        assert resp.message_count == 5

    def test_agent_message_response_model(self):
        """测试 AgentMessageResponse 模型。"""
        from app.api.v1.endpoints.agent import AgentMessageResponse

        resp = AgentMessageResponse(
            id="msg-id",
            session_id="session-id",
            role="user",
            content="Hello",
            created_at="2024-01-01T00:00:00",
            trace=None,
            tool_calls=None,
        )

        assert resp.role == "user"
        assert resp.trace is None

    def test_agent_router_exists(self):
        """测试 Agent router 存在。"""
        from app.api.v1.endpoints.agent import router

        # 检查路由存在
        paths = [r.path for r in router.routes] # type: ignore
        assert "/agent/chat" in paths
        assert "/agent/sessions" in paths

    def test_agent_history_response_model(self):
        """测试 AgentHistoryResponse 模型。"""
        from app.api.v1.endpoints.agent import (
            AgentHistoryResponse,
            AgentMessageResponse,
        )

        msg = AgentMessageResponse(
            id="msg-1",
            session_id="session-1",
            role="assistant",
            content="Hi there!",
            created_at="2024-01-01T00:00:00",
        )

        resp = AgentHistoryResponse(
            session_id="session-1",
            messages=[msg],
        )

        assert resp.session_id == "session-1"
        assert len(resp.messages) == 1
        assert resp.messages[0].content == "Hi there!"


class TestAgentMainIntegration:
    """测试 Agent 与 main.py 的集成。"""

    def test_agent_module_setup_runs(self):
        """测试 setup_agent_module 正常运行。"""
        from app.agent import setup_agent_module
        from app.agent.registry import AgentRegistry

        # 清空注册表
        AgentRegistry._agents.clear()
        AgentRegistry._tools.clear()
        AgentRegistry._skills.clear()

        # 运行 setup
        setup_agent_module()

        # 验证默认 Agent 已注册
        assert "default" in AgentRegistry._agents
        assert "calculator" in AgentRegistry._tools
        assert "writing_assistant" in AgentRegistry._skills

    def test_agent_router_registered_in_app(self):
        """测试 Agent router 已注册到 app。"""
        from app.main import app

        # 查找 agent 路由
        agent_routes = [
            r for r in app.routes if hasattr(r, "path") and "agent" in r.path # type: ignore
        ]
        assert len(agent_routes) >= 4  # chat, session, messages, sessions

    def test_agent_models_use_same_base(self):
        """测试 Agent 模型使用相同的 Base。"""
        from app.database.models import Base
        from app.agent.database.models import AgentSessionModel, AgentMessageModel

        # 验证 Agent 模型使用相同的 Base
        assert AgentSessionModel.__tablename__ == "agent_sessions"
        assert AgentMessageModel.__tablename__ == "agent_messages"

        # 验证表名在 Base 的 metadata 中
        assert "agent_sessions" in Base.metadata.tables
        assert "agent_messages" in Base.metadata.tables


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
