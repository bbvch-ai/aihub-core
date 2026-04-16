---
title: Einrichtung der Authentifizierung
source_sha: "c4860a0823b9007bdad8a261391c95a5b18692823254ebbd9fa8e297fa14bd8e"
---

# Einrichtung der Authentifizierung

Swiss AI Hub verwendet ein Multi-Mandanten-Authentifizierungs- und Autorisierungssystem mit lokaler Rollenverwaltung.

## Überblick

Das Authentifizierungssystem besteht aus mehreren Schlüsselkomponenten:

-   **Auth Handlers**: Validieren Anmeldeinformationen und lösen die Benutzeridentität auf
-   **Identity Models**: `UserIdentity` und `TenantIdentity` repräsentieren authentifizierte Benutzer und deren Mandantenkontext
-   **Access Control**: `AccessChecker` erzwingt Berechtigungen basierend auf hierarchischen Zugriffsregeln
-   **Multi-Tenancy**: Alle Operationen erfolgen innerhalb eines Mandantenkontexts

## Authentifizierungsablauf

### 1. Token-Validierung

Auth Handlers validieren eingehende Anfragen und extrahieren Benutzerinformationen:

```python
# Keycloak OIDC JWT validation
user_identity = await KeycloakAuthHandler()(request)

# Token-based authentication
user_identity = await TokenAuthHandler()(request)
```

Unterstützte Authentifizierungsmethoden:

-   **OAuth2/OIDC**: JWT-Tokens von Keycloak (unterstützt föderierte Identitätsanbieter wie Azure AD, Google usw.)
-   **API Tokens**: Langlebige Tokens für den programmatischen Zugriff
-   **OpenWebUI Integration**: Spezieller Handler für OpenWebUI-Benutzer

Für Tests und interaktive Playground-Server existiert ein dedizierter `TestAuthHandler` unter
`swiss_ai_hub.core.testing.auth_utils` (nicht `core.auth`) und umgeht die Token-Analyse, um eine feste Testidentität zurückzugeben. Er ist absichtlich nicht über die öffentliche Auth-Schnittstelle aus dem Produktionscode erreichbar.

### 2. Benutzerauflösung

Benutzerprofildaten (Name, E-Mail) werden für OAuth2-Flows aus JWT-Claims gelesen oder über den `KeycloakAdminService` für Bearer-Tokens abgerufen. Es gibt keinen lokalen Benutzerdatensatz – Keycloak ist die einzige Quelle der Wahrheit für die Benutzeridentität.

**Verhalten des ersten Benutzers**: Der erste Benutzer, der einem Mandanten beitritt, erhält automatisch Administratorrollen. Nachfolgende Benutzer erhalten Standardbenutzerrollen (konfigurierbar über `UserSignupSettings`). Dies gilt pro Mandant, nicht global, und wird in `UserTenantRoleEntity` erzwungen, wenn eine neue Mitgliedschaft erstellt wird.

### 3. Mandantenkontext-Auflösung

Die meisten authentifizierten Anfragen haben einen Mandantenkontext. Der Mandant wird über einen `{tenant_id}`-Pfadparameter in der URL identifiziert – die meisten API-Routen sind unter `/api/v1/{tenant_id}/...` gemountet. Sysadmin-only-Endpunkte (z. B. der Mandantenadministrations-Controller) sind global ohne Mandantenpräfix gemountet.

Die Mandantenauflösung wird innerhalb von `AuthHandler.build_identity()` und `AuthHandler._resolve_tenant_by_id()` gehandhabt. Letzterer konsultiert zuerst `KeycloakAdminService.tenant_exists()` – Keycloak ist die Autorität darüber, ob ein Mandant existiert – und prüft erst dann die `UserTenantRoleEntity`-Mitgliedschaft. Die Mitgliedschaftsprüfung wird für Sysadmins vollständig übersprungen (siehe „Sysadmin-Zugriff“ unten). Controller rufen diese Resolver nicht direkt auf; sie sind in `user_with_permission()` und `sys_admin_user()` verdrahtet.

**Mandanten-Pfadparameter**: Alle API-Anfragen müssen die `{tenant_id}` im URL-Pfad enthalten. Zwei Formate werden unterstützt:

