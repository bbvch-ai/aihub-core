<template>
  <EventDisplayBase
    :event="event"
    :thread="thread"
    icon="mage:robot-sad"
  >
    <div class="flex flex-col gap-2">
      <div class="flex gap-2">
        <Avatar
          size="large"
          icon="pi pi-verified"
        />
        <div
          class="mb-1 flex flex-col justify-center"
        >
          <p class="text-sm font-bold">
            {{ event.event.other_agent_topic.agent_class }}
          </p>
          <p class="text-sm">
            {{ event.event.other_agent_topic.agent_id }}
          </p>
        </div>
      </div>
      <component
        :is="vueComponent"
        :event="wrappedStartEvent"
        :thread="thread"
      />
    </div>
  </EventDisplayBase>
</template>

<script setup lang="ts">
import type { AgentInTheLoopRequestEvent, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

const props = defineProps<{
  event: ContextualizedAgentEvent & { event: AgentInTheLoopRequestEvent }
  thread: ThreadDto
}>()

const { resolveComponentForEvent } = useEventComponent()

const vueComponent = computed(() => {
  return resolveComponentForEvent(wrappedStartEvent.value)
})

const wrappedStartEvent = computed<ContextualizedAgentEvent>(() => {
  return {
    ...props.event,
    ...props.event.event.start_event,
    event_display_name: props.event.event.start_event.display_name[props.event.locale],
    event_display_description: props.event.event.start_event.display_description[props.event.locale],
    event: props.event.event.start_event,
  }
})
</script>
