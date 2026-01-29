<template>
  <div class="flex h-full flex-col">
    <DataTable
      :value="memories"
      :loading="loading"
      :selection="selectedMemory"
      selection-mode="single"
      :meta-key-selection="false"
      data-key="id"
      class="flex-1"
      size="small"
      scrollable
      scroll-height="flex"
      striped-rows
      @update:selection="handleSelection"
    >
      <Column
        field="memory"
        :header="t('memory.table.memory')"
        style="min-width: 300px"
      >
        <template #body="slotProps">
          <div class="line-clamp-2 text-surface-700 dark:text-surface-200">
            {{ slotProps.data.memory }}
          </div>
        </template>
      </Column>

      <Column
        v-if="!hideAgentColumn"
        field="agent_id"
        :header="t('memory.table.agent')"
        style="width: 200px"
      >
        <template #body="slotProps">
          <Tag
            v-if="slotProps.data.agent_id"
            :value="slotProps.data.agent_id"
            severity="secondary"
            class="font-mono"
          />
          <span
            v-else
            class="text-surface-400 dark:text-surface-500"
          >-</span>
        </template>
      </Column>
      <Column
        field="created"
        :header="t('memory.table.created')"
        style="width: 160px"
      >
        <template #body="slotProps">
          <div class="flex flex-col">
            <span class="text-sm font-medium text-surface-700 dark:text-surface-200">
              {{ useDateFormat(slotProps.data.created, 'DD.MM.YYYY') }}
            </span>
            <span class="text-xs text-surface-500 dark:text-surface-400">
              {{ useDateFormat(slotProps.data.created, 'HH:mm:ss') }}
            </span>
          </div>
        </template>
      </Column>
      <Column
        field="score"
        :header="t('memory.table.score')"
        style="width: 120px"
      >
        <template #body="slotProps">
          <Tag
            v-if="slotProps.data.score != null"
            :value="(1/slotProps.data.score).toFixed(2)"
            :severity="getScoreSeverity(1/slotProps.data.score)"
            rounded
          />
          <span
            v-else
            class="text-surface-400 dark:text-surface-500"
          >-</span>
        </template>
      </Column>
    </DataTable>

    <div
      v-if="totalPages > 1"
      class="flex items-center justify-between border-t p-4"
    >
      <Button
        icon="pi pi-chevron-left"
        :disabled="currentPage === 1"
        text
        @click="emit('prevPage')"
      />
      <span class="text-sm text-gray-600">
        {{ t('memory.table.pagination', { currentPage, totalPages }) }}
      </span>
      <Button
        icon="pi pi-chevron-right"
        :disabled="currentPage === totalPages"
        text
        @click="emit('nextPage')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { MemoryDto } from '@core/sdk/client'

interface Props {
  memories: MemoryDto[]
  loading?: boolean
  currentPage: number
  totalPages: number
  selectedMemoryId?: string
  hideAgentColumn?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  selectMemory: [memory: MemoryDto]
  nextPage: []
  prevPage: []
  goToPage: [page: number]
}>()

const selectedMemory = computed(() => {
  return props.memories.find(memory => memory.id === props.selectedMemoryId)
})

const { t } = useI18n()

const handleSelection = (memory: MemoryDto) => {
  emit('selectMemory', memory)
}

const getScoreSeverity = (score: number) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'info'
  if (score >= 0.4) return 'warn'
  return 'danger'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
