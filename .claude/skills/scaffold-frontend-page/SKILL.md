---
name: scaffold-frontend-page
description: Scaffold a new Nuxt 3 list page with StructuralScreen/Column layout, Pinia-Colada data fetching, card grid, create modal, and NuxtPage outlet for nested detail routes. Use when user says "create a new page", "scaffold a frontend page", "add a list page", "new resource page", "generate a Vue page for X", or "build a page like agents/roles". Do NOT use for detail pages with tabs (use scaffold-frontend-subpage), individual components (use scaffold-frontend-component), or composables only (use scaffold-composable). Generates page + card + i18n following agents.vue and roles.vue patterns.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, mcp__nuxt__get-documentation-page, mcp__nuxt__list-documentation-pages, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Scaffold a New Frontend Page

Generate a list page for a new resource. The resource name should be provided via `$ARGUMENTS`.

## Before You Start

1. Read the frontend scope guide: `aihub_web/CLAUDE.md`
2. Study these reference pages:
   - Simple list: `aihub_web/aihub_web/pages/service/roles.vue`
   - Complex list with grouping: `aihub_web/aihub_web/pages/service/agents.vue`
   - Knowledge list: `aihub_web/aihub_web/pages/service/knowledge.vue`

## Step 1: Check SDK Availability

Search `aihub_web/aihub_web/sdk/client/` for the resource's SDK functions and DTO types. If they don't exist, warn the
user to run `/generate-sdk` first.

Look up the actual DTO type name in `aihub_web/aihub_web/sdk/client/types.gen.ts` — types may be named
`{Resource}Response`, `Full{Resource}Dto`, or `{Resource}Dto` depending on the API schema.

## Step 2: Create Composables

If composables don't exist yet, create them first using the patterns from `/scaffold-composable`. At minimum you need:

- `composables/{resource}/use{Resource}s.ts` — List query
- `composables/{resource}/useCreate{Resource}.ts` — Create mutation (if applicable)

## Step 3: Create the List Page

Create `aihub_web/aihub_web/pages/service/{resource}s.vue`:

```vue
<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('<resource>.title')"
      :loading="<resource>sAreLoading"
    >
      <div class="flex flex-col gap-2">
        <!-- Create button (top right) -->
        <div class="flex w-full justify-end">
          <Button
            :label="t('<resource>.create_new')"
            icon="pi pi-plus"
            @click="createModalOpen = true"
          />
        </div>

        <!-- Card grid -->
        <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
          <<Resource>Card
            v-for="item in <resource>s"
            :key="item.id"
            :<resource>="item"
            @click="() => toDetail(item)"
          />
        </div>
      </div>

      <!-- Create modal -->
      <Dialog
        v-model:visible="createModalOpen"
        modal
        :header="t('<resource>.create_new')"
      >
        <<Resource>Create @close="createModalOpen = false" />
      </Dialog>
    </StructuralColumn>

    <!-- Nested detail page outlet -->
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { <Resource>Dto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { <resource>s, <resource>sAreLoading } = use<Resource>s()

const createModalOpen = ref(false)

const toDetail = (item: <Resource>Dto) => {
  router.push(localePath(`/service/<resource>s/${item.id}/overview`))
}
</script>
```

### Key Structural Elements

1. **`<StructuralScreen>`**: Top-level wrapper. Provides `h-[calc(100vh-50px)]` viewport,
   `bg-surface-50 dark:bg-surface-950`, horizontal flex at `2xl:`.
2. **`<StructuralColumn>`**: Card container with rounded-3xl, loading progress bar, title/close button. Props: `title`,
   `loading`, `size`, `closeRoute`, `childColumn`.
3. **`<NuxtPage />`**: MUST be placed as a sibling of StructuralColumn inside StructuralScreen. This renders nested
   detail routes as a second column.
4. **Card grid**: Use `grid grid-cols-2 gap-4 2xl:grid-cols-2` for consistent card layout.
5. **Create button**: Top-right aligned with `flex w-full justify-end`.
6. **Navigation**: Always use `localePath()` for i18n-aware routing.

## Step 4: Create Card Component

Create `aihub_web/aihub_web/components/{Resource}/Card.vue` following this exact pattern:

```vue
<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
    @click="emit('click', <resource>)"
  >
    <!-- Header: Icon + Title + Status -->
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center justify-start gap-2">
        <div class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900">
          <Icon :name="icon" size="1.5em" />
        </div>
        <div>
          <h3 class="font-semibold opacity-80">{{ <resource>.name }}</h3>
          <p class="text-xs font-light opacity-70">{{ <resource>.id }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Tag :value="statusLabel" :severity="statusSeverity" />
      </div>
    </div>

    <!-- Description -->
    <div>
      <span class="text-xs">{{ <resource>.description }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { <Resource>Dto } from '@core/sdk/client'

const props = defineProps<{
  <resource>: <Resource>Dto
}>()

const emit = defineEmits<{
  click: [<resource>: <Resource>Dto]
}>()

const route = useRoute()
const { t } = useI18n()

const isActive = computed(() => {
  return route.params.<resource>_id === props.<resource>.id
})
</script>
```

