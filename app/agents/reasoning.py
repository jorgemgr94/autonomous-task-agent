"""Reasoning agent that analyzes tasks and produces structured decisions."""

import json
import logging
from typing import cast

from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from app.agents.prompts import build_system_prompt
from app.config import settings
from app.schemas.task import AgentDecision, DecisionType, Observation, TaskInput
from app.tools import registry

logger = logging.getLogger(__name__)

# Retry configuration
MAX_PARSE_RETRIES = 2


class ReasoningAgent:
    """Agent that reasons about tasks and produces structured decisions.

    This agent does NOT execute tools - it only decides what to do.
    Tool execution is handled by the dispatcher.
    """

    def __init__(self, temperature: float = 0.0):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )

    @property
    def system_prompt(self) -> str:
        """Build system prompt with current available tools."""
        return build_system_prompt(registry.list_tools())

    def reason(
        self,
        task_input: TaskInput,
        observations: list[Observation] | None = None,
    ) -> AgentDecision:
        """Analyze a task and produce a structured decision.

        Includes retry logic for malformed LLM outputs.

        Args:
            task_input: The task to analyze
            observations: Previous tool execution results (for observation loop)

        Returns:
            AgentDecision with the agent's decision

        Raises:
            ValueError: If LLM output cannot be parsed after retries
        """
        messages = self._build_messages(task_input, observations)
        last_error: Exception | None = None

        logger.info(
            "agent.reason.start",
            extra={
                "task": task_input.task[:100],
                "observations_count": len(observations) if observations else 0,
            },
        )

        for attempt in range(1, MAX_PARSE_RETRIES + 1):
            try:
                response = self.llm.invoke(messages)
                raw_output = cast(str, response.content)

                logger.debug(
                    "agent.llm.response",
                    extra={"attempt": attempt, "output_length": len(raw_output)},
                )

                decision = self._parse_decision(raw_output)

                logger.info(
                    "agent.reason.success",
                    extra={
                        "decision_type": decision.decision_type.value,
                        "has_tool_call": decision.tool_call is not None,
                        "attempt": attempt,
                    },
                )

                return decision

            except ValueError as e:
                last_error = e
                logger.warning(
                    "agent.parse.retry",
                    extra={"attempt": attempt, "error": str(e)},
                )

                if attempt < MAX_PARSE_RETRIES:
                    # Add a hint to the conversation for retry
                    messages.append(
                        {
                            "role": "user",
                            "content": "Your response was not valid JSON. Please respond with ONLY valid JSON, no markdown.",
                        }
                    )
                    continue

        # All retries exhausted
        logger.error(
            "agent.reason.failed",
            extra={"attempts": MAX_PARSE_RETRIES, "error": str(last_error)},
        )
        raise ValueError(
            f"Failed to get valid response after {MAX_PARSE_RETRIES} attempts: {last_error}"
        )

    def _build_messages(
        self,
        task_input: TaskInput,
        observations: list[Observation] | None = None,
    ) -> list[dict[str, str]]:
        """Build the message history for the LLM."""
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._format_task(task_input)},
        ]

        if observations:
            for obs in observations:
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "decision_type": "use_tool",
                                "reasoning": f"Calling {obs.tool_name}",
                                "tool_call": {
                                    "tool_name": obs.tool_name,
                                    "arguments": {},
                                },
                            }
                        ),
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": self._format_observation(obs),
                    }
                )

        return messages

    def _format_task(self, task_input: TaskInput) -> str:
        """Format the initial task message."""
        message = f"Task: {task_input.task}"

        if task_input.context:
            context_str = json.dumps(task_input.context, indent=2)
            message += f"\n\nContext:\n{context_str}"

        return message

    def _format_observation(self, observation: Observation) -> str:
        """Format a tool observation for the agent."""
        if observation.success:
            result_str = json.dumps(observation.result, indent=2)
            return (
                f"Tool '{observation.tool_name}' executed successfully.\n\n"
                f"Result:\n{result_str}\n\n"
                f"What would you like to do next?"
            )
        else:
            return (
                f"Tool '{observation.tool_name}' failed.\n\n"
                f"Error: {observation.error}\n\n"
                f"What would you like to do next?"
            )

    def _parse_decision(self, raw_output: str) -> AgentDecision:
        """Parse LLM output into an AgentDecision.

        Raises:
            ValueError: If parsing or validation fails
        """
        cleaned = raw_output.strip()

        # Handle markdown code fences
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        try:
            return AgentDecision(
                decision_type=DecisionType(data.get("decision_type")),
                reasoning=data.get("reasoning", ""),
                message=data.get("message"),
                tool_call=data.get("tool_call"),
            )
        except (ValidationError, ValueError) as e:
            raise ValueError(f"Schema validation failed: {e}") from e
