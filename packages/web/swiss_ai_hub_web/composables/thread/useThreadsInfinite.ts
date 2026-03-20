import { getUserThreads, type ThreadDto } from '@core/sdk/client'
import { useInfiniteQuery } from '@pinia/colada'

export const useThreadsInfinite = defineQuery(() => {
  const PAGE_SIZE = 10

  const {
    state,
    loadMore: loadMoreThreads,
    isLoading: threadsAreLoading,
  } = useInfiniteQuery({
    key: () => ['threads'],
    query: async ({ nextPage }) => {
      if (nextPage === null) return null

      return await getUserThreads({
        composable: '$fetch',
        query: {
          page: nextPage,
          page_size: PAGE_SIZE,
        },
      })
    },
    initialPage: {
      threads: [] as ThreadDto[],
      nextPage: 1 as number | null,
      totalThreads: 0,
      totalPages: 0,
    },
    merge(accumulated, newData) {
      // If no new data was returned, return the accumulated data
      if (!newData) return accumulated

      return {
        threads: [...accumulated.threads, ...newData.threads],
        nextPage: newData.page < newData.total_pages ? newData.page + 1 : null,
        totalThreads: newData.total,
        totalPages: newData.total_pages,
      }
    },
  })

  // Computed property for hasMore
  const hasMoreThreads = computed(() => state.value?.data?.nextPage !== null)

  // Expose only the necessary data and functions
  return {
    threads: computed(() => state.value?.data?.threads || []),
    threadsAreLoading,
    hasMoreThreads,
    totalThreads: computed(() => state.value?.data?.totalThreads || 0),
    totalPages: computed(() => state.value?.data?.totalPages || 0),
    loadMoreThreads,
  }
})
