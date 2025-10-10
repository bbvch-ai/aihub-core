---
title: Dashboards
index: 2
---

# Dashboards

## Overview

Dashboards are visual interfaces that present complex platform information in an intuitive, easy-to-understand format. Instead of searching through thousands of individual data points, dashboards organize metrics, logs, traces, and health information into meaningful charts, graphs, and summaries that tell the story of your AI Hub platform's performance and health.

Think of dashboards as the instrument panel in an airplane cockpit - they present the most important information at a glance while allowing you to drill deeper into specific areas when needed.

## Primary Observability Platform: SigNoz

### What is SigNoz?

SigNoz is the central observability platform for your AI Hub. It receives all metrics, logs, and traces collected by the OpenTelemetry Collector and presents them through comprehensive, interactive dashboards. SigNoz is specifically designed for modern cloud applications and provides enterprise-grade observability without the complexity of traditional monitoring tools.

### Why SigNoz?

**Unified Experience**: All three pillars of observability - metrics, logs, and traces - are accessible from a single interface. You don't need to switch between different tools to understand what's happening in your platform.

**Cloud-Based Access**: SigNoz operates as a cloud service, meaning you can access your platform's health and performance data from anywhere, anytime, without managing additional infrastructure.

**Cost-Effective**: Unlike traditional observability platforms that charge per data point or user seat, SigNoz provides predictable pricing that scales with your needs.

**Modern Architecture**: Built specifically for containerized, microservices-based applications like your AI Hub, SigNoz understands the complexity of distributed systems.

### How Data Reaches SigNoz

All observability data flows through the OpenTelemetry Collector, which acts as a central processing hub. The collector receives metrics from Docker containers, logs from services and health checks, and traces from application operations. It then processes, enriches, and forwards this data securely to your SigNoz cloud endpoint using encrypted connections with authentication keys.

This architecture ensures that even if individual services experience problems, observability data continues to flow, and you maintain visibility into what's happening.

## Available Dashboards

### Infrastructure Overview Dashboard

A high-level view of your entire platform's health:

**Container Resource Usage**: Visual representation of CPU, memory, and network utilization across all services. Quickly identify which components are consuming the most resources and whether any are approaching capacity limits.

**Service Health Matrix**: Grid or heat map showing the health status of every platform component. Color coding makes it immediately obvious which services are healthy (green), experiencing warnings (yellow), or failed (red).

**Network Traffic Patterns**: Visualization of data flow between services, helping you understand communication patterns and identify potential bottlenecks in service-to-service communication.

**Storage Utilization**: Current usage and trends for MinIO object storage, PostgreSQL databases, and Milvus vector database, helping predict when additional capacity will be needed.

### Application Performance Dashboard

Focus on user-facing service quality:

**Response Time Trends**: Line graphs showing how quickly the platform responds to user requests over time, with breakdowns by operation type (AI queries, document uploads, searches).

**Request Volume**: Bar charts or area graphs displaying the number of requests handled, helping identify peak usage periods and capacity planning needs.

**Success and Error Rates**: Percentage of operations that complete successfully versus those that fail, with drill-down capability to investigate specific error types.

**Active User Sessions**: Current number of logged-in users and their activity levels, providing real-time insight into platform utilization.

**API Endpoint Performance**: Detailed metrics for each API endpoint, showing which operations are fastest, slowest, or most frequently used.

### AI Operations Dashboard

Specialized view for artificial intelligence activities:

**Model Usage Statistics**: Which AI models are being invoked, how frequently, and for what types of questions. This helps understand user preferences and optimize model selection.

**Token Consumption**: Real-time and historical tracking of AI token usage across all models, with cost calculations and trend analysis for budget management.

**Query Response Times**: How long AI operations take from question submission to answer delivery, broken down by model type and query complexity.

**Context Retrieval Performance**: Effectiveness of the RAG (Retrieval-Augmented Generation) system in finding relevant documents to answer questions.

**Cost per Operation**: Financial metrics showing the expense of different AI operations, enabling cost optimization and feature pricing decisions.

### Service Health Dashboard

Comprehensive health monitoring:

**Service Status Grid**: Real-time health status for every platform component with last-check timestamps and historical uptime percentages.

**Health Event Timeline**: Chronological view of all health status changes, showing when services became unhealthy and when they recovered.

**Recovery Time Analysis**: Statistics on how quickly services return to health after failures, helping identify services that need improvement.

**Dependency Health Map**: Visual representation of service dependencies, showing how the health of one service affects others.

**Restart Frequency**: Tracking of how often containers restart, helping identify unstable services that need attention.

### Log Analysis Dashboard

Making sense of millions of log entries:

**Log Volume Trends**: How many log entries are being generated over time, with breakdown by service and severity level.

**Error Distribution**: Which services are generating the most errors, what types of errors are occurring, and whether error rates are increasing or decreasing.

