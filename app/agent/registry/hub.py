"""AgentHub: single entrypoint for Agent + Tool + Provider (MCP, custom).

Design goals:
- One import path for all registration/lookup APIs.
- Providers are first-class: builtin, mcp, and future user-defined.
- No backwards compatibility layer.

Public API intentionally mirrors what the rest of the codebase needs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Protocol, Type, runtime_checkable

from app.agent.types import AgentConfig
from app.agent.tools.base import BaseTool, ToolExecutor

logger = logging.getLogger(__name__)


@runtime_checkable
class ToolProvider(Protocol):
    """Tool source provider.

    Examples:
    - builtin provider: registers python-implemented tools
    - mcp provider: loads & registers tools from MCP servers
    - custom provider: user-defined tools from DB/config
    """

    name: str

    def list_tool_infos(self) -> list[dict]:
        raise NotImplementedError

    def get_tool(self, name: str) -> Optional[BaseTool]:
        raise NotImplementedError

    def get_tool_schema(self, name: str) -> Optional[dict]:
        raise NotImplementedError

    def get_tool_schemas(self, names: Optional[list[str]] = None) -> list[dict]:
        raise NotImplementedError

    def list_tool_names(self) -> list[str]:
        raise NotImplementedError

    def register_tool(self, tool: BaseTool) -> None:
        raise NotImplementedError

    def unregister_tool(self, name: str) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class _AgentEntry:
    cls: Type["BaseAgent"]
    config: AgentConfig


class MCPServerProvider(ToolProvider, Protocol):
    def register_server(self, name: str, endpoint: str) -> None:
        raise NotImplementedError

    def list_servers(self) -> list[str]:
        raise NotImplementedError

    async def load_server_tools(self, name: str):
        raise NotImplementedError


class AgentHub:
    """Unified module hub."""

    _agents: dict[str, _AgentEntry] = {}
    _providers: dict[str, ToolProvider] = {}

    # ==================== Agent ====================

    @classmethod
    def register_agent(cls, agent_cls: Type["BaseAgent"], config: AgentConfig) -> None:
        cls._agents[config.name] = _AgentEntry(cls=agent_cls, config=config)
        logger.info(f"Registered agent: {config.name}")

    @classmethod
    def get_agent(cls, name: str) -> "BaseAgent":
        entry = cls._agents.get(name)
        if not entry:
            raise KeyError(f"Agent '{name}' not found")
        return entry.cls(entry.config)

    @classmethod
    def get_agent_config(cls, name: str) -> AgentConfig:
        entry = cls._agents.get(name)
        if not entry:
            raise KeyError(f"Agent '{name}' not found")
        return entry.config

    @classmethod
    def list_agents(cls) -> list[str]:
        return list(cls._agents.keys())

    @classmethod
    def clear_agents(cls) -> None:
        cls._agents.clear()

    # ==================== Providers ====================

    @classmethod
    def register_provider(cls, provider: ToolProvider) -> None:
        if provider.name in cls._providers:
            raise ValueError(f"Provider already registered: {provider.name}")
        cls._providers[provider.name] = provider
        logger.info(f"Registered tool provider: {provider.name}")

    @classmethod
    def get_provider(cls, name: str) -> ToolProvider:
        provider = cls._providers.get(name)
        if not provider:
            raise KeyError(f"Provider '{name}' not found")
        return provider

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def clear_providers(cls) -> None:
        cls._providers.clear()

    # ==================== Tool surface (aggregated) ====================

    @classmethod
    def register_tool(cls, tool: BaseTool, provider: str = "builtin") -> None:
        cls.get_provider(provider).register_tool(tool)

    @classmethod
    def unregister_tool(cls, name: str) -> bool:
        for p in cls._providers.values():
            if p.get_tool(name):
                return p.unregister_tool(name)
        return False

    @classmethod
    def get_tool(cls, name: str) -> Optional[BaseTool]:
        for p in cls._providers.values():
            tool = p.get_tool(name)
            if tool:
                return tool
        return None

    @classmethod
    def get_tool_schemas(cls, names: Optional[list[str]] = None) -> list[dict]:
        if names is None:
            schemas: list[dict] = []
            for p in cls._providers.values():
                schemas.extend(p.get_tool_schemas(None))
            return schemas

        # keep order per names
        result: list[dict] = []
        for n in names:
            for p in cls._providers.values():
                schema = p.get_tool_schema(n)
                if schema:
                    result.append(schema)
                    break
        return result

    @classmethod
    def list_tools(cls) -> list[str]:
        names: list[str] = []
        for p in cls._providers.values():
            names.extend(p.list_tool_names())
        return names

    @classmethod
    def list_tools_info(cls) -> list[dict]:
        infos: list[dict] = []
        for p in cls._providers.values():
            infos.extend(p.list_tool_infos())
        return infos

    @classmethod
    def create_tool_executor(
        cls, tool_names: Optional[list[str]] = None
    ) -> ToolExecutor:
        if tool_names is None:
            tools: dict[str, BaseTool] = {}
            for p in cls._providers.values():
                for name in p.list_tool_names():
                    tool = p.get_tool(name)
                    if tool:
                        tools[name] = tool
            return ToolExecutor(tools)

        tools = {}
        for n in tool_names:
            tool = cls.get_tool(n)
            if tool:
                tools[n] = tool
        return ToolExecutor(tools)

    # ==================== Cleanup ====================

    @classmethod
    def clear_all(cls) -> None:
        cls.clear_agents()
        cls.clear_providers()


# Imported only for type checking; avoid runtime circular import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agent.base import BaseAgent  # pragma: no cover
