---
title: Integration architecture
---

# Integration architecture

The Swiss AI Hub embeds **Open WebUI** directly in its interface rather than linking to a separate deployment. This
maintains a unified user experience while keeping the open-source component separate from the platform infrastructure.

## How embedding works

The platform uses an iframe to render the complete Open WebUI interface within the suite's service area. Users see a
single integrated application. The architecture maintains separation between the open-source component and platform
infrastructure.

When users navigate to the chat service, Open WebUI occupies the full service area. The suite navigation sidebar stays
accessible so users can switch to other services without losing their chat context.

The embedding preserves Open WebUI's complete interface and feature set. Keyboard shortcuts, drag-and-drop file
handling, and conversation management work as they do in the standalone application. The embedded interface adapts to
different screen sizes - desktop displays provide expanded workspace while mobile devices maintain functional access.

## Communication between components

The iframe and suite platform communicate using the browser-standard PostMessage API. This provides secure cross-origin
messaging while maintaining security boundaries between components.

The chat interface and platform exchange structured messages for user interactions, navigation requests, and state
synchronization. When users request platform capabilities within the chat interface - like viewing knowledge sources or
execution traces - the chat posts messages that trigger navigation and data display.

Messages follow defined contracts that specify intent, parameters, and behaviors. Types include source display requests,
tracing visibility requests, and context synchronization.

If message passing fails or the platform can't fulfill requests, users receive feedback rather than silent failures.

## Authentication and security

The platform and Open WebUI share authentication through OAuth. Users authenticate once to the Swiss AI Hub suite, and
this propagates to the embedded instance.

The platform enforces permission boundaries for AI models, knowledge bases, and agent capabilities. Users can't access
through the chat interface what they can't access through other services.

Sessions stay synchronized between platform and chat. Logging out from the suite terminates the chat session. Timeouts
and renewals coordinate across both components.

Communication uses secure channels with encryption and validation. The iframe integration includes security headers and
content security policies to prevent cross-site scripting.

## Model visibility and access control

The platform manages which agents each user can see in Open WebUI. Since Open WebUI's pipe discovery runs without user
context, AI-Hub pushes permission state into Open WebUI rather than filtering at the pipe level.

**How it works:**

1. **Groups**: AI-Hub creates Open WebUI groups for each tenant-role combination (named `aihub:{tenant}:{role}`), with
   memberships synced based on email matching between both systems. A user who holds a role in their active tenant but
   has not opened the chat yet gets their Open WebUI account created over SCIM in the same sync, so their models are
   there on their first chat visit; the chat login then links to that account
2. **Workspace models**: For each online agent, AI-Hub creates a workspace model that delegates to the corresponding
   pipe function
3. **Access grants**: For each workspace model, AI-Hub computes which groups have access using the platform's permission
   system (with tenant ceiling enforcement), then sets `access_control` on the model

The provisioner runs at API startup, when an agent instance is created, renamed, or deleted (reflected immediately in
the model picker), when the set of online agents changes (the periodic 60-second reconciler), when users switch tenants,
and when roles, tenants, or user-role assignments are modified. All changes propagate immediately.

**Reliability in multi-replica deployments:**

- **Debouncing**: Rapid access entity mutations (e.g. bulk user assignments) are collapsed into a single sync call using
  a 2-second quiet window
- **Distributed locking**: Each sync operation acquires a Redis lock, so concurrent API replicas never race. Model syncs
  skip while another holds the lock; access syncs wait for it, so a role change made during a running sync is still
  applied
- **Change detection**: The discovery service stores a SHA-256 hash of the online agent set in Redis, surviving restarts
  and working correctly across replicas

`BYPASS_MODEL_ACCESS_CONTROL=False` must be set on Open WebUI to enforce these access controls.

## Chat toggles for agents

For an agent, Open WebUI's Web Search, Code Interpreter and Image Generation toggles are a request to the agent, not
something Open WebUI runs itself. The agent decides what to do and runs it as a traced, cost-attributed step.

- **Which toggles appear**: an agent shows a toggle only when its blueprint supports that feature. Support comes from
  the capabilities the blueprint installs, and the provisioner writes it onto the agent's model in Open WebUI. Plain LLM
  models keep all of Open WebUI's own toggles.
- **What happens when a toggle is on**: an AI-Hub filter attached to agent models takes the toggles out of the request
  before Open WebUI acts on them, and hands the supported ones to the agent. Open WebUI runs none of its own search,
  image generation or code interpreter for agents, and does not change the prompt the agent receives.
- **Stale toggles**: Open WebUI sends a toggle's state even after the user switched to a model that hides it. The filter
  forwards only features the selected agent supports, and the agent ignores any other feature an API caller sends.
- **Memory**: Open WebUI's own memory injection is off for agents, which recall user and organization memory themselves.

## Attached files in agent chats

When a user attaches a file in an agent chat, the agent reads it; Open WebUI only stores the upload.

- **Open WebUI does not process it for agents**: file retrieval and injection (the File Context capability) are off on
  agent models, and Open WebUI no longer embeds uploads, since it runs in full-context mode and never read the
  embeddings. Plain LLM models keep Open WebUI's own file handling.
- **The agent reads the whole document**: the pipe copies each file into the agent's upload bucket, once per agent, and
  the agent parses it with the platform's document extraction (MinerU for PDFs and images, openpyxl for XLSX, MarkItDown
  for other Office files), cached by content so each file is converted once. The
  full text goes into the model's context, trimmed to fit, and the user is told when only part of a file fit.
- **Later turns and edited messages**: every file of the current message branch is sent on every turn, so a file
  attached earlier keeps answering later questions, and an edited or regenerated message sees only its branch's files.
