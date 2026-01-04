from fastapi import FastAPI

from app.schemas.task import TaskRequest, TaskResponse
from app.services.task_service import process_task

app = FastAPI(
    title="Autonomous Task Agent",
    description="Agent with reasoning and tool execution capabilities",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/tasks", response_model=TaskResponse)
def run_task(payload: TaskRequest):
    task_input = payload.to_task_input()
    agent_response = process_task(task_input)
    return TaskResponse.from_agent_response(agent_response)
