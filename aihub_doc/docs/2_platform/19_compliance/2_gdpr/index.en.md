---
title: GDPR Compliance
index: 2
---

# GDPR compliance

The platform provides technical measures to support GDPR compliance. Organizations using the platform act as data controllers and remain responsible for their own compliance.

## GDPR principles

Article 5 GDPR establishes six core principles for processing personal data, plus an accountability requirement:

### Lawfulness, fairness and transparency
The platform provides audit trails, source attribution, and Phoenix tracing for transparency. Organizations must document their legal basis for processing, provide privacy notices, maintain records of processing activities, and conduct data protection impact assessments. Processing must be lawful, fair, and transparent to data subjects.

### Purpose limitation
Data must be collected for specified, explicit and legitimate purposes and not further processed in a manner incompatible with those purposes. Organizations should define clear purposes for each data collection and processing activity.

### Data minimisation
Multi-tenant isolation, role-based access control, and namespace isolation restrict data access to what is necessary. Data collected must be adequate, relevant, and limited to what is necessary for the defined purposes.

### Accuracy
Version control tracks data changes to maintain accuracy. Organizations must ensure personal data is accurate and, where necessary, kept up to date. Inaccurate data must be erased or rectified without delay.

### Storage limitation
Ephemeral data expires automatically after 30 days. Organizations configure retention periods for permanent storage. Data must be kept in a form that permits identification of data subjects for no longer than necessary for the processing purposes.

### Integrity and confidentiality
The platform requires TLS/SSL encryption and supports OAuth, OIDC, and SAML authentication. Role-based access control, container security, and input validation protect data integrity. Processing must ensure appropriate security, including protection against unauthorized or unlawful processing and accidental loss, destruction, or damage.

### Accountability
Controllers must be able to demonstrate compliance with all principles. The platform supports this through comprehensive audit logging, documentation capabilities, and traceability features.

## Data subject rights

### Right of access (Art. 15)
Users can request copies of their personal data, processing details, recipients, retention periods, and data sources. The platform provides a user profile API and audit log access.

### Right to rectification (Art. 16)
Users can request corrections to inaccurate data. Administrators can update user profiles through the API. Thread messages and audit logs remain immutable to preserve audit trails.

### Right to erasure (Art. 17)
Users can request deletion of data when it's no longer necessary, consent is withdrawn, or processing is unlawful. The platform supports removing users from threads, and ephemeral data deletes automatically after 30 days.

Exceptions apply when processing is necessary for:
- Freedom of expression and information
- Compliance with legal obligations or tasks in the public interest
- Public health reasons
- Archiving, scientific or historical research, or statistical purposes (when deletion would make these impossible or seriously impair them)
- Establishment, exercise, or defence of legal claims

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

Article 33 GDPR requires notifying the supervisory authority without undue delay and, where feasible, not later than 72 hours after becoming aware of a breach, unless the breach is unlikely to result in a risk to the rights and freedoms of individuals. The notification must include the nature of the breach, affected data subjects, likely consequences, and remedial measures taken.

The platform provides audit logs, user access reports, monitoring, alerting, and backup capabilities to support breach investigation, documentation, and response.

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
