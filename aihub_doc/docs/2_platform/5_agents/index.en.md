---
title: Agents
index: 5
---

# Agents

Agents are specialized AI assistants that perform specific tasks through structured workflows. You interact with them
through the chat interface. Unlike open-ended chatbots, agents follow predefined steps to analyze documents, answer
questions, or complete business processes.

The structured approach makes agents predictable, transparent, and auditable.

## What is an agent?

An agent is an AI-powered assistant configured to handle specific tasks using a predefined workflow.

Examples:

- An HR Policy Agent answers questions about company leave policies by consulting the employee handbook.
- A Financial Analyst Agent queries last quarter's sales data from reports.
- A Project Support Agent summarizes status updates from project documents.

Agents combine large language models (LLMs) for understanding natural language with structured processes for reliable
operation.

## Agent "Training"

A common question is whether agents can be "trained" on company data. The AI-Hub does not offer model training or
fine-tuning. Agents access current information through their knowledge bases instead.

When people ask about training an agent, they usually want the agent to know their company's specific information. The
platform accomplishes this through Retrieval-Augmented Generation (RAG). The agent retrieves relevant information from
your knowledge base when answering questions, rather than having that information embedded in the model itself.

Advantages of this approach:

- Information stays current. Update your documents and agents immediately have access to new information.
- No expensive retraining process. Traditional model training requires significant compute resources and time.
- Transparency. You can see which documents the agent used to answer each question.
- Lower risk. Your proprietary data doesn't get embedded into model weights.

Agents "learn" by accessing an up-to-date knowledge base maintained through data pipelines. Add new documents or update
existing ones and agents automatically incorporate that information.

## How agents work

An agent's behavior follows a workflow, a predefined sequence of steps. This differs from general-purpose AI like
ChatGPT.

A typical workflow:

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

## Example

You ask an IT Support Agent: "How do I set up the new VPN on my laptop?"

The agent executes its workflow:

1. Identifies keywords "VPN" and "setup."
2. Searches the internal IT Knowledge Base for matching documents.
3. Finds the guide "VPN_Setup_Guide_v3.pdf."
4. Reads relevant sections.
5. Provides a summary based on that document with a link to the PDF.

The result is a verifiable answer from your company's actual documentation.

## Human-in-the-loop

Some tasks require human judgment. Agent workflows can integrate human oversight. An agent can pause and wait for your
approval before taking a step. For example, an agent might draft a customer response but wait for a support team member
to review and approve it before sending.

This lets you automate routine parts while maintaining control over decisions.
