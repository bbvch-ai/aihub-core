<template>
  <Card
    class="card !rounded-2xl"
    :class="{
      'striped-bg': isExternal || !isFromAgentInThread,
      'border-2 border-red-500 dark:!border-red-900': isError,
      'border-2 border-yellow-500 dark:!border-yellow-700': isWarning,
      'border border-surface-50 dark:!border-surface-850': !isError && !isWarning,
    }"
  >
    <template #header>
      <div
        class="absolute -top-3 right-12 rounded px-2 py-1 text-xs text-surface-500 dark:text-surface-400"
        :class="{
          'bg-red-500 text-white dark:!bg-red-900': isError,
          'bg-yellow-500 text-white dark:!bg-yellow-700': isWarning,
          'bg-white dark:!bg-surface-900': !isError && !isWarning,
        }"
      >
        {{ event.agent_class }}
      </div>
    </template>
    <template #content>
      <Panel
        toggleable
        collapsed
        class="border-none bg-transparent"
      >
        <template #header>
          <div class="relative flex flex-row items-center gap-4">
            <div class="w-8 pt-1">
              <Icon
                :name="icon ?? 'hugeicons:question'"
                class="size-5"
              />
            </div>
            <p class="font-semibold">
              {{ event.event_display_name }}
            </p>
          </div>
        </template>
        <div>
          <div class="flex items-start justify-between gap-4">
            <p class="flex-1 text-sm text-surface-800 dark:text-surface-200">
              {{ event.event_display_description }}
            </p>
            <Button
              variant="text"
              class="text-xs text-surface-500 underline hover:text-surface-700 dark:text-surface-400 dark:hover:text-surface-300"
              @click="showRawData = !showRawData"
            >
              {{ showRawData ? t('event.base.view_formatted') : t('event.base.view_raw_data') }}
            </Button>
          </div>

          <div v-if="!isEmpty && !showRawData">
            <Divider />
            <br>
            <div class="pb-3 pr-3 ">
              <slot />
            </div>
          </div>

          <EventDisplayRawDataContent
            v-if="showRawData"
            :event="event"
          />
        </div>
      </Panel>
    </template>
  </Card>
</template>

<script setup lang="ts">
import type { MinimalAgentInstanceDto, ThreadDto, ContextualizedAgentEvent } from '@core/sdk/client'

const props = withDefaults(defineProps<{
  event: ContextualizedAgentEvent
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

const { t } = useI18n()

const showRawData = ref(false)

const agentIds = computed<string[]>(() => {
  const agents = props.thread.agents ?? []
  return agents.map((agent: MinimalAgentInstanceDto) => `${agent.agent_class}/${agent.agent_id}`)
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
