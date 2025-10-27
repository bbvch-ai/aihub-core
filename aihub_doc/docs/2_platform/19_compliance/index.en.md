---
title: Compliance and regulations
index: 19
---

# Compliance and regulations

The platform provides technical measures to support regulatory compliance. Customers acting as data controllers remain responsible for their own compliance with applicable laws.

## Overview

The compliance documentation covers:

- **Data retention policies**: How the platform stores and expires different types of data
- **GDPR compliance**: Technical measures supporting EU data protection requirements
- **Swiss DSG**: Switzerland-specific data protection requirements
- **EU AI Act**: AI-specific regulatory considerations (coming soon)
- **Internationalization**: Multi-language support for Swiss organizations
- **Data subject access requests (DSAR)**: Procedures for handling data subject rights

## Implementation status

The platform implements many compliance features but has known gaps:

**✅ Implemented:**
- Multi-tenant isolation and RBAC
- Audit logging and tracing
- Configurable retention policies
- 30-day auto-deletion for ephemeral data
- TLS/SSL encryption
- OAuth/OIDC/SAML authentication

**🚧 Missing:**
- User deletion API with cascading delete
- Automated DSAR data export
- Data portability API
- Processing restriction flags
- Self-service DSAR portal

See individual compliance sections for details on implementation status and workarounds.

## Key principle

**Customers are data controllers**. The platform provides the technical foundation, but organizations must:

- Document legal basis for processing
- Conduct data protection impact assessments (DPIAs)
- Configure retention policies appropriately
- Respond to data subject requests
- Maintain records of processing activities (ROPA)
- Implement their own data lifecycle policies

Technical capabilities enable compliance, but don't replace legal and organizational requirements.
