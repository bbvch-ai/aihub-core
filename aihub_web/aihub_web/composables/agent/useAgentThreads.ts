import { getAgentThreads } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

export const useAgentThreads = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('agent_id', 'agent_class')

  // Pagination state
  const currentPage = ref(1)
  const pageSize = ref(10)

  // Query to fetch paginated threads
  const threadQuery = useQuery({
    key: () => ['agent-threads', route.params.agent_id as string, route.params.agent_class as string, currentPage.value, pageSize.value],
    enabled: isRouteReady,
    query: async () => {
      return await getAgentThreads({
        composable: '$fetch',
        path: {
          agent_id: route.params.agent_id as string,
          agent_class: route.params.agent_class as string,
        },
        query: {
          page: currentPage.value,
          page_size: pageSize.value,
        },
      })
    },
    placeholderData: previousData => previousData, // Keep previous data while fetching
  })

  // Update page size and refetch
  const setPageSize = (newSize: number) => {
    pageSize.value = newSize
    // When changing page size, reset to first page to avoid out-of-range issues
    currentPage.value = 1
  }

  // Update current page and refetch
  const setPage = (newPage: number) => {
    currentPage.value = newPage
  }

  // Extract pagination metadata
  const paginationMeta = computed(() => {
    const data = threadQuery.state.value?.data

    return {
      total: data?.total ?? 0,
      currentPage: data?.page ?? 1,
      pageSize: data?.page_size ?? 10,
      totalPages: data?.total_pages ?? 1,
    }
  })

  return {
    threads: computed(() => (threadQuery.state.value?.data)?.threads ?? []),
    isLoading: computed(() => threadQuery.asyncStatus.value === 'loading'),
    pagination: paginationMeta,
    currentPage,
    pageSize,
    setPage,
    setPageSize,
    refetch: threadQuery.refetch,
  }
})
