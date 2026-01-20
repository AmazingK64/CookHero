"""
MCP server management service.
"""

import logging
import re
from typing import List

from sqlalchemy import select

from app.agent.database.models import AgentMCPServerModel
from app.agent.registry import AgentHub
from app.agent.tools.providers.mcp import MCPToolProvider
from app.database.session import get_session_context

logger = logging.getLogger(__name__)

NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{2,64}$")


class MCPService:
    """Service for managing user-defined MCP servers."""

    async def list_servers(self, user_id: str) -> List[AgentMCPServerModel]:
        async with get_session_context() as session:
            stmt = select(AgentMCPServerModel).where(
                AgentMCPServerModel.user_id == user_id
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_server(
        self,
        *,
        user_id: str,
        name: str,
        endpoint: str,
        enabled: bool = True,
        auth_header_name: str | None = None,
        auth_token: str | None = None,
    ) -> AgentMCPServerModel:
        self._validate_name(name)
        self._validate_endpoint(endpoint)
        self._validate_auth(auth_header_name, auth_token)

        async with get_session_context() as session:
            existing_stmt = select(AgentMCPServerModel).where(
                AgentMCPServerModel.user_id == user_id,
                AgentMCPServerModel.name == name,
            )
            existing = (await session.execute(existing_stmt)).scalar_one_or_none()
            if existing:
                raise ValueError("MCP 名称已存在")

            server = AgentMCPServerModel(
                user_id=user_id,
                name=name,
                endpoint=endpoint,
                auth_header_name=auth_header_name,
                auth_token=auth_token,
                enabled=enabled,
            )
            session.add(server)
            await session.flush()

        if enabled:
            await self.register_server(server)

        return server

    async def register_server(self, server: AgentMCPServerModel) -> bool:
        if not server.enabled:
            return False

        provider = self._get_provider()
        headers = self._build_headers(server)
        provider.register_server(server.name, server.endpoint, headers)
        loaded = await provider.load_server_tools(server.name)
        return len(loaded) > 0

    async def register_all_for_user(self, user_id: str) -> None:
        servers = await self.list_servers(user_id)
        for server in servers:
            if not server.enabled:
                continue
            try:
                await self.register_server(server)
            except Exception as exc:
                logger.warning(
                    "Failed to register MCP server %s for user %s: %s",
                    server.name,
                    user_id,
                    exc,
                )

    async def register_all(self) -> None:
        async with get_session_context() as session:
            stmt = select(AgentMCPServerModel).where(
                AgentMCPServerModel.enabled.is_(True)
            )
            result = await session.execute(stmt)
            servers = list(result.scalars().all())

        for server in servers:
            try:
                await self.register_server(server)
            except Exception as exc:
                logger.warning("Failed to register MCP server %s: %s", server.name, exc)

    def _validate_name(self, name: str) -> None:
        if not NAME_PATTERN.match(name):
            raise ValueError("MCP 名称需为 2-64 位，支持字母、数字、_、-")

    def _validate_endpoint(self, endpoint: str) -> None:
        if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
            raise ValueError("Endpoint 需要以 http:// 或 https:// 开头")
        if len(endpoint) > 512:
            raise ValueError("Endpoint 过长")

    def _validate_auth(
        self, auth_header_name: str | None, auth_token: str | None
    ) -> None:
        if not auth_header_name and not auth_token:
            return
        if not auth_header_name or not auth_token:
            raise ValueError("Header 名称和 Token 需要同时填写")
        if len(auth_header_name) > 128:
            raise ValueError("Header 名称过长")
        if "\n" in auth_header_name or "\r" in auth_header_name:
            raise ValueError("Header 名称不合法")

    def _build_headers(self, server: AgentMCPServerModel) -> dict[str, str] | None:
        if server.auth_header_name and server.auth_token:
            return {server.auth_header_name: server.auth_token}
        return None

    def _get_provider(self) -> MCPToolProvider:
        return AgentHub.get_provider("mcp")  # type: ignore


mcp_service = MCPService()
