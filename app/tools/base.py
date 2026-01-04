"""Base tool interface and registry."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolError(Exception):
    """Raised when tool execution fails."""

    pass


class ToolResult(BaseModel):
    """Standardized result from tool execution."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class BaseTool(ABC):
    """Abstract base class for all tools.

    Tools are explicit automation primitives that:
    - Have validated inputs (via Pydantic schemas)
    - Return structured outputs (ToolResult)
    - Are deterministic (same input → same output)
    - Document their side effects
    """

    name: str
    description: str
    has_side_effects: bool = False  # Does this tool modify external state?

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with validated arguments.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            ToolResult with success status and data/error
        """
        pass

    def get_schema(self) -> dict[str, Any]:
        """Return tool metadata for agent prompt."""
        return {
            "name": self.name,
            "description": self.description,
            "has_side_effects": self.has_side_effects,
        }


class ToolRegistry:
    """Registry of available tools.

    Prevents hallucinated tools by validating tool names
    against registered tools.
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name. Returns None if not found."""
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> BaseTool:
        """Get a tool by name. Raises ToolError if not found."""
        tool = self._tools.get(name)
        if tool is None:
            available = list(self._tools.keys())
            raise ToolError(f"Unknown tool: {name}. Available: {available}")
        return tool

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools with their schemas."""
        return [tool.get_schema() for tool in self._tools.values()]

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())


registry = ToolRegistry()
