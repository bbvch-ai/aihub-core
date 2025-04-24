<template>
  <Card
    class="!rounded-2xl bg-surface-50 dark:!bg-surface-800"
    :class="{ 'striped-bg': isExternal || !isFromAgentInThread }"
  >
    <template #header>
      <div class="absolute -top-3 right-12 rounded bg-surface-50 px-2 py-1 text-xs font-semibold dark:!bg-surface-800">
        {{ event.agent_class }}
      </div>
    </template>
    <template #content>
      <Panel
        :toggleable="!isEmpty"
        collapsed
        class="panel border-none bg-transparent"
      >
        <template #header>
          <div class="relative flex flex-row gap-4">
            <div class="w-8 pt-1">
              <Icon
                :name="icon ?? 'hugeicons:question'"
                class="size-5"
              />
            </div>
            <div>
              <p class="text-xl font-bold">
                {{ event.event_display_name }}
              </p>
              <p class="text-sm text-surface-800 dark:text-surface-200">
                {{ event.event_display_description }}
              </p>
            </div>
          </div>
        </template>
        <div
          v-if="!isEmpty"
          class="pt-4"
        >
          <Divider />
          <br>
          <slot />
        </div>
      </Panel>
    </template>
  </Card>
</template>

<script setup lang="ts">
import type { AgentDto, ThreadResponse, WsServerEvent } from '@core/sdk/client'

const props = withDefaults(defineProps<{
  event: WsServerEvent
  thread: ThreadResponse
  icon: string
  isExternal?: boolean
  isEmpty?: boolean
}>(), {
  isExternal: false,
  isEmpty: false,
})

const agentIds = computed<string[]>(() => {
  const agents = props.thread.agents ?? []
  return agents.map((agent: AgentDto) => `${agent.agent_class}/${agent.agent_id}`)
})

const isFromAgentInThread = computed<boolean>(() => {
  return agentIds.value.includes(`${props.event.agent_class}/${props.event.agent_id}`)
})
</script>

<style scoped>
::v-deep(.panel) {
  .p-panel-header {
    padding: 0 !important;
  }
}
.striped-bg {
  background: repeating-linear-gradient(
    -55deg,
    rgba(155, 155, 155, 0.1),
    rgba(155, 155, 155, 0.1) 4px,
    rgba(155, 155, 155, 0) 4px,
    rgba(155, 155, 155, 0) 8px
  );
}
</style>
