# Frontend Tenant Selection & X-Tenant-Id Header Injection

**Blocked by:**
- #02 (Tenant-Aware Authorization)
- #03 (Tenant Management API)
- #05 (User-Tenant-Role Assignment API)

## Description

The frontend currently has no concept of tenants. All API requests are sent without tenant context. Users cannot select which tenant they're working in, and the API client doesn't inject the `X-Tenant-Id` header that the backend now requires.

We need to add tenant awareness to the frontend:
- Users select which tenant they're operating in
- Selected tenant persists across sessions (localStorage)
- All API requests automatically include `X-Tenant-Id` header
- Users can switch between tenants if they belong to multiple

## User Flow

When a user logs in:
1. Fetch which tenants they belong to (via API)
2. If they belong to multiple tenants, show a tenant selection screen
3. If they belong to one tenant, auto-select it
4. Store the selected tenant in localStorage
5. Show tenant selector in the UI (e.g., in top bar) for easy switching

## Key Components Needed

- Composable for tenant context management (current tenant state)
- Composable to fetch user's tenant memberships
- HTTP interceptor to inject `X-Tenant-Id` header on all requests
- Tenant selection page/modal
- Tenant switcher component in the UI
- Auth middleware to ensure tenant is selected before accessing protected routes

## Current Code Locations

- API client configuration: `aihub_web/aihub_web/app.vue` (see `client.setConfig()` with `onRequest` interceptor)
- Auth middleware: `aihub_web/aihub_web/middleware/auth.global.ts`
- User bar component: `aihub_web/aihub_web/components/User/Bar.vue`
- Existing composable pattern: `aihub_web/aihub_web/composables/user/useMyUser.ts`

## Header Injection Pattern

The `app.vue` already has an `onRequest` interceptor that sets the `lang` header. Add tenant header injection there.

## Error Handling

If the backend returns a 400 error about missing `X-Tenant-Id`, redirect the user to the tenant selection page.

## Definition of Done

This task is accepted when:

- [ ] Composable exists for managing selected tenant (with localStorage persistence)
- [ ] Composable exists to fetch user's tenant memberships from API
- [ ] `X-Tenant-Id` header is automatically injected on all API requests
- [ ] Tenant selection page/modal allows choosing a tenant
- [ ] Tenant selector component in UI shows current tenant
- [ ] Users can switch tenants without logging out
- [ ] Switching tenants refetches all data (invalidates query cache)
- [ ] Auth middleware redirects to tenant selection if no tenant selected
- [ ] Missing tenant errors from backend are handled gracefully
- [ ] SDK regenerated to include new tenant-related endpoints

## Hints

- Look at how `useMyUser()` composable works - follow similar pattern for tenants
- Consider using PrimeVue Popover for the tenant switcher (like user settings)
- Think about whether tenant selection should be required or if default tenant auto-selects
- The query cache invalidation pattern is used in existing composables - find examples
