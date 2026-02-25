---
title: GDPR Compliance
---

# GDPR compliance

The platform provides technical measures to support GDPR compliance. Organizations using the platform act as data
controllers and remain responsible for their own compliance.

## Applicability to Swiss organizations

GDPR applies to Swiss organizations when processing personal data of individuals in the EU if the processing relates to:

- Offering goods or services to EU residents (regardless of payment)
- Monitoring behavior of individuals in the EU

Organizations must comply with GDPR requirements even without an EU establishment when these conditions are met.

## Legal basis for processing

Article 6 GDPR requires a legal basis for all personal data processing. At least one of the following must apply:

- Consent: The data subject has given clear consent for specific purposes
- Contract: Processing is necessary for contract performance or pre-contractual measures
- Legal obligation: Processing is necessary to comply with legal requirements
- Vital interests: Processing is necessary to protect life or physical integrity
- Public task: Processing is necessary for tasks in the public interest or official authority
- Legitimate interests: Processing is necessary for legitimate interests, except where overridden by data subject rights
  (not available for public authorities)

Organizations must document their legal basis and inform data subjects accordingly.

## GDPR principles

Article 5 GDPR establishes six core principles for processing personal data, plus an accountability requirement:

### Lawfulness, fairness and transparency

The platform provides audit trails, source attribution, and Langfuse tracing for transparency. Organizations must
document their legal basis for processing, provide privacy notices, maintain records of processing activities, and
conduct data protection impact assessments. Processing must be lawful, fair, and transparent to data subjects.

### Purpose limitation

Data must be collected for specified, explicit and legitimate purposes and not further processed in a manner
incompatible with those purposes. Organizations should define clear purposes for each data collection and processing
activity.

### Data minimisation

Multi-tenant isolation, role-based access control, and namespace isolation restrict data access to what is necessary.
Data collected must be adequate, relevant, and limited to what is necessary for the defined purposes.

### Accuracy

Version control tracks data changes to maintain accuracy. Organizations must ensure personal data is accurate and, where
necessary, kept up to date. Inaccurate data must be erased or rectified without delay.

### Storage limitation

Ephemeral data expires automatically after 30 days. Organizations configure retention periods for permanent storage.
Data must be kept in a form that permits identification of data subjects for no longer than necessary for the processing
purposes.

### Integrity and confidentiality

The platform requires TLS/SSL encryption and supports OAuth, OIDC, and SAML authentication. Role-based access control,
container security, and input validation protect data integrity. Processing must ensure appropriate security, including
protection against unauthorized or unlawful processing and accidental loss, destruction, or damage.

### Accountability

Controllers must be able to demonstrate compliance with all principles. The platform supports this through comprehensive
audit logging, documentation capabilities, and traceability features.

## Data subject rights

### Right of access (Art. 15)

Users can request copies of their personal data, processing details, recipients, retention periods, and data sources.
The platform provides a user profile API and audit log access.

### Right to rectification (Art. 16)

Users can request corrections to inaccurate data. Administrators can update user profiles through the API. Thread
messages and audit logs remain immutable to preserve audit trails.

### Right to erasure (Art. 17)

Users can request deletion of data when it's no longer necessary, consent is withdrawn, or processing is unlawful. The
platform supports removing users from threads, and ephemeral data deletes automatically after 30 days.

Exceptions apply when processing is necessary for:

- Freedom of expression and information
- Compliance with legal obligations or tasks in the public interest
- Public health reasons
- Archiving, scientific or historical research, or statistical purposes (when deletion would make these impossible or
  seriously impair them)
- Establishment, exercise, or defence of legal claims

### Right to data portability (Art. 20)

Users can request their data in machine-readable format. This applies to data the user provided directly (messages,
uploads), not AI-generated responses, analytics, or derived data. The right applies only when processing is based on
consent or contract and carried out by automated means.

### Right to restriction (Art. 18)

Users can request suspension of processing while verifying data accuracy or assessing objections. Administrators can
suspend accounts through role-based access control.

### Right to object (Art. 21)

Users can object to processing based on legitimate interests. Permission revocation through role-based access control
stops processing.

## Technical measures

The platform implements privacy by design with mandatory TLS/SSL encryption, default-deny access control, automatic
audit logging, 30-day ephemeral data deletion, and minimal data collection. See
[Authentication](../../20_security/1_authentication/), [Encryption](../../20_security/5_data_encryption/), and
[Access Control](../../11_access_management/) for details.

## International data transfers

### EU adequacy decision for Switzerland

Switzerland has an EU adequacy decision (confirmed January 2024), meaning the European Commission recognizes Swiss data
protection law as providing an adequate level of protection. This allows personal data to flow freely from the EU to
Switzerland without additional safeguards.

For organizations hosting in Switzerland, this simplifies compliance with both GDPR and Swiss DSG requirements. See
[Deployment Options](../../3_deployment_guide/1_deployment_options/) for hosting configurations.

### Transfers to other countries

Transfers to countries without an adequacy decision require appropriate safeguards:

- Standard contractual clauses (SCCs) approved by the European Commission
- Binding corporate rules (BCRs)
- Approved codes of conduct or certification mechanisms
- Specific derogations (consent, contract necessity, vital interests, etc.)

## Data breach notification

Article 33 GDPR requires notifying the supervisory authority **without undue delay and, where feasible, not later than
72 hours** after becoming aware of a breach that is likely to result in a risk to individuals' rights and freedoms. If
notification is not made within 72 hours, reasons for the delay must be provided. Notification is not required if the
breach is unlikely to result in a risk.

The notification must include the nature of the breach, affected data subjects, likely consequences, and remedial
measures taken. Data subjects must be informed directly (Article 34) when the breach is likely to result in a high risk
to their rights and freedoms.

The platform provides audit logs, user access reports, monitoring, alerting, and backup capabilities to support breach
investigation, documentation, and response.

## Related documentation

- [Swiss DSG](../3_dsg/)
- [DSAR Procedures](../6_data_subject_requests/)
- [Data Retention](../1_data_retention/)
- [GDPR Full Text](https://gdpr-info.eu/)
- [EDPB Guidelines](https://edpb.europa.eu/)

______________________________________________________________________

:::info Legal disclaimer
This is technical documentation, not legal advice. Consult your data protection officer or legal counsel.
:::
