# Autonomous Task Agent (The Body) — Roadmap

## Overview

This project is the **Execution Engine**. While the RAG system *thinks* and *understands*, this agent *acts*. It is designed for reliability, safety, and real-world integration.

---

## 2026 Vision: The Agentic Worker

The "Task Agent" is no longer just a script; it is a **Digital Employee**.

- **Standardized Interfaces**: Clean, typed contracts for tool execution (Pydantic).
- **Human-in-the-Loop (HITL)**: Seamless handoff for critical decisions.
- **Autonomous Error Recovery**: Self-healing workflows that don't crash on the first API error.

---

## Roadmap Status

| Milestone | Focus | Status |
|-----------|-------|:------:|
| ** Phase 1: Core Engine ** | | |
| M1: API & Server Foundation | Architecture | ✅ |
| M2: Tool Registry System | Tools | ✅ |
| M3: Basic Observation Loop | Reasoning | ✅ |
| ** Phase 2: Advanced Capabilities ** | | |
| M4: Reliability Patterns | Resilience | 🆕 |
| M5: Human-in-the-Loop UI & Streamlit | Safety/UX | 🆕 |
| M6: Dynamic Planning (ReAct/Plan-and-Solve) | Autonomy | 🆕 |
| ** Phase 3: Production Readiness ** | | |
| M7: Docker & Containerization | Deployment | ⏳ |
| M8: Authentication & Security | Security | 🆕 |
| M9: Structured Observability | Monitoring | 🆕 |

---

## Detailed Milestones

### Phase 2: Advanced Capabilities

**Goal:** Enable the agent to handle complex, messy real-world tasks and provide a testing interface.

#### Milestone 4: Reliability & Circuit Breakers
*Production agents must survive flakiness.*
- [ ] **Circuit Breakers**: Stop calling a tool if it fails 5 times in a row.
- [ ] **Exponential Backoff**: Smart retries for rate-limited APIs.
- [ ] **Dead Letter Queues**: Handling tasks that simply cannot be completed.

#### Milestone 5: Human-in-the-Loop (HITL) Workflow & Streamlit UI
*Robots shouldn't push the big red button alone.*
- [ ] **Streamlit Playground**: Create a dashboard to trigger and monitor agent tasks.
- [ ] **Suspension State**: Agent pauses and waits for human feedback.
- [ ] **Approval UI**: Interface for humans to review and approve "Planned Actions".
- [ ] "Edit the Plan": Allow humans to correct the agent's course before it resumes.

#### Milestone 6: Advanced Planning Patterns
- [ ] **Plan-and-Solve**: Generate a full plan before executing step 1.
- [ ] **Hierarchical Agents**: A "Manager" agent breaking tasks for "Worker" agents.
- [ ] **Reflexion**: Agent critiques its own past performance to improve future attempts.

### Phase 3: Production Readiness

**Goal:** Move from "it runs on my machine" to "it runs in production".

#### Milestone 7: Docker & Cloud Deployment
- [ ] Optimize Dockerfile for production (multi-stage builds).
- [ ] Kubernetes/Helm chart basics (for scaling workers).
- [ ] CI/CD Pipeline (GitHub Actions).

#### Milestone 8: Authentication & Security
- [ ] API Key Management for incoming requests.
- [ ] Secret Management: Securely handling API keys for Tools (Slack_Token, CRM_Key).
- [ ] Role-Based Access Control (RBAC) for who can trigger which tools.

#### Milestone 9: Structured Observability
- [ ] **OpenTelemetry** integration (Tracing agent thoughts across services).
- [ ] Cost-tracking per task.
- [ ] "Black Box" logging: Save every thought/action/result for post-mortem analysis.
