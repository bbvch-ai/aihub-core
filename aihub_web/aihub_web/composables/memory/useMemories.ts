import { getMemories, type MemoriesResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { computed, ref } from 'vue'

export const useMemories = defineQuery(() => {
  const currentPage = ref(1)
  const pageSize = ref(20)

  const {
    data: memoriesData,
    isPending: memoriesAreLoading,
  } = useQuery<MemoriesResponse>({
    key: () => ['memories'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getMemories({
        composable: '$fetch',
        query: {
          limit: 1000,
        },
      })
    },
  })

  const paginatedMemories = computed(() => {
    if (!memoriesData.value) return []
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return memoriesData.value.memories.slice(start, end)
  })

  const totalPages = computed(() => {
    if (!memoriesData.value) return 0
    return Math.ceil(memoriesData.value.memories.length / pageSize.value)
  })

  const allRelations = computed(() => {
    return memoriesData.value?.relations || []
  })

  const nextPage = () => {
    if (currentPage.value < totalPages.value) {
      currentPage.value++
    }
  }

  const prevPage = () => {
    if (currentPage.value > 1) {
      currentPage.value--
    }
  }

  return {
    memoriesData,
    memoriesAreLoading,
    paginatedMemories,
    allRelations,
    currentPage,
    pageSize,
    totalPages,
    nextPage,
    prevPage,
  }
})
