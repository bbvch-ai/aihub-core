---
title: Authentifizierung einrichten
source_sha: 348a6ccd33ab751297eb5e9bc89c2a387bb2d1a24c59ee553e099604f858c582
---

# Authentifizierung einrichten

Der Swiss AI Hub verwendet ein Multi-Tenant-Authentifizierungs- und Autorisierungssystem mit lokaler Rollenverwaltung.

## Überblick

Das Authentifizierungssystem besteht aus mehreren Schlüsselkomponenten:

- **Auth Handlers**: Validieren Anmeldeinformationen und lösen die Benutzeridentität auf
- **Identity Models**: `UserIdentity` und `TenantIdentity` repräsentieren authentifizierte Benutzer und ihren
  Mandantenkontext
- **Zugriffskontrolle**: Der `AccessChecker` erzwingt Berechtigungen basierend auf hierarchischen Zugriffsregeln
- **Multi-Tenancy**: Alle Operationen erfolgen innerhalb eines Mandantenkontexts

## Authentifizierungsfluss

### 1. Token-Validierung

Auth Handler validieren eingehende Anfragen und extrahieren Benutzerinformationen:

```python
# Keycloak OIDC JWT validation
user_identity = await KeycloakAuthHandler()(request)

# Token-based authentication
user_identity = await TokenAuthHandler()(request)
```

Unterstützte Authentifizierungsmethoden:

- **OAuth2/OIDC**: JWT-Tokens von Keycloak (unterstützt föderierte Identity Provider wie Azure AD, Google usw.)
- **API-Tokens**: Langlebige Tokens für programmatischen Zugriff
- **OpenWebUI-Integration**: Spezieller Handler für OpenWebUI-Benutzer

Für Tests und interaktive Playground-Server befindet sich ein dedizierter `TestAuthHandler` unter
`swiss_ai_hub.core.testing.auth_utils` (nicht `core.auth`) und umgeht die Token-Analyse, um eine feste Testidentität
zurückzugeben. Er ist absichtlich nicht über die öffentliche Auth-Schnittstelle von Produktionscode aus erreichbar.

### 2. Benutzerauflösung

Benutzerprofildaten (Name, E-Mail) werden für OAuth2-Flows aus JWT-Claims gelesen oder für Bearer-Tokens über den
`KeycloakAdminService` abgerufen. Es gibt keinen lokalen Benutzerdatensatz – Keycloak ist die zentrale Quelle der
Wahrheit für die Benutzeridentität.

**Verhalten des ersten Benutzers**: Der erste Benutzer, der einem Mandanten beitritt, erhält automatisch Admin-Rollen.
Nachfolgende Benutzer erhalten Standard-Benutzerrollen (konfigurierbar über `UserSignupSettings`). Dies gilt pro
Mandant, nicht global, und wird in der `UserTenantRoleEntity` durchgesetzt, wenn eine neue Mitgliedschaft erstellt wird.

### 3. Mandantenkontext-Auflösung

Die meisten authentifizierten Anfragen haben einen Mandantenkontext. Der Mandant wird über einen
`{tenant_id}`-Pfadparameter in der URL identifiziert – die meisten API-Routen sind unter `/api/v1/{tenant_id}/...`
gemountet. Nur-Sysadmin-Endpunkte (z.B. der Mandantenadministrations-Controller) sind global ohne Mandantenpräfix
gemountet.

Die Mandantenauflösung wird innerhalb von `AuthHandler.build_identity()` und `AuthHandler._resolve_tenant_by_id()`
gehandhabt. Letzteres konsultiert zuerst `KeycloakAdminService.tenant_exists()` – Keycloak ist die maßgebliche Instanz
dafür, ob ein Mandant existiert – und prüft erst dann die `UserTenantRoleEntity`-Mitgliedschaft. Die
Mitgliedschaftsprüfung wird für Sysadmins vollständig übersprungen (siehe "Sysadmin-Zugriff" unten). Controller rufen
diese Resolver nicht direkt auf; sie sind in `user_with_permission()` und `sys_admin_user()` verdrahtet.

**Mandanten-Pfadparameter**: Alle API-Anfragen müssen die `{tenant_id}` im URL-Pfad enthalten. Zwei Formate werden
unterstützt:

- **Konkrete ID**: `/api/v1/507f1f77bcf86cd799439011/agents/...` – gibt den Mandanten direkt über die MongoDB ObjectId
  an
