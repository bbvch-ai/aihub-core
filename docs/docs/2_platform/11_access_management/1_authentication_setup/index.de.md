```markdown
---
title: Authentifizierungseinstellungen
source_sha: "5594a4671b6a13b80dbd2c52debaafecf49fd8e22deb39149118ef4475b35a11"
---

# Authentifizierungseinstellungen

Der Swiss AI Hub verwendet ein Multi-Mandanten-Authentifizierungs- und Autorisierungssystem mit lokaler Rollenverwaltung.

## Übersicht

Das Authentifizierungssystem besteht aus mehreren Schlüsselkomponenten:

-   **Auth Handlers**: Validieren Zugangsdaten und lösen die Benutzeridentität auf
-   **Identitätsmodelle**: `UserIdentity` und `TenantIdentity` repräsentieren authentifizierte Benutzer und ihren Mandantenkontext
-   **Zugriffssteuerung**: `AccessChecker` setzt Berechtigungen basierend auf hierarchischen Zugriffsregeln durch
-   **Multi-Tenancy**: Alle Operationen erfolgen innerhalb eines Mandantenkontextes

## Authentifizierungsablauf

### 1. Token-Validierung

Auth Handler validieren eingehende Anfragen und extrahieren Benutzerinformationen:

```python
# Keycloak OIDC JWT validation
user_identity = await KeycloakAuthHandler()(request)

# Token-based authentication
user_identity = await TokenAuthHandler()(request)
```

Unterstützte Authentifizierungsmethoden:

-   **OAuth2/OIDC**: JWT-Token von Keycloak (unterstützt föderierte Identitätsanbieter wie Azure AD, Google usw.)
-   **API-Token**: Langlebige Token für den programmatischen Zugriff
-   **OpenWebUI Integration**: Spezieller Handler für OpenWebUI-Benutzer
-   **Entwicklungsmodus**: Gefährlicher, nur für die Entwicklung bestimmter Handler (niemals in der Produktion verwenden!)

### 2. Benutzerauflösung

Auth Handler erstellen oder aktualisieren Benutzer bei der ersten Anmeldung automatisch:

```python
user_entity = UserEntity.ensure_user_exists_for_auth(
    oid=user_id,
    name=user_name,
    email=user_email,
)
```

**Verhalten des ersten Benutzers**: Der erste Benutzer, der sich authentifiziert, erhält automatisch Admin-Rollen. Nachfolgende Benutzer erhalten Standard-Benutzerrollen (konfigurierbar über `UserSignupSettings`).

### 3. Mandantenkontext-Auflösung

Jede authentifizierte Anfrage muss einen Mandantenkontext haben:

```python
# Extract from x-tenant-id header or fall back to default tenant
tenant = TenantIdentity.from_request_for_user(request, user_id)

# Verify user has access to this tenant
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
if not roles:
    raise HTTPException(403, "User not assigned to tenant")
```

**Mandanten-Header**: Clients sollten den Header `x-tenant-id: <tenant-id>` in Anfragen aufnehmen. Wird er weggelassen, wird der Standard-Mandant verwendet.

### 4. Konstruktion der UserIdentity

Auth Handler geben eine `UserIdentity` zurück, die sowohl Benutzer- als auch Mandanteninformationen enthält:

```python
return UserIdentity(
    id=user.id,
    name=user.name,
    email=user.email,
    roles=user.get_roles(tenant.id),
    acting_within_tenant=tenant,
)
```

## Multi-Mandanten-Rollenverwaltung

### Kern-Entitäten

**TenantEntity**

-   Definiert organisatorische Grenzen
-   Enthält `access_rules`, die begrenzen, worauf JEDER Benutzer im Mandanten zugreifen kann
-   Beispiel: `["aihub.user.agent.>"]` gewährt Benutzerzugriff auf alle Agents

**UserTenantRoleEntity**

-   Ordnet Benutzern Mandanten mit spezifischen Rollen zu
-   Autoritative Quelle für Benutzer-Mandant-Rollen-Beziehungen
-   Benutzer können in verschiedenen Mandanten unterschiedliche Rollen haben

**RoleEntity**

-   Definiert Rollen mit optionaler Mandanten-Einschränkung
-   Systemrollen: `tenant_id=None` (allen Mandanten zur Verfügung)
-   Mandantenspezifische Rollen: `tenant_id=<specific-tenant>` (nur für diesen Mandanten)

**UserEntity**

-   Speichert Benutzerprofildaten (Name, E-Mail usw.)
-   **Speichert KEINE Rollen** - Rollen werden von `UserTenantRoleEntity` abgerufen

### Zugriff auf Benutzerrollen

```python
# Get user's roles in a specific tenant
roles = user.get_roles(tenant_id)

