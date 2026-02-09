import { getUsers, type UserDto } from '@core/sdk/client'

export default defineQuery(() => {
  const currentPage = ref(1)
  const pageSize = ref(20)

  const usersQuery = useQuery({
    key: () => ['users', { page: currentPage.value, size: pageSize.value }],
    enabled: true,
    query: async () => {
      const pageToFetch = Math.max(1, currentPage.value)

      return await getUsers({
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

  const pagination = computed(() => {
    const data = usersQuery.data.value
    return {
      total: data?.total ?? 0,
      currentPage: data?.page ?? currentPage.value,
      pageSize: data?.page_size ?? pageSize.value,
      totalPages: data?.total_pages ?? 0,
    }
  })

  const users = computed(() => usersQuery.data.value?.users ?? ([] as UserDto[]))
  const usersAreLoading = computed(() => usersQuery.isLoading.value)

  return {
    users,
    usersAreLoading,
    pagination,
    currentPage,
    pageSize,
    setPage,
    setPageSize,
    refetchUsers: usersQuery.refetch,

  }
})
