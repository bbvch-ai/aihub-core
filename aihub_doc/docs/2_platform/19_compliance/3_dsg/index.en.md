---
title: Swiss Data Protection Act (DSG)
index: 3
---

# Swiss Data Protection Act (revDSG)

The revised Swiss Federal Act on Data Protection (revDSG/FADP) came into force September 1, 2023. It's 80-90% aligned with GDPR.

:::info
See [GDPR Compliance](/platform/compliance/gdpr) for shared requirements. This document covers Swiss-specific differences only.
:::

## Key Differences from GDPR

| Aspect | revDSG | GDPR |
|--------|---------|------|
| **Fines** | Up to CHF 250K on **individuals** (not companies) | Up to €20M or 4% revenue on companies |
| **DPO** | Not required | Often mandatory |
| **Legal Basis** | No explicit legal basis required (different approach) | Explicit legal basis mandatory (Art. 6) |
| **Breach Notification** | "As quickly as possible" if high risk (no deadline) | Within 72 hours if risk exists |
| **Sensitive Data** | Includes administrative/criminal proceedings + social security data | 9 special categories |
| **Scope** | Only natural persons (legal entities excluded since 2023) | Only natural persons |

## revDSG-Specific Requirements

### 1. High-Risk Profiling
**Definition:** Automated evaluation of personal aspects (risk assessment, behavioral prediction)

**✅ Implemented:** Human-in-the-loop, Phoenix tracing, source attribution

**Customer:** Identify high-risk profiling, conduct DPIA, implement human oversight

### 2. Data Processing Register
**Customer Responsibility:** Maintain register of processing activities (no AI-Hub feature needed)

### 3. Data Subject Rights
**Same as GDPR** with minor differences:
- Response time: **30 days** (vs. GDPR's 1 month)
- No "right to be forgotten" terminology (but erasure right exists)
- Simpler portability requirements

**Implementation:** Same gaps as GDPR (see [GDPR doc](/platform/compliance/gdpr#data-subject-rights))

### 4. Data Breach Notification
**Requirement:** Notify FDPIC (Federal Data Protection and Information Commissioner) "as quickly as possible" **only if high risk**

**No 72-hour deadline** unlike GDPR

**✅ Platform Tools:** Audit logs, monitoring, alerting

### 5. Privacy by Design
Now explicitly required (previously implicit)

**✅ Implemented:** TLS/SSL default, default-deny RBAC, 30-day auto-deletion, audit logging

## Swiss Hosting

**Advantages:**
- Data stays in Switzerland
- No international transfer issues
- Switzerland has EU adequacy decision (helps with mixed EU/CH compliance)

**✅ Supported:** On-premise and Swiss cloud options (see [Deployment Options](/platform/deployment_guide/deployment_options))

## Data Transfers
**Requirement:** Adequate protection in destination country OR appropriate safeguards (SCCs) OR explicit consent

**Recommendation:** Swiss hosting to avoid transfers, or use Swiss/EU LLM providers via LiteLLM

## Compliance Checklist

**revDSG-Specific:**
- [ ] DPIA for high-risk profiling
- [ ] Data processing register
- [ ] FDPIC breach notification procedure
- [ ] Swiss hosting or SCCs documentation

**Same as GDPR:** See [GDPR checklist](/platform/compliance/gdpr#compliance-checklist)

## Known Gaps

**Same as GDPR:**
- 🚧 User deletion API
- 🚧 Automated DSAR export
- 🚧 Data portability API

**revDSG-Specific:**
- ✅ High-risk profiling transparency available
- ✅ Swiss hosting supported
- 🚧 Automated FDPIC notification (manual process)

## Resources

- **FDPIC**: [edoeb.admin.ch](https://www.edoeb.admin.ch/)
- **revDSG Text**: [admin.ch classified compilation](https://www.admin.ch/opc/en/classified-compilation/19920153/)

**Related:** [GDPR](/platform/compliance/gdpr) | [DSAR](/platform/compliance/data_subject_requests) | [Data Retention](/platform/compliance/data_retention)

---

:::info Legal Disclaimer
This is technical guidance, not legal advice. Consult legal counsel or FDPIC.
:::