- **Aktiver Slug**: `/api/v1/active/agents/...` – löst sich zum persistenten aktiven Mandanten des Benutzers auf

Der aktive Mandant wird während der Anfrageauflösung niemals automatisch aktualisiert. Er kann nur über einen
dedizierten API-Endpunkt geändert werden. Health-Endpunkte bleiben außerhalb des Mandanten-Scopes unter
`/api/v1/health/`.

### 4. UserIdentity-Konstruktion

Auth Handler geben eine `UserIdentity` zurück, die sowohl Benutzer- als auch Mandanteninformationen enthält:

```python
return UserIdentity(
    id=user.id,
    name=user.name,
    email=user.email,
    roles=roles,
    acting_within_tenant=tenant,  # kann None sein für Nur-Sysadmin-Anfragen
    is_sys_admin=is_sys_admin,    # abgeleitet von der AIHubSysAdmin Keycloak Realm-Rolle
)
```

Das `is_sys_admin`-Flag ist das einzige Signal für den Plattform-Admin-Status – es kurzschließt den Access Checker
(siehe "Sysadmin-Zugriff" unten) und ist die Grundlage für die `Controller.sys_admin_user()`-Abhängigkeit, die
Nur-Sysadmin-Endpunkte schützt.

## Multi-Tenant-Rollenverwaltung

### Kernentitäten

**TenantMetadataEntity**

- Enthält Anzeige-Metadaten (Name, Beschreibung, Zugriffsregeln) für einen Mandanten
- **NICHT** die zentrale Quelle der Wahrheit für die Existenz des Mandanten – die Keycloak-Gruppe `/tenants/<id>` ist
  maßgeblich. Servicecode muss die Existenz über `KeycloakAdminService.tenant_exists()` überprüfen, bevor er den
  Metadaten vertraut.
- Enthält `access_rules`, die den Zugriff JEDES Benutzers im Mandanten begrenzen
- Beispiel: `["aihub.user.agent.>"]` gewährt Benutzerebene-Zugriff auf alle Agents

**UserTenantRoleEntity**

- Ordnet Benutzern Mandanten mit spezifischen Rollen zu
- Maßgebliche Quelle für Benutzer-Mandant-Rollen-Beziehungen
- Benutzer können in verschiedenen Mandanten unterschiedliche Rollen haben

**RoleEntity**

- Jede Rolle gehört zu genau einem Mandanten – `tenant_id` ist erforderlich
- Der Standardrollensatz (`AIHubUser`, `AIHubAdmin`, `AIHubAgentUser` usw.) wird pro Mandant bei der Erstellung
  initialisiert
- Systemweite Rollen existieren nicht mehr; siehe ADR `2026_04_14_tenant_scoped_roles.md`

**Benutzerprofildaten**

- In Keycloak gespeichert, nicht lokal – `KeycloakAdminService.get_user_by_id()` / `find_user_by_email()` zur Abfrage
- Name, E-Mail und Identitätsattribute fließen alle von Keycloak; die Plattform schreibt nichts in Benutzerdatensätze
- Rollen sind NICHT dem Benutzerdatensatz zugeordnet – sie werden pro Mandant von der `UserTenantRoleEntity` abgerufen

### Zugreifen auf Benutzerrollen

```python
# Get user's roles in a specific tenant
roles = user.get_roles(tenant_id)

# Get all access rules for a user in a tenant
access_rules = RoleEntity.get_access_rules_for_roles(roles, tenant_id=tenant_id)
```

## Zugriffskontrolle

### AccessChecker

Die Klasse `AccessChecker` führt Autorisierungsprüfungen mit zweistufiger Zugriffskontrolle durch:

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

# Erstellen Sie den Checker aus UserIdentity (enthält den Mandantenkontext)
checker = AccessChecker.from_user(user)

# Zugriffsebene prüfen
level = checker.access_level("aihub.user.agent.class-a.id-123")
# Returns: AccessLevel.ACCESS_ADMIN | ACCESS_USER | ACCESS_DENIED
```

### Zweistufige Zugriffsprüfung

**KRITISCH**: Mandantenzugriffsregeln fungieren als OBERGRENZE/GRENZE für Benutzerberechtigungen.

1. **STUFE 1**: Bestimmen der Zugriffsebene des Mandanten (Admin oder Benutzer)
2. **STUFE 2**: Bestimmen der Zugriffsebene des Benutzers (Admin oder Benutzer)
3. **STUFE 3**: Zurückgeben des MINIMUMS beider Ebenen

**Beispiel**:

```python
# Mandant hat: aihub.user.agent.> (Benutzerebene-Zugriff auf alle Agents)
# Benutzer hat: aihub.admin.agent.> (Admin-Ebene-Zugriff auf alle Agents)

