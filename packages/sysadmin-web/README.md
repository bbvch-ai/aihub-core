# packages/sysadmin-web — Swiss AI Hub system administration UI

**License**: AGPL-3.0-or-later. Network-copyleft: hosted modifications must publish their source. See `LICENSE` for full
terms.

A Nuxt 3 SPA dedicated to system administration: today, the multi-tenant management UI moved out of `@swiss-ai-hub/web`.
Hosted at `sysadmin.${DOMAIN}/*` and proxies API calls through the same origin to the `swiss-ai-hub-sysadmin-api` at
`/api/v1/*`.

## Why a separate package

The sysadmin plane is a separate deploy artifact on its own subdomain, isolating the sysadmin-only management surface
from the main app as a hard security boundary. Both `packages/web` and this package ship under AGPL-3.0-or-later, so the
separation is architectural — not a licensing boundary.

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

- `pages/tenants*` — tenant list + per-tenant overview / roles / users / Open WebUI settings
- `components/TenantAdmin/{Card,Configure,Edit}.vue` — sysadmin tenant cards/forms
- `composables/tenant-admin/*` — Pinia-Colada queries + mutations for sysadmin endpoints
- `layouts/sysadmin.vue` — the sysadmin shell (top bar with "Exit to main app"). Opted-in per page via
  `definePageMeta({ layout: 'sysadmin' })` so we don't override the inherited web `default.vue` for the inherited routes
- `middleware/sysadmin.global.ts` — refuses non-sysadmins
- `i18n/locales/*.yaml` — tenant administration and Open WebUI settings translations

## Open WebUI modifications

Tenant Open WebUI settings and Global Open WebUI share the package catalog and version dialog. Composables under
`openwebui-mods/` manage source uploads, publication and versioned saves through the same-origin SysAdmin API.
Components retain failed-save drafts and show pending global restart/worker status. See the
[administrator guide](https://docs.ai-hub.bbv.ch/docs/2_platform/10_chat_ui/16_openwebui_mods/) for the workflow and
[author guide](https://docs.ai-hub.bbv.ch/docs/3_sdk/6_feature_overview/1_openwebui_mods/) for package requirements.

## Runtime

- Container port: `80`. Traefik fronts it at `sysadmin.${DOMAIN}/*`.
- API calls: same-origin `/api/v1/*` → routed by Traefik to `sysadmin-api` (path prefix on `sysadmin.${DOMAIN}`).
- The sysadmin role gate uses the local SDK's same-origin `getMyIdentity` endpoint at
  `/api/v1/active/my-account/identity`. Users without the role see the local `sysadmin-required` page; failed identity
  checks redirect to local login. Authenticated sysadmins stay within the tenant and global Open WebUI sections.
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
- `packages/sysadmin-api/` — the AGPL-3.0-or-later backend this UI talks to
- `LICENSES.md` (repo root) — the per-package license matrix
