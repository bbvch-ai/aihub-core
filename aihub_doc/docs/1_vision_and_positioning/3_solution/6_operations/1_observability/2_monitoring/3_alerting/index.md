---
title: Alerting
index: 3
---

# Alerting

## Overview

Alerting is the proactive notification system that informs you when something requires attention in your AI Hub platform. While dashboards allow you to see what's happening when you look at them, alerts bring critical information to you automatically - ensuring that problems are addressed quickly, often before users are even aware of them.

Think of alerting as having a vigilant assistant who continuously monitors your platform and immediately notifies the right people when predefined conditions occur, whether that's a service failure, unusual usage patterns, or performance degradation.

## Current Implementation Status

### Infrastructure Foundation

The AI Hub platform has comprehensive alerting infrastructure in place through its integration with SigNoz. All the necessary data - metrics, logs, traces, and health checks - flows continuously to SigNoz, providing the foundation for sophisticated alerting capabilities.

### SigNoz Alerting Capabilities

SigNoz provides enterprise-grade alerting built on top of the observability data collected from your platform:

**Metric-Based Alerts**: Trigger notifications when performance indicators exceed thresholds, such as high CPU usage, memory pressure, or slow response times.

**Log-Based Alerts**: Generate alerts based on specific log patterns, such as error rates exceeding acceptable levels or security-relevant events like multiple failed login attempts.

**Trace-Based Alerts**: Notify teams when request performance degrades, such as AI operations taking longer than expected or document processing timeouts.

**Health Check Alerts**: Immediate notification when services transition from healthy to unhealthy status, enabling rapid response to availability issues.

### Configuration Approach

Alerting rules and notification channels are configured within the SigNoz platform itself rather than in the platform's code infrastructure. This separation provides several advantages:

**Dynamic Configuration**: Alert rules can be created, modified, or disabled without changing platform code or restarting services.

**Business Ownership**: Non-technical stakeholders can adjust alert thresholds and notification preferences based on business needs.

**Multi-Tenant Support**: Different organizations using the platform can configure alerts according to their specific requirements and risk tolerance.

**Rapid Response**: Alert configurations can be changed immediately in response to incidents or changing business conditions.

## Alert Categories

### Critical Service Alerts

Notifications for issues that immediately impact platform availability:

**Service Unavailability**: When core services like the API gateway, database systems, or AI agents become unhealthy and stop responding to requests.

**Complete Outages**: When multiple related services fail simultaneously, indicating a systemic problem requiring immediate attention.

**Data Loss Risk**: When storage systems approach capacity limits or backup processes fail, threatening data integrity.

**Security Breaches**: When authentication systems detect potential unauthorized access attempts or suspicious patterns.

**Business Impact**: Any condition that directly prevents users from accessing or using the platform.

These alerts typically trigger immediate notifications to on-call personnel through multiple channels (SMS, phone calls, paging systems) to ensure rapid response.

### Performance Degradation Alerts

Notifications for issues affecting user experience but not causing complete failure:

**Slow Response Times**: When operations take significantly longer than normal, such as AI queries exceeding acceptable latency or document uploads timing out.

**High Resource Utilization**: When CPU, memory, or network usage approaches capacity limits, indicating potential future failures if not addressed.

**Elevated Error Rates**: When the percentage of failed operations increases above baseline levels, even if most requests still succeed.

**Queue Buildup**: When background processing tasks accumulate faster than they can be processed, leading to delays.

**Degraded AI Performance**: When language model responses slow down or context retrieval becomes less effective.

These alerts typically notify operations teams through email, messaging platforms (Slack, Microsoft Teams), or incident management systems (PagerDuty, Opsgenie).

### Capacity Planning Alerts

Proactive notifications about trends requiring future action:

**Storage Growth**: When disk usage trends suggest capacity will be exhausted within a defined timeframe (e.g., 30 days).

**Traffic Increases**: When user activity shows sustained growth patterns that may require infrastructure scaling.

**Cost Thresholds**: When AI token consumption or cloud resource usage approaches budget limits.

**Resource Trends**: When any metric shows concerning long-term patterns even if current levels are acceptable.

These alerts typically have longer response timeframes and are delivered through regular reports or email to planning and management teams.

### Security and Compliance Alerts

Notifications related to security posture and regulatory requirements:

**Authentication Anomalies**: Unusual login patterns, such as multiple failed attempts from the same source or successful logins from unexpected locations.

