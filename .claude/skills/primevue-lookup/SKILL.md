---
name: primevue-lookup
description: Look up PrimeVue component documentation and generate usage examples
  matching project patterns. Uses PrimeVue and Context7 MCP servers for up-to-date
  docs. Use when building UI with PrimeVue components.
allowed-tools: Read, Grep, Glob
---

# PrimeVue Component Lookup

Look up PrimeVue component documentation and generate project-specific usage examples. Component name or use case via `$ARGUMENTS`.

## Step 1: Find the Component

If the user specified a component name (e.g., "DataTable", "Dialog"), use it directly.

If the user described a use case (e.g., "sortable list", "confirmation popup"), determine the best PrimeVue component.

Use the **PrimeVue MCP server** to look up the official component documentation:
- Props, events, slots, and their types
- Pass Through (PT) options for styling
- Accessibility features

Also use the **Context7 MCP server** (`resolve-library-id` → `query-docs`) to fetch up-to-date PrimeVue documentation and code examples.

## Step 2: Check Existing Usage in Project

Search the codebase for existing usage of the component:

1. Search in `aihub_web/aihub_web/components/` and `aihub_web/aihub_web/pages/` for the component tag
2. Note how the project currently uses the component (props, events, styling patterns)
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

- **Auto-imported**: PrimeVue components are auto-imported by `@primevue/nuxt-module` — no explicit imports needed
- **FormKit-wrapped**: These components are excluded from PrimeVue auto-import and must come from FormKit: `InputText`, `Textarea`, `Select`, `MultiSelect`, `InputNumber`, `DatePicker`, `Password`, `Checkbox`, `RadioButton`, `ToggleSwitch`, `Listbox`, `Slider`, `Rating`
- **Tailwind only**: Style with Tailwind utility classes, not custom CSS
- **i18n labels**: All user-visible text must use `$t('key.path')` or `t('key.path')`
- **Dark mode**: Use `dark:` Tailwind variants for dark mode support

## Step 5: Report

Provide:
- **Component name and import method** (auto-import vs FormKit)
- **Props table** with types and descriptions
- **Events table** with payload types
- **Slots** available for customization
- **Project-specific usage example** following all conventions
- **Links** to existing usage in the codebase
