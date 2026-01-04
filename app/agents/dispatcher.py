"""Tool dispatcher for executing agent tool calls."""

import logging

from app.schemas.task import ToolCall
from app.tools import ToolError, ToolResult, registry

logger = logging.getLogger(__name__)


def dispatch_tool(tool_call: ToolCall) -> ToolResult:
    """Execute a tool call from the agent.

    Args:
        tool_call: The tool call decision from the agent

    Returns:
        ToolResult with execution outcome

    This function:
    - Validates the tool exists (prevents hallucinated tools)
    - Executes the tool with provided arguments
    - Returns structured results
    """
    logger.info("Dispatching tool: %s", tool_call.tool_name)
    logger.debug("Tool arguments: %s", tool_call.arguments)

    try:
        # Get tool from registry (raises if not found)
        tool = registry.get_or_raise(tool_call.tool_name)

        # Execute tool
        result = tool.execute(**tool_call.arguments)

        logger.info(
            "Tool %s completed: success=%s",
            tool_call.tool_name,
            result.success,
        )

        return result

    except ToolError as e:
        # Tool not found or execution error
        logger.error("Tool error: %s", e)
        return ToolResult(success=False, error=str(e))

    except Exception as e:
        # Unexpected error during tool execution
        logger.exception("Unexpected error executing tool %s", tool_call.tool_name)
        return ToolResult(success=False, error=f"Tool execution failed: {e}")
