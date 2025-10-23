---
title: GDPR Compliance
index: 4
---

# GDPR Compliance

The AI-Hub platform provides technical and organizational measures to support GDPR compliance. **Customers remain data controllers** and are ultimately responsible for their own compliance.

:::warning Implementation Status
This document describes both **implemented features** and **planned capabilities**. Features marked as "🚧 Not Implemented" require additional development.
:::

## GDPR Principles & Platform Support

### 1. Lawfulness, Fairness, and Transparency

**✅ Implemented:**
- Complete audit trails ([Auditing](/platform/auditing))
- Source attribution for AI responses ([Source Attribution](/platform/chat_ui/source_attribution))
- Phoenix tracing for AI decision transparency

**Customer Responsibilities:**
- Document legal basis for processing
- Provide privacy notices to end users

### 2. Purpose Limitation

**✅ Implemented:**
- Multi-tenant architecture with data isolation
- Role-based access control (RBAC) ([Access Management](/platform/access_management))
- Namespace isolation for knowledge bases ([Knowledge Namespaces](/platform/knowledges/namespaces))

### 3. Data Minimization

**✅ Implemented:**
- Configurable retention policies ([Data Retention](/platform/compliance/data_retention))
- Granular RBAC permissions

**🚧 Not Implemented:**
- Automated anonymization for prompts/responses (planned)

### 4. Accuracy

**✅ Implemented:**
- Version control for knowledge base content
- Update tracking for documents

**Customer Responsibilities:**
- Maintain knowledge base accuracy
- Respond to correction requests

### 5. Storage Limitation

**✅ Implemented:**
- Automatic expiration: 30-day default for ephemeral data (Redis, NATS)
- Configurable retention for permanent storage (MongoDB)
- Backup and archival ([Backup and Recovery](/platform/deployment_guide/backup_and_recovery))

**Customer Responsibilities:**
- Configure appropriate retention periods
- Implement lifecycle policies for long-term data

### 6. Integrity and Confidentiality (Security)

**✅ Implemented:**
- TLS/SSL encryption ([Data Encryption](/platform/security/data_encryption))
- OAuth 2.0, OIDC, SAML authentication ([Authentication](/platform/security/authentication))
- Container security ([Container Security](/platform/security/container_security))
- Input validation ([Input Validation](/platform/security/input_validation))

**Customer Responsibilities:**
- Configure MFA and strong authentication
- Monitor security logs
- Review access permissions regularly

### 7. Accountability

**✅ Implemented:**
- Comprehensive logging and auditing
- Phoenix tracing for AI decisions

**Customer Responsibilities:**
- Maintain Records of Processing Activities (ROPA)
- Conduct Data Protection Impact Assessments (DPIAs)
- Designate Data Protection Officer (DPO) if required

## Data Subject Rights

### Right of Access (Article 15)

**✅ Implemented:**
- User profile retrieval API (`GET /api/v1/users/me`)
- Audit log access for administrators

**🚧 Not Implemented:**
- Comprehensive data export for all user data
- Self-service DSAR portal

**Current Procedure:**
1. User requests access via support channel
2. Admin uses API to retrieve user profile and audit logs
3. Manual compilation of data from different sources
4. Provide data to user in readable format

### Right to Rectification (Article 16)

**✅ Implemented:**
- Admin interfaces to update user profile data
- Knowledge base update workflows

**Procedure:**
1. Verify requestor identity
2. Locate data using admin API
3. Update through admin interface
4. Correction logged in audit trail

### Right to Erasure (Article 17)

**✅ Implemented:**
- Remove user from specific threads (`DELETE /api/v1/threads/{thread_id}/users/{user_id}`)
- Automatic ephemeral data deletion (30-day TTL)

**🚧 Not Implemented:**
- User-level deletion API
- Cascading deletion across all platform components
- Exposed thread deletion API endpoint (service exists but not exposed)

**Current Limitation:**
No automated way to delete all user data. Manual deletion required across:
- UserEntity (MongoDB)
- ThreadEntity where user is participant
- PersistedAgentEventEntity / PersistedProcessEventEntity
- Audit logs (consider retention requirements)
- Backup systems

### Right to Restriction of Processing (Article 18)

**✅ Implemented:**
- Account suspension via RBAC permission revocation

**🚧 Not Implemented:**
- "Processing restricted" flag in database
- Automated restriction enforcement

