# OpenWebUI Multi-Tenancy Integration Concept

This document captures all learnings about AI-Hub's permission system and OpenWebUI's capabilities, along with the challenges and high-level approaches for enabling multi-tenancy in the OpenWebUI integration.

---

## Part 1: AI-Hub Permission System

### Access Rules

Access rules define what resources a user or tenant can access. They follow a hierarchical dot-notation format:

```
aihub.[user|admin].<resource_type>.<resource_class>.<resource_id>
```

**Examples:**
- `aihub.user.agent.assistant.*` - User access to all agents in the "assistant" class
- `aihub.admin.agent.>` - Admin access to all agents (multi-level wildcard)
- `aihub.user.service.knowledge` - User access to the knowledge service

**Prefixes:**
- `aihub.user.*` - Regular user permissions
- `aihub.admin.*` - Admin permissions (implicitly includes user-level access)

**Wildcards:**
| Wildcard | Matches | Example |
|----------|---------|---------|
| `*` | Exactly one token | `aihub.user.agent.class-a.*` matches `...class-a.id-1` |
| `>` | One or more tokens (must be last) | `aihub.user.agent.>` matches any agent |
| `?*` | Template: "has any access at this level?" | Used in permission checks |
| `?>` | Template: "has any access at this level or below?" | Used in permission checks |

### Roles

Roles are named collections of access rules. They serve as templates for permissions.

**Properties:**
- `name` - Unique identifier (e.g., "AIHubAdmin", "AgentViewer")
- `access_rules` - List of access rule strings
- `tenant_id` - Optional; if set, role is tenant-specific; if null, role is system-wide

**System Roles** (tenant_id = null):
- Available to all tenants
- Examples: "AIHubAdmin", "AIHubUser"

**Tenant-Specific Roles** (tenant_id = "xyz"):
- Only available within that specific tenant
- Created by tenant administrators
- Can override system roles of the same name within that tenant

### Tenants

Tenants are organizational boundaries that define the maximum permissions available to any user within them.

**Properties:**
- `id` - Unique identifier
- `name` - Display name (unique)
- `access_rules` - List of access rules acting as a **permission ceiling**
- `is_default` - Boolean; one tenant must be the default

**Tenant as Ceiling:**
A tenant's access_rules define the MAXIMUM permissions any user within that tenant can have, regardless of their personal roles.

**Example:**
```
Tenant "Beta Inc": access_rules = [aihub.user.agent.>]  # Only agents, no processes

User Bob in "Beta Inc":
  roles: [AIHubAdmin]  # Would normally grant aihub.admin.> (full access)

When Bob tries to access a process:
  Result: ACCESS_DENIED (tenant ceiling doesn't allow processes)
```

### User-Tenant-Role Mapping

Users can belong to multiple tenants, with different roles in each.

**Data Model:**
```
UserTenantRoleEntity:
  user_id: string
  tenant_id: string
  roles: list[string]  # Role names active for this user in this tenant

  Unique constraint: (user_id, tenant_id)
```

**Example:**
```
User "alice@example.com":
  ├─ In Tenant "Marketing":
  │  └─ roles: ["TeamLead", "AgentManager"]
  │
  └─ In Tenant "IT":
     └─ roles: ["ReadOnly"]
```

### Two-Stage Access Control

The AccessChecker implements a two-stage authorization model:

**Stage 1: Tenant Check**
- Does the tenant's access_rules allow this resource?
- Returns: tenant_access_level (ADMIN, USER, or DENIED)

**Stage 2: User Check**
- Do the user's roles (aggregated access_rules) allow this resource?
- Returns: user_access_level (ADMIN, USER, or DENIED)

**Final Result:**
```
effective_access = MIN(tenant_access_level, user_access_level)
```

This ensures:
- Users can never exceed their tenant's permissions
- Users can only use permissions granted by their roles
- Both conditions must be satisfied

### Tenant Resolution in API Requests

When an API request arrives:
1. Check for `x-tenant-id` header
2. If missing, fall back to user's `active_tenant_id` (if stored)
3. If still missing, fall back to the system's default tenant
4. Verify user has role assignment in the resolved tenant
5. If no role assignment, return 403 Forbidden

---

## Part 2: OpenWebUI Capabilities

### Groups

Groups in OpenWebUI are organizational units for managing permissions and resource access.

**Properties:**
- `id` - Unique identifier (assigned by OpenWebUI)
- `displayName` - Human-readable name
- `members` - List of user references
- `externalId` - Optional; for OAuth/SCIM sync mapping
- `permissions` - Permission overrides for group members
- `visibility` - Who can see the group ("Anyone", "Members only", "No one")

**Key Characteristic - Additive Permissions:**
If a user is in multiple groups, they receive the **union** of all permissions. There is no "deny" mechanism - only grants exist.

### Workspace Models

OpenWebUI has workspace models - custom model configurations that can have access control.

**Model Properties:**
- `id` - Unique identifier
- `name` - Display name
- `base_model_id` - The underlying model/pipeline
- `meta` - Arbitrary metadata
- `access_control` - ACL defining who can read/write

