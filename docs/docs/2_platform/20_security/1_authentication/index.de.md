---
title: Authentifizierung und Autorisierung
source_sha: 50b10d4f1012632658dacf0ba16809b2a98a6aa4f1ce7d53beb127960b67de89
---

# Authentifizierung und Autorisierung

Der Swiss AI Hub implementiert Authentifizierung und Autorisierung basierend auf den branchenüblichen OpenID Connect
(OIDC)- und OAuth 2.0-Protokollen. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit Identity
Providern von Unternehmen und ermöglicht gleichzeitig eine sichere Zugriffskontrolle über alle Plattformressourcen.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer mittels OpenID Connect, einer Identitätsschicht, die auf OAuth 2.0 aufbaut. Dies
ermöglicht eine sichere Benutzerauthentifizierung über Identity Provider von Unternehmen wie Microsoft Entra ID (Azure
Active Directory) und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### Wie die Authentifizierung funktioniert

**Token-basierte Authentifizierung:** Benutzer authentifizieren sich über den Identity Provider ihrer Organisation, der
ein JSON Web Token (JWT) ausgibt, das kryptographisch signierte Claims über die Identität des Benutzers enthält. Die
Plattform validiert diese Tokens bei jeder Anfrage, um Authentizität und Aktualität sicherzustellen.

**JWT-Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS (JSON Web Key Set)-Endpunkt des Identity
Providers ab und verwendet diese, um die kryptographische Signatur jedes JWT-Tokens zu verifizieren. Diese Validierung
umfasst die Überprüfung des Ausstellers, der Zielgruppe, der Ablaufzeit und der Signaturintegrität des Tokens gemäß dem
JWT-Standard (RFC 7519).

**Auflösung der Benutzeridentität:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige
Benutzerkennung (OID) und grundlegende Profilinformationen (Name, E-Mail) aus den JWT-Token-Claims. Rollenzuweisungen
werden lokal innerhalb der Plattform über Mandanten-spezifische Rollenentitäten verwaltet und nicht vom Identity
Provider abgerufen.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth
2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den
Identity Provider ihrer Organisation weitergeleitet und erhalten nach erfolgreichem Login einen sicheren
Autorisierungscode, der gegen Access Tokens ausgetauscht wird.

**Bearer-Token-Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die
standardmäßige OAuth 2.0 Bearer-Token-Authentifizierung. API-Clients präsentieren gültige JWT-Tokens im HTTP
Authorization-Header, die mithilfe desselben JWKS-basierten Verifizierungsprozesses validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffskontrolle

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, wodurch eine konsistente Zugriffskontrolle
gewährleistet wird, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform evaluiert Berechtigungen für
jede API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das
unter [Berechtigungen](/de/docs/11_access_management/2_permissions/) beschrieben ist.

### Integration von Enterprise Identity Providern

Die Plattform integriert sich mit Enterprise Identity Providern über standardmäßige OIDC-/OAuth 2.0-Protokolle. Jeder
OIDC-konforme Provider (Microsoft Entra ID, Google Workspace, Okta, Auth0, Keycloak) kann zur Authentifizierung
verwendet werden.

**Generische OIDC-Integration:** Die Plattform verbindet sich mit dem konfigurierten OIDC-Provider als OAuth
2.0-Autorisierungsserver und Identity Provider. Die Benutzerauthentifizierung wird an den Provider delegiert, der die
Überprüfung der Anmeldeinformationen, die Multi-Faktor-Authentifizierung und die Sitzungsverwaltung gemäß den
Sicherheitsrichtlinien der Organisation handhabt.

**Lokale Rollenverwaltung:** Benutzerprofile werden aus JWT-Token-Claims (Name, E-Mail, OID) extrahiert. Rollen werden
lokal innerhalb der Plattform über Mandanten-spezifische Rollenzuweisungen verwaltet und nicht vom Identity Provider
synchronisiert. Dies entkoppelt die Plattform-Autorisierung von einem spezifischen Gruppen- oder Rollenmodell eines
Identity Providers.