# Benutzer erhält ACCESS_USER (begrenzt durch Mandantengrenze)
checker.access_level("aihub.user.agent.class-a.id-1")  # → ACCESS_USER
```

### Zugriffsregelformat

Zugriffsregeln folgen einer hierarchischen Punktnotation:

```
aihub.[admin|user].<resource>.<subresource>.<id>
```

**Platzhalter**:

- `*` – Platzhalter für eine Ebene: `aihub.user.agent.*` passt zu jedem einzelnen Agent
- `>` – Platzhalter für mehrere Ebenen: `aihub.user.agent.>` passt zu allen Agents und Unterressourcen

**Beispiele**:

```python
"aihub.admin.>"                    # Voller Admin-Zugriff auf alles
"aihub.user.>"                     # Voller Benutzerzugriff auf alles
"aihub.user.agent.>"               # Benutzerzugriff auf alle Agents
"aihub.user.agent.class-a.*"       # Benutzerzugriff auf alle Class-A-Agents
"aihub.user.agent.class-a.id-123"  # Benutzerzugriff auf spezifischen Agent
```

### Komfortmethoden

```python
# Spezifischen Agenten-Zugriff prüfen
has_access = checker.has_access_to_agent("class-a", "id-123")
access_level = checker.access_level_for_agent("class-a", "id-123")

# Agentenklassen-Zugriff prüfen
has_access = checker.has_access_to_agent_class("class-a")

# Prozess-Zugriff prüfen
has_access = checker.has_access_to_process("workflow", "proc-456")

# Service-Zugriff prüfen
has_access = checker.has_access_to_service("llm-gateway")
```

## Konfiguration

### Umgebungsvariablen

```bash
# Startup-Mandantenkonfiguration (initialisiert beim ersten Start; danach ein gewöhnlicher Mandant)
AIHUB_STARTUP_TENANT_NAME="Swiss AI Hub"
AIHUB_STARTUP_TENANT_DESCRIPTION="This tenant was auto-created on startup of the Swiss AI Hub."
AIHUB_STARTUP_TENANT_ACCESS_RULES="aihub.admin.>"

# Rollenzuweisung bei Benutzeranmeldung
AIHUB_USER_SIGNUP_DEFAULT_ROLES="AIHubUser"
AIHUB_USER_SIGNUP_REGULAR_USER_ROLES="AIHubUser"
AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES="AIHubAdmin,AIHubUser"

# OAuth2-Konfiguration
OAUTH2_ENABLED=true
OAUTH2_JWKS_URL="https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
OAUTH2_ISSUER="https://login.microsoftonline.com/{tenant}/v2.0"
OAUTH2_AUDIENCE="api://{app-id}"
```

### Einstellungsklassen

```python
from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings
from swiss_ai_hub.core.infrastructure.api.user_signup_settings import UserSignupSettings

# Auf Startup-Mandanteneinstellungen zugreifen
tenant_settings = StartupTenantSettings()
print(tenant_settings.access_rules_list)  # ['aihub.admin.>']

# Auf Benutzeranmeldungseinstellungen zugreifen
signup_settings = UserSignupSettings()
print(signup_settings.first_admin_user_roles_list)  # ['AIHubAdmin', 'AIHubUser']
```

## Best Practices

### 1. Immer Mandantenkontext bereitstellen

Erstellen Sie niemals einen `AccessChecker` ohne Mandantenzugriffsregeln:

```python
# ❌ SCHLECHT: Manuelle Konstruktion ohne Mandantenkontext
checker = AccessChecker(user_access_rules, [])

# ✅ GUT: Verwenden Sie die Factory-Methode, die sowohl Benutzer- als auch Mandantenregeln extrahiert
checker = AccessChecker.from_user(user)  # user ist UserIdentity mit Mandantenkontext
```

### 2. Mandantenmitgliedschaft überprüfen

Überprüfen Sie immer, ob Benutzer Zugriff auf den Mandanten haben, bevor Sie Operationen durchführen:

```python
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
if not roles:
    raise HTTPException(403, "Benutzer nicht dem Mandanten zugewiesen")
