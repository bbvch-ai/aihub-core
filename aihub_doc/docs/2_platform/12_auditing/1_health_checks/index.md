---
title: Health Check
index: 1
---

# Health Checks

## Overview

Health checks are continuous automated tests that verify all components of your AI Hub platform are working correctly.
Think of them as regular wellness checks that ensure every service is alive, responsive, and functioning properly -
similar to how a medical professional performs routine examinations to catch potential issues before they become serious
problems.

Unlike metrics that measure "how much" or logs that record "what happened," health checks answer the fundamental
question: "Is this working right now?"

## What We Monitor

### Core Infrastructure Services

Essential foundation components that everything else depends on:

- **Database Systems**: PostgreSQL for application data, MongoDB for operational data
- **Vector Database**: Milvus for AI-powered document search and retrieval
- **Storage Services**: MinIO for document and file storage
- **Cache Services**: Redis for session management and performance optimization
- **Message Queue**: NATS for communication between platform components
- **Coordination Services**: etcd for distributed system configuration

### Application Services

Business-critical capabilities that directly serve users:

- **API Gateway**: Entry point for all platform requests
- **Open WebUI**: User interface and interaction layer
- **LiteLLM Proxy**: Language model access and management
- **AI Agents**: LLM Wrapping Agent and RAG Agent for AI operations
- **Data Pipelines**: Document processing and knowledge base management
- **Workflow Engine**: Dagster for orchestrating complex operations

### Supporting Services

Components that enable core functionality:

- **Jupyter Lab**: Code execution and data analysis environment
- **Playwright Server**: Web content extraction for AI context
- **Docling Service**: Advanced document parsing and analysis
- **Phoenix**: LLM observability and performance tracking
- **OAuth Proxy**: Authentication and access control
- **Reverse Proxy**: Traefik for routing and load balancing

### Document Processing Components

Services specifically for handling and analyzing documents:

- **Document Extraction**: Converting various file formats to analyzable text
- **OCR Engines**: Text recognition from images and scanned documents
- **Table Recognition**: Extracting structured data from documents
- **Layout Analysis**: Understanding document structure and organization

## Types of Health Checks

### Native Docker Health Checks

Built-in health verification that Docker performs automatically:

- **Liveness Checks**: Confirms the service process is running
- **Readiness Checks**: Verifies the service can accept requests
- **Startup Checks**: Ensures proper initialization before accepting traffic
- **Continuous Monitoring**: Regular intervals to detect when services become unhealthy

These checks run automatically without configuration and restart services when problems are detected.

### HTTP Endpoint Checks

Services that expose dedicated health check URLs:

- **MinIO Storage**: Verifies object storage availability and responsiveness
- **Milvus Database**: Confirms vector database query capability
- **LiteLLM Proxy**: Ensures AI model access is functioning
- **API Gateway**: Validates request processing capability
- **Docling Service**: Checks document processing availability
- **Playwright Server**: Confirms web content extraction readiness

These endpoints provide detailed status information beyond simple "alive or dead" checks.

### Database Connection Checks

Verification that database systems are accepting connections and processing queries:

- **PostgreSQL**: Tests connection and basic query execution
- **MongoDB**: Validates document database availability
- **Redis**: Confirms cache operations are working
- **Milvus**: Verifies vector search capability

These checks ensure data operations can proceed normally.

### gRPC Health Probes

Specialized checks for services using gRPC protocol:

- **Pipeline Services**: Confirms data processing pipelines are ready
- **AI Agents**: Validates that AI operation handlers are responsive
- **Internal Services**: Checks communication between platform components

gRPC health checks verify both the service availability and protocol-level communication.

### Custom Polling Checks

Specialized monitoring for services without native health endpoints:

- **Attu**: Milvus management interface availability
- **NATS**: Message queue responsiveness
- **Phoenix**: LLM observability platform status
- **Dagster Webserver**: Workflow orchestration interface readiness

These services are monitored every 60 seconds to ensure continuous availability.

## Health Check Event Capture

### Real-Time Status Changes

The platform actively monitors and records all health status transitions:

- **Healthy to Unhealthy**: When a service develops problems
- **Unhealthy to Healthy**: When a service recovers
- **Service Starts**: When components initialize after deployment or restart
- **Service Stops**: When components shut down gracefully or crash

