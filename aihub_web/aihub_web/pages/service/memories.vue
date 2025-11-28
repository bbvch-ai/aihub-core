<script setup lang="ts">
import { useToast } from 'primevue/usetoast'

import { useLocalePath } from '#i18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const toast = useToast()

// Data fetching
const {
  paginatedMemories,
  allRelations,
  currentPage,
  totalPages,
  memoriesAreLoading,
  nextPage,
  prevPage,
} = useMemories()

// Mutations
const { updateMemory } = useUpdateMemory()
const { deleteMemory } = useDeleteMemory()

// Selection state (from route)
const selectedMemoryId = computed(() => route.params.memory_id as string | undefined)

// Handlers
const handleSelectMemory = (memory: { id: string }) => {
  router.push(localePath(`/service/memories/${memory.id}`))
}

const handleCloseDetail = () => {
  router.push(localePath('/service/memories'))
}

const handleUpdateMemory = async (memoryId: string, data: string) => {
  try {
    await updateMemory({ memoryId, data })
    toast.add({
      severity: 'success',
      summary: t('memory.update.success.title'),
      detail: t('memory.update.success.message'),
      life: 3000,
    })
  }
  catch (error) {
    console.error('Failed to update memory:', error)
    toast.add({
      severity: 'error',
      summary: t('memory.update.error.title'),
      detail: t('memory.update.error.message'),
      life: 5000,
    })
  }
}

const handleDeleteMemory = async (memoryId: string) => {
  try {
    await deleteMemory({ memoryId })
    toast.add({
      severity: 'success',
      summary: t('memory.delete.success.title'),
      detail: t('memory.delete.success.message'),
      life: 3000,
    })
    handleCloseDetail()
  }
  catch (error) {
    console.error('Failed to delete memory:', error)
    toast.add({
      severity: 'error',
      summary: t('memory.delete.error.title'),
      detail: t('memory.delete.error.message'),
      life: 5000,
    })
  }
}

const handleSelectNode = (nodeId: string) => {
  const memory = paginatedMemories.value.find(m => m.id === nodeId)
  if (memory) {
    handleSelectMemory(memory)
  }
}
</script>

<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('memory.graph.title')"
      :width="400"
      :loading="memoriesAreLoading"
      class="overflow-hidden"
    >
      <div class="size-full">
        <MemoryGraph
          :relations="allRelations"
          :selected-memory-id="selectedMemoryId"
          @select-node="handleSelectNode"
        />
      </div>
    </StructuralColumn>

    <StructuralColumn
      :title="t('memory.list.title')"
      :loading="memoriesAreLoading"
    >
      <MemoryList
        :memories="paginatedMemories"
        :current-page="currentPage"
        :total-pages="totalPages"
        :selected-memory-id="selectedMemoryId"
        @select-memory="handleSelectMemory"
        @next-page="nextPage"
        @prev-page="prevPage"
      />
    </StructuralColumn>

    <NuxtPage
      :selected-memory-id="selectedMemoryId"
      @close="handleCloseDetail"
      @update="handleUpdateMemory"
      @delete="handleDeleteMemory"
    />
  </StructuralScreen>
</template>
