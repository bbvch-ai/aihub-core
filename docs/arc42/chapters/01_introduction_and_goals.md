# Introduction and goals

## Requirements overview

The Swiss AI Hub is a self-hosted, open-source platform that gives organizations a complete AI infrastructure they own
and control. It runs on-premise or in a private cloud. The platform handles authentication, multi-tenancy, LLM routing,
vector storage, document parsing, data pipelines, process orchestration, and observability so that developers building
agents and workflows do not have to build or integrate this infrastructure themselves.

### The problem

Organizations in Switzerland that want to use generative AI in production face three interrelated barriers.

The first is legal exposure. Professionals bound by Art. 321 StGB (lawyers, doctors, fiduciaries) and public
administrations subject to the Swiss Data Protection Act (nDSG) cannot send client data to US-headquartered cloud
providers without confronting the CLOUD Act. Standard "region Switzerland" hosting from hyperscalers does not fully
resolve this, because operational access (support, debugging) often originates outside Switzerland.

The second is operational complexity. Running an LLM stack in production requires a vector database, an embedding
pipeline, a document parser, a message broker, an LLM gateway, an authentication layer, observability tooling, and a way
to coordinate all of it. Most IT departments do not have the staff or the specialized knowledge to assemble and maintain
this.

The third is vendor lock-in. Committing to a single cloud AI provider (Azure OpenAI, Google Vertex, AWS Bedrock) ties an
organization to that provider's pricing, roadmap, and ecosystem. If the provider raises prices or discontinues a model,
switching is expensive.

### The solution

The Swiss AI Hub addresses these barriers by packaging the full AI infrastructure stack as a single deployable
open-source product. Organizations get a working system out of the box and retain the ability to inspect, modify, and
self-host every component. See [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) for the
per-package license breakdown.

The platform is structured around a tier model that reflects how organizations typically adopt AI:

**Tier 1 (Secure AI access):** A web-based chat interface provides LLM access through a unified gateway that routes to
cloud models (Swiss LLM Cloud) or locally hosted models (vLLM on GPU). An admin UI handles user management, model
configuration, and usage monitoring. All queries and responses stay within the organization's infrastructure unless
external model access is explicitly configured.

**Tier 1+ (Channel integrations):** The platform extends into collaboration tools employees already use, including
Microsoft Teams, Slack, and Outlook. The same security policies and governance controls apply across all channels.

**Tier 2 (Contextual intelligence):** Dagster-orchestrated data pipelines ingest documents from sources like SharePoint
and OneDrive, parse them with MinerU (OCR and structural extraction), chunk them semantically, generate vector
embeddings, and store them in the vector database. Specialized agents built with the SDK can query this organizational
knowledge base to give contextually grounded answers. The Swiss AI Agent Protocol, an event-driven communication
standard over a message broker, governs how agents, the API gateway, and frontends exchange information.

**Tier 3 (Process orchestration):** A process engine coordinates multi-step workflows that involve AI agents, human
decision-makers, and external systems (Power Automate, n8n, UiPath). The engine maintains process state, handles
timeouts, routes tasks to the appropriate participant, and provides a visual process cockpit.

### Development and licensing

The platform is developed by bbv Software Services, a Swiss software engineering company. The platform is fully
open-source under a dual-license model: Apache 2.0 for the runtime and SDK, and AGPL-3.0 for the web UI, the
multi-tenant administration plane, and backup orchestration. The full per-package breakdown lives in
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

### Key functional requirements

| Requirement                     | Description                                                                                                                                                                 |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Self-hosted deployment          | The entire platform runs on a single server or cluster owned by the customer, with no mandatory external dependencies. Air-gapped operation with local models is supported. |
| Model-agnostic LLM routing      | Provides a unified OpenAI-compatible API to any configured model. Switching providers requires a configuration change, not a code change.                                   |
| Document ingestion pipeline     | Automated ingestion from cloud storage (SharePoint, OneDrive, S3, Google Drive, SFTP) through parsing, chunking, embedding, and indexing.                                   |
| Agent SDK                       | A Python SDK for building workflow-based agents with step decorators, event-driven dispatch, and automatic observability integration.                                       |
| Process orchestration           | Multi-step workflows that delegate tasks to agents, humans, or external programs, with state persistence and error handling.                                                |
| Multi-channel bot integration   | Agents accessible through Microsoft Teams, Slack, and web chat, using the same backend logic and security policies.                                                         |
| PII detection and anonymization | Intercepts requests before they reach external LLM providers, detecting and redacting personally identifiable information.                                                  |
| Per-user cost tracking          | Track token consumption and cost per user, per agent, and per trace. Token budgets can be set per user.                                                                     |
| Full audit trail                | Every agent step, LLM call, retrieval operation, and user interaction is logged as an immutable event in the NATS event stream and persisted to Storage.                    |
| Role-based access control       | Hierarchical permissions with wildcard-capable permission strings scoped to specific agents and resources.                                                                  |
| Internationalization            | The platform supports German, English, French, and Italian across all user-facing interfaces, agent responses, and administrative tools.                                    |

