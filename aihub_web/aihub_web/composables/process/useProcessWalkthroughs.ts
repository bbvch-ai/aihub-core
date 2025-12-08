import { getProcessWalkthroughs, type ProcessWalkthroughDto } from '@core/sdk/client'

export const useProcessWalkthroughs = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('process_class', 'process_id')

  const currentPage = ref(1)
  const pageSize = ref(10)

  const processClass = computed(() => route.params.process_class as string)
  const processId = computed(() => route.params.process_id as string)

  const walkthroughsQuery = useQuery({
    key: () => ['process-walkthroughs', processClass.value, processId.value, { page: currentPage.value, size: pageSize.value }],
    enabled: isRouteReady,
    query: async () => {
      const pageToFetch = Math.max(1, currentPage.value)

      return await getProcessWalkthroughs({
        composable: '$fetch',
        path: {
          process_class: processClass.value,
          process_id: processId.value,
        },
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
    const data = walkthroughsQuery.state.value?.data

    return {
      total: data?.total ?? 0,
      currentPage: data?.page ?? currentPage.value,
      pageSize: data?.page_size ?? pageSize.value,
      totalPages: data?.total_pages ?? 0,
    }
  })

  const walkthroughs = computed(() => (walkthroughsQuery.state.value?.data)?.walkthroughs ?? [] as ProcessWalkthroughDto[])

  const isLoading = computed(() => walkthroughsQuery.asyncStatus.value === 'loading')

  return {
    walkthroughs,
    isLoading,
    pagination: paginationMeta,
    currentPage,
    pageSize,
    setPage,
    setPageSize,
    refetch: walkthroughsQuery.refetch,
  }
})
