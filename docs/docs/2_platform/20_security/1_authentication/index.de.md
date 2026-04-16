---
title: Authentifizierung und Autorisierung
source_sha: "9ff7afdd202ecf971428eddf61971e7c96f8e8cba061975c033ddbf4e31735e9"
---

# Authentifizierung und Autorisierung

Der Swiss AI Hub implementiert Authentifizierung und Autorisierung basierend auf den branchenüblichen OpenID Connect (OIDC)- und OAuth 2.0-Protokollen. Dieser standardbasierte Ansatz gewährleistet die Kompatibilität mit Unternehmens-Identitätsanbietern, während der sichere Zugriff auf alle Plattformressourcen aufrechterhalten wird.

## Authentifizierung: OpenID Connect (OIDC)

Die Plattform authentifiziert Benutzer durch OpenID Connect, eine Identitätsebene, die auf OAuth 2.0 aufbaut. Dies ermöglicht eine sichere Benutzerauthentifizierung durch Unternehmens-Identitätsanbieter wie Microsoft Entra ID (Azure Active Directory), während der OAuth 2.0 Authorization Code Flow unterstützt wird.

### So funktioniert Authentifizierung

**Token-basierte Authentifizierung:** Benutzer authentifizieren sich über den Identitätsanbieter ihrer Organisation, der einen JSON Web Token (JWT) ausstellt, der kryptographisch signierte Claims über die Identität des Benutzers enthält. Die Plattform validiert diese Tokens bei jeder Anfrage, um Authentizität und Aktualität zu gewährleisten.

**JWT Token-Validierung:** Die Plattform ruft öffentliche Schlüssel vom JWKS-Endpunkt (JSON Web Key Set) des Identitätsanbieters ab und verwendet diese, um die kryptographische Signatur jedes JWT-Tokens zu verifizieren. Diese Validierung umfasst die Prüfung des Ausstellers, der Zielgruppe, der Ablaufzeit und der Signaturintegrität des Tokens gemäß dem JWT-Standard (RFC 7519).

**Auflösung der Benutzeridentität:** Nach erfolgreicher Token-Validierung extrahiert die Plattform den eindeutigen Bezeichner des Benutzers (OID) und grundlegende Profilinformationen (Name, E-Mail) aus den JWT-Token-Claims. Rollenzuweisungen werden lokal innerhalb der Plattform durch Mandanten-bezogene Rollenentitäten verwaltet und nicht vom Identitätsanbieter abgerufen.

### Unterstützte Authentifizierungsmethoden

**OAuth 2.0 Authorization Code Flow:** Die primäre Authentifizierungsmethode für interaktive Benutzer folgt dem OAuth 2.0 Authorization Code Flow mit PKCE (Proof Key for Code Exchange). Benutzer werden zur Authentifizierung an den Identitätsanbieter ihrer Organisation umgeleitet und erhalten nach erfolgreicher Anmeldung einen sicheren Autorisierungscode, der gegen Zugriffs-Tokens ausgetauscht wird.

**Bearer Token-Authentifizierung:** Für den API-Zugriff und programmatische Integrationen unterstützt die Plattform die Standard-OAuth 2.0 Bearer Token-Authentifizierung. API-Clients präsentieren gültige JWT-Tokens im HTTP-Autorisierungs-Header, die mit demselben JWKS-basierten Verifizierungsprozess validiert werden.

## Autorisierung: Berechtigungsbasierte Zugriffskontrolle

Die Autorisierung wird unabhängig von der Authentifizierung implementiert, wodurch eine konsistente Zugriffskontrolle ermöglicht wird, unabhängig davon, wie sich Benutzer authentifizieren. Die Plattform evaluiert Berechtigungen für jede API-Anfrage basierend auf den zugewiesenen Rollen des Benutzers und dem hierarchischen Berechtigungsmodell, das in den [Berechtigungen](/de/docs/11_access_management/2_permissions/) beschrieben ist.

### Integration von Unternehmens-Identitätsanbietern

Die Plattform integriert sich mit Unternehmens-Identitätsanbietern über standardmäßige OIDC-/OAuth 2.0-Protokolle. Jeder OIDC-konforme Anbieter (Microsoft Entra ID, Google Workspace, Okta, Auth0, Keycloak) kann zur Authentifizierung verwendet werden.