-   **Konkrete ID**: `/api/v1/507f1f77bcf86cd799439011/agents/...` – spezifiziert den Mandanten direkt per MongoDB ObjectId
-   **Aktiver Slug**: `/api/v1/active/agents/...` – löst sich zum persistenten aktiven Mandanten des Benutzers auf

Der aktive Mandant wird während der Anfragenauflösung niemals automatisch aktualisiert. Er kann nur über einen dedizierten API-Endpunkt geändert werden. Health-Endpunkte bleiben außerhalb des Mandantenbereichs unter `/api/v1/health/`.

### 4. Konstruktion der UserIdentity

Auth Handlers geben eine `UserIdentity` zurück, die sowohl Benutzer- als auch Mandanteninformationen enthält:

```python
return UserIdentity(
    id=user.id,
    name=user.name,
    email=user.email,
    roles=roles,
    acting_within_tenant=tenant,  # may be None for sysadmin-only requests
    is_sys_admin=is_sys_admin,    # derived from the AIHubSysAdmin Keycloak realm role
)
```

Das Flag `is_sys_admin` ist das einzige Signal für den Plattform-Admin-Status – es überbrückt den Access Checker (siehe
„Sysadmin-Zugriff“ unten) und bildet die Grundlage für die `Controller.sys_admin_user()`-Abhängigkeit, die Sysadmin-only-Endpunkte absichert.

## Multi-Mandanten-Rollenverwaltung

### Kern-Entitäten

**TenantMetadataEntity**

-   Enthält Anzeigemetadaten (Name, Beschreibung, Zugriffsregeln) für einen Mandanten
-   **NICHT** die Quelle der Wahrheit für die Existenz eines Mandanten – die Keycloak-Gruppe `/tenants/<id>` ist maßgeblich. Service-Code
    muss die Existenz über `KeycloakAdminService.tenant_exists()` überprüfen, bevor den Metadaten vertraut wird.
-   Enthält `access_rules`, die begrenzen, worauf JEDER Benutzer im Mandanten zugreifen kann
-   Beispiel: `["aihub.user.agent.>"]` gewährt Zugriff auf alle Agents auf Benutzerebene

**UserTenantRoleEntity**

-   Ordnet Benutzern Mandanten mit spezifischen Rollen zu
-   Maßgebliche Quelle für Benutzer-Mandant-Rollen-Beziehungen
-   Benutzer können unterschiedliche Rollen in verschiedenen Mandanten haben

**RoleEntity**

-   Jede Rolle gehört zu genau einem Mandanten – `tenant_id` ist erforderlich
-   Das Standardrollenset (`AIHubUser`, `AIHubAdmin`, `AIHubAgentUser`, usw.) wird pro Mandant bei der Erstellung initialisiert
-   Systemweite Rollen existieren nicht mehr; siehe ADR `2026_04_14_tenant_scoped_roles.md`

**Benutzerprofildaten**

-   Gespeichert in Keycloak, nicht lokal – `KeycloakAdminService.get_user_by_id()` / `find_user_by_email()` für die Suche
-   Name, E-Mail und Identitätsattribute stammen alle aus Keycloak; die Plattform schreibt nichts in Benutzerdatensätze
-   Rollen sind NICHT an den Benutzerdatensatz angehängt – sie werden aus `UserTenantRoleEntity` pro Mandant abgerufen

### Zugriff auf Benutzerrollen

```python
# Get user's roles in a specific tenant
roles = user.get_roles(tenant_id)

# Get all access rules for a user in a tenant
access_rules = RoleEntity.get_access_rules_for_roles(roles, tenant_id=tenant_id)
```

## Zugriffssteuerung

### AccessChecker

Die Klasse `AccessChecker` führt Autorisierungsprüfungen mit einer zweistufigen Zugriffssteuerung durch:

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

# Create checker from UserIdentity (includes tenant context)
checker = AccessChecker.from_user(user)

