# Architecture Overview

## System Flow

```mermaid
flowchart TD
    subgraph Client
        A[POST /tasks]
    end

    subgraph API["API Layer (main.py)"]
        B[TaskRequest] -->|validate| C[TaskInput]
    end

    subgraph Service["Task Service (task_service.py)"]
        D[process_task]
        
        subgraph Loop["Observation Loop"]
            E[Agent Reasoning] --> F{Decision?}
            F -->|USE_TOOL| G[Dispatcher]
            G --> H[Execute Tool]
            H --> I[Observation]
            I --> E
            F -->|RESPOND/CLARIFY/ESCALATE| J[Final Response]
        end
    end

    subgraph Tools["Tool System"]
        subgraph Registry["Tool Registry"]
            N[get_pricing]
            O[create_order]
            P[send_notification]
            Q[escalate_to_human]
        end
        G --> R[tool.execute]
        R --> S[ToolResult]
    end

    subgraph Response["AgentResponse"]
        T[status + message + data]
    end

    A --> B
    C --> D
    D --> E
    J --> T
    S --> I
```

## Observation Loop

```mermaid
flowchart TD
    Task[User Task] --> Reason[Agent Reasoning]
    Reason --> Decision{Decision Type}
    
    Decision -->|USE_TOOL| Execute[Execute Tool]
    Execute --> Observe[Create Observation]
    Observe -->|Feed back| Reason
    
    Decision -->|RESPOND| Final[Final Response]
    Decision -->|CLARIFY| Final
    Decision -->|ESCALATE| Final
    
    Guard{Max Iterations?} -->|Yes| Fail[Return Error]
    
    style Observe fill:#f9f,stroke:#333
```

The observation loop allows the agent to:
- **Chain multiple tool calls** — Get price, then create order
- **React to failures** — Try alternative approach
- **Craft informed responses** — Based on actual tool results
- **Safe execution** — Max 5 iterations prevents infinite loops

## Decision Flow

```mermaid
flowchart LR
    Task[User Task] --> Agent[Agent Reasoning]
    Agent --> Decision{Decision Type}
    
    Decision -->|RESPOND| R1[Direct Answer]
    Decision -->|CLARIFY| R2[Ask for Info]
    Decision -->|ESCALATE| R3[Human Handoff]
    Decision -->|USE_TOOL| Tool[Execute Tool]
    
    Tool --> Obs[Observation]
    Obs --> Agent
    
    R1 --> Response[AgentResponse]
    R2 --> Response
    R3 --> Response
```

## Tool Execution

```mermaid
sequenceDiagram
    participant S as TaskService
    participant A as Agent
    participant D as Dispatcher
    participant R as Registry
    participant T as Tool

    S->>A: reason(task, observations)
    A-->>S: AgentDecision(USE_TOOL)
    
    S->>D: dispatch_tool(tool_call)
    D->>R: get_or_raise(tool_name)
    
    alt Tool Not Found
        R-->>D: ToolError
        D-->>S: ToolResult(success=false)
    else Tool Found
        R-->>D: BaseTool
        D->>T: execute(**arguments)
        T-->>D: ToolResult
        D-->>S: ToolResult
    end
    
    S->>S: Create Observation
    S->>A: reason(task, [observation])
    A-->>S: AgentDecision(RESPOND)
```

## Component Summary

| Component | File | Responsibility |
|-----------|------|----------------|
| **API Layer** | `main.py` | HTTP endpoints, request/response validation |
| **Task Service** | `task_service.py` | Observation loop, orchestrates agent + tools |
| **Reasoning Agent** | `reasoning.py` | LLM integration, accepts observations |
| **Prompts** | `prompts.py` | Dynamic system prompt with tool list |
| **Dispatcher** | `dispatcher.py` | Tool lookup and safe execution |
| **Tool Registry** | `tools/base.py` | Tool registration, prevents hallucination |
| **Tools** | `tools/*.py` | Individual tool implementations |
| **Schemas** | `schemas/task.py` | Pydantic models including Observation |
| **Config** | `config.py` | Environment settings |

## Schemas

