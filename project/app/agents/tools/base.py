"""Base tool registry for pluggable tools and MCP integrations.

This module provides a registry pattern for managing tools that can be
used by the educational agents. It supports both LangChain tools and
MCP (Model Context Protocol) server integrations.
"""

from typing import Any

from langchain_core.tools import BaseTool


class ToolRegistry:
    """Registry for pluggable tools and MCPs.

    This class provides a centralized way to register and retrieve tools
    that can be used by the educational agents. It supports:
    - LangChain BaseTool instances
    - MCP client integrations (for future use)

    Example:
        >>> from langchain.tools import tool
        >>> @tool
        ... def my_tool(x: str) -> str:
        ...     return f"Processed: {x}"
        >>> tool_registry.register_tool(my_tool)
        >>> tools = tool_registry.get_all_tools()
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: dict[str, BaseTool] = {}
        self._mcp_clients: dict[str, Any] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Register a LangChain tool.

        Args:
            tool: A LangChain BaseTool instance
        """
        self._tools[tool.name] = tool

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool by name.

        Args:
            name: The name of the tool to remove
        """
        if name in self._tools:
            del self._tools[name]

    def register_mcp(self, name: str, client: Any) -> None:
        """Register an MCP client for future tool integration.

        Args:
            name: A unique identifier for this MCP client
            client: The MCP client instance
        """
        self._mcp_clients[name] = client

    def unregister_mcp(self, name: str) -> None:
        """Unregister an MCP client by name.

        Args:
            name: The name of the MCP client to remove
        """
        if name in self._mcp_clients:
            del self._mcp_clients[name]

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a specific tool by name.

        Args:
            name: The name of the tool

        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)

    def get_tools(self, names: list[str] | None = None) -> list[BaseTool]:
        """Get tools by name or all tools if no names specified.

        Args:
            names: Optional list of tool names to retrieve

        Returns:
            List of matching tools
        """
        if names is None:
            return list(self._tools.values())
        return [self._tools[n] for n in names if n in self._tools]

    def get_all_tools(self) -> list[BaseTool]:
        """Get all registered tools including MCP-converted tools.

        Returns:
            List of all available tools
        """
        tools = list(self._tools.values())
        # Future: Convert MCP tools to LangChain tools and add them
        # Example:
        # for mcp_client in self._mcp_clients.values():
        #     tools.extend(mcp_client.get_langchain_tools())
        return tools

    def get_mcp_client(self, name: str) -> Any | None:
        """Get a specific MCP client by name.

        Args:
            name: The name of the MCP client

        Returns:
            The MCP client if found, None otherwise
        """
        return self._mcp_clients.get(name)

    def list_tool_names(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def list_mcp_names(self) -> list[str]:
        """List all registered MCP client names.

        Returns:
            List of MCP client names
        """
        return list(self._mcp_clients.keys())

    def clear(self) -> None:
        """Clear all registered tools and MCP clients."""
        self._tools.clear()
        self._mcp_clients.clear()


# Global registry instance - singleton pattern
tool_registry = ToolRegistry()
