<div align="center">

# @swiss-ai-hub/web

**The admin and management UI for [Swiss AI-Hub](https://github.com/bbvch-ai/aihub-core), published as a
[Nuxt 3 layer](https://nuxt.com/docs/getting-started/layers).**

[![npm](https://img.shields.io/npm/v/@swiss-ai-hub/web?style=flat-square&logo=npm&logoColor=white)](https://www.npmjs.com/package/@swiss-ai-hub/web)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSE)

</div>

______________________________________________________________________

## Should you use this package?

**Probably not.** Most deployments should use the pre-built Docker image, which ships the admin UI ready to go:

```yaml
# docker-compose.yml
services:
  admin-ui:
    image: ghcr.io/bbvch-ai/aihub-web:latest
    ports:
      - "3333:80"
```

The Docker image works out of the box with zero frontend code. Configuration (OIDC provider, API endpoint, WebSocket
URL) is handled through environment variables at runtime.

**Use this npm package only if you need to extend the UI with your own code** -- adding custom pages, overriding
components, modifying translations, or changing the theme. This is an SDK for building a custom frontend on top of Swiss
AI-Hub, not a standalone app.

## When this package makes sense

| Use case                  | Example                                                                                                                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Custom pages**          | Add an organization-specific dashboard, a domain-specific tool, or internal admin views that don't belong in the open-source project                                                          |
| **Branding**              | Override the PrimeVue theme, replace the logo, adjust colors to match corporate identity                                                                                                      |
| **Translation overrides** | Fix or extend translations, add a fifth language, change terminology to match your domain                                                                                                     |
| **Component overrides**   | Replace a built-in component with your own implementation (Nuxt layers support [component overriding](https://nuxt.com/docs/guide/going-further/layers#multi-layer-support-for-nuxt-modules)) |
| **Custom plugins**        | Add organization-specific Nuxt plugins (analytics, feature flags, custom error tracking)                                                                                                      |
| **Custom auth flow**      | Extend the OIDC middleware for provider-specific requirements                                                                                                                                 |

## Installation

```bash
npm install @swiss-ai-hub/web
# or
pnpm add @swiss-ai-hub/web
```

Install the required peer dependencies:

```bash
npm install primevue@4.5.4 vue@3.5.17
```

## Quick start

### 1. Create a Nuxt project

```bash
npx nuxi init my-aihub-frontend
cd my-aihub-frontend
```

### 2. Extend the layer

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  extends: ['@swiss-ai-hub/web'],

  // These defaults match docker-compose.dev.yml + `make run-api`
  runtimeConfig: {
    public: {
      env: 'dev',
      oidc: {
        clientId: 'aihub-frontend',
        authorityUrl: 'http://localhost:8180/realms/aihub',
      },
      webui: {
        url: 'http://localhost:8080',
      },
      ws: {
        endpoint: 'ws://localhost:8000/api/v1/events/ws',
      },
    },
  },

  nitro: {
    devProxy: {
      '/api/v1': {
        target: 'http://localhost:8000/api/v1',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
```

### 3. Run

```bash
npx nuxi dev
```

You get the full Swiss AI-Hub admin UI -- agents, processes, threads, knowledge bases, models, roles, dashboards, and
chat -- running locally and pointing at your platform instance.

## What the layer provides

Everything the admin UI needs ships inside this package:

- **Pages** -- full file-based routing under `/service/` (agents, processes, threads, knowledge, models, roles,
  dashboards, chat, costs, evaluations)
- **Components** -- ~170 Vue components organized by domain
- **Composables** -- Pinia-Colada query/mutation wrappers for every API resource
- **SDK client** -- auto-generated TypeScript API client (HeyAPI)
- **Layouts** -- default (authenticated) and anonymous layouts
- **Middleware** -- OIDC auth guard on all routes
- **Plugins** -- OIDC client, config loader, ApexCharts
- **i18n** -- German, English, French, Italian (lazy-loaded YAML)
- **Theme** -- PrimeVue Aura-based theme with dark mode
- **FormKit config** -- custom inputs (agent selector, model select, knowledge database selector, etc.)

## Extending the UI

### Add a custom page

Create a page in your project. Nuxt merges it with the layer's pages:

```vue
<!-- pages/service/my-tool.vue -->
<template>
  <StructuralScreen>
    <StructuralColumn title="My Custom Tool">
      <p>This page is only in your deployment.</p>
    </StructuralColumn>
  </StructuralScreen>
</template>
```

All layer components (`StructuralScreen`, `StructuralColumn`, etc.), composables, and auto-imports are available in your
pages.

### Override translations

Create locale files in your project. Keys you define override the layer's defaults:

```
i18n/locales/en.yaml   # your overrides merge on top of the layer's en.yaml
i18n/locales/de.yaml
```

### Override the theme

Provide your own PrimeVue theme file:

```ts
// nuxt.config.ts
import { fileURLToPath } from 'url'

export default defineNuxtConfig({
  extends: ['@swiss-ai-hub/web'],

  primevue: {
    importTheme: {
      from: fileURLToPath(new URL('./themes/my-theme.ts', import.meta.url)),
    },
  },
})
```

### Override a component

Place a component with the same name and path in your project. Nuxt's layer system gives your project's components
priority over the layer's:

```
components/
  Navigation/
    Logo.vue    # your Logo.vue replaces the layer's Navigation/Logo.vue
```

## Building for production

```bash
npx nuxi generate
```

This produces a static site in `.output/public/` that you can serve from any static host or package into a Docker image:

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY . .
RUN npm install && npx nuxi generate

FROM nginx:alpine
COPY --from=build /app/.output/public /usr/share/nginx/html
```

## Runtime configuration

All configuration is provided through `runtimeConfig.public` in `nuxt.config.ts`. In production, these values are
typically injected via environment variables:

| Config key          | Environment variable             | Description                             |
| ------------------- | -------------------------------- | --------------------------------------- |
| `oidc.clientId`     | `NUXT_PUBLIC_OIDC_CLIENT_ID`     | OIDC client ID for authentication       |
| `oidc.authorityUrl` | `NUXT_PUBLIC_OIDC_AUTHORITY_URL` | OIDC provider URL (Keycloak realm)      |
| `webui.url`         | `NUXT_PUBLIC_WEBUI_URL`          | OpenWebUI URL for the chat interface    |
| `ws.endpoint`       | `NUXT_PUBLIC_WS_ENDPOINT`        | WebSocket endpoint for real-time events |
| `env`               | `NUXT_PUBLIC_ENV`                | Environment identifier (`dev`, `prod`)  |

## Peer dependencies

| Package    | Version  | Why                                                                        |
| ---------- | -------- | -------------------------------------------------------------------------- |
| `primevue` | `4.5.4`  | UI component library -- must be a single instance to avoid theme conflicts |
| `vue`      | `3.5.17` | Framework runtime                                                          |

## Tech stack

The layer is built on: **Nuxt 3**, **Vue 3** (Composition API), **TypeScript**, **PrimeVue**, **Tailwind CSS**,
**Pinia-Colada**, **FormKit**, **VueUse**, **oidc-client-ts**, **HeyAPI**, **VueFlow**, **ApexCharts**.

## License

Apache 2.0 -- see [LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSE).

______________________________________________________________________

<div align="center">

Part of [Swiss AI-Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
