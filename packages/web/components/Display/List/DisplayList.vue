<template>
  <DataTable
    :value="displays"
    table-style="min-width: 50rem"
    selection-mode="single"
    :selection="selectedDisplay"
    size="small"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="Started"
      :header="t('thread.display.list.started')"
    >
      <template #body="{ data }">
        <p>{{ formatted(data.started_at) }}</p>
      </template>
    </Column>
    <Column
      field="duration"
      :header="t('thread.display.list.duration')"
    >
      <template #body="{ data }">
        <Badge :value="data.duration" />
      </template>
    </Column>
    <Column
      field="n_events"
      :header="t('thread.display.list.events')"
    >
      <template #body="{ data }">
        <Badge :value="data.n_events" />
      </template>
    </Column>
    <Column
      field="has_errors"
      :header="t('thread.display.list.status')"
    >
      <template #body="{ data }">
        <Tag
          v-if="data.has_errors"
          severity="danger"
          :value="t('event.list.error')"
        />
        <Tag
          v-else
          severity="success"
          :value="t('event.list.successful')"
        />
      </template>
    </Column>
    <Column
      field="has_pending"
      :header="t('thread.display.list.pending')"
    >
      <template #body="{ data }">
        <Tag
          v-if="data.has_pending"
          severity="warn"
          :value="pendingType(data)"
        />
        <Tag
          v-else
          severity="success"
          :value="t('event.list.no')"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { DisplayStatistics } from '@core/sdk/client'

const route = useRoute()
const { t } = useI18n()

const props = defineProps<{
  displays: DisplayStatistics[]
}>()

const emit = defineEmits<{
  selected: [display: DisplayStatistics]
}>()

const formatted = (datestr: string) => useDateFormat(new Date(datestr), t('thread.display.list.dateFormat'))
const { pendingType } = useThreadUtils()

const selectedDisplay = computed(() => {
  return props.displays.filter((display: DisplayStatistics) => {
    return display.display_id === route.params.display_id
  })
})
</script>
