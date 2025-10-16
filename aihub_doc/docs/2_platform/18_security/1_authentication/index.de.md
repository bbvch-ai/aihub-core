---
title: Authentifizierung und Autorisierung
index: 2
source_sha: "5ba75e1432ee0dbf1afb5a273842adaf8bdbbb521d7b5af5ac032b881b21db73"
---

# TODO: @mhoegger überprüfen

# Authentifizierung und Autorisierung

Der Swiss AI-Hub implementiert Authentifizierung und Autorisierung basierend auf den Industriestandard-Protokollen OpenID Connect (OIDC) und OAuth 2.0. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit Enterprise Identity Providern und bietet gleichzeitig eine sichere Zugriffskontrolle über alle Plattformressourcen hinweg.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer über OpenID Connect, eine Identitätsschicht, die auf OAuth 2.0 aufbaut. Dies ermöglicht eine sichere Benutzerauthentifizierung über Enterprise Identity Provider wie Microsoft Entra ID (Azure Active Directory) und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### So funktioniert die Authentifizierung

**Token-basierte Authentifizierung:** Benutzer authentifizieren sich über den Identity Provider ihrer Organisation, der ein JSON Web Token (JWT) ausstellt, das kryptografisch signierte Claims über die Identität des Benutzers enthält. Die Plattform validiert diese Tokens bei jeder Anfrage, um Authentizität und Aktualität sicherzustellen.

**JWT Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS (JSON Web Key Set)-Endpunkt des Identity Providers ab und verwendet diese, um die kryptografische Signatur jedes JWT Tokens zu verifizieren. Diese Validierung umfasst die Überprüfung des Ausstellers, der Zielgruppe, der Ablaufzeit und der Signaturintegrität des Tokens gemäß dem JWT-Standard (RFC 7519).

**Benutzeridentitätsauflösung:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige Benutzerkennung (OID) aus den Token-Claims und ruft über die Microsoft Graph API vollständige Benutzerinformationen, einschließlich Name, E-Mail und Rollenzuweisungen, vom Identity Provider ab.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth 2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den Identity Provider ihrer Organisation weitergeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren Autorisierungscode, der gegen Access Tokens ausgetauscht wird.

