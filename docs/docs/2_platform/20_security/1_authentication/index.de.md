---
title: Authentifizierung und Autorisierung
source_sha: 8ba9b3dc1a50bda545a43ebc5ad0aa883131548b0f30b1bcd0d238e2e1276c0d
---

# Authentifizierung und Autorisierung

Der Swiss AI Hub implementiert Authentifizierung und Autorisierung basierend auf den Industriestandard-Protokollen
OpenID Connect (OIDC) und OAuth 2.0. Dieser standardbasierte Ansatz gewährleistet Kompatibilität mit
Enterprise-Identity-Providern und sichert gleichzeitig die Zugangskontrolle über alle Plattformressourcen hinweg.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer über OpenID Connect, eine auf OAuth 2.0 aufbauende Identity-Schicht. Dies
ermöglicht eine sichere Benutzerauthentifizierung über Enterprise-Identity-Provider wie Microsoft Entra ID (Azure Active
Directory) und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### Wie die Authentifizierung funktioniert

**Token-basierte Authentifizierung:** Benutzer authentifizieren sich über den Identity-Provider ihrer Organisation, der
ein JSON Web Token (JWT) ausgibt, das kryptographisch signierte Claims über die Identität des Benutzers enthält. Die
Plattform validiert diese Tokens bei jeder Anfrage, um Authentizität und Aktualität zu gewährleisten.

**JWT Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS (JSON Web Key Set)-Endpunkt des
Identity-Providers ab und verwendet diese, um die kryptographische Signatur jedes JWT Tokens zu verifizieren. Diese
Validierung umfasst die Überprüfung des Token-Ausstellers, der Zielgruppe (Audience), der Ablaufzeit und der
Signaturintegrität gemäß dem JWT-Standard (RFC 7519).

**Benutzeridentitätsauflösung:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige
Benutzerkennung (OID) und grundlegende Profilinformationen (Name, E-Mail) aus den JWT Token-Claims. Rollenzuweisungen
werden lokal innerhalb der Plattform über Mandanten-spezifische Rollenentitäten verwaltet und nicht vom
Identity-Provider abgerufen.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth
2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den
Identity-Provider ihrer Organisation weitergeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren
Autorisierungscode, der gegen Access Tokens ausgetauscht wird.

