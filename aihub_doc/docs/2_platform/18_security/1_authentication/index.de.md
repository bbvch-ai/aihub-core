---
title: Authentifizierung und Autorisierung
source_sha: "30266a9b1c90a03d9d4803c957c6d65fcd836c6ce4062d1dabac9c2d1fa44b90"
---

# ZU ERLEDIGEN: @mhoegger überprüfen

# Authentifizierung und Autorisierung

Der Swiss AI-Hub implementiert Authentifizierung und Autorisierung basierend auf den branchenüblichen OpenID Connect (OIDC)
und OAuth 2.0 Protokollen. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit
Unternehmens-Identitätsprovidern und sorgt gleichzeitig für eine sichere Zugriffskontrolle über alle Plattformressourcen.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer über OpenID Connect, eine auf OAuth 2.0 aufbauende Identitätsebene. Dies
ermöglicht eine sichere Benutzerauthentifizierung über Unternehmens-Identitätsprovider wie Microsoft Entra ID (Azure Active Directory)
und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### Funktionsweise der Authentifizierung

**Token-basierte Authentifizierung:** Benutzer authentifizieren sich über den Identitätsprovider ihrer Organisation, der einen
JSON Web Token (JWT) ausstellt. Dieser JWT enthält kryptografisch signierte Claims über die Identität des Benutzers.
Die Plattform validiert diese Tokens bei jeder Anfrage, um deren Authentizität und Aktualität zu gewährleisten.

**JWT Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS (JSON Web Key Set)-Endpunkt des
Identitätsproviders ab und verwendet sie, um die kryptografische Signatur jedes JWT Tokens zu verifizieren. Diese Validierung
umfasst die Überprüfung des Ausstellers (Issuer), der Zielgruppe (Audience), der Ablaufzeit (Expiration Time) und der Signaturintegrität
gemäß dem JWT-Standard (RFC 7519).

**Benutzeridentitätsauflösung:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige
Benutzerkennung (OID) aus den Token-Claims und ruft vollständige Benutzerinformationen, einschliesslich Name, E-Mail
und Rollenzuweisungen, vom Identitätsprovider über die Microsoft Graph API ab.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem
OAuth 2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den
Identitätsprovider ihrer Organisation weitergeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren
Autorisierungscode, der gegen Zugriffstokens (Access Tokens) ausgetauscht wird.

