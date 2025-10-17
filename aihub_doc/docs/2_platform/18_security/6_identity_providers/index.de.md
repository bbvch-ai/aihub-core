---
title: Unterstützte Identity Provider
index: 6
---

# Unterstützte Identity Provider

::: info Hinweis zur Dokumentation
Die englische Version dieser Dokumentation ist die maßgebliche und vollständige Version. Diese deutsche Version ist eine Zusammenfassung der wichtigsten Punkte.

Vollständige Dokumentation: [English Version](./index.en.md)
:::

## Überblick

Der Swiss AI Hub implementiert standardbasierte Authentifizierung und unterstützt Integration mit einer breiten Palette von Enterprise Identity Providern (IdPs) durch OpenID Connect (OIDC) und OAuth 2.0 Protokolle.

## Primär unterstützte Identity Provider

### Microsoft Entra ID (Azure Active Directory)

**Support-Level**: Vollständig unterstützt und empfohlen

Microsoft Entra ID ist der primäre Identity Provider für den Swiss AI Hub mit umfangreicher Integration.

**Hauptfunktionen**:
- Single Sign-On (SSO)
- Multi-Faktor-Authentifizierung (MFA)
- Conditional Access
- Gruppenbasierte Zugriffszuweisung
- Benutzerprofil-Synchronisation
- Anwendungsrollen

**Konfigurationsanforderungen**:
```yaml
identity_provider:
  type: "azure_ad"
  tenant_id: "your-tenant-id"
  client_id: "your-application-client-id"
  client_secret: "your-client-secret"
  authority: "https://login.microsoftonline.com/{tenant_id}"
```

### Generisches OpenID Connect (OIDC)

**Support-Level**: Vollständig unterstützt

Jeder OIDC-konforme Identity Provider kann mit dem Swiss AI Hub integriert werden.

**Unterstützte OIDC-Provider**:
- Okta
- Auth0
- Keycloak
- Google Workspace
- GitLab
- GitHub
- Benutzerdefinierte OIDC-Implementierungen

**Konfigurationsanforderungen**:
```yaml
identity_provider:
  type: "oidc"
  issuer: "https://your-idp.com"
  client_id: "your-client-id"
  client_secret: "your-client-secret"
  discovery_url: "https://your-idp.com/.well-known/openid-configuration"
```

## Enterprise Identity Provider Integrationen

### Okta

**Support-Level**: Getestet und vollständig unterstützt

Okta ist eine weit verbreitete Enterprise Identity Plattform mit voller OIDC-Unterstützung.

**Okta-spezifische Funktionen**:
- Universal Directory
- Adaptive Multi-Faktor-Authentifizierung
- API Access Management
- User Lifecycle Management

### Auth0

**Support-Level**: Getestet und vollständig unterstützt

Auth0 bietet flexible Authentifizierung und Autorisierung als Service.

**Auth0-spezifische Funktionen**:
- Universal Login
- Rules and Actions für benutzerdefinierte Authentifizierungslogik
- Social Identity Provider Aggregation
- Passwortlose Authentifizierung

### Keycloak

**Support-Level**: Getestet und vollständig unterstützt

Keycloak ist eine Open-Source-Identitäts- und Zugriffsverwaltungslösung, ideal für On-Premises-Deployments.

**Keycloak-spezifische Funktionen**:
- Self-hosted und Open-Source
- Multi-Realm-Support
- User Federation (LDAP, Active Directory)
- Feinkörnige Autorisierungsrichtlinien

### Google Workspace (Google Cloud Identity)

**Support-Level**: Getestet und vollständig unterstützt

Google Workspace bietet OIDC-Authentifizierung für Organisationen mit Google's Produktivitätssuite.

**Google-spezifische Funktionen**:
- Integration mit Google Workspace Services
- Domain-Beschränkung
- 2-Schritt-Verifizierung
- Google Admin Console

### LDAP / Active Directory (via Keycloak Federation)

**Support-Level**: Unterstützt durch Federation

Für Organisationen mit bestehender LDAP- oder Active Directory-Infrastruktur kann Keycloak Federation bereitstellen.

**Architektur**:
```
Swiss AI Hub <--> Keycloak (OIDC) <--> LDAP/Active Directory
```

## Erweiterte Integrationsfunktionen

### Gruppenbasierte Rollenzuweisung

Automatische Zuweisung von Plattformrollen basierend auf Identity Provider Gruppenmitgliedschaften:

```yaml
role_mapping:
  "Engineering-AI-Team": "data_scientist"
  "Product-Managers": "business_analyst"
  "IT-Administrators": "platform_admin"
```

### Just-In-Time (JIT) Benutzerbereitstellung

Automatische Erstellung von Benutzerkonten beim ersten Login.

### Single Logout (SLO)

Unterstützung für Single Logout über alle verbundenen Anwendungen.

### Token-Aktualisierung und Lebenszyklus

Automatische Token-Aktualisierung für langlebige Sitzungen.

## Sicherheitsüberlegungen

### Token-Validierung

Alle ID-Tokens werden auf Sicherheit validiert:

- Signaturverifizierung
- Issuer-Validierung
- Audience-Validierung
- Ablaufprüfung
- Nonce-Validierung

### Sichere Credential-Speicherung

- Niemals Secrets in Versionskontrolle committen
- Umgebungsvariablen oder Secret-Management-Services verwenden
- Secrets regelmäßig rotieren

## Weitere Informationen

Vollständige Details zu OAuth 2.0 Providern, erweiterten Konfigurationen, Sicherheitsmaßnahmen, Migration und Best Practices finden Sie in der [englischen Vollversion](./index.en.md).
