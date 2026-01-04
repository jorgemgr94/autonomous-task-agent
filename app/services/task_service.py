"""Task processing service - main entry point for agent execution."""

import logging
import time

from app.agents.dispatcher import dispatch_tool
from app.agents.reasoning import ReasoningAgent
from app.schemas.task import (
    AgentDecision,
    AgentResponse,
    DecisionType,
    Observation,
    ResponseStatus,
    TaskInput,
)

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 5  # Prevent infinite loops

# Initialize the reasoning agent
_agent = ReasoningAgent()


def process_task(task_input: TaskInput) -> AgentResponse:
    """Process a task using the observation loop.

    The agent can:
    1. Decide to use a tool → execute → observe result → decide again
    2. Decide to respond/clarify/escalate → return final response

    Loop continues until agent makes a final decision or max iterations reached.
    """
    observations: list[Observation] = []
    iteration = 0
    start_time = time.time()

    logger.info(
        "task.start",
        extra={
            "task": task_input.task[:100],
            "has_context": task_input.context is not None,
        },
    )

    try:
        while iteration < MAX_ITERATIONS:
            iteration += 1
            logger.info(
                "task.iteration",
                extra={"iteration": iteration, "max": MAX_ITERATIONS},
            )

            # Get agent's decision (with any previous observations)
            decision = _agent.reason(task_input, observations if observations else None)

            # Terminal decisions - return response
            if decision.decision_type in (
                DecisionType.RESPOND,
                DecisionType.CLARIFY,
                DecisionType.ESCALATE,
            ):
                duration = time.time() - start_time
                logger.info(
                    "task.complete",
                    extra={
                        "decision": decision.decision_type.value,
                        "iterations": iteration,
                        "tools_called": len(observations),
                        "duration_ms": int(duration * 1000),
                    },
                )
                return _decision_to_response(decision, observations)

            # USE_TOOL - execute and observe
            if decision.decision_type == DecisionType.USE_TOOL:
                observation = _execute_and_observe(decision)
                observations.append(observation)

                logger.info(
                    "task.tool_executed",
                    extra={
                        "tool": observation.tool_name,
                        "success": observation.success,
                        "iteration": iteration,
                    },
                )

                continue

        # Max iterations reached
        duration = time.time() - start_time
        logger.warning(
            "task.max_iterations",
            extra={
                "iterations": MAX_ITERATIONS,
                "tools_called": len(observations),
                "duration_ms": int(duration * 1000),
            },
        )
        return AgentResponse(
            status=ResponseStatus.FAILED,
            message="I was unable to complete the task within the allowed steps.",
            data={
                "iterations": iteration,
                "observations": [obs.model_dump() for obs in observations],
            },
        )

    except ValueError as e:
        logger.error("task.error.parsing", extra={"error": str(e)})
        return AgentResponse(
            status=ResponseStatus.FAILED,
            message="I encountered an error while processing your request.",
            data={"error": str(e)},
        )
    except Exception as e:
        logger.exception("task.error.unexpected")
        return AgentResponse(
            status=ResponseStatus.FAILED,
            message="An unexpected error occurred.",
            data={"error": str(e)},
        )


def _execute_and_observe(decision: AgentDecision) -> Observation:
    """Execute a tool and return an observation."""
    if decision.tool_call is None:
        logger.error(
            "task.tool.missing", extra={"decision": decision.decision_type.value}
        )
        return Observation(
            tool_name="unknown",
            success=False,
            error="Agent decided to use a tool but didn't specify which one.",
        )

    result = dispatch_tool(decision.tool_call)

    return Observation(
        tool_name=decision.tool_call.tool_name,
        success=result.success,
        result=result.data,
        error=result.error,
    )


def _decision_to_response(
    decision: AgentDecision,
    observations: list[Observation],
) -> AgentResponse:
    """Convert a terminal decision to an AgentResponse."""
    status_map = {
        DecisionType.RESPOND: ResponseStatus.SUCCESS,
        DecisionType.CLARIFY: ResponseStatus.NEEDS_INPUT,
        DecisionType.ESCALATE: ResponseStatus.ESCALATED,
    }

    status = status_map.get(decision.decision_type, ResponseStatus.FAILED)
    message = decision.message or ""

    data: dict = {"reasoning": decision.reasoning}
    if observations:
        data["tool_calls"] = [
            {
                "tool": obs.tool_name,
                "success": obs.success,
                "result": obs.result,
                "error": obs.error,
            }
            for obs in observations
        ]

    return AgentResponse(
        status=status,
        message=message,
        data=data,
    )
