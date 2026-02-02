---
title: Authentifizierung und Autorisierung
source_sha: 1fa440c3e30359d7544ba987107b5abe10a55fa42f4d6e156c4b33e81f87ea08
---

# TODO: @mhoegger verify

# Authentifizierung und Autorisierung

Der Swiss AI-Hub implementiert Authentifizierung und Autorisierung basierend auf den branchenüblichen Protokollen OpenID
Connect (OIDC) und OAuth 2.0. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit Enterprise Identity
Providern und sichert gleichzeitig die Zugriffskontrolle über alle Plattformressourcen hinweg.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer über OpenID Connect, eine Identitätsschicht, die auf OAuth 2.0 aufbaut. Dies
ermöglicht eine sichere Benutzerauthentifizierung über Enterprise Identity Provider wie Microsoft Entra ID (Azure Active
Directory) und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### Wie die Authentifizierung funktioniert

**Tokenbasierte Authentifizierung:** Benutzer authentifizieren sich über den Identity Provider ihrer Organisation, der
einen JSON Web Token (JWT) ausgibt. Dieser JWT enthält kryptografisch signierte Claims über die Identität des Benutzers.
Die Plattform validiert diese Tokens bei jeder Anfrage, um deren Authentizität und Aktualität sicherzustellen.

**JWT Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS-Endpoint (JSON Web Key Set) des Identity
Providers ab und verwendet diese, um die kryptografische Signatur jedes JWT-Tokens zu überprüfen. Diese Validierung
umfasst die Überprüfung des Ausstellers, der Zielgruppe, der Ablaufzeit und der Signaturintegrität des Tokens gemäß dem
JWT-Standard (RFC 7519).

**Benutzeridentitätsauflösung:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige
Benutzerkennung (OID) aus den Token-Claims und ruft über die Microsoft Graph API vollständige Benutzerinformationen,
einschließlich Name, E-Mail und Rollenzuweisungen, vom Identity Provider ab.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth
2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den
Identity Provider ihrer Organisation weitergeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren
Autorisierungscode, der gegen Access Tokens ausgetauscht wird.

