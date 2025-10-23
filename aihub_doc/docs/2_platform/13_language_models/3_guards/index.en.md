---
title: Input/Output Guards
index: 3
---

# LLM Guards

Guards are real-time safety mechanisms that protect your AI agents from producing inappropriate, inaccurate, or harmful
responses. Unlike evaluations (which test agents before deployment), guards actively monitor and intervene during live
conversations with users.

AI agents are powerful, but without proper safeguards, they can answer questions outside their area ofexpertise,
hallucinate information when they lack context, leak sensitive business data, or violate company policies. Guards act as
an automated, real-time quality control layer to prevent this.

They operate automatically in the background. When a user asks a question or the agent generates a response, configured
guards analyze the content. Depending on what's detected, a guard can **allow** the interaction, **block** it and inform
the user, **modify** the output (e.g., redacting sensitive info), or **request additional context**. This process is
very fast (typically 100-500ms per guard), adding minimal delay.

## Available Guard Types

The AI-Hub provides several guards, each addressing a specific risk. Whether and how these can be enabled depends on the
agent's implementation.

**Agent Description Guard**

- **Purpose:** Ensures user questions align with the agent's intended purpose.
- **Why it's useful:** Prevents off-topic questions, which improves user experience and stops the agent from providing
  low-quality responses outside its expertise.
- **Example scenario:** A user asks a financial compliance agent, "What's the weather forecast?" The guard intercepts
  this and politely informs the user that the agent only handles financial questions.

**Context Sufficient Guard**

- **Purpose:** Verifies the agent has enough relevant information to answer the question accurately.
- **Why it's useful:** Reduces hallucination by preventing the agent from responding when it lacks sufficient knowledge.
  This is critical for RAG agents that retrieve information from your knowledge base.
- **Example scenario:** A user asks a detailed technical question. The guard checks if the retrieved documents contain
  enough information to answer fully. If not, it can inform the user that the information isn't available.

::: tip Configuration Note
Some agents (like the RAG Agent) can be configured to automatically use the Context Sufficient Guard to ensure
high-quality, evidence-based responses.
:::

**Few-Shot Guard**

- **Purpose:** Enforces custom company policies and content moderation rules using specific examples.
- **Why it's useful:** Allows you to define organization-specific boundaries. You provide examples of acceptable and
  unacceptable requests, and the guard learns to enforce these patterns.
- **Example scenario:** Your policy prohibits using work assistants for personal entertainment. You configure the guard
  with examples like "Recommend a movie" (blocked) vs. "Recommend a project management tool" (allowed).

**Sensitive Info Guard**

- **Purpose:** Detects and removes confidential or personally identifiable information (PII) from agent responses.
- **Why it's useful:** Protects your organization from data leaks and helps maintain compliance with privacy regulations
  like GDPR.
- **Example scenario:** An agent retrieves a document containing an employee's email. Before sending the response, the
  guard detects and redacts the email, replacing it with `[REDACTED]`.

## Implementation and Strategy

Implementing guards provides tangible value by **reducing risk**, ensuring **quality control**, improving the **user
experience**, and building **confidence in deployment**.

### When to Use Guards

The decision to enable guards depends on your agent's purpose, audience, and risk profile.

::: warning High-Risk Scenarios (Guards Recommended)
- **Customer-facing agents** accessible to external users.
- **Compliance-critical domains** like healthcare, finance, or legal.
- **Agents with access to sensitive data** or internal databases.
- **Multi-purpose agents** where scope control is important.
:::

::: tip Lower-Risk Scenarios (Fewer Guards Needed)
- **Internal tools** for trusted employees in a controlled environment.
- **Narrow-scope agents** with a highly specialized, limited purpose.
- **Development/testing environments** where speed is prioritized.
:::

### Configuration, Performance, and Monitoring

Guards are built into agents during development. The level of control you have depends on how the agent was designed.

::: info What You Can Control
- **Pre-configured guards**: Some agents (like the RAG Agent with Context Sufficient Guard) come with guards built-in
  that cannot be disabled.
- **Optional guards**: Some agents may allow you to enable or disable specific guards through the agent configuration
  interface.
- **No configuration**: Some agents may not support guard customization at all.
:::

While guards add a small, often imperceptible latency (100-500ms), this is a worthwhile trade-off for the safety
benefits. The AI-Hub tracks all guard activations, allowing you to monitor how often they trigger, analyze false
positives, and fine-tune their sensitivity based on real-world data.

::: tip Best Practice
For customer-facing or high-risk agents, prefer agents that include appropriate guards by default. If you have the
option to disable guards, do so only after careful consideration of the risks and ideally after thorough testing in a
development environment.
:::

## Common Questions

::: details Do guards slow down responses?
Guards add minimal latency (typically 100-500ms per guard). For most use cases, this delay is imperceptible and a
worthwhile trade-off for the safety benefits.
:::

::: details Can guards make mistakes?
Yes, like any AI system, guards can occasionally produce false positives (blocking valid requests) or false negatives
(missing problematic content). Regular monitoring and adjustment help minimize these errors.
:::

::: details How do we know guards are working?
The AI-Hub logs all guard activations, showing when guards triggered and what actions they took. You can review these
logs to verify guards are functioning as intended.
:::

::: details What happens when a guard blocks something?
The user receives a polite message explaining why the request couldn't be processed (e.g., "This question is outside my
area of expertise"). This maintains a positive user experience while enforcing boundaries.
:::

::: details Can we customize guards for our business?
The Few-Shot Guard is specifically designed for custom policies through configuration. However, the ability to adjust
guard settings depends on the specific agent implementation. Check your agent's documentation for available
configuration options.
:::
