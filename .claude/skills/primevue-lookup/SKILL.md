---
name: primevue-lookup
description: Look up PrimeVue component docs, props, events, slots, and generate project-specific usage examples. Uses PrimeVue and Context7 MCP servers for up-to-date documentation. Use when user says "how do I use DataTable", "PrimeVue Dialog props", "what PrimeVue component for X", "show me how to use Tag", "PrimeVue examples", "which component for dropdowns", or "look up PrimeVue". Do NOT use for scaffolding new Vue components (use scaffold-frontend-component), design system or theming questions (use design-system), or frontend code audits (use audit-frontend). Returns props/events tables, existing codebase usage, and a ready-to-use code example.
allowed-tools: Read, Grep, Glob, mcp__primevue__get_component, mcp__primevue__get_component_props, mcp__primevue__get_component_events, mcp__primevue__get_component_slots, mcp__primevue__get_component_methods, mcp__primevue__get_component_pt, mcp__primevue__get_component_tokens, mcp__primevue__get_component_styles, mcp__primevue__get_component_import, mcp__primevue__search_components, mcp__primevue__suggest_component, mcp__primevue__generate_component_template, mcp__primevue__get_example, mcp__primevue__list_examples, mcp__primevue__find_by_prop, mcp__primevue__find_by_event, mcp__primevue__get_accessibility_info, mcp__primevue__get_related_components, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# PrimeVue Component Lookup

Look up PrimeVue component documentation and generate project-specific usage examples. Component name or use case via
`$ARGUMENTS`.

## Step 1: Find the Component

1. If the user specified a component name (e.g., "DataTable", "Dialog"), use `mcp__primevue__get_component` directly.
2. If the user described a use case (e.g., "sortable list", "confirmation popup"), use
   `mcp__primevue__suggest_component` to find the best match.
3. Look up component details with these PrimeVue MCP tools:
   - `mcp__primevue__get_component_props` — props with types and defaults
   - `mcp__primevue__get_component_events` — events with payload types
   - `mcp__primevue__get_component_slots` — available slots
   - `mcp__primevue__get_component_pt` — Pass Through options for styling
   - `mcp__primevue__get_accessibility_info` — accessibility features
4. Use `mcp__context7__resolve-library-id` then `mcp__context7__query-docs` to fetch additional PrimeVue documentation
   and code examples.

## Step 2: Check Existing Usage in Project

Search the codebase for existing usage of the component:

1. Search in `packages/web/aihub_web/components/` and `packages/web/aihub_web/pages/` for the component tag name (e.g.,
   `<DataTable`, `<Dialog`)
2. Note how the project currently uses the component (which props, events, styling patterns)
3. Check if the component is excluded from auto-import in `nuxt.config.ts` (some are wrapped by FormKit)

## Step 3: Check PrimeVue Theme Integration

Read the project theme: `packages/web/aihub_web/themes/aihub-theme.ts`

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
- **FormKit-wrapped**: These components are excluded from PrimeVue auto-import and MUST come from FormKit:
  `AutoComplete`, `CascadeSelect`, `Checkbox`, `Chip`, `ColorPicker`, `DatePicker`, `Editor`, `InputMask`,
  `InputNumber`, `InputOtp`, `InputText`, `Knob`, `Listbox`, `MultiSelect`, `Password`, `RadioButton`, `Rating`,
  `Select`, `SelectButton`, `Slider`, `Textarea`, `ToggleButton`, `ToggleSwitch`, `TreeSelect`
- **Also excluded from auto-import** (not FormKit-wrapped, imported differently): `Button`, `Form`, `FormField`, `Chart`
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

## Step 6: Verify

1. Confirm the component exists: `mcp__primevue__get_component` should return data
2. If FormKit-wrapped, verify the example does NOT use a direct PrimeVue import
3. Check that i18n keys used in the example exist in `packages/web/aihub_web/i18n/locales/en.yaml`
4. If referencing existing usage, confirm the file paths are current

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
