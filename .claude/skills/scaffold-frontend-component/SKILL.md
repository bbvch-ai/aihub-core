---
name: scaffold-frontend-component
description: Scaffold a new Vue 3 component following project conventions. Supports card, modal/dialog, list/DataTable, form, empty card, and display patterns with PrimeVue, Tailwind, typed props/emits, and i18n. Use when user says "create a component", "add a Vue component", "scaffold a card", "create a modal", "build a DataTable component", "new form component", or "add a dialog for X". Do NOT use for full list pages with card grids (use scaffold-frontend-page), detail pages with tabs (use scaffold-frontend-subpage), composables only (use scaffold-composable), or PrimeVue docs lookup (use primevue-lookup). Generates component file with correct placement, typed props/emits, and dark mode.
allowed-tools: Read, Write, Edit, Grep, Glob, mcp__primevue__get_component, mcp__primevue__get_component_props, mcp__primevue__get_component_events, mcp__primevue__get_component_slots, mcp__primevue__suggest_component, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Scaffold a New Frontend Component

Generate a new Vue component. Component name and type should be provided via `$ARGUMENTS`.

## Before You Start

1. Read the frontend scope guide: `packages/web/CLAUDE.md`
2. Study existing components for the pattern you need:
   - **Card**: `packages/web/swiss_ai_hub_web/components/Agent/Card.vue`
   - **Empty card**: `packages/web/swiss_ai_hub_web/components/Agent/EmptyCard.vue`
   - **Modal**: `packages/web/swiss_ai_hub_web/components/Agent/CreateModal.vue`
   - **List/Table**: `packages/web/swiss_ai_hub_web/components/Thread/List.vue`
   - **Display**: `packages/web/swiss_ai_hub_web/components/Event/Display/Base.vue`

## Step 1: Determine Component Type

Based on the user's description, identify the component pattern:

| Pattern        | When to Use                                             |
| -------------- | ------------------------------------------------------- |
| **Card**       | Clickable item in a grid, shows summary info            |
| **Empty Card** | Dashed-border placeholder for "add new" action          |
| **Modal**      | Dialog for create/edit forms with v-model visibility    |
| **List/Table** | DataTable with columns, selection, and custom templates |
| **Display**    | Read-only data visualization (charts, stats, details)   |
| **Form**       | FormKit-based input form (standalone or inside modal)   |

## Step 2: Create the Component File

Place in `packages/web/swiss_ai_hub_web/components/{Domain}/{ComponentName}.vue`.

Naming rules:

- **Directory**: Domain/resource name in PascalCase (`Agent/`, `Thread/`, `Process/`)
- **File**: PascalCase descriptive name (`Card.vue`, `CreateModal.vue`, `List.vue`)
- **Auto-import name**: Directory + File = `AgentCard`, `ThreadList`, `ProcessCreateModal`

______________________________________________________________________

### Pattern A: Card Component

```vue
<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
    @click="emit('click', item)"
  >
    <!-- Header row: icon + title + actions -->
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center justify-start gap-2">
        <!-- Icon in circular container -->
        <div class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900">
          <Icon :name="item.icon ?? 'hugeicons:question'" size="1.5em" />
        </div>
        <!-- Title + subtitle -->
        <div>
          <h3 class="font-semibold opacity-80">{{ item.name }}</h3>
          <p class="text-xs font-light opacity-70">{{ item.id }}</p>
        </div>
      </div>
      <!-- Status + actions -->
      <div class="flex items-center gap-2">
        <Tag :value="statusLabel" :severity="statusSeverity" />
        <Button
          v-if="showDelete"
          icon="pi pi-trash"
          severity="secondary"
          text
          rounded
          size="small"
          :loading="isDeleting"
          @click.stop="confirmDelete"
        />
      </div>
    </div>

    <!-- Description -->
    <div>
      <span class="text-xs">{{ item.description }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { <Resource>Dto } from '@core/sdk/client'

const props = withDefaults(defineProps<{
  item: <Resource>Dto
  showDelete?: boolean
}>(), {
  showDelete: true,
})

const emit = defineEmits<{
  click: [item: <Resource>Dto]
  deleted: [id: string]
}>()

const route = useRoute()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

const isActive = computed(() => route.params.id === props.item.id)
</script>
```

**Card Design Token Reference:**