**Access Violations**: Attempts to access restricted resources or perform unauthorized operations.

**Configuration Changes**: Modifications to security-sensitive settings or permissions.

**Compliance Violations**: Activities that breach defined policies, such as data retention rules or usage restrictions.

**Audit Trail Gaps**: Missing or corrupted log entries that compromise the audit trail.

These alerts are typically sent to security teams and compliance officers, with varying urgency depending on the specific event.

### Cost Management Alerts

Financial notifications to control operational expenses:

**Budget Thresholds**: When cumulative spending approaches or exceeds defined budget limits for specific time periods.

**Token Consumption Spikes**: Unusual increases in AI model usage that significantly impact costs.

**Resource Inefficiency**: Idle or underutilized resources consuming budget without delivering value.

**Expensive Operations**: Individual requests or users consuming disproportionate resources.

These alerts help finance teams and platform administrators manage costs proactively rather than reactively addressing budget overruns.

## SigNoz Alert Configuration

### Alert Rule Definition

Within SigNoz, administrators create alert rules by specifying:

**Metric or Log Query**: What data to monitor, such as "container CPU usage" or "error log entries."

**Condition**: The threshold or pattern that triggers the alert, such as "CPU usage above 80%" or "more than 10 errors in 5 minutes."

**Duration**: How long the condition must persist before triggering, preventing false alarms from momentary spikes.

**Severity Level**: Critical, warning, or informational classification that determines notification urgency and routing.

**Evaluation Interval**: How frequently SigNoz checks whether the condition is met, balancing responsiveness against system load.

### Multi-Dimensional Alerting

SigNoz supports sophisticated alert conditions based on multiple factors:

**Service-Specific Alerts**: Different thresholds for different components based on their normal operating characteristics.

**Time-Based Variation**: Different alert thresholds during business hours versus off-hours when lower usage is expected.

**Comparative Alerts**: Notifications when current performance deviates significantly from historical baselines.

**Aggregated Conditions**: Alerts that trigger only when multiple related metrics simultaneously indicate problems.

**Rate of Change**: Detection of rapid changes even when absolute values remain within acceptable ranges.

### Notification Channels

SigNoz can deliver alerts through multiple channels:

**Email**: Detailed alert information sent to distribution lists or individual addresses.

**Webhook Integration**: HTTP callbacks to incident management systems like PagerDuty, Opsgenie, or VictorOps.

**Slack**: Direct messages or channel notifications in Slack workspaces for team collaboration.

**Microsoft Teams**: Notifications in Teams channels for organizations using Microsoft 365.

**Custom Webhooks**: Integration with any system that can receive HTTP POST requests, enabling connection to custom tools or workflows.

Different alert severities can route to different channels - critical alerts might page on-call staff while warnings post to team chat channels.

### Alert Enrichment

When SigNoz sends notifications, it includes valuable context:

**Current Values**: The specific metric readings or log counts that triggered the alert.

**Threshold Information**: What threshold was exceeded and by how much.

**Time Context**: When the condition began and how long it has persisted.

**Service Details**: Which specific platform component is affected.

**Dashboard Links**: Direct URLs to relevant dashboards for investigation.

**Runbook References**: Links to documented procedures for addressing the specific alert type.

This enrichment enables faster response by providing all necessary information in the initial notification.

## Infrastructure-Specific Alerting

### Container Health Alerting

The platform's health check infrastructure feeds directly into alerting:

**Docker Health Events**: When the Docker health event stream shows services transitioning to unhealthy status, SigNoz can immediately trigger alerts based on the structured health check logs.

**Service Restart Frequency**: Alerts when containers restart repeatedly, indicating instability even if they eventually return to healthy status.

**Startup Failures**: Notifications when services fail to become healthy within expected startup periods.

**Host-Level Correlation**: Alerts when multiple services on the same host fail simultaneously, suggesting host-level problems rather than service-specific issues (available in nightly/latest configurations with hostname tracking).

### Resource Exhaustion Alerting

Critical infrastructure resource alerts:

**Memory Pressure**: Notifications when containers approach memory limits, preventing out-of-memory crashes.

**CPU Saturation**: Alerts when sustained high CPU usage indicates insufficient processing capacity.

**Disk Space**: Warnings when storage utilization threatens data operations.

**Network Congestion**: Detection of bandwidth limitations or packet loss affecting service communication.

