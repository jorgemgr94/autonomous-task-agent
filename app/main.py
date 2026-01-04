from fastapi import FastAPI

app = FastAPI(
    title="Autonomous Task Agent",
    description="Agent with reasoning and tool execution capabilities",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
