---
title: "Why our SDK"
---
[@mhoegger](https://github.com/mhoegger)
[WIP]

# Why our SDK

Building AI agents looks deceptively simple. Frameworks like LangChain, LlamaIndex, and Semantic Kernel make it easy to connect LLMs, chain operations, and create working prototypes. You can have an impressive demo running in hours.

But these frameworks solve only one piece of the puzzle: orchestrating LLM calls. They handle prompt templates, response parsing, and basic tool integration well. For everything else—security, access control, audit trails, cost management, scalability—you're on your own.

## The framework limitation

Popular AI frameworks focus on communication and orchestration between LLMs and tools. This covers maybe 20% of what production AI systems need. The remaining 80% becomes your responsibility:

**Security and access management** because agents need to know who can access what data, which actions are permitted, and how to enforce these policies across different users and teams.

**Audit trails and compliance** because organizations need to track every agent decision, data access, and action taken for regulatory compliance and operational debugging.

**Cost tracking and governance** because LLM usage across multiple agents, users, and models needs monitoring, budgeting, and appropriate limits.

**Integration with existing systems** because agents must work with corporate databases, APIs, authentication systems, and business processes that already exist.

**Observability and monitoring** because production systems need comprehensive logging, tracing, error handling, and performance metrics.

**Deployment and scaling infrastructure** because agents need to run reliably in production with proper resource management and failover capabilities.

Each of these areas requires specialized expertise. Building with frameworks alone means your team needs security engineers, compliance specialists, DevOps experts, and infrastructure architects. The simple agent becomes a complex systems integration project.

## The no-code trade-off

Low-code and no-code AI platforms solve the infrastructure problem but eliminate flexibility. They provide security, monitoring, and deployment out of the box, but you're limited to their predefined templates and workflows.

This works for standard use cases but breaks down when you need:
- Custom data processing logic
- Integration with proprietary systems  
- Specific workflow patterns that match your business processes
- Advanced error handling and recovery mechanisms
- Complex multi-step processes with conditional logic

You can have infrastructure or flexibility, but not both.

## Where our SDK fits

The Swiss AI Hub SDK bridges this gap. You get the infrastructure capabilities that frameworks lack without sacrificing the flexibility that no-code platforms remove.

Built on the Swiss AI Hub platform, the SDK provides immediate access to enterprise-grade infrastructure:

**Authentication and authorization** are handled automatically. Agents inherit the platform's SSO integration, role-based access controls, and user management without custom security code.

**Comprehensive audit trails** are built in. Every agent action, data access, and decision point is automatically logged with full context for compliance and debugging.

**Cost management is unified** across all agents. LLM usage flows through the platform's gateway, providing detailed tracking, budget controls, and usage analytics.

**Production deployment is standardized.** Agents containerize automatically, integrate with monitoring systems, and follow established operational patterns.

**Observability comes free.** Every workflow step is traced, every error is logged, and performance metrics are collected without instrumentation code.

At the same time, you maintain complete control over business logic:

```python
class CustomAnalyzer(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AnalysisEvent:
        # Your custom analysis logic here
        # Complex rules, proprietary algorithms, specific integrations
        return AnalysisEvent(results=your_custom_analysis)
```

This agent automatically inherits platform capabilities—streaming updates, authentication, audit logging, error handling—while implementing exactly the business logic you need.

## The sustainable advantage

Frameworks get you started quickly but create technical debt. Every production requirement becomes custom development that your team must maintain, secure, and scale.

No-code platforms avoid technical debt but limit your capabilities. When your needs outgrow their templates, you have to rebuild everything.

Our SDK provides sustainable development. The infrastructure is maintained by the platform team. Security updates, performance improvements, and new capabilities benefit all agents automatically. Your code focuses on business logic that creates competitive advantage.

This approach scales both technically and organizationally. New developers join your team and immediately have access to proven patterns and working infrastructure. Complex agents build on the same foundation as simple ones. Advanced capabilities emerge through combining well-tested components rather than rebuilding everything custom.

## The Swiss advantage

Our approach reflects Swiss engineering principles applied to AI development:

**Reliability through bounded behavior.** Agents follow explicit workflows rather than open-ended exploration. Each step defines what can happen, making behavior predictable and auditable.

**Transparency through complete observability.** Every agent decision is visible and traceable. Compliance teams can follow any output back to its sources and decision points.

**Control through data sovereignty.** Sensitive processing stays on your infrastructure while non-critical operations can use cloud resources. You choose where each component runs and where data is processed.

## When to choose our SDK

Use our SDK when you need production AI systems that real users depend on, that handle sensitive data, that integrate with business processes, or that require compliance documentation.

If you're exploring AI capabilities and building proofs of concept, start with popular frameworks. They excel at rapid prototyping and experimentation.

When you're ready to deploy AI systems that create business value, handle real data, and integrate with operational processes, our SDK provides the infrastructure those requirements demand.

You don't choose between our SDK and other frameworks—you use both. Develop your AI logic with familiar tools, then deploy through our SDK to get enterprise capabilities without enterprise development effort.

The Swiss AI Hub platform provides the solid foundation with security, traceability, and operational capabilities. The SDK gives you the tools to build custom solutions on that foundation. Together, they let you focus on solving business problems with AI rather than building AI infrastructure.