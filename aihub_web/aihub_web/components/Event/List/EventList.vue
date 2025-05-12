<template>
  <div class="flex flex-col gap-12 pt-4">
    <Panel
      :header="$t('eventList.chat')"
      toggleable
      collapsed
    >
      <div class="flex flex-col gap-8">
        <ChatThread
          :events="eventsInRuns"
          :thread="thread"
        />
      </div>
    </Panel>
    <div class="flex flex-col gap-8">
      <div class="flex w-full items-center justify-end gap-2 pr-4">
        <span class="font-semibold">
          {{ $t('eventList.agents') }}
        </span>
        <MultiSelect
          v-model="activeRuns"
          display="chip"
          input-id="agents"
          :options="display.runs"
          :option-label="runNameFn"
        />
      </div>
      <Timeline
        :value="eventsInRuns"
        data-key="event_id"
        align="left"
        class="customized-timeline w-full"
      >
        <template #opposite="{ item: event }">
          <div class="flex w-full flex-row justify-end">
            <div class="flex flex-col text-xs text-surface-500 dark:text-surface-400">
              <div>{{ useDateFormat(event.event.created_at / 1_000_000, 'DD.MM.YYYY') }}</div>
              <div>{{ useDateFormat(event.event.created_at / 1_000_000, 'hh:mm:ss') }}</div>
            </div>
          </div>
        </template>
        <template #content="{ item: event }">
          <div class="w-full pb-12">
            <component
              :is="resolveComponentForEvent(event)"
              :event="event"
              :thread="thread"
            />
          </div>
        </template>
        <template #marker>
          <span
            class="z-10 flex size-5 items-center justify-center rounded-full border border-surface-100 bg-white text-white shadow-md shadow-surface-200 dark:border-surface-800 dark:bg-surface-700 dark:shadow-surface-950"
          >
            <Icon
              class="text-green-700"
              name="material-symbols:check"
              size="xs"
            />
          </span>
        </template>
      </Timeline>
    </div>
  </div>
</template>

<script setup lang="ts">
import type {
  DisplayStatistics, RunStatistics,
  ThreadDto,
  WsServerEvent,
} from '@core/sdk/client'

const props = defineProps<{
  events: WsServerEvent[]
  thread: ThreadDto
  displayId?: string
}>()

const route = useRoute()

const display = computed(() => {
  const displayId = props.displayId ?? route.params.display_id
  return props.thread.displays?.find((display: DisplayStatistics) => display.display_id === displayId)
})

const activeRuns = computed(() => {
  return display.value?.runs ?? []
})

const eventsInRuns = computed<WsServerEvent[]>(() => {
  const runIds = activeRuns.value.map((run: RunStatistics) => run.run_id)
  return props.events.filter((event: WsServerEvent) => runIds.includes(event.run_id))
})

const { resolveComponentForEvent } = useEventComponent()

const runNameFn = (run: RunStatistics) => run.agent.agent_config.name
</script>

<style scoped>
.customized-timeline :deep(.p-timeline-event-opposite) {
  width: 60px;
  max-width: 60px;
}
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
