---
name: design-system
description: Reference guide for the Swiss AI Hub design system covering colors (aihub-theme.ts surface scale), typography, spacing, component patterns, dark mode, layout (StructuralScreen/Column), borders, radius, icons, buttons, severity mapping, confirmations, toasts, forms, charts, and panels. Use when user says "what colors to use", "design system", "Tailwind classes for cards", "dark mode classes", "spacing values", "which border radius", "typography scale", "layout structure", "icon sizes", "how to style X", "button pattern", "severity mapping", "which icon set", "chart pattern", "dashboard widget", or before building any UI to ensure visual consistency. Do NOT use for PrimeVue component API lookup (use primevue-lookup), scaffolding new components (use scaffold-frontend-component), or frontend code audits (use audit-frontend). Returns exact Tailwind classes and design tokens from the actual codebase.
allowed-tools: Read, Grep, Glob, mcp__context7__resolve-library-id, mcp__context7__query-docs, mcp__primevue__get_component_tokens, mcp__primevue__get_component_styles, mcp__playwright__browser_navigate, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_snapshot
---

# Swiss AI Hub Design System Reference

Look up design system information. Topic or question via `$ARGUMENTS` (e.g., "colors", "spacing", "card pattern", "dark
mode", "typography", "button", "severity", "icon", "chart").

If unsure about a Tailwind utility class, use `mcp__context7__query-docs` with library ID `/websites/v3_tailwindcss` to
look up current Tailwind CSS documentation.

## Design Philosophy

1. **Neutral palette**: No bright brand colors. Primary maps to surface/stone scale.
2. **Content-first**: Minimal chrome, maximum space for data.
3. **Dark mode as first-class**: Every `bg-*`, `text-*`, `border-*` MUST have a `dark:` variant.
4. **PrimeVue + Tailwind**: Components from PrimeVue, all styling via Tailwind utilities. No custom CSS.
5. **Generous radius**: `rounded-xl` (cards), `rounded-3xl` (columns), `rounded-full` (icons/avatars).
6. **Information density**: 14px base font, `text-xs` for metadata, compact but readable.

______________________________________________________________________

## Color Palette

**Theme file**: `packages/web/swiss_ai_hub_web/themes/aihub-theme.ts`

### Surface Scale (identical in light and dark mode)

| Token         | Hex       | Actual Usage in Codebase                                  |
| ------------- | --------- | --------------------------------------------------------- |
| `surface-50`  | `#f9f9f9` | StructuralScreen bg (light), EmptyCard hover bg (light)   |
| `surface-100` | `#ececec` | Active card bg (light), nav item hover (light)            |
| `surface-200` | `#e3e3e3` | Card borders (light), active nav bg (light)               |
| `surface-300` | `#cdcdcd` | Empty card dashed border (light), FormKit repeater border |
| `surface-400` | `#b4b4b4` | `pi pi-plus-circle` icon color, empty card title (dark)   |
| `surface-500` | `#9b9b9b` | Nav group labels, muted descriptions, KPI agent name      |
| `surface-600` | `#676767` | Empty card title (light), repeater legend (dark)          |
| `surface-700` | `#4e4e4e` | Nav items text (light), repeater legend (light)           |
| `surface-800` | `#333333` | Card borders (dark), active card bg (dark), hover bg dark |
| `surface-850` | `#262626` | Custom token: chat bubbles, selected table rows (dark)    |
| `surface-900` | `#171717` | StructuralColumn bg (dark), icon container bg (dark)      |
| `surface-950` | `#0d0d0d` | StructuralScreen bg (dark), nav sidebar bg (dark)         |

### Primary Color (Monochromatic)

Primary maps directly to stone: light `{stone.950}`, dark `{stone.50}`. No brand accent color.

### Semantic Colors (PrimeVue `severity` prop only)

| Severity    | States in Our Codebase                                                  |
| ----------- | ----------------------------------------------------------------------- |
| `success`   | Online, active, completed, score >= 0.8, guard accepted, last seen < 1h |
| `danger`    | Offline, failed, deleted, score < 0.4, guard rejected, last seen > 30d  |
| `warn`      | Pending, attention needed, score 0.4-0.6, last seen 7-30d               |
| `info`      | Informational, score 0.6-0.8, last seen 1-7d                            |
| `secondary` | Neutral metadata, agent IDs, feature tags, access rules, model details  |
| `contrast`  | Rare, only Role Card header emphasis                                    |

### Dark Mode

Selector: `.dark` CSS class. Config: `darkMode: ['class']` (Tailwind), `darkModeSelector: '.dark'` (PrimeVue).

**Rule**: Every `bg-*` MUST have a `dark:bg-*`. Every `text-surface-*` MUST have a `dark:text-surface-*`.

______________________________________________________________________

## Background Patterns (from real components)

| Context                    | Light                  | Dark                        | Source Component        |
| -------------------------- | ---------------------- | --------------------------- | ----------------------- |
| Screen bg                  | `bg-surface-50`        | `dark:bg-surface-950`       | Structural/Screen.vue   |
| Column/card bg             | `bg-white`             | `dark:bg-surface-900`       | Structural/Column.vue   |
| Icon container bg          | `bg-white`             | `dark:bg-surface-900`       | Agent/Card.vue          |
| Active card / selected row | `bg-surface-100`       | `dark:bg-surface-800`       | Agent/Card.vue `:class` |
| Card hover                 | `hover:bg-surface-100` | `hover:dark:bg-surface-800` | Agent/Card.vue          |
| Empty card hover           | `hover:bg-surface-50`  | `dark:hover:bg-surface-800` | Agent/EmptyCard.vue     |
| Nav item hover             | `hover:bg-surface-100` | `dark:hover:bg-surface-950` | Navigation/Left.vue     |
| Nav item active            | `bg-surface-200`       | `dark:bg-surface-900`       | Navigation/Left.vue     |

______________________________________________________________________

## Typography (from real components)

**Base**: 14px (`packages/web/swiss_ai_hub_web/assets/css/main.css`), system font stack.

### Hierarchy as Actually Used

| Class + Weight                         | Where Used                                        |
| -------------------------------------- | ------------------------------------------------- |
| `text-[12rem] font-medium opacity-70`  | Dashboard KPI number (Number.vue)                 |
| `text-2xl font-bold`                   | StructuralColumn `h2` title (default)             |
| `text-xl font-bold`                    | StructuralColumn `h3` title (`childColumn: true`) |
| `text-lg font-bold opacity-80`         | Dashboard KPI title (Number.vue)                  |
| `text-sm font-medium text-surface-900` | Nav sidebar title (Navigation/Left.vue)           |
| `font-semibold opacity-80`             | Card title (Agent/Card.vue `h3`)                  |
| `text-xs font-light opacity-70`        | Card subtitle / ID line (Agent/Card.vue `p`)      |
| `text-xs font-medium text-surface-500` | Nav group label (Navigation/Left.vue)             |
| `text-xs`                              | Card description body (Agent/Card.vue)            |
| `text-sm font-medium`                  | Form field labels (knowledge forms, role forms)   |
| `font-medium text-surface-600`         | Empty card title (EmptyCard.vue, light)           |
| `text-sm text-surface-500`             | Empty card description, muted help text           |
| `font-semibold`                        | Panel header text (Event Display), field labels   |
| `text-surface-500`                     | Dashboard agent name, KPI source label            |

### Text Colors as Actually Used

| Classes                                  | Where                                           |
| ---------------------------------------- | ----------------------------------------------- |
| `text-surface-900 dark:text-white`       | Nav sidebar title                               |
| `text-surface-700 dark:text-surface-200` | Nav item text, secondary body text              |
| `text-surface-600 dark:text-surface-400` | Empty card title, form labels                   |
| `text-surface-500 dark:text-surface-400` | Muted descriptions, nav group labels, help text |
| `text-surface-500 dark:text-surface-500` | Nav group labels (same in both modes)           |
| `text-surface-400`                       | `pi pi-plus-circle` icons, disabled text        |

______________________________________________________________________

## Spacing (from real components)

| Class       | Where Actually Used                                               |
| ----------- | ----------------------------------------------------------------- |
| `gap-2`     | Card header icon+title group, nav items vertical, tight groups    |
| `gap-3`     | Card body vertical spacing, StructuralColumn outer wrapper        |
| `gap-4`     | Card header justify-between row, grid items, form field groups    |
| `gap-5`     | Nav sidebar sections, nav item groups                             |
| `gap-6`     | Dialog form content, stepper form sections, role form fields      |
| `gap-8`     | StructuralScreen columns horizontal (2xl:flex-row), page sections |
| `p-3`       | Icon circular container padding                                   |
| `p-4`       | Card padding, empty card padding, pagination footer               |
| `p-6`       | StructuralColumn content padding                                  |
| `px-8 pt-8` | StructuralScreen top slot padding                                 |
| `py-4`      | Stepper step panel content                                        |
| `py-8`      | Dialog loading/empty state centering                              |

______________________________________________________________________

## Border Radius and Borders (from real components)

| Element          | Radius         | Border Classes                                                      |
| ---------------- | -------------- | ------------------------------------------------------------------- |
| Resource card    | `rounded-xl`   | `border border-surface-200 dark:border-surface-800`                 |
| Empty card       | `rounded-xl`   | `border-2 border-dashed border-surface-300 dark:border-surface-600` |
| StructuralColumn | `rounded-3xl`  | None (bg-white provides contrast)                                   |
| Icon container   | `rounded-full` | None                                                                |
| Nav item         | `rounded-lg`   | None                                                                |
| FormKit repeater | `rounded-lg`   | `border border-surface-300 dark:border-surface-600`                 |

______________________________________________________________________

## Layout System (from Structural/Screen.vue and Column.vue)

### StructuralScreen Template

```vue
<div class="flex h-[calc(100vh-50px)] w-full flex-col justify-start gap-2 overflow-auto bg-surface-50 dark:bg-surface-950">
  <div class="px-8 pt-8"><slot name="top" /></div>
  <div class="flex flex-col justify-start gap-8 px-8 2xl:flex-row"><slot /></div>
</div>
```

### StructuralColumn Template

```vue
<div class="relative flex flex-col gap-3 max-2xl:w-full">
  <div :class="['overflow-hidden rounded-3xl bg-white dark:bg-surface-900 max-2xl:w-full', sizeClass]">
    <ProgressBar v-if="loading" mode="indeterminate" style="height: 2px" />
    <div v-else class="h-[2px] w-full" />
    <div v-if="!loading" class="p-6">
      <div class="flex items-center justify-between font-bold">
        <h2 v-if="!childColumn" class="text-2xl">{{ title }}</h2>
        <h3 v-else class="text-xl">{{ title }}</h3>
        <i v-if="closeRoute" class="pi pi-times cursor-pointer text-xl" @click="close" />
      </div>
      <Divider />
      <slot />
    </div>
  </div>
</div>
```

Sizes: `small` = `2xl:w-[680px]`, `normal` = `2xl:w-[920px]`, `large` = `2xl:w-[1440px]`.

### Navigation Sidebar (Navigation/Left.vue)

Fixed `w-[260px]`, grouped nav items. Spacer div `min-w-[260px]` prevents content overlap.

### Responsive Pattern

- `< 2xl`: Single column, `max-2xl:w-full`
- `>= 2xl (1536px)`: Multi-column `2xl:flex-row`
- Grids: `grid-cols-2 gap-4 xl:grid-cols-4` (info panels), `grid-cols-1 lg:grid-cols-2` (cards)

______________________________________________________________________

## Component Patterns (from real components)

### Card (Agent/Card.vue)

```vue
<div
  class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
  :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
  @click="emit('click', item)"
>
  <div class="flex items-center justify-between gap-4">
    <div class="flex items-center justify-start gap-2">
      <div class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900">
        <Icon :name="item.icon" size="1.5em" />
      </div>
      <div>
        <h3 class="font-semibold opacity-80">{{ item.name }}</h3>
        <p class="text-xs font-light opacity-70">{{ item.class }} / {{ item.id }}</p>
      </div>
    </div>
    <div class="flex items-center gap-2">
      <Tag :severity="item.is_online ? 'success' : 'danger'" :value="statusLabel" />
      <Button icon="pi pi-trash" severity="secondary" text rounded size="small" @click.stop="confirmDelete" />
    </div>
  </div>
  <div>
    <span class="text-xs">{{ item.description }}</span>
    <div class="pt-2">
      <Tag v-if="item.is_conversational" :value="t('agent.can_chat')" severity="secondary" icon="pi pi-comments" />
    </div>
  </div>
</div>
```

### Empty Card (Agent/EmptyCard.vue)

```vue
<div
  class="flex cursor-pointer flex-col justify-center gap-3 rounded-xl border-2 border-dashed border-surface-300 p-4 hover:border-primary-500 hover:bg-surface-50 dark:border-surface-600 dark:hover:bg-surface-800"
  @click="handleAdd"
>
  <div class="flex items-center justify-center">
    <div class="flex items-center justify-center p-3">
      <i class="pi pi-plus-circle text-surface-400" style="font-size: 1.5rem" />
    </div>
  </div>
  <div class="text-center">
    <h3 class="font-medium text-surface-600 dark:text-surface-400">{{ t('resource.add.title') }}</h3>
    <p class="text-sm text-surface-500 dark:text-surface-400">{{ t('resource.add.description') }}</p>
  </div>
</div>
```

### Dialog (Agent/CreateModal.vue pattern)

Width: always `{ width: '50rem' }`. Three states: loading (`ProgressSpinner`), empty (`text-surface-500`), content.

```vue
<Dialog v-model:visible="visible" modal :header="t('resource.create.title')" :style="{ width: '50rem' }" :closable="!isCreating">
  <div class="flex flex-col gap-6"><!-- loading/empty/content states --></div>
  <template #footer>
    <Button :label="t('common.cancel')" severity="secondary" @click="visible = false" />
    <Button :label="t('resource.create.submit')" :disabled="!canSubmit" :loading="isCreating" @click="handleSubmit" />
  </template>
</Dialog>
```

### DataTable (Thread/List.vue pattern)

Always: `size="small"`, `selection-mode="single"`, `table-style="min-width: 50rem"`. Custom `#body` templates for Tags,
Badges, formatted dates. Status columns use `<Tag :severity="...">`, counts use `<Badge :value="...">`.

```vue
<DataTable :value="items" table-style="min-width: 50rem" selection-mode="single" :selection="selected" size="small"
  @update:selection="emit('selected', $event)">
  <Column field="name" :header="t('resource.list.name')" />
  <Column field="status" :header="t('resource.list.status')">
    <template #body="{ data }"><Tag :severity="data.has_errors ? 'danger' : 'success'" :value="statusLabel(data)" /></template>
  </Column>
</DataTable>
```

### Panel (Event Display pattern)

```vue
<Panel toggleable collapsed class="border-none bg-transparent">
  <template #header>
    <div class="relative flex flex-row items-center gap-4">
      <div class="w-8 pt-1"><Icon :name="icon" class="size-5" /></div>
      <p class="font-semibold">{{ event.event_display_name }}</p>
    </div>
  </template>
  <!-- Collapsible content -->
</Panel>
```

### Dashboard KPI Widget (Dashboard/Component/Number.vue)

```vue
<div class="pointer-events-none relative w-full">
  <p class="pointer-events-none -mt-8 w-full text-center text-[12rem] font-medium opacity-70">{{ sum }}</p>
  <span class="absolute bottom-8 w-full text-center text-lg font-bold opacity-80">{{ title }}</span>
  <span class="absolute bottom-2 w-full text-center text-surface-500">{{ agentName }}</span>
  <div class="absolute -bottom-6 flex w-full justify-center"><DashboardTrend :timeseries="timeseries" /></div>
</div>
```

______________________________________________________________________

## Button Patterns (from real components)

| Pattern            | Props                                                                            | Where Used                  |
| ------------------ | -------------------------------------------------------------------------------- | --------------------------- |
| Primary submit     | `:label`, `:disabled`, `:loading`, `@click`                                      | Dialog footers              |
| Secondary cancel   | `:label`, `severity="secondary"`, `@click`                                       | Dialog footers              |
| Secondary outlined | `:label`, `severity="secondary"`, `outlined`                                     | Confirmation reject buttons |
| Icon-only delete   | `icon="pi pi-trash"`, `severity="secondary"`, `text`, `rounded`, `size="small"`  | Card action buttons         |
| Icon-only nav      | `icon="pi pi-chevron-left"`, `text`, `:disabled`                                 | Pagination controls         |
| Small text + icon  | `:label`, `icon="pi pi-arrow-right"`, `icon-pos="right"`, `size="small"`, `text` | Notification links          |

______________________________________________________________________

## Icon System (from real component analysis)

### Icon Sets by Purpose

| Set                   | Purpose in Our Codebase                 | Most Common Icons                                                |
| --------------------- | --------------------------------------- | ---------------------------------------------------------------- |
| `mage:*`              | Event displays, agent representation    | `robot`, `robot-happy`, `robot-sad`, `file`, `message`, `search` |
| `pi pi-*`             | Button icons, form controls, UI actions | `trash`, `plus`, `times`, `chevron-*`, `spinner`, `check`        |
| `lucide:*`            | Memory/neural operations                | `brain`, `brain-circuit`, `database-zap`                         |
| `icon-park-twotone:*` | Guard/shield events                     | `shield`                                                         |
| `mingcute:*`          | Thought events, AI workflow steps       | `thought-fill`, `ai-fill`                                        |
| `mynaui:*`            | Tool events                             | `tool`                                                           |
| `meteor-icons:*`      | Model fallback icon                     | `cpu`                                                            |
| `hugeicons:*`         | Unknown event fallback                  | `question`                                                       |

### Icon Source Pattern

Icons are NOT centralized. They come from:

1. **Backend config**: `agent.agent_config.icon`, `process.process_config.icon` (dynamic, stored in DB)
2. **Hardcoded per event component**: Each `EventDisplay*.vue` sets `icon=` on `EventDisplayBase`
3. **Fallbacks**: Unknown event = `hugeicons:question`, unknown model = `meteor-icons:cpu`, unknown agent = `mage:robot`

### Icon Sizes

| Context               | Size Prop/Class  | Source Component        |
| --------------------- | ---------------- | ----------------------- |
| Card icon (in circle) | `size="1.5em"`   | Agent/Card.vue          |
| Event display icon    | `class="size-5"` | Event/Display/Base.vue  |
| Navigation avatar     | `size="xl"`      | Thread/List.vue Avatar  |
| Small inline          | `size="1em"`     | Various inline contexts |
| PrimeIcons in buttons | Via `icon` prop  | Button component        |

### Icon Container (from Agent/Card.vue)

```vue
<div class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900">
  <Icon :name="iconName" size="1.5em" />
</div>
```

______________________________________________________________________

## Severity & Status Mapping (from real composables and components)

### Time-Based Severity (useTimeAgo composable)

| Time Since      | Severity  |
| --------------- | --------- |
| < 1 hour        | `success` |
| 1 hour - 7 days | `info`    |
| 7 - 30 days     | `warning` |
| > 30 days       | `danger`  |

### Score-Based Severity (Memory/List.vue, Knowledge/Node/Content.vue)

| Score Range | Severity  |
| ----------- | --------- |
| >= 0.8      | `success` |
| 0.6 - 0.8   | `info`    |
| 0.4 - 0.6   | `warn`    |
| < 0.4       | `danger`  |

### Boolean Status Tags

```vue
<Tag :severity="item.is_online ? 'success' : 'danger'" :value="item.is_online ? t('online') : t('offline')" />
```

### Metadata Tags (always secondary)

```vue
<Tag :value="item.agent_id" severity="secondary" class="font-mono" />
<Tag :value="t('agent.can_chat')" severity="secondary" icon="pi pi-comments" />
```

______________________________________________________________________

## Confirmation & Toast Patterns (from real components)

### Confirmation Dialog (useConfirm)

```typescript
confirm.require({
  message: t('resource.delete.confirmMessage'),
  header: t('resource.delete.title'),
  icon: 'pi pi-exclamation-triangle',
  rejectProps: { label: t('common.cancel'), severity: 'secondary', outlined: true },
  acceptProps: { label: t('resource.delete.button'), severity: 'danger' },
  accept: handleDelete,
})
```

### Toast Notifications (useToast)

```typescript
// Success: life 3000ms
toast.add({ severity: 'success', summary: t('resource.saved.summary'), detail: t('resource.saved.detail'), life: 3000 })
// Error: life 5000ms, include error message
toast.add({ severity: 'error', summary: t('resource.error.summary'), detail: error.message, life: 5000 })
```

______________________________________________________________________

## Form Patterns (from real components)

### Field Label Structure

```vue
<div class="flex flex-col gap-2">
  <label class="text-sm font-medium">{{ t('field.label') }}<span class="ml-1 text-xs text-red-500">*</span></label>
  <Select v-model="value" :options="options" class="w-full" :disabled="isSubmitting" />
</div>
```

### FormKit Schema-Driven Forms (Agent/CreateModal.vue)

Forms use `FormKitSchema` with schema from backend, wrapped in `<Stepper orientation="vertical">`. Always
`:actions="false"` (custom footer buttons). Stepper panels: `<div class="flex flex-col gap-6 py-4">`.

### FloatLabel Input

```vue
<FloatLabel variant="in">
  <InputText id="field" v-model="value" class="w-full" />
  <label for="field">{{ t('field.label') }}</label>
</FloatLabel>
```

### FormKit Repeater (custom FormKit/Repeater.vue wrapper)

```vue
<fieldset class="mb-4 rounded-lg border border-surface-300 p-4 dark:border-surface-600">
  <legend class="px-2 text-sm font-semibold text-surface-700 dark:text-surface-300">{{ label }}</legend>
</fieldset>
```

______________________________________________________________________

## Charts (Event/Timeseries.vue with ApexCharts)

Stacked bar chart: `type: 'bar', stacked: true, toolbar: { show: false }`. Dark mode via CSS variables:
`foreColor: isDark ? 'var(--p-surface-200)' : 'var(--p-surface-800)'`, `tooltip.theme: isDark ? 'dark' : 'light'`.
X-axis labels formatted per time resolution ('1h', '24h', '30d', '365d'). Colors from backend series data.

______________________________________________________________________

## PrimeVue Overrides (only two acceptable forms)

Scoped `:deep()`: `<style scoped>.panel :deep(.p-panel-header) { padding: 0 !important; }</style>`

CSS custom properties: `<Popover class="[--p-popover-background:#f9f9f9] dark:[--p-popover-background:#0d0d0d]" />`

No other custom CSS. Everything else uses Tailwind utilities.

______________________________________________________________________

## Design Configuration Files

| File                                                  | Purpose                                    |
| ----------------------------------------------------- | ------------------------------------------ |
| `packages/web/swiss_ai_hub_web/themes/aihub-theme.ts` | PrimeVue theme preset (surface scale)      |
| `packages/web/swiss_ai_hub_web/tailwind.config.mjs`   | Tailwind extensions (surface-850, plugins) |
| `packages/web/swiss_ai_hub_web/assets/css/main.css`   | Base font size (14px) and font stack       |
| `packages/web/swiss_ai_hub_web/nuxt.config.ts`        | PrimeVue module config, auto-imports       |

______________________________________________________________________

## Visual Verification

After applying design system tokens to a component, verify the result visually using Playwright MCP:

1. Navigate to the page: `mcp__playwright__browser_navigate` to `http://localhost:3333/service/{page}`
2. Take a screenshot: `mcp__playwright__browser_take_screenshot` to capture the rendered UI
3. Inspect the DOM: `mcp__playwright__browser_snapshot` to verify Tailwind classes are applied correctly
4. Check dark mode: toggle `.dark` class on `<html>` element and screenshot again to verify dark mode variants

This ensures design tokens render correctly -- Tailwind class typos or missing `dark:` variants are caught visually.
