---
title: Swiss Data Protection Act (DSG)
---

# Swiss Data Protection Act (revDSG)

The revised Swiss Federal Act on Data Protection (revDSG/FADP) came into force on September 1, 2023. The revision was
designed to align with EU data protection standards while maintaining Swiss-specific approaches to certain requirements.

:::info
See [GDPR Compliance](../2_gdpr/) for shared requirements. This document covers Swiss-specific differences only.
:::

:::warning When GDPR also applies
Swiss organizations must comply with both revDSG and GDPR when offering goods/services to EU residents or monitoring EU
individuals' behavior. See [GDPR Applicability](../2_gdpr/#applicability-to-swiss-organizations).
:::

## Key differences from GDPR

| Aspect              | revDSG                                                              | GDPR                                                               |
| ------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Fines               | Up to CHF 250K on individuals (not companies)                       | Up to €20M or 4% revenue on companies                              |
| DPO                 | Not required                                                        | Often mandatory                                                    |
| Legal basis         | No explicit legal basis required (different approach)               | Explicit legal basis mandatory (Art. 6)                            |
| Breach notification | "As quickly as possible" if high risk (no statutory deadline)       | Without undue delay, where feasible within 72 hours if risk exists |
| Sensitive data      | Includes administrative/criminal proceedings + social security data | 9 special categories                                               |
| Scope               | Only natural persons (legal entities excluded since 2023)           | Only natural persons                                               |

## revDSG-specific requirements

### High-risk profiling

The revDSG requires oversight for automated evaluation of personal aspects like risk assessment and behavioral
prediction. The platform provides human-in-the-loop capabilities, Langfuse tracing, and source attribution to support
this requirement. Organizations must identify high-risk profiling activities, conduct data protection impact
assessments, and implement appropriate human oversight.

### Data processing register

Organizations must maintain a register of processing activities. This is an organizational requirement that doesn't need
platform features.

### Data subject rights

Data subject rights work the same as GDPR with minor differences. Response time is 30 days rather than 1 month. The
"right to be forgotten" terminology isn't used, but the erasure right exists. Portability requirements are simpler than
GDPR. See [GDPR documentation](../2_gdpr/#data-subject-rights) for details on how the platform supports these rights.

### Data breach notification

The revDSG requires notifying the Federal Data Protection and Information Commissioner "as quickly as possible" when a
breach is likely to result in high risk to personality rights or fundamental rights (Article 24). Unlike GDPR, Swiss law
does not specify a statutory deadline. However, legal practice generally interprets this as aligning with GDPR's 72-hour
expectation. The threshold for notification (high risk) is stricter than GDPR's general risk threshold. The platform
provides audit logs, monitoring, and alerting to support breach investigation and notification.

### Privacy by design

The revDSG now explicitly requires privacy by design. The platform implements this through mandatory TLS/SSL encryption,
default-deny access control, 30-day automatic deletion of ephemeral data, and audit logging.

## Swiss hosting and adequacy decision

Switzerland has an EU adequacy decision (confirmed January 2024), allowing personal data to flow freely between the EU
and Switzerland without additional safeguards. This means Swiss hosting simplifies compliance for organizations subject
to both GDPR and revDSG requirements.

For pure Swiss operations, hosting data in Switzerland also avoids international transfer requirements under the revDSG.
The platform supports on-premise and Swiss cloud deployment. See
[Deployment Options](../../3_deployment_guide/1_deployment_options/) and
[GDPR International Transfers](../2_gdpr/#international-data-transfers).

## Data transfers

Data transfers require adequate protection in the destination country, appropriate safeguards like standard contractual
clauses, or explicit consent. Swiss hosting avoids these requirements. Organizations can also use Swiss or EU LLM
providers through LiteLLM.

## Related documentation

- [GDPR](../2_gdpr/)
- [DSAR](../6_data_subject_requests/)
- [Data Retention](../1_data_retention/)
- [FDPIC](https://www.edoeb.admin.ch/)
- [revDSG Text](https://www.admin.ch/opc/en/classified-compilation/19920153/)

---

:::info Legal disclaimer
This is technical documentation, not legal advice. Consult legal counsel or the Federal Data Protection and Information
Commissioner.
:::
