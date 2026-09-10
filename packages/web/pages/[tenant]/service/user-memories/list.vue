<template>
  <StructuralColumn
    :title="t('memory.list.title')"
    :loading="memoriesAreLoading"
  >
    <div
      v-if="paginatedMemories.length > 0"
      class="flex h-full flex-col gap-2"
    >
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
          @select-memory="handleSelectMemory"
          @next-page="nextPage"
          @prev-page="prevPage"
        />
      </div>
    </div>

    <div
      v-else
      class="flex items-center justify-center py-8 text-surface-500"
    >
      <span class="text-xl">{{ t('memory.list.no_results') }}</span>
    </div>
  </StructuralColumn>

  <NuxtPage :selected-memory-id="selectedMemoryId" />
</template>

<script setup lang="ts">
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const tenantPath = useTenantPath()
const confirm = useConfirm()
const toast = useToast()

// Create user memory composables using factory
const { useMemories, useMemorySearch, useDeleteMemory } = createMemoryComposables({
  type: 'user',
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
  router.push(tenantPath(`/service/user-memories/list/${memory.id}?q=${searchInput.value ?? ''}`))
}

const handleDeleteAll = () => {
  confirm.require({
    message: t('memory.delete_all.confirm_message'),
    header: t('memory.delete_all.confirm_header'),
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteAllMemories()
        toast.add({
          severity: 'success',
          summary: t('memory.delete_all.success.title'),
          detail: t('memory.delete_all.success.message'),
          life: 3000,
        })
      }
      catch (error) {
        console.error('Failed to delete all memories:', error)
        toast.add({
          severity: 'error',
          summary: t('memory.delete_all.error.title'),
          detail: t('memory.delete_all.error.message'),
          life: 5000,
        })
      }
    },
  })
}
</script>
