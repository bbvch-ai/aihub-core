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
              <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ t('event.list.firstInteraction') }}
                  </span>
                  <Tag
                    :value="formattedDate(display.started_at)"
                    severity="secondary"
                  />
                </div>
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ t('event.list.lastInteraction') }}
                  </span>
                  <Tag
                    :value="formattedDate(display.ended_at)"
                    severity="secondary"
                  />
                </div>
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ t('event.list.pending') }}
                  </span>
                  <Tag
                    v-if="display.has_pending"
                    severity="warn"
                    :value="pendingType(display)"
                  />
                  <Tag
                    v-else
                    severity="success"
                    :value="t('event.list.no')"
                  />
                </div>
                <div class="flex flex-col items-start gap-2">
                  <span class="font-semibold">
                    {{ t('event.list.status') }}
                  </span>
                  <Tag
                    v-if="display.has_errors"
                    severity="danger"
                    :value="t('event.list.error')"
                  />
                  <Tag
                    v-else
                    severity="success"
                    :value="t('event.list.successful')"
                  />
                </div>
              </div>
            </Panel>
            <EventList
              :events="events"
              :thread="thread"
              :display-id="activeDisplayId"
              :show-chat="showChat"
            />
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns'

import type {
  DisplayStatistics,
  ThreadDto,
  ContextualizedAgentEvent,
} from '@core/sdk/client'

const props = withDefaults(defineProps<{
  events: ContextualizedAgentEvent[]
  thread: ThreadDto
  displayId?: string
  showChat?: boolean
}>(), {
  showChat: false,
})

const { pendingType } = useThreadUtils()
const { t } = useI18n()

const activeDisplayId = ref(props.thread.displays?.at(-1)?.display_id)

watch(() => props.displayId, (newDisplayId) => {
  activeDisplayId.value = newDisplayId
})

const displayNameFn = (display: DisplayStatistics) => format(new Date(display.started_at), 'dd.MM.yyyy HH:mm')
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
