"""Tools package for the educational agents.

This package provides a registry for pluggable tools and MCP integrations.
"""

from project.app.agents.tools.base import ToolRegistry, tool_registry

__all__ = ["ToolRegistry", "tool_registry"]
