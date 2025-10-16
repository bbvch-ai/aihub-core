---
title: Authentifizierung und Autorisierung
index: 2
source_sha: "8782828d64199e253b410423624bf53db367b53403bb46c5bfd3d86051cfaeb0"
---

# TODO: @mhoegger verifizieren

# Authentifizierung und Autorisierung

Der Swiss AI-Hub implementiert Authentifizierung und Autorisierung basierend auf den Industriestandards OpenID Connect (OIDC) und OAuth 2.0 Protokollen. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit Enterprise Identity Providern und erhält gleichzeitig eine sichere Zugriffskontrolle über alle Plattformressourcen hinweg aufrecht.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer über OpenID Connect, einer Identitätsschicht, die auf OAuth 2.0 aufbaut. Dies ermöglicht eine sichere Benutzerauthentifizierung über Enterprise Identity Provider wie Microsoft Entra ID (Azure Active Directory) und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### Wie die Authentifizierung funktioniert

**Tokenbasierte Authentifizierung:** Benutzer authentifizieren sich über den Identity Provider ihrer Organisation, der ein JSON Web Token (JWT) ausstellt, das kryptographisch signierte Claims über die Identität des Benutzers enthält. Die Plattform validiert diese Tokens bei jeder Anfrage, um Authentizität und Aktualität sicherzustellen.

**JWT Token Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS (JSON Web Key Set) Endpunkt des Identity Providers ab und verwendet diese, um die kryptographische Signatur jedes JWT Tokens zu verifizieren. Diese Validierung umfasst die Prüfung des Ausstellers (issuer), der Zielgruppe (audience), der Ablaufzeit und der Signaturintegrität des Tokens gemäß dem JWT-Standard (RFC 7519).

**Benutzeridentitätsauflösung:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige Benutzerkennung (OID) aus den Token-Claims und ruft vollständige Benutzerinformationen, einschließlich Name, E-Mail und Rollenzuweisungen, vom Identity Provider über die Microsoft Graph API ab.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth 2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den Identity Provider ihrer Organisation weitergeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren Autorisierungscode, der gegen Access Tokens ausgetauscht wird.

**Bearer Token Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die standardmäßige OAuth 2.0 Bearer Token Authentifizierung. API-Clients übermitteln gültige JWT Tokens im HTTP Authorization Header, welche mit demselben JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffssteuerung

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, was eine konsistente Zugriffssteuerung ermöglicht, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform bewertet Berechtigungen für jede API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das in der [RBAC-Dokumentation](../../../../1_vision_and_positioning/3_solution/4_security/2_rbac/index.md) beschrieben ist.

### Integration von Enterprise Identity Providern

Die Plattform integriert sich über standardisierte OIDC/OAuth 2.0 Protokolle mit Enterprise Identity Providern. Der primäre Integrationspunkt ist Microsoft Entra ID (Azure Active Directory), mit Unterstützung für die Erweiterung auf andere OIDC-konforme Identity Provider.

**Microsoft Entra ID Integration:** Die Plattform verbindet sich mit Microsoft Entra ID als OAuth 2.0 Autorisierungsserver und OIDC Identity Provider. Die Benutzerauthentifizierung wird an Entra ID delegiert, das die Validierung von Anmeldeinformationen, die Multi-Faktor-Authentifizierung und das Session-Management gemäß den Sicherheitsrichtlinien der Organisation handhabt.

**Abruf von Benutzerprofilen und Rollen:** Nach der Authentifizierung fragt die Plattform die Microsoft Graph API ab, um vollständige Benutzerprofile, einschließlich Anzeigename, E-Mail-Adresse und Mitgliedschaften in Organisationsgruppen, abzurufen. Diese Gruppenmitgliedschaften werden Plattformrollen zugeordnet, die die Zugriffsberechtigungen des Benutzers innerhalb des AI-Hub bestimmen.

### Wie die Autorisierung funktioniert

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines Benutzers durch OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen der Benutzer basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsbewertungsprozess:**

