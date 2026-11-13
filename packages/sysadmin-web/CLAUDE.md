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

- Sysadmin-only pages (tenant CRUD and tenant/global Open WebUI modifications)
- Components used ONLY by sysadmin pages (`TenantAdmin/{Card,Configure,Edit}.vue`)
- Composables used ONLY by sysadmin pages (`tenant-admin/use*`)
- The `sysadmin.vue` layout used by sysadmin pages (top bar with "Exit"). Opted-in per page via
  `definePageMeta({ layout: 'sysadmin' })`. We deliberately do NOT name it `default.vue` because that would override the
  web layer's own `default.vue` and pollute every inherited route with the sysadmin shell.
- The `sysadmin.global.ts` middleware that gates sysadmin access
- The `tenant_admin:` and `openwebui_mods:` i18n scopes (4 locale files)
- The SDK against `swiss-ai-hub-sysadmin-api` (auto-generated, never edit)

What does NOT belong here:

- Anything tenant-scoped (`/[tenant]/service/...` pages) — those are in `@swiss-ai-hub/web`
- User-facing endpoints (login, select-tenant, my-account) — those are in `@swiss-ai-hub/web`
- Shared UI primitives — extend the layer, do not copy

## Routing model

`sysadmin-web` inherits all of `@swiss-ai-hub/web`'s pages via the Layer extension. That includes the regular admin UI
routes (`/[tenant]/service/*`, `/select-tenant`, `/auth/*`). The `middleware/sysadmin.global.ts` middleware checks the
same-origin identity endpoint on navigation and confines sysadmin users to this app's management sections. Auth routes
and the terminal `/{locale}/sysadmin-required` page bypass the check. Authenticated users without the sysadmin role
see that terminal page; a failed identity check redirects to this origin's login page.

The sysadmin-specific routes live at `/{locale}/tenants/*` and `/{locale}/openwebui`. Other inherited routes redirect
sysadmins to the tenant list. The Exit button returns to the main UI using `runtimeConfig.public.mainApp.url`.

## SDK strategy

`swiss-ai-hub-sysadmin-api` (AGPL-3.0-or-later) serves same-origin requests at `sysadmin.${DOMAIN}/api/v1/*`. The local
SDK in `sdk/client/` is generated from its OpenAPI spec and used by the sysadmin composables. The role gate also uses
this SDK: `getMyIdentity` calls `/api/v1/active/my-account/identity`, without a cross-origin main-API request.

Inherited web composables use the web SDK with the same `/api/v1` base URL, so sysadmin-api must mount each endpoint
they need. The `mainApp.url` setting is the main UI origin for browser navigation, owned by
`composables/useMainAppNavigation.ts`; it is not an API base URL.

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
- App entry: `.app/nuxt.config.ts` (runtimeConfig including the same-origin `apiBaseUrl`, OIDC and `mainApp.url`, dev proxy → :8001)
- Sysadmin-api SDK init: `plugins/sysadmin-api-client.client.ts` (sets auth/base URL before route middleware);
  `app.vue` adds the error toast handler
- Sysadmin gate: `middleware/sysadmin.global.ts` (same-origin `getMyIdentity` role check and route confinement)
- Main-app redirect: `composables/useMainAppNavigation.ts` (`mainApp.url` cross-origin navigation for the Exit button)
- Sysadmin layout: `layouts/sysadmin.vue`
- ESLint config: `eslint.config.js` (Nuxt + import/order + SonarJS; no Tailwind linting by design)
- License terms: `LICENSE` (AGPL-3.0-or-later)
- Repo-wide license matrix: `LICENSES.md` (root)