**User Activity Timeline**: Chronological view of user actions, useful for investigating specific incidents or understanding user behavior.

**Security Event Summary**: Dedicated view of authentication attempts, access patterns, and potential security concerns.

**Search and Filter Interface**: Powerful tools to find specific log entries based on time, service, user, error type, or custom search terms.

### Trace Visualization Dashboard

Understanding request flows:

**Service Dependency Map**: Interactive diagram showing how different platform components communicate and depend on each other.

**Latency Distribution**: Histograms showing the spread of response times, helping identify whether performance is consistent or highly variable.

**Slow Trace Analysis**: Automatic identification of the slowest operations with detailed breakdowns of where time is being spent.

**Error Trace Collection**: Failed requests grouped by error type with the ability to examine individual failure scenarios in detail.

**AI Operation Breakdown**: Specialized view for AI requests showing context retrieval time, model processing time, and response assembly time.

## Specialized Service Dashboards

### Traefik Proxy Dashboard

Built-in dashboard for the reverse proxy and load balancer:

**Access URL**: `traefik.${DOMAIN}` (your domain)

**Authentication**: Basic authentication with admin credentials

**Key Features**:
- **Router Configuration**: Visual display of all routing rules and priorities
- **Service Backends**: Health and status of backend services receiving traffic
- **Middleware Chains**: Security headers, authentication, and other request processing
- **TLS Certificate Status**: Valid certificates, expiration dates, and renewal status
- **Real-Time Request Metrics**: Current requests per second and response times
- **HTTP and HTTPS Traffic**: Volume and patterns of secure versus insecure traffic

**Business Value**: Ensures that user requests are being routed correctly and that all security measures are active and functioning.

### Phoenix LLM Dashboard

Specialized observability for language model operations:

**Access**: Internal service at `http://phoenix:6006`

**Authentication**: Disabled for internal use (no credentials required)

**Key Features**:
- **Trace Visualization**: Visual flow of LLM operations from prompt to response
- **Token Usage Metrics**: Detailed tracking of input and output tokens per request
- **Latency Analysis**: Response time breakdown for different models and operation types
- **Model Performance Tracking**: Comparison of different AI models' speed and effectiveness
- **Cost Attribution**: Financial tracking linked to specific operations and users
- **Prompt Analysis**: Understanding of how questions are formatted for AI models

**Business Value**: Provides transparency into AI operations, enabling cost optimization and quality improvement for AI-powered features.

### Dagster Workflow Dashboard

Orchestration and data pipeline monitoring:

**Access URL**: `dagster.${DOMAIN}` (your domain)

**Authentication**: OAuth-based with role-based access control

**Key Features**:
- **Pipeline Execution Status**: Current and historical runs of data processing workflows
- **Job Scheduling**: Automated task timing and frequency
- **Resource Utilization**: Computing resources consumed by different pipelines
- **Dependency Graphs**: Visual representation of how data flows through processing stages
- **Error Tracking**: Failed pipeline runs with detailed error information
- **Asset Lineage**: Understanding of how data is transformed through processing

**Business Value**: Ensures that background data processing - like document indexing and knowledge base updates - is running smoothly and efficiently.

## Multi-Platform Support

### Architecture Flexibility

While SigNoz is the primary observability platform, the AI Hub's architecture supports sending data to multiple platforms simultaneously. This is possible because the OpenTelemetry Collector uses vendor-neutral data formats and can export to various backends.

### Supported Alternative Platforms

**ELK Stack (Elasticsearch, Logstash, Kibana)**:
The OpenTelemetry Collector can export directly to Elasticsearch, making metrics, logs, and traces available through Kibana dashboards. Organizations already invested in ELK infrastructure can leverage existing tools and expertise.

**Grafana with Loki and Prometheus**:
Metrics can be exported to Prometheus for time-series analysis, logs to Loki for aggregation, and both visualized through Grafana's powerful dashboarding capabilities. This open-source stack is popular in many enterprises.

**Splunk**:
Organizations using Splunk for security information and event management (SIEM) can receive AI Hub observability data through the Splunk HEC (HTTP Event Collector) exporter.

**Datadog**:
Companies standardized on Datadog for application performance monitoring can configure the collector to send all observability data to their Datadog account, leveraging its analytics and alerting capabilities.

**Fluent Bit / Fluentd with Elasticsearch**:
For organizations preferring Fluent-based log collection, the OpenTelemetry Collector can forward data to Fluentd, which then processes and routes to Elasticsearch or other destinations.

### Implementation Approach

Adding additional observability platforms requires configuration changes to the OpenTelemetry Collector, not modifications to individual services. This means you can:

- **Dual-Export**: Send data to both SigNoz and your corporate standard simultaneously
- **Gradual Migration**: Start with one platform and add others over time
- **Platform Evaluation**: Test multiple solutions without disrupting existing monitoring
- **Compliance Requirements**: Meet specific regulatory requirements for data retention or location

