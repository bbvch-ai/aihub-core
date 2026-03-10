<template>
  <StructuralColumn
    :title="t(`${translationPrefix}.memories.title`)"
    :loading="memoriesAreLoading || contextLoading"
  >
    <div class="flex h-full flex-col gap-2">
      <div class="mb-4">
        <span class="text-sm text-surface-500 dark:text-surface-400">
          {{ t(`${translationPrefix}.memories.description`, { [contextNameKey]: contextName }) }}
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
          :hide-agent-column="hideAgentColumn"
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

interface Props {
  translationPrefix: 'thread' | 'agent'
  contextName: string
  contextLoading: boolean
  memoryContext: {
    type: 'user'
    thread_id?: string
    agent_class?: string
    agent_id?: string
  }
  basePath: string
  hideAgentColumn?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  hideAgentColumn: false,
})

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const confirm = useConfirm()
const toast = useToast()

// Context-specific key for translation (threadName vs agentName)
const contextNameKey = computed(() => {
  return props.translationPrefix === 'thread' ? 'threadName' : 'agentName'
})

// Create memory composables with provided context
const { useMemories, useMemorySearch, useDeleteMemory } = createMemoryComposables(props.memoryContext)

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
  router.push(localePath(`${props.basePath}/${memory.id}?q=${searchInput.value ?? ''}`))
}

const handleDeleteAll = () => {
  confirm.require({
    message: t(`${props.translationPrefix}.memories.delete_all.confirm_message`),
    header: t(`${props.translationPrefix}.memories.delete_all.confirm_header`),
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteAllMemories()
        toast.add({
          severity: 'success',
          summary: t(`${props.translationPrefix}.memories.delete_all.success.title`),
          detail: t(`${props.translationPrefix}.memories.delete_all.success.message`),
          life: 3000,
        })
      }
      catch (error) {
        console.error(`Failed to delete ${props.translationPrefix} memories:`, error)
        toast.add({
          severity: 'error',
          summary: t(`${props.translationPrefix}.memories.delete_all.error.title`),
          detail: t(`${props.translationPrefix}.memories.delete_all.error.message`),
          life: 5000,
        })
      }
    },
  })
}
</script>