| Element        | Classes                                                            |
| -------------- | ------------------------------------------------------------------ |
| Container      | `rounded-xl border border-surface-200 p-4 dark:border-surface-800` |
| Hover          | `hover:bg-surface-100 hover:dark:bg-surface-800`                   |
| Active         | `bg-surface-100 dark:bg-surface-800`                               |
| Icon container | `rounded-full bg-white p-3 dark:bg-surface-900`                    |
| Title          | `font-semibold opacity-80`                                         |
| Subtitle       | `text-xs font-light opacity-70`                                    |
| Description    | `text-xs`                                                          |

______________________________________________________________________

### Pattern B: Empty Card (Add New)

```vue
<template>
  <div
    class="flex cursor-pointer flex-col justify-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
    @click="emit('add')"
  >
    <div class="flex items-center justify-center">
      <div class="flex items-center justify-center p-3">
        <i class="pi pi-plus-circle text-surface-400" style="font-size: 1.5rem" />
      </div>
    </div>
    <div class="text-center">
      <h3 class="font-medium text-surface-600 dark:text-surface-400">
        {{ t('<resource>.add.title') }}
      </h3>
      <p class="text-sm text-surface-500 dark:text-surface-400">
        {{ t('<resource>.add.description') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const emit = defineEmits<{ add: [] }>()
</script>
```

**Empty Card Design Token Reference:**

| Element     | Classes                                                                            |
| ----------- | ---------------------------------------------------------------------------------- |
| Container   | `rounded-xl border-2 border-dashed border-surface-300 p-4 dark:border-surface-600` |
| Hover       | `hover:border-primary-500 hover:bg-surface-50 dark:hover:bg-surface-800`           |
| Icon        | `pi pi-plus-circle text-surface-400` at `1.5rem`                                   |
| Title       | `font-medium text-surface-600 dark:text-surface-400`                               |
| Description | `text-sm text-surface-500 dark:text-surface-400`                                   |

______________________________________________________________________

### Pattern C: Modal Component

```vue
<template>
  <Dialog
    v-model:visible="visible"
    modal
    :header="t('<resource>.create.title')"
    :style="{ width: '50rem' }"
  >
    <!-- Form content -->
    <div class="flex flex-col gap-4">
      <!-- Form fields using FormKit or PrimeVue inputs -->
    </div>

    <template #footer>
      <Button
        :label="t('common.cancel')"
        severity="secondary"
        text
        @click="visible = false"
      />
      <Button
        :label="t('<resource>.create.submit')"
        :loading="isCreating"
        @click="handleSubmit"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: [id: string]
}>()

const { t } = useI18n()
const { create<Resource>, isCreating } = useCreate<Resource>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const handleSubmit = async () => {
  const result = await create<Resource>({ /* request body */ })
  emit('success', result.id)
  visible.value = false
}
</script>
```

**Modal Pattern Notes:**

- Use `v-model` pattern: prop `modelValue` + emit `update:modelValue`
- Parent uses `<MyModal v-model="isOpen" @success="handleSuccess" />`
- PrimeVue `Dialog` with `modal` prop for backdrop
- Footer buttons: Cancel (secondary, text) + Submit (primary, with loading)

______________________________________________________________________

### Pattern D: List/Table Component

```vue
<template>
  <DataTable
    :value="items"
    size="small"
    selection-mode="single"
    :selection="selectedItem"
    data-key="id"
    @update:selection="(item) => emit('selected', item)"
  >
    <Column field="name" :header="t('<resource>.list.name')" />
    <Column field="status" :header="t('<resource>.list.status')">
      <template #body="{ data }">
        <Tag :value="data.status" :severity="getSeverity(data)" />
      </template>
    </Column>
    <Column field="created_at" :header="t('<resource>.list.created')">
      <template #body="{ data }">
        {{ formatDate(data.created_at) }}
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { <Resource>Dto } from '@core/sdk/client'

const props = defineProps<{
  items: <Resource>Dto[]
}>()

const emit = defineEmits<{
  selected: [item: <Resource>Dto]
}>()

const { t } = useI18n()
const route = useRoute()

const selectedItem = computed(() => {
  return props.items.find(item => item.id === route.params.id)
})
</script>
```

**DataTable Pattern Notes:**

- Always use `size="small"` for compact display
- `selection-mode="single"` for row click selection
- `data-key="id"` for row identity
- Custom column templates via `<template #body="{ data }">`
- Selection synced with route params via computed

______________________________________________________________________

## Step 3: Component Conventions Checklist

Every component MUST follow these rules:

