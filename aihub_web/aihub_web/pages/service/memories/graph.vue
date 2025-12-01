<script setup lang="ts">
import { useLocalePath } from '#i18n'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()

const {
  paginatedMemories,
  allRelations,
  memoriesAreLoading,
} = useMemories()

const {
  searchData,
  searchIsLoading,
  isSearchActive,
  setSearchQuery,
  clearSearch,
} = useMemorySearch()

const searchInput = useRouteQuery('q', '')
const isSearchButtonLoading = computed(() => isSearchActive.value && searchIsLoading.value)

// Sync URL query param with search on mount
onMounted(() => {
  if (searchInput.value) {
    setSearchQuery(searchInput.value as string)
  }
})

const selectedMemoryId = computed(() => route.params.memory_id as string | undefined)

const handleSelectNode = (nodeId: string) => {
  const memory = paginatedMemories.value.find(m => m.id === nodeId)
  if (memory) {
    router.push(localePath(`/service/memories/graph/${memory.id}`))
  }
}

const handleSearch = () => {
  setSearchQuery(searchInput.value)
}

const handleClearSearch = () => {
  searchInput.value = null
  clearSearch()
}
</script>

<template>
  <StructuralColumn
    :title="t('memory.graph.title')"
    :loading="memoriesAreLoading"
    class="overflow-hidden"
  >
    <div class="flex h-full flex-col gap-2">
      <div class="flex w-full items-center gap-2">
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

      <div class="flex-1">
        <MemoryGraph
          :relations="allRelations"
          :selected-memory-id="selectedMemoryId"
          :search-results="isSearchActive ? searchData : null"
          @select-node="handleSelectNode"
        />
      </div>
    </div>
  </StructuralColumn>

  <NuxtPage :selected-memory-id="selectedMemoryId" />
</template>
