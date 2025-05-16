import { type DocumentDto, getDocumentsForNamespace } from '@core/sdk/client'

export const useDocuments = defineQuery(() => {
  const route = useRoute()
  const currentPage = ref(1)
  const pageSize = ref(10)

  const documentsQuery = useQuery({
    key: () => ['knowledge', 'db', route.params.db as string, 'namespace', route.params.namespace as string, 'document', { page: currentPage.value, size: pageSize.value }],
    query: async () => {
      const pageToFetch = Math.max(1, currentPage.value)

      return await getDocumentsForNamespace({
        composable: '$fetch',
        query: {
          page: pageToFetch,
          page_size: pageSize.value,
        },
        path: {
          db: route.params.db,
          namespace: route.params.namespace,
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
    const data = documentsQuery.state.value?.data

    return {
      total: data?.total ?? 0,
      currentPage: data?.page ?? currentPage.value,
      pageSize: data?.page_size ?? pageSize.value,
      totalPages: data?.total_pages ?? 0,
    }
  })

  const documents = computed(() => (documentsQuery.state.value?.data)?.documents ?? [] as DocumentDto[])

  const isLoading = computed(() => documentsQuery.asyncStatus.value === 'loading')

  return {
    documents,
    isLoading,
    pagination: paginationMeta,
    currentPage,
    pageSize,
    setPage,
    setPageSize,
    refetch: documentsQuery.refetch,
  }
})
