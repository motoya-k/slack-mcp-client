import abc
import logging
from typing import Dict, List, Optional, Any, Tuple

from mcp_client.server_manager import Server

Message = Dict[str, Any]
ToolSchema = Dict[str, Any]
ToolCall = Dict[str, Any]


class AgentManger(abc.ABC):
    MAX_DEPTH: int = 5

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    async def _prepare_tools(self, servers: List[Server]) -> List[ToolSchema]:
        """Convert MCP server tool list into provider-specific tool schemas."""
        pass

    @abc.abstractmethod
    async def _generate_response(
        self,
        messages: List[Message],
        tools: List[ToolSchema],
    ) -> Tuple[Any, bool, List[Any]]:
        """Return (raw_response, has_tool_call, assistant_parts)."""
        pass

    @abc.abstractmethod
    def _extract_tool_calls(self, assistant_parts: List[Any]) -> List[ToolCall]:
        """Find tool call directives inside the assistant response."""
        pass

    @abc.abstractmethod
    def _integrate_tool_result(
        self,
        messages: List[Message],
        call: ToolCall,
        result: Any,
    ) -> None:
        """Append tool result to message context (in-place)."""
        pass

    async def process_query(self, query: str, servers: List[Server]) -> str:
        """Main entry point usable by application code."""
        tools = await self._prepare_tools(servers)
        messages: List[Message] = [{"role": "user", "content": query}]
        depth = 0

        while depth < self.MAX_DEPTH:
            raw_resp, has_call, parts = await self._generate_response(messages, tools)
            messages.append({"role": "assistant", "content": parts})

            if not has_call:
                break

            calls = self._extract_tool_calls(parts)
            if not calls:
                self.logger.warning("Provider indicated tool_call but none extracted.")
                break

            for call in calls:
                server = await self._find_server_for_tool(servers, call["name"])
                result = await server.call_tool(call["name"], call["args"])
                self._integrate_tool_result(messages, call, result)

            depth += 1

        return self._flatten_assistant_text(messages)

    async def _find_server_for_tool(
        self, servers: List[Server], tool_name: str
    ) -> Server:
        for s in servers:
            tools = await s.list_tools()
            if any(t.name == tool_name for t in tools):
                return s
        raise RuntimeError(f"No server exposes tool '{tool_name}'")

    def _flatten_assistant_text(self, messages: List[Message]) -> str:
        all_texts = []
        for m in messages:
            if m["role"] == "assistant":
                content = m["content"]
                if isinstance(content, list):
                    for part in content:
                        all_texts.append(self._part_to_text(part))
                else:
                    all_texts.append(self._part_to_text(content))
        return "\n".join(all_texts)

    @staticmethod
    def _part_to_text(part: Any) -> str:
        if isinstance(part, str):
            return part
        if hasattr(part, "text") and part.text is not None:
            return str(part.text)
        if hasattr(part, "function_call") and part.function_call:
            return ""
        if hasattr(part, "function_response") and part.function_response:
            return ""

        return ""
