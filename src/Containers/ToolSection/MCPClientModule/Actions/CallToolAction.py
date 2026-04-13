from __future__ import annotations

import json
from typing import Any

import anyio
from pydantic import BaseModel, Field
from returns.result import Failure, Result, Success

from src.Containers.ToolSection.MCPClientModule.Errors import MCPError, ToolExecutionError
from src.Ship.Parents.Action import Action


class CallToolRequest(BaseModel):
    model_config = {"frozen": True}

    server_command: str
    server_args: list[str] = Field(default_factory=list)
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class CallToolAction(Action[CallToolRequest, dict[str, Any], MCPError]):
    """Вызов MCP-инструмента через stdio JSON-RPC."""

    async def run(self, data: CallToolRequest) -> Result[dict[str, Any], MCPError]:
        try:
            cmd = [data.server_command, *data.server_args]

            request_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": data.tool_name,
                    "arguments": data.arguments,
                },
            }

            input_bytes = json.dumps(request_payload).encode() + b"\n"

            result = await anyio.run_process(
                cmd,
                input=input_bytes,
                check=False,
            )

            if result.returncode != 0:
                return Failure(ToolExecutionError(
                    message=f"MCP tool failed: {result.stderr.decode()[:500]}",
                    tool_name=data.tool_name,
                ))

            output = json.loads(result.stdout.decode())
            return Success(output.get("result", output))

        except Exception as e:
            return Failure(ToolExecutionError(
                message=f"MCP call error: {e}",
                tool_name=data.tool_name,
            ))
