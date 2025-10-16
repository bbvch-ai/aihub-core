---
title: Model Context Protocol (MCP)
index: 17
---

# Model Context Protocol (MCP) Server

## Concept and Purpose

The Model Context Protocol (MCP) Server exposes Swiss AI-Hub capabilities to AI development assistants and automation
tools through a standardized protocol. Built on FastAPI and integrated directly into the main API service, this
interface enables AI assistants to interact with the platform.

## Core Design Principles

### Standards-Based Integration

MCP is an emerging standard for exposing application functionality to AI assistants in structured, discoverable ways. By
implementing MCP rather than proprietary interfaces, the Swiss AI-Hub ensures compatibility with any MCP-compatible
tool, enables automatic integration as new AI development tools adopt the protocol, and provides type safety through
schema-based interactions that prevent incorrect tool usage.

The standards-based approach future-proofs the platform's development ecosystem: as new AI assistants and automation
tools emerge, they gain immediate access to Swiss AI-Hub capabilities without requiring custom integration work.

### Automatic API Translation

The MCP Server automatically translates the existing FastAPI REST interface into MCP resources, eliminating duplicate
implementation and maintenance burden. OpenAPI specifications generated from code annotations transform into MCP schemas
automatically, ensuring consistency between human-facing REST APIs and AI-facing MCP resources. Changes to platform
capabilities instantly reflect in both interfaces without separate documentation or translation steps.

This architecture maintains a single source of truth: FastAPI route definitions, type annotations, and documentation
strings serve both development communities simultaneously.

## Supported Capabilities

The MCP Server provides AI assistants with read-only access to platform information across four domains:

**Agent Discovery and Inspection**: AI assistants can query available agents, retrieve detailed agent configurations and
capabilities, examine agent execution patterns and performance characteristics, and understand which agents handle which
task types. This enables assistants to recommend appropriate agents for specific problems and generate correct agent
invocation code.

**Conversation Analysis**: Access to conversation threads, message histories, and participant information helps AI
assistants understand application context. Assistants can trace conversation flows, analyze multi-agent collaboration
patterns, and provide debugging guidance based on actual conversation structures rather than assumptions.

**Observability and Diagnostics**: Complete access to event streams, execution logs, and time-series analytics enables
AI-assisted debugging. Assistants can correlate events across components, identify performance bottlenecks, trace errors
to root causes, and suggest optimizations based on actual operational data.

**Process Monitoring**: Visibility into business process definitions, execution states, and completion histories allows
AI assistants to understand application workflows. This supports process optimization, error analysis, and guidance on
implementing new process variants.

## Business Value

### AI-Assisted Operations and Monitoring

AI assistants can query live platform state for operational insights and troubleshooting. Operations teams receive
immediate answers about process execution status, agent performance metrics, event histories, and system health without
manually navigating interfaces or parsing logs. This reduces mean time to resolution for incidents and enables
proactive issue identification through AI-powered anomaly detection across conversation patterns, agent behaviors, and
business process execution.

### Intelligent Knowledge Management

The MCP interface provides AI assistants with access to knowledge bases, document repositories, and RAG indices,
enabling sophisticated knowledge discovery and analysis. Users can ask natural language questions that retrieve and
synthesize information across distributed document collections, identify knowledge gaps, and receive recommendations
for content improvements. This capability is valuable for compliance teams needing to locate specific regulatory
references and researchers exploring large technical document collections.

### Enhanced Development Productivity

Developers benefit from AI assistants with direct platform access for code generation and debugging. Code suggestions
validate against current API schemas rather than generic patterns, debugging conversations include actual platform
state, and test generation uses real agent configurations. Organizations report development productivity improvements
of 30-50% when AI assistants have structured system access. New team members gain productivity faster through
immediate, context-aware guidance that reduces onboarding time and eliminates dependency on documentation searches.

### Process Analysis and Optimization

AI assistants can analyze business process definitions, execution histories, and performance patterns to identify
optimization opportunities. By querying process instances, agent interactions, and completion metrics, assistants
provide actionable insights for workflow improvements, bottleneck identification, and resource allocation. This
capability supports continuous process improvement initiatives and helps organizations maximize return on AI automation
investments.

## Implementation Approach

Built using the FastMCP library, the MCP server generates resources automatically from FastAPI route definitions and
OpenAPI specifications. The server mounts at `/mcp` on the main API service, sharing authentication infrastructure,
database connections, and event system access with REST endpoints. Only read-only operations (GET endpoints) are
exposed, maintaining a secure development interface that allows platform observation without state modification.
Authentication uses the same OAuth2/SAML/LDAP identity providers as REST APIs, with hierarchical permission checks
filtering resources based on user access rights. AI development tools configure MCP connections via `.mcp.json` files in
project repositories, enabling automatic platform access during development sessions. The architecture scales
horizontally with API instances, requires no separate deployment, and adds minimal resource overhead to the existing
service.


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