**Connection Pool Exhaustion**: Alerts when database connection limits are approached.

### Dependency Failure Alerting

Sophisticated alerts understanding service relationships:

**Cascading Failure Detection**: When downstream services fail because upstream dependencies are unhealthy, alerts identify the root cause rather than flooding teams with notifications about symptoms.

**Critical Path Monitoring**: Enhanced alerting for services that many other components depend on, recognizing their outsized impact on platform stability.

**Integration Health**: Alerts when external systems (AI model providers, authentication services) become unavailable or degraded.

### Performance Baseline Alerting

Intelligent alerting based on normal behavior patterns:

**Anomaly Detection**: SigNoz can learn normal metric patterns and alert when current behavior significantly deviates, even if absolute thresholds aren't exceeded.

**Seasonal Adjustment**: Different baselines for different times (business hours, weekends, holidays) prevent false alarms from expected usage variations.

**Trend Analysis**: Alerts for concerning trends before they become critical problems, such as gradually increasing error rates.

## Alert Response Workflow

### Notification Delivery

When an alert condition is met:

1. **Evaluation**: SigNoz evaluates the alert rule and confirms the condition has persisted for the defined duration
2. **Severity Assessment**: The alert's configured severity level determines notification urgency and routing
3. **Channel Selection**: Notification is sent through configured channels (email, Slack, PagerDuty, etc.)
4. **Context Inclusion**: All relevant context and dashboard links are included in the notification
5. **Acknowledgment Tracking**: The system tracks whether and when someone acknowledges the alert

### Investigation

Recipients use the information in the alert to investigate:

1. **Dashboard Access**: Click provided links to view relevant SigNoz dashboards
2. **Context Review**: Examine metrics, logs, and traces from the time period around the alert
3. **Scope Assessment**: Determine whether the problem is isolated or affecting multiple components
4. **Impact Evaluation**: Understand whether users are affected and to what degree
5. **Root Cause Analysis**: Use correlated data to identify the underlying problem

### Resolution

Based on investigation findings:

1. **Remediation**: Take appropriate action to resolve the underlying issue
2. **Verification**: Confirm that metrics return to normal and services become healthy
3. **Documentation**: Record the incident, actions taken, and outcome
4. **Alert Closure**: Mark the alert as resolved in the alerting system
5. **Post-Incident Review**: Analyze whether the alert fired appropriately and whether response was effective

### Continuous Improvement

Alert effectiveness is reviewed regularly:

**False Positive Analysis**: Alerts that fire but don't represent real problems are tuned or disabled to reduce noise.

**Missed Incidents**: Problems that weren't caught by existing alerts lead to new alert rule creation.

**Threshold Adjustment**: Alert thresholds are refined based on operational experience and changing platform characteristics.

**Notification Routing**: Channels and escalation paths are adjusted to ensure the right people receive the right alerts.

## Business Benefits

### Reduced Downtime

Proactive alerting enables problems to be addressed before they escalate into outages. Many issues can be resolved during low-usage periods before users are affected, dramatically improving platform availability.

### Faster Incident Response

When problems do occur, immediate notification with rich context enables much faster diagnosis and resolution. The difference between discovering an issue through user complaints versus proactive alerting can be minutes or hours of downtime.

### Cost Control

Alerts on resource utilization and AI token consumption enable proactive budget management. Organizations can respond to unexpected cost increases before they result in budget overruns or service disruptions.

### Capacity Planning

Trend-based alerts provide early warning of future capacity needs, allowing orderly procurement and deployment of resources rather than emergency scaling under pressure.

### Operational Efficiency

By automatically detecting and routing issues to appropriate teams, alerting reduces the burden of constant manual monitoring. Operations staff can focus on proactive improvements rather than reactive firefighting.

### Service Level Compliance

Alerts based on SLA thresholds ensure that contractual commitments are met. When performance approaches SLA limits, teams can take action before violations occur.

### Security Posture

Security-focused alerts enable rapid response to potential threats, minimizing the window of opportunity for attackers and reducing the impact of security incidents.

## Alert Management Best Practices

### Alert Fatigue Prevention

Too many alerts, especially false positives, lead to ignored notifications and missed critical issues:

**Appropriate Thresholds**: Set thresholds that capture real problems without triggering on normal operational variance.

**Duration Requirements**: Require conditions to persist for meaningful periods before alerting, filtering transient spikes.

