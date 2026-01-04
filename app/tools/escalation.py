"""Escalation tool for human handoff."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class EscalateToHumanInput(BaseModel):
    """Input schema for escalate_to_human tool."""

    reason: str = Field(..., min_length=10, description="Reason for escalation")
    priority: Literal["low", "normal", "high", "urgent"] = Field(
        default="normal", description="Escalation priority"
    )
    context: str | None = Field(
        default=None, description="Additional context for the human operator"
    )


class EscalateToHumanTool(BaseTool):
    """Escalate a task to a human operator."""

    name = "escalate_to_human"
    description = (
        "Escalate the current task to a human operator when the agent cannot proceed"
    )
    has_side_effects = True

    def execute(self, **kwargs: Any) -> ToolResult:
        # Validate input
        try:
            inputs = EscalateToHumanInput(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=f"Invalid input: {e}")

        # Simulate escalation ticket creation
        # NOTE: Here we are simulating the escalation ticket creation.

        return ToolResult(
            success=True,
            data={
                "escalation_id": "ESC-001",
                "reason": inputs.reason,
                "priority": inputs.priority,
                "status": "pending_review",
                "message": "Task has been escalated to a human operator",
            },
        )
