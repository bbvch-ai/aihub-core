import { getUserThreads, type ThreadDto } from '@core/sdk/client'

export const useThreads = defineQuery(() => {
  const currentPage = ref(1)
  const pageSize = ref(10)

  const threadsQuery = useQuery({
    key: () => ['threads', { page: currentPage.value, size: pageSize.value }],
    enabled: true,
    query: async () => {
      const pageToFetch = Math.max(1, currentPage.value)

      return await getUserThreads({
        composable: '$fetch',
        query: {
          page: pageToFetch,
          page_size: pageSize.value,
        },
      })
    },
    placeholderData: previousData => previousData,
  })

  const setPageSize = (newSize: number) => {
    if (newSize > 0) {
      pageSize.value = newSize
      currentPage.value = 1
    }
  }

  const setPage = (newPage: number) => {
    if (newPage > 0) {
      currentPage.value = newPage
    }
  }

  const paginationMeta = computed(() => {
    const data = threadsQuery.state.value?.data

    return {
      total: data?.total ?? 0,
      currentPage: data?.page ?? currentPage.value,
      pageSize: data?.page_size ?? pageSize.value,
      totalPages: data?.total_pages ?? 0,
    }
  })

  const threads = computed(() => (threadsQuery.state.value?.data)?.threads ?? [] as ThreadDto[])

  const isLoading = computed(() => threadsQuery.asyncStatus.value === 'loading')

  return {
    threads,
    isLoading,
    pagination: paginationMeta,
    currentPage,
    pageSize,
    setPage,
    setPageSize,
    refetch: threadsQuery.refetch,
  }
})
