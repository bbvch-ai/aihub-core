---
name: scaffold-frontend-subpage
description: Scaffold a detail wrapper with SelectButton tab navigation and nested tab subpages. Creates the tab bar, NavItem routing, StructuralColumn content, and overview tab following the [agent_class]-[agent_id].vue pattern. Use when user says "add a detail page", "create subpage with tabs", "scaffold detail view", "add tab navigation", "create nested route page", or "build a detail page like agents". Do NOT use for list pages (use scaffold-frontend-page), individual components (use scaffold-frontend-component), or composables only (use scaffold-composable). Generates wrapper + tab pages + composable + i18n.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, mcp__nuxt__get-documentation-page, mcp__nuxt__list-documentation-pages, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Scaffold a Frontend Subpage (Detail + Tabs)

Generate a detail wrapper page with tab navigation and tab content pages. The resource name should be provided via
`$ARGUMENTS`.

## Before You Start

1. Read the frontend scope guide: `packages/web/CLAUDE.md`
2. Study these reference files:
   - Detail wrapper with tabs: `packages/web/aihub_web/pages/service/agents/[agent_class]-[agent_id].vue`
   - Tab content page: `packages/web/aihub_web/pages/service/agents/[agent_class]-[agent_id]/overview.vue`
   - Another wrapper: `packages/web/aihub_web/pages/service/threads/[thread_id].vue`
   - NavItem type: `packages/web/aihub_web/types/NavItem.ts`

## Architecture: How Nested Routing Works

```
pages/service/{resource}s.vue           <- List page (has NuxtPage outlet)
  pages/service/{resource}s/
    [{resource}_id].vue                 <- Detail WRAPPER (tab bar + NuxtPage)
      overview.vue                      <- Tab content page
      configuration.vue                 <- Tab content page
      other-tab.vue                     <- Tab content page
```

The list page renders as the left column. When a user clicks an item, the detail wrapper renders as a second column via
`NuxtPage`. The wrapper shows the tab bar and renders the active tab's content via its own nested `NuxtPage`.

## Step 1: Create Composable (if needed)

Ensure a single-item composable exists:

```
composables/{resource}/use{Resource}.ts  <- Fetches by route param ID
```

Follow the pattern from `composables/agent/useAgentInstance.ts`:

```typescript
export const use<Resource> = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('<resource>_id')

  const { data: <resource>, isPending: <resource>IsLoading } = useQuery<Full<Resource>Dto>({
    key: () => ['<resource>s', route.params.<resource>_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      return await get<Resource>({
        composable: '$fetch',
        path: { <resource>_id: route.params.<resource>_id as string },
      })
    },
  })
  return { <resource>, <resource>IsLoading }
})
```

## Step 2: Create the Detail Wrapper

Create `packages/web/aihub_web/pages/service/{resource}s/[{resource}_id].vue`:

```vue
<template>
  <div class="flex flex-col gap-2">
    <SelectButton
      v-if="navItems"
      :model-value="activeNavItem"
      :options="navItems"
      data-key="key"
      option-label="name"
      size="small"
      @update:model-value="toNavItem"
    />
    <div class="flex gap-8">
      <NuxtPage />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NavItem } from '@core/types/NavItem'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()

const { <resource> } = use<Resource>()

const subPath = (path: string) => {
  return `/service/<resource>s/${route.params.<resource>_id}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => {
  return [
    { name: t('<resource>.navigation.overview'), key: 'overview', path: subPath('overview'), isActive: isActive('overview') },
    { name: t('<resource>.navigation.configuration'), key: 'configuration', path: subPath('configuration'), isActive: isActive('configuration') },
    // Add more tabs as needed
  ]
})

const toNavItem = (navItem: NavItem | null) => {
  if (navItem) {
    router.push(localePath(navItem.path))
  }
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
```

### Key Patterns in the Wrapper

1. **`SelectButton` for tabs** — NOT PrimeVue `TabView`. Tabs are route-based, not component-based.
2. **`NavItem` type**: `{ name: string, key: string, path: string, isActive: () => boolean }`
3. **`subPath()` helper**: Builds child route paths from current params.
4. **`isActive()` helper**: Returns a function that checks `route.path.startsWith(localizedPath)`.
5. **`NuxtPage`**: Renders the active tab content as a nested route.
6. **Conditional tabs**: Tabs can be added conditionally based on resource state (e.g., show chat tab only if
   `is_conversational`).

### Dynamic Route Params

For compound identifiers (like agents), use `[agent_class]-[agent_id].vue`:

```typescript
const subPath = (path: string) => {
  return `/service/agents/${route.params.agent_class}-${route.params.agent_id}/${path}`
}
```

For simple identifiers, use `[{resource}_id].vue`:

```typescript
const subPath = (path: string) => {
  return `/service/<resource>s/${route.params.<resource>_id}/${path}`
}
```

## Step 3: Create Tab Content Pages

Create tab pages in `packages/web/aihub_web/pages/service/{resource}s/[{resource}_id]/`:

### Overview Tab (`overview.vue`)

```vue
<template>
  <StructuralColumn
    :title="<resource>?.name"
    close-route="/service/<resource>s"
    :loading="<resource>IsLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <!-- Description -->
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ <resource>?.description }}
      </span>

      <!-- Detail fields in a grid -->
      <Panel>
        <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">{{ t('<resource>.overview.name') }}</span>
            <Tag :value="<resource>?.name" severity="secondary" />
          </div>
          <div class="flex flex-col items-start gap-2">
            <span class="font-semibold">{{ t('<resource>.overview.status') }}</span>
            <Tag :value="statusLabel" :severity="statusSeverity" />
          </div>
          <!-- More fields... -->
        </div>
      </Panel>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { <resource>, <resource>IsLoading } = use<Resource>()
