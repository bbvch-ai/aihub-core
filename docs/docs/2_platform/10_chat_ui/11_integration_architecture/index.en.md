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
   memberships synced based on email matching between both systems
2. **Workspace models**: For each online agent, AI-Hub creates a workspace model that delegates to the corresponding
   pipe function
3. **Access grants**: For each workspace model, AI-Hub computes which groups have access using the platform's permission
   system (with tenant ceiling enforcement), then sets `access_control` on the model

The provisioner runs at API startup, when an agent instance is created, renamed, or deleted (reflected immediately in
the model picker), when the set of online agents changes (the periodic 60-second reconciler), when users switch tenants,
when new users sign up via an Open WebUI webhook, and when roles, tenants, or user-role assignments are modified. All
changes propagate immediately.

**Reliability in multi-replica deployments:**

- **Debouncing**: Rapid access entity mutations (e.g. bulk user assignments) are collapsed into a single sync call using
  a 2-second quiet window
- **Distributed locking**: Each sync operation acquires a non-blocking Redis lock, so concurrent API replicas skip
  rather than race
- **Change detection**: The discovery service stores a SHA-256 hash of the online agent set in Redis, surviving restarts
  and working correctly across replicas

`BYPASS_MODEL_ACCESS_CONTROL=False` must be set on Open WebUI to enforce these access controls.

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
