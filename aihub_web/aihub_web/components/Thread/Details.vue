<template>
  <div>
    <Tabs
      v-model:value="activeDisplayId"
      scrollable
    >
      <TabList>
        <Tab
          v-for="display in thread.displays"
          :key="display.display_id"
          :value="display.display_id"
        >
          {{ displayNameFn(display) }}
          <i
            v-if="display.has_errors"
            class="pi pi-exclamation-triangle text-red-500"
          />
          <i
            v-if="display.has_pending"
            class="pi pi-exclamation-triangle text-yellow-500"
          />
        </Tab>
      </TabList>
      <TabPanels>
        <TabPanel
          v-for="display in thread.displays"
          :key="display.display_id"
          :value="display.display_id"
        >
          <div class="flex flex-col gap-12 pt-4">
            <Panel class="panel pt-5">
              <div class="grid grid-cols-2 gap-4 2xl:grid-cols-4">
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ $t('eventList.firstInteraction') }}
                  </span>
                  <Tag
                    :value="formattedDate(display.started_at)"
                    severity="secondary"
                  />
                </div>
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ $t('eventList.lastInteraction') }}
                  </span>
                  <Tag
                    :value="formattedDate(display.ended_at)"
                    severity="secondary"
                  />
                </div>
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ $t('eventList.pending') }}
                  </span>
                  <Tag
                    v-if="display.has_pending"
                    severity="warn"
                    :value="pendingType(display)"
                  />
                  <Tag
                    v-else
                    severity="success"
                    :value="$t('eventList.no')"
                  />
                </div>
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ $t('eventList.status') }}
                  </span>
                  <Tag
                    v-if="display.has_errors"
                    severity="danger"
                    :value="$t('eventList.error')"
                  />
                  <Tag
                    v-else
                    severity="success"
                    :value="$t('eventList.successful')"
                  />
                </div>
              </div>
            </Panel>
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
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { useRouteQuery } from '@vueuse/router'
import { format } from 'date-fns'
import { ref } from 'vue'

import type {
  DisplayStatistics, RunStatistics,
  ThreadDto,
  WsServerEvent,
} from '@core/sdk/client'

const props = defineProps<{
  events: WsServerEvent[]
  thread: ThreadDto
}>()

const route = useRoute()
const { pendingType } = useThreadUtils()

const activeDisplayId = useRouteQuery('display')
const activeRuns = ref<RunStatistics[]>([])

onMounted(() => {
  activeDisplayId.value = activeDisplayId.value ?? props.thread.displays?.at(-1)?.display_id
})

watch(() => route.query, () => {
  activeRuns.value = props.thread.displays?.find((display: DisplayStatistics) => display.display_id === activeDisplayId.value)?.runs ?? []
}, { immediate: true })

const eventsInRuns = computed<WsServerEvent[]>(() => {
  const runIds = activeRuns.value.map((run: RunStatistics) => run.run_id)
  return props.events.filter((event: WsServerEvent) => runIds.includes(event.run_id))
})

const { resolveComponentForEvent } = useEventComponent()

const displayNameFn = (display: DisplayStatistics) => format(new Date(display.started_at), 'dd.MM.yyyy HH:mm')
const runNameFn = (run: RunStatistics) => run.agent.agent_config.name
const formattedDate = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY HH:mm:ss')
</script>

<style scoped>
.customized-timeline :deep(.p-timeline-event-opposite){
  width: 60px;
  max-width: 60px;
}
.panel :deep(.p-panel-header) {
  padding: 0 !important;
}
</style>
