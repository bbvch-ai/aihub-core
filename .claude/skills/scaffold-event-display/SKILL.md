---
name: scaffold-event-display
description: Create a new event display component for the agent event timeline.
  Generates the Vue component with EventDisplayBase wrapper and registers it in the
  event component resolver.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Scaffold a New Event Display Component

Create a display component for a new agent event type. The event name should be provided via `$ARGUMENTS`.

## Before You Start

Read the frontend scope guide: `/home/user/aihub-core/aihub_web/AGENTS.md`

Study existing event display components:
- Simple: `aihub_web/aihub_web/components/Event/Display/ThoughtEvent.vue`
- With data fields: `aihub_web/aihub_web/components/Event/Display/ToolEvent.vue`
- Complex: `aihub_web/aihub_web/components/Event/Display/LLMEvent.vue`
- Base wrapper: `aihub_web/aihub_web/components/Event/Display/Base.vue`

Check the event component resolver: `aihub_web/aihub_web/composables/event/useEventComponent.ts`

## Step 1: Identify the Event Type

Check the backend event definition in `aihub_lib/aihub_lib/events/` to understand:
- Event class name (e.g., `MyNewEvent`)
- Fields available on the event
- Parent event class (for inheritance-based resolution)

Also check the SDK types in `aihub_web/aihub_web/sdk/client/` for the TypeScript type.

## Step 2: Create the Component

Create `aihub_web/aihub_web/components/Event/Display/<EventName>Event.vue`:

```vue
<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="<iconify-icon-name>"
  >
    <!-- Event-specific content rendered inside the collapsible panel -->
    <p class="text-2xl font-bold">
      {{ event.event.field_name }}
    </p>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { ThreadDto, <EventName>Event, ContextualizedAgentEvent } from '@core/sdk/client'

defineProps<{
  event: ContextualizedAgentEvent & { event: <EventName>Event }
  thread: ThreadDto
}>()
</script>
```

### EventDisplayBase Props

The `Base.vue` wrapper provides the card layout, raw data toggle, and agent badge. Your component fills the `<slot>`:

| Prop | Type | Description |
|------|------|-------------|
| `event` | `ContextualizedAgentEvent` | Required. The event object |
| `thread` | `ThreadDto` | Required. Parent thread |
| `icon` | `string` | Required. Iconify icon name (e.g., `mynaui:tool`, `hugeicons:brain`) |
| `isExternal` | `boolean` | Optional. Striped background for external agents |
| `isEmpty` | `boolean` | Optional. Hides slot content area |
| `isWarning` | `boolean` | Optional. Yellow warning border |
| `isError` | `boolean` | Optional. Red error border |

## Step 3: Register in Event Resolver

Edit `aihub_web/aihub_web/composables/event/useEventComponent.ts`:

1. Add the import to the `#components` import block:
```typescript
import {
  // ... existing imports
  EventDisplay<EventName>Event,
} from '#components'
```

2. Add the mapping entry inside `resolveComponentForEvent`:
```typescript
const mapping = {
  // ... existing mappings
  <EventName>Event: EventDisplay<EventName>Event,
}
```

## Step 4: Choose an Icon

Browse icons at https://icon-sets.iconify.design/. The project uses these icon sets:
- `mynaui:*` (clean line icons)
- `hugeicons:*` (detailed icons)
- `prime:*` (PrimeVue icons)

Match the icon to the event's semantic meaning (e.g., `mynaui:tool` for tools, `hugeicons:brain` for LLM).

## Key Conventions

- **Props typing**: Always use `ContextualizedAgentEvent & { event: <SpecificType> }` for type narrowing
- **Tailwind only**: No custom CSS (exception: Base.vue has scoped styles for PrimeVue overrides)
- **PrimeVue components**: Use `InputText`, `Button`, `DataTable`, `Tag` etc. for data display
- **No i18n needed**: Event display names come from the backend `event_display_name` field
- **Inheritance resolution**: The resolver tries exact match first, then checks `_parent_event_names`