- [ ] **`<script setup lang="ts">`** — Composition API only, no Options API
- [ ] **Typed props**: `defineProps<{ prop: Type }>()` with SDK types from `@core/sdk/client`
- [ ] **Typed emits**: `defineEmits<{ eventName: [arg: Type] }>()`
- [ ] **PrimeVue only**: No raw `<button>`, `<input>`, `<select>` — use PrimeVue equivalents
- [ ] **Tailwind only**: No custom CSS (exception: scoped `:deep()` for PrimeVue overrides)
- [ ] **i18n all text**: `{{ t('key.path') }}` for user-visible text
- [ ] **Dark mode**: Every `bg-*` has a `dark:bg-*` variant, every `text-*` has `dark:text-*`
- [ ] **No unused imports**: Components are auto-imported by Nuxt
- [ ] **Composables for data**: Use `defineQuery`/`defineMutation`, never raw fetch
- [ ] **`useConfirm()` for deletions**: Always confirm destructive actions
- [ ] **`useToast()` for feedback**: Success/error messages via toast

## File Placement Rules

```
components/
├── {Domain}/              # Group by domain
│   ├── Card.vue           # Resource card for grid layouts
│   ├── EmptyCard.vue      # Add-new placeholder
│   ├── CreateModal.vue    # Create dialog
│   ├── EditModal.vue      # Edit dialog
│   └── List.vue           # DataTable list
├── Structural/            # Layout primitives (DO NOT modify)
│   ├── Screen.vue
│   ├── Column.vue
│   └── Substructure.vue
├── Event/                 # Event system
│   └── Display/           # Event display cards
├── Dashboard/             # Dashboard widgets
│   └── Component/         # Widget implementations
├── FormKit/               # Custom FormKit inputs
└── Navigation/            # Nav components
```

## Step 4: Verify

1. Confirm the component auto-import name resolves: `{Domain}/{ComponentName}.vue` becomes `{Domain}{ComponentName}`
2. Verify all PrimeVue components used are auto-imported (not in the FormKit-excluded list — see `primevue-lookup`
   skill)
3. Check dark mode: every `bg-*`, `text-*`, `border-*` class has a `dark:` variant
4. Verify i18n keys exist in ALL 4 locale files for any `t('key')` calls
5. If unsure about PrimeVue component props/events, use `mcp__primevue__get_component_props` to verify

## Examples

**Input**: `$ARGUMENTS = "Pipeline Card"`

**Output**: `packages/web/swiss_ai_hub_web/components/Pipeline/Card.vue` -- Pattern A card component with `PipelineDto`
typed props, click emit, active state from route params, icon + title + status Tag layout.

**Input**: `$ARGUMENTS = "Connector CreateModal"`

**Output**: `packages/web/swiss_ai_hub_web/components/Connector/CreateModal.vue` -- Pattern C modal with
`v-model:visible`, `useCreateConnector()` mutation, cancel/submit footer buttons, and `success` emit.

**Input**: `$ARGUMENTS = "Knowledge List table"`

**Output**: `packages/web/swiss_ai_hub_web/components/Knowledge/List.vue` -- Pattern D DataTable with `KnowledgeDto[]`
prop, single selection mode, custom column templates for status and dates.

**Auto-import name resolution**: Directory + File = component name. `Pipeline/Card.vue` becomes `<PipelineCard />`,
`Connector/CreateModal.vue` becomes `<ConnectorCreateModal />`.

## Troubleshooting

| Problem                                 | Cause                                     | Fix                                                                                                                    |
| --------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Component not auto-imported             | Wrong directory or naming                 | Must be under `components/` in PascalCase directory, file must be PascalCase `.vue`                                    |
| Raw HTML elements in template           | Not using PrimeVue                        | Replace `button` with `Button`, `input` with FormKit input, `select` with FormKit Select                               |
| Dark mode colors broken                 | Missing `dark:` variants                  | Every `bg-*`, `text-*`, `border-*` class needs a corresponding `dark:` variant                                         |
| Props not type-safe                     | Using `defineProps({})` object syntax     | Use generic syntax: `defineProps<{ item: ResourceDto }>()` with SDK types                                              |
| FormKit-wrapped component not rendering | Imported from PrimeVue instead of FormKit | 24 components excluded from PrimeVue auto-import — see `primevue-lookup` skill for full list or check `nuxt.config.ts` |
| Delete button triggers card click       | Missing `@click.stop`                     | Add `.stop` modifier to prevent event bubbling: `@click.stop="confirmDelete"`                                          |
