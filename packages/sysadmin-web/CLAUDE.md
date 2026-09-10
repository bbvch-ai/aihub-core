# packages/sysadmin-web - System Administration UI (AGPL-3.0-or-later)

**Purpose**: Nuxt 3 SPA dedicated to system administration. Multi-tenant management lives here. Hosted at
`sysadmin.${DOMAIN}/*`.

**License**: AGPL-3.0-or-later. Network-copyleft: if you offer a modified version as a hosted service, you must publish
the source.

## Architecture: Nuxt Layer over @swiss-ai-hub/web

This package is a Nuxt Layer that **extends `@swiss-ai-hub/web`** via the pnpm workspace symlink:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  extends: ['@swiss-ai-hub/web'],
})
```

```jsonc
// package.json
{ "dependencies": { "@swiss-ai-hub/web": "workspace:*" } }
```

Everything not sysadmin-specific is **inherited from the web layer**: components (Structural primitives, Navigation,
generic widgets), composables (auth, tenant, dashboard), plugins (`0.runtime-config`, `api-client`, `oidc-client`,
`apexcharts`), layouts (`anonymous.vue`, `default.vue` from web), theme, tailwind config, primevue config, i18n setup,
formkit config. Do NOT duplicate any of those here.

## Scope responsibility

What belongs here:

- Sysadmin-only pages (tenant CRUD)
- Components used ONLY by sysadmin pages (`TenantAdmin/{Card,Configure,Edit}.vue`)
- Composables used ONLY by sysadmin pages (`tenant-admin/use*`)
- The `sysadmin.vue` layout used by sysadmin pages (top bar with "Exit"). Opted-in per page via
  `definePageMeta({ layout: 'sysadmin' })`. We deliberately do NOT name it `default.vue` because that would override the
  web layer's own `default.vue` and pollute every inherited route with the sysadmin shell.
- The `sysadmin.global.ts` middleware that gates sysadmin access
- The `tenant_admin:` i18n scope (4 locale files)
- The SDK against `swiss-ai-hub-sysadmin-api` (auto-generated, never edit)

What does NOT belong here:

- Anything tenant-scoped (`/[tenant]/service/...` pages) — those are in `@swiss-ai-hub/web`
- User-facing endpoints (login, select-tenant, my-account) — those are in `@swiss-ai-hub/web`
- Shared UI primitives — extend the layer, do not copy

## Routing model

`sysadmin-web` inherits all of `@swiss-ai-hub/web`'s pages via the Layer extension. That includes the regular admin UI
routes (`/[tenant]/service/*`, `/select-tenant`, `/auth/*`). This is intentional: it keeps sysadmin-web minimal AND lets
sysadmin users follow inherited links seamlessly. The `middleware/sysadmin.global.ts` middleware verifies the user is a
sysadmin on every request; non-sysadmins are bounced to the main app's tenant selector via a cross-origin
`window.location.replace()` using `runtimeConfig.public.mainApp.url` (the main UI origin, not the API origin — they
differ in dev).

The sysadmin-specific routes added by this package live at `/tenants/*` (no leading `/sysadmin/` prefix — the entire app
IS the sysadmin app, so the URL doesn't need to re-declare that fact).

## SDK strategy

Two backends are in play:

- `swiss-ai-hub-sysadmin-api` (AGPL-3.0-or-later) — same-origin at `sysadmin.${DOMAIN}/api/v1/*`. The local SDK in
  `sdk/client/` is generated from its OpenAPI spec and used by the tenant-admin composables.
- `swiss-ai-hub-api` (main API, Apache-2.0) — cross-origin at `${DOMAIN}/api/v1/*`. Used for ONE call: `getMyTenants`
  for the sysadmin role check in `middleware/sysadmin.global.ts`. We do NOT generate a second SDK for one call — the
  middleware uses `$fetch` against `runtimeConfig.public.mainApi.url` (the API origin) for that check. Cross-origin
  browser redirects (non-sysadmin bounce, Exit button, 403 handler) use `runtimeConfig.public.mainApp.url` instead (the
  UI origin). In dev these differ: API is `localhost:8000`, UI is `localhost:3333`; in prod both are `${DOMAIN}`. The
  `composables/useMainAppNavigation.ts` composable owns the `mainApp.url` redirect contract.

Regenerate the local SDK with `pnpm generate-sdk` after changing sysadmin-api endpoints (requires sysadmin-api on port
8001 — `cd packages/sysadmin-api && make run-dev`).

## Auth / session

Same Keycloak realm + same `aihub-frontend` client as `@swiss-ai-hub/web`. The realm-level SSO cookie makes silent renew
transparent across `${DOMAIN}` and `sysadmin.${DOMAIN}` (Keycloak's session cookie domain is `auth.${DOMAIN}` and the
silent-renew iframe carries it on both origins). The OIDC plugin inherited from the web layer handles all the wiring —
no plugin override needed here.

## Commands

| Command             | What it does                                                |
| ------------------- | ----------------------------------------------------------- |
| `pnpm dev`          | Dev server at localhost:3334 (expects sysadmin-api on 8001) |
| `pnpm lint`         | ESLint auto-fix                                             |
| `pnpm generate-sdk` | Regenerate SDK from sysadmin-api OpenAPI spec (needs :8001) |
| `pnpm build`        | Production build (static generation, `.app/.output/public`) |

`make test` is a no-op — no frontend tests configured (mirrors `@swiss-ai-hub/web`).

## Essential files

- Layer config: `nuxt.config.ts` (`extends: ['@swiss-ai-hub/web']`)
- App entry: `.app/nuxt.config.ts` (runtimeConfig including `mainApi.url` + `mainApp.url`, dev proxy → :8001)
- Sysadmin-api SDK init: `app.vue` (sets sysadmin-api `client.baseURL = '/api/v1'` + 403 → `mainApp.url` redirect)
- Sysadmin gate: `middleware/sysadmin.global.ts` (cross-origin `getMyTenants` check via `mainApi.url`)
- Main-app redirect: `composables/useMainAppNavigation.ts` (`mainApp.url` cross-origin redirect — Exit button +
  non-sysadmin bounce)
- Sysadmin layout: `layouts/sysadmin.vue`
- ESLint config: `eslint.config.js` (Nuxt + import/order + SonarJS; no Tailwind linting by design)
- License terms: `LICENSE` (AGPL-3.0-or-later)
- Repo-wide license matrix: `LICENSES.md` (root)
