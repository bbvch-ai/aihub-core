<template>
  <div class="flex flex-col gap-4">
    <!-- SelectButton for List/Graph toggle -->
    <SelectButton
      v-model="selectedView"
      :options="viewOptions"
      option-label="label"
      option-value="value"
      size="small"
    />

    <!-- List View -->
    <div v-if="selectedView === 'list'">
      <div
        v-if="agentMemoriesAreLoading"
        class="flex items-center justify-center p-8"
      >
        <ProgressSpinner />
      </div>
      <div v-else>
        <MemoryList
          :memories="agentPaginatedMemories"
          :current-page="agentCurrentPage"
          :total-pages="agentTotalPages"
          :hide-agent-column="true"
          @next-page="agentNextPage"
          @prev-page="agentPrevPage"
        />
      </div>
    </div>

    <!-- Graph View -->
    <div v-else-if="selectedView === 'graph'">
      <div
        v-if="allMemoriesAreLoading"
        class="flex items-center justify-center p-8"
      >
        <ProgressSpinner />
      </div>
      <div
        v-else
        class="h-[600px]"
      >
        <MemoryGraph
          :memories="allMemoriesData?.memories || []"
          :relations="allRelations"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  agentClass: string
  agentId: string
}>()

const { t } = useI18n()

// View selection
const selectedView = ref<'list' | 'graph'>('list')
const viewOptions = [
  { label: t('openwebui.memories.list'), value: 'list' },
  { label: t('openwebui.memories.graph'), value: 'graph' },
]

// Query 1: Agent-specific memories for LIST view (filtered by agent)
const { useMemories: useAgentMemories } = createMemoryComposables({
  type: 'user',
  agent_class: props.agentClass,
  agent_id: props.agentId,
  // No thread_id filter - show all memories from this agent
})

const {
  paginatedMemories: agentPaginatedMemories,
  currentPage: agentCurrentPage,
  totalPages: agentTotalPages,
  memoriesAreLoading: agentMemoriesAreLoading,
  nextPage: agentNextPage,
  prevPage: agentPrevPage,
} = useAgentMemories()

// Query 2: ALL user memories for GRAPH view (no agent filter to get relations)
const { useMemories: useAllMemories } = createMemoryComposables({
  type: 'user',
  // No filters - fetch ALL user memories to get relations across all agents
})

const {
  memoriesData: allMemoriesData,
  allRelations,
  memoriesAreLoading: allMemoriesAreLoading,
} = useAllMemories()
</script>
