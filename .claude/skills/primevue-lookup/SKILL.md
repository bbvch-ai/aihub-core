---
name: primevue-lookup
description: Look up PrimeVue component docs, props, events, slots, and generate project-specific usage examples. Uses PrimeVue and Context7 MCP servers for up-to-date documentation. Use when user says "how do I use DataTable", "PrimeVue Dialog props", "what PrimeVue component for X", "show me how to use Tag", "PrimeVue examples", "which component for dropdowns", or "look up PrimeVue". Returns props/events tables, existing codebase usage, and a ready-to-use code example.
allowed-tools: Read, Grep, Glob
---

# PrimeVue Component Lookup

Look up PrimeVue component documentation and generate project-specific usage examples. Component name or use case via
`$ARGUMENTS`.

## Step 1: Find the Component

1. If the user specified a component name (e.g., "DataTable", "Dialog"), use it directly.
2. If the user described a use case (e.g., "sortable list", "confirmation popup"), determine the best PrimeVue
   component.
3. Use the **PrimeVue MCP server** to look up official component documentation:
   - Props, events, slots, and their types
   - Pass Through (PT) options for styling
   - Accessibility features
4. Also use the **Context7 MCP server** (`resolve-library-id` then `query-docs`) to fetch up-to-date PrimeVue
   documentation and code examples.

## Step 2: Check Existing Usage in Project

Search the codebase for existing usage of the component:

1. Search in `aihub_web/aihub_web/components/` and `aihub_web/aihub_web/pages/` for the component tag name (e.g.,
   `<DataTable`, `<Dialog`)
2. Note how the project currently uses the component (which props, events, styling patterns)
3. Check if the component is excluded from auto-import in `nuxt.config.ts` (some are wrapped by FormKit)

## Step 3: Check PrimeVue Theme Integration

Read the project theme: `aihub_web/aihub_web/themes/aihub-theme.ts`

Note any custom design tokens or component-specific overrides that affect styling.

## Step 4: Generate Usage Example

Create a usage example that follows project conventions:

```vue
<template>
  <!-- PrimeVue component with project-standard patterns -->
  <ComponentName
    v-model="value"
    :prop="data"
    class="tailwind-classes"
    @event="handler"
  />
</template>

<script setup lang="ts">
// Typed refs matching project patterns
const value = ref<Type>(initialValue)
</script>
```

### Project-Specific Rules

- **Auto-imported**: PrimeVue components are auto-imported by `@primevue/nuxt-module` -- no explicit imports needed
- **FormKit-wrapped**: These components are excluded from PrimeVue auto-import and MUST come from FormKit: `InputText`,
  `Textarea`, `Select`, `MultiSelect`, `InputNumber`, `DatePicker`, `Password`, `Checkbox`, `RadioButton`,
  `ToggleSwitch`, `Listbox`, `Slider`, `Rating`
- **Tailwind only**: Style with Tailwind utility classes, not custom CSS
- **i18n labels**: All user-visible text must use `$t('key.path')` or `t('key.path')`
- **Dark mode**: Use `dark:` Tailwind variants for dark mode support

## Step 5: Report

Provide the following in a structured format:

1. **Component name and import method** (auto-import vs FormKit)
2. **Props table** with types, defaults, and descriptions
3. **Events table** with payload types
4. **Slots** available for customization
5. **Project-specific usage example** following all conventions above
6. **Existing usage** -- file paths where this component is already used in the codebase

## Examples

**Input**: `$ARGUMENTS = "DataTable"`

**Expected output**: Props table (value, selection, dataKey, size, etc.), events table (update:selection, row-click,
sort, etc.), slots (header, body, footer, empty), plus a code example using `size="small"`, `selection-mode="single"`,
typed SDK DTO array, and i18n column headers.

**Input**: `$ARGUMENTS = "confirmation popup"`

**Expected output**: Identifies `ConfirmDialog` + `useConfirm()` composable as the correct approach. Shows project
pattern with `confirm.require({ message, header, accept, reject })` and i18n strings.

**Input**: `$ARGUMENTS = "Tag"`

**Expected output**: Props (value, severity, icon, rounded), existing usage showing severity patterns
(`success`/`danger`/`secondary`), and code example with dynamic severity.

## Troubleshooting

| Problem                         | Cause                                         | Fix                                                                                        |
| ------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Component renders but unstyled  | PrimeVue theme not loaded                     | Check `nuxt.config.ts` for `@primevue/nuxt-module` configuration                           |
| FormKit input not rendering     | Using PrimeVue import for a wrapped component | Check the FormKit-wrapped list above; use FormKit version instead                          |
| Component not found at runtime  | Typo in component name or not auto-imported   | PrimeVue components are PascalCase; check `nuxt.config.ts` exclude list                    |
| Custom CSS not applying         | PrimeVue internal DOM elements                | Use `:deep()` selector in scoped styles or CSS custom properties (see design-system skill) |
| MCP server returning no results | Server not running or wrong query             | Verify PrimeVue MCP is configured in `.mcp.json`; try exact component name                 |
