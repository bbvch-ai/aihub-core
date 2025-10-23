---
title: Swiss Data Protection Act (DSG)
index: 3
---

# Swiss Data Protection Act (revDSG)

The revised Swiss Federal Act on Data Protection (revDSG) came into force on September 1, 2023. The AI-Hub platform is designed to support compliance with Swiss data protection requirements.

:::info
The revDSG is largely aligned with GDPR but has Swiss-specific requirements. This document focuses on Swiss-specific aspects. For general data protection features, see [GDPR Compliance](/platform/compliance/gdpr).
:::

## Key Differences from GDPR

| Aspect | revDSG | GDPR | AI-Hub Support |
|--------|---------|------|----------------|
| **Territorial Scope** | Applies to data processing affecting Swiss residents | Applies to EU/EEA residents | ✅ Supported via Swiss hosting |
| **Legal Basis** | Less restrictive than GDPR | Strict consent requirements | ✅ Supports both approaches |
| **Data Breach Notification** | Only if "high risk" to affected persons | Within 72 hours if "risk to rights and freedoms" | ✅ Audit logs support both |
| **DPO Requirement** | No mandatory DPO requirement | Mandatory DPO in many cases | N/A - Customer decision |
| **Profiling** | Special provisions for "high-risk profiling" | Provisions for automated decision-making | ✅ Human-in-the-loop available |
| **Data Transfers** | Adequacy assessment required | Adequacy decision or safeguards required | ✅ Swiss hosting recommended |

## revDSG-Specific Requirements

### 1. Privacy by Design and Default

**✅ Implemented:**
- Default-deny RBAC permissions
- Encryption by default (TLS/SSL)
- Minimal data collection
- 30-day automatic deletion for ephemeral data

### 2. Data Processing Register

**Customer Responsibility:**
- Maintain register of processing activities
- Document data categories, purposes, and recipients
- No specific technical implementation required in AI-Hub

### 3. High-Risk Profiling

**Definition:** Automated processing of personal data to evaluate personal aspects, particularly for risk assessment or behavioral prediction.

**✅ Implemented:**
- Human-in-the-loop workflows ([Human-in-the-Loop](/platform/agents/agent_workflows/human_in_the_loop))
- Phoenix tracing for transparency
- Source attribution for explainability

**Customer Responsibilities:**
- Identify high-risk profiling activities
- Conduct Data Protection Impact Assessment (DPIA) for high-risk processing
- Implement human oversight for high-risk decisions

### 4. Data Security

**✅ Implemented:**
- Encryption in transit ([Data Encryption](/platform/security/data_encryption))
- Authentication and authorization ([Authentication](/platform/security/authentication))
- Access controls ([Access Management](/platform/access_management))
- Audit logging for breach detection

**revDSG Requirement:** "Appropriate technical and organizational measures" - implementation level depends on data sensitivity and processing risk.

### 5. Data Subject Rights

**Similarities to GDPR:**
- Right of access
- Right to rectification
- Right to deletion
- Right to data portability (limited)

**Differences:**
- Shorter response timeframe (30 days vs. GDPR's 1 month)
- No explicit "right to be forgotten" terminology
- Simpler data portability requirements

**Implementation Status:**
- See [GDPR Compliance](/platform/compliance/gdpr#data-subject-rights) for current implementation status
- Same limitations apply (🚧 user deletion, DSAR automation not fully implemented)

### 6. Data Breach Notification

**revDSG Requirements:**
- Notify Federal Data Protection and Information Commissioner (FDPIC) "as quickly as possible"
- Only required if "high risk" to affected persons
- No specific 72-hour deadline (unlike GDPR)

**✅ Implemented:**
- Audit logs for breach investigation
- User access reports
- Monitoring and alerting

**Customer Responsibilities:**
- Assess breach risk level
- Notify FDPIC if high risk
- Document all breaches
- Notify affected individuals if appropriate

## Swiss Cloud Hosting

**Advantages for revDSG Compliance:**
- Data remains in Switzerland
- Subject to Swiss data protection law
- No international data transfer issues
- Switzerland has EU adequacy decision (bonus for mixed compliance)

**✅ Supported:**
- On-premise deployment in Switzerland
- Swiss cloud provider options (see [Deployment Options](/platform/deployment_guide/deployment_options))
- No mandatory data transfer outside Switzerland

## Data Transfer Outside Switzerland

**revDSG Requirements:**
When transferring data outside Switzerland:
1. Adequate protection in destination country, OR
2. Appropriate safeguards (e.g., SCCs), OR
3. Explicit consent from data subjects

**AI-Hub Recommendations:**
- **Preferred**: Swiss hosting to avoid transfers
- **Alternative**: Use Swiss-based or EU-based LLM providers via LiteLLM configuration
- **If transfers necessary**: Execute Standard Contractual Clauses with providers

## Compliance Checklist (revDSG-Specific)

**Initial Setup:**
- [ ] Conduct DPIA for high-risk processing (profiling, AI decision-making)
- [ ] Maintain data processing register
- [ ] Configure Swiss hosting or document data transfer safeguards
- [ ] Document legal basis for processing (simpler than GDPR)
- [ ] Establish breach notification procedure for FDPIC
- [ ] Create privacy policy for Swiss users

**Ongoing:**
- [ ] Review data processing register annually
- [ ] Monitor for high-risk profiling activities
- [ ] Test breach notification procedures
- [ ] Review data transfer arrangements
- [ ] Audit Swiss hosting/data residency compliance

## Known Gaps & Implementation Status

**Same as GDPR:**
- 🚧 User-level deletion API
- 🚧 Comprehensive DSAR automation
- 🚧 Data portability automation
- 🚧 Processing restriction flags

**revDSG-Specific:**
- ✅ High-risk profiling transparency (human-in-the-loop available)
- ✅ Swiss hosting options available
- ✅ Breach detection capabilities (audit logs)
- 🚧 Automated FDPIC breach notification (manual process required)

## Differences in Practice

| Requirement | GDPR | revDSG | Practical Impact for AI-Hub |
|-------------|------|---------|----------------------------|
| **Consent** | Must be explicit and documented | Can be implied in some cases | AI-Hub supports explicit consent mechanisms; customer decides approach |
| **Breach Notification** | 72 hours to authority | "As quickly as possible" if high risk | AI-Hub audit logs support both; customer determines timing |
| **DPO** | Often mandatory | Not mandatory | No AI-Hub-specific requirement |
| **Fines** | Up to €20M or 4% revenue | Up to CHF 250,000 (individuals only, not companies) | Lower financial risk, but reputational risk remains |

## Resources

- **FDPIC Official Site**: [https://www.edoeb.admin.ch/](https://www.edoeb.admin.ch/)
- **revDSG Full Text**: [https://www.admin.ch/opc/en/classified-compilation/19920153/index.html](https://www.admin.ch/opc/en/classified-compilation/19920153/index.html)
- **FDPIC Guidelines**: [https://www.edoeb.admin.ch/edoeb/en/home.html](https://www.edoeb.admin.ch/edoeb/en/home.html)

**Related Documentation:**
- [GDPR Compliance](/platform/compliance/gdpr)
- [Data Retention](/platform/compliance/data_retention)
- [Deployment Options](/platform/deployment_guide/deployment_options)

---

:::info Legal Disclaimer
This documentation provides technical guidance but is not legal advice. Consult your legal counsel or the FDPIC for compliance questions specific to your use case.
:::
