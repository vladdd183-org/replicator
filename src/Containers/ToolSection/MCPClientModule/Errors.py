from __future__ import annotations

from src.Ship.Core.Errors import BaseError


class MCPError(BaseError):
    code: str = "MCP_ERROR"


class MCPConnectionError(MCPError):
    code: str = "MCP_CONNECTION_ERROR"
    server: str = ""


class ToolNotFoundError(MCPError):
    code: str = "TOOL_NOT_FOUND"
    http_status: int = 404
    tool_name: str = ""


class ToolExecutionError(MCPError):
    code: str = "TOOL_EXECUTION_ERROR"
    tool_name: str = ""
