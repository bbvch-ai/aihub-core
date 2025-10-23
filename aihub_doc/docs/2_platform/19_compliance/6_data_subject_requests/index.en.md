---
title: Data Subject Access Requests (DSAR)
index: 6
---

# Data Subject Access Requests (DSAR)

Data subjects have the right to request access to their personal data under both GDPR (Article 15) and Swiss revDSG. This document outlines the procedures for handling such requests with the AI-Hub platform.

:::warning Manual Process
**Current Status**: DSAR procedures are largely **manual**. Automated data export and user deletion APIs are not yet implemented (🚧 planned). Administrators must compile data from multiple sources using admin APIs and database queries.
:::

## Request Types

| Request Type | GDPR | revDSG | AI-Hub Status |
|--------------|------|--------|---------------|
| **Access** (data copy) | Article 15 | Art. 25 | 🟡 Manual compilation required |
| **Rectification** (correct data) | Article 16 | Art. 32 | ✅ Admin API available |
| **Erasure** (delete data) | Article 17 | Art. 32 | 🔴 No automation (manual) |
| **Restriction** (suspend processing) | Article 18 | Art. 32 | 🟡 Via permission revocation |
| **Portability** (export machine-readable) | Article 20 | Limited | 🔴 No automation (manual) |
| **Object** (stop processing) | Article 21 | Art. 32 | 🟡 Via permission revocation |

## 1. Access Request (DSAR) - Manual Procedure

**Timeline**: GDPR: 1 month, revDSG: 30 days

**Current Process:**

###  Step 1: Verify Identity
- Confirm requestor identity through secure channel
- For employees: internal HR verification
- For external users: email verification or authentication

### Step 2: Locate User Data

Use admin APIs to find the user:
```bash
# Find user by OID or email
GET /api/v1/users?search={email_or_oid}
```

### Step 3: Compile Data from All Sources

**UserEntity (Profile Data):**
```python
# Admin must query MongoDB directly or use admin API
GET /api/v1/users/{user_oid}

# Contains:
# - User ID (OID)
# - Email, name, profile image
# - Dashboard settings
# - Roles and permissions
# - Created/updated timestamps
```

**ThreadEntity (Conversation Data):**
```python
# Find all threads where user is a participant
# Currently NO API endpoint for "threads by user"
# Admin must query MongoDB:
db.thread_entity.find({"participants.user_ids": user_oid})

# Contains:
# - Thread IDs
# - Participant list (users and agents)
# - Thread metadata
# - Creation timestamps
```

**PersistedAgentEventEntity / PersistedProcessEventEntity:**
```python
# Find all events related to user's threads
# NO API endpoint available
# Admin must query MongoDB:
db.persisted_agent_event_entity.find({"thread_id": {$in: thread_ids}})
db.persisted_process_event_entity.find({"thread_id": {$in: thread_ids}})

# Contains:
# - User messages
# - Agent responses
# - Tool calls and results
# - Event timestamps
```

**Audit Logs:**
```python
# Currently stored in observability systems (SigNoz, OpenTelemetry)
# Admin must access observability dashboard or query trace storage
# Contains:
# - User actions (login, API calls)
# - Resource access logs
# - Timestamps and IP addresses
```

**Knowledge Base Data:**
```python
# User-uploaded documents in namespaces
# Admin must query:
# - Namespace permissions (which namespaces user can access)
# - Document metadata (who uploaded, when)
# Note: Vector embeddings are not personal data
```

### Step 4: Format and Deliver

- Compile all data into readable format (PDF or JSON)
- Include explanations of data categories
- Provide within regulatory timeline
- Document the request fulfillment in audit logs

## 2. Rectification Request - Semi-Automated

**Timeline**: GDPR: 1 month, revDSG: 30 days

**✅ Available:** Admin can update user profile data

```bash
# Update user profile via admin interface or API
PUT /api/v1/users/{user_oid}
{
  "name": "Corrected Name",
  "email": "corrected@email.com"
}
```

**For other data:**
- Thread messages: Immutable (audit trail requirement) - explain to user
- Knowledge base documents: Update source documents and re-ingest
- Audit logs: Immutable (compliance requirement)

