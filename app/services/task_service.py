from app.schemas.task import AgentResponse, ResponseStatus, TaskInput


def process_task(task_input: TaskInput) -> AgentResponse:
    """Process a task and return the agent's response.

    This is the main entry point for agent processing.
    Currently returns a placeholder
    """
    return AgentResponse(
        status=ResponseStatus.FAILED,
        message="Agent logic not implemented yet",
        data={"received_task": task_input.task},
    )
