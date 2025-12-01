import { searchMemories, type MemorySearchResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { computed, ref } from 'vue'

export const useMemorySearch = defineQuery(() => {
  const query = ref<string>('')
  const limit = ref(100)

  const {
    data: searchData,
    isPending: searchIsLoading,
  } = useQuery<MemorySearchResponse>({
    key: () => ['memory-search', { query: query.value, limit: limit.value }],
    staleTime: minutesToMilliseconds(1),
    enabled: () => !!query.value,
    query: async () => {
      if (!query.value) {
        return {
          query: '',
          total: 0,
          memories: [],
          relations: [],
        }
      }

      return await searchMemories({
        composable: '$fetch',
        query: {
          query: query.value,
          limit: limit.value,
        },
      })
    },
  })

  const isSearchActive = computed(() => !!query.value)

  const setSearchQuery = (q: string) => {
    query.value = q
  }

  const clearSearch = () => {
    query.value = ''
  }

  return {
    searchData,
    searchIsLoading,
    query,
    isSearchActive,
    setSearchQuery,
    clearSearch,
  }
})