# Get all access rules for a user in a tenant
access_rules = RoleEntity.get_access_rules_for_roles(roles, tenant_id=tenant_id)
```

## Zugriffssteuerung

### AccessChecker

Die `AccessChecker`-Klasse führt Autorisierungsprüfungen mit zweistufiger Zugriffssteuerung durch:

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

# Create checker from UserIdentity (includes tenant context)
checker = AccessChecker.from_user(user)

# Check access level
level = checker.access_level("aihub.user.agent.class-a.id-123")
# Returns: AccessLevel.ACCESS_ADMIN | ACCESS_USER | ACCESS_DENIED
```

### Zweistufige Zugriffsprüfung

**WICHTIG**: Mandanten-Zugriffsregeln fungieren als OBERGRENZE für Benutzerberechtigungen.

1.  **STUFE 1**: Zugriffsebene des Mandanten bestimmen (Admin oder Benutzer)
2.  **STUFE 2**: Zugriffsebene des Benutzers bestimmen (Admin oder Benutzer)
3.  **STUFE 3**: Das MINIMUM beider Ebenen zurückgeben

**Beispiel**:

```python
# Mandant hat: aihub.user.agent.> (Benutzerzugriff auf alle Agents)
# Benutzer hat: aihub.admin.agent.> (Admin-Zugriff auf alle Agents)

# Benutzer erhält ACCESS_USER (begrenzt durch die Mandantengrenze)
checker.access_level("aihub.user.agent.class-a.id-1")  # → ACCESS_USER
```

### Format der Zugriffsregeln

Zugriffsregeln folgen einer hierarchischen Punktnotation:

```
aihub.[admin|user].<resource>.<subresource>.<id>
```

**Platzhalter**:

-   `*` - Platzhalter für eine Ebene: `aihub.user.agent.*` passt auf jeden einzelnen Agent
-   `>` - Platzhalter für mehrere Ebenen: `aihub.user.agent.>` passt auf alle Agents und Unterressourcen

**Beispiele**:

```python
"aihub.admin.>"                    # Voller Admin-Zugriff auf alles
"aihub.user.>"                     # Voller Benutzerzugriff auf alles
"aihub.user.agent.>"               # Benutzerzugriff auf alle Agents
"aihub.user.agent.class-a.*"       # Benutzerzugriff auf alle Agenten der Klasse A
"aihub.user.agent.class-a.id-123"  # Benutzerzugriff auf einen bestimmten Agenten
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
# ❌ SCHLECHT: Manuelle Konstruktion ohne Mandantenkontext
checker = AccessChecker(user_access_rules, [])

# ✅ GUT: Verwenden Sie eine Factory-Methode, die sowohl Benutzer- als auch Mandantenregeln extrahiert
checker = AccessChecker.from_user(user)  # user ist UserIdentity mit Mandantenkontext
```

### 2. Mandantenzugehörigkeit überprüfen

Überprüfen Sie immer, ob Benutzer Zugriff auf den Mandanten haben, bevor Sie Operationen ausführen:

```python
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
if not roles:
    raise HTTPException(403, "User not assigned to tenant")
```

