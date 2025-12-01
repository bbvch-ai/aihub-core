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

const { deleteAllMemories } = useDeleteAllMemories()

const searchInput = useRouteQuery('q', '')
const isSearchButtonLoading = computed(() => isSearchActive.value && searchIsLoading.value)

// Sync URL query param with search on mount
onMounted(() => {
  if (searchInput.value) {
    setSearchQuery(searchInput.value as string)
  }
})

const selectedMemoryId = computed(() => route.params.memory_id as string | undefined)

const displayedMemories = computed(() => {
  return isSearchActive.value && searchData.value
    ? searchData.value.memories
    : paginatedMemories.value
})

const displayedCurrentPage = computed(() => {
  return isSearchActive.value ? 1 : currentPage.value
})

const displayedTotalPages = computed(() => {
  return isSearchActive.value ? 1 : totalPages.value
})

const handleSelectMemory = (memory: { id: string }) => {
  router.push(localePath(`/service/memories/list/${memory.id}?q=${searchInput.value ?? ''}`))
}

const handleSearch = () => {
  setSearchQuery(searchInput.value)
}

const handleClearSearch = () => {
  searchInput.value = null
  clearSearch()
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

<template>
  <StructuralColumn
    :title="t('memory.list.title')"
    :loading="memoriesAreLoading"
  >
    <div class="flex h-full flex-col gap-2">
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
  </StructuralColumn>

  <NuxtPage :selected-memory-id="selectedMemoryId" />
</template>
