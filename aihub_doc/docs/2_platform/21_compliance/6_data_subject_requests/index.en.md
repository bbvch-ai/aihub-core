---
title: Data Subject Access Requests (DSAR)
---

# Data subject access requests

Data subjects have rights under GDPR (Articles 15-21) and Swiss revDSG (Articles 25, 32) to access, correct, delete, and
control their personal data. This section explains what the platform supports for these rights.

## Response times

Organizations must respond to data subject requests within one month under GDPR or 30 days under Swiss revDSG. Some
requests can be processed immediately, while others require manual data compilation.

## Access requests

Data subjects can request copies of their personal data, including processing purposes, categories, recipients,
retention periods, and data sources. The platform stores this information in user profiles, conversation threads, and
audit logs. Organizations verify the requester's identity before providing data.

## Rectification

Data subjects can request corrections to inaccurate data. Administrators can update user profiles through the platform's
API. Thread messages and audit logs remain immutable to preserve audit trails.

## Erasure

Data subjects can request deletion when data is no longer necessary, consent is withdrawn, or processing is unlawful.
Exceptions apply for legal obligations, archiving, research, or legal claims. The platform supports removing users from
threads. Ephemeral data deletes automatically after 30 days.

## Restriction

Data subjects can request suspension of processing while verifying data accuracy or assessing objections. Administrators
can suspend accounts through the platform's access control system, preventing resource access while preserving data.

## Portability

Data subjects can request their data in machine-readable format. This applies only to data the subject provided
directly, like messages and uploads, not AI-generated responses, analytics, or derived data. The right applies when
processing is based on consent or contract and carried out by automated means.

## Objection

Data subjects can object to processing based on legitimate interests. Organizations revoke permissions through the
platform's access control to stop processing. Organizations must assess whether overriding legitimate interests exist.

## Related documentation

- [GDPR Compliance](../2_gdpr/)
- [Swiss DSG](../3_dsg/)
- [Data Retention](../1_data_retention/)

---

:::info Legal disclaimer
This is technical documentation, not legal advice. Consult your data protection officer or legal counsel.
:::
