import { type DocumentDto, getDocumentsForNamespace } from '@core/sdk/client'

export interface SortState {
  field: string | null
  order: 1 | -1
}

export const useDocuments = defineQuery(() => {
  const route = useRoute()
  const { tenantId } = useTenant()

  const currentPage = ref(1)
  const pageSize = ref(10)
  const searchQuery = ref<string | null>(null)
  const sortState = ref<SortState>({ field: null, order: 1 })

  const database = computed(() => route.params.db as string)
  const namespace = computed(() => route.params.namespace as string)

  const documentsQuery = useQuery({
    key: () => ['tenant', tenantId.value, 'knowledge', 'databases', database.value, 'namespaces', namespace.value, 'documents', { page: currentPage.value, size: pageSize.value, search: searchQuery.value, sortField: sortState.value.field, sortOrder: sortState.value.order }],
    enabled: useTenantReady('db', 'namespace'),
    query: async () => {
      const db = database.value
      const ns = namespace.value

      if (!db || !ns) {
        throw new Error('Database and namespace are required')
      }

      const pageToFetch = Math.max(1, currentPage.value)

      return await getDocumentsForNamespace({
        composable: '$fetch',
        query: {
          page: pageToFetch,
          page_size: pageSize.value,
          search: searchQuery.value ?? undefined,
          sort_field: sortState.value.field ?? undefined,
          sort_order: sortState.value.order,
        },
        path: {
          tenant_id: tenantId.value!,
          database: db,
          namespace: ns,
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

  const setSearch = (query: string | null) => {
    searchQuery.value = query && query.trim() ? query.trim() : null
    currentPage.value = 1
  }

  const setSort = (field: string | null, order: 1 | -1 = 1) => {
    sortState.value = { field, order }
    currentPage.value = 1
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

  // Only show loading on initial load, not during refetch/search when we have data
  const isLoading = computed(() => documentsQuery.asyncStatus.value === 'loading' && !documentsQuery.state.value?.data)
  const isFetching = computed(() => documentsQuery.asyncStatus.value === 'loading')

  return {
    documents,
    isLoading,
    isFetching,
    pagination: paginationMeta,
    currentPage,
    pageSize,
    searchQuery,
    sortState,
    setPage,
    setPageSize,
    setSearch,
    setSort,
    refetch: documentsQuery.refetch,
  }
})
