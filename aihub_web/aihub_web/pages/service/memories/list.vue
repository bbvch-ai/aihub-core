<template>
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

  <NuxtPage :selected-memory-id="selectedMemoryId" />
</template>

<script setup lang="ts">
import { useLocalePath } from '#i18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()

// Data fetching
const {
  paginatedMemories,
  currentPage,
  totalPages,
  memoriesAreLoading,
  nextPage,
  prevPage,
} = useMemories()

// Selection state (from route)
const selectedMemoryId = computed(() => route.params.memory_id as string | undefined)

// Handlers
const handleSelectMemory = (memory: { id: string }) => {
  router.push(localePath(`/service/memories/list/${memory.id}`))
}
</script>