**Current Procedure:**
1. Verify identity and grounds for restriction
2. Revoke user permissions via access management
3. Document restriction in audit logs

### Right to Data Portability (Article 20)

**🚧 Not Implemented:**
- Automated data export in machine-readable format
- API for bulk data retrieval

**Current Limitation:**
Manual data compilation required using admin APIs.

### Right to Object (Article 21)

**✅ Implemented:**
- Audit logging can be disabled per-user (configuration)

**🚧 Not Implemented:**
- Granular opt-out mechanisms
- Consent management system

### Rights Related to Automated Decision-Making (Article 22)

**✅ Implemented:**
- Human-in-the-loop workflows ([Human-in-the-Loop](/platform/agents/agent_workflows/human_in_the_loop))
- Explainability through source attribution and Phoenix tracing

**Customer Responsibilities:**
- Identify automated decisions with legal/significant effects
- Configure human review for such decisions

## Technical and Organizational Measures

**✅ Privacy by Design:**
- Minimal data collection by default
- TLS/SSL encryption enabled by default
- Default-deny RBAC permissions
- Automatic audit logging
- 30-day ephemeral data retention by default

**✅ Security Measures:**
- See [Authentication](/platform/security/authentication), [Data Encryption](/platform/security/data_encryption), [Input Validation](/platform/security/input_validation), [Container Security](/platform/security/container_security)

**Data Processing Agreements (DPA):**
- Required for LLM providers and sub-processors
- Customer responsibility to execute and maintain

## International Data Transfers

**Swiss Hosting Advantage:**
- Switzerland has EU adequacy decision
- On-premise deployment avoids international transfers
- Swiss cloud hosting recommended for GDPR compliance

**For other jurisdictions:**
- Use Standard Contractual Clauses (SCCs)
- Conduct transfer impact assessments
- See [Deployment Options](/platform/deployment_guide/deployment_options)

## Compliance Checklists

**Initial Setup:**
- [ ] Conduct DPIA for AI-Hub deployment
- [ ] Document legal basis for processing
- [ ] Configure authentication (OAuth/OIDC/SAML with MFA)
- [ ] Set up RBAC with least privilege
- [ ] Configure data retention policies
- [ ] Execute DPAs with LLM providers
- [ ] Create user privacy notice
- [ ] Designate DPO if required

**Ongoing:**
- [ ] Review ROPA quarterly
- [ ] Audit access permissions monthly
- [ ] Review knowledge bases for outdated data
- [ ] Test DSAR procedures (when implemented)
- [ ] Monitor security logs
- [ ] Annual GDPR compliance review

## Data Breach Procedures

**Breach must be reported within 72 hours** to supervisory authority if high risk to individuals.

**Response Steps:**
1. **Detect and Contain** (immediate): Identify scope, contain breach, preserve evidence
2. **Assess** (24 hours): Determine personal data involvement, assess risk
3. **Notify Authority** (72 hours): Report to supervisory authority if required
4. **Notify Individuals** (if high risk): Direct notification in plain language
5. **Investigate** (ongoing): Root cause analysis, implement fixes
6. **Document** (required): Record all breaches and remediation

**Platform Tools:**
- Audit logs for breach investigation
- User access reports
- Monitoring and alerting
- Backup for recovery

## Known Gaps & Roadmap

**High Priority (Required for Full Compliance):**
- 🚧 User-level deletion API with cascading delete
- 🚧 Comprehensive DSAR data export functionality
- 🚧 Data portability automation
- 🚧 Exposed thread deletion API endpoint

**Medium Priority:**
- 🚧 Processing restriction flags and enforcement
- 🚧 Granular consent management
- 🚧 Self-service data access portal
- 🚧 Automated anonymization

## Resources

- **GDPR Full Text**: [https://gdpr-info.eu/](https://gdpr-info.eu/)
- **EDPB Guidelines**: [https://edpb.europa.eu/](https://edpb.europa.eu/)
- **Swiss FDPIC**: [https://www.edoeb.admin.ch/](https://www.edoeb.admin.ch/)

**Related Documentation:**
- [Swiss DSG](/platform/compliance/dsg)
- [Data Retention](/platform/compliance/data_retention)
- [AI Act Compliance](/platform/compliance/ai_act)

---

:::info Legal Disclaimer
This documentation provides technical guidance but is not legal advice. Consult your Data Protection Officer or legal counsel for compliance questions.
:::
