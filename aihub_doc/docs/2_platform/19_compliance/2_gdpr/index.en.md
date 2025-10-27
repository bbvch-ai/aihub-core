---
title: GDPR Compliance
index: 4
---

# GDPR compliance

The platform provides technical measures to support GDPR compliance. Organizations using the platform act as data controllers and remain responsible for their own compliance.

## GDPR principles

### Lawfulness, transparency, and accountability
The platform provides audit trails, source attribution, and Phoenix tracing for transparency. Organizations must document their legal basis, provide privacy notices, maintain records of processing activities, and conduct data protection impact assessments.

### Purpose limitation and data minimization
Multi-tenant isolation, role-based access control, and namespace isolation restrict data access. Configurable retention policies allow organizations to limit data storage duration.

### Accuracy and storage limitation
Version control tracks data changes. Ephemeral data expires automatically after 30 days. Organizations configure retention periods for permanent storage and maintain data accuracy.

### Security and integrity
The platform requires TLS/SSL encryption and supports OAuth, OIDC, and SAML authentication. Role-based access control, container security, and input validation protect data integrity.

## Data subject rights

### Right of access (Art. 15)
Users can request copies of their personal data, processing details, recipients, retention periods, and data sources. The platform provides a user profile API and audit log access.

### Right to rectification (Art. 16)
Users can request corrections to inaccurate data. Administrators can update user profiles through the API. Thread messages and audit logs remain immutable to preserve audit trails.

### Right to erasure (Art. 17)
Users can request deletion of data when it's no longer necessary, consent is withdrawn, or processing is unlawful. Exceptions apply for legal obligations, archiving, research, or legal claims. The platform supports removing users from threads, and ephemeral data deletes automatically after 30 days.

### Right to data portability (Art. 20)
Users can request their data in machine-readable format. This applies to data the user provided directly (messages, uploads), not AI-generated responses, analytics, or derived data. The right applies only when processing is based on consent or contract and carried out by automated means.

### Right to restriction (Art. 18)
Users can request suspension of processing while verifying data accuracy or assessing objections. Administrators can suspend accounts through role-based access control.

### Right to object (Art. 21)
Users can object to processing based on legitimate interests. Permission revocation through role-based access control stops processing.

## Technical measures

The platform implements privacy by design with mandatory TLS/SSL encryption, default-deny access control, automatic audit logging, 30-day ephemeral data deletion, and minimal data collection. See [Authentication](/platform/security/authentication), [Encryption](/platform/security/data_encryption), and [Access Control](/platform/access_management) for details.

For data transfers, Swiss hosting is recommended (Switzerland has an EU adequacy decision). Other locations require standard contractual clauses. See [Deployment Options](/platform/deployment_guide/deployment_options).

## Data breach notification

GDPR requires notifying the supervisory authority within 72 hours if a breach risks data subjects' rights. The platform provides audit logs, user access reports, monitoring, alerting, and backup capabilities to support breach investigation and response.

## Related documentation

- [Swiss DSG](/platform/compliance/dsg)
- [DSAR Procedures](/platform/compliance/data_subject_requests)
- [Data Retention](/platform/compliance/data_retention)
- [GDPR Full Text](https://gdpr-info.eu/)
- [EDPB Guidelines](https://edpb.europa.eu/)

---

:::info Legal disclaimer
This is technical documentation, not legal advice. Consult your data protection officer or legal counsel.
:::
