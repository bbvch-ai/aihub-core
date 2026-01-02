---
title: MCP Agent Server
---

# MCP Agent Server

## Concept and Purpose

The Swiss AI-Hub can expose its AI agents as interactive tools through the Model Context Protocol (MCP). This enables
any MCP-compatible AI assistant—whether a desktop application, development tool, or custom automation—to discover and
use your organization's agents.

When a user asks their AI assistant to "check our HR policies about remote work" or "summarize the latest project
updates," the assistant can invoke your organization's agents directly. Your agents—with access to your documents,
policies, and specialized workflows—become tools that any MCP-compatible assistant can use, extending their reach far
beyond the platform's web interface.

## Key Capabilities

### Interactive Agent Conversations

Users can chat with organizational agents through any MCP-compatible assistant. An agent configured to understand your
company policies can answer employee questions. A documentation agent can help users find information across your
knowledge bases. This happens within whatever interface the user prefers—whether a desktop app, IDE, or custom
application.

### Human-in-the-Loop Interaction

When an agent workflow requires human input—such as confirming an action, providing clarification, or choosing between
alternatives—the request appears directly in the user's AI assistant interface. The user provides input, and the agent
continues its work. This preserves the collaborative nature of agent workflows even when agents are invoked remotely.

### Real-Time Progress Visibility

Long-running agent operations provide progress updates as they work. Users see the agent's reasoning steps and partial
outputs in real time, maintaining awareness of what the agent is doing without waiting for final results. This
transparency helps users understand agent behavior and intervene if needed.

### Consistent Access Control

The same permissions that govern agent access through the web interface apply when agents are invoked via MCP. Users
only see and use agents they are authorized to access. All interactions are logged for compliance and auditing purposes.

## Business Value

### Extended Agent Reach

Making agents available through MCP extends their value beyond the platform's native interfaces. Users who prefer other
AI assistants—whether for accessibility, workflow integration, or personal preference—gain access to organizational
agents through tools they already use. This increases adoption and return on investment in agent development.

### Seamless Integration

Organizations can integrate AI-Hub agents into existing workflows and tools. Developers can access code review agents
from their IDE. Business analysts can query data agents from desktop assistants. Automation pipelines can invoke agents
programmatically. The same agents serve all these use cases consistently.

### Consistent AI Experience

Whether users interact with agents through the web interface, team chat integrations, or third-party assistants, they
receive the same capabilities and quality of response. Agents access the same knowledge bases and follow the same
workflows regardless of how they are invoked.

### Reduced Context Switching

Users can access organizational knowledge without switching applications. Instead of navigating to the AI-Hub web
interface, they ask questions directly from whatever tool they are using. This keeps users focused on their primary
tasks while still benefiting from agent capabilities.

## How It Works

The platform exposes agents through the Model Context Protocol (MCP), an emerging standard for connecting AI assistants
to external capabilities. Any MCP-compatible client can discover available agents and invoke them as tools.

From the user's perspective, organizational agents appear alongside other capabilities in their AI assistant. They can
invoke agents through natural conversation, and the assistant handles the details of connecting to the platform,
authenticating, and managing the interaction.

Administrators configure which agents are exposed through MCP and can monitor usage through the platform's standard
observability tools.

## Use Cases

**For developers**: Access code review agents, documentation agents, and architecture guidance directly from your IDE
using tools like Claude Code, Cursor, or VS Code extensions.

**For business users**: Query HR policy agents, project status agents, or document analysis agents from desktop AI
assistants like Claude Desktop.

**For automation**: Integrate agents into workflows and pipelines using any MCP-compatible automation framework.

**For custom applications**: Build applications that leverage organizational agents through the standard MCP interface.

## Getting Started

To use AI-Hub agents from an MCP-compatible client, you need:

1. An AI assistant that supports MCP (such as Claude Desktop, Claude Code, Cursor, or compatible applications)
2. Access credentials for the Swiss AI-Hub platform
3. Permission to access the agents you want to use

Your MCP client's configuration points to your organization's Swiss AI-Hub instance. Once configured, agents appear
automatically as available tools in your assistant.

## Related

- [MCP Protocol Overview](../index.en.md)
- [Agents](../../5_agents/index.en.md)
- [Access Management](../../11_access_management/index.en.md)
