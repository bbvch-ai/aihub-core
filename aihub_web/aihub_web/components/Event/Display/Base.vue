<template>
  <Card
    class="card !rounded-2xl"
    :class="{
      'striped-bg': isExternal || !isFromAgentInThread,
      'border-2 border-red-500 dark:!border-red-900': isError,
      'border-2 border-yellow-500 dark:!border-yellow-700': isWarning,
      'bg-surface-50 dark:!bg-surface-800': !isError && !isWarning,
    }"
  >
    <template #header>
      <div
        class="absolute -top-3 right-12 rounded px-2 py-1 text-sm font-semibold"
        :class="{
          'bg-red-500 text-white dark:!bg-red-900': isError,
          'bg-yellow-500 text-white dark:!bg-yellow-700': isWarning,
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
        class="border-none bg-transparent"
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
              <p class="text-lg font-bold">
                {{ event.event_display_name }}
              </p>
            </div>
          </div>
        </template>
        <div
          v-if="!isEmpty"
        >
          <p class="text-sm text-surface-800 dark:text-surface-200">
            {{ event.event_display_description }}
          </p>
          <Divider />
          <br>
          <div class="pb-3 pr-3 ">
            <slot />
          </div>
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
.card :deep(.p-panel-header) {
  padding: 0 !important;
}
.card :deep(.p-card-body) {
  padding: 0 5px 0 15px !important;
}
.card :deep(.p-panel-content) {
  padding: 0 !important;
}
.striped-bg {
  background: repeating-linear-gradient(
    -55deg,
    rgba(155, 155, 155, 0.08),
    rgba(155, 155, 155, 0.08) 4px,
    rgba(155, 155, 155, 0) 4px,
    rgba(155, 155, 155, 0) 8px
  );
}
</style>
