---
title: Agents
---

# Agents

Agents are specialized AI assistants that perform specific tasks through structured workflows. Unlike open-ended
chatbots, agents follow predefined steps to analyze documents, answer questions, or complete business processes.

Agents can be interactive (responding to user questions via chat) or autonomous (executing tasks automatically on a
schedule or triggered by events). The structured workflow approach makes agents predictable, transparent, and auditable
regardless of how they operate.

## What is an agent?

An agent is an AI-powered assistant configured to handle specific tasks using a predefined workflow.

Examples:

- An HR Policy Agent answers employee questions about leave policies by consulting the employee handbook (interactive,
  chat-based).
- A Compliance Monitoring Agent reviews documents on a schedule, flagging potential policy violations (autonomous,
  scheduled).

Agents combine large language models (LLMs) for understanding natural language with structured processes for reliable
operation.

## Agent "Training"

A common question is whether agents can be "trained" on company data. The Swiss AI Hub does not offer model training or
fine-tuning. Agents access current information through their knowledge bases instead.

When people ask about training an agent, they usually want the agent to know their company's specific information. The
platform accomplishes this through Retrieval-Augmented Generation (RAG). The agent retrieves relevant information from
your knowledge base when answering questions, rather than having that information embedded in the model itself.

Advantages of this approach:

- Information stays current. Update your documents and agents immediately use the new information without any
  reprocessing.
- Transparency. You can see exactly which documents the agent referenced to answer each question.
- Flexibility. Different agents can access different subsets of your knowledge base by configuring which collections
  they can search.

Agents "learn" by accessing an up-to-date knowledge base maintained through data pipelines. Add new documents or update
existing ones and agents automatically incorporate that information.

## How agents work

An agent's behavior follows a workflow, a predefined sequence of steps. This differs from general-purpose conversational
AI.

Example workflow for a question-answering agent:

1. Understand the request: The agent uses an LLM to interpret your question.
2. Retrieve information: The agent searches a designated knowledge base (e.g., a SharePoint folder) for relevant
   documents using semantic search (RAG).
3. Synthesize the answer: The agent combines your question with retrieved information and generates a response.
4. Cite sources: The answer includes references to source documents for verification.

Workflow benefits:

- Transparency: You can see which documents the agent consulted.
- Reliability: Constraining the agent to a workflow and knowledge base reduces hallucinations and incorrect answers.
- Control: Administrators define what an agent can access and do. Agents can't access unauthorized data or perform
  actions outside their workflow.

## Human-in-the-loop

Some tasks require human judgment. Agent workflows can integrate human oversight. An agent can pause and wait for your
approval before taking a step. For example, an agent might draft a customer response but wait for a support team member
to review and approve it before sending.

This lets you automate routine parts while maintaining control over decisions.
