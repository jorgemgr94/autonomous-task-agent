"""Schema validation tests."""

import pytest
from pydantic import ValidationError

from app.schemas.task import (
    AgentDecision,
    AgentResponse,
    DecisionType,
    Observation,
    ResponseStatus,
    TaskInput,
    ToolCall,
)


def test_task_input_valid():
    """TaskInput should accept valid input."""
    task = TaskInput(task="Do something")
    assert task.task == "Do something"
    assert task.context is None


def test_task_input_with_context():
    """TaskInput should accept context."""
    task = TaskInput(task="Do something", context={"key": "value"})
    assert task.context == {"key": "value"}


def test_task_input_missing_task():
    """TaskInput should reject missing task."""
    with pytest.raises(ValidationError):
        TaskInput()  # type: ignore


def test_agent_decision_respond():
    """AgentDecision should accept RESPOND type."""
    decision = AgentDecision(
        decision_type=DecisionType.RESPOND,
        reasoning="I can answer this",
        message="The answer is 42",
    )
    assert decision.decision_type == DecisionType.RESPOND
    assert decision.tool_call is None


def test_agent_decision_use_tool():
    """AgentDecision should accept USE_TOOL with tool_call."""
    decision = AgentDecision(
        decision_type=DecisionType.USE_TOOL,
        reasoning="Need to get pricing",
        tool_call=ToolCall(
            tool_name="get_pricing", arguments={"product_id": "PROD-001"}
        ),
    )
    assert decision.decision_type == DecisionType.USE_TOOL
    assert decision.tool_call is not None
    assert decision.tool_call.tool_name == "get_pricing"


def test_observation_success():
    """Observation should capture successful tool result."""
    obs = Observation(
        tool_name="get_pricing",
        success=True,
        result={"price": 29.99},
    )
    assert obs.success is True
    assert obs.error is None


def test_observation_failure():
    """Observation should capture failed tool result."""
    obs = Observation(
        tool_name="get_pricing",
        success=False,
        error="Product not found",
    )
    assert obs.success is False
    assert obs.result is None


def test_agent_response_success():
    """AgentResponse should accept success status."""
    response = AgentResponse(
        status=ResponseStatus.SUCCESS,
        message="Done!",
        data={"result": "value"},
    )
    assert response.status == ResponseStatus.SUCCESS


def test_response_status_values():
    """ResponseStatus should have all expected values."""
    assert ResponseStatus.SUCCESS.value == "success"
    assert ResponseStatus.FAILED.value == "failed"
    assert ResponseStatus.NEEDS_INPUT.value == "needs_input"
    assert ResponseStatus.ESCALATED.value == "escalated"