## Quality goals

The following quality goals shape the architecture. They are ordered by priority as determined by the primary
stakeholders (regulated Swiss organizations and the platform development team).

| Priority | Quality goal                                    | Scenario                                                                                                                                                                                                                                                                                                                                                                                                              |
| -------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1        | **Data sovereignty**                            | A cantonal administration deploys the platform on its own servers. No data leaves the canton's network. When external LLM access is configured, PII is redacted before the request leaves the platform. The organization can verify this by inspecting the open-source code and the network isolation configuration.                                                                                                  |
| 2        | **Transparency and auditability**               | A compliance officer at a law firm reviews how an AI agent arrived at a recommendation. She opens the thread in the admin UI and sees every step the agent executed, every LLM call it made (including the full prompt and response), every document it retrieved, and the cost of each operation. The agent's workflow is a deterministic sequence of named steps, not an opaque chain-of-thought.                   |
| 3        | **Vendor independence**                         | An organization currently using Azure OpenAI GPT-4o decides to switch to a locally hosted Llama model after evaluating costs. An administrator changes the model assignment in Swiss AI Hub's configuration. No agent code changes. No data migration. The switch takes effect on the next request.                                                                                                                   |
| 4        | **Operational self-sufficiency**                | A mid-sized fiduciary firm with a two-person IT team deploys the platform using the provided Docker Compose configuration. The system starts with `docker compose up`, runs the full stack on a single server, and is usable within an hour. Updates arrive as new Docker image tags. The firm does not need Kubernetes expertise, cloud engineering skills, or ongoing vendor involvement to keep it running.        |
| 5        | **Extensibility without platform modification** | A developer builds a new agent that monitors regulatory changes and notifies affected departments. She writes a Python class with step-decorated methods, defines its configuration schema, and deploys it as a Docker container. The platform discovers the agent automatically via the message broker, registers its API endpoints, and begins streaming its events to the frontend. No platform code was modified. |

## Stakeholders

| Role                                                           | Expectations                                                                                                                                                                                                                                                                                            |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Platform operators** (IT departments, system administrators) | Straightforward deployment (Docker Compose or Kubernetes). Clear operational documentation. Manageable resource requirements. Automated updates. Monitoring and alerting out of the box. No vendor dependency for day-to-day operations.                                                                |
| **End users** (employees in client organizations)              | A chat interface that works like the consumer AI tools they already know. Access through Teams or Slack without switching applications. Fast, relevant answers grounded in company data. No need to understand the underlying infrastructure.                                                           |
| **Agent developers** (software engineers building on the SDK)  | A well-documented SDK with clear abstractions. Working examples and playground projects. Type-safe Python with modern syntax. Automatic integration with platform capabilities (tracing, cost tracking, event streaming) without boilerplate. The ability to test agents locally before deploying them. |
| **Compliance and security officers**                           | Full audit trail for every AI interaction. Verifiable data residency (no data leaves defined boundaries). PII detection before external API calls. Role-based access control integrated with existing identity providers. Open-source code they can inspect or have audited by a third party.           |
| **Organization leadership** (CIOs, CDOs, managing partners)    | Predictable, transparent costs (per-user and per-token tracking). No vendor lock-in (open-source, model-agnostic). Compliance with Swiss data protection law and professional secrecy obligations. A platform that scales from a pilot project to organization-wide deployment without re-architecture. |
| **Platform developer**                                         | A codebase that supports rapid iteration (monorepo, shared libraries, automated testing). A clear boundary between platform and SDK that allows independent release cycles. Open-source distribution that builds trust in regulated markets.                                                            |
| **Integration partners** (IT service providers)                | A platform they can deploy and operate for their own clients without deep AI expertise. Clear documentation and tooling. Clear licensing terms.                                                                                                                                                         |
| **Open-source community**                                      | Permissive licensing (Apache 2.0) for the platform runtime + SDK (other components AGPL-3.0 — see `LICENSES.md`). Transparent development practices (public repository, issue tracker, CI).                                                                                                             |