### Card Design Rules

- **Container**: `rounded-xl border border-surface-200 p-4` with hover and dark mode variants
- **Active state**: `bg-surface-100 dark:bg-surface-800` when route matches
- **Icon container**: `rounded-full bg-white p-3 dark:bg-surface-900` with `Icon size="1.5em"`
- **Title**: `font-semibold opacity-80`
- **Subtitle**: `text-xs font-light opacity-70`
- **Description**: `text-xs`
- **Status**: PrimeVue `Tag` with severity (`success`, `danger`, `secondary`)
- **Delete button**: `Button icon="pi pi-trash" severity="secondary" text rounded size="small"` with `@click.stop`

## Step 5: Add i18n Keys

Add translation keys in all 4 locale files (`aihub_web/aihub_web/i18n/locales/{de,en,fr,it}.yaml`):

```yaml
{resource}:
  title: "{Resource}s"
  create_new: "Create {Resource}"
  list:
    empty: "No {resource}s found"
  delete:
    title: "Delete {Resource}"
    confirmMessage: "Are you sure you want to delete this {resource}?"
    button: "Delete"
    success: "{Resource} deleted successfully"
    error: "Failed to delete {resource}"
    cancel: "Cancel"
```

## Step 6: Verify

1. Check Nuxt file-based routing resolves the new page: filename must be `{resource}s.vue` (plural) in `pages/service/`
2. Verify `NuxtPage` renders nested routes: create a placeholder `pages/service/{resource}s/` directory if detail routes
   are planned
3. Check sidebar registration: `useSuite()` → `useApps()` fetches service definitions from the API — the new resource
   may need API-side registration
4. Verify i18n keys exist in ALL 4 locale files (`de.yaml`, `en.yaml`, `fr.yaml`, `it.yaml`)
5. If unsure about Nuxt routing conventions, use `mcp__nuxt__get-documentation-page` with
   `/docs/4.x/guide/directory-structure/pages` or `mcp__context7__query-docs` with library `/websites/nuxt`

## Key Conventions

- **PrimeVue components only**: `Button`, `Tag`, `Dialog`, `DataTable` -- never raw HTML for interactive elements
- **Tailwind only**: No custom CSS (exception: scoped `:deep()` for PrimeVue overrides)
- **SDK types for props**: Import from `@core/sdk/client`, never define manually
- **i18n all text**: `{{ t('key.path') }}` for everything user-visible
- **Pinia-Colada**: `defineQuery`/`defineMutation` -- never raw fetch or global stores
- **`useLocalePath()`**: Always for navigation -- `router.push(localePath('/path'))`
- **`useConfirm()` + `useToast()`**: For delete confirmations and success/error messages

## Examples

**Input**: `$ARGUMENTS = "pipeline"`

**Output files created**:

1. `aihub_web/aihub_web/pages/service/pipelines.vue` -- List page with card grid
2. `aihub_web/aihub_web/components/Pipeline/Card.vue` -- Resource card component
3. `aihub_web/aihub_web/composables/pipeline/usePipelines.ts` -- List query composable
4. `aihub_web/aihub_web/composables/pipeline/useCreatePipeline.ts` -- Create mutation composable
5. i18n keys added to all 4 locale files (`de.yaml`, `en.yaml`, `fr.yaml`, `it.yaml`)

**Input**: `$ARGUMENTS = "connector"`

**Output**: Same structure with `connector` replacing `pipeline` -- `connectors.vue`, `Connector/Card.vue`,
`useConnectors.ts`, etc.

## Troubleshooting

| Problem                          | Cause                            | Fix                                                                         |
| -------------------------------- | -------------------------------- | --------------------------------------------------------------------------- |
| SDK types not found for resource | SDK not generated yet            | Tell user to run `/generate-sdk` first                                      |
| Page not appearing in sidebar    | Not registered in service config | Check `useSuite()` / `useApps()` API service definitions                    |
| Cards not rendering              | Composable returns empty array   | Verify SDK endpoint URL and check browser Network tab for API errors        |
| i18n keys showing raw paths      | Missing translation keys         | Ensure keys were added to ALL 4 locale files (`de`, `en`, `fr`, `it`)       |
| Route not matching / 404         | File naming mismatch             | Verify filename matches Nuxt file-based routing: `{resource}s.vue` (plural) |
| Dark mode broken on cards        | Missing `dark:` variant          | Every `bg-*` class must have a corresponding `dark:bg-*` class              |
