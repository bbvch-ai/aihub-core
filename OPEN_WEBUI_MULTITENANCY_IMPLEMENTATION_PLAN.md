# Multi-Tenancy for OpenWebUI Integration - Implementation Plan

> **Reference Document**: For detailed background on AI-Hub's permission system, OpenWebUI's capabilities, and the theoretical foundation for this approach, see [`OPEN_WEBUI_MULTITENANCY_CONCEPT.md`](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md).

## Problem Statement

Multi-tenancy requires three capabilities:
1. **API Tenant Context**: Every API request needs `x-tenant-id` header
2. **Model Visibility**: Users should only see agents/models they have access to (per-user within tenant)
3. **Chat History Isolation**: Chats should be scoped per tenant

The OpenWebUI pipeline runs **server-side** - it cannot access browser-side data (URL params, postMessage). See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 3: The Challenge](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#part-3-the-challenge) for detailed analysis.

---

## Decisions Made

- **Model visibility**: Register agents as OpenWebUI workspace models with ACLs
- **Group strategy**: Map each (tenant, role) tuple to an OpenWebUI group
- **Tenant switch UX**: Window reload is acceptable (required for Pinia-Colada cache invalidation)
- **Chat organization**: Folders as tenants (each tenant = folder)
- **Initial sync**: On system startup via background job
- **User group management**: Via SCIM API

---

## Approach: Composite Group Mapping

**Map each (tenant, role) tuple to an OpenWebUI group.** This elegantly bridges AI-Hub's two-stage access control with OpenWebUI's native RBAC. See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 4: Approach 1](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#approach-1-composite-group-mapping) for the theoretical foundation.

### How It Works

**1. Group Naming Convention:**
```
OpenWebUI Group = "{tenant_id}__{role_name}"

Examples:
- "acme__AIHubAdmin"
- "acme__AgentViewer"
- "beta__AIHubAdmin"
- "beta__ReadOnly"
```

**2. Model/Agent ACL Assignment (computed):**
```
For each agent A:
  For each tenant T:
    IF T.access_rules allows agent A:
      For each role R (system + tenant-specific):
        IF R.access_rules allows agent A:
          Add group "{T.id}__{R.name}" to agent A's read ACL
```

This pre-computes the intersection: only groups where BOTH tenant AND role allow access.

**3. User Group Assignment (on tenant switch):**
```
User U switches to tenant T:
  user_roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(U.id, T.id)
  groups = [f"{T.id}__{role}" for role in user_roles]

  Via SCIM: Set user's OpenWebUI groups to exactly `groups`
```

User is placed ONLY in groups for their roles within the selected tenant.

### Why This Works

| AI-Hub Concept | OpenWebUI Mapping |
|----------------|-------------------|
| Tenant ceiling | Model only in groups where tenant allows |
| User roles | User only in groups for their roles |
| Two-stage intersection | Group represents the intersection |
| Per-user visibility | Different roles → different groups → different models |

See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 1: Two-Stage Access Control](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#two-stage-access-control) for the permission model details.

**Example:**
```
Tenant "Acme": access_rules = [aihub.user.agent.>]
Role "AgentViewer": access_rules = [aihub.user.agent.assistant.*]
Role "AgentAdmin": access_rules = [aihub.admin.agent.>]

Agent "assistant": requires aihub.user.agent.assistant.>

Group "acme__AgentViewer" ACL includes "assistant" ✓
  (tenant allows agents, role allows assistant)

Group "acme__AgentAdmin" ACL includes "assistant" ✓
  (tenant allows agents, role allows assistant via admin)

User Alice in Acme with roles [AgentViewer]:
  → Placed in group "acme__AgentViewer"
  → Sees agent "assistant" ✓

User Bob in Acme with roles [ReadOnly]:
  → Placed in group "acme__ReadOnly"
  → Group has no agent access
  → Sees no agents ✓
```

### Sync Triggers

| Event | Action |
|-------|--------|
| Tenant access_rules updated | Recompute ACLs for all groups with that tenant |
| Role access_rules updated | Recompute ACLs for all groups with that role |
| Agent created/modified | Compute which groups get access |
| User switches tenant | Update user's OpenWebUI groups via SCIM |
| User roles change in tenant | Update user's OpenWebUI groups via SCIM |

See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 5: Sync Considerations](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#part-5-sync-considerations) for detailed sync logic.

### Advantages Over Pipeline Filtering

- ✅ **Native OpenWebUI RBAC** - model visibility enforced by OpenWebUI
- ✅ **Secure** - no reliance on pipeline code for access control
- ✅ **Efficient** - no per-request API calls to check permissions
- ✅ **Consistent** - same permission model as AI-Hub
- ✅ **Auditable** - group membership visible in OpenWebUI admin

---

## Implementation Plan

### Phase 1: Backend Active Tenant

**Purpose**: Enable API to resolve tenant from user profile, add tenant switch endpoint, and build the frontend UI for tenant selection.

**Reference**: See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 4: Approach 3 - Backend Active Tenant](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#approach-3-backend-active-tenant) for the theoretical foundation.

#### 1.1 Database Schema Change

**File: `aihub_lib/aihub_lib/persistence/user/UserEntity.py`**

Add a new field to store the user's currently selected tenant:

```python
class UserEntity(Document):
    # ... existing fields ...
    active_tenant_id: str | None = StringField(null=True)
```

This field stores the tenant ID that the user has actively selected. When `None`, the system falls back to the default tenant.

#### 1.2 Auth Handler Modification

**File: `aihub_lib/aihub_lib/auth/dependencies/AuthHandler.py`**

Modify the `resolve_tenant_for_user()` method to implement a three-tier fallback:

```python
async def resolve_tenant_for_user(self, request: Request, user: UserIdentity) -> TenantEntity:
    """
    Resolve the tenant for the current request using three-tier fallback:
    1. x-tenant-id header (explicit per-request override)
    2. user.active_tenant_id (user's saved preference)
    3. Default tenant (system fallback)
    """
    # Priority 1: Explicit header
    tenant_id = request.headers.get("x-tenant-id")
    if tenant_id:
        tenant = TenantEntity.by_id(tenant_id)
        if tenant:
            return tenant

    # Priority 2: User's active tenant preference
    if user.active_tenant_id:
        tenant = TenantEntity.by_id(user.active_tenant_id)
        if tenant:
            return tenant

    # Priority 3: System default tenant
    return TenantEntity.get_default()
```

#### 1.3 API Endpoints

**File: `aihub_api/aihub_api/routes/user/UserController.py`**

Add three new endpoints for tenant management:

**GET `/users/me/tenant`** - Get current active tenant:
```python
@router.get("/users/me/tenant")
async def get_active_tenant(
    user: Annotated[UserIdentity, Security(auth_handler)]
) -> TenantResponse:
    """
    Returns the user's currently active tenant.
    Falls back to default tenant if no active tenant is set.
    """
    if user.active_tenant_id:
        tenant = TenantEntity.by_id(user.active_tenant_id)
        if tenant:
            return TenantResponse.from_entity(tenant)

    return TenantResponse.from_entity(TenantEntity.get_default())
```

**PUT `/users/me/tenant`** - Switch active tenant:
```python
@router.put("/users/me/tenant")
async def set_active_tenant(
    user: Annotated[UserIdentity, Security(auth_handler)],
    body: SetActiveTenantRequest,  # Contains tenant_id: str
) -> TenantResponse:
    """
    Switch the user's active tenant.

    Validates that:
    1. The tenant exists
    2. The user has at least one role assignment in that tenant

    After switching, the user's OpenWebUI groups will be updated
    to reflect their roles in the new tenant (Phase 4+).
    """
    tenant = TenantEntity.by_id(body.tenant_id)
    if not tenant:
        raise HTTPException(404, "Tenant not found")

    # Verify user has role assignment in this tenant
    user_tenant_role = UserTenantRoleEntity.by_user_and_tenant(user.id, body.tenant_id)
    if not user_tenant_role:
        raise HTTPException(403, "User has no roles in this tenant")

    # Update user's active tenant
    user_entity = UserEntity.by_id(user.id)
    user_entity.active_tenant_id = body.tenant_id
    user_entity.save()

    return TenantResponse.from_entity(tenant)
```

**GET `/users/me/tenants`** - List available tenants:
```python
@router.get("/users/me/tenants")
async def list_available_tenants(
    user: Annotated[UserIdentity, Security(auth_handler)]
) -> list[TenantWithRolesResponse]:
    """
    Returns all tenants the user has access to, along with their roles in each.

    This is used by the frontend to populate the tenant selector dropdown.
    """
    user_tenant_roles = UserTenantRoleEntity.by_user(user.id)

    result = []
    for utr in user_tenant_roles:
        tenant = TenantEntity.by_id(utr.tenant_id)
        if tenant:
            result.append(TenantWithRolesResponse(
                tenant=TenantResponse.from_entity(tenant),
                roles=utr.roles
            ))

    return result
```

#### 1.4 Frontend UI Design

**Visual Design Specification**:

The tenant selector appears in the top-right corner of the application, next to the user's profile area. The design follows this layout:

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Logo]  AI-Hub                          [🏢 Acme Corp ▼] [👤 Alice] │
└─────────────────────────────────────────────────────────────────────┘
                                                    ↑
                                           Tenant Selector