**Access Control Structure:**
```
access_control:
  read:
    user_ids: [list of user IDs]
    group_ids: [list of group IDs]
  write:
    user_ids: [list of user IDs]
    group_ids: [list of group IDs]
```

**Visibility Modes:**
- **Public**: Visible to all users (empty ACL)
- **Private**: Visible only to owner
- **Restricted**: Visible to specific users/groups (via ACL)

A model is visible to a user if:
- Model is public, OR
- User's ID is in read.user_ids, OR
- Any of user's groups is in read.group_ids

### SCIM 2.0 API

OpenWebUI supports SCIM 2.0 for programmatic user and group management.

**Configuration:**
```env
SCIM_ENABLED=true
SCIM_TOKEN=<secure-random-string>
```

**Endpoints (at `/api/v1/scim/v2/`):**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /Groups | Create group |
| GET | /Groups | List groups |
| GET | /Groups/{id} | Get group |
| PUT | /Groups/{id} | Replace group (full update) |
| PATCH | /Groups/{id} | Partial update |
| DELETE | /Groups/{id} | Delete group |

**Group membership is managed at the Group level:**
- To add/remove users, update the group's `members` array
- Users can be in multiple groups
- Changes are immediate

### OAuth Group Synchronization

OpenWebUI can sync groups from OAuth/OIDC providers.

**Configuration:**
```env
ENABLE_OAUTH_GROUP_MANAGEMENT=true
ENABLE_OAUTH_GROUP_CREATION=true  # Auto-create groups not in OpenWebUI
OAUTH_GROUP_CLAIM=groups          # Token claim containing group list
```

**Behavior:**
- On each OAuth login, user's groups are synced from token claims
- Groups in token → user added to those groups
- Groups NOT in token → user removed from those groups
- This is **strict synchronization** - manual group assignments may be overwritten

**Limitation:** Admin users are exempt from automatic OAuth group sync.

### Pipelines and pipes()

OpenWebUI pipelines can dynamically return available "models" via the `pipes()` method.

**Current AI-Hub Integration:**
- The `pipes()` method calls AI-Hub API to discover online agents
- Returns list of agents as selectable "models" in the UI
- These are NOT persistent OpenWebUI models - they're discovered dynamically

**Important Distinction:**
- **Pipeline models** (from `pipes()`): Dynamic, no ACL support
- **Workspace models**: Persistent, support ACLs via groups

### Folders/Projects

OpenWebUI folders are more than simple organization - they're project workspaces.

**Folder Properties:**
- Nested hierarchy support
- **System Prompt**: Auto-applied to all chats in the folder
- **Attached Knowledge**: RAG context shared across folder chats
- **Visual Customization**: Custom backgrounds

**Potential for Multi-Tenancy:**
Each tenant could be represented as a folder with:
- Tenant-specific system prompts
- Tenant-specific knowledge bases
- Visual distinction between tenants

### Permission Categories

OpenWebUI permissions are organized hierarchically:

1. **Workspace**: models, knowledge, prompts, tools access
2. **Sharing**: public sharing of resources
3. **Chat**: file upload, edit, delete, temporary chats
4. **Features**: API keys, notes, channels, web search, image generation
5. **Settings**: interface configuration

Permissions follow additive logic across groups.

---

## Part 3: The Challenge

### Core Problem

The OpenWebUI pipeline runs **server-side** within OpenWebUI, not in the browser. When a user selects a tenant in the aihub_web frontend:
- The tenant selection lives in the browser
- The pipeline has no direct access to this browser state
- The pipeline cannot know which tenant the user has selected

### Model Visibility Challenge

AI-Hub's permission model is more granular than OpenWebUI's:
- **AI-Hub**: Effective access = tenant.access_rules ∩ user.role.access_rules
- **OpenWebUI**: Groups are additive (union)

Two users in the same tenant may have different roles, and thus should see different models. This cannot be expressed with simple tenant-level groups.

### Agent Discovery Challenge

Currently, agents are discovered via the pipeline's `pipes()` method, which returns them dynamically. These dynamic models:
- Cannot have persistent ACLs
- Are not OpenWebUI workspace models
- Visibility cannot be controlled via native RBAC

### Chat Isolation Challenge

OpenWebUI stores all chats per user, regardless of tenant. Even with tags or folders:
- Users can see all their chats
- No strict tenant-level isolation exists
- Filtering is user-initiated, not enforced

---

## Part 4: High-Level Approaches

### Approach 1: Composite Group Mapping

Map each (tenant, role) combination to an OpenWebUI group.

**Concept:**
```
OpenWebUI Group = "{tenant_id}__{role_name}"

Examples:
- "acme__AIHubAdmin"
- "acme__AgentViewer"
- "beta__ReadOnly"
```

**Why This Works:**
- A group represents the intersection of tenant ceiling AND role permissions
- Model ACLs include only groups where BOTH tenant AND role allow access
- User is placed only in groups for their roles within the selected tenant
- Different roles → different groups → different visible models

### Approach 2: Register Agents as Workspace Models

Instead of relying on `pipes()` for agent discovery, register each AI-Hub agent as a persistent OpenWebUI workspace model.

