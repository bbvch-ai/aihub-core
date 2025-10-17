---
title: Logging, Storage & Audit Trails
index: 3
---

# Logging, Storage & Audit Trails

The Swiss AI Hub implements comprehensive logging and auditing capabilities designed to meet enterprise security, compliance, and operational requirements. The platform captures detailed records of all system activities, user actions, and security events, providing complete transparency and traceability for regulatory compliance and forensic analysis.

## Overview

Logging in the Swiss AI Hub serves three critical purposes:

1. **Operational Monitoring**: Real-time visibility into system health, performance, and errors
2. **Security Auditing**: Complete records of access attempts, permission checks, and security events
3. **Compliance**: Immutable audit trails that satisfy regulatory requirements for data protection and access control

The platform's logging architecture is built on industry-standard OpenTelemetry protocols, ensuring flexibility, vendor neutrality, and integration with existing enterprise monitoring infrastructure.

## Log Collection Architecture

### Multi-Layer Log Collection

The platform captures logs from multiple sources to provide comprehensive visibility:

**Application Logs**: Structured logging from all Python services using standard logging libraries
- Informational messages about service startup, configuration, and normal operations
- Warning messages for recoverable issues or degraded performance
- Error messages for exceptions, failures, and critical issues
- Debug logs for detailed troubleshooting (disabled in production by default)

**Container Logs**: All output from Docker containers, including:
- Standard output (`stdout`) from all service processes
- Standard error (`stderr`) for uncaught exceptions and system errors
- Container lifecycle events (start, stop, restart, health check failures)

**HTTP Request Logs**: Detailed records of all API interactions:
- Request method, path, query parameters, and headers
- Response status codes and timing
- User identity and authentication status
- Client IP addresses and user agents

**Security Event Logs**: Dedicated logging for security-relevant events:
- Authentication attempts (successful and failed)
- Permission checks and authorization decisions
- Token validation events
- Administrative actions (user management, role assignments, configuration changes)
- Suspicious activities (repeated failed logins, access to restricted resources)

**AI Operation Logs**: Specialized logging for AI-specific activities:
- LLM requests and responses (with configurable PII redaction)
- Token consumption and cost tracking
- Agent workflow execution steps
- RAG retrieval operations and results
- Model guardrail violations and content filtering events

### Structured Logging Format

All logs are emitted in a structured JSON format to enable efficient parsing, indexing, and analysis:

```json
{
  "timestamp": "2025-10-17T15:21:12.028Z",
  "level": "INFO",
  "logger": "aihub_api.auth",
  "message": "User authenticated successfully",
  "trace_id": "a1b2c3d4e5f6",
  "span_id": "1234567890ab",
  "user_id": "user@example.com",
  "user_oid": "123e4567-e89b-12d3-a456-426614174000",
  "resource": "aihub.user.agent.customer_support",
  "action": "access_granted",
  "client_ip": "192.168.1.100",
  "request_id": "req_xyz789"
}
```

**Key Fields**:
- **timestamp**: ISO 8601 formatted timestamp in UTC
- **level**: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **logger**: Source component that generated the log
- **message**: Human-readable description of the event
- **trace_id / span_id**: OpenTelemetry identifiers for distributed tracing correlation
- **user_id / user_oid**: Identity of the user associated with the event
- **resource**: The resource being accessed or modified
- **action**: The specific action being performed
- **client_ip**: Source IP address for security tracking
- **request_id**: Unique identifier for correlating related log entries

## Log Storage and Retention

### Centralized Log Aggregation

All logs are centralized in the **SigNoz** observability platform (or alternative OpenTelemetry-compatible backend), providing:

- **Single Point of Access**: Query all logs from all services through a unified interface
- **Correlation**: Automatically link logs with distributed traces and metrics
- **Efficient Storage**: Optimized columnar storage with compression
- **Fast Querying**: Index-based search across millions of log entries

### Storage Architecture

**Primary Storage**: Logs are written to the observability backend's time-series database
- High-performance ingestion supporting thousands of log entries per second
- Indexed by timestamp, severity, service, and custom fields
- Optimized for range queries and pattern matching

**Long-Term Archival**: For compliance requirements, logs can be exported to:
- **Azure Data Lake Storage**: For long-term retention with encryption at rest
- **Local File System**: For on-premises air-gapped deployments
- **S3-Compatible Storage**: For cloud-agnostic archival solutions

### Log Retention Policies

The platform supports configurable retention periods based on log type and compliance requirements:

**Default Retention Periods**:
- **Operational Logs** (INFO, DEBUG): 30 days in hot storage, 90 days in archive
- **Security Audit Logs**: 90 days in hot storage, 7 years in archive (compliance requirement)
- **Error Logs** (ERROR, CRITICAL): 90 days in hot storage, 1 year in archive
- **AI Operation Logs**: 30 days in hot storage (with PII redaction), 90 days in archive