**Generische OIDC-Integration:** Die Plattform verbindet sich mit dem konfigurierten OIDC-Anbieter als OAuth 2.0 Autorisierungsserver und Identitätsanbieter. Die Benutzerauthentifizierung wird an den Anbieter delegiert, der die Überprüfung der Anmeldeinformationen, die Multi-Faktor-Authentifizierung und das Session-Management gemäß den Sicherheitsrichtlinien der Organisation handhabt.

**Lokales Rollenmanagement:** Benutzerprofile werden aus JWT-Token-Claims (Name, E-Mail, OID) extrahiert. Rollen werden lokal innerhalb der Plattform durch Mandanten-bezogene Rollenzuweisungen verwaltet und nicht vom Identitätsanbieter synchronisiert. Dies entkoppelt die Plattformautorisierung von der Gruppen- oder Rollenmodellierung eines spezifischen Identitätsanbieters.

### So funktioniert Autorisierung

Autorisierungsentscheidungen werden unabhängig von der Authentifizierung getroffen. Nachdem die Identität eines Benutzers durch OIDC-Authentifizierung festgestellt wurde, bestimmt die Plattform, auf welche Ressourcen und Operationen der Benutzer zugreifen kann, basierend auf seinen zugewiesenen Rollen.

**Berechtigungsevaluierungsprozess:**

1. Die Plattform löst die Rollenzuweisungen des Benutzers aus der lokalen, mandantenbezogenen Rollendatenbank auf.
2. Jede Rolle ist mit einem Satz von Zugriffsregeln verknüpft, die in der Plattformdatenbank gespeichert sind.
3. Für jede API-Anfrage evaluiert die Plattform die erforderliche Berechtigung anhand der Zugriffsregeln des Benutzers.
4. Zugriffsregeln unterstützen hierarchisches Matching mit Wildcard-Mustern für flexibles Berechtigungsmanagement.
5. Die Autorisierungsentscheidung (Gewähren oder Verweigern) wird getroffen und zu Audit-Zwecken protokolliert.

**API-Level-Berechtigungsdurchsetzung:** Jeder API-Endpunkt deklariert seine erforderlichen Berechtigungen. Diese Berechtigungen werden automatisch überprüft, bevor die Endpunktlogik ausgeführt wird, wodurch sichergestellt wird, dass kein Ressourcenzugriff die Autorisierung umgeht. Die Berechtigungsevaluierung verwendet das hierarchische Berechtigungsmodell, das in den [Berechtigungen](/de/docs/11_access_management/2_permissions/) beschrieben ist.

**Dynamische Autorisierung:** Für Operationen, die Laufzeit-Berechtigungsprüfungen erfordern, bietet die Plattform programmatischen Zugriff auf das Berechtigungsevaluierungssystem. Dies ermöglicht das Filtern von Ergebnismengen basierend auf Benutzerberechtigungen, die Implementierung unterschiedlicher Verhaltensweisen für verschiedene Zugriffsebenen und die Validierung von Berechtigungen vor ressourcenintensiven Operationen.

## Dynamische Identitätsanbieter-Erkennung

Die Anmeldeseite entdeckt dynamisch verfügbare Identitätsanbieter von Keycloak zur Laufzeit. Wenn ein Benutzer die Anmeldeseite besucht, ruft das Frontend `GET /api/v1/{tenant_id}/auth-providers/` auf – ein nicht authentifizierter API-Endpunkt, der die Keycloak Admin API unter Verwendung eines dedizierten Service-Kontos mit den geringsten Berechtigungen (`aihub-api-service`) mit nur der `view-identity-providers`-Berechtigung abfragt.

Die API filtert die Anbieterliste, um nur aktivierte, sichtbare Anbieter einzuschließen, und gibt deren Alias, Anzeigenamen und Icon zurück. Ergebnisse werden für 5 Minuten gecached. Das Frontend rendert einen Marken-Login-Button für jeden Anbieter. Das Klicken auf einen Button initiiert den OIDC Authorization Code Flow, wobei `kc_idp_hint` auf den Alias des Anbieters gesetzt ist, und leitet den Benutzer direkt zum vorgelagerten Identitätsanbieter weiter, ohne Keycloaks Login-Theme anzuzeigen.