**Benefits:**
- Workspace models support ACLs
- Native OpenWebUI RBAC enforces visibility
- No reliance on pipeline code for access control

**Agent-to-Model Mapping:**
- Each online AI-Hub agent becomes an OpenWebUI workspace model
- Model metadata links back to the AI-Hub agent
- Pipeline routes requests based on model metadata

### Approach 3: Backend Active Tenant

Store the user's currently selected tenant in the AI-Hub backend.

**Flow:**
1. User switches tenant in aihub_web
2. Frontend calls API to update user's active_tenant_id
3. API also updates user's OpenWebUI groups via SCIM
4. API requests resolve tenant from header OR user's active_tenant_id OR default

**Benefits:**
- Works for all integrations (not just OpenWebUI)
- Single API call for tenant switch
- Pipeline doesn't need to know tenant - API resolves it

### Approach 4: Folders as Tenants

Use OpenWebUI folders to organize chats by tenant.

**Concept:**
- Each tenant = one OpenWebUI folder
- Folder contains tenant-specific system prompts and knowledge
- Users are encouraged to work within their tenant's folder
- Chats created in folder inherit tenant context

**Limitation:**
- Not strict isolation - users can still see/access other folders
- Organizational, not security boundary

---

## Part 5: Sync Considerations

### Events Requiring Sync

| Event | Required Action |
|-------|-----------------|
| Tenant access_rules changed | Recompute model ACLs for all groups with that tenant |
| Role access_rules changed | Recompute model ACLs for all groups with that role |
| Role created | Create new groups, recompute ACLs |
| Role deleted | Delete groups, recompute ACLs |
| Agent comes online | Register as workspace model, set ACLs |
| Agent goes offline | Update or remove workspace model |
| User switches tenant | Update user's OpenWebUI groups via SCIM |
| User roles change in tenant | Update user's OpenWebUI groups via SCIM |

### ACL Computation Logic

For each agent, determine which (tenant, role) groups should have access:

```
For each tenant T:
  Does T.access_rules allow this agent?
    No → skip tenant
    Yes →
      For each role R (system + tenant-specific):
        Does R.access_rules allow this agent?
          Yes → Add "{T.id}__{R.name}" to agent's ACL
```

### User Group Assignment Logic

When user U switches to tenant T:

```
user_roles = get_roles_for_user_in_tenant(U, T)
groups_to_assign = ["{T.id}__{role}" for role in user_roles]
set_user_groups(U, groups_to_assign)  # Via SCIM
```

---

## Part 6: Open Considerations

### OpenWebUI Iframe Refresh
When a user switches tenant and their groups change, does OpenWebUI automatically reflect the new model visibility? Or is a page refresh/re-login required?

### User ID Mapping
How to map AI-Hub user IDs to OpenWebUI user IDs for SCIM operations? Email is a natural candidate since both systems use email as a unique identifier.

### Performance at Scale
For large deployments with many tenants, roles, and agents:
- ACL recomputation could be expensive
- Consider batch processing, async events, or caching

### Initial Sync
On system startup or deployment, how to ensure all groups exist and ACLs are correct? Options include startup background job or manual sync endpoint.

### Pipeline Modification
The pipeline may need modification to route requests based on workspace model metadata rather than dynamic discovery.

---

## References

### AI-Hub Files
- Access rules and checking: `aihub_lib/aihub_lib/auth/access/AccessChecker.py`
- Tenant entity: `aihub_lib/aihub_lib/persistence/access/entities/TenantEntity.py`
- Role entity: `aihub_lib/aihub_lib/persistence/access/entities/RoleEntity.py`
- User-tenant-role mapping: `aihub_lib/aihub_lib/persistence/access/entities/UserTenantRoleEntity.py`
- Auth handler with tenant resolution: `aihub_lib/aihub_lib/auth/dependencies/AuthHandler.py`
- OpenWebUI pipeline: `deployment/templates/openwebui_functions/aihub_pipeline.py`
- Infrastructure pattern example: `aihub_lib/aihub_lib/infrastructure/litellm/`

### OpenWebUI Documentation
- Groups: https://docs.openwebui.com/features/rbac/groups
- Permissions: https://docs.openwebui.com/features/rbac/permissions
- Roles: https://docs.openwebui.com/features/rbac/roles
- SCIM: https://docs.openwebui.com/features/auth/scim
- SSO: https://docs.openwebui.com/features/auth/sso
- Models: https://docs.openwebui.com/features/workspace/models
- Folders: https://docs.openwebui.com/features/chat-features/conversation-organization

### OpenWebUI Internal APIs (for pipeline use)
```python
# Available within the pipeline context
from open_webui.models.chats import Chats
from open_webui.models.folders import Folders, FolderForm

# Folder operations
Folders.get_folder_by_parent_id_and_user_id_and_name(parent_id, user_id, name)
Folders.insert_new_folder(user_id, FolderForm(name=folder_name))

# Chat operations
Chats.get_chat_by_id(chat_id)
Chats.update_chat_folder_id_by_id_and_user_id(chat_id, user_id, folder_id)
```