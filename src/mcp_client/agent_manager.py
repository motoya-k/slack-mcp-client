"""Agent manager for MCP clients.

This module provides the AgentManager class which abstracts different AI providers
(Anthropic, OpenAI, Gemini) for use with MCP tools.
"""

import abc
import logging
import os
from typing import Dict, List, Optional, Any, Union

from anthropic import Anthropic
from mcp import ClientSession
import openai
from google import genai
from google.genai import types as genai_types


class AgentManager(abc.ABC):
    """Base class for AI agent managers."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the agent manager.

        Args:
            logger: Optional logger
        """
        self.logger = logger or logging.getLogger(__name__)

    @abc.abstractmethod
    async def process_query_without_tools(self, query: str) -> str:
        """Process a query directly without using MCP tools.

        Args:
            query: The user query to process

        Returns:
            The processed response
        """
        pass

    @abc.abstractmethod
    async def process_query_with_server(
        self,
        query: str,
        session: Any,
        server_name: str,
    ) -> str:
        """Process a query using a specific MCP server.

        This method handles the complete conversation flow including executing tool calls
        and processing the results until no more tool calls are needed.

        Args:
            query: The user query to process
            session: The server session to use for tool calls
            server_name: The name of the server being used

        Returns:
            The final processed response as a string
        """
        pass

    @staticmethod
    def create(provider: str, **kwargs) -> "AgentManager":
        """Factory method to create an agent manager for a specific provider.

        Args:
            provider: The provider name ('anthropic', 'openai', or 'gemini')
            **kwargs: Additional arguments to pass to the provider's constructor

        Returns:
            An instance of the appropriate AgentManager subclass

        Raises:
            ValueError: If the provider is not supported or the required package is not installed
        """
        provider = provider.lower()

        if provider == "anthropic":
            return AnthropicAgentManager(**kwargs)
        elif provider == "openai":
            return OpenAIAgentManager(**kwargs)
        elif provider == "gemini":
            return GeminiAgentManager(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


class AnthropicAgentManager(AgentManager):
    """Agent manager for Anthropic Claude."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Anthropic agent manager.

        Args:
            model: The Claude model to use
            max_tokens: Maximum tokens to generate
            api_key: Optional API key (if not provided, uses environment variable)
            logger: Optional logger
        """
        super().__init__(logger)
        self.model = model
        self.max_tokens = max_tokens
        # Use ANTHROPIC_API_KEY from environment if api_key is not provided
        if api_key is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.anthropic = Anthropic(api_key=api_key) if api_key else Anthropic()
        self.logger.info(f"Initialized Anthropic agent manager with model: {model}")

    async def process_query_without_tools(self, query: str = "") -> str:
        """Process a query directly with Claude without using MCP tools.

        Args:
            query: The user query to process

        Returns:
            The processed response
        """
        self.logger.info(
            f"🔍 Processing query directly with Claude (no tools): {query}"
        )
        messages = [{"role": "user", "content": query}]

        # Call Claude API without tools
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
        )

        # Extract text response
        return response.content[0].text

    async def _process_query_with_tools(
        self,
        messages: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]],
    ) -> tuple:
        """Internal method to process a query using Claude with available MCP tools.

        Args:
            messages: The conversation history
            available_tools: List of available tools

        Returns:
            Tuple of (response, has_tool_call, assistant_message_content)
        """
        # Call Claude API with tools
        response = self.anthropic.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            tools=available_tools,
        )

        has_tool_call = False
        assistant_message_content = []

        for content in response.content:
            if content.type == "tool_use":
                has_tool_call = True
            assistant_message_content.append(content)

        return response, has_tool_call, assistant_message_content

    async def process_query_with_server(
        self,
        query: str,
        session: ClientSession,
        server_name: str,
    ) -> str:
        """Process a query using Claude with available MCP tools from a specific server.

        This method handles the complete conversation flow including executing tool calls
        and processing the results until no more tool calls are needed.

        Args:
            query: The user query to process
            session: The server session to use for tool calls
            server_name: The name of the server being used

        Returns:
            The final processed response as a string
        """
        # Get available tools from the server
        response = await session.list_tools()
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

        # Prepare initial messages
        messages = [{"role": "user", "content": query}]

        # Initial AI API call
        response, has_tool_call, assistant_message_content = (
            await self._process_query_with_tools(messages, available_tools)
        )

        final_text = []

        # Continue processing responses until no more tool calls are made
        while True:
            for content in assistant_message_content:
                if content.type == "text":
                    final_text.append(content.text)
                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input
                    tool_id = content.id

                    # Execute tool call on the specified server
                    result = await session.call_tool(tool_name, tool_args)
                    final_text.append(
                        f"[Calling tool {tool_name} with args {tool_args} on server '{server_name}']"
                    )

                    messages.append(
                        {"role": "assistant", "content": assistant_message_content}
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": result.content,
                                }
                            ],
                        }
                    )

                    # Get next response from AI
                    response, has_tool_call, assistant_message_content = (
                        await self._process_query_with_tools(messages, available_tools)
                    )

                    # Break the inner loop to process the new response
                    break

            # If no tool calls were made in this response, we're done
            if not has_tool_call:
                break

        return "\n".join(final_text)