```

**Tenant Selector Component Behavior**:

1. **Display State**: Shows the currently active tenant name with a building icon (🏢) and a dropdown chevron (▼)
2. **Click Behavior**: Opens a dropdown listing all tenants the user has access to
3. **Dropdown Items**: Each item shows:
   - Tenant name
   - User's roles in that tenant (as subtle badges)
   - Checkmark (✓) next to the currently active tenant
4. **Selection Behavior**: When user selects a different tenant:
   - API call to `PUT /users/me/tenant`
   - On success: **Full window reload** (`window.location.reload()`)
   - The reload is REQUIRED because Pinia-Colada caches all API responses and there's no way to invalidate the entire cache programmatically

**Why Window Reload?**

Pinia-Colada (the state management library) caches API responses with query keys. When the tenant changes, ALL cached data becomes invalid because it was fetched under the previous tenant context. Rather than trying to manually invalidate every possible cache key, a full page reload ensures a clean state.

**File: `aihub_web/aihub_web/components/User/TenantSelector.vue`** (NEW)

```vue
<script setup lang="ts">
import { useTenantSelector } from '@/composables/user/useTenantSelector'

const {
  currentTenant,
  availableTenants,
  isLoading,
  switchTenant
} = useTenantSelector()

async function onTenantSelect(tenantId: string) {
  if (tenantId === currentTenant.value?.id) return

  await switchTenant(tenantId)
  // Full page reload to invalidate all Pinia-Colada caches
  window.location.reload()
}
</script>

<template>
  <Dropdown
    :model-value="currentTenant?.id"
    :options="availableTenants"
    option-label="tenant.name"
    option-value="tenant.id"
    :loading="isLoading"
    @update:model-value="onTenantSelect"
  >
    <template #value="{ value }">
      <div class="flex items-center gap-2">
        <i class="pi pi-building" />
        <span>{{ currentTenant?.name }}</span>
      </div>
    </template>
    <template #option="{ option }">
      <div class="flex items-center justify-between w-full">
        <span>{{ option.tenant.name }}</span>
        <div class="flex gap-1">
          <Tag
            v-for="role in option.roles"
            :key="role"
            :value="role"
            severity="secondary"
            class="text-xs"
          />
        </div>
      </div>
    </template>
  </Dropdown>
</template>
```

**File: `aihub_web/aihub_web/composables/user/useTenantSelector.ts`** (NEW)

```typescript
import { defineQuery, defineMutation } from '@pinia/colada'
import { getActiveTenant, getAvailableTenants, setActiveTenant } from '@core/sdk/client'

export const useTenantSelector = () => {
  // Query: Get current active tenant
  const { data: currentTenant, isPending: isLoadingCurrent } = useQuery({
    key: ['user', 'active-tenant'],
    query: () => getActiveTenant({ composable: '$fetch' }),
  })

  // Query: Get all available tenants with roles
  const { data: availableTenants, isPending: isLoadingTenants } = useQuery({
    key: ['user', 'available-tenants'],
    query: () => getAvailableTenants({ composable: '$fetch' }),
  })

  // Mutation: Switch tenant
  const { mutateAsync: switchTenant } = useMutation({
    mutation: async (tenantId: string) => {
      await setActiveTenant({
        composable: '$fetch',
        body: { tenant_id: tenantId }
      })
      // Note: Caller should trigger window.location.reload() after this
    },
  })

  return {
    currentTenant,
    availableTenants,
    isLoading: computed(() => isLoadingCurrent.value || isLoadingTenants.value),
    switchTenant,
  }
}
```

**File: `aihub_web/aihub_web/components/User/Bar.vue`** (MODIFY)

Add the TenantSelector component to the existing user bar:

```vue
<template>
  <div class="flex items-center gap-4">
    <!-- Add tenant selector before user avatar -->
    <TenantSelector />

    <!-- Existing user avatar and menu -->
    <UserAvatar />
  </div>
</template>
```

#### 1.5 Files to Create/Modify Summary

| File | Change |
|------|--------|
| `aihub_lib/.../persistence/user/UserEntity.py` | Add `active_tenant_id` field |
| `aihub_lib/.../auth/dependencies/AuthHandler.py` | Modify `resolve_tenant_for_user()` with three-tier fallback |
| `aihub_api/.../routes/user/UserController.py` | Add `GET/PUT /users/me/tenant` and `GET /users/me/tenants` |
| `aihub_web/.../components/User/TenantSelector.vue` | **NEW** - Tenant dropdown component |
| `aihub_web/.../composables/user/useTenantSelector.ts` | **NEW** - Tenant queries and mutation |
| `aihub_web/.../components/User/Bar.vue` | Add TenantSelector to layout |
| `aihub_web/.../sdk/` | Regenerate SDK with `pnpm generate-sdk` |

---

### Phase 2: Pipeline Tenant-Aware Folders

**Purpose**: The OpenWebUI pipeline must fetch the user's active tenant from AI-Hub API and then place chats in tenant-named folders for organization.

**Reference**: See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 2: Folders/Projects](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#foldersprojects) and [Part 4: Approach 4 - Folders as Tenants](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#approach-4-folders-as-tenants).

#### 2.1 The Challenge

The pipeline runs server-side within OpenWebUI. It receives:
- The user's email (from OpenWebUI's auth context)
- The chat ID
- The message content

It does NOT have direct access to:
- The browser's state (URL params, localStorage)
- The tenant the user selected in the aihub_web frontend

**Solution**: The pipeline must call the AI-Hub API to fetch the user's active tenant.

#### 2.2 Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline pipe() method                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Receive message from user                                   │
│  2. Extract user email from __user__ context                    │
│  3. Call AI-Hub API: GET /users/me/tenant                       │
│     - Pass user email for identification                        │
│     - Receive: { tenant_id, tenant_name }                       │
│  4. Ensure tenant folder exists (create if not)                 │
│  5. Move chat to tenant folder (if not already)                 │
│  6. Add x-tenant-id header to all AI-Hub API calls              │
│  7. Process the message normally                                │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.3 Implementation

**File: `deployment/templates/openwebui_functions/aihub_pipeline.py`**

Add the following methods and modify the `pipe()` method:

```python
from open_webui.models.chats import Chats
from open_webui.models.folders import Folders, FolderForm

