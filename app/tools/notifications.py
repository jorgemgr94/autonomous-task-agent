"""Notification tool for sending alerts."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class SendNotificationInput(BaseModel):
    """Input schema for send_notification tool."""

    recipient: str = Field(..., description="Email or user ID of the recipient")
    message: str = Field(
        ..., min_length=1, max_length=500, description="Notification message"
    )
    channel: Literal["email", "sms", "slack"] = Field(
        default="email", description="Notification channel"
    )
    priority: Literal["low", "normal", "high"] = Field(
        default="normal", description="Message priority"
    )


class SendNotificationTool(BaseTool):
    """Send a notification to a user."""

    name = "send_notification"
    description = "Send a notification message to a user via email, SMS, or Slack"
    has_side_effects = True

    def execute(self, **kwargs: Any) -> ToolResult:
        # Validate input
        try:
            inputs = SendNotificationInput(**kwargs)
        except Exception as e:
            return ToolResult(success=False, error=f"Invalid input: {e}")

        # Simulate sending notification
        # NOTE: Here we are simulating the notification sending.

        return ToolResult(
            success=True,
            data={
                "recipient": inputs.recipient,
                "channel": inputs.channel,
                "priority": inputs.priority,
                "status": "sent",
                "message_preview": inputs.message[:50] + "..."
                if len(inputs.message) > 50
                else inputs.message,
            },
        )
