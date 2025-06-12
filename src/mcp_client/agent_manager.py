import asyncio
import logging
import os
import json
from typing import List, Optional, Any, Tuple
from anthropic import Anthropic, types as claude_types
from google import genai
from google.genai import types as genai_types
from pathlib import Path

from mcp_client.server_manager import Server
from mcp_client.agent_manager_interface import (
    AgentManger,
    Message,
    ToolSchema,
    ToolCall,
)


def load_system_prompt(file_path: Optional[str] = None) -> Optional[str]:
    """Load system prompt from a file.

    Args:
        file_path: Path to the system prompt file

    Returns:
        The system prompt as a string, or None if file_path is None or file doesn't exist
    """
    if not file_path:
        return None

    path = Path(file_path)
    if not path.exists():
        return None

    return path.read_text(encoding="utf-8")


class ClaudeAgent(AgentManger):
    """Anthropic Claude adapter."""

    def __init__(
        self,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 1024,
        logger: Optional[logging.Logger] = None,
        system_prompt: Optional[str] = None,
    ):
        super().__init__(logger, system_prompt)
        if Anthropic is None:
            raise RuntimeError("anthropic package not installed")
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    async def _apply_system_prompt(
        self, servers: List[Server], messages: List[Message]
    ) -> None:
        """Apply the system prompt for Claude."""
        tools = [t.format_for_llm() for srv in servers for t in await srv.list_tools()]
        tool_descriptions = "\n".join(tools)
        if self.system_prompt:
            messages.append(
                {
                    "role": "user",
                    "content": f"<system>\n{self.system_prompt}\n# Available Tools:\n{tool_descriptions}</system>",
                }
            )

    async def _prepare_tools(self, servers: List[Server]) -> List[ToolSchema]:
        tool_schemas: List[ToolSchema] = []
        for srv in servers:
            for t in await srv.list_tools():
                tool_schemas.append(
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema,  # Claude expects JSON schema
                    }
                )
        return tool_schemas

    async def _generate_response(
        self,
        messages: List[Message],
        tools: List[ToolSchema],
    ) -> Tuple[claude_types.Message, bool, List[claude_types.ContentBlock]]:
        params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
            "tools": tools,
        }

        # if self.system_prompt:
        #     params["system"] = self.system_prompt

        resp = await asyncio.to_thread(self.client.messages.create, **params)
        parts: List[claude_types.ContentBlock] = resp.content
        has_call = any(p.type == "tool_use" for p in parts)
        return resp, has_call, parts

    def _extract_tool_calls(self, parts: List[Any]) -> List[ToolCall]:
        calls: List[ToolCall] = []
        for p in parts:
            if getattr(p, "type", None) == "tool_use":
                calls.append(
                    {
                        "id": p.id,
                        "name": p.name,
                        "args": p.input,
                    }
                )
        return calls

    def _integrate_tool_result(
        self,
        messages: List[Message],
        call: ToolCall,
        result: Any,
    ) -> None:
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": call["id"],
                        "content": (
                            result.content if hasattr(result, "content") else result
                        ),
                    }
                ],
            }
        )


class GeminiAgent(AgentManger):
    """Google Gemini adapter."""

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        max_tokens: int = 1024,
        logger: Optional[logging.Logger] = None,
        system_prompt: Optional[str] = None,
    ):
        super().__init__(logger, system_prompt)
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    async def _prepare_tools(self, servers: List[Server]) -> List[ToolSchema]:
        schemas: List[ToolSchema] = []
        for srv in servers:
            for t in await srv.list_tools():
                schemas.append(
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    }
                )
        return schemas

    async def _apply_system_prompt(
        self, servers: List[Server], messages: List[Message]
    ) -> None:
        """Apply the system prompt for Gemini.

        Gemini handles system prompts as a 'user' role message at the beginning,
        with a special prefix to indicate it's a system instruction.
        """
        tools = [t.format_for_llm() for srv in servers for t in await srv.list_tools()]
        tool_descriptions = "\n".join(tools)
        if self.system_prompt:
            # For Gemini, we add the system prompt as a user message with a special prefix
            messages.append(
                {
                    "role": "user",
                    "content": f"<system>\n{self.system_prompt}\n# Available Tools:\n{tool_descriptions}</system>",
                }
            )

    async def _generate_response(
        self,
        messages: List[Message],
        tools: List[ToolSchema],
    ) -> Tuple[genai_types.GenerateContentResponse, bool, List[genai_types.Part]]:
        gemini_contents = []
        for msg in messages:
            role = msg["role"]
            content_parts = []
            if isinstance(msg["content"], str):
                content_parts.append(genai_types.Part(text=msg["content"]))
            elif isinstance(msg["content"], list):
                for item in msg["content"]:
                    if "function_response" in item:
                        content_parts.append(
                            genai_types.Part(
                                function_response=item["function_response"]
                            )
                        )
                    elif "function_call" in item:
                        content_parts.append(
                            genai_types.Part(function_call=item["function_call"])
                        )
                    elif "text" in item:
                        content_parts.append(genai_types.Part(text=item["text"]))
                    else:
                        content_parts.append(genai_types.Part(text=str(item)))
            else:
                content_parts.append(genai_types.Part(text=str(msg["content"])))

            gemini_role = "model" if role == "assistant" else role
            gemini_contents.append(
                genai_types.Content(role=gemini_role, parts=content_parts)
            )

        tool_defs = genai_types.Tool(function_declarations=tools)
        resp = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=gemini_contents,  # Use the converted messages
            config=genai_types.GenerateContentConfig(tools=[tool_defs]),
        )
        parts = resp.candidates[0].content.parts
        has_call = any(hasattr(p, "function_call") and p.function_call for p in parts)
        return resp, has_call, parts

    def _extract_tool_calls(self, parts: List[Any]) -> List[ToolCall]:
        calls: List[ToolCall] = []
        for p in parts:
            if getattr(p, "function_call", None):
                fc = p.function_call
                calls.append(
                    {
                        "id": fc.id,
                        "name": fc.name,
                        "args": fc.args,
                    }
                )
        return calls

    def _integrate_tool_result(
        self,
        messages: List[Message],
        call: ToolCall,
        result: Any,
    ) -> None:
        response_content = result.content if hasattr(result, "content") else result
        if isinstance(response_content, str):
            try:
                response_content = json.loads(response_content)
            except json.JSONDecodeError:
                response_content = {"text_response": response_content}
        elif not isinstance(response_content, dict):
            response_content = {"value": str(response_content)}

        messages.append(
            {
                "role": "user",
                "content": [
                    genai_types.Part(
                        function_response={
                            "name": call["name"],
                            "response": response_content,
                        }
                    )
                ],
            }
        )


def create_agent(
    provider: str, system_prompt_path: Optional[str] = None, **kwargs
) -> AgentManger:
    """Create an agent for the specified provider.

    Args:
        provider: The provider to use (claude, anthropic, gemini)
        system_prompt_path: Path to a file containing the system prompt
        **kwargs: Additional arguments to pass to the agent constructor

    Returns:
        An instance of AgentManger
    """
    # Load system prompt if a path is provided
    system_prompt = load_system_prompt(system_prompt_path)
    if system_prompt:
        kwargs["system_prompt"] = system_prompt

    provider = provider.lower()
    if provider == "claude" or provider == "anthropic":
        return ClaudeAgent(**kwargs)
    if provider == "gemini":
        return GeminiAgent(**kwargs)
    raise ValueError(f"Unknown provider: {provider}")
