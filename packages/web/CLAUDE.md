# packages/web - Admin & Management UI

**Purpose**: Nuxt 3 frontend for Swiss AI Hub. Admin interface for agents, processes, threads, knowledge, models, roles,
dashboards, and chat. Vue 3 Composition API, TypeScript strict, PrimeVue, Tailwind CSS, Pinia-Colada. Client-side only
(no SSR).

## Folder Structure

```
packages/web/
├── .app/                    # Nuxt layer entry point (extends parent, runtimeConfig, FormKit config)
├── assets/css/              # Global CSS (main.css)
├── components/              # Domain-organized Vue components (~170 files)
│   ├── Agent/               # Agent cards, configuration, workflow visualization
│   ├── Chat/                # Chat interface
│   ├── Dashboard/           # GridStack dashboard widgets (ApexCharts)
│   ├── Event/Display/       # 26 event display components (agent timeline)
│   ├── Event/List/          # Event timeline container (PrimeVue Timeline)
│   ├── FormKit/             # Custom FormKit inputs (AgentSelector, ModelSelect, etc.)
│   ├── Navigation/          # Left nav, breadcrumbs
│   ├── Process/             # Process management + walkthrough UI
│   ├── Structural/          # Layout primitives (Screen, Column, Substructure)
│   ├── Thread/              # Thread display
│   ├── Workflow/            # VueFlow agent workflow visualization
│   └── ...                  # Costs, Display, Evaluation, Knowledge, Memory, Models, etc.
├── composables/             # Pinia-Colada query/mutation wrappers (domain-organized)
│   ├── agent/               # useAgentInstances, useAgentClasses, mutations
│   ├── thread/              # useThreads, useThreadEvents (WebSocket real-time)
│   ├── tenant/              # useTenant — reads tenant id from either route shape (`[tenant]` or `[tenant_id]`)
│   ├── tenant-admin/        # useTenantAdminList, useConfigureTenant, useUpdateTenant, useDeleteTenant, useUnconfiguredTenantIds
│   ├── form/                # useFormKitTransform (backend schema → FormKit nodes)
│   ├── event/               # useEventComponent (event → display component resolver)
│   └── ...                  # auth, chat, dashboard, document, evaluation, file, etc.
├── i18n/locales/            # de.yaml, en.yaml, fr.yaml, it.yaml
├── layouts/                 # default.vue, anonymous.vue, sysadmin.vue (sysadmin-only routes)
├── middleware/              # auth.global.ts (OIDC guard on all routes)
├── pages/                   # File-based routing
│   ├── [tenant]/service/    # Tenant-scoped admin pages (regular users + tenant admins)
│   └── sysadmin/            # Sysadmin tenant management (requires AIHubSysAdmin realm role)
├── plugins/                 # 0.runtime-config.client.ts (config), api-client.client.ts (SDK), oidc-client.ts, apexcharts.client.ts
├── sdk/client/              # Auto-generated HeyAPI TypeScript client (NEVER edit)
├── themes/                  # aihub-theme.ts (PrimeVue Aura preset customization)
└── types/                   # Shared TypeScript types (NavItem, DashboardWidget, etc.)
```

## Nuxt Layer Architecture

The `.app/` directory is the actual entry point — it extends the parent via `extends: ['..']` in its `nuxt.config.ts`.
`pnpm dev` runs `nuxi dev .app`. The parent `packages/web/` provides components, composables, pages, and config. `.app/`
adds `runtimeConfig` (OIDC, WebSocket endpoint, env vars). FormKit registration lives in the layer itself
(`packages/web/formkit.config.ts`, wired via `formkit.configFile` in `nuxt.config.ts`), so extenders inherit it.

## Page Composition Pattern

Master-detail layout using nested Nuxt routing:

```
StructuralScreen                          ← list page (agents.vue)
  StructuralColumn title="Agents"         ← list panel
    AgentCard × N
  NuxtPage                                ← renders detail hub page
    SelectButton (sub-nav)                ← NavItem tabs
    NuxtPage                              ← renders leaf page (overview, config, etc.)
      StructuralColumn title="Overview"   ← detail panel (close-route="/service/agents")
```