```

### 3. Die minimal erforderliche Zugriffsebene verwenden

Gewähren Sie Benutzern die minimal erforderliche Zugriffsebene für ihre Rolle:

```python
# ❌ SCHLECHT: Übermäßig permissiv
access_rules = ["aihub.admin.>"]

# ✅ GUT: Auf spezifische Ressourcen beschränkt
access_rules = ["aihub.user.agent.class-a.>"]
```

### 4. Mandantenzugriffsregeln als Grenzen

Verwenden Sie Mandantenzugriffsregeln, um den Umfang ALLER Benutzer in einem Mandanten zu begrenzen:

```python
# Mandant für das Analyseteam – nur Zugriff auf spezifische Agentenklassen
tenant_access_rules = [
    "aihub.user.agent.analytics.*",
    "aihub.user.service.data-pipeline"
]

# Selbst Admin-Benutzer in diesem Mandanten können nicht auf andere Ressourcen zugreifen
```

## Fehlerbehebung

### Fehler „Benutzer nicht dem Mandanten zugewiesen“

**Ursache**: Der Benutzer existiert, hat aber keine Rollen im angeforderten Mandanten.

**Lösung**: Weisen Sie dem Benutzer Rollen im Mandanten zu:

```python
UserTenantRoleEntity.create_or_update(
    user_id=user_id,
    tenant_id=tenant_id,
    roles=["AIHubUser"]
)
```

### „Zugriff verweigert“, obwohl der Benutzer Admin-Rollen hat

**Ursache**: Mandantenzugriffsregeln schränken Benutzerberechtigungen ein. (Sysadmins – Benutzer mit der `AIHubSysAdmin`
Keycloak Realm-Rolle – umgehen diese Überprüfung vollständig; wenn das Problem für einen Sysadmin weiterhin besteht, ist
der Bypass selbst falsch konfiguriert.)

**Lösung**: Überprüfen Sie die Mandantenzugriffsregeln:

```python
tenant = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
print(tenant.access_rules)  # Prüfen Sie, was der Mandant zulässt
```

### Leere Mandantenzugriffsregeln = Kein Zugriff

Wenn ein Mandant keine Zugriffsregeln (`[]`) hat, wird ALLEN Benutzern in diesem Mandanten der Zugriff auf alles
verweigert.

**Lösung**: Legen Sie angemessene Mandantenzugriffsregeln fest:

```python
tenant.access_rules = ["aihub.user.>"]
tenant.save()
```

## Sicherheitsüberlegungen

- **Mounten Sie niemals den `TestAuthHandler` an Produktionseinstiegspunkten** – er befindet sich aus diesem Grund unter
  `core.testing`; Produktions-`app/main.py`-Dateien müssen `KeycloakAuthHandler` oder `TokenAuthHandler` verwenden.
- **Validieren Sie JWTs korrekt** – überprüfen Sie immer Issuer, Audience und Signatur.
- **Verwenden Sie HTTPS** – übertragen Sie Tokens niemals über unverschlüsselte Verbindungen.
- **Rotieren Sie API-Tokens regelmäßig** – implementieren Sie Token-Ablauf und -Rotation.
- **Auditieren Sie Änderungen der Zugriffskontrolle** – protokollieren Sie alle Rollen- und Berechtigungsänderungen.
- **Prinzip der geringsten Privilegien** – gewähren Sie minimal erforderlichen Zugriff.
- **Mandantenisolation** – Benutzer können nicht auf Ressourcen außerhalb der Grenzen ihres Mandanten zugreifen.

## Migration vom vorherigen System

Frühere Versionen riefen Rollen aus Azure AD über die Microsoft Graph API ab. Das neue System:

- ✅ **Speichert Rollen lokal** in der `UserTenantRoleEntity`
- ✅ **Keine externen API-Aufrufe** während der Authentifizierung
- ✅ **Mandantenspezifische Rollen** für Multi-Tenancy
- ❌ **Keine automatische Rollensynchronisation** vom Identity Provider
- ❌ **Kein automatisches Abrufen von Profilbildern** vom Identity Provider

Details finden Sie unter
[ADR: Lokale Multi-Tenant-Rollenverwaltung](/arc42/decisions/2025_12_25_local_role_management.md).
