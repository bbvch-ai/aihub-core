---
title: Authentifizierung und Autorisierung
source_sha: 18e217226f9c432c5d90abe9f5ab364a2dfc8e8523885a237826d9c89dc946b7
---

# Authentifizierung und Autorisierung

Der Swiss AI Hub implementiert Authentifizierung und Autorisierung basierend auf den Industriestandard-Protokollen
OpenID Connect (OIDC) und OAuth 2.0. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit Enterprise
Identity Providern und sorgt gleichzeitig für eine sichere Zugriffskontrolle über alle Plattformressourcen hinweg.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer über OpenID Connect, eine Identitätsschicht, die auf OAuth 2.0 aufbaut. Dies
ermöglicht eine sichere Benutzerauthentifizierung über Enterprise Identity Provider wie Microsoft Entra ID (Azure Active
Directory) und unterstützt gleichzeitig den OAuth 2.0 Authorization Code Flow.

### So funktioniert die Authentifizierung

**Token-basierte Authentifizierung:** Benutzer authentifizieren sich über den Identity Provider ihrer Organisation, der
ein JSON Web Token (JWT) ausstellt, das kryptografisch signierte Claims über die Identität des Benutzers enthält. Die
Plattform validiert diese Tokens bei jeder Anfrage, um deren Authentizität und Aktualität zu gewährleisten.

**JWT Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS (JSON Web Key Set)-Endpunkt des Identity
Providers ab und verwendet diese, um die kryptografische Signatur jedes JWT Tokens zu verifizieren. Diese Validierung
umfasst die Überprüfung des Ausstellers, der Zielgruppe, der Ablaufzeit und der Signaturintegrität des Tokens gemäss dem
JWT-Standard (RFC 7519).

**Auflösung der Benutzeridentität:** Nach erfolgreicher Token-Validierung extrahiert die Plattform die eindeutige
Benutzerkennung (OID) und grundlegende Profilinformationen (Name, E-Mail) aus den JWT Token-Claims. Rollenzuweisungen
werden lokal innerhalb der Plattform über Mandanten-bezogene Rollenentitäten verwaltet und nicht vom Identity Provider
abgerufen.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth
2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den
Identity Provider ihrer Organisation weitergeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren
Autorisierungscode, der gegen Access Tokens ausgetauscht wird.

