---
title: MCP (Model Context Protocol)
index: 1
---

# MCP Integration :tada: :100:

::: info **TL;DR - What is MCP Integration?**
The AI-Hub acts as an **MCP (Model Context Protocol) server**, enabling external AI coding assistants and AI-powered
tools to seamlessly interact with your AI-Hub instance through a standardized protocol. This means your favorite AI
tools can directly access AI-Hub APIs, observe system state, and provide context-aware assistance without manual data
export or complex integrations.
:::

## What is MCP and How Does AI-Hub Support It? :brain:

The **Model Context Protocol (MCP)** is an emerging industry standard that allows AI coding assistants and AI-powered
tools to communicate with external services and databases through a unified interface. Think of it as a universal
translator that lets your AI tools "speak" to your business systems.

The AI-Hub **exposes its API functionality through MCP**, making it possible for tools like:

- **Claude Code** - Anthropic's AI coding assistant
- **Gemini CLI** - Google's AI development tool
- **Cursor** - AI-powered code editor
- **JetBrains AI** - IntelliJ's AI assistant
- **Custom AI Tools** - Any tool that supports MCP protocol

to directly interact with your AI-Hub instance without requiring manual API calls or complex setup procedures.

## Why This is a Game-Changer for Your AI Strategy :trophy:

This integration represents a **paradigm shift** in how AI tools can work with your enterprise systems:

**🔗 Seamless Integration**: Your AI coding assistants can now access your AI-Hub data, agents, and processes directly.
No more copying and pasting data between systems or manually feeding context to AI tools.

**🧠 Enhanced AI Capabilities**: AI tools can provide suggestions and assistance based on real-time data from your
AI-Hub, including:

- Current agent configurations and workflows
- Process execution history and patterns
- System health and performance metrics
- Knowledge base contents and retrieval results

**🛡️ Controlled Access**: The MCP server implementation provides **read-only access** to ensure security while
maximizing utility. Your AI tools can observe and analyze without risk of unintended modifications.

**⚡ Developer Productivity**: Developers can use AI assistants that understand the full context of your AI-Hub setup,
leading to more accurate code suggestions, better debugging assistance, and faster development cycles.

**🌐 Ecosystem Integration**: This opens the door for a rich ecosystem of AI-powered tools that can work together with
your AI-Hub, creating a truly integrated AI development environment.

::: details **Setting Up AI-Hub as an MCP Server**
## Configuration Requirements

To enable MCP server functionality in your AI-Hub:

1. **Enable MCP Endpoint**: The AI-Hub automatically exposes an MCP endpoint at `/mcp` when running
2. **Configure AI Tools**: Set up your AI coding assistants to connect to your AI-Hub instance

## Example Configuration for Claude Code

Create or update your `.mcp.json` configuration file:

```json
{
  "mcpServers": {
    "aihub": {
      "type": "http",
      "url": "http://your-aihub-instance:8000/mcp",
      "description": "AI-Hub MCP Server Integration"
    }
  }
}
```

## Example Configuration for Other AI Tools

Most MCP-compatible AI tools use similar configuration patterns:

```json
{
  "mcp_servers": {
    "aihub": {
      "endpoint": "http://your-aihub-instance:8000/mcp",
      "type": "http",
      "read_only": true
    }
  }
}
```

## Available MCP Capabilities

The AI-Hub MCP server currently provides:

- **Agent Information**: Access to agent configurations and capabilities
- **Process Monitoring**: Real-time process execution status and history
- **System Health**: Performance metrics and system status
- **Knowledge Base**: Read-only access to knowledge base contents
- **API Documentation**: Interactive API schema and endpoint information

## Security Considerations

- **Read-Only Access**: Current implementation provides only read access to ensure system security
- **Network Security**: Configure appropriate firewall rules and network access controls
- **Authentication**: Ensure proper authentication is configured for your AI-Hub instance
- **Monitoring**: Monitor MCP endpoint usage through standard AI-Hub logging and observability tools
:::

## Getting Started

To begin using MCP integration with your AI-Hub:

1. **Ensure Your AI-Hub is Running**: The MCP server is automatically available at `/mcp` endpoint
2. **Configure Your AI Tools**: Add your AI-Hub instance to your AI tool's MCP configuration
3. **Start Collaborating**: Your AI assistants can access AI-Hub context and provide enhanced assistance

For advanced configuration options and troubleshooting, refer to your AI tool's MCP documentation and the AI-Hub API
reference.