const { t } = useI18n()
</script>
```

### Key Patterns in Tab Pages

1. **`<StructuralColumn>`**: Every tab page wraps content in a StructuralColumn.
2. **`close-route`**: Points back to the list page (e.g., `/service/{resource}s`). Shows an X button.
3. **`size="large"`**: Most detail pages use `large` (1440px). Use `normal` (920px) for simpler content.
4. **`:loading`**: Pass the composable's loading state. Content waits for loading to complete.
5. **`childColumn`**: Set to `true` if this is a nested subpage within another column.
6. **Field display pattern**: `font-semibold` label + `Tag severity="secondary"` value, in a grid.

## Step 4: Add i18n Keys

```yaml
{resource}:
  navigation:
    overview: "Overview"
    configuration: "Configuration"
    # Add more tabs
  overview:
    name: "Name"
    status: "Status"
    # Add more field labels
```

## Step 5: Create File Structure

Final directory structure:

```
packages/web/aihub_web/
├── pages/service/
│   ├── {resource}s.vue                    <- List page (from /scaffold-frontend-page)
│   └── {resource}s/
│       └── [{resource}_id].vue            <- Detail wrapper (tab bar)
│           ├── overview.vue               <- Overview tab
│           ├── configuration.vue          <- Config tab (optional)
│           └── other-tab.vue              <- More tabs as needed
└── composables/{resource}/
    ├── use{Resource}s.ts                  <- List query
    └── use{Resource}.ts                   <- Single item query (route param)
```

## Step 6: Verify

1. Check the nested route resolves: `pages/service/{resource}s/[{resource}_id].vue` must be inside a directory matching
   the parent list page filename (`{resource}s/`)
2. Verify tab navigation works: each NavItem `path` must match a `.vue` file in the `[{resource}_id]/` directory
3. Verify `isActive()` returns a closure (function returning boolean), not a boolean value
4. Verify i18n keys exist in ALL 4 locale files for navigation labels and field labels
5. If unsure about Nuxt nested routing, use `mcp__nuxt__get-documentation-page` with
   `/docs/4.x/guide/directory-structure/pages` or `mcp__context7__query-docs` with library `/websites/nuxt`

## Key Conventions

- **Tabs are routes, not components**: Each tab is a separate `.vue` file in the nested directory
- **SelectButton, not TabView**: Tab navigation uses PrimeVue `SelectButton` with `NavItem` type
- **Loading gates content**: StructuralColumn doesn't render children until `loading === false`
- **Close navigates to list**: `close-route` on StructuralColumn always points back to the parent list
- **Composable reuse**: The same `use{Resource}()` composable is shared between wrapper and tab pages (Pinia-Colada
  deduplicates the query)

## Examples

**Input**: `$ARGUMENTS = "pipeline"`

**Output files created**:

1. `packages/web/aihub_web/pages/service/pipelines/[pipeline_id].vue` -- Detail wrapper with tab bar
2. `packages/web/aihub_web/pages/service/pipelines/[pipeline_id]/overview.vue` -- Overview tab
3. `packages/web/aihub_web/pages/service/pipelines/[pipeline_id]/configuration.vue` -- Configuration tab
4. `packages/web/aihub_web/composables/pipeline/usePipeline.ts` -- Single-item query composable
5. i18n keys added for navigation labels and field labels in all 4 locales

**Input**: `$ARGUMENTS = "connector with tabs: overview, settings, logs"`

**Output**: Wrapper at `[connector_id].vue` plus three tab files (`overview.vue`, `settings.vue`, `logs.vue`) with
NavItem entries for each tab.

## Troubleshooting

| Problem                                    | Cause                               | Fix                                                                                             |
| ------------------------------------------ | ----------------------------------- | ----------------------------------------------------------------------------------------------- |
| Tab content not rendering                  | Missing `NuxtPage` in wrapper       | Ensure wrapper template has `NuxtPage` inside the flex container                                |
| Tab bar not highlighting active tab        | `isActive()` path mismatch          | Verify `subPath()` builds the correct URL with `route.params` values                            |
| Detail page not appearing as second column | Parent list page missing `NuxtPage` | Ensure the parent list page (`{resource}s.vue`) has `NuxtPage` as sibling of `StructuralColumn` |
| Route params undefined                     | Filename bracket syntax wrong       | Dynamic route file must be named `[{resource}_id].vue` with square brackets                     |
| Composable fetches on every tab switch     | Not using `staleTime`               | Set `staleTime: minutesToMilliseconds(5)` in the query options                                  |
| Close button navigates to wrong page       | Incorrect `close-route` prop        | Set `close-route="/service/{resource}s"` (plural, pointing to list page)                        |
