---
title: Model Context Protocol (MCP)
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
manually navigating interfaces or parsing logs. This reduces mean time to resolution for incidents and enables proactive
issue identification through AI-powered anomaly detection across conversation patterns, agent behaviors, and business
process execution.

### Intelligent Knowledge Management

The MCP interface provides AI assistants with access to knowledge bases, document repositories, and RAG indices,
enabling sophisticated knowledge discovery and analysis. Users can ask natural language questions that retrieve and
synthesize information across distributed document collections, identify knowledge gaps, and receive recommendations for
content improvements. This capability is valuable for compliance teams needing to locate specific regulatory references
and researchers exploring large technical document collections.

### Enhanced Development Productivity

Developers benefit from AI assistants with direct platform access for code generation and debugging. Code suggestions
validate against current API schemas rather than generic patterns, debugging conversations include actual platform
state, and test generation uses real agent configurations. Organizations report development productivity improvements of
30-50% when AI assistants have structured system access. New team members gain productivity faster through immediate,
context-aware guidance that reduces onboarding time and eliminates dependency on documentation searches.

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
