<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:arrowlist"
  >
    <div class="flex flex-col gap-3">
      <p class="border-l-4 border-surface-200 pl-3 italic dark:border-surface-600">
        {{ event.event.reason }}
      </p>
      <Panel
        v-for="route in event.event.routes"
        :key="route.event_id"
        class="flex flex-col gap-2"
      >
        <template #header>
          <div class="flex w-full flex-row items-center justify-between gap-2 px-5 pt-3">
            <span class="font-bold">
              {{ route.name }}
            </span>
            <Tag
              v-if="isSelectedRoute(route)"
              icon="pi pi-check"
              severity="success"
              value="Selected"
            />
            <Tag
              v-else
              icon="pi pi-times"
              severity="danger"
              value="Rejected"
            />
          </div>
        </template>
        <span>
          {{ route.description }}
        </span>
      </Panel>
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { RouteOptions, RouterEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: RouterEvent }
  thread: ThreadDto
}>()

const isSelectedRoute = (route: RouteOptions) => {
  return route.event_id == props.event.event.selected_option.event_id
}
</script>
