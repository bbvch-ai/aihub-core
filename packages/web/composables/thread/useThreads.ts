import { getUserThreads, type ThreadDto } from '@core/sdk/client'
import { endOfDay } from 'date-fns/endOfDay'
import { format } from 'date-fns/format'
import { startOfDay } from 'date-fns/startOfDay'

export type ThreadSortField = 'created_at' | 'name'
export type ThreadSortOrder = 1 | -1

export const useThreads = defineQuery(() => {
  const { tenantId } = useTenant()
  const currentPage = ref(1)
  const pageSize = ref(10)
  const sortField = ref<ThreadSortField>('created_at')
  const sortOrder = ref<ThreadSortOrder>(-1)
  const searchQuery = ref<string | null>(null)
  const debouncedSearch = refDebounced(searchQuery, 300)
  const agentInstanceId = useRouteQuery<string | null>('agent_id', null)
  const userSearchId = useRouteQuery<string | null>('user_id', null)
  const status = useRouteQuery<string | null>('status', null)
  const fromDate = useRouteQuery<string | null>('from', null)
  const toDate = useRouteQuery<string | null>('to', null)

  const threadsQuery = useQuery({
    key: () => ['tenant', tenantId.value, 'threads', currentPage.value, pageSize.value, sortField.value, sortOrder.value, debouncedSearch.value, agentInstanceId.value, userSearchId.value, status.value, fromDate.value, toDate.value],
    enabled: useTenantReady(),
    placeholderData: previousData => previousData,
    query: async () => {
      const pageToFetch = Math.max(1, currentPage.value)

      return await getUserThreads({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        query: {
          page: pageToFetch,
          page_size: pageSize.value,
          sort_field: sortField.value,
          sort_order: sortOrder.value,
          search: debouncedSearch.value || undefined,
          agent_id: agentInstanceId.value || undefined,
          user_id: userSearchId.value || undefined,
          status: status.value || undefined,
          from: fromDate.value ? startOfDay(new Date(fromDate.value)).toISOString() : undefined,
          to: toDate.value ? endOfDay(new Date(toDate.value)).toISOString() : undefined,
        },
      })
    },
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

  const isLoading = computed(() => threadsQuery.asyncStatus.value === 'loading' && !threadsQuery.state.value?.data)

  const setSort = (field: ThreadSortField, order: ThreadSortOrder) => {
    sortField.value = field
    sortOrder.value = order
    currentPage.value = 1
  }

  const dateRange = computed<(Date | null)[] | null>({
    get() {
      if (!fromDate.value && !toDate.value) return null

      return [
        fromDate.value ? new Date(fromDate.value) : null,
        toDate.value ? new Date(toDate.value) : null,
      ]
    },
    set(range) {
      const [start, end] = range ?? [null, null]
      if (range && start && !end) return

      fromDate.value = start ? format(start, 'yyyy-MM-dd') : null
      toDate.value = end ? format(end, 'yyyy-MM-dd') : null
      currentPage.value = 1
    },
  })

  watch([status, agentInstanceId, userSearchId, debouncedSearch], () => currentPage.value = 1)

  return {
    threads,
    isLoading,
    pagination: paginationMeta,
    currentPage,
    pageSize,
    setPage,
    setPageSize,
    setSort,
    refetch: threadsQuery.refetch,
    sortField,
    sortOrder,
    searchQuery,
    agentInstanceId,
    userSearchId,
    status,
    dateRange,
  }
})