**StructuralColumn** props: `title`, `loading` (shows ProgressBar, suppresses slot content), `closeRoute` (back button),
`size` (`'small' | 'normal' | 'large'`), `childColumn` (h2 → h3 heading).

**StructuralScreen**: Full-height scrollable container. `2xl:flex-row` creates side-by-side columns on large screens.

**Key rule**: List pages contain `<NuxtPage />` — they ARE the layout frame for their detail children. Don't create
separate layout files for detail pages.

## NavItem Pattern

```typescript
type NavItem = { name: string; key: string; path: string; isActive: () => boolean }
```

`isActive` is a **function returning boolean**, not a boolean. Always define as a closure:

```typescript
const isActive = (path: string) => () => route.path.startsWith(localePath(subPath(path)))
```

Sub-page navigation uses PrimeVue `<SelectButton>` with NavItem options.

## Pinia-Colada (State Management)

**Query pattern** (GET):

```typescript
export const useAgentInstances = defineQuery(() => {
  const { data: agentInstances, isPending: agentInstancesAreLoading } = useQuery<FullAgentInstanceDto[]>({
    key: () => ['agent-instances'],                                          // MUST be a function
    staleTime: minutesToMilliseconds(5),                                     // date-fns helper
    query: async () => await getAllAgentInstances({ composable: '$fetch' }), // composable: '$fetch' REQUIRED
  })
  return { agentInstances, agentInstancesAreLoading }
})
```

**Mutation pattern** (POST/PUT/DELETE):

```typescript
export const useDeleteAgentInstance = defineMutation(() => {
  const queryCache = useQueryCache()
  const { mutateAsync: deleteAgentInstanceMutation } = useMutation({
    mutation: async ({ agentClass, agentId }: { agentClass: string, agentId: string }) => {
      await deleteAgentInstance({ composable: '$fetch', path: { agent_class: agentClass, agent_id: agentId } })
      queryCache.invalidateQueries({ key: ['agent-instances'] })                       // Broad
      queryCache.invalidateQueries({ key: ['agent-class-instances', agentClass] })     // Specific
    },
  })
  return { deleteAgentInstance: deleteAgentInstanceMutation }
})
```

**Conventions**:

- `defineQuery`/`defineMutation` are auto-imported — no explicit import needed
- Query keys: always `() => [...]` (function returning array, not plain array)
- `staleTime: minutesToMilliseconds(5)` — standard cache duration, use `date-fns` helper
- Route-dependent queries: `enabled: useRouteReady('param_name')` prevents firing before route resolves
- Export as `export const useFoo = defineQuery(...)` (named export, not default)
- Mutations invalidate both broad and specific query keys
- **`composable: '$fetch'` REQUIRED** on every SDK call (HeyAPI Nuxt adapter requirement)

## SDK Generation

- **Generate**: `pnpm generate-sdk` (requires API running at localhost:8000)
- **Config**: `openapi-ts.config.ts`
- **Output**: `sdk/client/` — NEVER edit, fully generated
- **Import types**: `import type { AgentDto } from '@core/sdk/client'`
- **Import endpoints**: `import { getAgent } from '@core/sdk/client'`
- **`@core` alias** = app root (`packages/web/`), defined in `nuxt.config.ts`

SDK client initialized in `plugins/api-client.client.ts` with global auth token injection and error handling. This
plugin runs in every app that extends this layer (including `sysadmin-web`), which is why it lives in a plugin rather
than `app.vue` — extenders supply their own `app.vue`, so anything in the layer's `app.vue` would not run for them.

## FormKit Dynamic Forms

The backend defines form schemas (`FormkitElement[]`), the frontend renders them dynamically.

**Flow**: Backend `AgentConfig.as_form()` → SDK `FormkitElement[]` → `useFormKitTransform().buildFormKitSchema()` →
`<FormKitSchema :schema="schema" />` → rendered form.

