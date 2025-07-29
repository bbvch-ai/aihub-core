import { getNotifications, type PaginatedNotificationsResponse } from '@core/sdk/client'

import type { Ref } from 'vue'

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
  const { currentPage, pageSize, filters } = options

  const query = useQuery<PaginatedNotificationsResponse>({
    key: () => {
      const keyArray = [
        'notifications',
        currentPage.value,
        pageSize.value,
        ...(filters?.read?.value !== undefined ? ['read', filters.read.value] : []),
        ...(filters?.done?.value !== undefined ? ['done', filters.done.value] : []),
        ...(filters?.types?.value ? ['types', ...filters.types.value] : []),
        ...(filters?.severities?.value ? ['severities', ...filters.severities.value] : []),
      ]
      return keyArray
    },
    query: () => getNotifications({
      composable: '$fetch',
      query: {
        page: currentPage.value,
        page_size: pageSize.value,
        types: filters?.types?.value,
        severities: filters?.severities?.value,
        read: filters?.read?.value,
        done: filters?.done?.value,
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