### Docker Event Stream

A dedicated sidecar container monitors Docker's native health status events:

- **Historical Context**: Captures the last 15 minutes of health events on startup
- **Continuous Monitoring**: Streams all subsequent health status changes
- **Structured Format**: Events recorded in standardized JSON format
- **Host Attribution**: Each event tagged with the server hostname
- **Automatic Collection**: No manual configuration required

### Synthetic Health Checks

For services without built-in health monitoring, the platform performs active checks:

- **HTTP Endpoints**: Tests connectivity and response for web services
- **gRPC Services**: Validates protocol-level communication health
- **Periodic Execution**: Runs every 60 seconds to detect problems quickly
- **Status Recording**: Results logged in the same format as Docker events
- **Failure Detection**: Distinguishes between unavailable and unhealthy states

## Business Benefits

### Proactive Problem Detection

Health checks identify issues before users are affected:

- **Early Warning**: Problems detected within seconds or minutes of occurrence
- **Service Recovery**: Automatic restarts of unhealthy services minimize downtime
- **Degradation Detection**: Identify services performing poorly before they fail completely
- **Dependency Awareness**: Understand when one service failure affects others
- **Preventive Action**: Address issues during low-usage periods when possible

This proactive approach significantly reduces user-facing incidents and maintains consistent service quality.

### Operational Transparency

Clear visibility into platform status at all times:

- **Current State**: Instant understanding of which components are healthy
- **Historical Patterns**: Track service reliability over time
- **Failure Frequency**: Identify chronically problematic components
- **Recovery Speed**: Measure how quickly services return to health after issues
- **Availability Metrics**: Calculate uptime percentages for reporting

This transparency supports informed decision-making and builds confidence in platform reliability.

### Incident Response

When problems occur, health checks provide critical information:

- **Failure Scope**: Which services are affected and which are still healthy
- **Timeline Establishment**: Exact time when problems began
- **Dependency Impact**: How one service failure cascaded to others
- **Recovery Verification**: Confirmation when services return to normal
- **Root Cause Clues**: Patterns that suggest underlying issues

This information dramatically accelerates problem resolution and reduces mean time to recovery.

### Service Level Compliance

Health checks support contractual and governance requirements:

- **SLA Tracking**: Accurate uptime measurement for service level agreements
- **Compliance Reporting**: Documented proof of system availability
- **Audit Evidence**: Historical records of platform health
- **Performance Baselines**: Establish what "normal" availability looks like
- **Improvement Measurement**: Track reliability improvements over time

### Capacity Planning

Health check patterns reveal resource needs:

- **Stress Indicators**: Services that become unhealthy under load
- **Recovery Times**: How long services take to restart after failures
- **Failure Clusters**: Multiple services failing simultaneously suggests resource constraints
- **Startup Performance**: Whether services initialize quickly or struggle
- **Degradation Patterns**: Early signs of insufficient capacity

This information guides infrastructure investment and scaling decisions.

### Automated Recovery

Health checks enable self-healing platform behavior:

- **Automatic Restarts**: Docker automatically restarts unhealthy containers
- **Traffic Rerouting**: Traefik removes unhealthy services from load balancing
- **Cascade Prevention**: Stop sending requests to failing services
- **Graceful Degradation**: Platform continues operating with reduced capabilities
- **Recovery Verification**: Confirm services are truly healthy before resuming traffic

This automation reduces operational burden and improves reliability without human intervention.

## How It Works

### Multi-Layer Monitoring

The platform implements health checking at multiple levels:

**Container Level**: Docker monitors service processes and basic responsiveness using native health check commands built
into each service.

**Application Level**: Services expose dedicated health endpoints that verify not just that they're running, but that
they can actually perform their functions.

**Infrastructure Level**: External monitoring verifies that services are reachable and responsive from outside their
containers.

**Integration Level**: Health checks verify that services can communicate with their dependencies and external systems.

This layered approach ensures comprehensive coverage - a service isn't considered healthy just because its process is
running, but because it can actually perform its intended function.

### Continuous Evaluation

Health checks run on regular intervals:

- **Standard Services**: Checked every 10-30 seconds
- **Critical Services**: More frequent checks for essential components
- **Startup Grace Periods**: Initial delays allow services time to initialize (5-90 seconds depending on service
  complexity)
