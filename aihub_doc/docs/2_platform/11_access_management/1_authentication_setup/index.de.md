---
title: Authentifizierungs-Setup
source_sha: f6e9915967d9144034d52df67dcb7c486cb92c4cbac61a3ccf782869b43a69bf
---

# Authentifizierungs-Setup

Swiss AI Hub verwendet ein Multi-Mandanten-Authentifizierungs- und Autorisierungssystem mit lokalem Rollenmanagement.

## Übersicht

Das Authentifizierungssystem besteht aus mehreren Schlüsselkomponenten:

- **Auth Handlers**: Validieren Anmeldeinformationen und lösen die Benutzeridentität auf
- **Identity Models**: `UserIdentity` und `TenantIdentity` repräsentieren authentifizierte Benutzer und ihren
  Mandantenkontext
- **Access Control**: `AccessChecker` erzwingt Berechtigungen basierend auf hierarchischen Zugriffsregeln
- **Multi-Tenancy**: Alle Operationen erfolgen innerhalb eines Mandantenkontextes

## Authentifizierungsfluss

### 1. Token-Validierung

Auth Handlers validieren eingehende Anfragen und extrahieren Benutzerinformationen:

```python
# OAuth2 JWT validation
user_identity = await OAuth2AuthHandler()(request)

# Token-based authentication
user_identity = await TokenAuthHandler()(request)
```

Unterstützte Authentifizierungsmethoden:

- **OAuth2/OIDC**: JWT-Token von Azure AD oder kompatiblen Anbietern
- **API Tokens**: Langlebige Token für den programmatischen Zugriff
- **OpenWebUI Integration**: Spezieller Handler für OpenWebUI-Benutzer
- **Development Mode**: Gefährlicher, nur für die Entwicklung geeigneter Handler (niemals in der Produktion verwenden!)

### 2. Benutzerauflösung

Auth Handlers erstellen oder aktualisieren Benutzer automatisch beim ersten Login:

```python
user_entity = UserEntity.ensure_user_exists_for_auth(
    oid=user_id,
    name=user_name,
    email=user_email,
)
```

**Verhalten des ersten Benutzers**: Der erste Benutzer, der sich authentifiziert, erhält automatisch Admin-Rollen.
Nachfolgende Benutzer erhalten Standard-Benutzerrollen (konfigurierbar über `UserSignupSettings`).

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

**Mandanten-Header**: Clients sollten den Header `x-tenant-id: <tenant-id>` in Anfragen aufnehmen. Wird er weggelassen,
wird der Standardmandant verwendet.

### 4. UserIdentity-Konstruktion

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

## Multi-Mandanten-Rollenmanagement

### Kernentitäten

**TenantEntity**

- Definiert organisatorische Grenzen
- Enthält `access_rules`, die den Zugriff ALLER Benutzer im Mandanten einschränken
- Beispiel: `["aihub.user.agent.>"]` gewährt Zugriff auf Benutzerebene für alle Agents

**UserTenantRoleEntity**

- Ordnet Benutzern Mandanten mit spezifischen Rollen zu
- Autoritative Quelle für Benutzer-Mandanten-Rollen-Beziehungen
- Benutzer können in verschiedenen Mandanten unterschiedliche Rollen haben

**RoleEntity**

- Definiert Rollen mit optionaler Mandanten-Eingrenzung (Scoping)
- Systemrollen: `tenant_id=None` (für alle Mandanten verfügbar)
- Mandantenspezifische Rollen: `tenant_id=<specific-tenant>` (nur für diesen Mandanten)

**UserEntity**

- Speichert Benutzerprofildaten (Name, E-Mail usw.)
- **Speichert KEINE Rollen** – Rollen werden von `UserTenantRoleEntity` abgerufen

### Zugriff auf Benutzerrollen

```python
# Get user's roles in a specific tenant
roles = user.get_roles(tenant_id)

# Get all access rules for a user in a tenant
access_rules = RoleEntity.get_access_rules_for_roles(roles, tenant_id=tenant_id)
```

## Zugriffskontrolle

### AccessChecker

Die `AccessChecker`-Klasse führt Autorisierungsprüfungen mit zweistufiger Zugriffskontrolle durch:

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker

# Create checker from UserIdentity (includes tenant context)
checker = AccessChecker.from_user(user)

# Check access level
level = checker.access_level("aihub.user.agent.class-a.id-123")
# Returns: AccessLevel.ACCESS_ADMIN | ACCESS_USER | ACCESS_DENIED
```

### Zweistufige Zugriffsprüfung

**WICHTIG**: Mandantenzugriffsregeln fungieren als OBERGRENZE/BOUNDARY für Benutzerberechtigungen.

1. **STUFE 1**: Bestimmen des Zugriffslevels des Mandanten (Admin oder Benutzer)
2. **STUFE 2**: Bestimmen des Zugriffslevels des Benutzers (Admin oder Benutzer)
3. **STUFE 3**: Zurückgeben des MINIMUMS beider Levels

**Beispiel**:

```python
# Mandant hat: aihub.user.agent.> (Zugriff auf Benutzerebene auf alle Agents)
# Benutzer hat: aihub.admin.agent.> (Zugriff auf Admin-Ebene auf alle Agents)