**Bearer Token Authentifizierung:** Für API-Zugriffe und programmatische Integrationen unterstützt die Plattform die
standardmässige OAuth 2.0 Bearer Token Authentifizierung. API-Clients präsentieren gültige JWT Tokens im
HTTP Authorization Header, die mit demselben JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffskontrolle

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, was eine konsistente Zugriffskontrolle
ermöglicht, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform bewertet die Berechtigungen für jede
API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das unter
[Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

### Integration von Unternehmens-Identitätsprovidern

Die Plattform integriert sich über Standard-OIDC-/OAuth 2.0-Protokolle mit Unternehmens-Identitätsprovidern. Der primäre
Integrationspunkt ist Microsoft Entra ID (Azure Active Directory), mit Unterstützung für die Erweiterbarkeit auf andere
OIDC-konforme Identitätsprovider.

**Microsoft Entra ID Integration:** Die Plattform verbindet sich mit Microsoft Entra ID als OAuth 2.0 Autorisierungsserver
und OIDC Identitätsprovider. Die Benutzerauthentifizierung wird an Entra ID delegiert, das die Anmeldeinformationenvalidierung,
die Multi-Faktor-Authentifizierung und das Sitzungsmanagement gemäss den Sicherheitsrichtlinien der Organisation handhabt.

**Abruf von Benutzerprofil und Rollen:** Nach der Authentifizierung fragt die Plattform die Microsoft Graph API ab, um
vollständige Benutzerprofile einschliesslich Anzeigename, E-Mail-Adresse und Organisationsgruppenzugehörigkeiten
abzurufen. Diese Gruppenzugehörigkeiten werden Plattformrollen zugeordnet, die die Zugriffsrechte des Benutzers innerhalb des AI-Hub bestimmen.

### Funktionsweise der Autorisierung

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines Benutzers
durch die OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen der Benutzer
basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsbewertungsprozess:**

1.  Die Plattform extrahiert die Rollenzuweisungen des Benutzers vom Identitätsprovider.
2.  Jede Rolle ist mit einem Satz von Zugriffsregeln verbunden, die in der Plattformdatenbank gespeichert sind.
3.  Für jede API-Anfrage bewertet die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers.
4.  Zugriffsregeln unterstützen hierarchische Übereinstimmungen mit Wildcard-Mustern für ein flexibles Berechtigungsmanagement.
5.  Die Autorisierungsentscheidung (Gewährung oder Verweigerung) wird getroffen und zu Audit-Zwecken protokolliert.

**API-Level Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese
Berechtigungen werden automatisch überprüft, bevor die Endpunktlogik ausgeführt wird, um sicherzustellen, dass kein
Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsbewertung verwendet das hierarchische Berechtigungsmodell,
das unter [Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform
programmatischen Zugriff auf das Berechtigungsbewertungssystem. Dies ermöglicht das Filtern von Ergebnismengen
basierend auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene
Zugriffsstufen und die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Sicherheitsstandards und Betriebsfähigkeiten

### Standardkonformität

Die Implementierung von Authentifizierung und Autorisierung hält sich an branchenübliche Protokolle und Spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

-   OpenID Connect Core 1.0 für die Authentifizierung
-   OAuth 2.0 Authorization Framework (RFC 6749)
-   OAuth 2.0 Authorization Code Flow mit PKCE
-   JSON Web Token (JWT) - RFC 7519
-   JSON Web Key Set (JWKS) - RFC 7517
-   OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptografische Sicherheit:** Alle JWT Tokens werden mittels RSA-256 kryptografischer Signaturen validiert. Öffentliche
Schlüssel werden vom JWKS-Endpunkt des Identitätsproviders abgerufen und zur Leistungsoptimierung zwischengespeichert.
Die Token-Validierung umfasst die Signaturverifikation, die Überprüfung von Aussteller, Zielgruppe und Ablaufzeit bei jeder Anfrage.

### Audit und Überwachung

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und
Sicherheitsüberwachungszwecke protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen,
Berechtigungsbewertungen, Zugriffsentscheidungen und den vollständigen Anfragekontext.

**Sicherheitsereignisprotokollierung:** Die Plattform integriert sich in OpenTelemetry-Standards, um strukturierte,
rückverfolgbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über
verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheitsüberwachung:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler,
Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht die schnelle
Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Unternehmenskonformität

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und
Unternehmenssicherheitsstandards:

**Datenschutzkonformität:**

-   DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
-   Einhaltung des Schweizer Datenschutzgesetzes durch Optionen für selbstgehostete Bereitstellung
-   Umfassende Audit-Trails, die regulatorische Anforderungen an die Zugriffsprotokollierung erfüllen
-   Datenhoheit durch On-Premises- oder Schweizer Cloud-Bereitstellung gewahrt

**Anforderungen an die Unternehmenssicherheit:**

-   Unterstützung der Multi-Faktor-Authentifizierung durch Unternehmens-Identitätsprovider
-   Integration in bestehende Unternehmensidentitätsinfrastrukturen
-   Schutz vor gängigen Authentifizierungsangriffen (Token-Replay, Session Hijacking, CSRF)
-   Sicheres Token-Lebenszyklusmanagement mit Ablauf und Widerruf
-   HTTPS-only-Kommunikation für alle Authentifizierungsflüsse

**Best Practices für die Sicherheit:**

-   Zero-Trust-Sicherheitsmodell mit Authentifizierung, die für alle API-Zugriffe erforderlich ist
-   Trennung von Authentifizierungs- und Autorisierungsbelangen
-   Prinzip der geringsten Berechtigung durch ein granuläres Berechtigungssystem
-   Mehrschichtige Verteidigung (Defense in Depth) mit mehreren Sicherheitsebenen
-   Regelmässige Token-Validierungs- und Aktualisierungsmechanismen

Dieser standardbasierte Ansatz für Authentifizierung und Autorisierung stellt sicher, dass die Plattform die
Sicherheitsanforderungen von Unternehmen erfüllt und gleichzeitig mit Standard-Identitätsprovidern und
Sicherheitsinfrastrukturen interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte
Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, geprüft und vertrauenswürdig sind.
