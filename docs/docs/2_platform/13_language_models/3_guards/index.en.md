---
title: Input/output guards
---

# LLM guards

Guards check AI agent interactions in real time. They catch inappropriate questions before the agent sees them and
screen responses before users receive them. Unlike evaluations that test agents before deployment, guards run during
live conversations.

## How guards work

Guards check conversations at two points:

Input guards analyze user questions before the agent processes them. They filter out off-topic requests, block policy
violations, or ask for clarification.

Output guards examine agent responses before delivery. They verify quality, redact sensitive information, and catch
hallucinations or harmful content.

::: tip Complete PII protection
Guards work at the agent level. For platform-level PII protection that catches sensitive information in user inputs
before they reach any agent, see [Data Anonymization](../2_anonymization/) which covers Presidio integration. Use both
layers for defense-in-depth.
:::

## Available guards

The Swiss AI Hub includes several guards that address specific risks. Which guards you can enable depends on how your
agent was built.

### Input guards

Agent description guard: Checks that questions match what the agent does. A financial compliance agent would block
"What's the weather?" and explain it only handles financial questions.

Few-shot guard: Enforces custom policies through examples. If your company prohibits using work assistants for
entertainment, you'd provide examples like "Recommend a movie" (blocked) and "Recommend a project management tool"
(allowed). The guard learns to recognize similar patterns.

### Output guards

Context sufficient guard: Checks whether the agent has enough information to answer accurately. Particularly useful for
RAG agents that pull from knowledge bases. If a user asks a detailed technical question but the retrieved documents
don't contain enough detail, the guard stops the response and tells the user the information isn't available.

::: tip Configuration note
Some agents (like the RAG Agent) can use the context sufficient guard automatically to prevent responses without
adequate evidence.
:::

Sensitive info guard: Detects and redacts confidential or personally identifiable information in agent responses. This
catches PII that appears in retrieved documents. For example, if an agent pulls a document containing an employee email
address, the guard redacts it before the user sees it, replacing it with `[REDACTED]`.

## When to use guards

| Agent type                                               | Recommended guards                                                               |
| -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Customer-facing agents                                   | Agent description guard, Few-shot guard (for policies), Context sufficient guard |
| Compliance-critical domains (healthcare, finance, legal) | All guards + [Presidio PII protection](../2_anonymization/)                      |
| Internal knowledge assistants                            | Agent description guard, Context sufficient guard                                |
| Narrow-scope specialized agents                          | Context sufficient guard (minimal guardrails needed)                             |
| Development/testing environments                         | Optional (prioritize speed over safety)                                          |

## Relationship with Presidio

Guards and [Presidio anonymization](../2_anonymization/) operate at different layers to provide complete PII protection:

| Layer                          | Component                            | Purpose                                                                  |
| ------------------------------ | ------------------------------------ | ------------------------------------------------------------------------ |
| LiteLLM proxy (platform-level) | Presidio                             | Removes PII from user questions before they reach external LLM providers |
| Agent (application-level)      | Input guards                         | Validate question appropriateness and scope                              |
| Agent (application-level)      | Output guards (Sensitive info guard) | Detect PII in responses from retrieved documents                         |

Presidio protects **user input** from being sent to external providers. The sensitive info guard protects **agent
responses** that might contain PII from your knowledge base documents. Both are needed for complete PII protection.

## Configuration

Guards get built into agents during development. How much control you have depends on the agent's design. Some agents
ship with mandatory guards you can't disable. Others let you toggle specific guards through the configuration interface.
Some don't support customization at all.