# Benutzer erhält ACCESS_USER (begrenzt durch die Mandantengrenze)
checker.access_level("aihub.user.agent.class-a.id-1")  # → ACCESS_USER
```

### Format der Zugriffsregeln

Zugriffsregeln folgen einer hierarchischen Punktnotation:

```
aihub.[admin|user].<resource>.<subresource>.<id>
```

**Wildcards**:

- `*` - Single-Level-Wildcard: `aihub.user.agent.*` stimmt mit jedem einzelnen Agent überein
- `>` - Multi-Level-Wildcard: `aihub.user.agent.>` stimmt mit allen Agents und Unterressourcen überein

**Beispiele**:

```python
"aihub.admin.>"                    # Voller Admin-Zugriff auf alles
"aihub.user.>"                     # Voller Benutzerzugriff auf alles
"aihub.user.agent.>"               # Benutzerzugriff auf alle Agents
"aihub.user.agent.class-a.*"       # Benutzerzugriff auf alle Agents der Klasse A
"aihub.user.agent.class-a.id-123"  # Benutzerzugriff auf einen spezifischen Agent
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

Erstellen Sie niemals einen `AccessChecker` ohne Mandantenzugriffsregeln:

```python
# ❌ BAD: Manuelle Konstruktion ohne Mandantenkontext
checker = AccessChecker(user_access_rules, [])

# ✅ GOOD: Verwenden Sie die Factory-Methode, die sowohl Benutzer- als auch Mandantenregeln extrahiert
checker = AccessChecker.from_user(user)  # user ist UserIdentity mit Mandantenkontext
```

### 2. Mandantenzugehörigkeit überprüfen

Verifizieren Sie immer, dass Benutzer Zugriff auf den Mandanten haben, bevor Sie Operationen durchführen:

```python
roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id)
if not roles:
    raise HTTPException(403, "User not assigned to tenant")
```

### 3. Das Mindesterforderliche Zugriffslevel verwenden

Gewähren Sie Benutzern das minimale Zugriffslevel, das für ihre Rolle erforderlich ist:

```python
# ❌ BAD: Übermäßig permissiv
access_rules = ["aihub.admin.>"]

# ✅ GOOD: Auf spezifische Ressourcen beschränkt
access_rules = ["aihub.user.agent.class-a.>"]
```

### 4. Mandantenzugriffsregeln als Grenzen

Verwenden Sie Mandantenzugriffsregeln, um den Umfang ALLER Benutzer in einem Mandanten zu begrenzen:

```python
# Mandant für das Analyseteam – nur Zugriff auf spezifische Agent-Klassen
tenant_access_rules = [
    "aihub.user.agent.analytics.*",
    "aihub.user.service.data-pipeline"
]

# Selbst Admin-Benutzer in diesem Mandanten können nicht auf andere Ressourcen zugreifen
```

## Fehlerbehebung

### Fehler "Benutzer keinem Mandanten zugewiesen"

**Ursache**: Der Benutzer existiert, hat aber keine Rollen im angeforderten Mandanten.

**Lösung**: Weisen Sie dem Benutzer Rollen im Mandanten zu:

```python
UserTenantRoleEntity.create_or_update(
    user_id=user_id,
    tenant_id=tenant_id,
    roles=["AIHubUser"]
)
```

### "Zugriff verweigert", obwohl Benutzer Admin-Rollen hat

**Ursache**: Mandantenzugriffsregeln schränken die Benutzerberechtigungen ein.

**Lösung**: Überprüfen Sie die Mandantenzugriffsregeln:

```python
tenant = TenantEntity.get_tenant_by_id(tenant_id)
print(tenant.access_rules)  # Überprüfen Sie, was der Mandant erlaubt
```

### Leere Mandantenzugriffsregeln = Kein Zugriff

Wenn ein Mandant keine Zugriffsregeln (`[]`) hat, wird ALLEN Benutzern in diesem Mandanten der Zugriff auf alles
verweigert.

**Lösung**: Legen Sie geeignete Mandantenzugriffsregeln fest:

```python
tenant.access_rules = ["aihub.user.>"]
tenant.save()
```

## Sicherheitsaspekte

- **Verwenden Sie niemals DangerousDevelopmentOnlyAuthHandler in der Produktion** – er umgeht alle
  Sicherheitsmechanismen
- **JWTs korrekt validieren** – immer Issuer, Audience und Signatur überprüfen
- **HTTPS verwenden** – niemals Token über unverschlüsselte Verbindungen übertragen
- **API-Token regelmäßig rotieren** – Token-Ablauf und Rotation implementieren
- **Zugriffskontrolländerungen auditieren** – alle Änderungen an Rollen und Berechtigungen protokollieren
- **Prinzip der geringsten Rechte** – minimal benötigten Zugriff gewähren
- **Mandantenisolation** – Benutzer können nicht auf Ressourcen außerhalb der Grenzen ihres Mandanten zugreifen

## Migration vom vorherigen System

Frühere Versionen bezogen Rollen aus Azure AD über die Microsoft Graph API. Das neue System:

- ✅ **Speichert Rollen lokal** in `UserTenantRoleEntity`
- ✅ **Keine externen API-Aufrufe** während der Authentifizierung
- ✅ **Mandanten-eingegrenzte Rollen** für Multi-Tenancy
- ❌ **Keine automatische Rollensynchronisation** vom Identitätsanbieter
- ❌ **Kein automatisches Abrufen von Profilbildern** vom Identitätsanbieter

Siehe [ADR: Lokales Multi-Mandanten-Rollenmanagement](/de/aihub_doc/arc42/decisions/2025_12_25_local_role_management.md)
für Details.
