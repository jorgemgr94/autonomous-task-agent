import logging

from app.agents.reasoning import ReasoningAgent
from app.schemas.task import AgentResponse, DecisionType, ResponseStatus, TaskInput

logger = logging.getLogger(__name__)

# Initialize the reasoning agent
_agent = ReasoningAgent()


def process_task(task_input: TaskInput) -> AgentResponse:
    """Process a task and return the agent's response.

    This orchestrates the agent reasoning and converts
    the decision into a final response.
    """
    try:
        # Get agent's decision
        decision = _agent.reason(task_input)

        # Convert decision to response
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


def _decision_to_response(decision) -> AgentResponse:
    """Convert an AgentDecision to an AgentResponse.

    Maps decision types to response statuses.
    """
    status_map = {
        DecisionType.RESPOND: ResponseStatus.SUCCESS,
        DecisionType.CLARIFY: ResponseStatus.NEEDS_INPUT,
        DecisionType.ESCALATE: ResponseStatus.ESCALATED,
        DecisionType.USE_TOOL: ResponseStatus.FAILED,  # No tools yet (M3/M4)
    }

    status = status_map.get(decision.decision_type, ResponseStatus.FAILED)

    # For USE_TOOL, explain that tools aren't implemented yet
    message = decision.message or ""
    if decision.decision_type == DecisionType.USE_TOOL:
        message = "Tool execution is not yet implemented."

    return AgentResponse(
        status=status,
        message=message,
        data={"reasoning": decision.reasoning},
    )
