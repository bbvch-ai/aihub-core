# Adopt OpenTelemetry for End-to-End Distributed Tracing

## Context

The Swiss AI Hub operates as a distributed microservice architecture with multiple independent components (agents,
processes, pipelines, API services) communicating asynchronously through NATS messaging. This architecture provides
excellent scalability and flexibility but creates significant observability challenges:

- **Visibility Gap**: When an agent triggers another agent or a process orchestrates multiple services, there was no way
  to trace the complete execution flow across service boundaries.
- **Debugging Complexity**: Identifying performance bottlenecks or failure points required manual correlation of logs
  from multiple services, making root cause analysis time-consuming and error-prone.
- **Performance Analysis**: Without distributed tracing, understanding the end-to-end latency breakdown and identifying
  slow components in complex workflows was nearly impossible.
- **Service Dependencies**: The actual runtime dependencies between services were opaque, making it difficult to
  understand the impact of changes or failures in one component on the overall system.

While we already had Phoenix tracing integration for individual agent runs (as noted in ADR
`2025_07_09_adopt_mcp_protocol.md`), this only provided visibility within single service boundaries, not across the
entire distributed system.

## Decision Drivers

- **Complete Observability**: Need to trace requests as they flow through multiple services, agents, and processes
- **Context Preservation**: Must maintain trace context across asynchronous NATS message boundaries
- **Minimal Code Changes**: Solution should integrate transparently with existing NATS publishers and subscribers
- **Standards Compliance**: Adopt industry-standard protocols for vendor-agnostic observability
- **Performance Impact**: Tracing overhead must be negligible to avoid affecting system performance
- **Developer Experience**: Traces must be easily accessible and provide actionable insights for debugging

## Decision

We will implement comprehensive end-to-end distributed tracing using OpenTelemetry (OTel) with the following approach:

1. **OpenTelemetry as the Tracing Standard**: Use OpenTelemetry SDK for generating, propagating, and exporting traces
   across all services.

2. **NATS Context Propagation**: Implement trace context propagation through NATS message headers using the W3C Trace
   Context standard, ensuring trace continuity across asynchronous message boundaries.

3. **Named Publishers and Subscribers**: Require all NATS publishers and subscribers to have meaningful names, enabling
   clear identification of trace spans and understanding of event flow patterns.

4. **Automatic Instrumentation**: Integrate tracing directly into base classes (`AbstractPublisher`,
   `AbstractSubscriber`) to ensure all messaging automatically participates in distributed tracing without requiring
   changes to existing code.

5. **Phoenix as Visualization Layer**: Continue using Arize Phoenix for trace visualization and analysis, leveraging its
   AI/ML-specific observability features while maintaining OpenTelemetry compatibility.

## Consequences

### Positive Outcomes

- **Full System Visibility**: Complete end-to-end tracing of requests across all microservices, agents, and processes
- **Faster Debugging**: Developers can quickly identify bottlenecks and failures by following a single trace ID through
  the entire system
- **Performance Insights**: Clear visibility into latency distribution across components enables targeted optimization
- **Service Dependency Mapping**: Automatic discovery of runtime service dependencies through trace analysis
- **Standards Compliance**: OpenTelemetry ensures compatibility with multiple observability backends and future-proofs
  our implementation
- **Transparent Integration**: Existing code automatically gains tracing capabilities through base class modifications

### Trade-offs and Considerations

- **Naming Requirement**: All publishers and subscribers must now be named, requiring updates to existing anonymous
  implementations
- **Header Overhead**: Small increase in message size due to trace context headers (typically ~100 bytes)
- **Storage Requirements**: Trace data storage needs will increase, requiring appropriate retention policies
- **Learning Curve**: Developers need to understand OpenTelemetry concepts and best practices for effective trace
  analysis
- **Configuration Complexity**: Proper setup of OpenTelemetry exporters and sampling strategies requires careful
  configuration