# Check access level
level = checker.access_level("aihub.user.agent.class-a.id-123")
# Returns: AccessLevel.ACCESS_ADMIN | ACCESS_USER | ACCESS_DENIED
```

### Zweistufige Zugriffsprüfung

**KRITISCH**: Mandanten-Zugriffsregeln fungieren als OBERGRENZE/GRENZE für Benutzerberechtigungen.

1.  **STUFE 1**: Bestimmen Sie das Zugriffslevel des Mandanten (Admin oder Benutzer)
2.  **STUFE 2**: Bestimmen Sie das Zugriffslevel des Benutzers (Admin oder Benutzer)
3.  **STUFE 3**: Geben Sie das MINIMUM beider Level zurück

**Beispiel**:

```python
# Tenant has: aihub.user.agent.> (user-level access to all agents)
# User has: aihub.admin.agent.> (admin-level access to all agents)

# User gets ACCESS_USER (capped by tenant boundary)
checker.access_level("aihub.user.agent.class-a.id-1")  # → ACCESS_USER
```

### Format der Zugriffsregeln

Zugriffsregeln folgen einer hierarchischen Punktnotation:

```
aihub.[admin|user].<resource>.<subresource>.<id>
```

**Platzhalter**:

-   `*` - Ein-Ebenen-Platzhalter: `aihub.user.agent.*` passt auf jeden einzelnen Agent
-   `>` - Mehr-Ebenen-Platzhalter: `aihub.user.agent.>` passt auf alle Agents und Unterressourcen

**Beispiele**:

```python
"aihub.admin.>"                    # Full admin access to everything
"aihub.user.>"                     # Full user access to everything
"aihub.user.agent.>"               # User access to all agents
"aihub.user.agent.class-a.*"       # User access to all class-a agents
"aihub.user.agent.class-a.id-123"  # User access to specific agent
```

### Komfortmethoden

```python
# Check specific agent access
has_access = checker.has_access_to_agent("class-a", "id-123")
access_level = checker.access_level_for_agent("class-a", "id-123")

# Check agent class access
has_access = checker.has_access_to_agent_class("class-a")

# Check process access
has_access = checker.has_access_to_process("workflow", "proc-456")

# Check service access
has_access = checker.has_access_to_service("llm-gateway")
```

## Konfiguration

### Umgebungsvariablen

```bash
# Default Tenant Configuration
AIHUB_DEFAULT_TENANT_NAME="Default Organization"
AIHUB_DEFAULT_TENANT_DESCRIPTION="The default organization for all users."
AIHUB_DEFAULT_TENANT_ACCESS_RULES="aihub.admin.>"

# User Signup Role Assignment
AIHUB_USER_SIGNUP_DEFAULT_ROLES="AIHubUser"
AIHUB_USER_SIGNUP_REGULAR_USER_ROLES="AIHubUser"
AIHUB_USER_SIGNUP_FIRST_ADMIN_USER_ROLES="AIHubAdmin,AIHubUser"

# OAuth2 Configuration
OAUTH2_ENABLED=true
OAUTH2_JWKS_URL="https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
OAUTH2_ISSUER="https://login.microsoftonline.com/{tenant}/v2.0"
OAUTH2_AUDIENCE="api://{app-id}"
```

### Einstellungsklassen

```python
from aihub_lib.infrastructure.api.DefaultTenantSettings import DefaultTenantSettings
from aihub_lib.infrastructure.api.UserSignupSettings import UserSignupSettings

# Access default tenant settings
tenant_settings = DefaultTenantSettings()
print(tenant_settings.default_access_rules_list)  # ['aihub.admin.>']

# Access user signup settings
signup_settings = UserSignupSettings()
print(signup_settings.first_admin_user_roles_list)  # ['AIHubAdmin', 'AIHubUser']
```

## Best Practices

### 1. Immer Mandantenkontext bereitstellen

Erstellen Sie niemals einen `AccessChecker` ohne Mandanten-Zugriffsregeln:

```python
# ❌ BAD: Manual construction without tenant context
checker = AccessChecker(user_access_rules, [])

# ✅ GOOD: Use factory method that extracts both user and tenant rules
checker = AccessChecker.from_user(user)  # user is UserIdentity with tenant context
```

### 2. Mandantenmitgliedschaft überprüfen

Überprüfen Sie immer, ob Benutzer Zugriff auf den Mandanten haben, bevor Sie Operationen ausführen:

```python
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
if not roles:
    raise HTTPException(403, "User not assigned to tenant")