class OpenAIAgentManager(AgentManager):
    """Agent manager for OpenAI models."""

    def __init__(
        self,
        model: str = "gpt-4o",
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        raise NotImplementedError("OpenAI is not supported yet")


class GeminiAgentManager(AgentManager):
    """Agent manager for Google Gemini models."""

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Gemini agent manager.

        Args:
            model: The Gemini model to use
            max_tokens: Maximum tokens to generate
            api_key: Optional API key (if not provided, uses environment variable)
            logger: Optional logger
        """
        super().__init__(logger)
        self.model = model
        self.max_tokens = max_tokens

        # Use GEMINI_API_KEY from environment if api_key is not provided
        if api_key is None:
            api_key = os.environ.get("GEMINI_API_KEY")

        self.gemini = genai.Client(api_key=api_key)
        self.logger.info(f"Initialized Gemini agent manager with model: {model}")

    async def process_query_without_tools(self, query: str) -> str:
        """Process a query directly with Gemini without using MCP tools.

        Args:
            query: The user query to process

        Returns:
            The processed response
        """
        self.logger.info(
            f"🔍 Processing query directly with Gemini (no tools): {query}"
        )
        response = self.gemini.models.generate_content(
            model=self.model,
            contents=query,
        )
        return response.text

    async def _process_query_with_tools(
        self,
        messages: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]],
    ) -> tuple[genai_types.GenerationConfig, bool, List[genai_types.Part]]:
        """Internal method to process a query using Gemini with available MCP tools.

        Args:
            query: The user query to process
            messages: The conversation history
            available_tools: List of available tools

        Returns:
            Tuple of (response, has_tool_call, assistant_message_content)
        """
        tool_defs = genai_types.Tool(function_declarations=available_tools)
        response = self.gemini.models.generate_content(
            model=self.model,
            contents=messages,
            config=genai_types.GenerateContentConfig(
                tools=[tool_defs],
            ),
        )

        has_tool_call = False
        assistant_message_content = []

        self.logger.info(f"🍇 Gemini response: {response}")

        for candidate in response.candidates:
            if candidate.content.parts[0].function_call:
                has_tool_call = True
            if len(candidate.content.parts) > 0:
                assistant_message_content = candidate.content.parts

        return response, has_tool_call, assistant_message_content

    async def process_query_with_server(
        self,
        query: str,
        session: ClientSession,
        server_name: str,
    ) -> str:
        """Process a query using Gemini with available MCP tools from a specific server.

        This method handles the complete conversation flow including executing tool calls
        and processing the results until no more tool calls are needed.

        Args:
            query: The user query to process
            session: The server session to use for tool calls
            server_name: The name of the server being used

        Returns:
            The final processed response as a string
        """
        response = await session.list_tools()
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            }
            for tool in response.tools
        ]

        # Prepare initial messages
        messages = [query]

        # Initial AI API call
        response, has_tool_call, assistant_message_content = (
            await self._process_query_with_tools(messages, available_tools)
        )

        final_text = []
        while True:
            for content in assistant_message_content:
                self.logger.info(
                    f"🍇 Gemini content: {content.function_call} {bool(content.function_call)}"
                )
                if content.function_call:
                    tool_name = content.function_call.name
                    tool_args = content.function_call.args
                    tool_id = content.function_call.id

                    # Execute tool call on the specified server
                    result = await session.call_tool(tool_name, tool_args)
                    final_text.append(
                        f"[Calling tool {tool_name} with args {tool_args} on server '{server_name}']"
                    )

                    messages.append({"role": "assistant", "content": content.text})
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_id,
                                    "content": result.content,
                                }
                            ],
                        }
                    )

                    # Get next response from AI
                    response, has_tool_call, assistant_message_content = (
                        await self._process_query_with_tools(messages, available_tools)
                    )

                    # Break the inner loop to process the new response
                    break
            # If no tool calls were made in this response, we're done
            if not has_tool_call:
                break
        return "\n".join(final_text)
