# aihub_web - Frontend Application

**Purpose**: Nuxt 3 web application. User interface for AI-Hub (agents, processes, threads, admin).

Tech Stack & Paradigms: Nuxt 3 with Vue 3 Composition API. TypeScript strict mode. PrimeVue as primary UI component
library (@primevue/nuxt-module, @primevue/forms, @primeuix/themes). FormKit for form management (@formkit/nuxt,
@sfxcode/formkit-primevue-nuxt). Pinia + Pinia-Colada for state management and reactive data fetching. VueFlow for
node-based workflows (@vue-flow/core, background, controls, minimap). Radix Vue for unstyled primitives. Tailwind CSS +
tailwindcss-primeui. OIDC authentication (oidc-client-ts). Socket.IO client for WebSocket real-time updates. ApexCharts
for data visualization (vue3-apexcharts). Quill rich text editor. GridStack dashboard layouts. Lucide icons
(lucide-vue-next). VueUse utilities (@vueuse/nuxt, router, integrations, math). @hey-api for OpenAPI SDK generation.
i18n (@nuxtjs/i18n). Dagre for graph layouts. ESLint + TypeScript ESLint. Vite for HMR. Client-side only (no SSR).

## Scope Responsibility

Frontend UI, API consumption, real-time updates, state management. NOT backend logic (consume `aihub_api`).

## Folder Structure

```
aihub_web/aihub_web/
├── components/                # Vue components (domain-organized)
│   ├── Agent/                 # Agent UI components
│   ├── Chat/                  # Chat interface
│   ├── Process/               # Process management
│   ├── Thread/                # Thread display
│   └── ...                    # Other domains
├── composables/               # Vue composables (API state wrappers)
│   ├── agent/                 # useAgent(), useAgents()
│   ├── thread/                # useThread(), useThreads()
│   └── ...                    # Other domains
├── pages/                     # File-based routing
│   ├── service/               # Main app pages
│   │   ├── agents/            # Agent pages
│   │   ├── processes/         # Process pages
│   │   └── ...                # Other services
│   └── auth/                  # Auth pages
├── sdk/                       # Generated API client (HeyAPI, type-safe)
├── i18n/                      # Translations (de, en, fr, it)
├── layouts/                   # App layouts
├── middleware/                # Route guards (auth)
└── themes/                    # PrimeVue themes
```

## Tech Stack

**Framework**: Nuxt 3, Vue 3 Composition API, TypeScript (strict mode) **UI**: PrimeVue (components), Tailwind CSS
(styling), PrimeIcons + Iconify **State**: Pinia-Colada (reactive API queries/mutations, NOT global Pinia store)
**API**: Auto-generated SDK (HeyAPI from OpenAPI), Socket.IO (real-time) **Utils**: VueUse, lodash (sub-packages),
date-fns **Charting**: ApexCharts

## Service-Driven Architecture

**Pattern**: Each API service (agent, thread, user, etc.) has:

- **Page**: `/pages/service/<service>.vue` (list view)
- **Nested Pages**: `/pages/service/<service>/<item>.vue` (detail views)
- **Components**: `/components/<Service>/` (domain-specific UI)
- **Composables**: `/composables/<service>/` (API wrappers)

**Example**: Agent service

- List: `/pages/service/agents.vue` → `useAgents()`
- Detail: `/pages/service/agents/agent-[id]-[class].vue` → `useAgent()`
- Components: `/components/Agent/Card.vue`, `/components/Agent/Workflow.vue`
- Composables: `/composables/agent/useAgent.ts`, `/composables/agent/useAgents.ts`

## State Management (Pinia-Colada)

**Query** (GET): Map API to reactive state.

```typescript
export const useRole = defineQuery(() => {
  const route = useRoute()
  const { data: role, isPending: roleIsLoading } = useQuery<RoleResponse>({
    key: () => ['roles', route.params.role_id as string],
    staleTime: minutesToMilliseconds(5),
    query: async () => await getRole({ composable: '$fetch', path: { role_id: route.params.role_id as string } }),
  })
  return { role, roleIsLoading }
})
```

**Mutation** (POST/PUT/DELETE): Update + auto-invalidate queries.

