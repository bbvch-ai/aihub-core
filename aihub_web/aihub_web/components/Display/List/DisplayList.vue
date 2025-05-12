<template>
  <DataTable
    :value="displays"
    table-style="min-width: 50rem"
    selection-mode="single"
    @update:selection="emit('selected', $event)"
  >
    <Column
      field="Started"
      header="Started"
    >
      <template #body="{ data }">
        <p>{{ formatted(data.started_at) }}</p>
      </template>
    </Column>
    <Column
      field="duration"
      header="Duration"
    >
      <template #body="{ data }">
        <Badge :value="data.duration" />
      </template>
    </Column>
    <Column
      field="n_events"
      header="Events"
    >
      <template #body="{ data }">
        <Badge :value="data.n_events" />
      </template>
    </Column>
    <Column
      field="has_errors"
      header="Status"
    >
      <template #body="{ data }">
        <Tag
          v-if="data.has_errors"
          severity="danger"
          :value="t('eventList.error')"
        />
        <Tag
          v-else
          severity="success"
          :value="t('eventList.successful')"
        />
      </template>
    </Column>
    <Column
      field="has_pending"
      header="Pending"
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
          :value="t('eventList.no')"
        />
      </template>
    </Column>
  </DataTable>
</template>

<script setup lang="ts">
import type { DisplayStatistics } from '@core/sdk/client'

const { t } = useI18n()

defineProps<{
  displays: DisplayStatistics[]
}>()

const emit = defineEmits<{
  selected: [display: DisplayStatistics]
}>()

const formatted = (datestr: string) => useDateFormat(new Date(datestr), 'DD.MM.YYYY HH:mm:ss')
const { pendingType } = useThreadUtils()
</script>

<style scoped>

</style>
