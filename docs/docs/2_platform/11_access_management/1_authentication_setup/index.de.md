---
title: Authentifizierung einrichten
source_sha: beb62c6692bca92ce547ae08d30363b977e9e57614c70d0973933a2512753dd4
---

# Authentifizierung einrichten

Der Swiss AI Hub verwendet ein Multi-Tenant-Authentifizierungs- und -Autorisierungssystem mit lokaler Rollenverwaltung.

## Überblick

Das Authentifizierungssystem besteht aus mehreren Schlüsselkomponenten:

- **Auth Handlers**: Validieren Anmeldeinformationen und ermitteln die Benutzeridentität
- **Identity Models**: `UserIdentity` und `TenantIdentity` repräsentieren authentifizierte Benutzer und deren
  Mandantenkontext
- **Zugriffskontrolle**: `AccessChecker` setzt Berechtigungen basierend auf hierarchischen Zugriffsregeln durch
- **Multi-Tenancy**: Alle Operationen erfolgen innerhalb eines Mandantenkontextes

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

- **OAuth2/OIDC**: JWT-Tokens von Keycloak (unterstützt föderierte Identitätsanbieter wie Azure AD, Google usw.)
- **API Tokens**: Langlebige Tokens für den programmatischen Zugriff
- **OpenWebUI-Integration**: Spezieller Handler für OpenWebUI-Benutzer
- **Entwicklungsmodus**: Gefährlicher Handler nur für die Entwicklung (niemals in Produktion verwenden!)

### 2. Benutzerauflösung

Auth Handlers erstellen oder aktualisieren Benutzer automatisch bei der ersten Anmeldung:

```python
user_entity = UserEntity.ensure_user_exists_for_auth(
    oid=user_id,
    name=user_name,
    email=user_email,
)
```

**Verhalten des ersten Benutzers**: Der erste Benutzer, der sich authentifiziert, erhält automatisch
Administratorrollen. Nachfolgende Benutzer erhalten Standard-Benutzerrollen (konfigurierbar über `UserSignupSettings`).

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

**Tenant Header**: Clients sollten den Header `x-tenant-id: <tenant-id>` in Anfragen aufnehmen. Wird er weggelassen,
wird der Standard-Mandant verwendet.

### 4. Erstellung der UserIdentity

Auth Handlers geben eine `UserIdentity` zurück, die sowohl Benutzer- als auch Mandanteninformationen enthält:

```python
return UserIdentity(
    id=user.id,
    name=user.name,
    email=user.email,
    roles=user.get_roles(tenant.id),
    acting_within_tenant=tenant,
)
```

## Multi-Tenant-Rollenverwaltung

### Kernentitäten

**TenantEntity**

- Definiert organisatorische Grenzen
- Enthält `access_rules`, die begrenzen, worauf JEDER Benutzer im Mandanten zugreifen kann
- Beispiel: `["aihub.user.agent.>"]` gewährt Zugriff auf Benutzer-Ebene für alle Agents

**UserTenantRoleEntity**

- Ordnet Benutzer Mandanten mit spezifischen Rollen zu
- Massgebliche Quelle für Benutzer-Mandant-Rollen-Beziehungen
- Benutzer können in verschiedenen Mandanten unterschiedliche Rollen haben

**RoleEntity**

- Definiert Rollen mit optionaler Mandanten-Einschränkung
- Systemrollen: `tenant_id=None` (für alle Mandanten verfügbar)
- Mandanten-spezifische Rollen: `tenant_id=<specific-tenant>` (nur für diesen Mandanten)

**UserEntity**

- Speichert Benutzerprofildaten (Name, E-Mail usw.)
- **Speichert KEINE Rollen** - Rollen werden aus `UserTenantRoleEntity` abgerufen

### Zugriff auf Benutzerrollen

```python
# Get user's roles in a specific tenant
roles = user.get_roles(tenant_id)

# Get all access rules for a user in a tenant
access_rules = RoleEntity.get_access_rules_for_roles(roles, tenant_id=tenant_id)
```

## Zugriffskontrolle

### AccessChecker

Die Klasse `AccessChecker` führt Autorisierungsprüfungen mit einer zweistufigen Zugriffskontrolle durch:

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

# Create checker from UserIdentity (includes tenant context)
checker = AccessChecker.from_user(user)

# Check access level
level = checker.access_level("aihub.user.agent.class-a.id-123")
# Returns: AccessLevel.ACCESS_ADMIN | ACCESS_USER | ACCESS_DENIED
```

### Zweistufige Zugriffsprüfung

**KRITISCH**: Mandanten-Zugriffsregeln dienen als OBERGRENZE/BEGRENZUNG für Benutzerberechtigungen.

1. **STUFE 1**: Bestimmen Sie die Zugriffsebene des Mandanten (Admin oder Benutzer)
2. **STUFE 2**: Bestimmen Sie die Zugriffsebene des Benutzers (Admin oder Benutzer)
3. **STUFE 3**: Geben Sie das MINIMUM beider Ebenen zurück

**Beispiel**:

```python
# Tenant has: aihub.user.agent.> (user-level access to all agents)
# User has: aihub.admin.agent.> (admin-level access to all agents)

