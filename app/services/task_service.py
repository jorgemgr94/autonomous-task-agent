from app.schemas.task import TaskResponse


def process_task(task: str) -> TaskResponse:
    return TaskResponse(
        decision="not_implemented", details="Agent logic not implemented yet"
    )
