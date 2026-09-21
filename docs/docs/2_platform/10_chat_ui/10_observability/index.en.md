---
title: Observability
---

# Observability

The Swiss AI Hub provides visibility into agent execution processes. Users can see the steps an agent executed, the
decisions it made, and the data it processed.

## Why observability matters

Traditional AI systems show results without showing reasoning. Users see responses but can't see intermediate steps,
decision logic, or where things went wrong.

Decision-makers hesitate to rely on systems they can't understand or validate. When AI produces unexpected results,
users need information to determine whether the system malfunctioned or correctly processed flawed input.

Development teams debugging unexpected agent behavior need more than log files. Quality assurance teams need systematic
ways to validate agent behavior.

Regulated industries need to explain and justify AI-assisted decisions. Compliance frameworks require evidence showing
how systems reached conclusions and where human oversight occurred.

## How execution tracing works

The platform captures detailed records of agent workflow execution.

Execution traces show the complete sequence of steps the agent executed - decision points, tool invocations, knowledge
retrievals, intermediate calculations. Users see structured processes rather than mysterious computations.

Each workflow step consumes input events and produces output events. The trace display shows how data transforms through
the workflow. Input messages become classification events, then retrieval requests, then synthesized responses.

Traces include timing information for each step. Users can identify performance bottlenecks and assess whether slow
responses come from complex reasoning or infrastructure delays.

When workflows include conditional logic, traces show which branches executed and why. This helps users validate that
agents apply appropriate logic to specific scenarios.

## Interactive exploration

Trace display opens an adjacent panel within the chat interface. Users correlate chat responses with workflow steps
without switching applications.

Traces present information hierarchically - workflow overview, step execution, event data. Users drill into areas of
interest without excessive detail for straightforward operations.

At the most granular level, users examine complete event data - the JSON structures flowing between workflow steps. This
supports sophisticated debugging and validation.

From trace views, users navigate to related capabilities - knowledge documents accessed during retrieval, agent
configurations, system logs.

## Langfuse tracing integration

The platform uses Langfuse, an open-source AI observability platform.

The implementation follows OpenInference semantic conventions. Trace data uses standardized formats compatible with
industry observability tools.

The system captures semantic events - LLM invocations, retrieval operations, embedding generations - as structured trace
spans. These capture AI-specific concepts like token usage, retrieval relevance scores, and model selection.

When workflows involve multiple agents, traces maintain correlation across interactions. Users can follow execution
flows spanning multiple agents.

Execution traces persist beyond conversation sessions. Users can review historical executions for quality assurance,
compliance documentation, or incident investigation.

## What this provides

When agents behave unexpectedly, execution traces enable rapid troubleshooting. Support teams examine execution
sequences, identify failure points, and resolve issues without extensive reproduction.

Quality assurance teams validate agent behavior systematically. By examining how agents process inputs and handle edge
cases, QA verifies correctness before production deployment.

Developers identify optimization opportunities from trace data. Traces revealing inefficient patterns or unnecessary
steps guide refinement efforts.

For regulatory compliance, execution traces document how systems reached conclusions. Audits can review traces
demonstrating appropriate data usage and human oversight at required points.

When users can examine execution details, confidence increases. The ability to inspect processes makes AI more
understandable.

## Developer use

Developers building agents use trace visualization during development. Rather than log files or print statements,
developers watch workflows execute through trace interfaces.

Automated tests capture execution traces. Tests can verify that agents invoked appropriate tools, accessed correct
knowledge sources, and followed expected paths.

Trace timing data enables performance profiling. Developers identify slow steps, quantify configuration impacts, and
validate optimization results.

Execution traces serve as living documentation. Developers reference actual traces showing how agents behave in
practice.

## Privacy and security

Access to the Langfuse UI (`langfuse.<domain>`) is restricted to system administrators: only users with the
`AIHubSysAdmin` Keycloak realm role can log in. The restriction is enforced at the Keycloak login itself, so users
without the role are denied before any trace data is reachable.

Trace visibility respects the permission system. Users can only view traces for conversations they participated in or
are authorized to audit. Administrative access requires explicit permissions.

The platform can redact sensitive information from traces - personally identifiable information, confidential data -
while preserving workflow structure.

The system logs trace access, documenting who reviewed which traces and when. This supports compliance requirements and
detects inappropriate access.

Organizations configure trace retention policies balancing observability value against storage costs and regulations.
Traces can expire after periods, or selective retention can preserve significant conversations while aging out routine
interactions.
