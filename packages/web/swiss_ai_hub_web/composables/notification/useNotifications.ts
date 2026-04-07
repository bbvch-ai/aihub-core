import { getNotifications, type PaginatedNotificationsResponse } from '@core/sdk/client'

export const useNotifications = (options: {
  currentPage: Ref<number>
  pageSize: Ref<number>
  filters?: {
    read?: Ref<boolean | undefined>
    done?: Ref<boolean | undefined>
    types?: Ref<string[] | undefined>
    severities?: Ref<string[] | undefined>
  }
}) => {
  const { tenantId } = useTenant()
  const { currentPage, pageSize, filters } = options

  const key = () => [
    'notifications',
    tenantId.value,
    {
      page: currentPage.value,
      pageSize: pageSize.value,
      read: filters?.read?.value,
      done: filters?.done?.value,
      types: filters?.types?.value,
      severities: filters?.severities?.value,
    },
  ]

  const query = useQuery<PaginatedNotificationsResponse>({
    key,
    enabled: computed(() => !!tenantId.value),
    query: () =>
      getNotifications({
        composable: '$fetch',
        path: { tenant_id: tenantId.value! },
        query: {
          page: currentPage.value,
          page_size: pageSize.value,
          read: filters?.read?.value,
          done: filters?.done?.value,
          types: filters?.types?.value,
          severities: filters?.severities?.value,
        },
      }),
  })

  const notifications = computed(() => query.data.value?.notifications ?? [])
  const totalRecords = computed(() => query.data.value?.total ?? 0)

  return {
    notifications,
    isLoading: query.isPending,
    refetch: query.refetch,
    totalRecords,
  }
}
