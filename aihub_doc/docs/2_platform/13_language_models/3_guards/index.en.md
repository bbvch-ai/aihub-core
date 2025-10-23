---
title: Input/Output Guards
index: 3
---

# LLM Guards

Guards are real-time safety mechanisms that protect your AI agents from producing inappropriate, inaccurate, or harmful responses. Unlike evaluations (which test agents before deployment), guards actively monitor and intervene during live conversations with users.

## Input Guards vs Output Guards

Guards operate at two critical points in the conversation flow:

**Input Guards** analyze user questions before they reach the agent. They determine whether a question is appropriate, on-topic, and safe to process. Input guards can block off-topic requests, filter out policy violations, or request clarification before the agent begins processing.

**Output Guards** inspect the agent's generated response before it's sent to the user. They verify the response quality, detect sensitive information that should be redacted, and ensure the agent hasn't hallucinated or produced harmful content.

Both types operate automatically in the background. The entire guard evaluation process is fast (typically 100-500ms per guard), adding minimal delay to the conversation.

## Available Guard Types

The AI-Hub provides several guards, each addressing a specific risk. Whether and how these can be enabled depends on the agent's implementation.

### Input Guards

Input guards analyze user questions before the agent processes them.

**Agent Description Guard**

Ensures user questions align with the agent's intended purpose. Prevents off-topic questions that would result in low-quality responses outside the agent's expertise.

*Example:* A user asks a financial compliance agent, "What's the weather forecast?" The guard blocks this and informs the user that the agent only handles financial questions.

**Few-Shot Guard**

Enforces custom company policies using specific examples. You provide examples of acceptable and unacceptable requests, and the guard learns to enforce these patterns.

*Example:* Your policy prohibits using work assistants for personal entertainment. You configure the guard with examples like "Recommend a movie" (blocked) vs. "Recommend a project management tool" (allowed).

### Output Guards

Output guards inspect agent-generated responses before they reach the user.

**Context Sufficient Guard**

Verifies the agent has enough relevant information to answer accurately. Reduces hallucination by blocking responses when the agent lacks sufficient knowledge. Critical for RAG agents that retrieve information from knowledge bases.

*Example:* A user asks a detailed technical question. The guard checks if the retrieved documents contain enough information to answer fully. If not, it informs the user that the information isn't available.

::: tip Configuration Note
Some agents (like the RAG Agent) can be configured to automatically use the Context Sufficient Guard to ensure high-quality, evidence-based responses.
:::

**Sensitive Info Guard**

Detects and removes confidential or personally identifiable information (PII) from agent responses. Protects your organization from data leaks and helps maintain compliance with privacy regulations like GDPR.

*Example:* An agent retrieves a document containing an employee's email. Before sending the response, the guard detects and redacts the email, replacing it with `[REDACTED]`.

## When to Use Guards

The decision to enable guards depends on your agent's purpose, audience, and risk profile.

::: warning High-Risk Scenarios (Guards Recommended)
- Customer-facing agents accessible to external users
- Compliance-critical domains like healthcare, finance, or legal
- Agents with access to sensitive data or internal databases
- Multi-purpose agents where scope control is important
:::

::: tip Lower-Risk Scenarios (Fewer Guards Needed)
- Internal tools for trusted employees in a controlled environment
- Narrow-scope agents with a highly specialized, limited purpose
- Development/testing environments where speed is prioritized
:::

## Configuration and Monitoring

Guards are built into agents during development. The level of control depends on how the agent was designed. Some agents come with guards that cannot be disabled, some allow you to enable or disable specific guards through the configuration interface, and some may not support guard customization at all.

The AI-Hub tracks all guard activations, allowing you to monitor how often they trigger and analyze patterns in real-world usage.

::: tip Best Practice
For customer-facing or high-risk agents, prefer agents that include appropriate guards by default. If you have the option to disable guards, do so only after careful consideration of the risks and thorough testing in a development environment.
:::