- **Sources**: each file the model read is listed as a source that opens the original upload and shows the text the
  model received. A file that cannot be read is reported instead of silently skipped.
- **Temporary chats**: Open WebUI stores nothing and sends the text it extracted in the browser; the agent reads that
  text like any other attachment.

## Inline citations

Agent answers link each statement to the source it came from, the way Open WebUI does for its own retrieval.

- **What the model cites**: every knowledge document and attached file in the prompt carries a short id, and the model
  cites it as `[s3f9a1c]`. The ids stay stable across turns and retrievals because they derive from the document itself,
  not from its position in a list.
- **What Open WebUI shows**: Open WebUI links only numbers, counted over the sources of the message. The pipe lists each
  document once, in the order the agent handed them over, and rewrites every cited id into that document's number while
  the answer streams. An id the agent never listed as a source is dropped instead of shown as a dead marker.
- **Which documents are listed**: the documents the model actually read, after reranking and including documents carried
  over from an earlier turn, not every search hit. Each is labelled with its title or file name, and links to the
  document when its source provides a reference URL.

## Referencing our knowledge with `#`

In an agent chat, typing `#` lists the knowledge collections the user may read, named "Database / Collection", next to
Open WebUI's own knowledge bases. Open WebUI stays a picker: the entries hold no content and it runs no retrieval on
them. The agent searches the referenced collections itself, with the embedding model each database was indexed with, and
cites what it finds like any other source.

- **Who sees what**: an entry is readable by the role groups that may browse the collection, so the list matches the
  knowledge area. The agent checks the asking user's access again before it searches, so a reference never reaches a
  collection the user may not read. A collection that is unreadable or deleted is named to the model, which tells the
  user it could not use it.
- **Kept in sync automatically**: entries are created when a collection appears, a few seconds after a collection or
  database changes, and on every discovery cycle for collections a pipeline creates. A collection that is gone loses its
  entry.
- **On top of the agent's own retrieval**: a Document Intelligence Assistant searches its configured sources and the
  referenced collections; an Instructed Assistant answers from the referenced collections alone.

## Tool calls in agent chats

When an agent lets the model choose its tools (see [Agents overview](../../5_agents/#tools-the-model-chooses)), every
call shows in Open WebUI as one of its own collapsible tool blocks, under a readable label such as "Search our
knowledge", with the result inside, as the model received it. Text the model streamed before a call moves into a
collapsed thought, so the answer starts where the work ends. While the agent gathers, the chat shows what it is doing,
including when a long conversation is being condensed to fit the model.

- **Approvals**: a tool an admin marked for approval asks a yes/no confirmation in the chat that names the tool and what
  the call does. A declined tool is not requested again for that answer, and the model answers without it.
- **Toggles decide what is offered**: a tool that needs Code Interpreter or My Files is offered only while that toggle
  is on. See [Chat toggles for agents](#chat-toggles-for-agents).
- **Limits**: a profile caps how often the model may decide and how many calls it may make. At the cap the model answers
  with what it has and says it stopped early.
- **Sources**: a knowledge search the model chose produces the same citation chips as a `#` reference.

## Chat disclaimer

A short note below the chat input, such as "AI can make mistakes. Please verify answers.", is managed per tenant by
system administrators in the SysAdmin UI under **Tenants → Overview**. It can be set in German, English, French and
Italian, up to 100 characters each, and follows the user's language; a tenant without custom text shows the translated
default. Open WebUI has no setting for this, so the platform shows the text through a small script Open WebUI loads. The
deployment details are in `infra/deployment/openwebui-disclaimer.md`.

## Configuration and deployment

Open WebUI deploys as an independent Docker container within the platform. This provides isolation while managing the
lifecycle - starting, stopping, and updating - alongside other services.

The chat container accesses platform infrastructure like databases, object storage, and message queues through standard
patterns. Chat data persists with other platform data, supporting unified backup and data governance.

Configuration parameters propagate through environment variables and configuration files. Authentication endpoints,
model access URLs, and feature toggles stay consistent across development, testing, and production environments.

The platform tests new Open WebUI releases in isolated environments before production deployment. This protects against
breaking changes while providing access to improvements.

## Extension points

The integration preserves Open WebUI's core functionality but adds platform-specific enhancements.

The PostMessage protocol extends chat capabilities beyond native features. Custom message types trigger platform
workflows or data displays without modifying the open-source codebase.

The platform can overlay UI elements like notification badges or quick-action buttons without modifying Open WebUI.
These enhance functionality while keeping updates simple.

API calls between the chat interface and backend services can be intercepted to add context, enrich responses, or
enforce governance.

Platform theme settings apply through CSS customization rather than source code modification. This maintains visual
consistency with the suite's design.

## Monitoring

The platform monitors Open WebUI container health through standard endpoints. Service failures trigger automatic
recovery or administrator alerts.

Usage metrics - conversation counts, response times, error rates - flow to platform observability systems.
Administrators monitor chat service performance alongside other metrics.

Chat logs aggregate with platform logs in unified infrastructure. This supports troubleshooting across multiple
components.

Resource consumption monitoring - CPU, memory, network - supports capacity planning as user populations and conversation
volumes grow.

## What this approach provides

Open WebUI and the platform evolve independently. New releases integrate through standard processes without platform
code changes. Platform enhancements don't require chat interface modifications.

Responsibilities stay clear. Open WebUI handles chat interactions. The platform provides authentication, authorization,
knowledge management, and agent orchestration. This separation simplifies testing and maintenance.

Embedding rather than forking preserves open-source advantages. The platform receives community contributions, security
patches, and features without maintaining a custom variant.

Organizations can replace Open WebUI with alternative chat interfaces using the same embedding and messaging patterns.
This avoids lock-in to specific chat technology.
