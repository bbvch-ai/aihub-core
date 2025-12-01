<template>
  <StructuralColumn
    :title="t('memory.graph.title')"
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
  allRelations,
  memoriesAreLoading,
} = useMemories()

// Selection state (from route)
const selectedMemoryId = computed(() => route.params.memory_id as string | undefined)

// Handlers
const handleSelectNode = (nodeId: string) => {
  const memory = paginatedMemories.value.find(m => m.id === nodeId)
  if (memory) {
    router.push(localePath(`/service/memories/graph/${memory.id}`))
  }
}
</script>
