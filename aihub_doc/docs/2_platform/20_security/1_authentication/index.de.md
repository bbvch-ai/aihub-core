```markdown
---
title: Authentifizierung und Autorisierung
source_sha: "ee4c1de8d43e3a9802a6a9fe34d08351c497aa589d3b4a9a4c3360ca6cc37a18"
---

# Authentifizierung und Autorisierung

Der Swiss AI-Hub implementiert Authentifizierung und Autorisierung basierend auf den Industriestandard-Protokollen OpenID Connect (OIDC) und OAuth 2.0. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit Unternehmens-Identitätsprovidern und sorgt gleichzeitig für eine sichere Zugriffskontrolle über alle Plattformressourcen hinweg.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer über OpenID Connect, eine Identitätsschicht, die auf OAuth 2.0 aufbaut. Dies ermöglicht eine sichere Benutzerauthentifizierung über Unternehmens-Identitätsprovider wie Microsoft Entra ID (Azure Active Directory) und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### Wie die Authentifizierung funktioniert

**Token-basierte Authentifizierung:** Benutzer authentifizieren sich über den Identitätsprovider ihrer Organisation, der ein JSON Web Token (JWT) ausstellt, das kryptografisch signierte Claims über die Identität des Benutzers enthält. Die Plattform validiert diese Tokens bei jeder Anfrage, um Authentizität und Aktualität zu gewährleisten.

**JWT-Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS (JSON Web Key Set)-Endpunkt des Identitätsproviders ab und verwendet diese, um die kryptografische Signatur jedes JWT-Tokens zu verifizieren. Diese Validierung umfasst die Überprüfung des Ausstellers, der Zielgruppe, der Ablaufzeit und der Signaturintegrität des Tokens gemäß dem JWT-Standard (RFC 7519).

**Benutzeridentitätsauflösung:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige Benutzerkennung (OID) und grundlegende Profilinformationen (Name, E-Mail) aus den JWT-Token-Claims. Rollenzuweisungen werden lokal innerhalb der Plattform über Mandanten-bezogene Rollenentitäten verwaltet und nicht vom Identitätsprovider abgerufen.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth 2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den Identitätsprovider ihrer Organisation weitergeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren Autorisierungscode, der gegen Zugriffstokens ausgetauscht wird.

**Bearer Token Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die standardmäßige OAuth 2.0 Bearer Token Authentifizierung. API-Clients präsentieren gültige JWT-Tokens im HTTP Authorization Header, die mit dem gleichen JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffssteuerung

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, was eine konsistente Zugriffssteuerung ermöglicht, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform bewertet Berechtigungen für jede API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das unter [Berechtigungen](/de/docs/11_access_management/2_permissions/) beschrieben ist.

### Integration von Unternehmens-Identitätsprovidern

Die Plattform integriert sich mit Unternehmens-Identitätsprovidern über Standard-OIDC-/OAuth 2.0-Protokolle. Jeder OIDC-konforme Provider (Microsoft Entra ID, Google Workspace, Okta, Auth0, Keycloak) kann für die Authentifizierung verwendet werden.

**Generische OIDC-Integration:** Die Plattform verbindet sich mit dem konfigurierten OIDC-Provider als OAuth 2.0-Autorisierungsserver und Identitätsprovider. Die Benutzerauthentifizierung wird an den Provider delegiert, der die Anmeldeinformationen, Multi-Faktor-Authentifizierung und Sitzungsverwaltung gemäß den Sicherheitsrichtlinien der Organisation handhabt.

**Lokale Rollenverwaltung:** Benutzerprofile werden aus JWT-Token-Claims (Name, E-Mail, OID) extrahiert. Rollen werden lokal innerhalb der Plattform durch Mandanten-bezogene Rollenzuweisungen verwaltet und nicht vom Identitätsprovider synchronisiert. Dies entkoppelt die Plattformautorisierung von einem spezifischen Gruppen- oder Rollenmodell eines Identitätsproviders.

### Wie die Autorisierung funktioniert

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines Benutzers durch OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen der Benutzer basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsbewertungsprozess:**

1. Die Plattform löst die Rollenzuweisungen des Benutzers aus der lokalen Mandanten-bezogenen Rollendatenbank auf
2. Jede Rolle ist mit einem Satz von Zugriffsregeln verknüpft, die in der Plattformdatenbank gespeichert sind
3. Für jede API-Anfrage bewertet die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers
4. Zugriffsregeln unterstützen hierarchische Übereinstimmung mit Wildcard-Mustern für eine flexible Berechtigungsverwaltung
5. Die Autorisierungsentscheidung (Gewährung oder Verweigerung) wird getroffen und für Audit-Zwecke protokolliert

**API-Level-Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese Berechtigungen werden automatisch überprüft, bevor die Endpunktlogik ausgeführt wird, um sicherzustellen, dass kein Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsbewertung verwendet das hierarchische Berechtigungsmodell, das unter [Berechtigungen](/de/docs/11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform programmatischen Zugriff auf das Berechtigungsbewertungssystem. Dies ermöglicht das Filtern von Ergebnismengen basierend auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene Zugriffsebenen und die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Sicherheitsstandards und operative Fähigkeiten

### Standardkonformität

Die Implementierung von Authentifizierung und Autorisierung hält sich an Industriestandard-Protokolle und -Spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

- OpenID Connect Core 1.0 for authentication
- OAuth 2.0 Authorization Framework (RFC 6749)
- OAuth 2.0 Authorization Code Flow with PKCE
- JSON Web Token (JWT) - RFC 7519
- JSON Web Key Set (JWKS) - RFC 7517
- OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptografische Sicherheit:** Alle JWT-Tokens werden unter Verwendung kryptografischer RSA-256-Signaturen validiert. Öffentliche Schlüssel werden vom JWKS-Endpunkt des Identitätsproviders abgerufen und zur Leistungsverbesserung gecached. Die Token-Validierung umfasst Signaturprüfung, Ausstellerprüfung, Zielgruppenprüfung und Ablaufprüfung bei jeder Anfrage.

### Audit und Monitoring

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und Sicherheits-Monitoring-Zwecke protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen, Berechtigungsbewertungen, Zugriffsentscheidungen und den vollständigen Anfragekontext.

**Sicherheitsereignisprotokollierung:** Die Plattform integriert sich mit OpenTelemetry-Standards, um strukturierte, nachvollziehbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheits-Monitoring:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler, Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht die schnelle Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Unternehmenskonformität

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und Unternehmenssicherheitsstandards:

**Datenschutzkonformität:**

- DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
- Einhaltung des Schweizer Datenschutzgesetzes durch Self-Hosted Deployment-Optionen
- Umfassende Audit-Trails, die regulatorische Anforderungen für die Zugriffsprotokollierung erfüllen
- Datenhoheit gewahrt durch On-Premises- oder Schweizer Cloud-Deployment

**Unternehmenssicherheitsanforderungen:**

- Unterstützung der Multi-Faktor-Authentifizierung durch Unternehmens-Identitätsprovider
- Integration in bestehende Unternehmensidentitätsinfrastruktur
- Schutz vor gängigen Authentifizierungsangriffen (Token Replay, Session Hijacking, CSRF)
- Sicheres Token-Lebenszyklusmanagement mit Ablauf und Widerruf
- HTTPS-only-Kommunikation für alle Authentifizierungs-Flows

**Best Practices für Sicherheit:**

- Zero-Trust-Sicherheitsmodell mit Authentifizierung für jeden API-Zugriff
- Trennung von Authentifizierungs- und Autorisierungsbelangen
- Prinzip der geringsten Rechte durch ein granular Berechtigungssystem
- Defense in Depth mit mehreren Schichten von Sicherheitskontrollen
- Regelmäßige Token-Validierungs- und Refresh-Mechanismen

Dieser standardbasierte Ansatz für Authentifizierung und Autorisierung stellt sicher, dass die Plattform die Sicherheitsanforderungen von Unternehmen erfüllt und gleichzeitig mit Standard-Identitätsprovidern und Sicherheitsinfrastrukturen interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, geprüft und vertrauenswürdig sind.
```