**Severity Discipline**: Reserve critical severity for truly urgent issues to maintain its meaning.

**Regular Review**: Periodically assess alert value and disable rules that aren't providing actionable information.

### Actionable Alerts

Every alert should enable a clear response:

**Defined Actions**: Alert documentation should specify what actions to take in response.

**Appropriate Recipients**: Notifications should reach people who can actually address the issue.

**Sufficient Context**: Alerts should include enough information to begin investigation immediately.

**Clear Urgency**: Severity levels should accurately reflect required response timeframes.

### Coverage Without Overlap

Effective alerting covers critical scenarios without redundancy:

**Single Root Cause**: Multiple symptoms of the same problem should trigger one alert, not many.

**Priority Ordering**: More specific alerts should suppress more general ones to avoid confusion.

**Dependency Awareness**: Downstream failures caused by upstream issues should be suppressed.

### Continuous Refinement

Alert configurations should evolve with the platform:

**New Features**: New platform capabilities require new alerts to monitor their health.

**Changing Patterns**: Normal behavior evolves, requiring threshold adjustments.

**Operational Learning**: Incident experience informs improvements to alert rules.

**Business Changes**: Shifting business priorities may require different alerting emphasis.

## Getting Started with Alerting

### Initial Configuration

Organizations typically begin with a core set of critical alerts:

1. **Service Health**: Immediate notification of any service becoming unhealthy
2. **API Availability**: Alerts when the main API endpoint fails health checks
3. **Database Connectivity**: Notifications of database connection failures
4. **Storage Capacity**: Warnings when disk usage reaches 80% and critical alerts at 90%
5. **High Error Rates**: Alerts when error rates exceed 5% of total requests

### Progressive Enhancement

After establishing baseline alerting, organizations add:

**Performance Alerts**: Notifications when response times degrade significantly
**Resource Alerts**: Warnings about high CPU or memory usage approaching limits
**Cost Alerts**: Budget threshold notifications for AI token consumption
**Security Alerts**: Authentication failure patterns and access violations

### Customization

Over time, alerts are tailored to organizational needs:

**Business Hours Adjustment**: Different thresholds during active hours versus overnight
**Team-Specific Routing**: Alerts directed to appropriate specialized teams
**Escalation Policies**: Multi-tier notification for unacknowledged critical alerts
**Seasonal Patterns**: Adjusted baselines for predictable usage variations

## Technical Foundation

### OpenTelemetry Integration

All alert-relevant data flows through the OpenTelemetry Collector to SigNoz:

**Metrics Pipeline**: Container resource usage, application performance metrics, and custom business metrics.

**Logs Pipeline**: Health check events, error logs, security events, and audit trails - all structured and searchable.

**Traces Pipeline**: Request performance data, AI operation details, and service interaction patterns.

This unified data collection ensures that alerting has access to comprehensive information about every aspect of platform operations.

### Structured Health Events

The platform's health check infrastructure produces structured events specifically designed for alerting:

**Consistent Format**: All health events use standardized JSON structure with predictable fields.

**Rich Attributes**: Events include container name, host name, health status, and event timing.

**Immediate Availability**: Health status changes are captured and forwarded in real-time.

**Historical Context**: The system maintains recent health event history for pattern analysis.

These structured events enable sophisticated health-based alerting without requiring custom log parsing or complex query logic.

### Multi-Environment Support

The platform's configuration architecture supports different alert configurations across environments:

**Development**: Minimal alerting to avoid noise during active development.

**Staging**: Representative alerting to validate alert configurations before production deployment.

**Production**: Comprehensive alerting with appropriate severity and notification routing.

**Multi-Host**: Hostname enrichment (in nightly/latest configurations) enables alerts that understand which physical or virtual hosts are experiencing problems.

## Future Alerting Enhancements

While the current infrastructure provides comprehensive alerting through SigNoz, potential enhancements include:

**Machine Learning Anomaly Detection**: Automated identification of unusual patterns without manual threshold configuration.

**Predictive Alerts**: Notifications of probable future issues based on trend analysis.

**Automated Remediation**: Integration with orchestration systems to automatically respond to certain alert types.

**Advanced Correlation**: More sophisticated multi-signal alerts that understand complex system behaviors.

**Business Metric Integration**: Alerts based on business KPIs rather than just technical metrics.

These capabilities can be implemented through SigNoz's evolving feature set and integration with complementary tools as organizational needs grow.