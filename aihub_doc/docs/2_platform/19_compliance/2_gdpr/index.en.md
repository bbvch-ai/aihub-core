---
title: GDPR Compliance
index: 4
---

# GDPR compliance

The platform provides technical measures to support GDPR compliance. **Customers are data controllers** and responsible for their own compliance.

:::warning Implementation Status
✅ = Implemented | 🚧 = Not Implemented
:::

## GDPR principles

### Lawfulness, transparency, and accountability
**✅ Implemented:** Audit trails, source attribution, Phoenix tracing
**Customer:** Document a legal basis, provide privacy notices, maintain ROPA, conduct DPIAs

### Purpose limitation and data minimization
**✅ Implemented:** Multi-tenant isolation, RBAC, namespace isolation, configurable retention
**Customer:** Define processing purposes, configure retention, prune unused data

### Accuracy and storage limitation
**✅ Implemented:** Version control, 30-day auto-deletion (ephemeral), configurable retention (permanent)
**Customer:** Maintain data accuracy, configure appropriate retention periods

### Security and integrity
**✅ Implemented:** TLS/SSL, OAuth/OIDC/SAML, RBAC, container security, input validation
**Customer:** Enable MFA, monitor logs, review permissions

## Data subject rights

### Right of access (Art. 15)
**What's required:** Copy of personal data, processing details, recipients, retention period, source (if collected from others)

**✅ Implemented:**
- User profile API (`GET /api/v1/users/me`)
- Audit log access (admin)

**🚧 Missing:** Automated export of all user data across all entities

**Workaround:** Admin manually compiles from UserEntity, ThreadEntity, audit logs

### Right to rectification (Art. 16)
**What's required:** Correct inaccurate data

**✅ Implemented:** Admin can update user profile via API

**Note:** Thread messages and audit logs are immutable (audit trail requirement)

### Right to erasure (Art. 17)
**What's required:** Delete data when no longer necessary, consent withdrawn, or unlawfully processed

**⚠️ Exceptions apply:** Not required for legal obligations, archiving, research, or legal claims

**✅ Implemented:**
- Remove user from threads (`DELETE /api/v1/threads/{thread_id}/users/{user_id}`)
- 30-day auto-deletion (ephemeral data)

**🚧 Missing:** User-level deletion API with cascading delete

**Workaround:** Admin manually deletes from UserEntity, ThreadEntity, PersistedEvents

### Right to data portability (Art. 20)
**What's required:** Provide data "provided by the data subject" in machine-readable format

**⚠️ Scope:** Only user-provided data (messages, uploads). **Does NOT include** AI responses, analytics, or derived data.

**⚠️ Conditions:** Only when processing based on consent/contract and automated

**🚧 Missing:** Automated export API

**Workaround:** Admin manually exports user messages and uploads as JSON/CSV

### Right to restriction (Art. 18)
**What's required:** Suspend processing while verifying accuracy or assessing objection

**✅ Implemented:** Account suspension via RBAC revocation

**🚧 Missing:** "Processing restricted" database flag

### Right to object (Art. 21)
**What's required:** Stop processing based on legitimate interests

**✅ Implemented:** Permission revocation via RBAC

## Technical measures

**Privacy by design (default settings):**
- TLS/SSL encryption mandatory
- Default-deny RBAC
- Automatic audit logging
- 30-day ephemeral data deletion
- Minimal data collection

**Security:** See [Authentication](/platform/security/authentication), [Encryption](/platform/security/data_encryption), [Access Control](/platform/access_management)

**Data Transfers:** Swiss hosting recommended (EU adequacy decision). Use SCCs for other countries. See [Deployment Options](/platform/deployment_guide/deployment_options).

## Data breach notification

**Requirement:** Notify supervisory authority within **72 hours** if risk to data subjects' rights exists

**✅ Platform tools:**
- Audit logs for investigation
- User access reports
- Monitoring and alerting
- Backup and recovery

**Customer responsibility:** Assess risk, notify authority, notify individuals (if high risk), document breach

## Compliance checklist

**Setup:**
- [ ] DPIA for AI processing
- [ ] Document legal basis
- [ ] Configure authentication (MFA)
- [ ] Configure RBAC (least privilege)
- [ ] Set retention policies
- [ ] Execute DPAs with LLM providers
- [ ] Create a privacy notice
- [ ] Designate DPO (if required)

**Ongoing:**
- [ ] Review ROPA quarterly
- [ ] Audit permissions monthly
- [ ] Prune knowledge bases
- [ ] Monitor security logs
- [ ] Annual compliance review

## Known gaps

**Required for full compliance:**
- 🚧 User deletion API (cascading)
- 🚧 Automated DSAR data export
- 🚧 Data portability API

**Optional enhancements:**
- 🚧 Processing restriction flags
- 🚧 Consent management system
- 🚧 Self-service DSAR portal

## Resources

- GDPR Full Text: [gdpr-info.eu](https://gdpr-info.eu/)
- EDPB Guidelines: [edpb.europa.eu](https://edpb.europa.eu/)

**Related:** [Swiss DSG](/platform/compliance/dsg) | [DSAR Procedures](/platform/compliance/data_subject_requests) | [Data Retention](/platform/compliance/data_retention)

---

:::info Legal Disclaimer
This is technical guidance, not legal advice. Consult your DPO or legal counsel.
:::
