---
title: Agents
---

# Agents

Agents are specialized AI assistants that perform specific tasks through structured workflows. Unlike open-ended
chatbots, agents follow predefined steps to analyze documents, answer questions, or complete business processes.

Agents can be interactive (responding to user questions via chat) or autonomous (executing tasks automatically on a
schedule or triggered by events). The structured workflow approach makes agents predictable, transparent, and auditable
regardless of how they operate. Where a task calls for it, the Universal Agent lets the model choose among tools you
have enabled, still inside limits, permissions and approvals you set.

## What is an agent?

An agent is an AI-powered assistant configured to handle specific tasks using a predefined workflow.

Examples:

- An HR Policy Agent answers employee questions about leave policies by consulting the employee handbook (interactive,
  chat-based).
- A Compliance Monitoring Agent reviews documents on a schedule, flagging potential policy violations (autonomous,
  scheduled).

Agents combine large language models (LLMs) for understanding natural language with structured processes for reliable
operation.

## The standard blueprint set

The pages that follow document every agent blueprint the platform ships. A tenant does not get all of them.

Three are granted to a new tenant by default:

- **Instructed Assistant** — follows plain-text instructions you write
- **Teachable Assistant** — learns the shape of the answer you want from examples
- **Document Intelligence Assistant** — answers from your knowledge bases and cites its sources

The Universal Agent is the one profile an admin configures once for open-ended work: the model decides per message
whether to search knowledge, read the user's attached files, recall memory or use another enabled tool.

The rest are documented here because they are built, supported and ready to run — but a tenant only sees one after a
sysadmin grants it. That keeps a new tenant's catalog small enough to choose from, without taking anything away from a
tenant that already relies on an agent outside the set. Granting one takes effect immediately, with no redeploy; see
[Access control](../16_multi_tenancy/4_access_control/).

## What every chat agent can do

The conversational blueprints built on the shared capabilities (Instructed, Teachable, Document Intelligence, Company
Knowledge, MCP Tool and Universal) share the same behaviour in the conversation:

- **Attached files.** Files attached in the chat are read by the agent itself and listed as sources. A long file is cut
  down to the sections that matter for the question, and the answer says so.
- **Knowledge references.** Typing `#` in Open WebUI points the agent at one of the company's knowledge collections,
  limited to what the user may read.
- **Inline citations.** Statements link to the document they came from, as numbered chips in the answer.
- **Memory.** What the agent remembers about the user and the organization joins the model's instructions.
- **Chat toggles.** A chat toggle is a request to the agent, which runs it as traced, cost-attributed steps. An agent
  shows a toggle only if it can serve it; today that is Code Interpreter and My Files, on the Universal Agent.
- **Refusals instead of errors.** A message larger than the model's context window, or a request outside a Teachable
  Assistant's remit, is answered with a short explanation in the chat rather than an error.

How these show up in Open WebUI is described under
[Integration architecture](../10_chat_ui/11_integration_architecture/); the settings are in
[Blueprints & Profiles](2_blueprints_and_profiles/#shared-chat-settings).

## Tools the model chooses

A fixed workflow is the default, because it is predictable. Some jobs cannot be written as a fixed sequence, so an agent
can also hand the model a set of tools and let it decide, per message, which to use, run them, and decide again until it
can answer. This is the tool loop, and it is how the Universal Agent works.

The loop stays inside controls an admin sets per profile:

- **Only what is offered runs.** A tool is offered only if the profile enables it, the user's access allows it and, for
  Code Interpreter or My Files, the chat toggle is on. A call to anything else is refused.
- **Approvals.** A tool can ask the user to confirm first: on every call, once per answer or once per conversation. A
  declined tool is not requested again for that answer.
- **Limits.** The profile caps the number of decisions and tool calls. At the cap the model answers with what it has and
  the chat says it stopped early.
- **Transparency.** Every call and result appears in the chat and in the event history, so the path to an answer can be
  audited like any workflow.

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

## Connecting to external tools

Agents are not limited to reading from knowledge bases — they can also take actions in other systems. Through the Model
Context Protocol (MCP), an agent connects to an external tool server and uses the tools it exposes: creating a ticket,
sending a message, or looking up a record in another application.

A connection can authenticate as the requesting user, so an external action is attributed to that person rather than to
a shared service account. The other system's audit trail and per-user permissions stay correct.
