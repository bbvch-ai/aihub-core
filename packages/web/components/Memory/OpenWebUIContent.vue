<template>
  <div
    v-if="memoriesAreLoading"
    class="flex items-center justify-center p-8"
  >
    <ProgressSpinner />
  </div>
  <MemoryList
    v-else
    :memories="paginatedMemories"
    :current-page="currentPage"
    :total-pages="totalPages"
    :hide-agent-column="true"
    @next-page="nextPage"
    @prev-page="prevPage"
  />
</template>

<script setup lang="ts">
const props = defineProps<{
  agentClass: string
  agentId: string
}>()

// No thread_id filter - show all memories from this agent
const { useMemories } = createMemoryComposables({
  type: 'user',
  agent_class: props.agentClass,
  agent_id: props.agentId,
})

const {
  paginatedMemories,
  currentPage,
  totalPages,
  memoriesAreLoading,
  nextPage,
  prevPage,
} = useMemories()
</script>