**Custom FormKit inputs** (registered in `formkit.config.ts`): `agentSelector`, `chipsInput`,
`knowledgeDatabaseSelector`, `iconSelector`, `localeInput`, `modelSelect`, `tenantSelect`, `vectorStoreInput`.

**Custom validation rules** are registered in the same file under `rules`, with their messages under `messages` (one
entry per locale). The backend attaches a rule to a field via `PrimeVueElement.additional_validation_rules`, which
surfaces as the FormKit node's `validation` string. Cross-field rules read siblings with `node.at('<field_name>')` —
FormKit tracks whatever the rule reads, so it re-runs when that sibling changes too. Such rules are advisory: the API
validates submissions against a JSON Schema and never sees them.

Custom input components receive props via `context` (not Vue props): read from `context.value`, write via
`context.node.input(newValue)`.

**Repeater elements** must be extracted separately and rendered via `<FormKitRepeater>` — the standard `repeater` type
is not supported inside `<FormKitSchema>`.

## Real-Time Events (WebSocket)

Uses **VueUse `useWebSocket`** — NOT Socket.IO:

- Single WebSocket in `composables/thread/useThreadEvents.ts`
- Auth via first message: `ws.send(JSON.stringify({ type: 'auth', token }))`
- New events pushed directly into Pinia-Colada cache via `queryCache.setQueryData()` (no refetch)
- Terminal events (`StopEvent`, `ExceptionEvent`) trigger `queryCache.invalidateQueries()`
- Auto-reconnect: `{ retries: -1, delay: 1000 }`

## Event Display System

26 components in `components/Event/Display/` — one per event type (ChunkEvent, LLMEvent, RetrieverEvent, etc.).

- `EventDisplayBase.vue`: wrapper card (icon, timestamp, raw-data toggle). All event components wrap in this.
- `composables/event/useEventComponent.ts`: `resolveComponentForEvent(event)` maps `_event_name` → Vue component. Falls
  back through `_parent_event_names` for inheritance-based matching. Unknown events → `EventDisplayUnknownEvent`.
- **Event timestamps are in nanoseconds** — divide by `1_000_000` for JavaScript milliseconds.

## i18n

- 4 languages: `de`, `en`, `fr`, `it` (lazy loaded YAML files in `i18n/locales/`)
- Strategy: `prefix` — URLs include locale: `/en/service/agents`, `/de/service/agents`
- Default locale: `en`
- **ALL navigation MUST use `localePath()`**: `router.push(localePath('/service/agents'))` — never bare paths
- Import `useLocalePath` from `'#i18n'` (auto-imported in most contexts)
- All 4 locale files must have matching keys

## PrimeVue Component Exclusions

These PrimeVue components are **excluded from Nuxt auto-import** (registered globally via FormKit bridge instead):

- All form inputs (`wrappedPrimeInputs` in `nuxt.config.ts`): `InputText`, `Select`, `Checkbox`, `DatePicker`, etc.
- `Button`, `Form`, `FormField`, `Chart`

They still work in templates — they're globally registered through `@sfxcode/formkit-primevue` and PrimeVue's own
registration. Don't add manual imports for them.

## Auto-Imports

**Auto-imported** (no explicit import needed):

- All composables from `composables/` and `composables/**/`
- `defineQuery`, `defineMutation`, `useQuery`, `useMutation`, `useQueryCache` (Pinia-Colada)
- `computed`, `ref`, `watch`, `onMounted` (Vue)
- `useRoute`, `useRouter`, `navigateTo` (Nuxt)
- `useI18n` (i18n)
- PrimeVue components (except excluded ones above)

**Needs explicit import**:

- SDK types/endpoints: `import { ... } from '@core/sdk/client'`
- `useLocalePath` from `'#i18n'`
- VueFlow: `import { VueFlow } from '@vue-flow/core'` + CSS imports
- GridStack: `import { GridStack } from 'gridstack'` + CSS import

## Dark Mode