**Bearer Token-Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die
Standard-OAuth 2.0 Bearer Token-Authentifizierung. API-Clients präsentieren gültige JWT Tokens im HTTP Authorization
Header, die mit demselben JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffskontrolle

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, was eine konsistente Zugriffskontrolle
ermöglicht, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform bewertet die Berechtigungen für jede
API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das in den
[Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

### Integration von Enterprise-Identity-Providern

Die Plattform integriert sich über Standard-OIDC-/OAuth 2.0-Protokolle in Enterprise-Identity-Provider. Jeder
OIDC-konforme Provider (Microsoft Entra ID, Google Workspace, Okta, Auth0, Keycloak) kann für die Authentifizierung
verwendet werden.

**Generische OIDC-Integration:** Die Plattform verbindet sich mit dem konfigurierten OIDC-Provider als OAuth 2.0
Autorisierungsserver und Identity-Provider. Die Benutzerauthentifizierung wird an den Provider delegiert, der die
Anmeldeinformationen-Validierung, Multi-Faktor-Authentifizierung und Sitzungsverwaltung gemäß den Sicherheitsrichtlinien
der Organisation handhabt.

**Lokale Rollenverwaltung:** Benutzerprofile werden aus JWT Token-Claims (Name, E-Mail, OID) extrahiert. Rollen werden
lokal innerhalb der Plattform durch Mandanten-spezifische Rollenzuweisungen verwaltet, nicht vom Identity-Provider
synchronisiert. Dies entkoppelt die Plattform-Autorisierung von einem spezifischen Gruppen- oder Rollenmodell eines
Identity-Providers.

### Wie die Autorisierung funktioniert

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines
Benutzers durch OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen
der Benutzer basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsbewertungsprozess:**

1. Die Plattform löst die Rollenzuweisungen des Benutzers aus der lokalen Mandanten-spezifischen Rollendatenbank auf
2. Jede Rolle ist mit einem Satz von Zugriffsregeln verbunden, die in der Plattformdatenbank gespeichert sind
3. Für jede API-Anfrage bewertet die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers
4. Zugriffsregeln unterstützen hierarchische Übereinstimmungen mit Wildcard-Mustern für eine flexible
   Berechtigungsverwaltung
5. Die Autorisierungsentscheidung (Gewährung oder Verweigerung) wird getroffen und zu Prüfzwecken protokolliert

**API-Level-Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese
Berechtigungen werden automatisch überprüft, bevor die Endpunktlogik ausgeführt wird, um sicherzustellen, dass kein
Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsbewertung verwendet das hierarchische Berechtigungsmodell,
das in den [Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform
programmatischen Zugriff auf das Berechtigungsbewertungssystem. Dies ermöglicht das Filtern von Ergebnismengen basierend
auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene Zugriffsebenen und
die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Dynamische Identity-Provider-Erkennung

Die Anmeldeseite erkennt dynamisch verfügbare Identity-Provider von Keycloak zur Laufzeit. Wenn ein Benutzer die
Anmeldeseite besucht, ruft das Frontend `GET /api/v1/auth-providers/` auf – einen nicht authentifizierten API-Endpunkt,
der die Keycloak Admin API unter Verwendung eines dedizierten Service-Accounts mit geringsten Privilegien
(`aihub-api-service`) und nur der `view-identity-providers`-Berechtigung abfragt.

Die API filtert die Providerliste, um nur aktivierte, sichtbare Provider aufzunehmen, und gibt deren Alias, Anzeigenamen
und Symbol zurück. Die Ergebnisse werden 5 Minuten lang zwischengespeichert. Das Frontend rendert für jeden Provider
einen gebrandeten Login-Button. Das Klicken auf einen Button initiiert den OIDC Authorization Code Flow, wobei
`kc_idp_hint` auf den Alias des Providers gesetzt wird, was den Benutzer direkt zum übergeordneten Identity-Provider
umleitet, ohne das Keycloak-Login-Theme anzuzeigen.

Dieser Ansatz eliminiert jegliche Frontend-Konfiguration für Identity-Provider – das Hinzufügen oder Entfernen eines IdP
ist eine reine Keycloak-Änderung. Details zur Begründung und Implementierung finden Sie unter
[ADR: Dynamisches Laden von Identity Providern](../../../../arc42/decisions/2026_02_27_dynamic_identity_provider_loading.md).

### Konfiguration von Provider-Symbolen

Jeder Identity-Provider kann ein benutzerdefiniertes Symbol auf seinem Login-Button anzeigen. Symbole werden direkt in
der `config`-Map des Keycloak Identity-Providers als `icon`-Feld unter Verwendung von PrimeIcon CSS-Klassen (z.B.
`pi-microsoft`, `pi-google`) konfiguriert. Provider ohne konfiguriertes Symbol greifen auf `pi-sign-in` zurück.

Um ein Symbol festzulegen, fügen Sie das `icon`-Feld zur Konfiguration des Identity-Providers in
`keycloak-identity-providers.json.j2` hinzu:

```json
"config": {
  "clientId": "...",
  "icon": "pi-microsoft"
}
```

### Direkter Keycloak-Login

Wenn `KEYCLOAK_SHOW_KEYCLOAK_LOGIN=true` (API-Umgebungsvariable, Standard: `true`), erscheint ein zusätzlicher "Login
mit Keycloak"-Button neben den föderierten Provider-Buttons. Dies ermöglicht die Anmeldung mit Benutzername/Passwort
über den eigenen Benutzer-Store von Keycloak – nützlich für Entwicklungsumgebungen oder Deployments, bei denen sich
einige Benutzer direkt mit Keycloak authentifizieren, anstatt über einen externen IdP.

## Admin Service-Authentifizierung über OAuth2 Proxy

Interne Admin-Services (Dagster, Attu, SeaweedFS) werden durch [OAuth2 Proxy](https://oauth2-proxy.github.io/)-Instanzen
geschützt, die vor jedem Service sitzen. OAuth2 Proxy wickelt den vollständigen OIDC-Login-Flow gegenüber Keycloak ab,
bevor authentifizierte Anfragen an den Upstream-Service weitergeleitet werden. Nur Benutzer mit der Rolle
`AIHubSysAdmin` können auf diese Services zugreifen.

Aufgrund des Split-Horizon-Netzwerks in Docker-Deployments (Container verwenden interne Hostnamen, Browser externe URLs)
wird die OIDC-Erkennung übersprungen und Endpunkte werden explizit konfiguriert. Die technische Begründung finden Sie
unter
[ADR: OIDC Discovery für OAuth2 Proxy überspringen](../../../../arc42/decisions/2026_02_26_skip_oidc_discovery_for_oauth2_proxy.md).

## Härtung: Keycloak Admin Console-Zugriff

Die Keycloak Admin Console (`https://auth.<domain>/admin/`) ist durch Benutzername und Passwort geschützt, aber
standardmäßig von jeder IP-Adresse aus zugänglich. Für Produktions-Deployments wird dringend empfohlen, den Zugriff auf
die Admin Console und den Metrik-Endpunkt auf bekannte Administrator-IP-Adressen zu beschränken.

### Empfehlung: IP-Allowlisting über Traefik

Die Plattform verwendet Traefik v3 als Reverse-Proxy. Die
[`ipAllowList`](https://doc.traefik.io/traefik/middlewares/http/ipallowlist/)-Middleware von Traefik kann den Zugriff
auf die Keycloak-Admin-Pfade einschränken, während die OIDC-Login-Endpunkte für alle Benutzer öffentlich zugänglich
bleiben.

**Implementierungsschritte:**

1. Fügen Sie eine Umgebungsvariable zu `.env` mit Ihren erlaubten IP-Bereichen hinzu:

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

Der öffentliche Router (Priorität 7000) bedient weiterhin OIDC-Endpunkte (`/realms/...`) ohne Einschränkung, während der
Admin-Router (Priorität 7500) `/admin`- und `/metrics`-Anfragen abfängt und Verbindungen von nicht zugelassenen IPs mit
einer `403 Forbidden`-Antwort ablehnt.

::: tip
Dasselbe Muster kann auf jeden über Traefik exponierten Service angewendet werden. Erwägen Sie auch, den Zugriff auf das
Traefik-Dashboard selbst einzuschränken, falls es in der Produktion aktiviert ist.
:::

## Keycloak Realm-Rollen und automatische Zuweisung

Keycloak verwaltet Realm-Level-Rollen, die bestimmen, ob ein Benutzer auf die Plattform zugreifen darf. Diese Rollen
sind grobe Zugangstore – fein abgestufte Berechtigungen werden lokal von der Plattform verwaltet (siehe
[Berechtigungen](../../11_access_management/2_permissions/)).

| Rolle            | Zweck                                                                                                                |
| ---------------- | -------------------------------------------------------------------------------------------------------------------- |
| `AIHubAccess`    | Erforderlich für den Plattform-Login. Benutzern ohne diese Rolle wird der Zugriff im Keycloak-Login-Flow verweigert. |
| `AIHubAdmin`     | Voller administrativer Zugriff                                                                                       |
| `AIHubUser`      | Standard-Benutzerzugriff                                                                                             |
| `AIHubDeveloper` | Zugriff auf Entwickler-Tools (Dagster, Attu, etc.)                                                                   |
| `AIHubSysAdmin`  | Systemadministrator-Zugriff auf Infrastruktur-Tools                                                                  |

Standardmäßig werden neuen Benutzern keine Rollen automatisch zugewiesen. Dies stellt sicher, dass Benutzer, die von
einem externen Identity-Provider föderiert werden, nur die Rollen erhalten, die explizit aus ihren IdP-Claims abgebildet
wurden, gemäß dem Prinzip der geringsten Privilegien.

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

**Option 2: Identity Provider-Mapper (gilt pro IdP)**

Für eine granularere Kontrolle konfigurieren Sie Rollen-Mapper bei einzelnen Identity-Providern. Dies ermöglicht
unterschiedliche Rollen für Benutzer aus verschiedenen Organisationen. Navigieren Sie in der Keycloak Admin Console zu
**Identity Providers > [Ihr IdP] > Mappers** und fügen Sie einen **Hardcoded Role**-Mapper hinzu:

| Feld        | Wert                |
| ----------- | ------------------- |
| Name        | `default-user-role` |
| Mapper Type | Hardcoded Role      |
| Rolle       | `AIHubUser`         |

Dies weist die Rolle nur Benutzern zu, die sich über diesen spezifischen Identity-Provider authentifizieren.

**Option 3: Claim-basierte Rollenzuweisung (bedingte Zuweisung)**

Für die bedingte Rollenzuweisung basierend auf IdP-Claims (z.B. Azure AD App-Rollen) verwenden Sie das bestehende
`oidc-role-idp-mapper`-Muster, das bereits in `keycloak-identity-providers.json.j2` konfiguriert ist. Jede Azure AD
App-Rolle wird einer entsprechenden Keycloak-Realm-Rolle zugeordnet. Um eine neue Zuordnung hinzuzufügen, fügen Sie
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
Die Rolle `AIHubAccess` wird auf Ebene des Keycloak-Login-Flows über den Authentifizierungs-Flow "Post Broker Login -
AIHubAccess Check" durchgesetzt. Benutzern ohne diese Rolle wird der Zugriff verweigert, unabhängig von anderen
Rollenzuweisungen. Stellen Sie sicher, dass Ihre Rollenmapping-Strategie `AIHubAccess` für Benutzer einschließt, die
sich anmelden können sollen.
:::

## Sicherheitsstandards und operationale Fähigkeiten

### Standardkonformität

Die Implementierung der Authentifizierung und Autorisierung hält sich an Industriestandard-Protokolle und
-Spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

- OpenID Connect Core 1.0 für die Authentifizierung
- OAuth 2.0 Authorization Framework (RFC 6749)
- OAuth 2.0 Authorization Code Flow mit PKCE
- JSON Web Token (JWT) - RFC 7519
- JSON Web Key Set (JWKS) - RFC 7517
- OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptographische Sicherheit:** Alle JWT Tokens werden unter Verwendung von RSA-256 kryptographischen Signaturen
validiert. Öffentliche Schlüssel werden vom JWKS-Endpunkt des Identity-Providers abgerufen und zur Leistungsverbesserung
zwischengespeichert. Die Token-Validierung umfasst Signaturprüfung, Aussteller-Validierung, Audience-Validierung und
Ablaufprüfung bei jeder Anfrage.

### Audit und Monitoring

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und
Sicherheitsüberwachungszwecke protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen,
Berechtigungsbewertungen, Zugriffsentscheidungen und den vollständigen Anfragekontext.

**Sicherheitsereignisprotokollierung:** Die Plattform integriert sich in OpenTelemetry-Standards, um strukturierte,
nachverfolgbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über
verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheitsüberwachung:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler,
Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht eine schnelle
Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Unternehmens-Compliance

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und
Unternehmens-Sicherheitsstandards:

**Datenschutz-Compliance:**

- DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
- Einhaltung des Schweizer Datenschutzgesetzes durch selbstgehostete Deployment-Optionen
- Umfassende Audit-Trails zur Erfüllung regulatorischer Anforderungen an die Zugriffsprotokollierung
- Datenhoheit durch On-Premises- oder Schweizer Cloud-Deployment aufrechterhalten

**Anforderungen an die Unternehmenssicherheit:**

- Unterstützung der Multi-Faktor-Authentifizierung durch Enterprise-Identity-Provider
- Integration in bestehende Enterprise-Identity-Infrastruktur
- Schutz vor gängigen Authentifizierungsangriffen (Token-Replay, Session Hijacking, CSRF)
- Sicheres Token-Lifecycle-Management mit Ablauf und Widerruf
- Nur HTTPS-Kommunikation für alle Authentifizierungs-Flows

**Best Practices für Sicherheit:**

- Zero-Trust-Sicherheitsmodell mit Authentifizierungspflicht für alle API-Zugriffe
- Trennung von Authentifizierungs- und Autorisierungsbelangen
- Prinzip der geringsten Privilegien durch ein granuläres Berechtigungssystem
- Defense in Depth mit mehreren Schichten von Sicherheitskontrollen
- Regelmäßige Token-Validierung und Refresh-Mechanismen

Dieser standardbasierte Ansatz für Authentifizierung und Autorisierung stellt sicher, dass die Plattform die
Anforderungen an die Unternehmenssicherheit erfüllt und gleichzeitig mit Standard-Identity-Providern und der
Sicherheitsinfrastruktur interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte
Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, geprüft und vertraut sind.
