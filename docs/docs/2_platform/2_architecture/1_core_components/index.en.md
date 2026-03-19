---
title: Core Components
---

# Core components

The Swiss AI Hub is a complete platform that includes infrastructure for agents, pipelines, and process automation. The
tier model described here is a recommended adoption path, not a set of separate software versions.

Organizations often struggle when they attempt complex automation projects without first building foundational AI
literacy. The tier model provides a structured approach that aligns with successful adoption patterns.

**Tier 1** provides secure LLM access to everyone in the organization. Through direct experience, users learn the
capabilities and limitations of the models, improve their prompt writing skills, and identify tasks in their daily work
where AI could be beneficial.

After a period of use, the friction of switching between work applications and a dedicated AI interface becomes a common
complaint. This leads to **Tier 1+**, which integrates the same AI capabilities directly into tools like Microsoft
Teams, Slack, and Outlook. This reduces workflow disruption and encourages wider adoption.

Users may then find that the generic models lack specific company context. For example, a model asked to evaluate a job
application would be unaware of an organization's internal hiring philosophy. This signals readiness for **Tier 2**.

**Tier 2** introduces specialized agents that are given access to organizational knowledge. An HR agent can be
configured to understand hiring criteria from employee handbooks. A finance agent can be taught the company's chart of
accounts to query financial systems. These agents use an organization's specific data to provide relevant, contextual
responses.

As agent usage grows, repetitive patterns of orchestration emerge. An employee might manually route a document to one
agent for analysis, then to a manager for review, and finally to another agent for a background check. This type of
multi-step, manual routing indicates a need for **Tier 3**.

**Tier 3** automates these patterns as formal processes. The system can be configured to ingest job applications, route
them to an HR agent for screening, request human review only for borderline cases, trigger background checks via
external systems, and notify the appropriate hiring managers. This allows human workers to focus on decision-making and
exception handling.

The platform includes all these capabilities from the start. The tier model addresses the question of when to adopt each
capability based on organizational readiness. The progression allows people time to adjust workflows, develop skills,
and build confidence in the system.

## Tier 1: Foundation for secure AI access

![Tier 1 Architecture](../../../../media/architecture/high_level/tier_1.png)

The primary user entry point is the Open-WebUI web interface, which supports text, document, and voice inputs.

All requests are processed through an API layer that handles authentication, verifies permissions for the requested
model, and logs the interaction for auditing. The request is then routed to the appropriate LLM, such as an OpenAI or
Google Gemini model, based on system configuration.

Responses from the LLM are streamed back to the browser using Server-Sent Events, allowing the user to see the text as
it is generated. This architecture maintains a responsive interface, even for queries that require longer processing
times.

A separate Admin UI, built with Nuxt, provides administrators with visibility into system usage, user management, and
model configuration. It allows them to monitor model use, set cost limits, and review audit logs.

All data, including user queries, LLM responses, conversation history, and system logs, is stored in the platform's
internal database. This ensures data remains within the organization's controlled infrastructure unless external model
access is explicitly configured.

## Tier 1+: Meeting users where they work

![Tier 1+ Architecture](../../../../media/architecture/high_level/tier_1_plus.png)

The limitation of a standalone web interface is the workflow disruption caused by context switching. Tier 1+ resolves
this by extending the platform's capabilities into the applications employees use daily. A user in Microsoft Teams can
summarize a conversation thread directly within the application, and the AI's response appears in the same channel.

::: details Supported Channels
The platform uses the Azure Bot Framework for integrations. Supported channels include:

- Alexa
- Email
- Facebook
- MS Teams
- Outlook
- Skype
- Slack
- Telegram
- WeChat
- Web
- ... and more
:::

Each integration adapts to the interaction patterns of the host tool. For example, an AI response in Slack might be
posted in a thread, while in Outlook it might assist with drafting email replies. The central API layer ensures that all
interactions, regardless of their origin, are subject to the same security, governance, and logging policies.

## Tier 2: From data to contextual intelligence

![Tier 2 Architecture](../../../../media/architecture/high_level/tier_2.png)

Tier 2 introduces capabilities for ingesting and structuring organizational data to provide context to AI agents. The
process starts with information sources like SharePoint document libraries.

A pipeline orchestrates the data processing workflow. It monitors connected sources for new or updated files and
triggers a processing sequence. Documents are parsed to extract not just text but also structural elements like headings
and tables. The content is then divided into semantically meaningful chunks based on topic changes or section breaks.
Each chunk is converted into a vector embedding using a model like Mistral.

::: tip
The pipeline described here is a default configuration. The SDK allows for the creation of custom pipelines to connect
to other sources (databases, APIs, FTP servers), customize document processing, and enrich data.
:::

These embeddings are stored and indexed in a vector database, which serves as the platform's knowledge base. This
enables semantic search, allowing agents to retrieve information based on meaning rather than exact keyword matches. The
system maintains a clear lineage from each embedding back to its source document for traceability and verification.

With a knowledge base in place, the platform can support multiple agents. Default agents might include a document
analyst or a data interpreter. Custom agents can be built with the SDK to handle organization-specific tasks, understand
internal terminology, or apply domain-specific reasoning.

The platform is also open towards the outside world using Model Context Protocol (MCP). Through MCP, agents from other
systems can securely access the platform, including its agents.

## Tier 3: Orchestrating business processes

![Tier 3 Architecture](../../../../media/architecture/high_level/tier_3.png)

Tier 3 introduces a process orchestration engine to automate multi-step workflows that involve AI agents, humans, and
external systems.

A dedicated Process UI allows users to visualize and interact with these workflows. It displays active processes as flow
diagrams, showing the current step, the responsible entity (human, agent or external system), and the subsequent steps.

When a process is triggered, the orchestration engine evaluates the first step. If the step requires document analysis,
the task is delegated to an AI agent. The agent's output is returned to the orchestrator, which then proceeds to the
next step. If a step requires human judgment, a task is created in the relevant user's workspace in the Process UI. The
interface provides the AI's analysis, the source document, and context for the decision. Once the human completes the
task, the process continues.

External systems can be integrated through connectors. Power Automate connections can trigger flows to update SharePoint
lists or send emails. An n8n integration enables communication with UiPath for robotic process automation tasks
involving legacy systems.

::: tip
The process described here is an example. The SDK can be used to create custom processes that connect to various
external and internal systems.
:::

The orchestration engine maintains the state of each process, managing timeouts and handling errors. If an external
system fails to respond, the process can be configured to route the task to a human for manual intervention. The API
layer is extended in this tier to manage conversation contexts that span multiple participants and long durations.