Class-based: `.dark` on `<html>`. Both Tailwind (`darkMode: ['class']`) and PrimeVue theme (`darkModeSelector: '.dark'`)
use this. Use `dark:` Tailwind prefix for dark-mode styles.

## Sysadmin Layout

Tenant administration lives in the `packages/sysadmin-web` layer (its own `sysadmin.vue` layout + pages), used
exclusively by users with the `AIHubSysAdmin` Keycloak realm role. Because that app IS the sysadmin app, its routes are
mounted at `/tenants/...` — there is NO `/sysadmin/` URL prefix. The route shape is independent of the regular
`/[tenant]/service/...` admin pages:

- `/tenants` — tenant list (Active + Orphaned + Unconfigured states)
- `/tenants/[tenant_id]/overview` — metadata edit
- `/tenants/[tenant_id]/roles` — role management within the tenant
- `/tenants/[tenant_id]/users` — user list within the tenant (read-only; user lifecycle managed in Keycloak)

`useTenant()` reads from either `route.params.tenant` (regular routes) or `route.params.tenant_id` (sysadmin routes), so
role/user composables work transparently in both contexts.

## Agent Class vs Agent Instance

The UI strictly separates blueprint from profile:

- **AgentClass** = blueprint/definition (what an agent can do)
- **AgentInstance** = deployed profile (configured instance of a class)
- Route params: `agent_class` and `agent_id` are always separate
- Different composables: `useAgentClasses()` vs `useAgentInstances()`

## Commands

| Command             | What it does                                             |
| ------------------- | -------------------------------------------------------- |
| `pnpm dev`          | Dev server at localhost:3333 (via Nuxt layer in `.app/`) |
| `pnpm lint`         | ESLint + auto-fix (SonarJS, Tailwind, import order)      |
| `pnpm generate-sdk` | Regenerate TypeScript SDK from API OpenAPI spec          |
| `pnpm build`        | Production build (static generation)                     |

`make test` is a no-op — no frontend tests are configured.

## Development Workflow (New Feature)

1. Add API endpoint in `packages/api`, run `pnpm generate-sdk`
2. Create composables in `composables/<domain>/use*.ts` (defineQuery/defineMutation)
3. Create list page: `pages/service/<domain>.vue` with StructuralScreen + StructuralColumn + NuxtPage
4. Create detail hub: `pages/service/<domain>/[param].vue` with SelectButton nav + NuxtPage
5. Create leaf pages: `pages/service/<domain>/[param]/overview.vue` etc. with StructuralColumn
6. Create components: `components/<Domain>/Card.vue`, etc.
7. Add i18n keys to all 4 locale files (`de.yaml`, `en.yaml`, `fr.yaml`, `it.yaml`)

## Essential Files

- Nuxt config: `nuxt.config.ts`
- Nuxt layer entry: `.app/nuxt.config.ts`
- FormKit config (inputs, validation rules, messages): `formkit.config.ts`
- ESLint config: `eslint.config.js`
- Tailwind config: `tailwind.config.mjs`
- PrimeVue theme: `themes/aihub-theme.ts`
- SDK config: `openapi-ts.config.ts`
- SDK output: `sdk/client/` (generated, never edit)
- Auth plugin: `plugins/oidc-client.ts`
- Auth middleware: `middleware/auth.global.ts`
- Layout primitives: `components/Structural/Screen.vue`, `Column.vue`, `Substructure.vue`
- FormKit transform: `composables/form/useFormKitTransform.ts`
- Event resolver: `composables/event/useEventComponent.ts`
- WebSocket events: `composables/thread/useThreadEvents.ts`
- NavItem type: `types/NavItem.ts`
- App entry: `app.vue` (global setup — theme imports, toast/confirm providers)
- SDK client plugin: `plugins/api-client.client.ts` (SDK base URL + auth — runs in this app and all extenders)
- Runtime config plugin: `plugins/0.runtime-config.client.ts` (maps `window.__AIHUB_CONFIG__` into
  `runtimeConfig.public`; runs first due to numeric prefix)
