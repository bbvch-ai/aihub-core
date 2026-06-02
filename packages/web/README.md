<div align="center">

# @swiss-ai-hub/web

**The admin and management UI for [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core), published as a
[Nuxt 3 layer](https://nuxt.com/docs/getting-started/layers).**

[![npm](https://img.shields.io/npm/v/@swiss-ai-hub/web?style=flat-square&logo=npm&logoColor=white)](https://www.npmjs.com/package/@swiss-ai-hub/web)
[![License](https://img.shields.io/badge/license-AGPL%203.0--or--later-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/web/LICENSE)

</div>

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. One
`docker compose up` starts ~30 integrated containers: an LLM gateway (LiteLLM), vector search (Milvus), data pipelines
(Dagster), document parsing (MinerU), SSO (Keycloak), observability (Langfuse + OpenTelemetry), a chat UI (Open-WebUI),
and more. You build custom agents, pipelines, and processes using the Python SDK; the platform provides the runtime.

## What is this package?

This package is the **admin and management UI** -- one component of the larger platform. It is the interface where
administrators configure agents, manage knowledge bases, monitor processes, inspect threads, assign roles, track costs,
and build dashboards. It is **not** the chat UI (that's [Open-WebUI](https://github.com/open-webui/open-webui)) and not
the backend API.

The admin UI is built with [Nuxt 3](https://nuxt.com/), [Vue 3](https://vuejs.org/), [PrimeVue](https://primevue.org/),
and [Tailwind CSS](https://tailwindcss.com/). It is published as a
**[Nuxt layer](https://nuxt.com/docs/getting-started/layers)** -- a mechanism that lets you inherit an entire Nuxt
application (pages, components, composables, plugins, config) and extend or override any part of it in your own project.

______________________________________________________________________

## Should you use this package?

**Probably not.** Most deployments should use the pre-built Docker image, which ships the admin UI ready to go:

```yaml
# docker-compose.yml
services:
  admin-ui:
    image: ghcr.io/bbvch-ai/aihub-core/web:latest
    ports:
      - "3333:80"
```

The Docker image works out of the box with zero frontend code. Configuration (OIDC provider, API endpoint, WebSocket
URL) is handled through environment variables at runtime.

**Use this npm package only if you need to extend the UI with your own code** -- adding custom pages, overriding
components, modifying translations, or changing the theme. This is an SDK for building a custom frontend on top of Swiss
Swiss AI Hub, not a standalone app.

## When this package makes sense

| Use case                  | Example                                                                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **Custom pages**          | Add an organization-specific dashboard, a domain-specific tool, or internal admin views that don't belong in the open-source project |
| **Branding**              | Override the PrimeVue theme, replace the logo, adjust colors to match corporate identity                                             |
| **Translation overrides** | Fix or extend translations, add a fifth language, change terminology to match your domain                                            |
| **Component overrides**   | Replace a built-in component with your own implementation                                                                            |
| **Custom plugins**        | Add organization-specific Nuxt plugins (analytics, feature flags, custom error tracking)                                             |
| **Custom auth flow**      | Extend the OIDC middleware for provider-specific requirements                                                                        |

______________________________________________________________________

## How Nuxt layers work

If you're not familiar with [Nuxt layers](https://nuxt.com/docs/getting-started/layers), here's the idea: a layer is a
full Nuxt application that another Nuxt project can inherit from using `extends` in `nuxt.config.ts`. When you extend
this layer, you get all of its pages, components, composables, plugins, middleware, layouts, and configuration -- merged
into your project automatically. Nuxt resolves conflicts by giving your project priority: if you define a component with
the same name and path as one in the layer, yours wins. Same for pages, composables, and config keys.

This means you don't fork the repo or copy files. You install the package, extend it, and only write the code for what
you want to change or add.

For a deeper understanding, see the [official Nuxt layers documentation](https://nuxt.com/docs/getting-started/layers)
and the [layer authoring guide](https://nuxt.com/docs/guide/going-further/layers).

______________________________________________________________________

## Installation

```bash
npm install @swiss-ai-hub/web
# or
pnpm add @swiss-ai-hub/web
```

Install the required peer dependencies:

```bash
npm install primevue@4.5.5 vue@3.5.17
```

### Required dependency overrides

**Do not skip this step.** Without it your project ends up with two copies of Vue in `node_modules`, and the UI will
either fail to build or render with broken behavior.

Nuxt and several of its modules depend on their own (newer) copy of Vue, while this layer is built and tested against an
exact Vue version. With nothing forcing them to agree, your install resolves **two different Vue versions** -- and
therefore two copies of `@vue/runtime-core`, the package that owns Vue's runtime identity. Two Vue runtimes means two
separate reactivity systems: `provide`/`inject` stops working across the boundary, component instance checks fail, and
you get cryptic errors like _"Vue instance ... was created in a different application"_. The same single-instance
requirement applies to PrimeVue, whose theme system relies on a global singleton (two instances → unstyled components).

The fix is to force the whole dependency tree onto one Vue version using your package manager's override mechanism. Add
this to your project's `package.json`:

```jsonc
// npm or yarn
{
  "overrides": {
    "vue": "3.5.17",
    "@vueuse/router": { "vue-router": "4.6.4" }
  }
}
```

```jsonc
// pnpm
{
  "pnpm": {
    "overrides": {
      "vue": "3.5.17",
      "@vueuse/router>vue-router": "4.6.4"
    }
  }
}
```

Then reinstall from a clean state so the lockfile is regenerated, and confirm a single Vue instance:

```bash
rm -rf node_modules package-lock.json   # or pnpm-lock.yaml
npm install
npm ls @vue/runtime-core                # must print exactly one version: 3.5.17
```

> **Why these entries?** `vue` pins the framework runtime to a single instance shared by your app, the layer, and every
> Nuxt module -- this is the one that actually breaks if omitted. The scoped `@vueuse/router > vue-router` entry
> resolves a harmless peer-range mismatch (`@vueuse/router` expects vue-router 4, Nuxt's router is 5); it is scoped so
> it only affects that one nested dependency and never the router Nuxt itself uses. The versions match the
> [peer dependencies](#peer-dependencies) the layer is built and tested against.

## Quick start

### 1. Create a Nuxt project

```bash
npx nuxi init my-aihub-frontend
cd my-aihub-frontend
npm install
```

Then install this package, its peer dependencies, and -- importantly -- add the
[required dependency overrides](#required-dependency-overrides). Skipping the overrides leaves two copies of Vue in your
tree and the app will not work.

### 2. Extend the layer

Replace the generated `nuxt.config.ts` with:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  extends: ['@swiss-ai-hub/web'],

  // These dev defaults match infra/docker-compose.dev.yml + `make run-api`.
  // For production, leave these declared (the keys must exist) but blank, and
  // inject values at runtime via /config.js -- see Runtime configuration below.
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
        endpoint: 'ws://localhost:8000/api/v1/active/events/ws',
      },
    },
  },

  // Proxy API requests to the backend during development.
  // In production, your reverse proxy (Traefik) handles this.
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

### 3. Start the platform

Make sure the Swiss AI Hub backend is running (either via `docker compose up` or locally with `make run-api`).

### 4. Run

```bash
npx nuxi dev
```

Open `http://localhost:3000`. You get the full admin UI -- agents, processes, threads, knowledge bases, models, roles,
dashboards, and chat -- running locally and pointing at your platform instance. Log in with your Keycloak credentials
(default: `admin` / `admin`).

______________________________________________________________________

## What the layer provides

Everything the admin UI needs ships inside this package:

| Category           | What you get                                                                                                                            |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Pages**          | Full file-based routing under `/service/` -- agents, processes, threads, knowledge, models, roles, dashboards, chat, costs, evaluations |
| **Components**     | ~170 Vue components organized by domain (Agent, Chat, Dashboard, Event, Navigation, Process, Thread, Workflow, ...)                     |
| **Composables**    | [Pinia-Colada](https://pinia-colada.esm.dev/) query/mutation wrappers for every API resource                                            |
| **SDK client**     | Auto-generated TypeScript API client ([HeyAPI](https://heyapi.dev/))                                                                    |
| **Layouts**        | `default` (authenticated) and `anonymous` layouts                                                                                       |
| **Middleware**     | OIDC auth guard on all routes                                                                                                           |
| **Plugins**        | OIDC client, config loader, ApexCharts                                                                                                  |
| **i18n**           | German, English, French, Italian (lazy-loaded YAML files)                                                                               |
| **Theme**          | PrimeVue [Aura](https://primevue.org/theming/styled/#aura)-based theme with dark mode support                                           |
| **FormKit config** | Custom form inputs (agent selector, model select, knowledge database selector, icon selector, locale input, vector store input)         |

______________________________________________________________________

## Extending the UI

### Add a custom page

Create a Vue file in `pages/` and Nuxt merges it with the layer's routes. The layer's components and composables are
auto-imported and available in your pages without any explicit imports:

```vue
<!-- pages/service/my-tool.vue -->
<template>
  <StructuralScreen>
    <StructuralColumn title="My Custom Tool">
      <p>This page lives only in your deployment, not in the open-source project.</p>
      <p>All layer components and composables are available here.</p>
    </StructuralColumn>
  </StructuralScreen>
</template>
```

`StructuralScreen` is the full-height scrollable container used by every page. `StructuralColumn` provides a titled
panel with built-in loading states -- pass `:loading="true"` to show a progress bar and suppress content until data is
ready. These are the two layout primitives that all admin UI pages are built on.

To add navigation for your page, you can extend the sidebar by overriding the navigation component (see
[Override a component](#override-a-component) below).

### Override translations

The layer ships i18n files for German, English, French, and Italian in `i18n/locales/`. To override specific keys or add
a new language, create matching locale files in your project:

```
my-project/
  i18n/
    locales/
      en.yaml   # keys here override the layer's en.yaml
      de.yaml
      pt.yaml   # add a new language
```

```yaml
# i18n/locales/en.yaml -- only the keys you want to change
agent:
  title: "AI Assistants"  # override "Agents" with your preferred term
my_tool:
  title: "My Custom Tool"  # add keys for your custom pages
```

You also need to register new languages in your `nuxt.config.ts`:

```ts
export default defineNuxtConfig({
  extends: ['@swiss-ai-hub/web'],

  i18n: {
    locales: [
      { code: 'pt', file: 'pt.yaml', name: 'Portugues' },
    ],
  },
})
```

### Override the theme

The admin UI uses [PrimeVue's styled mode](https://primevue.org/theming/styled/) with a customized
[Aura preset](https://primevue.org/theming/styled/#aura). Theming works through **design tokens** -- semantic color
values that PrimeVue components reference. You override tokens to change the look of every component at once.

To create your own theme, start from the Aura preset and customize the tokens you want to change:

```ts
// themes/my-theme.ts
import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

const MyPreset = definePreset(Aura, {
  semantic: {
    // Change the primary color palette (used for buttons, selections, highlights)
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
      950: '#172554',
    },
    // Override light/dark mode colors
    colorScheme: {
      light: {
        primary: {
          color: '#2563eb',
          inverseColor: '#ffffff',
          hoverColor: '#1d4ed8',
          activeColor: '#1e40af',
        },
      },
      dark: {
        primary: {
          color: '#60a5fa',
          inverseColor: '#172554',
          hoverColor: '#93c5fd',
          activeColor: '#bfdbfe',
        },
      },
    },
  },
})

export default {
  preset: MyPreset,
  options: {
    darkModeSelector: '.dark',  // must stay '.dark' to match the Tailwind dark mode config
  },
}
```

Then point your `nuxt.config.ts` at it:

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

For the full list of design tokens you can customize, see the
[PrimeVue theming documentation](https://primevue.org/theming/styled/) and the
[Aura preset reference](https://primevue.org/theming/styled/#aura).

### Override a component

Nuxt's layer system resolves components by name and directory path. If you place a component with the same name in the
same directory structure, your version takes priority over the layer's:

```
my-project/
  components/
    Navigation/
      Logo.vue          # replaces the layer's Navigation/Logo.vue
    Agent/
      Card.vue          # replaces the layer's Agent/Card.vue
```

This works for any component in the layer. You can inspect the layer's component directory structure in the
[source repository](https://github.com/bbvch-ai/aihub-core/tree/main/packages/web/components) to find the exact names
and paths.

______________________________________________________________________

## Building for production

```bash
npx nuxi generate
```

This produces a fully static SPA in `.output/public/` (the layer is client-only -- `ssr: false`). Because the output is
static, there is **no Node server at runtime to read environment variables**. Instead, the layer ships a small
runtime-config mechanism (see [Runtime configuration](#runtime-configuration)) so you build **one** image and configure
it per environment at container start -- including which backend API it talks to.

### Dockerfile example

This mirrors how Swiss AI Hub ships the admin UI: build the static site, serve it with nginx, and generate `/config.js`
from a template at startup so the same image works in any environment.

```dockerfile
# 1. Build the static SPA. ENV must be unset (or anything other than 'dev') so
#    the layer emits the <script src="/config.js"> tag that loads runtime config.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx nuxi generate

# 2. Serve with nginx; render /config.js from env vars on container start.
FROM nginx:alpine
RUN apk add --no-cache gettext   # provides envsubst
COPY --from=build /app/.output/public /usr/share/nginx/html
COPY config.template.js /usr/share/nginx/html/config.template.js
CMD ["/bin/sh", "-c", "envsubst < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js && nginx -g 'daemon off;'"]
```

nginx must serve `/config.js` uncached and never fall back to `index.html` for it -- declare it **before** the SPA
catch-all:

```nginx
location = /config.js {
  add_header Cache-Control "no-store" always;
  default_type application/javascript;
  try_files $uri =404;
}
location / { try_files $uri /index.html; }
```

______________________________________________________________________

## Runtime configuration

The layer reads all runtime configuration from `runtimeConfig.public`, populated in **two phases**:

1. **Build-time defaults** -- whatever you put in `runtimeConfig.public` in your `nuxt.config.ts`. Used directly in dev,
   baked into the static build.
2. **Runtime overrides (production)** -- a `window.__AIHUB_CONFIG__` object loaded synchronously from `/config.js`
   **before** the app boots. A plugin shipped in this layer (`plugins/0.runtime-config.client.ts`) maps it into
   `runtimeConfig.public`. This is how a single static build is configured per environment without rebuilding.

`/config.js` is rendered by `envsubst` from your `config.template.js` at container start (see the Dockerfile above). The
layer injects the `<script src="/config.js">` tag automatically for any non-dev build, and the mapping plugin runs in
every app that extends the layer -- so you only supply the template:

```js
// config.template.js -- envsubst replaces ${...} at container start.
// Include only the keys your deployment needs; unset ones resolve to defaults.
window.__AIHUB_CONFIG__ = {
  API_BASE_URL: '${API_BASE_URL}',
  OAUTH_CLIENT_ID: '${OAUTH_CLIENT_ID}',
  OAUTH_AUTHORITY_URL: '${OAUTH_AUTHORITY_URL}',
  WEBUI_URL: '${WEBUI_URL}',
  WS_ENDPOINT: '${WS_ENDPOINT}',
}
```

| `runtimeConfig.public` key | `window.__AIHUB_CONFIG__` key | Default                 | Description                                                        |
| -------------------------- | ----------------------------- | ----------------------- | ------------------------------------------------------------------ |
| `apiBaseUrl`               | `API_BASE_URL`                | `/api/v1` (same origin) | Backend API base URL -- see [below](#pointing-at-your-backend-api) |
| `oidc.clientId`            | `OAUTH_CLIENT_ID`             | --                      | OIDC client ID (Keycloak)                                          |
| `oidc.authorityUrl`        | `OAUTH_AUTHORITY_URL`         | --                      | OIDC authority / realm URL                                         |
| `webui.url`                | `WEBUI_URL`                   | --                      | Open-WebUI URL (chat link)                                         |
| `ws.endpoint`              | `WS_ENDPOINT`                 | --                      | WebSocket endpoint for real-time agent events                      |
| `env`                      | --                            | --                      | Set to `dev` locally (uses build-time values, skips `/config.js`)  |

> **Declare the groups you want populated.** The mapping plugin only writes into config groups your app already declared
> in `runtimeConfig.public` (e.g. `oidc: {}`, `webui: {}`, `ws: {}`); in production set their build-time values to empty
> strings and let `/config.js` fill them. `apiBaseUrl` is the exception -- it is always applied when `API_BASE_URL` is
> present.

### Pointing at your backend API

The admin UI talks to the Swiss AI Hub backend through a single base URL, `runtimeConfig.public.apiBaseUrl`. It defaults
to the **same origin** as the UI (`/api/v1`) -- the simplest setup: put the UI and the API behind one reverse proxy
(what the platform's Traefik does) and no API configuration is needed at all.

If your UI is served from a **different origin** than the API, set the base URL explicitly:

- **Dev / build-time** -- set it in `nuxt.config.ts`, or (recommended for local dev) keep `/api/v1` and proxy it with
  Nitro:

  ```ts
  export default defineNuxtConfig({
    extends: ['@swiss-ai-hub/web'],
    // Option A: point straight at the API origin
    runtimeConfig: { public: { apiBaseUrl: 'https://aihub.example.com/api/v1' } },
    // Option B (same-origin dev): keep /api/v1 and proxy it
    nitro: { devProxy: { '/api/v1': { target: 'http://localhost:8000/api/v1', changeOrigin: true, ws: true } } },
  })
  ```

- **Production (static image)** -- inject `API_BASE_URL` at container start via `config.template.js`. One image, any
  backend:

  ```bash
  docker run -e API_BASE_URL=https://aihub.example.com/api/v1 my-aihub-frontend
  ```

> **Cross-origin caveats.** A different API origin must allow your UI's origin via CORS, and your Keycloak client must
> list it as an allowed web/redirect origin. Same-origin (`/api/v1` behind one proxy) avoids both. Do **not** call
> `client.setConfig({ baseURL: ... })` in your own `app.vue` unless you deliberately want to hard-override this
> mechanism.

## Peer dependencies

| Package    | Version  | Why                                                                                                                                    |
| ---------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `primevue` | `4.5.5`  | UI component library -- must be a single instance to avoid theme-singleton conflicts (see [overrides](#required-dependency-overrides)) |
| `vue`      | `3.5.17` | Framework runtime -- must be a single instance; enforce with the [required overrides](#required-dependency-overrides)                  |

> These exact versions are what the layer is built and published against. They are declared as `peerDependencies`, so
> your project must provide them, and the [overrides](#required-dependency-overrides) above ensure every transitive
> dependency resolves to the same single copy.

## Tech stack

| Category          | Technologies                                                                                                                                                   |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Framework**     | [Nuxt 3](https://nuxt.com/), [Vue 3](https://vuejs.org/) (Composition API), [TypeScript](https://www.typescriptlang.org/)                                      |
| **UI**            | [PrimeVue](https://primevue.org/), [Tailwind CSS](https://tailwindcss.com/), [FormKit](https://formkit.com/)                                                   |
| **State**         | [Pinia-Colada](https://pinia-colada.esm.dev/) (query/mutation caching)                                                                                         |
| **Auth**          | [oidc-client-ts](https://github.com/authts/oidc-client-ts) (OpenID Connect)                                                                                    |
| **API**           | [HeyAPI](https://heyapi.dev/) (auto-generated TypeScript SDK)                                                                                                  |
| **Visualization** | [VueFlow](https://vueflow.dev/) (workflow graphs), [ApexCharts](https://apexcharts.com/) (dashboards), [Sigma.js](https://www.sigmajs.org/) (knowledge graphs) |
| **Utilities**     | [VueUse](https://vueuse.org/), [lodash-es](https://lodash.com/), [date-fns](https://date-fns.org/)                                                             |
| **i18n**          | [@nuxtjs/i18n](https://i18n.nuxtjs.org/) (4 languages, lazy-loaded YAML)                                                                                       |

## License

Copyright (C) 2024-2026 bbv Software Services AG.

AGPL-3.0-or-later — see [packages/web/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/web/LICENSE).
For the full per-package matrix (root, AGPL, and proprietary packages), see
[LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
