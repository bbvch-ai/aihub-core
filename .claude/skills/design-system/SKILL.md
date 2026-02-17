---
name: design-system
description: Reference guide for the AI-Hub design system covering colors, typography, spacing, component patterns, dark mode, layout, borders, radius, and icons. Use when user says "what colors to use", "design system", "Tailwind classes for cards", "dark mode classes", "spacing values", "which border radius", "typography scale", "layout structure", "icon sizes", "how to style X", or before building any UI to ensure visual consistency. Returns exact Tailwind classes and design tokens.
allowed-tools: Read, Grep, Glob
---

# AI-Hub Design System Reference

Look up design system information. Topic or question via `$ARGUMENTS` (e.g., "colors", "spacing", "card pattern", "dark
mode", "typography").

## Design Philosophy

The AI-Hub admin interface follows a **monochromatic, professional** design language:

1. **Neutral palette**: No bright brand colors. Primary colors map to the surface/stone scale.
2. **Content-first**: Minimal chrome, maximum space for data.
3. **Dark mode as first-class**: Every element must work in both light and dark modes.
4. **PrimeVue + Tailwind**: Components from PrimeVue, all styling via Tailwind utilities. No custom CSS.
5. **Generous radius**: Modern, soft aesthetic with `rounded-xl` (12px) and `rounded-3xl` (24px).
6. **Information density**: 14px base font, `text-xs` for metadata, compact but readable.

---

## Color Palette

Based on PrimeVue Aura theme with custom stone/surface colors.

**Theme file**: `aihub_web/aihub_web/themes/aihub-theme.ts`

### Surface Scale (same values in light and dark mode)

| Token         | Hex       | Usage                                          |
| ------------- | --------- | ---------------------------------------------- |
| `surface-50`  | `#f9f9f9` | Page background (light), lightest text (dark)  |
| `surface-100` | `#ececec` | Active card background (light), selected row   |
| `surface-200` | `#e3e3e3` | Borders (light), active nav items              |
| `surface-300` | `#cdcdcd` | Dashed borders, dividers                       |
| `surface-400` | `#b4b4b4` | Disabled icons, placeholder text               |
| `surface-500` | `#9b9b9b` | Muted text, metadata                           |
| `surface-600` | `#676767` | Secondary text, labels                         |
| `surface-700` | `#4e4e4e` | Body text (dark mode)                          |
| `surface-800` | `#333333` | Active background (dark), borders (dark)       |
| `surface-850` | `#262626` | Custom: chat bubbles, selected rows (dark)     |
| `surface-900` | `#171717` | Card background (dark), icon containers (dark) |
| `surface-950` | `#0d0d0d` | Page background (dark), deepest black          |

### Primary Color

Primary maps directly to surface (monochromatic):

- **Light mode**: `{stone.950}` (almost black)
- **Dark mode**: `{stone.50}` (almost white)

### Semantic Colors

Used only via PrimeVue `severity` prop on `Tag`, `Button`, `Message`:

- **`success`** — Online, active, completed (green)
- **`danger`/`error`** — Offline, failed, deleted (red)
- **`warning`** — Pending, attention needed (yellow)
- **`secondary`** — Neutral metadata, informational tags (gray)

### Dark Mode

- Selector: `.dark` CSS class (class-based, not `prefers-color-scheme`)
- **Tailwind config**: `darkMode: ['class']`
- **PrimeVue config**: `darkModeSelector: '.dark'`

---

## Background Patterns

### Light Mode

| Context                | Classes                |
| ---------------------- | ---------------------- |
| Page/screen background | `bg-surface-50`        |
| Card/column background | `bg-white`             |
| Icon container         | `bg-white`             |
| Active card/selected   | `bg-surface-100`       |
| Hover state            | `hover:bg-surface-100` |

### Dark Mode

| Context                | Classes                     |
| ---------------------- | --------------------------- |
| Page/screen background | `dark:bg-surface-950`       |
| Card/column background | `dark:bg-surface-900`       |
| Icon container         | `dark:bg-surface-900`       |
| Active card/selected   | `dark:bg-surface-800`       |
| Hover state            | `dark:hover:bg-surface-800` |

### Rule: Every `bg-*` MUST have a `dark:bg-*` variant.

---

## Typography

**Base font size**: 14px (set in `assets/css/main.css`) **Font stack**: System fonts (Apple, Segoe UI, Roboto, Inter)

### Size Scale

| Class       | Size    | Usage                                     |
| ----------- | ------- | ----------------------------------------- |
| `text-xs`   | 10.5px  | Metadata, descriptions, IDs (most common) |
| `text-sm`   | 12.25px | Body text in cards, lists                 |
| `text-base` | 14px    | Default body text                         |
| `text-lg`   | 15.75px | Section group names                       |
| `text-xl`   | 17.5px  | Column titles (`childColumn: true`)       |
| `text-2xl`  | 21px    | Column titles (default `h2`)              |
| `text-4xl`  | 31.5px  | Dashboard numbers                         |
| `text-6xl`  | 42px    | Welcome/hero text                         |

### Weight Scale

| Class           | Usage                                           |
| --------------- | ----------------------------------------------- |
| `font-light`    | Descriptions, secondary values                  |
| `font-medium`   | Labels, navigation items, empty card titles     |
| `font-semibold` | Card titles, field labels, panel headers        |
| `font-bold`     | Column titles, table headers, dashboard numbers |

### Opacity for Visual Hierarchy

| Class        | Usage                       |
| ------------ | --------------------------- |
| `opacity-80` | Card title (slightly muted) |
| `opacity-70` | Card subtitle (more muted)  |

### Text Colors

| Classes                                  | Usage                              |
| ---------------------------------------- | ---------------------------------- |
| `text-surface-900 dark:text-surface-100` | Primary text                       |
| `text-surface-700 dark:text-surface-200` | Secondary text                     |
| `text-surface-600 dark:text-surface-400` | Labels, field names                |
| `text-surface-500 dark:text-surface-400` | Muted text, descriptions, metadata |
| `text-surface-400`                       | Disabled text, icons               |

---

## Spacing

### Common Values

| Class       | Pixels (at 14px base) | Usage                       |
| ----------- | --------------------- | --------------------------- |
| `gap-2`     | 7px                   | Default flex gap (tight)    |
| `gap-3`     | 10.5px                | Card internal spacing       |
| `gap-4`     | 14px                  | Grid items, header sections |
| `gap-8`     | 28px                  | Page sections, column gaps  |
| `gap-12`    | 42px                  | Major section separation    |
| `p-3`       | 10.5px                | Icon containers             |
| `p-4`       | 14px                  | Card padding (standard)     |
| `p-6`       | 21px                  | Column content padding      |
| `px-8 pt-8` | 28px                  | Screen-level padding        |

### Guidelines

- **Card internal**: `gap-3` (vertical), `gap-4` (horizontal header), `gap-2` (tight groups)
- **Grid items**: `gap-4`
- **Page sections**: `gap-12`
- **Icon containers**: `p-3`
- **Card padding**: `p-4`
- **Column padding**: `p-6` (inside StructuralColumn)

---

## Border Radius

| Class          | Pixels | Usage                                        |
| -------------- | ------ | -------------------------------------------- |
| `rounded-xl`   | 12px   | **Cards** (standard for all clickable cards) |
| `rounded-2xl`  | 16px   | Event display cards                          |
| `rounded-3xl`  | 24px   | **Columns** (StructuralColumn container)     |
| `rounded-full` | 50%    | Icon containers, avatars                     |
| `rounded-lg`   | 8px    | Form elements, small containers              |

### Guidelines

- **Cards**: Always `rounded-xl`
- **Major containers**: `rounded-3xl`
- **Circular elements**: `rounded-full`

---

## Borders

| Context           | Light Mode                                  | Dark Mode                 |
| ----------------- | ------------------------------------------- | ------------------------- |
| Card border       | `border border-surface-200`                 | `dark:border-surface-800` |
| Empty card border | `border-2 border-dashed border-surface-300` | `dark:border-surface-600` |
| Error border      | `border-2 border-red-500`                   | `dark:border-red-900`     |
| Warning border    | `border-2 border-yellow-500`                | `dark:border-yellow-700`  |

---

## Layout System

### Page Structure

```
+----------------------------------------------+
| <- 50px fixed sidebar (navigation)           |
| +------+-------------------------------------+
| | Logo |  50px fixed top bar (breadcrumb)     |
| |------+-------------------------------------+
| | Apps |  StructuralScreen                    |
| |      |  +------------+  +----------------+ |
| |      |  | Column 1   |  |  Column 2      | |
| |      |  | (list)     |  |  (detail)      | |
| |------|  +------------+  +----------------+ |
| | User |                                      |
| +------+-------------------------------------+
+----------------------------------------------+
```

### Structural Components

| Component          | Role           | Key Classes                                              |
| ------------------ | -------------- | -------------------------------------------------------- |
| `StructuralScreen` | Page container | `h-[calc(100vh-50px)] bg-surface-50 dark:bg-surface-950` |
| `StructuralColumn` | Content card   | `rounded-3xl bg-white dark:bg-surface-900 p-6`           |

### Column Sizes

| Size     | Width            | Usage                           |
| -------- | ---------------- | ------------------------------- |
| `small`  | `2xl:w-[680px]`  | Simple detail views             |
| `normal` | `2xl:w-[920px]`  | Standard lists and details      |
| `large`  | `2xl:w-[1440px]` | Complex detail pages with grids |

### Responsive Behavior

- **Mobile/tablet (< 2xl)**: Single column, full width (`max-2xl:w-full`)
- **Desktop (>= 2xl / 1536px)**: Multi-column side-by-side
- **Grid layouts**: `grid-cols-1 lg:grid-cols-2` or `grid-cols-2 xl:grid-cols-4`

---

## Component Patterns

### Card (Resource Item)

```
+----------------------------------+
| [O] Title           [Status] [x] |  <- gap-4 header
|     subtitle (id)                 |
| Description text...               |  <- gap-3 vertical
| [Feature Tag]                     |
+----------------------------------+
```

Classes: `rounded-xl border border-surface-200 p-4 gap-3`

### Empty Card (Add New)

```
+ - - - - - - - - - - - - - - - - +
|           [+]                    |  <- dashed border
|       Add new item               |
|    Click to create               |
+ - - - - - - - - - - - - - - - - +
```

Classes: `rounded-xl border-2 border-dashed border-surface-300 p-4`

### Loading State

```
+----------------------------------+
| =================== (2px bar)    |  <- ProgressBar indeterminate
|                                  |
|        (content hidden)          |
|                                  |
+----------------------------------+
```

StructuralColumn hides content until `loading === false`.

---

## Icon System

**Provider**: Nuxt Icon module (Iconify)

### Icon Sets

| Set                  | Usage                          | Example                              |
| -------------------- | ------------------------------ | ------------------------------------ |
| `hugeicons:*`        | Primary custom icons           | `hugeicons:brain`, `hugeicons:agent` |
| `mynaui:*`           | Clean line icons               | `mynaui:tool`, `mynaui:chat`         |
| `pi pi-*`            | PrimeIcons (in PrimeVue props) | `pi pi-trash`, `pi pi-plus`          |
| `meteor-icons:*`     | Specialty icons                | `meteor-icons:robot`                 |
| `material-symbols:*` | Material icons                 | `material-symbols:home`              |

### Icon Sizes

| Context       | Size             |
| ------------- | ---------------- |
| Card icons    | `size="1.5em"`   |
| Navigation    | `size="xl"`      |
| Event display | `class="size-5"` |
| Small inline  | `size="1em"`     |

### Icon Container Pattern

```vue
<div class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900">
  <Icon :name="iconName" size="1.5em" />
</div>
```

---

## PrimeVue Overrides

When PrimeVue components don't respond to Tailwind classes, use:

### Scoped `:deep()` for Internal Selectors

```vue
<style scoped>
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
```

### CSS Custom Properties for Theming

```vue
<Popover class="[--p-popover-background:#f9f9f9] dark:[--p-popover-background:#0d0d0d]" />
```

These are the ONLY acceptable forms of custom CSS. Everything else uses Tailwind utilities.

---

## Design Configuration Files

| File                                        | Purpose                                    |
| ------------------------------------------- | ------------------------------------------ |
| `aihub_web/aihub_web/themes/aihub-theme.ts` | PrimeVue theme preset (colors, tokens)     |
| `aihub_web/aihub_web/tailwind.config.mjs`   | Tailwind extensions (surface-850, plugins) |
| `aihub_web/aihub_web/assets/css/main.css`   | Base font size and font stack              |
| `aihub_web/aihub_web/nuxt.config.ts`        | PrimeVue module config, auto-imports       |

---

## Quick Reference: Common Recipes

### Standard Card with Dark Mode

```vue
<div class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800">
```

### Icon Container

```vue
<div class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900">
  <Icon :name="icon" size="1.5em" />
</div>
```

### Field Label + Value

```vue
<div class="flex flex-col items-start gap-2">
  <span class="font-semibold">{{ t('label') }}</span>
  <Tag :value="value" severity="secondary" />
</div>
```

### Status Tag

```vue
<Tag :value="isOnline ? t('online') : t('offline')" :severity="isOnline ? 'success' : 'danger'" />
```

### Muted Description

```vue
<span class="text-sm text-surface-500 dark:text-surface-400">{{ description }}</span>
```

### Section with Vertical Spacing

```vue
<div class="flex flex-col gap-12">
  <!-- Major sections -->
</div>
```

### Responsive Grid

```vue
<div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
  <!-- Grid items -->
</div>
```