Dieser Ansatz eliminiert jegliche Frontend-Konfiguration für Identitätsanbieter – das Hinzufügen oder Entfernen eines IdP ist eine reine Keycloak-Änderung. Siehe
[ADR: Dynamic Identity Provider Loading](../../../../arc42/decisions/2026_02_27_dynamic_identity_provider_loading.md)
für die vollständige Begründung und Implementierungsdetails.

### Konfigurieren von Anbieter-Icons

Jeder Identitätsanbieter kann ein benutzerdefiniertes Icon haben, das auf seinem Login-Button angezeigt wird. Icons werden direkt in der `config`-Map des Keycloak-Identitätsanbieters als `icon`-Feld unter Verwendung von PrimeIcon CSS-Klassen (z. B. `pi-microsoft`, `pi-google`) konfiguriert. Anbieter ohne konfiguriertes Icon fallen auf `pi-sign-in` zurück.

Um ein Icon festzulegen, fügen Sie das `icon`-Feld zur Konfiguration des Identitätsanbieters in `keycloak-identity-providers.json.j2` hinzu:

```json
"config": {
  "clientId": "...",
  "icon": "pi-microsoft"
}
```

### Direkter Keycloak-Login

Wenn `KEYCLOAK_SHOW_KEYCLOAK_LOGIN=true` (API-Umgebungsvariable, Standard: `true`) ist, erscheint ein zusätzlicher "Login with Keycloak"-Button neben den Buttons der föderierten Anbieter. Dies ermöglicht die Anmeldung mit Benutzername/Passwort über Keycloaks eigenen Benutzer-Store – nützlich für Entwicklungsumgebungen oder Deployments, in denen sich einige Benutzer direkt mit Keycloak authentifizieren, anstatt über einen externen IdP.

## Admin Service Authentifizierung via OAuth2 Proxy