**Compliance-Driven Retention**: Organizations can configure retention policies to meet specific regulatory requirements:
- **GDPR**: Logs containing personal data can be automatically purged after the retention period
- **Financial Services**: Extended retention (7-10 years) for audit trails
- **Healthcare (HIPAA)**: 6-year retention with strict access controls
- **Government**: Custom retention based on specific regulatory frameworks

### Log Rotation and Archival

**Automatic Rotation**: Logs are automatically rotated based on:
- **Time-Based**: Daily or weekly rotation for manageable file sizes
- **Size-Based**: Rotation when log files reach a configured size threshold (e.g., 100MB)

**Archival Process**:
1. **Compression**: Rotated logs are compressed using gzip or similar algorithms to reduce storage costs
2. **Encryption**: Archived logs are encrypted using AES-256 before storage
3. **Metadata Preservation**: Index files maintain searchability without accessing archived logs
4. **Integrity Verification**: Checksums ensure archived logs haven't been tampered with

**Archival Storage Options**:
- **Azure Blob Storage (Cool/Archive Tiers)**: Cost-effective long-term storage with automatic lifecycle management
- **AWS S3 Glacier**: For extremely long retention periods at minimal cost
- **On-Premises NAS**: For organizations requiring data sovereignty
- **Write-Once-Read-Many (WORM)** storage: For regulatory requirements preventing log modification or deletion

## Security Event Logging and Audit Trails

### Authentication and Authorization Events

Every security-relevant event is logged with complete context:

**Successful Authentication**:
```json
{
  "level": "INFO",
  "event_type": "authentication_success",
  "user_id": "user@example.com",
  "user_oid": "123e4567-e89b-12d3-a456-426614174000",
  "authentication_method": "oidc",
  "identity_provider": "azure_ad",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

**Failed Authentication**:
```json
{
  "level": "WARNING",
  "event_type": "authentication_failure",
  "attempted_user_id": "user@example.com",
  "failure_reason": "invalid_token",
  "client_ip": "192.168.1.100",
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

**Permission Check**:
```json
{
  "level": "INFO",
  "event_type": "permission_check",
  "user_id": "user@example.com",
  "user_oid": "123e4567-e89b-12d3-a456-426614174000",
  "requested_permission": "aihub.user.agent.customer_support.chatbot_v2",
  "decision": "granted",
  "matching_rule": "aihub.user.agent.customer_support.*",
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

**Access Denied**:
```json
{
  "level": "WARNING",
  "event_type": "access_denied",
  "user_id": "user@example.com",
  "user_oid": "123e4567-e89b-12d3-a456-426614174000",
  "requested_resource": "aihub.admin.service.roles",
  "required_permission": "aihub.admin.service.roles",
  "user_permissions": ["aihub.user.?>"],
  "client_ip": "192.168.1.100",
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

### Administrative Action Logging

All administrative operations are logged with full details:

**Role Assignment**:
```json
{
  "level": "INFO",
  "event_type": "role_assignment",
  "admin_user_id": "admin@example.com",
  "admin_user_oid": "admin-oid-123",
  "target_user_id": "user@example.com",
  "target_user_oid": "user-oid-456",
  "role_name": "data_scientist",
  "action": "added",
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

**Configuration Change**:
```json
{
  "level": "INFO",
  "event_type": "configuration_change",
  "admin_user_id": "admin@example.com",
  "admin_user_oid": "admin-oid-123",
  "resource_type": "agent",
  "resource_id": "customer_support.chatbot_v2",
  "field_changed": "model_parameters",
  "old_value": "gpt-4",
  "new_value": "gpt-4-turbo",
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

### Data Access Logging

**Knowledge Base Access**:
```json
{
  "level": "INFO",
  "event_type": "knowledge_access",
  "user_id": "user@example.com",
  "user_oid": "user-oid-456",
  "knowledge_base": "hr_documents",
  "namespace": "policies",
  "query": "vacation policy",
  "num_results": 5,
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

**Document Upload**:
```json
{
  "level": "INFO",
  "event_type": "document_upload",
  "user_id": "user@example.com",
  "user_oid": "user-oid-456",
  "knowledge_base": "hr_documents",
  "namespace": "policies",
  "document_name": "vacation_policy_2025.pdf",
  "document_size_bytes": 245760,
  "timestamp": "2025-10-17T15:21:12.028Z"
}
```

## Activity Logging and Protocol

### User Activity Tracking

The platform provides comprehensive tracking of user interactions:

**Conversation Tracking**:
- Thread creation and participation
- Message timestamps and content (with optional PII redaction)
- Agent invocations within conversations
- File attachments and downloads

**Resource Usage**:
- AI model token consumption per user/department
- Knowledge base query frequency
- Agent execution counts and durations
- Cost allocation for chargeback reporting

**Workflow Execution**:
- Process initiation and completion
- Step-by-step workflow progression
- Human-in-the-loop approval decisions
- Exception handling and error recovery

### Compliance and Regulatory Reporting

**Audit Log Export**: Generate compliance reports covering:
- User access patterns and frequency
- Permission changes and administrative actions
- Data access (who accessed what data, when)
- Configuration changes and system modifications

**Report Formats**:
- **CSV/Excel**: For business users and compliance officers
- **JSON**: For automated compliance monitoring systems
- **PDF**: For signed audit reports with executive summaries
- **SIEM Integration**: Real-time streaming to Security Information and Event Management systems

**Tamper-Evident Logging**: For high-compliance environments:
- **Cryptographic Signatures**: Each log entry is signed to prevent modification
- **Blockchain Integration** (optional): Write log hashes to immutable ledgers
- **Audit Log Verification**: Tools to verify log integrity and detect tampering

## Log Query and Analysis

### Search Capabilities

The platform provides powerful log search capabilities:

**Full-Text Search**: Find logs containing specific keywords or phrases
```
message:"authentication failure"
```

**Field-Based Filtering**: Query specific structured fields
```
user_id:"user@example.com" AND level:ERROR
```

**Time Range Queries**: Search within specific time windows
```
timestamp:[2025-10-01 TO 2025-10-31] AND event_type:permission_check
```

**Pattern Matching**: Use wildcards and regular expressions
```
resource:aihub.user.agent.* AND decision:denied
```

**Aggregation and Analytics**: Generate statistics from log data
- Count authentication failures per user
- Analyze average response times by endpoint
- Track token consumption trends over time
- Identify most-accessed resources

### Log Correlation and Distributed Tracing

**Trace ID Correlation**: Every log entry includes OpenTelemetry trace and span IDs, enabling:
- Following a request across multiple services
- Understanding the complete context of an error
- Measuring end-to-end latency for complex operations
- Identifying performance bottlenecks

**User Journey Reconstruction**: Link all activities for a specific user:
```
user_oid:"user-oid-456" | sort timestamp
```

**Incident Investigation**: Rapidly diagnose issues by correlating:
- Error logs with preceding warning logs
- Failed permission checks with the user's role configuration
- Performance degradation with resource utilization metrics
- Security incidents with related authentication events

## Privacy and Data Protection

### Personal Data in Logs

**PII Redaction**: The platform can automatically redact personally identifiable information:
- User email addresses (replaced with hash identifiers)
- IP addresses (masked to subnet level)
- Conversation content (configurable per deployment)
- Document names and file paths

**Configurable Redaction Levels**:
- **Full Logging**: Capture all details (for development and low-sensitivity deployments)
- **Selective Redaction**: Redact specific PII categories based on regulatory requirements
- **Minimal Logging**: Log only essential security events with all PII removed

### GDPR Compliance

**Right to Access**: Generate reports of all log entries associated with a specific user

**Right to Erasure**: Support for user data deletion including:
- Anonymizing user identifiers in logs
- Purging logs beyond retention periods
- Exporting logs before deletion for compliance records

**Data Processing Records**: Maintain logs demonstrating compliance with data processing obligations

## Best Practices

### Log Management

- **Log Levels**: Use appropriate severity levels (DEBUG for development, INFO/WARNING for production)
- **Structured Fields**: Include consistent structured data for automated analysis
- **Context Inclusion**: Add relevant context (user, resource, operation) to every log entry
- **Sensitive Data**: Never log passwords, tokens, or encryption keys

### Security Monitoring

- **Real-Time Alerting**: Configure alerts for security events (failed logins, privilege escalation)
- **Anomaly Detection**: Monitor for unusual patterns in user behavior or system activity
- **Regular Review**: Schedule periodic reviews of security logs and access patterns
- **Incident Response**: Define procedures for investigating security events from logs

### Operational Excellence

- **Proactive Monitoring**: Use logs to identify issues before they impact users
- **Capacity Planning**: Analyze log trends to forecast resource needs
- **Performance Optimization**: Identify slow operations from timing logs
- **Cost Optimization**: Track AI token usage to manage costs

## Conclusion

The Swiss AI Hub's comprehensive logging and auditing system provides the transparency, security, and compliance capabilities required for enterprise deployments. By capturing detailed records of all activities, implementing secure storage with appropriate retention policies, and providing powerful analysis tools, the platform enables organizations to maintain security, meet regulatory requirements, and operate with confidence.
