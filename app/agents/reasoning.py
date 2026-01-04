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

        Args:
            task_input: The task to analyze
            observations: Previous tool execution results (for observation loop)

        Returns:
            AgentDecision with the agent's decision

        Raises:
            ValueError: If LLM output cannot be parsed
        """
        messages = self._build_messages(task_input, observations)

        logger.info("Starting reasoning for task: %s", task_input.task[:100])
        if observations:
            logger.info("With %d observation(s)", len(observations))

        response = self.llm.invoke(messages)
        raw_output = cast(str, response.content)

        logger.debug("Raw LLM output: %s", raw_output)

        decision = self._parse_decision(raw_output)

        logger.info(
            "Decision made: type=%s, reasoning=%s",
            decision.decision_type.value,
            decision.reasoning[:100],
        )

        return decision

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
                # Add each observation as assistant action + result
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
        """Parse LLM output into an AgentDecision."""
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1])

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM output as JSON: %s", e)
            raise ValueError(f"LLM output is not valid JSON: {e}") from e

        try:
            decision = AgentDecision(
                decision_type=DecisionType(data.get("decision_type")),
                reasoning=data.get("reasoning", ""),
                message=data.get("message"),
                tool_call=data.get("tool_call"),
            )
        except (ValidationError, ValueError) as e:
            logger.error("Failed to validate decision schema: %s", e)
            raise ValueError(f"LLM output does not match expected schema: {e}") from e

        return decision