1.  Die Plattform extrahiert die Rollenzuweisungen des Benutzers vom Identity Provider
2.  Jede Rolle ist mit einem Satz von Zugriffsregeln verbunden, die in der Plattformdatenbank gespeichert sind
3.  Für jede API-Anfrage bewertet die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers
4.  Zugriffsregeln unterstützen hierarchische Übereinstimmungen mit Wildcard-Mustern für eine flexible Berechtigungsverwaltung
5.  Die Autorisierungsentscheidung (Gewähren oder Verweigern) wird getroffen und zu Audit-Zwecken protokolliert

**API-Level-Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese Berechtigungen werden automatisch überprüft, bevor die Endpunktlogik ausgeführt wird, um sicherzustellen, dass kein Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsbewertung verwendet das hierarchische Berechtigungsmodell, das in der [RBAC-Dokumentation](../../../../1_vision_and_positioning/3_solution/4_security/2_rbac/index.md) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform programmatischen Zugriff auf das Berechtigungsbewertungssystem. Dies ermöglicht das Filtern von Ergebnismengen basierend auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene Zugriffsebenen und die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Sicherheitsstandards und operationale Fähigkeiten

### Standardkonformität

Die Implementierung von Authentifizierung und Autorisierung entspricht den Industriestandardprotokollen und -spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

-   OpenID Connect Core 1.0 für die Authentifizierung
-   OAuth 2.0 Authorization Framework (RFC 6749)
-   OAuth 2.0 Authorization Code Flow mit PKCE
-   JSON Web Token (JWT) - RFC 7519
-   JSON Web Key Set (JWKS) - RFC 7517
-   OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptographische Sicherheit:** Alle JWT Tokens werden mittels kryptographischer RSA-256 Signaturen validiert. Öffentliche Schlüssel werden vom JWKS-Endpunkt des Identity Providers abgerufen und zur Leistungssteigerung zwischengespeichert. Die Token-Validierung umfasst Signaturverifikation, Issuer-Validierung, Audience-Validierung und die Überprüfung des Ablaufdatums bei jeder Anfrage.

### Audit und Monitoring

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und Sicherheitsüberwachungszwecke protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen, Berechtigungsbewertungen, Zugriffsentscheidungen und den vollständigen Anfragekontext.

**Sicherheitsereignisprotokollierung:** Die Plattform integriert sich in OpenTelemetry-Standards, um strukturierte, nachvollziehbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheitsüberwachung:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler, Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht die schnelle Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und unternehmensweite Compliance

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und unternehmensweiter Sicherheitsstandards:

**Datenschutzkonformität:**

-   DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
-   Einhaltung des Schweizer Datenschutzgesetzes durch Self-Hosted-Deployment-Optionen
-   Umfassende Audit-Trails, die regulatorische Anforderungen für die Zugriffsprotokollierung erfüllen
-   Datenhoheit durch On-Premises- oder Schweizer Cloud-Bereitstellung gewahrt

**Unternehmensweite Sicherheitsanforderungen:**

-   Unterstützung der Multi-Faktor-Authentifizierung durch Enterprise Identity Provider
-   Integration in die bestehende Unternehmens-Identitätsinfrastruktur
-   Schutz vor gängigen Authentifizierungsangriffen (Token-Replay, Session-Hijacking, CSRF)
-   Sicheres Token-Lebenszyklusmanagement mit Ablauf und Widerruf
-   Nur HTTPS-Kommunikation für alle Authentifizierungsabläufe

**Sicherheits-Best-Practices:**

-   Zero-Trust-Sicherheitsmodell mit erforderlicher Authentifizierung für alle API-Zugriffe
-   Trennung von Authentifizierungs- und Autorisierungsbelangen
-   Prinzip der geringsten Privilegien durch ein granularisiertes Berechtigungssystem
-   Verteidigung in der Tiefe mit mehreren Schichten von Sicherheitskontrollen
-   Regelmäßige Token-Validierungs- und Refresh-Mechanismen

Dieser standardbasierte Ansatz für Authentifizierung und Autorisierung stellt sicher, dass die Plattform die Sicherheitsanforderungen von Unternehmen erfüllt und gleichzeitig mit Standard-Identity-Providern und der Sicherheitsinfrastruktur interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, geprüft und vertraut sind.
