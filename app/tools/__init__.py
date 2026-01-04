"""Tool system initialization and registration."""

from app.tools.base import BaseTool, ToolError, ToolRegistry, ToolResult, registry
from app.tools.escalation import EscalateToHumanTool
from app.tools.notifications import SendNotificationTool
from app.tools.orders import CreateOrderTool
from app.tools.pricing import GetPricingTool

# Register all tools
registry.register(GetPricingTool())
registry.register(CreateOrderTool())
registry.register(SendNotificationTool())
registry.register(EscalateToHumanTool())

__all__ = [
    "BaseTool",
    "ToolError",
    "ToolResult",
    "ToolRegistry",
    "registry",
    "GetPricingTool",
    "CreateOrderTool",
    "SendNotificationTool",
    "EscalateToHumanTool",
]
