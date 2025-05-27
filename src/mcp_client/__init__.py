"""Slack MCP Client package.

This package provides a client for the Model Context Protocol (MCP) with support
for connecting to various MCP servers and AI providers (Anthropic, OpenAI, Gemini).
"""

from .client import MCPClient
from .server_manager import ServerConnectionManager
from .agent_manager import (
    AgentManger,
    ClaudeAgent,
    GeminiAgent,
)

__all__ = [
    "MCPClient",
    "ServerConnectionManager",
    "AgentManager",
    "AnthropicAgentManager",
    "OpenAIAgentManager",
    "GeminiAgentManager",
]