Interne Admin-Services (Dagster, Attu, SeaweedFS) werden durch [OAuth2 Proxy](https://oauth2-proxy.github.io/)-Instanzen geschützt, die vor jedem Service sitzen. OAuth2 Proxy handhabt den vollständigen OIDC-Login-Flow gegen Keycloak, bevor authentifizierte Anfragen an den vorgelagerten Service weitergeleitet werden. Nur Benutzer mit der Rolle `AIHubSysAdmin` können auf diese Services zugreifen.

Aufgrund des Split-Horizon-Netzwerks in Docker-Deployments (Container verwenden interne Hostnamen, Browser externe URLs) wird die OIDC-Erkennung übersprungen und Endpunkte werden explizit konfiguriert. Siehe
[ADR: Skip OIDC Discovery for OAuth2 Proxy](../../../../arc42/decisions/2026_02_26_skip_oidc_discovery_for_oauth2_proxy.md)
für die technische Begründung.

## Hardening: Keycloak Admin-Konsolenzugriff

Die Keycloak Admin-Konsole (`https://auth.<domain>/admin/`) ist durch Benutzername und Passwort geschützt, aber standardmäßig von jeder IP-Adresse aus zugänglich. Für Produktions-Deployments wird dringend empfohlen, den Zugriff auf die Admin-Konsole und den Metrik-Endpunkt auf bekannte Administrator-IP-Adressen zu beschränken.

### Empfohlen: IP Allowlisting via Traefik

Die Plattform verwendet Traefik v3 als Reverse-Proxy. Traefiks
[`ipAllowList`](https://doc.traefik.io/traefik/middlewares/http/ipallowlist/)-Middleware kann den Zugriff auf die Keycloak Admin-Pfade einschränken, während die OIDC-Login-Endpunkte für alle Benutzer öffentlich zugänglich bleiben.

**Implementierungsschritte:**

1. Fügen Sie eine Umgebungsvariable zu `.env` mit Ihren erlaubten IP-Bereichen hinzu:

   ```bash
   KEYCLOAK_ADMIN_ALLOWED_IPS="203.0.113.0/24,198.51.100.10/32"
   ```

2. Fügen Sie in `docker-compose.yml` einen zweiten Traefik-Router für Admin-Pfade zu den `keycloak`-Service-Labels hinzu (neben dem bestehenden `keycloak`-Router):

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

Der öffentliche Router (Priorität 7000) bedient weiterhin OIDC-Endpunkte (`/realms/...`) ohne Einschränkung, während der Admin-Router (Priorität 7500) `/admin`- und `/metrics`-Anfragen abfängt und Verbindungen von nicht zugelassenen IPs mit einer `403 Forbidden`-Antwort abweist.

::: tip
Dasselbe Muster kann auf jeden über Traefik exponierten Service angewendet werden. Erwägen Sie auch, den Zugriff auf das Traefik-Dashboard selbst einzuschränken, wenn es in Produktion aktiviert ist.
:::

## Keycloak Realm-Rollen und Automatische Zuweisung

Keycloak verwaltet Realm-Level-Rollen, die bestimmen, ob ein Benutzer auf die Plattform zugreifen darf. Diese Rollen sind grobe Zugangstore – fein granulare Berechtigungen werden lokal von der Plattform verwaltet (siehe
[Berechtigungen](/de/docs/11_access_management/2_permissions/)).

| Rolle            | Zweck                                                                                       |
| ---------------- | ------------------------------------------------------------------------------------------- |
| `AIHubAccess`    | Erforderlich für den Plattform-Login. Benutzern ohne diese Rolle wird der Zugriff im Keycloak Login-Flow verweigert. |
| `AIHubAdmin`     | Voller administrativer Zugriff                                                              |
| `AIHubUser`      | Standard-Benutzerzugriff                                                                    |
| `AIHubDeveloper` | Zugriff auf Entwickler-Tools (Dagster, Attu, etc.)                                          |
| `AIHubSysAdmin`  | Systemadministrator-Zugriff auf Infrastruktur-Tools                                         |

Standardmäßig werden neuen Benutzern keine Rollen automatisch zugewiesen. Dies stellt sicher, dass Benutzer, die von einem externen Identitätsanbieter föderiert werden, nur die Rollen erhalten, die explizit aus ihren IdP-Claims abgebildet wurden, dem Prinzip der geringsten Rechte folgend.

### Konfigurieren der Automatischen Rollenzuweisung

Wenn Ihr Deployment erfordert, dass alle neuen Benutzer eine Standardrolle (z. B. `AIHubUser`) erhalten, kann dies in Keycloak konfiguriert werden:

**Option 1: Realm-Standardrollen (gilt für alle neuen Benutzer)**

Navigieren Sie in der Keycloak Admin-Konsole zu **Realm Settings > User Registration > Default Roles** und fügen Sie die gewünschten Rollen hinzu. Alternativ legen Sie das `defaultRoles`-Array in der Realm-Konfigurationsvorlage (`keycloak-realm.json.j2`) fest:

```json
"defaultRoles": ["AIHubUser"]
```

**Option 2: Identitätsanbieter-Mapper (gilt pro IdP)**

Für eine granularere Kontrolle konfigurieren Sie Rollen-Mapper für individuelle Identitätsanbieter. Dies ermöglicht unterschiedliche Rollen für Benutzer aus verschiedenen Organisationen. Navigieren Sie in der Keycloak Admin-Konsole zu **Identity Providers > [Ihr IdP] > Mappers** und fügen Sie einen **Hardcoded Role**-Mapper hinzu:

| Feld        | Wert                |
| ----------- | ------------------- |
| Name        | `default-user-role` |
| Mapper-Typ  | Hardcoded Role      |
| Rolle       | `AIHubUser`         |

Dies weist die Rolle nur Benutzern zu, die sich über diesen spezifischen Identitätsanbieter authentifizieren.

**Option 3: Claim-basierte Rollen-Mapping (bedingte Zuweisung)**

Für die bedingte Rollenzuweisung basierend auf IdP-Claims (z. B. Azure AD App-Rollen) verwenden Sie das bestehende `oidc-role-idp-mapper`-Muster, das bereits in `keycloak-identity-providers.json.j2` konfiguriert ist. Jede Azure AD App-Rolle wird auf eine entsprechende Keycloak-Realm-Rolle abgebildet. Um eine neue Zuordnung hinzuzufügen, fügen Sie einen Eintrag zum `identityProviderMappers`-Array hinzu:

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
Die Rolle `AIHubAccess` wird auf der Ebene des Keycloak Login-Flows über den Authentifizierungs-Flow "Post Broker Login - AIHubAccess Check" durchgesetzt. Benutzern ohne diese Rolle wird der Zugriff unabhängig von anderen Rollenzuweisungen verweigert. Stellen Sie sicher, dass Ihre Rollen-Mapping-Strategie `AIHubAccess` für Benutzer einschließt, die sich anmelden können sollen.
:::

## Sicherheitsstandards und Operationale Fähigkeiten

### Standards-Konformität

Die Authentifizierungs- und Autorisierungsimplementierung hält sich an branchenübliche Protokolle und Spezifikationen:

**OIDC- und OAuth 2.0-Standards:**

- OpenID Connect Core 1.0 für Authentifizierung
- OAuth 2.0 Autorisierungs-Framework (RFC 6749)
- OAuth 2.0 Authorization Code Flow mit PKCE
- JSON Web Token (JWT) - RFC 7519
- JSON Web Key Set (JWKS) - RFC 7517
- OAuth 2.0 Bearer Token Nutzung (RFC 6750)

**Kryptographische Sicherheit:** Alle JWT-Tokens werden mittels kryptographischer RSA-256-Signaturen validiert. Öffentliche Schlüssel werden vom JWKS-Endpunkt des Identitätsanbieters abgerufen und für die Performance gecached. Die Token-Validierung umfasst die Signaturprüfung, Ausstellerprüfung, Zielgruppenprüfung und Ablaufprüfung bei jeder Anfrage.

### Audit und Monitoring

Alle Authentifizierungs- und Autorisierungsereignisse werden umfassend mit strukturierten Metadaten zu Audit- und Sicherheitsüberwachungszwecken protokolliert. Dies umfasst Benutzeridentität, angeforderte Ressourcen, Berechtigungsevaluierungen, Zugriffsentscheidungen und den vollständigen Anforderungskontext.

**Sicherheitsereignisprotokollierung:** Die Plattform integriert sich mit OpenTelemetry-Standards, um strukturierte, nachvollziehbare Sicherheitsereignisse bereitzustellen. Dies ermöglicht die Korrelation von Sicherheitsereignissen über verteilte Systemkomponenten hinweg und unterstützt Compliance-Anforderungen für Audit-Trails.

**Echtzeit-Sicherheitsüberwachung:** Sicherheitsteams können Authentifizierungsmuster, Autorisierungsfehler, Token-Validierungsereignisse und Zugriffsmuster in Echtzeit überwachen. Diese Transparenz ermöglicht eine schnelle Erkennung und Reaktion auf potenzielle Sicherheitsvorfälle.

### Regulatorische und Unternehmens-Compliance

Die Authentifizierungs- und Autorisierungsarchitektur unterstützt die Einhaltung regulatorischer Anforderungen und Unternehmens-Sicherheitsstandards:

**Datenschutz-Compliance:**

- DSGVO-konforme Benutzerauthentifizierung und Datenverarbeitung
- Einhaltung des Schweizer Datenschutzgesetzes durch selbst gehostete Deployment-Optionen
- Umfassende Audit-Trails, die regulatorische Anforderungen für die Zugriffsprotokollierung erfüllen
- Datenhoheit durch On-Premises- oder Schweizer Cloud-Deployment gewahrt

**Unternehmens-Sicherheitsanforderungen:**

- Multi-Faktor-Authentifizierungsunterstützung durch Unternehmens-Identitätsanbieter
- Integration in bestehende Unternehmens-Identitätsinfrastruktur
- Schutz vor gängigen Authentifizierungsangriffen (Token-Replay, Session-Hijacking, CSRF)
- Sicheres Token-Lifecycle-Management mit Ablauf und Widerruf
- HTTPS-only-Kommunikation für alle Authentifizierungs-Flows

**Security Best Practices:**

- Zero-Trust-Sicherheitsmodell mit Authentifizierung, die für jeden API-Zugriff erforderlich ist
- Trennung von Authentifizierungs- und Autorisierungsbelangen
- Prinzip der geringsten Rechte durch granuläres Berechtigungssystem
- Defense in Depth mit mehreren Schichten von Sicherheitskontrollen
- Regelmäßige Token-Validierungs- und Refresh-Mechanismen

Dieser standardbasierte Ansatz zur Authentifizierung und Autorisierung stellt sicher, dass die Plattform die Sicherheitsanforderungen von Unternehmen erfüllt, während sie mit Standard-Identitätsanbietern und Sicherheitsinfrastruktur interoperabel bleibt. Die Verwendung von OIDC und OAuth 2.0 bietet bewährte Sicherheitsmechanismen, die in Unternehmensumgebungen weit verbreitet verstanden, auditiert und vertraut sind.