```typescript
export const useUpdateRole = defineMutation(() => {
  const queryCache = useQueryCache()
  const { mutateAsync: updateRoleMutation } = useMutation({
    mutation: async ({ roleId, updatedRole }) => {
      await updateRole({ composable: '$fetch', path: { role_id: roleId }, body: updatedRole })
      queryCache.invalidateQueries({ key: ['roles'] })  // Triggers useRole() refetch
      queryCache.invalidateQueries({ key: ['suite'] })  // Cascade invalidation
    },
  })
  return { updateRole: updateRoleMutation }
})
```

## SDK Generation

**Generate**: `pnpm generate-sdk` (from API OpenAPI spec) **Import types**:
`import type { AgentDto } from '@core/sdk/client'` **Import endpoints**: `import { getAgent } from '@core/sdk/client'`

## i18n

**Required languages**: de (default), en, fr, it **Files**: `/i18n/locales/{de,en,fr,it}.yaml` **Usage**:
`const { t } = useI18n()` → `{{ t('agent.title') }}` **Structure**: Organize by service domain

## Component Patterns

**StructuralColumn**: Standard container with loading, title, close route. Waits for data before rendering children.
**Routing**: `useLocalePath()` for i18n-aware paths, `router.push(localePath('/path'))` **PrimeVue**: Use built-in
components (Button, DataTable, etc.). DO NOT rebuild low-level components. **Tailwind**: Utility classes only. NO custom
CSS classes.

## Development Workflow

1. **Add endpoint**: Create in `aihub_api`, generate SDK (`pnpm generate-sdk`)
2. **Create composables**: Wrap SDK calls in `composables/<service>/use*.ts`
3. **Create pages**: File-based routing in `pages/service/<service>/`
4. **Create components**: Domain-specific in `components/<Service>/`
5. **Add i18n**: Translations in `i18n/locales/*.yaml`
6. **Lint**: `pnpm lint` (ESLint with SonarJS recommended rules)
7. **Run**: `pnpm dev` (http://localhost:3000)

## Coding Standards

**TypeScript**: Strict mode, full typing (NO `any`) **Naming**: `camelCase` (vars/functions), `PascalCase`
(components/types) **Formatting**: Prettier (auto-format) **Linting**: ESLint config:
`/home/user/aihub-core/aihub_web/aihub_web/.eslintrc.cjs`

**Do's**:

- Re-use PrimeVue components
- Use Tailwind utilities
- Keep components domain-focused
- Let Pinia-Colada handle caching

**Don'ts**:

- Build custom low-level components (buttons, inputs, etc.)
- Write inline CSS or custom CSS classes
- Use global Pinia store (use Pinia-Colada queries/mutations)
- Over-abstract components

## Pre-Commit

```bash
pnpm lint  # ESLint + auto-fix
```

## Essential Files

- ESLint config: `/home/user/aihub-core/aihub_web/aihub_web/.eslintrc.cjs`
- Prettier config: `/home/user/aihub-core/aihub_web/aihub_web/.prettierrc`
- Nuxt config: `/home/user/aihub-core/aihub_web/aihub_web/nuxt.config.ts`
- Tailwind config: `/home/user/aihub-core/aihub_web/aihub_web/tailwind.config.mjs`
- SDK client: `/home/user/aihub-core/aihub_web/aihub_web/sdk/client.ts`

## Quick Reference

**Create service UI**:

1. Generate SDK: `pnpm generate-sdk`
2. Create composables: `composables/my_service/useMyService.ts`
3. Create list page: `pages/service/my-service.vue` (uses `useMyServices()`)
4. Create detail page: `pages/service/my-service/[id].vue` (uses `useMyService()`)
5. Create components: `components/MyService/Card.vue`, etc.
6. Add i18n: `i18n/locales/en.yaml` → `myService: { title: "..." }`

**File-based routing**:

- `/pages/foo.vue` → `/foo`
- `/pages/foo/bar.vue` → `/foo/bar`
- `/pages/foo/[id].vue` → `/foo/:id` (dynamic)
- `/pages/foo-[id]-[slug].vue` → `/foo-:id-:slug`

**Access params**: `const route = useRoute()` → `route.params.id`
