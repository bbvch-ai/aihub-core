---
title: Swiss Data Protection Act (DSG)
index: 3
---

# Swiss Data Protection Act (revDSG)

The revised Swiss Federal Act on Data Protection (revDSG/FADP) came into force on September 1, 2023. It's 80-90% aligned with GDPR.

:::info
See [GDPR Compliance](/platform/compliance/gdpr) for shared requirements. This document covers Swiss-specific differences only.
:::

## Key differences from GDPR

| Aspect | revDSG | GDPR |
|--------|---------|------|
| **Fines** | Up to CHF 250K on **individuals** (not companies) | Up to €20M or 4% revenue on companies |
| **DPO** | Not required | Often mandatory |
| **Legal basis** | No explicit legal basis required (different approach) | Explicit legal basis mandatory (Art. 6) |
| **Breach notification** | "As quickly as possible" if high risk (no deadline) | Within 72 hours if risk exists |
| **Sensitive data** | Includes administrative/criminal proceedings + social security data | 9 special categories |
| **Scope** | Only natural persons (legal entities excluded since 2023) | Only natural persons |

## revDSG-specific requirements

### High-risk profiling
The revDSG requires oversight for automated evaluation of personal aspects like risk assessment and behavioral prediction. The platform provides human-in-the-loop capabilities, Phoenix tracing, and source attribution to support this requirement. Organizations must identify high-risk profiling activities, conduct data protection impact assessments, and implement appropriate human oversight.

### Data processing register
Organizations must maintain a register of processing activities. This is an organizational requirement that doesn't need platform features.

### Data subject rights
Data subject rights work the same as GDPR with minor differences. Response time is 30 days rather than 1 month. The "right to be forgotten" terminology isn't used, but the erasure right exists. Portability requirements are simpler than GDPR. See [GDPR documentation](/platform/compliance/gdpr#data-subject-rights) for details on how the platform supports these rights.

### Data breach notification
The revDSG requires notifying the Federal Data Protection and Information Commissioner "as quickly as possible" when a breach presents high risk. Unlike GDPR, there's no 72-hour deadline. The platform provides audit logs, monitoring, and alerting to support breach investigation and notification.

### Privacy by design
The revDSG now explicitly requires privacy by design. The platform implements this through mandatory TLS/SSL encryption, default-deny access control, 30-day automatic deletion of ephemeral data, and audit logging.

## Swiss hosting

Swiss hosting keeps data in Switzerland, avoiding international transfer issues. Switzerland has an EU adequacy decision, which simplifies mixed EU and Swiss compliance. The platform supports on-premise and Swiss cloud deployment. See [Deployment Options](/platform/deployment_guide/deployment_options).

## Data transfers

Data transfers require adequate protection in the destination country, appropriate safeguards like standard contractual clauses, or explicit consent. Swiss hosting avoids these requirements. Organizations can also use Swiss or EU LLM providers through LiteLLM.

## Related documentation

- [GDPR](/platform/compliance/gdpr)
- [DSAR](/platform/compliance/data_subject_requests)
- [Data Retention](/platform/compliance/data_retention)
- [FDPIC](https://www.edoeb.admin.ch/)
- [revDSG Text](https://www.admin.ch/opc/en/classified-compilation/19920153/)

---

:::info Legal disclaimer
This is technical documentation, not legal advice. Consult legal counsel or the Federal Data Protection and Information Commissioner.
:::