class Pipeline:
    # ... existing code ...

    async def get_user_active_tenant(self, user_email: str) -> dict:
        """
        Fetch the user's active tenant from AI-Hub API.

        This is the critical step that bridges the browser-side tenant
        selection with the server-side pipeline execution.

        Args:
            user_email: The user's email from OpenWebUI auth context

        Returns:
            dict with tenant_id and tenant_name
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.valves.AIHUB_API_URL}/users/me/tenant",
                headers={
                    "Authorization": f"Bearer {self.get_user_token(user_email)}",
                    # Note: We don't pass x-tenant-id here - we're ASKING what
                    # the tenant is, not assuming one
                },
            )
            response.raise_for_status()
            return response.json()

    def ensure_chat_in_tenant_folder(
        self,
        chat_id: str,
        user_id: str,
        tenant_name: str
    ) -> None:
        """
        Place the chat in a folder named after the tenant.

        This provides visual organization of chats by tenant in OpenWebUI.
        Note: This is organizational, not a security boundary.

        Uses OpenWebUI's internal APIs available within the pipeline context.
        See OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 2: OpenWebUI Internal APIs.

        Args:
            chat_id: The OpenWebUI chat ID
            user_id: The OpenWebUI user ID
            tenant_name: The tenant name to use as folder name
        """
        # Check if chat is already in a folder
        chat = Chats.get_chat_by_id(chat_id)
        if chat and chat.folder_id:
            return  # Already in a folder, don't move

        # Find or create the tenant folder
        folder = Folders.get_folder_by_parent_id_and_user_id_and_name(
            parent_id=None,  # Top-level folder
            user_id=user_id,
            name=tenant_name
        )

        if not folder:
            # Create the folder
            folder = Folders.insert_new_folder(
                user_id=user_id,
                form=FolderForm(name=tenant_name)
            )

        # Move chat to the tenant folder
        if folder:
            Chats.update_chat_folder_id_by_id_and_user_id(
                chat_id=chat_id,
                user_id=user_id,
                folder_id=folder.id
            )

    async def pipe(self, body: dict, __user__: dict, __event_emitter__) -> str:
        """
        Main pipeline entry point.

        Modified to:
        1. Fetch user's active tenant FIRST
        2. Organize chat into tenant folder
        3. Pass tenant context to all AI-Hub API calls
        """
        user_email = __user__.get("email")
        user_id = __user__.get("id")
        chat_id = body.get("chat_id")

        # STEP 1: Fetch user's active tenant from AI-Hub
        # This is the bridge between browser and server-side
        tenant_info = await self.get_user_active_tenant(user_email)
        tenant_id = tenant_info["tenant_id"]
        tenant_name = tenant_info["tenant_name"]

        # STEP 2: Organize chat into tenant folder
        if chat_id and user_id:
            self.ensure_chat_in_tenant_folder(chat_id, user_id, tenant_name)

        # STEP 3: Store tenant_id for use in subsequent API calls
        # All AI-Hub API calls should include x-tenant-id header
        self._current_tenant_id = tenant_id

        # ... rest of existing pipe() logic ...
        # When making API calls, include:
        # headers={"x-tenant-id": self._current_tenant_id}
```

#### 2.4 API Authentication for Pipeline

The pipeline needs to authenticate with AI-Hub API to fetch user tenant info. Options:

1. **Service Account**: Pipeline uses a dedicated service account token
2. **User Token Forwarding**: Pipeline forwards the user's OAuth token

For Phase 2, use a service account approach with an API key that has permission to read user tenant assignments.

#### 2.5 Files to Modify

| File | Change |
|------|--------|
| `deployment/.../aihub_pipeline.py` | Add `get_user_active_tenant()`, `ensure_chat_in_tenant_folder()`, modify `pipe()` |

---

### Phase 3: OpenWebUI Infrastructure Client

**Purpose**: Create a reusable client for programmatic interaction with OpenWebUI's API and SCIM endpoints. This is the foundation for all subsequent synchronization work.

**Reference**:
- See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 2: SCIM 2.0 API](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#scim-20-api) for SCIM endpoint documentation
- Follow the pattern established in `aihub_lib/aihub_lib/infrastructure/litellm/` for Settings + Service structure

#### 3.1 Obtaining OpenWebUI API Tokens

Before implementing the client, you need to obtain the necessary API tokens from OpenWebUI:

**API Key (for general API access)**:
1. Log into OpenWebUI as an admin user
2. Navigate to Settings → Account → API Keys
3. Generate a new API key with a descriptive name (e.g., "aihub-sync-service")
4. Copy and securely store the key

**SCIM Token (for user/group management)**:
1. OpenWebUI must be configured with SCIM enabled:
   ```env
   SCIM_ENABLED=true
   SCIM_TOKEN=<generate-a-secure-random-string>
   ```
2. The SCIM token is set in OpenWebUI's environment configuration
3. For AI-Hub, we'll use the same token value in our settings

**Important**: Both tokens should be treated as secrets and never committed to version control.

#### 3.2 Docker Compose Configuration

**File: `deployment/templates/docker-compose.yml.j2`**

Add the OpenWebUI integration environment variables to the `aihub_api` service:

```yaml
services:
  aihub_api:
    # ... existing configuration ...
    environment:
      # ... existing env vars ...

      # OpenWebUI Integration (Phase 3+)
      OPEN_WEBUI_BASE_URL: "http://open_webui:8080"  # Internal Docker network URL
      OPEN_WEBUI_API_KEY: "${OPEN_WEBUI_API_KEY}"    # From .env file
      OPEN_WEBUI_SCIM_TOKEN: "${OPEN_WEBUI_SCIM_TOKEN}"  # From .env file
```

**File: `.env.dev` and `.env.prod`**

Add the required environment variables:

```env
# OpenWebUI Integration
OPEN_WEBUI_API_KEY=your-api-key-here
OPEN_WEBUI_SCIM_TOKEN=your-scim-token-here
```

**File: `deployment/templates/docker-compose.yml.j2`** (OpenWebUI service)

Ensure OpenWebUI has SCIM enabled:

```yaml
services:
  open_webui:
    # ... existing configuration ...
    environment:
      # ... existing env vars ...

      # Enable SCIM for programmatic user/group management
      SCIM_ENABLED: "true"
      SCIM_TOKEN: "${OPEN_WEBUI_SCIM_TOKEN}"
```

#### 3.3 Settings Class

**New File: `aihub_lib/aihub_lib/infrastructure/open_webui/OpenWebuiSettings.py`**

This class follows the pattern established by `LiteLLMProxySettings`:

```python
"""
OpenWebUI connection settings.

Provides configuration for connecting to OpenWebUI's REST API and SCIM endpoints.
Used by OpenWebuiService for group management, model registration, and user sync.