- **Failure Thresholds**: Multiple consecutive failures required before declaring unhealthy
- **Recovery Confirmation**: Multiple successful checks required before declaring recovered

This continuous evaluation quickly detects problems while avoiding false alarms from momentary issues.

### Centralized Collection

All health check results flow to a central observability system:

- **Unified Dashboard**: Single view of entire platform health
- **Event Stream**: Real-time feed of status changes
- **Historical Storage**: Long-term record for trend analysis
- **Cross-Correlation**: Connect health events with logs, metrics, and traces
- **Alert Integration**: Health failures can trigger notifications

### Intelligent Interpretation

The system understands relationships between services:

- **Dependency Mapping**: Know which services depend on others
- **Cascading Failures**: Identify root causes when multiple services fail
- **Expected Patterns**: Understand normal restart behavior during deployments
- **Anomaly Detection**: Flag unusual health patterns for investigation
- **Context Awareness**: Distinguish between planned maintenance and unexpected failures

## What You Can Learn

### Real-Time Platform Status

- **Overall Health**: Is the platform operating normally right now?
- **Component Status**: Which specific services are healthy or unhealthy?
- **Critical Paths**: Are services that users directly interact with available?
- **Dependency Health**: Are supporting services functioning correctly?
- **Degraded Operation**: Is the platform running with reduced capability?

### Reliability Patterns

- **Uptime Percentages**: Historical availability for each service
- **Failure Frequency**: Which components have problems most often
- **Mean Time Between Failures**: How reliable each service is
- **Mean Time to Recovery**: How quickly problems are resolved
- **Failure Correlation**: Which services tend to fail together

### Operational Quality

- **Stability Trends**: Is reliability improving or declining over time?
- **Deployment Impact**: How updates affect service health
- **Resource Adequacy**: Whether current infrastructure is sufficient
- **Configuration Quality**: If services are properly tuned
- **Integration Health**: How well components work together

### Planning Information

- **Scaling Needs**: Which services need more resources
- **Redundancy Requirements**: Where backup capacity is needed
- **Upgrade Priorities**: Which components need improvement most urgently
- **Risk Assessment**: Potential single points of failure
- **Investment Justification**: Evidence supporting infrastructure improvements

## Accessing Health Information

Health status is available through multiple interfaces:

**Real-Time Dashboards**: Visual displays showing current platform health with color-coded status indicators that make
it immediately obvious whether everything is working correctly.

**Status Pages**: Public or internal pages that communicate platform availability to users and stakeholders without
requiring access to detailed monitoring systems.

**Alert Notifications**: Automatic messages when health checks detect problems, sent via email, messaging systems, or
incident management tools.

**Historical Reports**: Summaries of health over time for trend analysis, compliance reporting, or executive briefings.

## Health Check Best Practices

### Meaningful Checks

Each health check verifies actual functionality, not just that a process is running. For example, database health checks
attempt to execute a simple query rather than just checking if the database process exists.

### Appropriate Intervals

Check frequency balances rapid problem detection against system overhead. Critical user-facing services are checked more
frequently than background processing services.

### Startup Awareness

Services receive adequate time to initialize before health checks begin. Complex services like document processors may
need 60-90 seconds to load models and prepare for work.

### Failure Tolerance

Multiple consecutive failures are required before declaring a service unhealthy, preventing false alarms from momentary
network issues or brief performance spikes.

### Recovery Confirmation

Services must demonstrate sustained health through multiple successful checks before being restored to service, ensuring
stability rather than flapping between healthy and unhealthy states.

## Integration with Platform Operations

### Automated Service Recovery

When health checks detect failures, Docker automatically attempts to restart the affected service, often resolving
transient issues without manual intervention.

### Load Balancing

Traefik removes unhealthy services from its routing table, ensuring user requests are only sent to healthy instances.

### Dependency Management

Services wait for their dependencies to become healthy before attempting to start, preventing cascading failures during
system initialization.

### Deployment Safety

During updates, new service versions must pass health checks before old versions are removed, ensuring zero-downtime
deployments.

### Monitoring Integration

Health check events are automatically exported to the observability platform, connecting service health with metrics,
logs, and traces for comprehensive analysis.
