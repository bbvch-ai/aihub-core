<template>
  <Card
    class="!rounded-2xl"
    :class="{
      'striped-bg': isExternal || !isFromAgentInThread,
      'border-2 border-red-500 dark:!border-red-900': isError,
      'border-2 border-orange-500 dark:!border-orange-700': isWarning,
      'bg-surface-50 dark:!bg-surface-800': !isError && !isWarning,
    }"
  >
    <template #header>
      <div
        class="absolute -top-3 right-12 rounded px-2 py-1 text-sm font-semibold"
        :class="{
          'bg-red-500 text-white dark:!bg-red-900': isError,
          'bg-orange-500 text-white dark:!bg-orange-700': isWarning,
          'bg-surface-50 dark:!bg-surface-800': !isError && !isWarning,
        }"
      >
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
import type { AgentDto, ThreadDto, WsServerEvent } from '@core/sdk/client'

const props = withDefaults(defineProps<{
  event: WsServerEvent
  thread: ThreadDto
  icon: string
  isExternal?: boolean
  isEmpty?: boolean
  isWarning?: boolean
  isError?: boolean
}>(), {
  isExternal: false,
  isEmpty: false,
  isWarning: false,
  isError: false,
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