**Bearer Token Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die
Standard-OAuth 2.0 Bearer Token Authentifizierung. API-Clients präsentieren gültige JWT Tokens im HTTP Authorization
Header, die mit demselben JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffskontrolle

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, was eine konsistente Zugriffskontrolle
ermöglicht, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform bewertet Berechtigungen für jede
API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das unter
[Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

### Integration von Enterprise Identity Providern

Die Plattform integriert sich über standardisierte OIDC/OAuth 2.0-Protokolle mit Enterprise Identity Providern. Jeder
OIDC-konforme Provider (Microsoft Entra ID, Google Workspace, Okta, Auth0, Keycloak) kann zur Authentifizierung
verwendet werden.

**Generische OIDC-Integration:** Die Plattform verbindet sich mit dem konfigurierten OIDC-Provider als OAuth 2.0
Autorisierungsserver und Identity Provider. Die Benutzerauthentifizierung wird an den Provider delegiert, der die
Anmeldeinformationen-Validierung, Multi-Faktor-Authentifizierung und Sitzungsverwaltung gemäss den
Sicherheitsrichtlinien der Organisation handhabt.

**Lokale Rollenverwaltung:** Benutzerprofile werden aus JWT Token-Claims (Name, E-Mail, OID) extrahiert. Rollen werden
lokal innerhalb der Plattform über Mandanten-bezogene Rollenzuweisungen verwaltet und nicht vom Identity Provider
synchronisiert. Dies entkoppelt die Plattformautorisierung von jedem spezifischen Gruppen- oder Rollenmodell eines
Identity Providers.

### So funktioniert die Autorisierung

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines
Benutzers durch OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen
der Benutzer basierend auf seinen zugewiesenen Rollen zugreifen kann.

**Berechtigungsbewertungsprozess:**

1. Die Plattform löst die Rollenzuweisungen des Benutzers aus der lokalen, Mandanten-bezogenen Rollendatenbank auf
2. Jede Rolle ist mit einem Satz von Zugriffsregeln verknüpft, die in der Plattformdatenbank gespeichert sind
3. Für jede API-Anfrage bewertet die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers
4. Zugriffsregeln unterstützen hierarchische Übereinstimmungen mit Wildcard-Mustern für eine flexible
   Berechtigungsverwaltung
5. Die Autorisierungsentscheidung (Gewähren oder Verweigern) wird getroffen und für Audit-Zwecke protokolliert

**API-Level-Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese
Berechtigungen werden automatisch überprüft, bevor die Endpunktlogik ausgeführt wird, um sicherzustellen, dass kein
Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsbewertung verwendet das hierarchische Berechtigungsmodell,
das unter [Berechtigungen](../../11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform
programmatischen Zugriff auf das Berechtigungsbewertungssystem. Dies ermöglicht das Filtern von Ergebnismengen basierend
auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene Zugriffsebenen und
die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Dynamische Erkennung von Identity Providern

Die Anmeldeseite erkennt dynamisch verfügbare Identity Provider von Keycloak zur Laufzeit. Wenn ein Benutzer die
Anmeldeseite besucht, ruft das Frontend `GET /api/v1/{tenant_id}/auth-providers/` auf – einen nicht authentifizierten
API-Endpunkt, der die Keycloak Admin API unter Verwendung eines dedizierten, auf das geringste Privileg beschränkten
Service-Accounts (`aihub-api-service`) mit nur der `view-identity-providers`-Berechtigung abfragt.

Die API filtert die Providerliste, um nur aktivierte, sichtbare Provider einzuschliessen, und gibt deren Alias,
Anzeigenamen und Symbol zurück. Die Ergebnisse werden 5 Minuten lang gecached. Das Frontend rendert für jeden Provider
einen gebrandeten Login-Button. Das Klicken auf einen Button initiiert den OIDC Authorization Code Flow, wobei
`kc_idp_hint` auf den Alias des Providers gesetzt wird, wodurch der Benutzer direkt zum upstream Identity Provider
umgeleitet wird, ohne Keycloaks Login-Theme anzuzeigen.

Dieser Ansatz eliminiert jegliche Frontend-Konfiguration für Identity Provider – das Hinzufügen oder Entfernen eines IdP
ist eine reine Keycloak-Änderung.

### Konfigurieren von Provider-Symbolen

Jeder Identity Provider kann ein benutzerdefiniertes Symbol auf seinem Login-Button anzeigen. Symbole werden direkt in
der `config`-Map des Keycloak Identity Providers als `icon`-Feld unter Verwendung von PrimeIcon CSS-Klassen (z. B.
`pi-microsoft`, `pi-google`) konfiguriert. Provider ohne konfiguriertes Symbol greifen auf `pi-sign-in` zurück.

Um ein Symbol festzulegen, fügen Sie das Feld `icon` zur Konfiguration des Identity Providers in
`infra/deployment/templates/configs/keycloak/managed/50-identity-providers.json.j2` hinzu:

```json
"config": {
  "clientId": "...",
  "icon": "pi-microsoft"
}
```

### Direkter Keycloak-Login

Wenn `KEYCLOAK_SHOW_KEYCLOAK_LOGIN=true` (API-Umgebungsvariable, Standard: `true`), erscheint ein zusätzlicher "Login
with Keycloak"-Button neben den Buttons der föderierten Provider. Dies ermöglicht die Anmeldung mit
Benutzername/Passwort über Keycloaks eigenen Benutzer-Store – nützlich für Entwicklungsumgebungen oder Deployments, bei
denen einige Benutzer sich direkt mit Keycloak und nicht über einen externen IdP authentifizieren.

## Admin Service Authentifizierung über OAuth2 Proxy

Interne Admin Services (Dagster, Attu, SeaweedFS) werden durch [OAuth2 Proxy](https://oauth2-proxy.github.io/)-Instanzen
geschützt, die vor jedem Service liegen. OAuth2 Proxy handhabt den gesamten OIDC-Login-Flow gegenüber Keycloak, bevor
authentifizierte Anfragen an den Upstream-Service weitergeleitet werden. Nur Benutzer mit der Rolle `AIHubSysAdmin`
können auf diese Services zugreifen.

Aufgrund des Split-Horizon-Netzwerks in Docker-Deployments (Container verwenden interne Hostnamen, Browser externe URLs)
wird die OIDC-Erkennung übersprungen und Endpunkte werden explizit konfiguriert.

## Langfuse-Zugriff

Langfuse sitzt nicht hinter einem OAuth2 Proxy — es nutzt seine native Keycloak-SSO-Integration (OIDC-Client
`langfuse`). Der Zugriff ist direkt in Keycloak auf Benutzer mit der Rolle `AIHubSysAdmin` beschränkt: Der
`langfuse`-Client trägt den Marker-Client-Scope `langfuse-sysadmin-gate`, der eine bedingte Zugriffsverweigerung in den
Authentifizierungs-Flows aktiviert (Browser-Flow `browser-aihub` und Post-Broker-Login-Flow). Benutzer ohne
`AIHubSysAdmin` werden beim Keycloak-Login abgewiesen — sowohl bei neuen Logins über den Identity Provider als auch bei
bestehenden SSO-Sitzungen.

## Härtung: Zugriff auf die Keycloak Admin Console

Die Keycloak Admin Console (`https://auth.<domain>/admin/`) ist durch Benutzername und Passwort geschützt, aber
standardmässig von jeder IP-Adresse aus zugänglich. Für Produktions-Deployments wird dringend empfohlen, den Zugriff auf
die Admin Console und den Metriken-Endpunkt auf bekannte Administrator-IP-Adressen zu beschränken.

### Empfohlen: IP-Allowlisting via Traefik

Die Plattform verwendet Traefik v3 als ihren Reverse Proxy. Traefiks
[`ipAllowList`](https://doc.traefik.io/traefik/middlewares/http/ipallowlist/) Middleware kann den Zugriff auf die
Keycloak Admin-Pfade einschränken, während die OIDC Login-Endpunkte für alle Benutzer öffentlich zugänglich bleiben.

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
Admin-Router (Priorität 7500) `/admin`- und `/metrics`-Anfragen abfängt und Verbindungen von nicht in der Allowlist
enthaltenen IPs mit einer `403 Forbidden`-Antwort ablehnt.

::: tip
Das gleiche Muster kann auf jeden Service angewendet werden, der über Traefik exponiert wird. Erwägen Sie auch, den
Zugriff auf das Traefik-Dashboard selbst einzuschränken, wenn es in der Produktion aktiviert ist.
:::

## Keycloak Realm-Rollen und automatische Zuweisung

Keycloak verwaltet Realm-Level-Rollen, die bestimmen, ob ein Benutzer auf die Plattform zugreifen darf. Diese Rollen
sind grobe Zugangstore – feingranulare Berechtigungen werden lokal von der Plattform über Mandanten-bezogene Rollen
verwaltet (siehe [Berechtigungen](../../11_access_management/2_permissions/)).

Zwei Realm-Rollen wirken sich auf die Plattform aus:

| Rolle           | Effekt                                                                                                                                                                        |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AIHubAccess`   | Für den Plattform-Login erforderlich. Benutzer ohne diese Rolle werden im Keycloak Login Flow abgelehnt.                                                                      |
| `AIHubSysAdmin` | Plattform-Administrator. Wird vom Token gelesen, um Admin-Zugriff zu gewähren und die OAuth2-Proxy Admin-Tools (Dagster, Attu, SeaweedFS, Backup) sowie Langfuse zu schützen. |

::: info Realm-Rollen vs. Plattform-Rollen
Das `aihub`-Realm definiert nur diese beiden Rollen. Feingranulare, alltägliche Berechtigungen werden separat durch
**Mandanten-bezogene Rollen** innerhalb der Plattform verwaltet – diese können Namen wie `AIHubUser` oder `AIHubAdmin`
teilen, sind aber unabhängig von Keycloak Realm-Rollen und werden nicht vom IdP abgeleitet. Weisen Sie in Ihrem Identity
Provider nur `AIHubAccess` und `AIHubSysAdmin` zu.

Für die Operator-Einrichtung der Azure App-Registrierung und Rollenzuweisung siehe
[Identity Provider Einrichtung](../../3_deployment_guide/10_identity_provider_setup/).
:::

Standardmässig werden neuen Benutzern keine Rollen automatisch zugewiesen. Dies stellt sicher, dass Benutzer, die von
einem externen Identity Provider föderiert werden, nur die Rollen erhalten, die explizit aus ihren IdP-Claims gemappt
wurden, gemäss dem Prinzip der geringsten Rechte.

### Konfiguration der automatischen Rollenzuweisung

Wenn Ihr Deployment erfordert, dass alle neuen Benutzer eine Standardrolle (z. B. `AIHubUser`) erhalten, kann dies in
Keycloak konfiguriert werden:

**Option 1: Realm-Standardrollen (gilt für alle neuen Benutzer)**

In der Keycloak Admin Console navigieren Sie zu **Realm Settings > User Registration > Default Roles** und fügen die
gewünschten Rollen hinzu. Alternativ können Sie das `defaultRoles`-Array in der Bootstrap-Realm-Konfigurationsvorlage
(`infra/deployment/templates/configs/keycloak/bootstrap/groups.json.j2` — nur beim ersten Start angewendet) festlegen:

```json
"defaultRoles": ["AIHubUser"]
```

**Option 2: Identity Provider Mapper (gilt pro IdP)**

Für eine granularere Kontrolle konfigurieren Sie Rollen-Mapper für einzelne Identity Provider. Dies ermöglicht
unterschiedliche Rollen für Benutzer aus verschiedenen Organisationen. Fügen Sie einen **Hardcoded Role** Mapper-Eintrag
zum `identityProviderMappers`-Array in
`infra/deployment/templates/configs/keycloak/managed/50-identity-providers.json.j2` hinzu:

| Feld        | Wert                |
| ----------- | ------------------- |
| Name        | `default-user-role` |
| Mapper Type | Hardcoded Role      |
| Role        | `AIHubUser`         |

Dies weist die Rolle nur Benutzern zu, die sich über diesen spezifischen Identity Provider authentifizieren.

::: warning Identity Provider Mapper sind verwaltete Konfiguration
Identity Provider und ihre Mapper werden bei jedem Stack-Start aus `50-identity-providers.json.j2` abgeglichen – ein
Mapper, der nur in der Keycloak Admin Console hinzugefügt wird, wird beim nächsten Neustart gelöscht. Fügen Sie Mapper
immer zur Konfigurationsdatei hinzu.
:::

**Option 3: Claim-basierte Rollenzuweisung (bedingte Zuweisung)**

Für eine bedingte Rollenzuweisung basierend auf IdP-Claims (z. B. Azure AD App-Rollen) verwenden Sie das bestehende
`oidc-role-idp-mapper`-Muster, das bereits in `50-identity-providers.json.j2` konfiguriert ist. Jede Azure AD App-Rolle
wird einer entsprechenden Keycloak Realm-Rolle zugeordnet. Um eine neue Zuordnung hinzuzufügen, fügen Sie einen Eintrag
zum `identityProviderMappers`-Array hinzu:

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
Die `AIHubAccess`-Rolle wird auf Keycloak Login Flow-Ebene über den Authentifizierungsfluss "Post Broker Login -
AIHubAccess Check" erzwungen. Benutzern ohne diese Rolle wird der Zugriff unabhängig von anderen Rollenzuweisungen
verweigert. Stellen Sie sicher, dass Ihre Rollenzuweisungsstrategie `AIHubAccess` für Benutzer einschliesst, die sich
anmelden können sollen.
:::

## Sicherheitsstandards und operationale Fähigkeiten

### Standardkonformität

Die Authentifizierungs- und Autorisierungsimplementierung hält sich an Industriestandard-Protokolle und
-Spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

- OpenID Connect Core 1.0 für die Authentifizierung
- OAuth 2.0 Authorization Framework (RFC 6749)
- OAuth 2.0 Authorization Code Flow mit PKCE
- JSON Web Token (JWT) - RFC 7519
- JSON Web Key Set (JWKS) - RFC 7517
- OAuth 2.0 Bearer Token Usage (RFC 6750)

**Kryptografische Sicherheit:** Alle JWT Tokens werden mittels RSA-256 kryptografischer Signaturen validiert.
Öffentliche Schlüssel werden vom JWKS-Endpunkt des Identity Providers abgerufen und zur Leistungsverbesserung gecached.
Die Token-Validierung umfasst die Signaturverifikation, Aussteller-Validierung, Zielgruppen-Validierung und
Ablaufzeitprüfung bei jeder Anfrage.

### Audit und Monitoring

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten für Audit- und
Sicherheitsüberwachungszwecke protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen,
Berechtigungsbewertungen, Zugriffsentscheidungen und den vollständigen Anforderungskontext.

**Sicherheitsereignisprotokollierung:** Die Plattform integriert sich in OpenTelemetry-Standards, um strukturierte,
nachvollziehbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über
verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheitsmonitoring:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler,
Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht die schnelle
Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Enterprise-Compliance

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und
Enterprise-Sicherheitsstandards:

**Datenschutz-Compliance:**

- DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
- Einhaltung des Schweizer Datenschutzgesetzes durch Self-Hosted-Deployment-Optionen
- Umfassende Audit-Trails zur Erfüllung regulatorischer Anforderungen an die Zugriffsprotokollierung
- Datenhoheit wird durch On-Premises- oder Schweizer Cloud-Deployment gewahrt

**Enterprise-Sicherheitsanforderungen:**

- Unterstützung der Multi-Faktor-Authentifizierung über Enterprise Identity Provider
- Integration in bestehende Enterprise-Identitätsinfrastruktur
- Schutz vor gängigen Authentifizierungsangriffen (Token-Replay, Session Hijacking, CSRF)
- Sicheres Token-Lifecycle-Management mit Ablauf und Widerruf
- HTTPS-only-Kommunikation für alle Authentifizierungsflüsse

**Best Practices für Sicherheit:**

- Zero-Trust-Sicherheitsmodell mit Authentifizierung für jeden API-Zugriff
- Trennung von Authentifizierungs- und Autorisierungsbelangen
- Prinzip der geringsten Rechte durch ein granulareres Berechtigungssystem
- Defense-in-Depth mit mehreren Schichten von Sicherheitskontrollen
- Regelmässige Token-Validierung und Refresh-Mechanismen

Dieser standardbasierte Ansatz zur Authentifizierung und Autorisierung stellt sicher, dass die Plattform
Enterprise-Sicherheitsanforderungen erfüllt und gleichzeitig mit Standard-Identity-Providern und
Sicherheitsinfrastrukturen interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte
Sicherheitsmechanismen, die in Unternehmensumgebungen weithin verstanden, geprüft und vertrauenswürdig sind.