The configuration changes are straightforward and involve adding exporter definitions and updating pipeline configurations in the collector's YAML file.

## Dashboard Access and Permissions

### SigNoz Cloud Access

Access to SigNoz dashboards is controlled through the ingestion endpoint and authentication key configured in your platform. Your organization's designated administrators receive login credentials to the SigNoz web interface, where they can:

- View all dashboards
- Create custom dashboards
- Configure alerts
- Manage user access
- Export reports

### Traefik Dashboard Security

The Traefik dashboard is protected with basic authentication. Only administrators with valid credentials can access routing configuration and real-time traffic information. This prevents unauthorized users from learning about internal platform architecture.

### Phoenix Internal Access

The Phoenix dashboard operates without authentication but is only accessible from within the platform's internal network. This means it's available to administrators who have secure access to the platform infrastructure but not exposed to the public internet.

### Dagster Workflow Security

Dagster uses OAuth-based authentication with role-based access control. Only users assigned to the "DagsterAdmin" role can access workflow dashboards and make configuration changes. This ensures that sensitive data pipeline operations are controlled appropriately.

## Data Retention and Storage

### Retention Policies

Observability platforms store telemetry data according to configurable retention policies that balance detail with storage costs:

**High-Resolution Data**: 15-30 days of fine-grained metrics and logs (seconds or minutes granularity). This detailed data enables precise troubleshooting of recent issues and performance analysis.

**Downsampled Data**: 90-365 days of aggregated metrics (hourly or daily summaries). Historical trends remain visible while reducing storage requirements for older data.

**Long-Term Archives**: Multi-year retention of coarse-grained summaries for compliance, audit trails, and long-term trend analysis.

### Configuration Flexibility

Organizations configure retention policies based on:

- **Compliance Requirements**: Regulatory mandates for audit trail retention
- **Budget Constraints**: Storage costs versus historical data value
- **Analytical Needs**: Required lookback periods for capacity planning and trend analysis
- **Incident Investigation**: How far back you need detailed data for troubleshooting

### SigNoz Retention

SigNoz Cloud retention policies are configured through your SigNoz account settings. Different retention periods can be set for metrics, logs, and traces independently, enabling cost optimization based on each telemetry type's value.

### Alternative Platform Retention

When using other observability platforms, retention policies depend on the chosen platform:

- **Prometheus**: Typically 15-30 days, with remote write for long-term storage
- **Elasticsearch/ELK**: Configurable through index lifecycle management (ILM) policies
- **Grafana Cloud**: Tiered retention based on subscription level
- **Datadog**: Retention included in subscription with options for extended retention

## Dashboard Best Practices

### Regular Monitoring

Dashboards provide the most value when reviewed regularly:

- **Daily**: Quick health checks to ensure everything is operating normally
- **Weekly**: Performance trend review to identify developing issues
- **Monthly**: Comprehensive analysis for capacity planning and optimization
- **Quarterly**: Strategic review for investment planning and improvement priorities

### Customization

While default dashboards provide comprehensive coverage, custom dashboards tailored to your organization's specific needs often provide the most value:

- **Executive Summary**: High-level business metrics without technical detail
- **Operations Team**: Detailed technical metrics for day-to-day management
- **Security Team**: Focus on authentication, authorization, and potential threats
- **Finance Team**: Cost tracking and resource utilization for budget management

### Alert Integration

Dashboards are most powerful when combined with proactive alerting. Key metrics displayed on dashboards can trigger notifications when they exceed thresholds, enabling rapid response before users are affected.

### Mobile Access

Modern dashboard platforms, including SigNoz, provide mobile-responsive interfaces. This means you can check platform health from anywhere, enabling faster incident response and providing peace of mind outside business hours.

## Business Value of Dashboards

### Operational Efficiency

Dashboards consolidate information from hundreds of services and thousands of data points into concise, actionable views. This dramatically reduces the time needed to understand platform status and identify issues.

### Informed Decision-Making

Visual presentation of trends and patterns makes it easy to spot opportunities for improvement, justify infrastructure investments, and prioritize development efforts based on actual usage data rather than assumptions.

### Stakeholder Communication

Dashboards provide objective, data-driven status that can be shared with executives, customers, or regulatory bodies. They answer questions like "How reliable is the platform?" or "How efficiently are we using AI resources?" with concrete evidence.

### Continuous Improvement

By making performance visible, dashboards create a culture of continuous improvement. Teams can set goals, track progress, and celebrate achievements in platform reliability, performance, and efficiency.

### Cost Management

Detailed visibility into resource consumption and AI token usage enables precise cost tracking and optimization. You can identify expensive operations, compare the cost of different approaches, and make informed decisions about feature pricing or usage limits.