### Wie die Autorisierung funktioniert

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines
Benutzers durch die OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und
Operationen der Benutzer basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsevaluierungsprozess:**

1. Die Plattform löst die Rollenzuweisungen des Benutzers aus der lokalen, Mandanten-spezifischen Rollendatenbank auf.
2. Jede Rolle ist mit einem Satz von Zugriffsregeln verknüpft, die in der Plattformdatenbank gespeichert sind.
3. Für jede API-Anfrage evaluiert die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers.
4. Zugriffsregeln unterstützen hierarchisches Matching mit Wildcard-Mustern für eine flexible Berechtigungsverwaltung.
5. Die Autorisierungsentscheidung (Gewährung oder Verweigerung) wird getroffen und zu Prüfzwecken protokolliert.

**API-Level-Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese
Berechtigungen werden automatisch überprüft, bevor die Endpunkt-Logik ausgeführt wird, um sicherzustellen, dass kein
Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsevaluierung verwendet das hierarchische
Berechtigungsmodell, das unter [Berechtigungen](/de/docs/11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform
programmatischen Zugriff auf das Berechtigungsevaluierungssystem. Dies ermöglicht das Filtern von Ergebnismengen
basierend auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene
Zugriffsebenen und die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Dynamische Erkennung von Identity Providern

Die Login-Seite erkennt verfügbare Identity Provider von Keycloak dynamisch zur Laufzeit. Wenn ein Benutzer die
Login-Seite besucht, ruft das Frontend `GET /api/v1/{tenant_id}/auth-providers/` auf – einen nicht authentifizierten
API-Endpunkt, der die Keycloak Admin API unter Verwendung eines dedizierten Service-Kontos mit geringsten Rechten
(`aihub-api-service`) und nur der `view-identity-providers`-Berechtigung abfragt.

Die API filtert die Provider-Liste, um nur aktivierte, sichtbare Provider einzuschließen und gibt deren Alias,
Anzeigenamen und Icon zurück. Die Ergebnisse werden für 5 Minuten zwischengespeichert. Das Frontend rendert einen
gebrandeten Login-Button für jeden Provider. Durch Klicken auf einen Button wird der OIDC Authorization Code Flow mit
`kc_idp_hint`, der auf den Alias des Providers gesetzt ist, initiiert und der Benutzer direkt zum vorgelagerten Identity
Provider weitergeleitet, ohne Keycloaks Login-Theme anzuzeigen.

Dieser Ansatz eliminiert jede Frontend-Konfiguration für Identity Provider – das Hinzufügen oder Entfernen eines IdP ist
eine reine Keycloak-Änderung.

### Konfiguration von Provider-Icons

Jeder Identity Provider kann ein benutzerdefiniertes Icon auf seinem Login-Button anzeigen. Icons werden direkt in der
`config`-Map des Keycloak Identity Providers als `icon`-Feld unter Verwendung von PrimeIcon CSS-Klassen (z.B.
`pi-microsoft`, `pi-google`) konfiguriert. Provider ohne konfiguriertes Icon greifen auf `pi-sign-in` zurück.

Um ein Icon festzulegen, fügen Sie das `icon`-Feld zur Konfiguration des Identity Providers in
`keycloak-identity-providers.json.j2` hinzu:

```json
"config": {
  "clientId": "...",
  "icon": "pi-microsoft"
}
```

### Direkter Keycloak-Login

Wenn `KEYCLOAK_SHOW_KEYCLOAK_LOGIN=true` (API-Umgebungsvariable, Standard: `true`), erscheint ein zusätzlicher „Login
mit Keycloak“-Button neben den Buttons der föderierten Provider. Dies ermöglicht die Benutzername/Passwort-Anmeldung
über den eigenen Benutzer-Store von Keycloak – nützlich für Entwicklungsumgebungen oder Deployments, bei denen einige
Benutzer sich direkt bei Keycloak anstatt über einen externen IdP authentifizieren.

## Authentifizierung von Admin-Services über OAuth2 Proxy

Interne Admin-Services (Dagster, Attu, SeaweedFS) werden durch [OAuth2 Proxy](https://oauth2-proxy.github.io/)-Instanzen
geschützt, die vor jedem Service sitzen. OAuth2 Proxy handhabt den vollständigen OIDC-Login-Flow gegenüber Keycloak,
bevor authentifizierte Anfragen an den vorgelagerten Service weitergeleitet werden. Nur Benutzer mit der Rolle
`AIHubSysAdmin` können auf diese Services zugreifen.

Aufgrund des Split-Horizon-Netzwerks in Docker-Deployments (Container verwenden interne Hostnamen, Browser externe URLs)
wird die OIDC-Erkennung übersprungen und Endpunkte werden explizit konfiguriert.

## Härtung: Zugriff auf die Keycloak Admin Console

Die Keycloak Admin Console (`https://auth.<domain>/admin/`) ist durch Benutzername und Passwort geschützt, aber
standardmäßig von jeder IP-Adresse aus zugänglich. Für Produktions-Deployments wird dringend empfohlen, den Zugriff auf
die Admin Console und den Metrik-Endpunkt auf bekannte Administrator-IP-Adressen zu beschränken.

### Empfohlen: IP-Allowlisting via Traefik

Die Plattform verwendet Traefik v3 als Reverse Proxy. Traefiks
[`ipAllowList`](https://doc.traefik.io/traefik/middlewares/http/ipallowlist/)-Middleware kann den Zugriff auf die
Keycloak Admin-Pfade einschränken, während die OIDC-Login-Endpunkte für alle Benutzer öffentlich zugänglich bleiben.

**Implementierungsschritte:**

1. Fügen Sie eine Umgebungsvariable zu `.env` mit Ihren zulässigen IP-Bereichen hinzu:

   ```bash
   KEYCLOAK_ADMIN_ALLOWED_IPS="203.0.113.0/24,198.51.100.10/32"
   ```

2. Fügen Sie in `docker-compose.yml` einen zweiten Traefik-Router für Admin-Pfade zu den `keycloak`-Service-Labels hinzu
   (neben dem bestehenden `keycloak`-Router):

   ```yaml
   # Admin-only router with IP restriction (higher priority than public router)
   - "traefik.http.routers.keycloak-admin.rule=Host(`auth.${DOMAIN}`) && (PathPrefix(`/admin`) || PathPrefix(`/metrics`))"
   - "traefik.http.routers.keycloak-admin.entrypoints=websecure"
   - "traefik.http.routers.keycloak-admin.tls=true"
   - "traefik.http.routers.keycloak-admin.priority=7500"
   - "traefik.http.routers.keycloak-admin.middlewares=keycloak-admin-ipallowlist,keycloak-security-headers"
   - "traefik.http.routers.keycloak-admin.service=keycloak"
   # IP allowlist middleware
   - "traefik.http.middlewares.keycloak-admin-ipallowlist.ipallowlist.sourcerange=${KEYCLOAK_ADMIN_ALLOWED_IPS}"
   ```

Der öffentliche Router (Priorität 7000) dient weiterhin OIDC-Endpunkten (`/realms/...`) ohne Einschränkung, während der
Admin-Router (Priorität 7500) Anfragen an `/admin` und `/metrics` abfängt und Verbindungen von nicht-allowgelisteten IPs
mit einer `403 Forbidden`-Antwort ablehnt.

::: tip
Das gleiche Muster kann auf jeden über Traefik exponierten Service angewendet werden. Erwägen Sie auch, den Zugriff auf
das Traefik-Dashboard selbst zu beschränken, wenn es in der Produktion aktiviert ist.
:::

## Keycloak Realm-Rollen und automatische Zuweisung

Keycloak verwaltet Realm-Level-Rollen, die bestimmen, ob ein Benutzer auf die Plattform zugreifen darf. Diese Rollen
sind grobe Zugangstore – fein abgestufte Berechtigungen werden lokal von der Plattform über Mandanten-spezifische Rollen
verwaltet (siehe [Berechtigungen](/de/docs/11_access_management/2_permissions/)).

Zwei Realm-Rollen treten in der Plattform in Kraft:

| Rolle           | Effekt                                                                                                                                                         |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AIHubAccess`   | Für den Plattform-Login erforderlich. Benutzer ohne diese Rolle werden im Keycloak Login Flow abgelehnt.                                                       |
| `AIHubSysAdmin` | Plattform-Administrator. Wird vom Token gelesen, um Admin-Zugriff zu gewähren und die OAuth2-Proxy Admin-Tools (Dagster, Attu, SeaweedFS, Backup) zu schützen. |

::: info Realm-Rollen vs. Plattform-Rollen
Das `aihub`-Realm definiert nur diese beiden Rollen. Fein abgestufte, alltägliche Berechtigungen werden separat von
**Mandanten-spezifischen Rollen** gehandhabt, die innerhalb der Plattform verwaltet werden – diese können Namen wie
`AIHubUser` oder `AIHubAdmin` tragen, sind aber unabhängig von Keycloak Realm-Rollen und werden nicht vom IdP
abgeleitet. Weisen Sie in Ihrem Identity Provider nur `AIHubAccess` und `AIHubSysAdmin` zu.

Für die Operator-Einrichtung der Azure App-Registrierung und Rollenzuweisung siehe
[Identity Provider Einrichtung](/de/docs/3_deployment_guide/10_identity_provider_setup/).
:::

Standardmäßig werden neuen Benutzern keine Rollen automatisch zugewiesen. Dies stellt sicher, dass Benutzer, die von
einem externen Identity Provider föderiert werden, nur die Rollen erhalten, die explizit aus ihren IdP-Claims abgebildet
wurden, gemäß dem Prinzip der geringsten Rechte.

### Konfiguration der automatischen Rollenzuweisung

Wenn Ihr Deployment erfordert, dass alle neuen Benutzer eine Standardrolle (z.B. `AIHubUser`) erhalten, kann dies in
Keycloak konfiguriert werden:

**Option 1: Realm-Standardrollen (gilt für alle neuen Benutzer)**

Navigieren Sie in der Keycloak Admin Console zu **Realm Settings > User Registration > Default Roles** und fügen Sie die
gewünschten Rollen hinzu. Alternativ können Sie das `defaultRoles`-Array in der Realm-Konfigurationsvorlage
(`keycloak-realm.json.j2`) festlegen:

```json
"defaultRoles": ["AIHubUser"]
```

**Option 2: Identity Provider Mapper (gilt pro IdP)**

Für eine granularere Kontrolle konfigurieren Sie Rollen-Mapper auf einzelnen Identity Providern. Dies ermöglicht
unterschiedliche Rollen für Benutzer aus verschiedenen Organisationen. Navigieren Sie in der Keycloak Admin Console zu
**Identity Providers > [Ihr IdP] > Mappers** und fügen Sie einen **Hardcoded Role** Mapper hinzu:

| Feld        | Wert                |
| ----------- | ------------------- |
| Name        | `default-user-role` |
| Mapper Type | Hardcoded Role      |
| Role        | `AIHubUser`         |

Dies weist die Rolle nur Benutzern zu, die sich über diesen spezifischen Identity Provider authentifizieren.

**Option 3: Claim-basierte Rollenzuweisung (bedingte Zuweisung)**

Für die bedingte Rollenzuweisung basierend auf IdP-Claims (z.B. Azure AD App-Rollen) verwenden Sie das bestehende
`oidc-role-idp-mapper`-Muster, das bereits in `keycloak-identity-providers.json.j2` konfiguriert ist. Jede Azure AD
App-Rolle wird einer entsprechenden Keycloak Realm-Rolle zugeordnet. Um eine neue Zuordnung hinzuzufügen, fügen Sie
einen Eintrag zum `identityProviderMappers`-Array hinzu:

```json
{
  "name": "role-mapper-my-role",
  "identityProviderAlias": "azure-ad",
  "identityProviderMapper": "oidc-role-idp-mapper",
  "config": {
    "syncMode": "INHERIT",
    "claim": "roles",
    "claim.value": "MyAzureAppRole",
    "role": "AIHubUser"
  }
}
```

::: warning
Die Rolle `AIHubAccess` wird auf Ebene des Keycloak Login Flows über den Authentifizierungsfluss „Post Broker Login -
AIHubAccess Check“ erzwungen. Benutzer ohne diese Rolle wird der Zugriff verweigert, unabhängig von anderen
Rollenzuweisungen. Stellen Sie sicher, dass Ihre Rollenzuweisungsstrategie `AIHubAccess` für Benutzer einschließt, die
sich anmelden können sollen.
:::

## Sicherheitsstandards und operative Fähigkeiten

### Standardkonformität

Die Implementierung von Authentifizierung und Autorisierung entspricht branchenüblichen Protokollen und Spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

- OpenID Connect Core 1.0 zur Authentifizierung
- OAuth 2.0 Authorization Framework (RFC 6749)
- OAuth 2.0 Authorization Code Flow mit PKCE
- JSON Web Token (JWT) - RFC 7519
- JSON Web Key Set (JWKS) - RFC 7517
- OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptographische Sicherheit:** Alle JWT-Tokens werden mithilfe von RSA-256 kryptographischen Signaturen validiert.
Öffentliche Schlüssel werden vom JWKS-Endpunkt des Identity Providers abgerufen und zur Leistungsoptimierung
zwischengespeichert. Die Token-Validierung umfasst die Signaturprüfung, Aussteller-Validierung, Zielgruppen-Validierung
und die Überprüfung der Ablaufzeit bei jeder Anfrage.

### Audit und Monitoring

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und
Sicherheitsüberwachungszwecke protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen,
Berechtigungsevaluierungen, Zugriffsentscheidungen und den vollständigen Anforderungskontext.

**Sicherheitsereignisprotokollierung:** Die Plattform integriert sich mit OpenTelemetry-Standards, um strukturierte,
nachvollziehbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über
verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheitsüberwachung:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler,
Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht die schnelle
Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Unternehmenskonformität

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und
Unternehmenssicherheitsstandards:

**Datenschutzkonformität:**

- GDPR-konforme Benutzerauthentifizierung und Datenverarbeitung
- Einhaltung des Schweizer Datenschutzgesetzes durch selbst gehostete Deployment-Optionen
- Umfassende Audit-Trails, die die regulatorischen Anforderungen an die Zugriffsprotokollierung erfüllen
- Datensouveränität durch On-Premises- oder Schweizer Cloud-Deployment gewahrt

**Anforderungen an die Unternehmenssicherheit:**

- Multi-Faktor-Authentifizierungsunterstützung durch Enterprise Identity Provider
- Integration in bestehende Unternehmens-Identity-Infrastruktur
- Schutz vor gängigen Authentifizierungsangriffen (Token Replay, Session Hijacking, CSRF)
- Sicheres Token-Lifecycle-Management mit Ablauf und Widerruf
- Nur HTTPS-Kommunikation für alle Authentifizierungsflüsse

**Best Practices für Sicherheit:**

- Zero-Trust-Sicherheitsmodell mit Authentifizierung, die für jeden API-Zugriff erforderlich ist
- Trennung von Authentifizierungs- und Autorisierungsanliegen
- Prinzip der geringsten Rechte durch granular abgestuftes Berechtigungssystem
- Defense-in-Depth mit mehreren Schichten von Sicherheitskontrollen
- Regelmäßige Token-Validierungs- und Aktualisierungsmechanismen

Dieser standardbasierte Ansatz für Authentifizierung und Autorisierung stellt sicher, dass die Plattform die
Sicherheitsanforderungen von Unternehmen erfüllt und gleichzeitig mit Standard-Identity-Providern und
Sicherheitsinfrastrukturen interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte
Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, geprüft und vertraut sind.
