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

## Available guards

The AI-Hub includes several guards that address specific risks. Which guards you can enable depends on how your agent
was built.

### Input guards

**Agent description guard**

Checks that questions match what the agent does. A financial compliance agent would block "What's the weather?" and
explain it only handles financial questions.

**Few-shot guard**

Enforces custom policies through examples. If your company prohibits using work assistants for entertainment, you'd
provide examples like "Recommend a movie" (blocked) and "Recommend a project management tool" (allowed). The guard
learns to recognize similar patterns.

### Output guards

**Context sufficient guard**

Checks whether the agent has enough information to answer accurately. Particularly useful for RAG agents that pull from
knowledge bases. If a user asks a detailed technical question but the retrieved documents don't contain enough detail,
the guard stops the response and tells the user the information isn't available.

::: tip Configuration note
Some agents (like the RAG Agent) can use the context sufficient guard automatically to prevent responses without
adequate evidence.
:::

**Sensitive info guard**

Finds and removes confidential or personally identifiable information from responses. If an agent retrieves a document
containing an employee email, the guard redacts it before the user sees it, replacing it with `[REDACTED]`.

## When to use guards

Your agent's purpose, audience, and risk level determine which guards make sense.

Use guards for:

- Customer-facing agents accessible to external users
- Compliance-critical domains like healthcare, finance, or legal
- Agents with access to sensitive data or internal databases
- Multi-purpose agents where controlling scope matters

You may need fewer guards for:

- Internal tools for trusted employees in controlled environments
- Narrow-scope agents with highly specialized purposes
- Development or testing environments where speed matters more than safety

## Configuration

Guards get built into agents during development. How much control you have depends on the agent's design. Some agents
ship with mandatory guards you can't disable. Others let you toggle specific guards through the configuration interface.
Some don't support customization at all.