### 3. Das Minimum an erforderlichen Zugriffsrechten verwenden

Gewähren Sie Benutzern die minimale Zugriffsebene, die für ihre Rolle erforderlich ist:

```python
# ❌ SCHLECHT: Übermäßig freizügig
access_rules = ["aihub.admin.>"]

# ✅ GUT: Auf spezifische Ressourcen beschränkt
access_rules = ["aihub.user.agent.class-a.>"]
```

### 4. Mandanten-Zugriffsregeln als Grenzen

Verwenden Sie Mandanten-Zugriffsregeln, um den Umfang ALLER Benutzer in einem Mandanten zu begrenzen:

```python
# Mandant für das Analyseteam - nur Zugriff auf spezifische Agentenklassen
tenant_access_rules = [
    "aihub.user.agent.analytics.*",
    "aihub.user.service.data-pipeline"
]

# Selbst Admin-Benutzer in diesem Mandanten können nicht auf andere Ressourcen zugreifen
```

## Fehlerbehebung

### Fehler "Benutzer keinem Mandanten zugewiesen"

**Ursache**: Der Benutzer existiert, hat aber keine Rollen im angeforderten Mandanten.

**Lösung**: Weisen Sie den Benutzer mit Rollen dem Mandanten zu:

```python
UserTenantRoleEntity.create_or_update(
    user_id=user_id,
    tenant_id=tenant_id,
    roles=["AIHubUser"]
)
```

### "Zugriff verweigert", obwohl der Benutzer Admin-Rollen hat

**Ursache**: Mandanten-Zugriffsregeln begrenzen die Benutzerberechtigungen.

**Lösung**: Mandanten-Zugriffsregeln prüfen:

```python
tenant = TenantEntity.get_tenant_by_id(tenant_id)
print(tenant.access_rules)  # Überprüfen Sie, was der Mandant zulässt
```

### Leere Mandanten-Zugriffsregeln = Kein Zugriff

Wenn ein Mandant keine Zugriffsregeln (mittels `[]`) hat, wird ALLEN Benutzern in diesem Mandanten der Zugriff auf alles verweigert.

**Lösung**: Legen Sie geeignete Mandanten-Zugriffsregeln fest:

```python
tenant.access_rules = ["aihub.user.>"]
tenant.save()
```

## Sicherheitsaspekte

-   **Verwenden Sie niemals den DangerousDevelopmentOnlyAuthHandler in der Produktion** - er umgeht alle Sicherheitsmechanismen
-   **JWTs korrekt validieren** - immer Aussteller, Zielgruppe und Signatur überprüfen
-   **HTTPS verwenden** - niemals Token über unverschlüsselte Verbindungen übertragen
-   **API-Token regelmäßig rotieren** - Token-Ablauf und -Rotation implementieren
-   **Zugriffssteuerungsänderungen auditieren** - alle Rollen- und Berechtigungsänderungen protokollieren
-   **Prinzip der geringsten Privilegien** - minimal erforderlichen Zugriff gewähren
-   **Mandantenisolation** - Benutzer können nicht auf Ressourcen außerhalb der Grenzen ihres Mandanten zugreifen

## Migration vom vorherigen System

Frühere Versionen haben Rollen aus Azure AD über die Microsoft Graph API abgerufen. Das neue System:

-   ✅ **Speichert Rollen lokal** in `UserTenantRoleEntity`
-   ✅ **Keine externen API-Aufrufe** während der Authentifizierung
-   ✅ **Mandanten-spezifische Rollen** für Multi-Tenancy
-   ❌ **Keine automatische Rollensynchronisation** vom Identitätsanbieter
-   ❌ **Kein automatisches Abrufen von Profilbildern** vom Identitätsanbieter

Weitere Details finden Sie unter [ADR: Lokale Multi-Mandanten-Rollenverwaltung](/de/arc42/decisions/2025_12_25_local_role_management.md).
```
