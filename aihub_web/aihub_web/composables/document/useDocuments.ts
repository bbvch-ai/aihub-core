import { type DocumentDto, getDocumentsForNamespace } from '@core/sdk/client'

export const useDocuments = defineQuery(() => {
  const route = useRoute()
  const currentPage = ref(1)
  const pageSize = ref(10)

  const database = computed(() => route.params.db as string)
  const namespace = computed(() => route.params.namespace as string)

  const documentsQuery = useQuery({
    key: () => ['knowledge', 'databases', database.value, 'namespaces', namespace.value, 'documents', { page: currentPage.value, size: pageSize.value }],
    enabled: () => !!database.value && !!namespace.value,
    query: async () => {
      const pageToFetch = Math.max(1, currentPage.value)

      return await getDocumentsForNamespace({
        composable: '$fetch',
        query: {
          page: pageToFetch,
          page_size: pageSize.value,
        },
        path: {
          database: database.value,
          namespace: namespace.value,
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
