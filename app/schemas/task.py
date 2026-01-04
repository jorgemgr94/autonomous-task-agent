from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Task Input Schema
# =============================================================================


class TaskInput(BaseModel):
    """Input schema for agent tasks.

    This is the primary contract for what the agent receives.
    """

    task: str = Field(..., description="The task description for the agent to process")
    context: dict[str, Any] | None = Field(
        default=None, description="Optional context or metadata for the task"
    )


# =============================================================================
# Agent Decision Schema
# =============================================================================


class DecisionType(str, Enum):
    """Types of decisions the agent can make."""

    USE_TOOL = "use_tool"  # Agent decides to call an external tool
    RESPOND = "respond"  # Agent has enough info to respond directly
    CLARIFY = "clarify"  # Agent needs more information from the user
    ESCALATE = "escalate"  # Agent cannot handle this, escalate to human


class ToolCall(BaseModel):
    """Schema for a tool invocation decision.

    When the agent decides to use a tool, this captures which tool
    and with what arguments.
    """

    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments to pass to the tool"
    )


class AgentDecision(BaseModel):
    """Structured decision output from the agent's reasoning.

    This is the core contract for agent behavior - all decisions
    must be machine-readable and structured.
    """

    decision_type: DecisionType = Field(..., description="The type of decision made")
    reasoning: str = Field(
        ..., description="Internal reasoning (logged, not exposed to users)"
    )
    tool_call: ToolCall | None = Field(
        default=None,
        description="Tool call details (required if decision_type is USE_TOOL)",
    )
    message: str | None = Field(
        default=None,
        description="Message content (for RESPOND, CLARIFY, or ESCALATE decisions)",
    )


# =============================================================================
# Agent Response Schema
# =============================================================================


class ResponseStatus(str, Enum):
    """Status of the agent's final response."""

    SUCCESS = "success"  # Task completed successfully
    FAILED = "failed"  # Task failed (tool error, validation, etc.)
    NEEDS_INPUT = "needs_input"  # Waiting for user clarification
    ESCALATED = "escalated"  # Handed off to human


class AgentResponse(BaseModel):
    """Final structured response from the agent.

    This is what external systems receive after the agent completes processing.
    """

    status: ResponseStatus = Field(..., description="Outcome status of the task")
    message: str = Field(..., description="Human-readable response message")
    data: dict[str, Any] | None = Field(
        default=None, description="Structured data from tool execution (if any)"
    )


# =============================================================================
# API Request/Response Models
# =============================================================================


class TaskRequest(BaseModel):
    """API request model for the /tasks endpoint."""

    task: str = Field(..., description="The task to process")
    context: dict[str, Any] | None = Field(default=None, description="Optional context")

    def to_task_input(self) -> TaskInput:
        """Convert API request to internal TaskInput."""
        return TaskInput(task=self.task, context=self.context)


class TaskResponse(BaseModel):
    """API response model for the /tasks endpoint."""

    status: ResponseStatus = Field(..., description="Outcome status")
    message: str = Field(..., description="Response message")
    data: dict[str, Any] | None = Field(default=None, description="Response data")

    @classmethod
    def from_agent_response(cls, response: AgentResponse) -> "TaskResponse":
        """Convert internal AgentResponse to API response."""
        return cls(
            status=response.status,
            message=response.message,
            data=response.data,
        )