**Bearer Token-Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die
standardmäßige OAuth 2.0 Bearer Token-Authentifizierung. API-Clients übergeben gültige JWT-Tokens im HTTP Authorization
Header, welche mit demselben JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffskontrolle

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, was eine konsistente Zugriffskontrolle
ermöglicht, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform evaluiert Berechtigungen für jede
API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das unter
[Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

### Integration mit Enterprise Identity Providern

Die Plattform integriert sich über standardisierte OIDC/OAuth 2.0 Protokolle mit Enterprise Identity Providern. Der
primäre Integrationspunkt ist Microsoft Entra ID (Azure Active Directory), wobei die Erweiterbarkeit auf andere
OIDC-konforme Identity Provider unterstützt wird.

**Microsoft Entra ID Integration:** Die Plattform verbindet sich mit Microsoft Entra ID als OAuth 2.0
Autorisierungsserver und OIDC Identity Provider. Die Benutzerauthentifizierung wird an Entra ID delegiert, welches die
Überprüfung der Anmeldeinformationen, die Multi-Faktor-Authentifizierung und die Sitzungsverwaltung gemäß den
Sicherheitsrichtlinien der Organisation handhabt.

**Abruf von Benutzerprofilen und Rollen:** Nach der Authentifizierung fragt die Plattform die Microsoft Graph API ab, um
vollständige Benutzerprofile, einschließlich Anzeigename, E-Mail-Adresse und Mitgliedschaften in Organisationsgruppen,
abzurufen. Diese Gruppenmitgliedschaften werden Plattformrollen zugeordnet, die die Zugriffsrechte des Benutzers
innerhalb des AI-Hubs bestimmen.

### Wie die Autorisierung funktioniert

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines
Benutzers durch OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen
der Benutzer basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsevaluierungsprozess:**

1. Die Plattform extrahiert die Rollenzuweisungen des Benutzers vom Identity Provider.
2. Jede Rolle ist mit einem Satz von Zugriffsregeln verknüpft, die in der Plattformdatenbank gespeichert sind.
3. Für jede API-Anfrage evaluiert die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers.
4. Zugriffsregeln unterstützen hierarchische Übereinstimmungen mit Wildcard-Mustern für ein flexibles
   Berechtigungsmanagement.
5. Die Autorisierungsentscheidung (Gewährung oder Verweigerung) wird getroffen und zu Audit-Zwecken protokolliert.

**API-Ebenen-Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese
Berechtigungen werden automatisch überprüft, bevor die Endpunktlogik ausgeführt wird, wodurch sichergestellt wird, dass
kein Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsevaluierung verwendet das hierarchische
Berechtigungsmodell, das unter [Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform
programmatischen Zugriff auf das Berechtigungsevaluierungssystem. Dies ermöglicht das Filtern von Ergebnismengen
basierend auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene
Zugriffsebenen und die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Sicherheitsstandards und operationale Fähigkeiten

### Standardkonformität

Die Implementierung von Authentifizierung und Autorisierung hält sich an branchenübliche Protokolle und Spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

- OpenID Connect Core 1.0 für die Authentifizierung
- OAuth 2.0 Authorization Framework (RFC 6749)
- OAuth 2.0 Authorization Code Flow mit PKCE
- JSON Web Token (JWT) - RFC 7519
- JSON Web Key Set (JWKS) - RFC 7517
- OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptografische Sicherheit:** Alle JWT-Tokens werden unter Verwendung von kryptografischen RSA-256-Signaturen
validiert. Öffentliche Schlüssel werden vom JWKS-Endpoint des Identity Providers abgerufen und zur Leistungsverbesserung
zwischengespeichert. Die Token-Validierung umfasst die Signaturprüfung, die Ausstellerprüfung, die Zielgruppenprüfung
und die Ablaufprüfung bei jeder Anfrage.

### Audit und Überwachung

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und
Sicherheitsüberwachungszwecke protokolliert. Dies umfasst die Benutzeridentität, angeforderte Ressourcen,
Berechtigungsevaluierungen, Zugriffsentscheidungen und den vollständigen Anfragekontext.

**Protokollierung von Sicherheitsereignissen:** Die Plattform integriert sich in OpenTelemetry-Standards, um
strukturierte, nachvollziehbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von
Sicherheitsereignissen über verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für
Audit-Trails.

**Echtzeit-Sicherheitsüberwachung:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler,
Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht die schnelle
Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Unternehmenskonformität

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und
Unternehmenssicherheitsstandards:

**Datenschutzkonformität:**

- DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
- Einhaltung des Schweizer Datenschutzgesetzes durch Self-Hosted-Deployment-Optionen
- Umfassende Audit-Trails, die regulatorische Anforderungen für die Zugriffsprotokollierung erfüllen
- Datenhoheit durch On-Premises- oder Schweizer Cloud-Deployment gewahrt

**Anforderungen an die Unternehmenssicherheit:**

- Unterstützung der Multi-Faktor-Authentifizierung durch Enterprise Identity Provider
- Integration in die bestehende Unternehmens-Identitätsinfrastruktur
- Schutz vor gängigen Authentifizierungsangriffen (Token-Replay, Session Hijacking, CSRF)
- Sicheres Token-Lifecycle-Management mit Ablauf und Widerruf
- HTTPS-only-Kommunikation für alle Authentifizierungsflüsse

**Bewährte Sicherheitspraktiken:**

- Zero-Trust-Sicherheitsmodell mit erforderlicher Authentifizierung für jeden API-Zugriff
- Trennung von Authentifizierungs- und Autorisierungsbelangen
- Prinzip der geringsten Rechte durch ein granular Berechtigungssystem
- Defense in Depth mit mehreren Schichten von Sicherheitskontrollen
- Regelmäßige Token-Validierungs- und Refresh-Mechanismen

Dieser standardbasierte Ansatz für Authentifizierung und Autorisierung stellt sicher, dass die Plattform die
Sicherheitsanforderungen von Unternehmen erfüllt und gleichzeitig mit Standard-Identity Providern und
Sicherheitsinfrastrukturen interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte
Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, auditiert und vertraut sind.
