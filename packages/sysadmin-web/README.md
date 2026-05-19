# packages/sysadmin-web — Swiss AI Hub system administration UI

**License**: Business Source License 1.1 (BUSL-1.1). Non-production use only — see `LICENSE` for full terms.

A Nuxt 3 SPA dedicated to system administration: today, the multi-tenant management UI moved out of `@swiss-ai-hub/web`.
Hosted at `sysadmin.${DOMAIN}/*` and proxies API calls through the same origin to the BSL `swiss-ai-hub-sysadmin-api` at
`/api/v1/*`.

## Why a separate package

`packages/web` ships under AGPL. The sysadmin plane is the commercial value-add and ships under BUSL-1.1, so it must be
a separately-licensed artifact. Keeping it physically separate also avoids accidentally pulling the BUSL terms into the
AGPL-bound admin UI.

## Nuxt Layer over @swiss-ai-hub/web

This app is a Nuxt 3 Layer that **extends `@swiss-ai-hub/web`**, declared as a pnpm workspace dependency:

```jsonc
// package.json
{
  "dependencies": { "@swiss-ai-hub/web": "workspace:*" }
}
```

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  extends: ['@swiss-ai-hub/web'],
})
```

Nuxt resolves `@swiss-ai-hub/web` via pnpm's node_modules symlink. The Layer extension inherits components, composables,
plugins (including OIDC auth), layouts, theme, tailwind config, primevue config, and i18n setup — no duplication.

Only sysadmin-specific assets live here:

- `pages/tenants*` — tenant list + per-tenant overview / roles / users
- `components/TenantAdmin/{Card,Configure,Edit}.vue` — sysadmin tenant cards/forms
- `composables/tenant-admin/*` — Pinia-Colada queries + mutations for sysadmin endpoints
- `layouts/sysadmin.vue` — the sysadmin shell (top bar with "Exit to main app"). Opted-in per page via
  `definePageMeta({ layout: 'sysadmin' })` so we don't override the inherited web `default.vue` for the inherited routes
- `middleware/sysadmin.global.ts` — refuses non-sysadmins
- `i18n/locales/*.yaml` — `tenant_admin:` translations only

## Runtime

- Container port: `80`. Traefik fronts it at `sysadmin.${DOMAIN}/*`.
- API calls: same-origin `/api/v1/*` → routed by Traefik to `sysadmin-api` (path prefix on `sysadmin.${DOMAIN}`).
- Cross-origin `getMyTenants` check (for the sysadmin role gate) hits the main API at `runtimeConfig.public.mainApi.url`
  (e.g. `https://${DOMAIN}` in prod, `http://localhost:8000` in dev).
- Auth: same Keycloak realm + same `aihub-frontend` client as `@swiss-ai-hub/web`. The Keycloak SSO cookie makes silent
  renew transparent across `${DOMAIN}` and `sysadmin.${DOMAIN}`.
- Dev port: `pnpm dev` binds Nuxt to `localhost:3334` and proxies `/api/v1` to the sysadmin-api on `localhost:8001`.

## Commands

| Command             | What it does                                               |
| ------------------- | ---------------------------------------------------------- |
| `pnpm dev`          | Dev server at localhost:3334; expects sysadmin-api on 8001 |
| `pnpm build`        | Static generation (`.app/.output/public`)                  |
| `pnpm generate-sdk` | Regenerate TypeScript SDK from sysadmin-api OpenAPI spec   |
| `pnpm lint`         | ESLint with `--fix`                                        |

## See also

- `packages/web/README.md` — the parent admin UI (AGPL-3.0-or-later)
- `packages/sysadmin-api/` — the BSL backend this UI talks to
- `LICENSES.md` (repo root) — the per-package license matrix
