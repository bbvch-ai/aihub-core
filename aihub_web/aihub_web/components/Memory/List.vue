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
      @update:selection="handleSelection"
    >
      <Column
        field="memory"
        :header="t('memory.table.memory')"
        style="min-width: 300px"
      >
        <template #body="slotProps">
          <div class="line-clamp-2">
            {{ slotProps.data.memory }}
          </div>
        </template>
      </Column>

      <Column
        field="agent_id"
        :header="t('memory.table.agent')"
        style="width: 150px"
      >
        <template #body="slotProps">
          <span
            v-if="slotProps.data.agent_id"
            class="font-mono text-sm"
          >
            {{ slotProps.data.agent_id }}
          </span>
          <span
            v-else
            class="text-gray-400"
          >-</span>
        </template>
      </Column>
      <Column
        field="created"
        :header="t('memory.table.created')"
        style="width: 180px"
      >
        <template #body="slotProps">
          <span class="text-sm">
            {{ useDateFormat(slotProps.data.created, 'DD.MM.YYYY HH:mm:ss') }}
          </span>
        </template>
      </Column>
      <Column
        field="score"
        :header="t('memory.table.score')"
        style="width: 100px"
      >
        <template #body="slotProps">
          <span v-if="slotProps.data.score != null">
            {{ slotProps.data.score.toFixed(2) }}
          </span>
          <span
            v-else
            class="text-gray-400"
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
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