## 3. Erasure Request - Manual Procedure

**Timeline**: GDPR: 1 month, revDSG: 30 days

:::danger Implementation Gap
**No automated user deletion**. The following procedure requires manual database operations and should be performed by a database administrator.
:::

**Current Manual Process:**

### Step 1: Assess Legal Grounds
Verify the request meets legal requirements:
- User withdrew consent
- Data no longer necessary
- No legal obligation to retain data
- No overriding legitimate interests

### Step 2: Manual Deletion Checklist

**⚠️ WARNING**: Execute in order, test in staging first

```python
# 1. Remove user from all threads
# API available:
DELETE /api/v1/threads/{thread_id}/users/{user_oid}
# Repeat for all threads

# 2. Delete user's PersistedAgentEvents
# NO API - Direct MongoDB operation:
db.persisted_agent_event_entity.deleteMany({
  "thread_id": {$in: user_thread_ids}
})

# 3. Delete user's PersistedProcessEvents
# NO API - Direct MongoDB operation:
db.persisted_process_event_entity.deleteMany({
  "thread_id": {$in: user_thread_ids}
})

# 4. Delete user entity
# NO API - Direct MongoDB operation:
db.user_entity.deleteOne({"_id": ObjectId(user_oid)})

# 5. Clean up audit logs (OPTIONAL - consider retention requirements)
# Access observability system and delete/anonymize user traces

# 6. Remove from backups (COMPLEX)
# Requires backup restore without user data or backup retention expiry
```

### Step 3: Verify Deletion
- Confirm user cannot authenticate
- Verify no personal data remains in queries
- Document deletion in compliance records (not in same system)

### Step 4: Notify User
- Confirm erasure completion
- Explain any retained data (legal obligations, audit requirements)
- Provide timeline for backup expiry if applicable

## 4. Restriction Request

**Timeline**: GDPR: 1 month, revDSG: 30 days

**🟡 Available via Permission Revocation:**

```bash
# Revoke all user permissions
# Admin interface or:
POST /api/v1/access/users/{user_oid}/revoke-all
```

**Effect:**
- User cannot access any resources
- Data is preserved (not deleted)
- Processing is suspended

**🚧 Not Implemented:**
- "Processing restricted" flag in database
- Automated system-wide restriction enforcement
- User-visible restriction status

## 5. Portability Request

**Timeline**: GDPR: 1 month, revDSG: N/A (limited requirement)

**🔴 No Automation:** Use same data compilation process as Access Request (Section 1)

**Additional Requirements:**
- Provide data in machine-readable format (JSON, CSV)
- Include only data "provided by the data subject" (user messages, uploads)
- Exclude derived data (AI responses, analytics)

## 6. Objection Request

**Timeline**: GDPR: Immediate, revDSG: Immediate

**🟡 Available via Permission Revocation:**
- Same process as Restriction (Section 4)
- Revoke permissions for specific processing activities
- Document objection grounds

## Automated Future Roadmap

**Planned Implementations:**

### Phase 1: Self-Service Data Access
- 🚧 User-facing DSAR portal
- 🚧 Automated data export API
- 🚧 Download personal data as JSON/CSV

### Phase 2: User Deletion API
- 🚧 Cascading user deletion endpoint
- 🚧 Automated cleanup across all entities
- 🚧 Thread deletion API exposure

### Phase 3: Advanced Features
- 🚧 Data portability API
- 🚧 Processing restriction flags
- 🚧 Consent management system

## Compliance Records

**Required Documentation:**
- Date of request received
- Type of request
- Verification method used
- Data provided/actions taken
- Date of completion
- User confirmation of receipt

**Storage:**
- Maintain separate compliance log (not in AI-Hub database)
- Retain for regulatory period (6+ years recommended)
- Do not store in same system as user data (survives deletion)

## Resources

- [GDPR Compliance](/platform/compliance/gdpr)
- [Swiss DSG](/platform/compliance/dsg)
- [Data Retention](/platform/compliance/data_retention)
- [Access Management](/platform/access_management)

---

:::info Questions
For assistance with DSAR procedures, contact your Data Protection Officer or legal counsel. This documentation describes technical procedures, not legal requirements.
:::
