---
name: scaffold-dashboard-widget
description: >-
  Create a new dashboard widget using GridStack and ApexCharts. Generates the widget component,
  registers it in the dashboard system, and adds configuration. Use when user says 'create a
  dashboard widget', 'add a chart widget', 'scaffold dashboard component', 'new ApexCharts widget',
  'add number widget to dashboard', or 'create GridStack widget'. Takes a widget name/type as argument.

allowed-tools: Read, Write, Edit, Grep, Glob
---

# Scaffold a New Dashboard Widget

Create a new dashboard widget for the admin interface. The widget name/type should be provided via `$ARGUMENTS`.

## Before You Start

Read the frontend scope guide: `/home/user/aihub-core/aihub_web/CLAUDE.md`

Study existing dashboard components:

- Grid layout: `aihub_web/aihub_web/components/Dashboard/Grid.vue`
- Widget wrapper: `aihub_web/aihub_web/components/Dashboard/Item.vue`
- Chart widgets: `aihub_web/aihub_web/components/Dashboard/Component/BarChart.vue`
- Number widget: `aihub_web/aihub_web/components/Dashboard/Component/Number.vue`
- Line chart: `aihub_web/aihub_web/components/Dashboard/Component/LineChart.vue`
- Trend display: `aihub_web/aihub_web/components/Dashboard/Trend.vue`
- Widget type: `aihub_web/aihub_web/types/DashboardWidget.ts`
- Component resolver: `aihub_web/aihub_web/composables/dashboard/useDashboardComponent.ts`

## Step 1: Define the Widget Type

Check the existing widget types in `aihub_web/aihub_web/types/DashboardWidget.ts` and add your new widget type to the
union.

## Step 2: Create the Widget Component

Create `aihub_web/aihub_web/components/Dashboard/Component/<WidgetName>.vue`:

### For chart-based widgets (using ApexCharts):

```vue
<template>
  <div class="flex h-full flex-col">
    <p class="mb-2 text-sm font-semibold text-surface-600 dark:text-surface-300">
      {{ title }}
    </p>
    <ClientOnly>
      <apexchart
        type="<chart-type>"
        height="100%"
        :options="chartOptions"
        :series="series"
      />
    </ClientOnly>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  title: string
  data: Record<string, number>
}>()

const chartOptions = computed(() => ({
  chart: { toolbar: { show: false }, background: 'transparent' },
  theme: { mode: 'dark' },
  // ... chart-specific options
}))

const series = computed(() => [{ name: props.title, data: Object.values(props.data) }])
</script>
```

### For data display widgets (numbers, text, status):

```vue
<template>
  <div class="flex h-full flex-col items-center justify-center">
    <p class="text-4xl font-bold">
      {{ formattedValue }}
    </p>
    <p class="mt-2 text-sm text-surface-500">
      {{ label }}
    </p>
    <DashboardTrend
      v-if="trend !== undefined"
      :value="trend"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: number
  trend?: number
}>()

const formattedValue = computed(() => /* format logic */)
</script>
```

## Step 3: Register in Component Resolver

Edit `aihub_web/aihub_web/composables/dashboard/useDashboardComponent.ts` to add your widget to the component resolution
map.

## Step 4: Add Data Composable (if needed)

If the widget needs its own API data, create a composable following the Pinia-Colada pattern in
`aihub_web/aihub_web/composables/dashboard/`:

```typescript
export const use<WidgetName>Data = defineQuery(() => {
  const { data, isPending } = useQuery({
    key: () => ['dashboard', '<widget-name>'],
    staleTime: minutesToMilliseconds(1), // Dashboard widgets refresh more often
    query: async () => await get<Endpoint>({ composable: '$fetch' }),
  })
  return { data, isLoading: isPending }
})
```

## Examples

**Typical invocation**: `/scaffold-dashboard-widget cost-breakdown`

**Result**: Creates:

- `components/Dashboard/Component/CostBreakdown.vue` — widget component
- Updated `DashboardWidget.ts` — new widget type added to union
- Updated `useDashboardComponent.ts` — component resolver mapping

## Troubleshooting

| Problem                            | Solution                                                                  |
| ---------------------------------- | ------------------------------------------------------------------------- |
| Chart not rendering                | Ensure `ClientOnly` wrapper is present — ApexCharts doesn't work with SSR |
| Widget doesn't appear on dashboard | Check component resolver mapping in `useDashboardComponent.ts`            |
| Widget overflows its grid cell     | Use `h-full` and `flex` classes for responsive sizing                     |
| Dark mode colors wrong             | Set `theme: { mode: 'dark' }` and `chart: { background: 'transparent' }`  |
| Type error on widget type          | Add the new type to the union in `DashboardWidget.ts`                     |

## Key Conventions

- **ApexCharts**: Wrap in `<ClientOnly>` (SSR-incompatible, even though SSR is disabled)
- **Responsive sizing**: Use `h-full` and `flex` to fill the GridStack cell
- **Dark mode**: Charts must use `theme: { mode: 'dark' }` and transparent backgrounds
- **Tailwind only**: No custom CSS for layout
- **GridStack defaults**: Widgets have default `w`, `h`, `minW`, `minH` in their type definition
