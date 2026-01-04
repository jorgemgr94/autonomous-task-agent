"""Task processing service - main entry point for agent execution."""

import logging

from app.agents.dispatcher import dispatch_tool
from app.agents.reasoning import ReasoningAgent
from app.schemas.task import (
    AgentDecision,
    AgentResponse,
    DecisionType,
    ResponseStatus,
    TaskInput,
)

logger = logging.getLogger(__name__)

# Initialize the reasoning agent
_agent = ReasoningAgent()


def process_task(task_input: TaskInput) -> AgentResponse:
    """Process a task and return the agent's response.

    This orchestrates the agent reasoning, tool execution,
    and converts the final decision into a response.
    """
    try:
        # Get agent's decision
        decision = _agent.reason(task_input)

        # Handle tool execution if needed
        if decision.decision_type == DecisionType.USE_TOOL:
            return _handle_tool_decision(decision)

        # Convert other decisions to response
        return _decision_to_response(decision)

    except ValueError as e:
        # Parsing/validation errors from agent
        logger.error("Agent reasoning failed: %s", e)
        return AgentResponse(
            status=ResponseStatus.FAILED,
            message="I encountered an error while processing your request.",
            data={"error": str(e)},
        )
    except Exception as e:
        # Unexpected errors
        logger.exception("Unexpected error processing task")
        return AgentResponse(
            status=ResponseStatus.FAILED,
            message="An unexpected error occurred.",
            data={"error": str(e)},
        )


def _handle_tool_decision(decision: AgentDecision) -> AgentResponse:
    """Handle a USE_TOOL decision by executing the tool.

    Args:
        decision: The agent's decision with tool_call

    Returns:
        AgentResponse with tool execution results
    """
    if decision.tool_call is None:
        logger.error("USE_TOOL decision without tool_call")
        return AgentResponse(
            status=ResponseStatus.FAILED,
            message="Agent decided to use a tool but didn't specify which one.",
            data={"reasoning": decision.reasoning},
        )

    # Dispatch the tool
    result = dispatch_tool(decision.tool_call)

    if result.success:
        return AgentResponse(
            status=ResponseStatus.SUCCESS,
            message=decision.message or "Tool executed successfully.",
            data={
                "tool": decision.tool_call.tool_name,
                "result": result.data,
                "reasoning": decision.reasoning,
            },
        )
    else:
        return AgentResponse(
            status=ResponseStatus.FAILED,
            message=result.error or "Tool execution failed.",
            data={
                "tool": decision.tool_call.tool_name,
                "error": result.error,
                "reasoning": decision.reasoning,
            },
        )


def _decision_to_response(decision: AgentDecision) -> AgentResponse:
    """Convert an AgentDecision to an AgentResponse.

    Maps decision types to response statuses.
    """
    status_map = {
        DecisionType.RESPOND: ResponseStatus.SUCCESS,
        DecisionType.CLARIFY: ResponseStatus.NEEDS_INPUT,
        DecisionType.ESCALATE: ResponseStatus.ESCALATED,
    }

    status = status_map.get(decision.decision_type, ResponseStatus.FAILED)
    message = decision.message or ""

    return AgentResponse(
        status=status,
        message=message,
        data={"reasoning": decision.reasoning},
    )
