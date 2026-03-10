---
name: scaffold-event-display
description: Create a new event display component for the agent event timeline. Generates the Vue component with EventDisplayBase wrapper and registers it in the event component resolver (useEventComponent.ts). Use when user says 'create event display', 'scaffold event component', 'add event to timeline', 'new agent event UI', 'display a new event type', or 'register event display component'. Do NOT use for general Vue components (use scaffold-frontend-component), backend event class definitions (use nats-events reference), or full page scaffolding (use scaffold-frontend-page). Takes an event name as argument.
allowed-tools: Read, Write, Edit, Grep, Glob, mcp__context7__resolve-library-id, mcp__context7__query-docs
---

# Scaffold a New Event Display Component

Create a display component for a new agent event type. The event name should be provided via `$ARGUMENTS`.

## Before You Start

Read the frontend scope guide: `packages/web/CLAUDE.md`

Study existing event display components:

- Simple: `packages/web/aihub_web/components/Event/Display/ThoughtEvent.vue`
- With data fields: `packages/web/aihub_web/components/Event/Display/ToolEvent.vue`
- Complex: `packages/web/aihub_web/components/Event/Display/LLMEvent.vue`
- Base wrapper: `packages/web/aihub_web/components/Event/Display/Base.vue`

Check the event component resolver: `packages/web/aihub_web/composables/event/useEventComponent.ts`

## Step 1: Identify the Event Type

Check the backend event definition in `packages/core/swiss_ai_hub/core/nats/events/` to understand:

- Event class name (e.g., `MyNewEvent`)
- Fields available on the event
- Parent event class (for inheritance-based resolution)

Also check the SDK types in `packages/web/aihub_web/sdk/client/` for the TypeScript type.

## Step 2: Create the Component

Create `packages/web/aihub_web/components/Event/Display/{EventName}Event.vue`:

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

| Prop         | Type                       | Description                                                          |
| ------------ | -------------------------- | -------------------------------------------------------------------- |
| `event`      | `ContextualizedAgentEvent` | Required. The event object                                           |
| `thread`     | `ThreadDto`                | Required. Parent thread                                              |
| `icon`       | `string`                   | Required. Iconify icon name (e.g., `mynaui:tool`, `hugeicons:brain`) |
| `isExternal` | `boolean`                  | Optional. Striped background for external agents                     |
| `isEmpty`    | `boolean`                  | Optional. Hides slot content area                                    |
| `isWarning`  | `boolean`                  | Optional. Yellow warning border                                      |
| `isError`    | `boolean`                  | Optional. Red error border                                           |

## Step 3: Register in Event Resolver

Edit `packages/web/aihub_web/composables/event/useEventComponent.ts`:

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

## Step 5: Verify

1. Confirm the component file exists at `packages/web/aihub_web/components/Event/Display/{EventName}Event.vue`
2. Confirm `useEventComponent.ts` has both the `#components` import and the mapping entry for the new event
3. Verify the component wraps content in `EventDisplayBase` with `event`, `thread`, and `icon` props
4. Verify props use the intersection type pattern: `ContextualizedAgentEvent & { event: {EventType} }`
5. Verify SDK types exist for the event — if not, warn user to run `/generate-sdk`

## Examples

**Typical invocation**: `/scaffold-event-display ToolCall`

**Result**: Creates:

- `components/Event/Display/ToolCallEvent.vue` — display component with EventDisplayBase wrapper
- Updated `useEventComponent.ts` — import and mapping entry added

## Troubleshooting

| Problem                          | Solution                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------- |
| Event not rendered in timeline   | Check mapping in `useEventComponent.ts` — event type name must match exactly  |
| Type errors on event props       | Verify SDK types are generated — run `/generate-sdk` if missing               |
| Icon not showing                 | Verify icon name at https://icon-sets.iconify.design/                         |
| Component renders but empty      | Check that `isEmpty` prop is not set and slot content accesses correct fields |
| Inheritance fallback not working | Verify `_parent_event_names` includes the parent event type                   |

## Key Conventions

- **Props typing**: Always use `ContextualizedAgentEvent & { event: {SpecificType} }` for type narrowing (see
  `ThoughtEvent.vue` for example)
- **Tailwind only**: No custom CSS (exception: Base.vue has scoped styles for PrimeVue overrides)
- **PrimeVue components**: Use `InputText`, `Button`, `DataTable`, `Tag` etc. for data display
- **No i18n needed**: Event display names come from the backend `event_display_name` field
- **Inheritance resolution**: The resolver tries exact match first, then checks `_parent_event_names`
