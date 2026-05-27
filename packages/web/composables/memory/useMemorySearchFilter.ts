import { computed, onMounted } from 'vue'

import type { Ref } from 'vue'

export interface UseMemorySearchFilterOptions {
  searchData: Ref<{ memories: unknown[] } | undefined>
  paginatedMemories: Ref<unknown[]>
  isSearchActive: Ref<boolean>
  setSearchQuery: (query: string) => void
  clearSearch: () => void
  searchIsLoading: Ref<boolean>
  currentPage?: Ref<number>
  totalPages?: Ref<number>
}

/**
 * Shared composable for memory search and filtering logic.
 * Eliminates duplication across user/org list and graph pages.
 *
 * Provides:
 * - Search input synced with URL query param
 * - Displayed memories (search results or paginated)
 * - Search/clear handlers
 * - Loading states
 *
 * @param options - Memory search composable outputs from factory
 * @returns Search filter state and handlers
 */
export function useMemorySearchFilter(options: UseMemorySearchFilterOptions) {
  const searchInput = useRouteQuery('q', '')
  const isSearchButtonLoading = computed(() =>
    options.isSearchActive.value && options.searchIsLoading.value,
  )

  // Sync URL query param with search on mount
  onMounted(() => {
    if (searchInput.value) {
      options.setSearchQuery(searchInput.value as string)
    }
  })

  const displayedMemories = computed(() => {
    return options.isSearchActive.value && options.searchData.value
      ? options.searchData.value.memories
      : options.paginatedMemories.value
  })

  const displayedCurrentPage = computed(() => {
    return options.isSearchActive.value ? 1 : (options.currentPage?.value ?? 1)
  })

  const displayedTotalPages = computed(() => {
    return options.isSearchActive.value ? 1 : (options.totalPages?.value ?? 1)
  })

  const handleSearch = () => {
    options.setSearchQuery(searchInput.value)
  }

  const handleClearSearch = () => {
    searchInput.value = null
    options.clearSearch()
  }

  return {
    searchInput,
    isSearchButtonLoading,
    displayedMemories,
    displayedCurrentPage,
    displayedTotalPages,
    handleSearch,
    handleClearSearch,
  }
}
