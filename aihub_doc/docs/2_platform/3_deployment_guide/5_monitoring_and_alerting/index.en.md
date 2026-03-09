---
title: Monitoring & Alerting
---

# Monitoring & Alerting

A production AI system must be transparent, reliable, and predictable. While Day 1 is about impressive demos, Day 2 is
about maintaining trust through operational excellence. The Swiss AI Hub provides a comprehensive, built-in
observability suite to give you a complete picture of your platform's health, performance, and cost.

This section explains the layers of monitoring and alerting built into the platform. You'll learn what we measure, how
you can visualize it, and how the system proactively notifies you of issues.

## The Pillars of Observability

The platform's monitoring philosophy is built on the industry-standard pillars of observability, providing answers to
critical operational questions.

### 1. Health Checks: "Is it working right now?"

Health checks are the platform's heartbeat, continuously verifying that every component is alive and functional. Unlike
metrics or logs, they provide a simple, immediate answer to the most fundamental question.

The platform uses a multi-layered approach:

- **Native Docker Checks**: Automatically monitor if service processes are running and responsive. Docker can restart
  unhealthy containers, enabling self-healing for transient issues.
- **Application Endpoint Checks**: Services expose dedicated health endpoints (`/health`) that verify not just liveness,
  but readiness to perform their specific function (e.g., can the database accept a query?).
- **Synthetic Probes**: For services without native health endpoints, the platform actively polls them to ensure they
  are available and responsive.

Every health status change - from healthy to unhealthy, service starts, and stops - is captured as a structured event,
providing a complete historical record of service availability.

### 2. Metrics: "How is it performing?"

Metrics are quantitative measurements that track performance and resource utilization over time. They are essential for
trend analysis, capacity planning, and identifying performance bottlenecks before they impact users.

The platform automatically collects key metrics across two main categories:

- **Infrastructure Metrics**: Container-level data for every service, including CPU utilization, memory consumption,
  network traffic, and disk I/O. This provides a clear view of resource usage and helps in cost management and capacity
  planning.
- **Application Metrics**: (In progress) As services are instrumented, they will emit detailed performance data, such as
  API request latency, error rates, AI agent execution times, and document processing throughput.

These metrics provide the data needed to optimize performance, forecast budgets, and make informed decisions about
scaling your infrastructure.

### 3. Logs: "What happened and why?"

Logs provide a detailed, chronological record of every event that occurs within the platform. When an issue arises, logs
are the primary tool for root cause analysis, offering the context needed to understand exactly what happened.

The platform captures logs from multiple sources:

- **Application Logs**: Structured output from all Python services, including informational messages, warnings, and
  critical errors.
- **Container Logs**: All `stdout` and `stderr` output from every container, capturing everything from startup messages
  to unhandled exceptions.
- **Request Logs**: Records of HTTP requests and their outcomes.
- **Security Logs**: Audit trail of authentication events, access attempts, and permission checks.

All logs are centralized, structured, and searchable, allowing you to quickly diagnose problems, audit activity, and
analyze usage patterns.

## Dashboards: The Unified View

Data is only useful if you can understand it. The Swiss AI Hub uses **SigNoz**, an open-source, OpenTelemetry-native
platform, as its central observability backend. It provides a single, unified interface to visualize all your health,
metric, and log data.

Out-of-the-box, you get access to several key dashboards:

- **Infrastructure Overview**: A high-level view of CPU, memory, and network utilization across all services, plus a
  real-time matrix of service health.
- **AI Operations Dashboard**: Specialized view of AI activities, including model usage, token consumption, query
  latency, and cost-per-operation tracking.
- **Application Performance**: User-facing service quality metrics, such as API response times, request volumes, and
  error rates.
- **Log Analysis**: A powerful interface to search, filter, and analyze log data from every component in the platform.

::: details Specialized Service Dashboards
For deeper insights, the platform also includes built-in dashboards for specific infrastructure components:

- **Traefik (Reverse Proxy)**: Visualizes request routing, service health, and TLS certificate status.
- **Langfuse (LLM Observability)**: Traces every LLM operation, showing token usage, latency, cost attribution, and full
  prompt/response context. Also provides dataset management and experiment evaluation.
- **Dagster (Workflow Engine)**: Monitors the status, history, and performance of all data ingestion and processing
  pipelines.
:::

## Alerting: Proactive Notifications

While dashboards are for pulling information, alerting proactively pushes critical information to you. It turns your
observability data into automated notifications, ensuring you're aware of issues often before your users are.

The alerting system is highly flexible and configured within your observability platform (e.g., SigNoz), not hardcoded
into the Swiss AI Hub. This allows you to tailor notifications to your organization's specific needs. You can configure
alerts for:

- **Critical Service Failures**: Immediate notification if a core service like the API gateway or database becomes
  unhealthy.
- **Performance Degradation**: Alerts when API response times exceed targets or error rates begin to climb.
- **Resource Limits**: Proactive warnings when CPU, memory, or storage utilization approaches capacity limits.
- **Cost Management**: Notifications when AI token consumption or cloud spending approaches predefined budget
  thresholds.
- **Security Events**: Alerts for suspicious activity, such as repeated failed login attempts.

Alerts can be routed to various channels, including email, Slack, Microsoft Teams, and incident management platforms
like PagerDuty.

## The Observability Foundation: OpenTelemetry

The entire monitoring and alerting system is built on **OpenTelemetry (OTel)**, a CNCF-graduated, vendor-neutral
standard for observability.

This is a deliberate architectural choice with significant benefits:

- **No Vendor Lock-in**: The platform emits data in a standard format. While SigNoz is the default, you are free to send
  telemetry to any OTel-compatible backend - be it Grafana, Datadog, Splunk, or your existing enterprise monitoring tool.
  Adding a new destination is a configuration change, not a re-instrumentation project.
- **Unified Data**: OTel provides a consistent way to collect metrics, logs, and traces. This means all your data is
  automatically correlated, allowing you to seamlessly pivot from a performance metric spike to the exact logs and
  traces that explain it.
- **Future-Proof**: By building on an industry standard, the platform benefits from the continuous innovation of the
  entire observability community.

All telemetry flows through a central **OpenTelemetry Collector** within the platform. This component receives data from
all services, enriches it with useful metadata, and securely exports it to your chosen destination(s). This architecture
ensures that you have complete control and ownership over your observability data, just as you do with the rest of the
platform.
