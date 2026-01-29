<template>
  <StructuralColumn
    :title="t('agent.memories.title')"
    :loading="memoriesAreLoading || agentIsLoading"
  >
    <div class="flex h-full flex-col gap-2">
      <div class="mb-4">
        <span class="text-sm text-surface-500 dark:text-surface-400">
          {{ t('agent.memories.description', { agentName: agent?.agent_config.name }) }}
        </span>
      </div>

      <div class="flex w-full items-center justify-between gap-2">
        <div class="flex flex-1 items-center gap-2">
          <IconField class="flex-1">
            <InputIcon>
              <i class="pi pi-search" />
            </InputIcon>
            <InputText
              v-model="searchInput"
              :placeholder="t('memory.search.placeholder')"
              class="w-full"
              @keyup.enter="handleSearch"
            />
          </IconField>
          <Button
            icon="pi pi-search"
            :label="t('memory.search.button')"
            :loading="isSearchButtonLoading"
            @click="handleSearch"
          />
          <Button
            v-if="isSearchActive"
            icon="pi pi-times"
            severity="secondary"
            :label="t('memory.search.clear')"
            @click="handleClearSearch"
          />
        </div>
        <Button
          v-tooltip.top="t('memory.delete_all.button')"
          icon="pi pi-trash"
          severity="danger"
          text
          rounded
          @click="handleDeleteAll"
        />
      </div>

      <div class="flex-1">
        <MemoryList
          :memories="displayedMemories"
          :current-page="displayedCurrentPage"
          :total-pages="displayedTotalPages"
          :selected-memory-id="selectedMemoryId"
          :hide-agent-column="true"
          @select-memory="handleSelectMemory"
          @next-page="nextPage"
          @prev-page="prevPage"
        />
      </div>
    </div>
  </StructuralColumn>

  <NuxtPage :selected-memory-id="selectedMemoryId" />
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

import { useLocalePath } from '#i18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const confirm = useConfirm()
const toast = useToast()

// Get agent info
const { agent, agentIsLoading } = useAgent()

// Create agent-specific memory composables
const { useMemories, useMemorySearch, useDeleteMemory } = createMemoryComposables({
  type: 'user',
  agent_class: route.params.agent_class as string,
  agent_id: route.params.agent_id as string,
})

const {
  paginatedMemories,
  currentPage,
  totalPages,
  memoriesAreLoading,
  nextPage,
  prevPage,
} = useMemories()

const {
  searchData,
  searchIsLoading,
  isSearchActive,
  setSearchQuery,
  clearSearch,
} = useMemorySearch()

const { deleteAllMemories } = useDeleteMemory()

// Use shared search filter composable
const {
  searchInput,
  isSearchButtonLoading,
  displayedMemories,
  displayedCurrentPage,
  displayedTotalPages,
  handleSearch,
  handleClearSearch,
} = useMemorySearchFilter({
  searchData,
  paginatedMemories,
  isSearchActive,
  setSearchQuery,
  clearSearch,
  searchIsLoading,
  currentPage,
  totalPages,
})

const selectedMemoryId = computed(() => route.params.memory_id as string | undefined)

const handleSelectMemory = (memory: { id: string }) => {
  const agentPath = `/service/agents/${route.params.agent_class}-${route.params.agent_id}/memories`
  router.push(localePath(`${agentPath}/${memory.id}?q=${searchInput.value ?? ''}`))
}

const handleDeleteAll = () => {
  confirm.require({
    message: t('agent.memories.delete_all.confirm_message'),
    header: t('agent.memories.delete_all.confirm_header'),
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteAllMemories()
        toast.add({
          severity: 'success',
          summary: t('agent.memories.delete_all.success.title'),
          detail: t('agent.memories.delete_all.success.message'),
          life: 3000,
        })
      }
      catch (error) {
        console.error('Failed to delete agent memories:', error)
        toast.add({
          severity: 'error',
          summary: t('agent.memories.delete_all.error.title'),
          detail: t('agent.memories.delete_all.error.message'),
          life: 5000,
        })
      }
    },
  })
}
</script>