# User gets ACCESS_USER (capped by tenant boundary)
checker.access_level("aihub.user.agent.class-a.id-1")  # → ACCESS_USER
```

### Zugriffsregelformat

Zugriffsregeln folgen einer hierarchischen Punktnotation:

```
aihub.[admin|user].<resource>.<subresource>.<id>
```

**Platzhalter**:

- `*` - Einzelstufen-Platzhalter: `aihub.user.agent.*` passt zu jedem einzelnen Agenten
- `>` - Mehrstufen-Platzhalter: `aihub.user.agent.>` passt zu allen Agents und Unterressourcen

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

Erstellen Sie niemals `AccessChecker` ohne Mandanten-Zugriffsregeln:

```python
# ❌ BAD: Manual construction without tenant context
checker = AccessChecker(user_access_rules, [])

# ✅ GOOD: Use factory method that extracts both user and tenant rules
checker = AccessChecker.from_user(user)  # user is UserIdentity with tenant context
```

### 2. Mandantenzugehörigkeit überprüfen

Verifizieren Sie immer, dass Benutzer Zugriff auf den Mandanten haben, bevor Sie Operationen durchführen:

```python
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
if not roles:
    raise HTTPException(403, "User not assigned to tenant")
```

### 3. Verwenden Sie die minimal erforderliche Zugriffsebene

Gewähren Sie Benutzern die minimale Zugriffsebene, die für ihre Rolle erforderlich ist:

```python
# ❌ BAD: Over-permissive
access_rules = ["aihub.admin.>"]

# ✅ GOOD: Scoped to specific resources
access_rules = ["aihub.user.agent.class-a.>"]
```

### 4. Mandanten-Zugriffsregeln als Begrenzungen

Verwenden Sie Mandanten-Zugriffsregeln, um den Geltungsbereich ALLER Benutzer in einem Mandanten zu begrenzen:

```python
# Tenant for analytics team - only access to specific agent classes
tenant_access_rules = [
    "aihub.user.agent.analytics.*",
    "aihub.user.service.data-pipeline"
]

# Selbst Admin-Benutzer in diesem Mandanten können nicht auf andere Ressourcen zugreifen
```

## Fehlerbehebung

### Fehler: "User not assigned to tenant"

**Ursache**: Der Benutzer existiert, hat aber keine Rollen im angeforderten Mandanten.

**Lösung**: Weisen Sie dem Benutzer Rollen im Mandanten zu:

```python
UserTenantRoleEntity.create_or_update(
    user_id=user_id,
    tenant_id=tenant_id,
    roles=["AIHubUser"]
)
```

### "Zugriff verweigert", obwohl der Benutzer Administratorrollen hat

**Ursache**: Mandanten-Zugriffsregeln schränken die Benutzerberechtigungen ein.

**Lösung**: Überprüfen Sie die Mandanten-Zugriffsregeln:

```python
tenant = TenantEntity.get_tenant_by_id(tenant_id)
print(tenant.access_rules)  # Überprüfen Sie, was der Mandant erlaubt
```

### Leere Mandanten-Zugriffsregeln = Kein Zugriff

Wenn ein Mandant keine Zugriffsregeln (`[]`) hat, wird ALLEN Benutzern in diesem Mandanten der Zugriff auf alles
verweigert.

**Lösung**: Legen Sie geeignete Mandanten-Zugriffsregeln fest:

```python
tenant.access_rules = ["aihub.user.>"]
tenant.save()
```

## Sicherheitsaspekte

- **Verwenden Sie niemals DangerousDevelopmentOnlyAuthHandler in der Produktion** - er umgeht alle
  Sicherheitsmechanismen
- **JWTs korrekt validieren** - überprüfen Sie immer Herausgeber (Issuer), Zielgruppe (Audience) und Signatur
- **HTTPS verwenden** - übertragen Sie Tokens niemals über unverschlüsselte Verbindungen
- **API-Tokens regelmässig rotieren** - implementieren Sie Token-Ablauf und -Rotation
- **Änderungen an der Zugriffskontrolle auditieren** - protokollieren Sie alle Rollen- und Berechtigungsänderungen
- **Prinzip der geringsten Rechte** - gewähren Sie den minimal erforderlichen Zugriff
- **Mandantenisolation** - Benutzer können nicht auf Ressourcen ausserhalb der Grenzen ihres Mandanten zugreifen

## Migration vom vorherigen System

Frühere Versionen haben Rollen aus Azure AD über die Microsoft Graph API abgerufen. Das neue System:

- ✅ **Speichert Rollen lokal** in `UserTenantRoleEntity`
- ✅ **Keine externen API-Aufrufe** während der Authentifizierung
- ✅ **Mandanten-bezogene Rollen** für Multi-Tenancy
- ❌ **Keine automatische Rollensynchronisierung** vom Identitätsanbieter
- ❌ **Kein automatisches Abrufen von Profilbildern** vom Identitätsanbieter

Weitere Details finden Sie unter
[ADR: Local Multi-Tenant Role Management](/de/arc42/decisions/2025_12_25_local_role_management.md).
