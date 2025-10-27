---
title: Data subject access requests (DSAR)
index: 6
---

# Data subject access requests (DSAR)

Procedures for handling data subject rights requests under GDPR Article 15 and Swiss revDSG Article 25.

:::warning Manual procedures
DSAR handling is **largely manual**. Automated APIs are not yet implemented. Admins compile data using APIs and database queries.
:::

## Request types and status

| Right | GDPR | revDSG | Status | Response Time |
|-------|------|--------|--------|---------------|
| **Access** | Art. 15 | Art. 25 | 🟡 Manual | 1 month / 30 days |
| **Rectification** | Art. 16 | Art. 32 | ✅ API available | 1 month / 30 days |
| **Erasure** | Art. 17 | Art. 32 | 🔴 Manual | 1 month / 30 days |
| **Restriction** | Art. 18 | Art. 32 | 🟡 Via RBAC | Immediate |
| **Portability** | Art. 20 | Limited | 🔴 Manual | 1 month / 30 days |
| **Objection** | Art. 21 | Art. 32 | 🟡 Via RBAC | Immediate |

## 1. Access request (copy of data)

**Required data:**
- Personal data being processed
- Processing purposes, categories, recipients
- Retention period
- Rights information
- Source (if not collected from data subject)

**Process:**

### Verify identity
Use secure channel (authenticated session, HR verification, email confirmation)

### Collect data

**UserEntity:**
```bash
GET /api/v1/users/{user_oid}
# Returns: user profile, email, dashboard settings, roles
```

**ThreadEntity (conversations):**
```python
# NO API - Query MongoDB:
db.thread_entity.find({"participants.user_ids": user_oid})
```

**Messages (PersistedEvents):**
```python
# NO API - Query MongoDB:
db.persisted_agent_event_entity.find({"thread_id": {$in: thread_ids}})
db.persisted_process_event_entity.find({"thread_id": {$in: thread_ids}})
```

**Audit logs:**
```python
# Access observability system (SigNoz/OpenTelemetry)
# Query by user_oid for login, API calls, resource access
```

### Format and deliver
- Compile as PDF or JSON
- Explain data categories
- Respond within deadline
- Document request fulfillment

## 2. Rectification (correct data)

**✅ Available:**
```bash
PUT /api/v1/users/{user_oid}
{
  "name": "Corrected Name",
  "email": "corrected@email.com"
}
```

**Immutable data:** Thread messages and audit logs cannot be changed (audit trail requirement)

## 3. Erasure (delete data)

**⚠️ Assess exceptions first:**
- Legal obligation to retain? → **Cannot delete**
- Archiving/research purposes? → **Cannot delete**
- Legal claims pending? → **Cannot delete**
- Data no longer necessary? → **Must delete**

**🔴 Manual process required:**

```bash
# 1. Remove from threads (API available)
DELETE /api/v1/threads/{thread_id}/users/{user_oid}

# 2-4. Delete from MongoDB (NO API)
db.persisted_agent_event_entity.deleteMany({"thread_id": {$in: user_thread_ids}})
db.persisted_process_event_entity.deleteMany({"thread_id": {$in: user_thread_ids}})
db.user_entity.deleteOne({"_id": ObjectId(user_oid)})

# 5. Clean audit logs (consider retention requirements)
# 6. Backups (wait for expiry or restore without user data)
```

**Verify:** Confirm user cannot authenticate, no data remains in queries

## 4. Restriction (suspend processing)

**🟡 Via permission revocation:**
```bash
# Revoke all permissions via admin interface
# Effect: User cannot access resources, data preserved
```

**🚧 Missing:** "Processing restricted" database flag

## 5. Portability (export machine-readable)

**⚠️ Scope:** Only data "provided by the data subject" (user messages, uploads)

**NOT included:** AI responses, analytics, derived/inferred data

**⚠️ Conditions:** Only when processing based on consent/contract

**🔴 Manual:** Use same data collection as access request (Section 1), export as JSON/CSV

## 6. Objection (stop processing)

**🟡 Via permission revocation:** Same as restriction (Section 4)

**Customer:** Assess if overriding legitimate interests exist

## Compliance records

**Required documentation:**
- Request date & type
- Identity verification method
- Data provided / actions taken
- Completion date
- User confirmation

**Storage:** Maintain separate compliance log (not in platform), retain 6+ years

## Planned automation

**Phase 1:**
- 🚧 Self-service DSAR portal
- 🚧 Automated data export API

**Phase 2:**
- 🚧 User deletion API (cascading)
- 🚧 Thread deletion API endpoint

**Phase 3:**
- 🚧 Processing restriction flags
- 🚧 Consent management

## Resources

[GDPR Compliance](/platform/compliance/gdpr) | [Swiss DSG](/platform/compliance/dsg) | [Data Retention](/platform/compliance/data_retention)

---

:::info
This describes technical procedures, not legal requirements. Consult your DPO or legal counsel.
:::
