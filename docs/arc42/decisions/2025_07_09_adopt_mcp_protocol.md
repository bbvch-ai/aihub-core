# Adopt MCP (Model Context Protocol) for AI-Assisted Development

## Context

The Swiss AI Hub development team increasingly relies on AI coding assistants (Claude Code, Gemini CLI, OpenAI Codex,
JetBrains Junie) for writing and debugging code. These tools needed better access to the development environment to
provide more effective assistance, including:

- Real-time observation of running services and their state
- Direct access to development databases for debugging
- Ability to interact with Swiss AI Hub APIs for testing and validation
- Integration with observability tools for tracing and monitoring

Previously, AI coding assistants worked in isolation with limited context about the running development environment.
This reduced their effectiveness in debugging complex issues and understanding system behavior.

Additionally, we wanted to make our Swiss AI Hub API more accessible to third-party AI tools and potential integrations
while maintaining security boundaries.

## Decision Drivers

- **Enhanced AI Assistant Capabilities**: Enable coding assistants to observe and interact with the development
  environment
- **Improved Debugging Experience**: Allow AI tools to access runtime data, logs, and system state
- **Standardized Tool Integration**: Use emerging industry standards for AI tool integration
- **Developer Productivity**: Reduce context switching between AI assistants and development tools
- **API Accessibility**: Make Swiss AI Hub API available to third-party AI tools through standardized protocols
- **Security**: Maintain controlled access to sensitive operations and data

## Decision

We will adopt a two-pronged MCP (Model Context Protocol) integration strategy:

### Decision 1: MCP Client Integration for Development Tools

Configure AI coding assistants to access development tools through MCP servers using `.mcp.json`:

1. **Phoenix MCP Server**: For AI observability and tracing (`@arizeai/phoenix-mcp`)
2. **MongoDB MCP Server**: For database access and monitoring (`mongodb/mongodb-mcp-server`)
3. **Swiss AI Hub API MCP Server**: For internal API integration (`http://localhost:8000/mcp`)

### Decision 2: Swiss AI Hub API as MCP Server

Implement MCP server capabilities directly in the Swiss AI Hub API to expose functionality to AI coding assistants:

1. **Read-Only Access**: Currently expose only GET endpoints through MCP for security
2. **Standardized Interface**: Provide AI tools with structured access to API functionality
3. **Third-Party Integration**: Enable external AI tools to interact with Swiss AI Hub through MCP protocol

## Consequences

### Positive

- **Enhanced AI Assistance**: Coding assistants can now observe running services, access databases, and interact with
  APIs
- **Improved Debugging**: AI tools can analyze real-time system state and provide context-aware debugging help
- **Standardized Integration**: All AI tool integrations follow the same MCP protocol
- **Developer Productivity**: Reduced context switching between AI assistants and development tools
- **API Accessibility**: Third-party AI tools can integrate with Swiss AI Hub through standardized MCP interface
- **Future-Proof**: Leverages emerging industry standard for AI tool integration

### Negative

- **Additional Complexity**: Introduces new protocol and configuration management requirements
- **Docker Dependency**: Requires Docker for external MCP server management
- **Security Considerations**: Need to carefully manage access levels and exposed endpoints
- **Learning Curve**: Team needs to understand MCP protocol and server management
- **Version Management**: Additional dependency on MCP server versions and compatibility

### Neutral

- **Configuration Management**: `.mcp.json` becomes critical for development environment setup
- **Documentation**: Need for comprehensive documentation of MCP integration and usage
- **Monitoring**: MCP servers and integration points require monitoring and health checks
- **Security Policy**: Current read-only restriction may need revision as requirements evolve