See OPEN_WEBUI_MULTITENANCY_CONCEPT.md for the full integration design.
"""
import httpx
from pydantic import SecretStr

from aihub_lib.settings import EnvironmentSettings


class OpenWebuiSettings(EnvironmentSettings):
    """
    Settings for OpenWebUI API and SCIM integration.

    Environment variables are prefixed with OPEN_WEBUI_:
    - OPEN_WEBUI_BASE_URL: Base URL of OpenWebUI instance
    - OPEN_WEBUI_API_KEY: API key for general API access
    - OPEN_WEBUI_SCIM_TOKEN: Token for SCIM operations (defaults to API_KEY)

    Example .env:
        OPEN_WEBUI_BASE_URL=http://localhost:8080
        OPEN_WEBUI_API_KEY=sk-abc123...
        OPEN_WEBUI_SCIM_TOKEN=scim-token-xyz...
    """

    model_config = EnvironmentSettings.create_settings_config("OPEN_WEBUI_")

    BASE_URL: str
    """Base URL of the OpenWebUI instance (e.g., http://localhost:8080)"""

    API_KEY: SecretStr
    """API key for authenticating with OpenWebUI's REST API"""

    SCIM_TOKEN: SecretStr | None = None
    """
    Token for SCIM 2.0 operations. If not provided, falls back to API_KEY.
    SCIM is used for programmatic group and user management.
    See: https://docs.openwebui.com/features/auth/scim
    """

    @property
    def api_headers(self) -> dict[str, str]:
        """Headers for standard API requests."""
        return {
            "Authorization": f"Bearer {self.API_KEY.get_secret_value()}",
            "Content-Type": "application/json",
        }

    @property
    def scim_headers(self) -> dict[str, str]:
        """Headers for SCIM API requests."""
        token = self.SCIM_TOKEN or self.API_KEY
        return {
            "Authorization": f"Bearer {token.get_secret_value()}",
            "Content-Type": "application/scim+json",
        }

    @property
    def httpx_aclient(self) -> httpx.AsyncClient:
        """
        Async HTTP client configured for OpenWebUI API.

        Usage:
            async with settings.httpx_aclient as client:
                response = await client.get("/api/v1/models")
        """
        return httpx.AsyncClient(
            headers=self.api_headers,
            base_url=self.BASE_URL,
            timeout=30.0,
        )

    @property
    def scim_aclient(self) -> httpx.AsyncClient:
        """
        Async HTTP client configured for OpenWebUI SCIM API.

        SCIM endpoints are at /api/v1/scim/v2/
        See OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 2: SCIM 2.0 API

        Usage:
            async with settings.scim_aclient as client:
                response = await client.get("/Groups")
        """
        return httpx.AsyncClient(
            headers=self.scim_headers,
            base_url=f"{self.BASE_URL}/api/v1/scim/v2",
            timeout=30.0,
        )
```

#### 3.4 Service Class

**New File: `aihub_lib/aihub_lib/infrastructure/open_webui/OpenWebuiService.py`**

This class provides static methods for all OpenWebUI interactions:

```python
"""
OpenWebUI API and SCIM service.

Provides methods for:
- SCIM Group CRUD operations
- User group membership management
- Workspace model CRUD operations
- Model ACL management

All methods are static and take an httpx.AsyncClient as their first argument,
following the pattern established by LiteLLMService.

See OPEN_WEBUI_MULTITENANCY_CONCEPT.md for the full integration design.
"""
import httpx
from typing import Any


class OpenWebuiService:
    """
    Service for interacting with OpenWebUI via API and SCIM.

    All methods are static to allow for flexible client injection.
    Use OpenWebuiSettings to create appropriately configured clients.

    Example:
        settings = OpenWebuiSettings()
        async with settings.scim_aclient as client:
            groups = await OpenWebuiService.list_groups(client)
    """

    # =========================================================================
    # SCIM Group Operations
    # See: https://docs.openwebui.com/features/auth/scim
    # =========================================================================

    @staticmethod
    async def list_groups(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """
        List all groups in OpenWebUI.

        Returns SCIM ListResponse with Resources array containing groups.
        Each group has: id, displayName, members, meta, externalId
        """
        response = await client.get("/Groups")
        response.raise_for_status()
        data = response.json()
        return data.get("Resources", [])

    @staticmethod
    async def get_group(client: httpx.AsyncClient, group_id: str) -> dict[str, Any]:
        """Get a specific group by ID."""
        response = await client.get(f"/Groups/{group_id}")
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def get_group_by_display_name(
        client: httpx.AsyncClient,
        display_name: str
    ) -> dict[str, Any] | None:
        """
        Find a group by its display name.

        SCIM filter: displayName eq "value"
        Returns None if not found.
        """
        # SCIM filter syntax
        filter_param = f'displayName eq "{display_name}"'
        response = await client.get("/Groups", params={"filter": filter_param})
        response.raise_for_status()
        data = response.json()
        resources = data.get("Resources", [])
        return resources[0] if resources else None

    @staticmethod
    async def create_group(
        client: httpx.AsyncClient,
        display_name: str,
        external_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new group.

        Args:
            display_name: Human-readable group name (e.g., "acme__AIHubAdmin")
            external_id: Optional external identifier for sync tracking

        Returns:
            Created group object with assigned id
        """
        payload = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "displayName": display_name,
        }
        if external_id:
            payload["externalId"] = external_id

        response = await client.post("/Groups", json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def update_group_members(
        client: httpx.AsyncClient,
        group_id: str,
        member_ids: list[str],
    ) -> dict[str, Any]:
        """
        Replace the entire member list of a group.

        Uses SCIM PUT (full replacement) semantics.

        Args:
            group_id: The OpenWebUI group ID
            member_ids: List of OpenWebUI user IDs to set as members
        """
        # First get current group to preserve other fields
        current = await OpenWebuiService.get_group(client, group_id)

        # Update members
        current["members"] = [
            {"value": uid, "type": "User"} for uid in member_ids
        ]

        response = await client.put(f"/Groups/{group_id}", json=current)
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def delete_group(client: httpx.AsyncClient, group_id: str) -> bool:
        """Delete a group. Returns True if successful."""
        response = await client.delete(f"/Groups/{group_id}")
        return response.status_code == 204

    # =========================================================================
    # User Operations
    # =========================================================================

    @staticmethod
    async def get_user_by_email(
        client: httpx.AsyncClient,
        email: str
    ) -> dict[str, Any] | None:
        """
        Find a user by email address.

        This is how we map AI-Hub users to OpenWebUI users.
        See OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 6: User ID Mapping
        """
        filter_param = f'userName eq "{email}"'
        response = await client.get("/Users", params={"filter": filter_param})
        response.raise_for_status()
        data = response.json()
        resources = data.get("Resources", [])
        return resources[0] if resources else None

    @staticmethod
    async def set_user_groups(
        client: httpx.AsyncClient,
        user_id: str,
        group_ids: list[str],
    ) -> None:
        """
        Set the user's group memberships.

        This removes the user from all current groups and adds them
        to the specified groups. Used when user switches tenant.

        Note: This is a destructive operation - the user will ONLY
        be in the specified groups after this call.
        """
        # Get all groups
        all_groups = await OpenWebuiService.list_groups(client)

        for group in all_groups:
            group_id = group["id"]
            current_members = [m["value"] for m in group.get("members", [])]

            should_be_member = group_id in group_ids
            is_member = user_id in current_members

            if should_be_member and not is_member:
                # Add user to group
                new_members = current_members + [user_id]
                await OpenWebuiService.update_group_members(client, group_id, new_members)
            elif not should_be_member and is_member:
                # Remove user from group
                new_members = [m for m in current_members if m != user_id]
                await OpenWebuiService.update_group_members(client, group_id, new_members)

    # =========================================================================
    # Model Operations
    # See: https://docs.openwebui.com/features/workspace/models
    # =========================================================================

    @staticmethod
    async def list_models(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """List all workspace models."""
        response = await client.get("/api/v1/models")
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def create_model(
        client: httpx.AsyncClient,
        model_id: str,
        name: str,
        base_model_id: str,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a workspace model.

        Used to register AI-Hub agents as OpenWebUI models.

        Args:
            model_id: Unique identifier (e.g., "aihub-assistant-123")
            name: Display name
            base_model_id: The underlying model/pipeline ID
            meta: Arbitrary metadata (store agent_class, agent_id here)
        """
        payload = {
            "id": model_id,
            "name": name,
            "base_model_id": base_model_id,
            "meta": meta or {},
        }
        response = await client.post("/api/v1/models/create", json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def update_model_acl(
        client: httpx.AsyncClient,
        model_id: str,
        read_group_ids: list[str],
        write_group_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Update a model's access control list.

        See OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 2: Workspace Models
        for the ACL structure.

        Args:
            model_id: The model to update
            read_group_ids: Groups that can see/use this model
            write_group_ids: Groups that can edit this model (defaults to empty)
        """
        payload = {
            "access_control": {
                "read": {
                    "group_ids": read_group_ids,
                    "user_ids": [],
                },
                "write": {
                    "group_ids": write_group_ids or [],
                    "user_ids": [],
                },
            }
        }
        response = await client.post(
            f"/api/v1/models/{model_id}/update",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    async def delete_model(client: httpx.AsyncClient, model_id: str) -> bool:
        """Delete a workspace model. Returns True if successful."""
        response = await client.delete(f"/api/v1/models/{model_id}/delete")
        return response.status_code == 200
```

#### 3.5 Package Init

**New File: `aihub_lib/aihub_lib/infrastructure/open_webui/__init__.py`**

```python
"""
OpenWebUI integration infrastructure.

Provides clients for interacting with OpenWebUI's API and SCIM endpoints
for multi-tenancy synchronization.

See OPEN_WEBUI_MULTITENANCY_CONCEPT.md for the full integration design.
"""
from aihub_lib.infrastructure.open_webui.OpenWebuiSettings import OpenWebuiSettings
from aihub_lib.infrastructure.open_webui.OpenWebuiService import OpenWebuiService

__all__ = ["OpenWebuiSettings", "OpenWebuiService"]
```

#### 3.6 Files to Create

| File | Purpose |
|------|---------|
| `aihub_lib/.../infrastructure/open_webui/__init__.py` | Package exports |
| `aihub_lib/.../infrastructure/open_webui/OpenWebuiSettings.py` | Connection settings |
| `aihub_lib/.../infrastructure/open_webui/OpenWebuiService.py` | API/SCIM methods |
| `deployment/templates/docker-compose.yml.j2` | Add environment variables |
| `.env.dev`, `.env.prod` | Add token placeholders |

---

### Phase 4: Group Synchronization

**Purpose**: Create and manage the mapping between AI-Hub (tenant, role) tuples and OpenWebUI groups. This is the core of the multi-tenancy integration.

**Reference**: See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 5: Sync Considerations](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#part-5-sync-considerations) for the detailed sync logic.

#### 4.1 Understanding the Group Model

Each AI-Hub (tenant, role) combination maps to exactly one OpenWebUI group:

```
AI-Hub                                    OpenWebUI
┌─────────────┐                          ┌──────────────────────┐
│ Tenant: acme│                          │ Group: acme__Admin   │
│ Role: Admin │  ────────────────────►   │ Group: acme__Viewer  │
│ Role: Viewer│                          └──────────────────────┘
└─────────────┘

┌─────────────┐                          ┌──────────────────────┐
│ Tenant: beta│                          │ Group: beta__Admin   │
│ Role: Admin │  ────────────────────►   │ Group: beta__ReadOnly│
│ Role: ReadOnly                         └──────────────────────┘
└─────────────┘
```

The group name uses double underscore (`__`) as delimiter because:
- Tenant IDs may contain single underscores
- Role names may contain single underscores
- Double underscore is unlikely to appear in either

#### 4.2 Group Sync Service

**New File: `aihub_lib/aihub_lib/infrastructure/open_webui/OpenWebuiGroupSyncService.py`**

```python
"""
OpenWebUI Group Synchronization Service.

Manages the mapping between AI-Hub (tenant, role) tuples and OpenWebUI groups.
This is the core component that bridges AI-Hub's two-stage access control
with OpenWebUI's group-based RBAC.

See OPEN_WEBUI_MULTITENANCY_CONCEPT.md for the full design.

Key responsibilities:
1. Ensure all (tenant, role) groups exist in OpenWebUI
2. Update user group memberships when they switch tenants
3. Trigger ACL recomputation when access rules change

Usage:
    sync_service = OpenWebuiGroupSyncService(settings)

    # On startup: ensure all groups exist
    await sync_service.ensure_all_groups_exist()

    # On tenant switch: update user's groups
    await sync_service.set_user_groups_for_tenant(user_email, tenant_id)
"""
import logging
from typing import TYPE_CHECKING

from aihub_lib.infrastructure.open_webui.OpenWebuiSettings import OpenWebuiSettings
from aihub_lib.infrastructure.open_webui.OpenWebuiService import OpenWebuiService
from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class OpenWebuiGroupSyncService:
    """
    Synchronizes AI-Hub tenant-role access to OpenWebUI groups.

    This service implements the "Composite Group Mapping" approach
    described in OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 4.

    Each (tenant_id, role_name) tuple maps to one OpenWebUI group
    with the naming convention: "{tenant_id}__{role_name}"
    """

    GROUP_NAME_DELIMITER = "__"
    """
    Delimiter between tenant_id and role_name in group names.
    Using double underscore to avoid conflicts with single underscores
    that may appear in tenant IDs or role names.
    """

    def __init__(self, settings: OpenWebuiSettings):
        """
        Initialize the sync service.

        Args:
            settings: OpenWebUI connection settings with SCIM credentials
        """
        self.settings = settings

    def group_name(self, tenant_id: str, role_name: str) -> str:
        """
        Generate the OpenWebUI group name for a (tenant, role) tuple.

        Examples:
            group_name("acme", "AIHubAdmin") → "acme__AIHubAdmin"
            group_name("beta-corp", "Agent Viewer") → "beta-corp__Agent Viewer"
        """
        return f"{tenant_id}{self.GROUP_NAME_DELIMITER}{role_name}"

    def parse_group_name(self, group_name: str) -> tuple[str, str] | None:
        """
        Parse a group name back into (tenant_id, role_name).

        Returns None if the group name doesn't follow our naming convention.
        """
        if self.GROUP_NAME_DELIMITER not in group_name:
            return None
        parts = group_name.split(self.GROUP_NAME_DELIMITER, 1)
        if len(parts) != 2:
            return None
        return (parts[0], parts[1])

    async def ensure_all_groups_exist(self) -> dict[str, str]:
        """
        Create OpenWebUI groups for all (tenant, role) combinations.

        This should be called:
        - On system startup
        - After creating a new tenant
        - After creating a new role

        Returns:
            dict mapping group_name → group_id for all created/existing groups
        """
        logger.info("Ensuring all tenant-role groups exist in OpenWebUI")

        async with self.settings.scim_aclient as client:
            # Get existing groups
            existing_groups = await OpenWebuiService.list_groups(client)
            existing_by_name = {g["displayName"]: g["id"] for g in existing_groups}

            result = {}

            # Get all tenants
            tenants = TenantEntity.objects.all()

            for tenant in tenants:
                # Get all roles (system-wide + tenant-specific)
                system_roles = RoleEntity.objects(tenant_id=None)
                tenant_roles = RoleEntity.objects(tenant_id=tenant.id)
                all_roles = list(system_roles) + list(tenant_roles)

                for role in all_roles:
                    group_name = self.group_name(tenant.id, role.name)

                    if group_name in existing_by_name:
                        # Group already exists
                        result[group_name] = existing_by_name[group_name]
                        logger.debug(f"Group already exists: {group_name}")
                    else:
                        # Create new group
                        logger.info(f"Creating group: {group_name}")
                        group = await OpenWebuiService.create_group(
                            client,
                            display_name=group_name,
                            external_id=f"aihub:{tenant.id}:{role.name}",
                        )
                        result[group_name] = group["id"]

            logger.info(f"Group sync complete. Total groups: {len(result)}")
            return result

    async def set_user_groups_for_tenant(
        self,
        user_email: str,
        tenant_id: str
    ) -> list[str]:
        """
        Set the user's OpenWebUI groups based on their roles in a tenant.

        This is called when a user switches their active tenant.
        The user will be:
        - REMOVED from all current groups (including other tenant groups)
        - ADDED to groups for their roles in the specified tenant

        This ensures users only see models for their currently active tenant.

        Args:
            user_email: The user's email (used to find them in OpenWebUI)
            tenant_id: The tenant they're switching to

        Returns:
            List of group names the user is now a member of

        Raises:
            ValueError: If user doesn't exist in OpenWebUI
            ValueError: If user has no roles in the specified tenant
        """
        logger.info(f"Setting groups for user {user_email} in tenant {tenant_id}")

        async with self.settings.scim_aclient as client:
            # Find the user in OpenWebUI
            owui_user = await OpenWebuiService.get_user_by_email(client, user_email)
            if not owui_user:
                raise ValueError(f"User not found in OpenWebUI: {user_email}")

            owui_user_id = owui_user["id"]

            # Get user's roles in the tenant from AI-Hub
            user_tenant_role = UserTenantRoleEntity.by_user_and_tenant(
                # Note: We need the AI-Hub user ID, not email
                # This may require a lookup - see Phase 6 for user ID mapping
                user_id="...",  # TODO: Map email to AI-Hub user ID
                tenant_id=tenant_id
            )

            if not user_tenant_role or not user_tenant_role.roles:
                raise ValueError(f"User has no roles in tenant {tenant_id}")

            # Build list of target groups
            target_group_names = [
                self.group_name(tenant_id, role_name)
                for role_name in user_tenant_role.roles
            ]

            # Get existing groups to find their IDs
            existing_groups = await OpenWebuiService.list_groups(client)
            name_to_id = {g["displayName"]: g["id"] for g in existing_groups}

            target_group_ids = []
            for group_name in target_group_names:
                if group_name not in name_to_id:
                    # Group doesn't exist - this shouldn't happen if sync is working
                    logger.warning(f"Group not found, creating: {group_name}")
                    group = await OpenWebuiService.create_group(
                        client,
                        display_name=group_name
                    )
                    target_group_ids.append(group["id"])
                else:
                    target_group_ids.append(name_to_id[group_name])

            # Update user's group memberships
            await OpenWebuiService.set_user_groups(
                client,
                owui_user_id,
                target_group_ids
            )

            logger.info(f"User {user_email} now in groups: {target_group_names}")
            return target_group_names

    async def delete_groups_for_tenant(self, tenant_id: str) -> int:
        """
        Delete all OpenWebUI groups associated with a tenant.

        Called when a tenant is deleted.

        Args:
            tenant_id: The tenant being deleted

        Returns:
            Number of groups deleted
        """
        logger.info(f"Deleting groups for tenant: {tenant_id}")

        async with self.settings.scim_aclient as client:
            existing_groups = await OpenWebuiService.list_groups(client)
            deleted = 0

            for group in existing_groups:
                parsed = self.parse_group_name(group["displayName"])
                if parsed and parsed[0] == tenant_id:
                    await OpenWebuiService.delete_group(client, group["id"])
                    logger.info(f"Deleted group: {group['displayName']}")
                    deleted += 1

            return deleted

    async def delete_groups_for_role(self, role_name: str) -> int:
        """
        Delete all OpenWebUI groups associated with a role.

        Called when a role is deleted.

        Args:
            role_name: The role being deleted

        Returns:
            Number of groups deleted
        """
        logger.info(f"Deleting groups for role: {role_name}")

        async with self.settings.scim_aclient as client:
            existing_groups = await OpenWebuiService.list_groups(client)
            deleted = 0

            for group in existing_groups:
                parsed = self.parse_group_name(group["displayName"])
                if parsed and parsed[1] == role_name:
                    await OpenWebuiService.delete_group(client, group["id"])
                    logger.info(f"Deleted group: {group['displayName']}")
                    deleted += 1

            return deleted
```

#### 4.3 Integration Points

The group sync service needs to be called from several places:

**1. On User Tenant Switch (Phase 1 endpoint)**

Modify the `PUT /users/me/tenant` endpoint to also sync OpenWebUI groups:

```python
# In UserController.py
@router.put("/users/me/tenant")
async def set_active_tenant(
    user: Annotated[UserIdentity, Security(auth_handler)],
    body: SetActiveTenantRequest,
    owui_settings: Annotated[OpenWebuiSettings, Depends(get_owui_settings)],
) -> TenantResponse:
    # ... existing validation ...

    # Update user's active tenant
    user_entity.active_tenant_id = body.tenant_id
    user_entity.save()

    # Sync OpenWebUI groups
    sync_service = OpenWebuiGroupSyncService(owui_settings)
    await sync_service.set_user_groups_for_tenant(user.email, body.tenant_id)

    return TenantResponse.from_entity(tenant)
```

**2. On System Startup**

Create a startup task that ensures all groups exist:

```python
# In aihub_api startup
@app.on_event("startup")
async def ensure_owui_groups():
    settings = OpenWebuiSettings()
    sync_service = OpenWebuiGroupSyncService(settings)
    await sync_service.ensure_all_groups_exist()
```

**3. On Role/Tenant Changes**

Add hooks in the admin APIs (covered in Phase 6).

#### 4.4 Files to Create/Modify

| File | Change |
|------|--------|
| `aihub_lib/.../infrastructure/open_webui/OpenWebuiGroupSyncService.py` | **NEW** - Core sync logic |
| `aihub_lib/.../infrastructure/open_webui/__init__.py` | Export new class |
| `aihub_api/.../routes/user/UserController.py` | Call sync on tenant switch |
| `aihub_api/aihub_api/main.py` | Add startup task for group sync |

---

### Phase 5: Model Registration & ACL Sync

**Purpose**: Register AI-Hub agents as OpenWebUI workspace models and compute their ACLs based on the composite group model.

**Reference**: See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 4: Approach 2 - Register Agents as Workspace Models](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#approach-2-register-agents-as-workspace-models) and [Part 5: ACL Computation Logic](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#acl-computation-logic).

#### 5.1 Why Workspace Models?

The current pipeline uses `pipes()` to dynamically return available agents. However, these dynamic "models" have a critical limitation: **they don't support ACLs**. See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 3: Agent Discovery Challenge](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#agent-discovery-challenge).

By registering agents as **workspace models**, we can:
- Set persistent ACLs that OpenWebUI enforces
- Control which groups (tenant×role) can see each agent
- Have native RBAC without pipeline code involvement

#### 5.2 ACL Computation Algorithm

For each agent, we need to determine which groups should have access:

```
Input: Agent A with access rule requirement (e.g., aihub.user.agent.assistant.*)

For each Tenant T:
    tenant_allows = AccessChecker.check(T.access_rules, agent_access_rule)
    IF NOT tenant_allows:
        CONTINUE  # Skip this tenant entirely

    For each Role R (system roles + T's tenant-specific roles):
        role_allows = AccessChecker.check(R.access_rules, agent_access_rule)
        IF role_allows:
            # Both tenant AND role allow → add group to ACL
            group_name = f"{T.id}__{R.name}"
            ADD group_name to agent's read ACL

Output: List of group names that should have read access to agent A
```

#### 5.3 Model Sync Service Extension

**Add to `OpenWebuiGroupSyncService.py`:**

```python
# Additional imports
from aihub_lib.auth.access.AccessChecker import AccessChecker


class OpenWebuiGroupSyncService:
    # ... existing code ...

    def compute_agent_acl(
        self,
        agent_class: str,
        agent_id: str
    ) -> list[str]:
        """
        Compute which groups should have access to an agent.

        This implements the two-stage access check:
        1. Tenant must allow the agent (tenant as permission ceiling)
        2. Role must allow the agent (role grants specific permissions)

        Only groups where BOTH tenant AND role allow access are included.

        Args:
            agent_class: The agent's class (e.g., "assistant")
            agent_id: The agent's ID

        Returns:
            List of group names (e.g., ["acme__AIHubAdmin", "acme__Viewer"])
        """
        allowed_groups = []

        # Get all tenants
        tenants = TenantEntity.objects.all()

        for tenant in tenants:
            # Check if tenant allows this agent
            tenant_checker = AccessChecker(tenant.access_rules)
            if not tenant_checker.has_access_to_agent(agent_class, agent_id):
                # Tenant doesn't allow - skip all roles in this tenant
                continue

            # Tenant allows - check each role
            system_roles = RoleEntity.objects(tenant_id=None)
            tenant_roles = RoleEntity.objects(tenant_id=tenant.id)

            for role in list(system_roles) + list(tenant_roles):
                role_checker = AccessChecker(role.access_rules)
                if role_checker.has_access_to_agent(agent_class, agent_id):
                    # Both tenant AND role allow → add group
                    group_name = self.group_name(tenant.id, role.name)
                    allowed_groups.append(group_name)

        return allowed_groups

    async def register_agent_as_model(
        self,
        agent_class: str,
        agent_id: str,
        agent_name: str,
        pipeline_id: str,
    ) -> dict:
        """
        Register an AI-Hub agent as an OpenWebUI workspace model.

        The model is created with:
        - Unique ID: f"aihub-{agent_class}-{agent_id}"
        - Metadata linking back to the AI-Hub agent
        - ACLs computed from the two-stage access check

        Args:
            agent_class: Agent class (e.g., "assistant")
            agent_id: Agent ID (e.g., "support-bot")
            agent_name: Display name for the model
            pipeline_id: The OpenWebUI pipeline that handles this agent

        Returns:
            The created model object
        """
        model_id = f"aihub-{agent_class}-{agent_id}"

        async with self.settings.httpx_aclient as client:
            # Check if model already exists
            existing_models = await OpenWebuiService.list_models(client)
            existing = next((m for m in existing_models if m["id"] == model_id), None)

            if not existing:
                # Create the model
                model = await OpenWebuiService.create_model(
                    client,
                    model_id=model_id,
                    name=agent_name,
                    base_model_id=pipeline_id,
                    meta={
                        "agent_class": agent_class,
                        "agent_id": agent_id,
                        "source": "aihub",
                    },
                )
            else:
                model = existing

            # Compute and set ACLs
            allowed_groups = self.compute_agent_acl(agent_class, agent_id)

            # Get group IDs from names
            async with self.settings.scim_aclient as scim_client:
                all_groups = await OpenWebuiService.list_groups(scim_client)
                name_to_id = {g["displayName"]: g["id"] for g in all_groups}

                group_ids = [
                    name_to_id[name]
                    for name in allowed_groups
                    if name in name_to_id
                ]

            # Update ACL
            await OpenWebuiService.update_model_acl(
                client,
                model_id=model_id,
                read_group_ids=group_ids,
            )

            logger.info(
                f"Registered agent {agent_class}/{agent_id} as model {model_id} "
                f"with {len(group_ids)} groups"
            )

            return model

    async def sync_agent_acls(self, agent_class: str, agent_id: str) -> None:
        """
        Recompute and update ACLs for an existing agent model.

        Called when:
        - Tenant access_rules are modified
        - Role access_rules are modified
        - New roles are created
        """
        model_id = f"aihub-{agent_class}-{agent_id}"
        allowed_groups = self.compute_agent_acl(agent_class, agent_id)

        async with self.settings.scim_aclient as scim_client:
            all_groups = await OpenWebuiService.list_groups(scim_client)
            name_to_id = {g["displayName"]: g["id"] for g in all_groups}

            group_ids = [
                name_to_id[name]
                for name in allowed_groups
                if name in name_to_id
            ]

        async with self.settings.httpx_aclient as client:
            await OpenWebuiService.update_model_acl(
                client,
                model_id=model_id,
                read_group_ids=group_ids,
            )

        logger.info(f"Updated ACLs for {model_id}: {len(group_ids)} groups")

    async def sync_all_agent_acls(self) -> int:
        """
        Recompute ACLs for ALL registered agent models.

        Called on startup or after bulk changes to access rules.

        Returns:
            Number of models updated
        """
        async with self.settings.httpx_aclient as client:
            models = await OpenWebuiService.list_models(client)

            updated = 0
            for model in models:
                meta = model.get("meta", {})
                if meta.get("source") == "aihub":
                    agent_class = meta.get("agent_class")
                    agent_id = meta.get("agent_id")
                    if agent_class and agent_id:
                        await self.sync_agent_acls(agent_class, agent_id)
                        updated += 1

            logger.info(f"Synced ACLs for {updated} agent models")
            return updated

    async def unregister_agent(self, agent_class: str, agent_id: str) -> bool:
        """
        Remove an agent's workspace model.

        Called when an agent goes offline or is deleted.
        """
        model_id = f"aihub-{agent_class}-{agent_id}"

        async with self.settings.httpx_aclient as client:
            return await OpenWebuiService.delete_model(client, model_id)
```

#### 5.4 Integration with Agent Lifecycle

The agent registration needs to be triggered when agents come online/offline:

**Option A: Synchronous (simpler, Phase 5)**
- In the agent discovery endpoint, register/unregister models
- Pros: Simple, immediate
- Cons: Adds latency to agent operations

**Option B: Event-driven (production, Phase 6)**
- Publish events when agents change state
- Background worker processes events and syncs models
- Pros: Non-blocking, scalable
- Cons: More complex, eventual consistency

For Phase 5, use Option A (synchronous).

#### 5.5 Files to Modify

| File | Change |
|------|--------|
| `aihub_lib/.../infrastructure/open_webui/OpenWebuiGroupSyncService.py` | Add ACL computation and model registration |
| Agent discovery service | Call register/unregister on agent state changes |

---

### Phase 6: Event-Driven Sync (Production)

**Purpose**: Move from synchronous sync calls to an event-driven architecture for production scalability.

**Reference**: See [OPEN_WEBUI_MULTITENANCY_CONCEPT.md Part 5: Events Requiring Sync](./OPEN_WEBUI_MULTITENANCY_CONCEPT.md#events-requiring-sync) for the complete event list.

#### 6.1 Why Event-Driven?

Synchronous sync has limitations:
- Adds latency to every operation that affects permissions
- If OpenWebUI is temporarily unavailable, the operation fails
- Doesn't scale well with many tenants/roles/agents

Event-driven approach:
- Operations complete immediately
- Background worker processes events
- Retry logic for transient failures
- Better observability (events are logged)

#### 6.2 Events to Publish

| Source | Event | Payload | Action |
|--------|-------|---------|--------|
| TenantController | `tenant.access_rules.updated` | `{tenant_id, old_rules, new_rules}` | Recompute all agent ACLs for tenant |
| TenantController | `tenant.created` | `{tenant_id}` | Create groups for all roles |
| TenantController | `tenant.deleted` | `{tenant_id}` | Delete all groups for tenant |
| RoleController | `role.access_rules.updated` | `{role_id, tenant_id, old_rules, new_rules}` | Recompute all agent ACLs for role |
| RoleController | `role.created` | `{role_id, role_name, tenant_id}` | Create groups for role in all tenants |
| RoleController | `role.deleted` | `{role_id, role_name, tenant_id}` | Delete groups, recompute ACLs |
| UserController | `user.tenant.switched` | `{user_id, user_email, tenant_id}` | Update user's OpenWebUI groups |
| AgentService | `agent.online` | `{agent_class, agent_id, agent_name}` | Register as workspace model |
| AgentService | `agent.offline` | `{agent_class, agent_id}` | Optionally remove model |

#### 6.3 Event Definitions

**New File: `aihub_lib/aihub_lib/nats/events/open_webui/`**

Create NATS events following the existing event hierarchy:

```python
# OpenWebuiSyncEvent.py
from aihub_lib.nats.events import ControlEvent


class TenantAccessRulesUpdatedEvent(ControlEvent):
    """Triggered when a tenant's access_rules are modified."""
    tenant_id: str
    old_rules: list[str]
    new_rules: list[str]


class RoleAccessRulesUpdatedEvent(ControlEvent):
    """Triggered when a role's access_rules are modified."""
    role_id: str
    role_name: str
    tenant_id: str | None  # None for system roles
    old_rules: list[str]
    new_rules: list[str]


class UserTenantSwitchedEvent(ControlEvent):
    """Triggered when a user switches their active tenant."""
    user_id: str
    user_email: str
    new_tenant_id: str


class AgentStateChangedEvent(ControlEvent):
    """Triggered when an agent comes online or goes offline."""
    agent_class: str
    agent_id: str
    agent_name: str
    is_online: bool
```

#### 6.4 Event Subscriber (Background Worker)

**New File: `aihub_lib/aihub_lib/infrastructure/open_webui/OpenWebuiSyncWorker.py`**

```python
"""
Background worker that processes OpenWebUI sync events.

Subscribes to NATS events and triggers appropriate sync operations.
"""
import logging
from aihub_lib.nats.subscribers import BaseSubscriber
from aihub_lib.infrastructure.open_webui import OpenWebuiSettings, OpenWebuiGroupSyncService

logger = logging.getLogger(__name__)


class OpenWebuiSyncWorker(BaseSubscriber):
    """
    NATS subscriber that handles OpenWebUI synchronization events.

    Processes:
    - Tenant/role access rule changes → ACL recomputation
    - User tenant switches → group membership updates
    - Agent state changes → model registration/removal
    """

    def __init__(self):
        self.settings = OpenWebuiSettings()
        self.sync_service = OpenWebuiGroupSyncService(self.settings)

    async def on_tenant_access_rules_updated(self, event: TenantAccessRulesUpdatedEvent):
        """Recompute ACLs for all agents when tenant rules change."""
        logger.info(f"Tenant {event.tenant_id} access rules updated, recomputing ACLs")
        await self.sync_service.sync_all_agent_acls()

    async def on_role_access_rules_updated(self, event: RoleAccessRulesUpdatedEvent):
        """Recompute ACLs for all agents when role rules change."""
        logger.info(f"Role {event.role_name} access rules updated, recomputing ACLs")
        await self.sync_service.sync_all_agent_acls()

    async def on_user_tenant_switched(self, event: UserTenantSwitchedEvent):
        """Update user's OpenWebUI groups when they switch tenants."""
        logger.info(f"User {event.user_email} switched to tenant {event.new_tenant_id}")
        await self.sync_service.set_user_groups_for_tenant(
            event.user_email,
            event.new_tenant_id
        )

    async def on_agent_state_changed(self, event: AgentStateChangedEvent):
        """Register/unregister agent as workspace model."""
        if event.is_online:
            logger.info(f"Agent {event.agent_class}/{event.agent_id} online, registering")
            await self.sync_service.register_agent_as_model(
                event.agent_class,
                event.agent_id,
                event.agent_name,
                pipeline_id="aihub-pipeline",  # Configure appropriately
            )
        else:
            logger.info(f"Agent {event.agent_class}/{event.agent_id} offline")
            # Optionally: await self.sync_service.unregister_agent(...)
```

#### 6.5 Event Publishing

Modify the controllers to publish events instead of calling sync directly:

```python
# In TenantController.py
@router.put("/tenants/{tenant_id}/access-rules")
async def update_tenant_access_rules(
    tenant_id: str,
    body: UpdateAccessRulesRequest,
    event_publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
):
    tenant = TenantEntity.by_id(tenant_id)
    old_rules = tenant.access_rules

    # Update rules
    tenant.access_rules = body.access_rules
    tenant.save()

    # Publish event (async processing by worker)
    await event_publisher.publish(TenantAccessRulesUpdatedEvent(
        tenant_id=tenant_id,
        old_rules=old_rules,
        new_rules=body.access_rules,
    ))

    return TenantResponse.from_entity(tenant)
```

#### 6.6 Files to Create/Modify

| File | Change |
|------|--------|
| `aihub_lib/.../nats/events/open_webui/*.py` | **NEW** - Sync event definitions |
| `aihub_lib/.../infrastructure/open_webui/OpenWebuiSyncWorker.py` | **NEW** - Event subscriber |
| `aihub_api/.../routes/tenant/TenantController.py` | Publish events on changes |
| `aihub_api/.../routes/access/RoleController.py` | Publish events on changes |
| `aihub_api/.../routes/user/UserController.py` | Publish event on tenant switch |

---

## Testing Plan

### Unit Tests

1. **OpenWebuiSettings tests**:
   - Test settings load from environment
   - Test client creation with correct headers

2. **OpenWebuiService tests** (mock httpx):
   - Test SCIM group CRUD operations
   - Test user lookup by email
   - Test model CRUD operations
   - Test error handling

3. **OpenWebuiGroupSyncService tests**:
   - Test group name generation/parsing
   - Test ACL computation for various access rule combinations
   - Test user group assignment logic

### Integration Tests

1. **Against real OpenWebUI** (docker-compose.dev.yml):
   - Create/delete groups via SCIM
   - Create/delete workspace models
   - Update model ACLs
   - Verify group membership changes

2. **End-to-end flow**:
   - Create tenant + role in AI-Hub
   - Verify OpenWebUI group created
   - Create agent, verify model registered
   - Switch user tenant, verify groups updated
   - Verify model visibility changes

### Manual Testing Checklist

- [ ] User logs in, sees tenant selector with correct tenants
- [ ] User switches tenant, page reloads
- [ ] User's active tenant is persisted across sessions
- [ ] In OpenWebUI, user sees only models for their tenant+roles
- [ ] Chats are organized into tenant folders
- [ ] Admin changes tenant access_rules → model ACLs update
- [ ] New agent comes online → appears as model

---

## Open Questions (Resolved)

1. ✅ **OpenWebUI iframe refresh**: Window reload on tenant switch (Pinia-Colada cache invalidation)

2. **Performance**: For large deployments, consider:
   - Batch SCIM operations
   - Cache computed ACLs in Redis
   - Use NATS events for async processing (Phase 6)

3. ✅ **User ID mapping**: By email address (both systems use email as unique identifier)

4. **Pipeline base model**: The pipeline may need modification to route based on model metadata

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI-Hub Backend                           │
├─────────────────────────────────────────────────────────────────┤
│  TenantEntity          RoleEntity         UserTenantRoleEntity  │
│  ├─ id                 ├─ name            ├─ user_id            │
│  ├─ access_rules       ├─ access_rules    ├─ tenant_id          │
│  └─ ...                └─ tenant_id       └─ roles[]            │
└───────────────┬─────────────────┬───────────────────────────────┘
                │                 │
                ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              OpenWebuiGroupSyncService                          │
├─────────────────────────────────────────────────────────────────┤
│  • ensure_groups_exist()        Creates {tenant}__{role} groups │
│  • compute_agent_acl()          Two-stage access check          │
│  • register_agent_as_model()    Creates workspace model + ACL   │
│  • set_user_groups_for_tenant() Updates user group membership   │
└───────────────┬─────────────────────────────────────────────────┘
                │ SCIM API + REST API
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OpenWebUI                                │
├─────────────────────────────────────────────────────────────────┤
│  Groups                    Models (Agents)                      │
│  ├─ acme__AIHubAdmin       ├─ aihub-assistant-support           │
│  ├─ acme__AgentViewer        ├─ ACL: [acme__AIHubAdmin,         │
│  ├─ beta__AIHubAdmin               acme__AgentViewer]           │
│  └─ beta__ReadOnly         └─ aihub-workflow-bot-1              │
│                               └─ ACL: [acme__AIHubAdmin]        │
│                                                                 │
│  User alice@example.com                                         │
│  └─ groups: [acme__AgentViewer]  ← Updated on tenant switch     │
└─────────────────────────────────────────────────────────────────┘
```