**Bearer Token Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die Standard OAuth 2.0 Bearer Token Authentifizierung. API-Clients präsentieren gültige JWT Tokens im HTTP Authorization Header, die mit demselben JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffskontrolle

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, was eine konsistente Zugriffskontrolle unabhängig davon ermöglicht, wie sich Benutzer authentifizieren. Die Plattform bewertet Berechtigungen für jede API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das unter [Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

### Integration von Enterprise Identity Providern

Die Plattform integriert sich über Standard-OIDC-/OAuth 2.0-Protokolle mit Enterprise Identity Providern. Der primäre Integrationspunkt ist Microsoft Entra ID (Azure Active Directory), mit Unterstützung für die Erweiterbarkeit auf andere OIDC-konforme Identity Provider.

**Microsoft Entra ID Integration:** Die Plattform verbindet sich mit Microsoft Entra ID als OAuth 2.0 Autorisierungsserver und OIDC Identity Provider. Die Benutzerauthentifizierung wird an Entra ID delegiert, welches die Überprüfung der Anmeldeinformationen, die Multi-Faktor-Authentifizierung und die Sitzungsverwaltung gemäß den Sicherheitsrichtlinien der Organisation handhabt.

**Abruf von Benutzerprofil und Rollen:** Nach der Authentifizierung fragt die Plattform die Microsoft Graph API ab, um vollständige Benutzerprofile, einschließlich Anzeigename, E-Mail-Adresse und Mitgliedschaften in Organisationsgruppen, abzurufen. Diese Gruppenmitgliedschaften werden Plattformrollen zugeordnet, die die Zugriffsrechte des Benutzers innerhalb des AI-Hubs bestimmen.

### So funktioniert die Autorisierung

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines Benutzers durch OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen der Benutzer basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsbewertungsprozess:**

1.  Die Plattform extrahiert die Rollenzuweisungen des Benutzers vom Identity Provider
2.  Jede Rolle ist mit einem Satz von Zugriffsregeln verknüpft, die in der Plattformdatenbank gespeichert sind
3.  Für jede API-Anfrage bewertet die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers
4.  Zugriffsregeln unterstützen hierarchische Abgleiche mit Wildcard-Mustern für ein flexibles Berechtigungsmanagement
5.  Die Autorisierungsentscheidung (Gewähren oder Verweigern) wird getroffen und zu Prüfzwecken protokolliert

**API-Level Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese Berechtigungen werden automatisch geprüft, bevor die Endpunktlogik ausgeführt wird, um sicherzustellen, dass kein Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsbewertung verwendet das hierarchische Berechtigungsmodell, das unter [Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform programmatischen Zugriff auf das Berechtigungsbewertungssystem. Dies ermöglicht das Filtern von Ergebnismengen basierend auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene Zugriffsebenen und die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Sicherheitsstandards und Betriebsfunktionen

### Standardkonformität

Die Implementierung der Authentifizierung und Autorisierung hält sich an Industriestandardprotokolle und -spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

-   OpenID Connect Core 1.0 für Authentifizierung
-   OAuth 2.0 Authorization Framework (RFC 6749)
-   OAuth 2.0 Authorization Code Flow mit PKCE
-   JSON Web Token (JWT) - RFC 7519
-   JSON Web Key Set (JWKS) - RFC 7517
-   OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptografische Sicherheit:** Alle JWT Tokens werden unter Verwendung von kryptografischen RSA-256-Signaturen validiert. Öffentliche Schlüssel werden vom Identity Provider-JWKS-Endpunkt abgerufen und zur Leistungsverbesserung zwischengespeichert. Die Token-Validierung umfasst bei jeder Anfrage die Signaturverifizierung, die Aussteller-, Zielgruppen- und Ablaufzeitvalidierung.

### Audit und Überwachung

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und Sicherheitsüberwachungszwecke protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen, Berechtigungsbewertungen, Zugriffsentscheidungen und den vollständigen Anfragekontext.

**Protokollierung von Sicherheitsereignissen:** Die Plattform integriert sich in OpenTelemetry-Standards, um strukturierte, nachvollziehbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheitsüberwachung:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler, Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht eine schnelle Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Unternehmenskonformität

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und Unternehmenssicherheitsstandards:

**Datenschutzkonformität:**

-   DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
-   Einhaltung des Schweizer Datenschutzgesetzes durch selbst gehostete Bereitstellungsoptionen
-   Umfassende Audit-Trails, die regulatorische Anforderungen an die Zugriffsprotokollierung erfüllen
-   Datensouveränität durch On-Premises- oder Schweizer Cloud-Bereitstellung

**Anforderungen an die Unternehmenssicherheit:**

-   Unterstützung der Multi-Faktor-Authentifizierung durch Enterprise Identity Provider
-   Integration in die bestehende Unternehmens-Identitätsinfrastruktur
-   Schutz vor gängigen Authentifizierungsangriffen (Token-Replay, Session Hijacking, CSRF)
-   Sicheres Token-Lebenszyklusmanagement mit Ablauf und Widerruf
-   HTTPS-only-Kommunikation für alle Authentifizierungsflows

**Sicherheits-Best-Practices:**

-   Zero-Trust-Sicherheitsmodell mit Authentifizierung für jeden API-Zugriff erforderlich
-   Trennung von Authentifizierungs- und Autorisierungsaspekten
-   Prinzip der geringsten Rechte (Principle of Least Privilege) durch granuläres Berechtigungssystem
-   Defense in Depth mit mehreren Schichten von Sicherheitskontrollen
-   Regelmäßige Token-Validierungs- und Refresh-Mechanismen

Dieser standardbasierte Ansatz zur Authentifizierung und Autorisierung stellt sicher, dass die Plattform die Sicherheitsanforderungen von Unternehmen erfüllt und gleichzeitig mit Standard-Identity Providern und Sicherheitsinfrastrukturen interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, geprüft und vertraut sind.
