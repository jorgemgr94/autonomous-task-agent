"""Reasoning agent that analyzes tasks and produces structured decisions."""

import json
import logging
from typing import cast

from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from app.agents.prompts import build_system_prompt
from app.config import settings
from app.schemas.task import AgentDecision, DecisionType, TaskInput
from app.tools import registry

logger = logging.getLogger(__name__)


class ReasoningAgent:
    """Agent that reasons about tasks and produces structured decisions.

    This agent does NOT execute tools - it only decides what to do.
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

    def reason(self, task_input: TaskInput) -> AgentDecision:
        """Analyze a task and produce a structured decision.

        Args:
            task_input: The task to analyze

        Returns:
            AgentDecision with the agent's decision

        Raises:
            ValueError: If LLM output cannot be parsed after retries
        """
        user_message = self._build_user_message(task_input)

        logger.info("Starting reasoning for task: %s", task_input.task[:100])

        # Call LLM
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        response = self.llm.invoke(messages)
        raw_output = cast(str, response.content)

        logger.debug("Raw LLM output: %s", raw_output)

        # Parse and validate
        decision = self._parse_decision(raw_output)

        logger.info(
            "Decision made: type=%s, reasoning=%s",
            decision.decision_type.value,
            decision.reasoning[:100],
        )

        return decision

    def _build_user_message(self, task_input: TaskInput) -> str:
        """Build the user message from task input."""
        message = f"Task: {task_input.task}"

        if task_input.context:
            context_str = json.dumps(task_input.context, indent=2)
            message += f"\n\nContext:\n{context_str}"

        return message

    def _parse_decision(self, raw_output: str) -> AgentDecision:
        """Parse LLM output into an AgentDecision.

        Args:
            raw_output: Raw string from LLM

        Returns:
            Validated AgentDecision

        Raises:
            ValueError: If parsing fails
        """
        # Clean up output (remove markdown code blocks if present)
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            # Remove markdown code fence
            lines = cleaned.split("\n")
            # Skip first line (```json) and last line (```)
            cleaned = "\n".join(lines[1:-1])

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM output as JSON: %s", e)
            raise ValueError(f"LLM output is not valid JSON: {e}") from e

        # Validate against schema
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