| Schema | Purpose |
|--------|---------|
| `TaskInput` | What the agent receives |
| `AgentDecision` | Agent's structured decision (type, reasoning, tool_call, message) |
| `ToolCall` | Tool name + arguments |
| `Observation` | Tool execution result fed back to agent |
| `AgentResponse` | Final output (status, message, data) |

## Decision Types

| Decision | Status | When Used |
|----------|--------|-----------|
| `RESPOND` | `success` | Agent has enough information to answer directly |
| `USE_TOOL` | `success`/`failed` | Agent needs to call an external tool |
| `CLARIFY` | `needs_input` | Agent needs more information from user |
| `ESCALATE` | `escalated` | Task requires human intervention |

## Safety Guards

| Guard | Value | Purpose |
|-------|-------|---------|
| `MAX_ITERATIONS` | 5 | Prevents infinite tool loops |
| `MAX_PARSE_RETRIES` | 2 | Retries on malformed LLM output |
| `ToolRegistry` | — | Prevents hallucinated tool names |
| Pydantic validation | — | Validates all inputs/outputs |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Basic liveness check |
| `/status` | GET | Agent config, available tools |
| `/tasks` | POST | Process a task through the agent |

## Design Decisions & Trade-offs

### 1. Structured JSON Output vs Function Calling

**Decision:** Use prompt-based JSON output instead of OpenAI's native function calling.

**Trade-offs:**
- ✅ Model-agnostic (works with any LLM that outputs JSON)
- ✅ Full control over output schema
- ❌ Requires JSON parsing and retry logic
- ❌ Slightly less reliable than native function calling

**Rationale:** Portability and control outweigh the minor reliability cost. Retry logic mitigates parsing failures.

### 2. Observation Loop vs Single-Shot

**Decision:** Implement a multi-turn observation loop instead of single tool call.

**Trade-offs:**
- ✅ Enables multi-step workflows (get price → create order)
- ✅ Agent can react to tool failures
- ❌ Higher latency (multiple LLM calls)
- ❌ Higher token cost

**Rationale:** Business automation requires multi-step workflows. The MAX_ITERATIONS guard prevents runaway costs.

### 3. Tool Registry vs Dynamic Tool Discovery

**Decision:** Explicit tool registration in `__init__.py`.

**Trade-offs:**
- ✅ Prevents hallucinated tool names
- ✅ Clear, auditable list of capabilities
- ❌ Requires code change to add tools
- ❌ No runtime tool discovery

**Rationale:** For business automation, explicit > implicit. Security and predictability are priorities.

### 4. Pydantic Settings vs Raw Environment Variables

**Decision:** Use `pydantic-settings` for configuration.

**Trade-offs:**
- ✅ Type-safe configuration
- ✅ Automatic .env loading
- ✅ Fail-fast on missing required values
- ❌ Additional dependency

**Rationale:** Type safety and validation at startup prevent runtime configuration errors.

### 5. Synchronous API vs Async

**Decision:** Synchronous FastAPI endpoints (for now).

**Trade-offs:**
- ✅ Simpler code, easier debugging
- ✅ LangChain's sync API is more stable
- ❌ Lower throughput under load
- ❌ Blocking during LLM calls

**Rationale:** Simplicity for MVP. Async can be added in M9 (Production Readiness) if needed.

### 6. Centralized Task Service vs Distributed Handlers

**Decision:** Single `process_task()` function orchestrates everything.

**Trade-offs:**
- ✅ Easy to follow the flow
- ✅ Single place for logging and error handling
- ❌ Could become a "god function"
- ❌ Harder to test in isolation

**Rationale:** For current complexity, centralization aids understanding. Refactor when the service grows.

## Logging Strategy

All logs use structured format with `extra` dict for machine-readable fields:

```python
logger.info("task.complete", extra={
    "decision": "respond",
    "iterations": 2,
    "tools_called": 1,
    "duration_ms": 1234,
})
```

Log events follow `component.action` naming:
- `task.start`, `task.complete`, `task.error.*`
- `agent.reason.start`, `agent.reason.success`
- `agent.parse.retry`, `agent.llm.response`