```

### 3. Den minimal erforderlichen Zugriffslevel verwenden

Gewähren Sie Benutzern das minimale Zugriffslevel, das für ihre Rolle erforderlich ist:

```python
# ❌ BAD: Over-permissive
access_rules = ["aihub.admin.>"]

# ✅ GOOD: Scoped to specific resources
access_rules = ["aihub.user.agent.class-a.>"]
```

### 4. Mandanten-Zugriffsregeln als Grenzen

Verwenden Sie Mandanten-Zugriffsregeln, um den Geltungsbereich ALLER Benutzer in einem Mandanten zu begrenzen:

```python
# Tenant for analytics team - only access to specific agent classes
tenant_access_rules = [
    "aihub.user.agent.analytics.*",
    "aihub.user.service.data-pipeline"
]

# Even admin users in this tenant cannot access other resources
```

## Fehlerbehebung

### Fehler „User not assigned to tenant“

**Ursache**: Der Benutzer existiert, hat aber keine Rollen im angeforderten Mandanten.

**Lösung**: Weisen Sie dem Benutzer Rollen in einem Mandanten zu:

```python
UserTenantRoleEntity.create_or_update(
    user_id=user_id,
    tenant_id=tenant_id,
    roles=["AIHubUser"]
)
```

### „Zugriff verweigert“, obwohl der Benutzer Admin-Rollen hat

**Ursache**: Mandanten-Zugriffsregeln schränken die Benutzerberechtigungen ein. (Sysadmins – Benutzer mit der Keycloak Realm-Rolle `AIHubSysAdmin` – umgehen diese Prüfung vollständig; wenn das Problem für einen Sysadmin weiterhin besteht, ist die Umgehung selbst falsch konfiguriert.)

**Lösung**: Überprüfen Sie die Mandanten-Zugriffsregeln:

```python
tenant = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
print(tenant.access_rules)  # Check what the tenant allows
```

### Leere Mandanten-Zugriffsregeln = Kein Zugriff

Wenn ein Mandant keine Zugriffsregeln (`[]`) hat, wird ALLEN Benutzern in diesem Mandanten der Zugriff auf alles verweigert.

**Lösung**: Legen Sie entsprechende Mandanten-Zugriffsregeln fest:

```python
tenant.access_rules = ["aihub.user.>"]
tenant.save()
```

## Sicherheitsaspekte

-   **Mounten Sie niemals `TestAuthHandler` an Produktions-Einstiegspunkten** – er befindet sich aus diesem Grund unter `core.testing`;
    Produktionsdateien `app/main.py` müssen `KeycloakAuthHandler` oder `TokenAuthHandler` verwenden
-   **JWTs korrekt validieren** – Issuer, Audience und Signatur immer überprüfen
-   **HTTPS verwenden** – niemals Tokens über unverschlüsselte Verbindungen übertragen
-   **API-Tokens regelmäßig rotieren** – Token-Ablauf und Rotation implementieren
-   **Zugriffssteuerungsänderungen auditieren** – alle Rollen- und Berechtigungsmodifikationen protokollieren
-   **Prinzip der geringsten Privilegien** – minimal erforderlichen Zugriff gewähren
-   **Mandantenisolation** – Benutzer können nicht auf Ressourcen außerhalb der Grenzen ihres Mandanten zugreifen

## Migration vom vorherigen System

Frühere Versionen haben Rollen über die Microsoft Graph API von Azure AD abgerufen. Das neue System:

-   ✅ **Speichert Rollen lokal** in `UserTenantRoleEntity`
-   ✅ **Keine externen API-Aufrufe** während der Authentifizierung
-   ✅ **Mandantenbezogene Rollen** für Multi-Tenancy
-   ❌ **Keine automatische Rollensynchronisierung** vom Identitätsanbieter
-   ❌ **Kein automatisches Abrufen von Profilbildern** vom Identitätsanbieter

Weitere Details finden Sie unter [ADR: Lokale Multi-Mandanten-Rollenverwaltung](/de/arc42/decisions/2025_12_25_local_role_management.md).
