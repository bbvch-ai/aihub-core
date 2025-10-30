---
title: Agents
---

# Agents

At the heart of the Swiss AI Hub are **Agents**: specialized AI assistants designed to perform specific tasks within a
structured and reliable framework. Unlike open-ended chatbots, our agents operate like expert colleagues. You interact
with them through the chat interface, and they follow well-defined workflows to help you analyze documents, answer
questions, or complete business processes.

This structured approach is a core design choice. It ensures that agents are not only intelligent but also predictable,
transparent, and auditable—qualities essential for enterprise and public sector use.

## What is an Agent?

In the Swiss AI Hub, an agent is an AI-powered assistant that you interact with in a chat. Each agent is configured to
handle a specific set of tasks using a predefined workflow.

Think of them as digital specialists:

- An **HR Policy Agent** can answer questions about your company's leave policies by consulting the official employee
  handbook.
- A **Financial Analyst Agent** can help you query last quarter's sales data from a specific report.
- A **Project Support Agent** can summarize the latest status updates from a collection of project documents.

These agents combine the power of large language models (LLMs) for natural language understanding with the reliability
of a structured process.

## How Agents Work: The Workflow Advantage

An agent's behavior is guided by a **workflow**, which is a predefined sequence of steps. This is the key difference
between our agents and a general-purpose AI like ChatGPT.

A typical workflow might look like this:

1. **Understand the User's Request**: The agent uses an LLM to interpret your question.
2. **Retrieve Relevant Information**: If necessary, the agent performs a semantic search on a designated knowledge base
   (e.g., a specific SharePoint folder) to find relevant documents. This is known as Retrieval-Augmented Generation
   (RAG).
3. **Synthesize the Answer**: The agent combines your original question with the retrieved information and uses an LLM
   to generate a clear, accurate, and helpful response.
4. **Cite Sources**: The final answer includes direct references to the source documents, so you can always verify the
   information.

This workflow-based approach delivers several key benefits:

- **Transparency**: You can see the steps the agent took to arrive at an answer, including which documents it consulted.
  This eliminates the "black box" problem and builds trust.
- **Reliability**: By constraining the agent to a specific workflow and knowledge base, the risk of "hallucinations" or
  factually incorrect answers is dramatically reduced.
- **Control**: Administrators and developers define what an agent can and cannot do. An agent can't decide to access
  data it shouldn't or perform actions outside its defined workflow.

## Agents in Action: A Practical Example

Imagine you ask the "IT Support Agent": *“How do I set up the new VPN on my laptop?”*

Instead of giving a generic answer from the internet, the agent executes its workflow:

1. It identifies the keywords "VPN" and "setup."
2. It searches the company's internal "IT Knowledge Base" for documents matching these terms.
3. It finds the official, up-to-date guide titled "VPN_Setup_Guide_v3.pdf."
4. It reads the relevant sections of the PDF.
5. It provides you with a step-by-step summary based *only* on that document and includes a direct link to the PDF for
   your reference.

The result is a trustworthy, relevant, and verifiable answer. This is the power of combining AI's language capabilities
with structured, auditable workflows.

## Human-in-the-Loop: Collaboration, Not Just Automation

Some tasks require human judgment. Our agent workflows are designed to seamlessly integrate human oversight. An agent
can be configured to pause its process and wait for your approval before taking a critical step. For example, an agent
might prepare a draft response to a customer inquiry but wait for a support team member to review and approve it before
sending.

This "human-in-the-loop" capability makes our agents powerful assistants for complex processes, allowing you to automate
the routine parts of a task while keeping full control over the final decision.
