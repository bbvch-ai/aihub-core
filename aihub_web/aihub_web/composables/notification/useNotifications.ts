import {
  getNotifications,
  type PaginatedNotificationsResponse,
  updateNotification,
  type UpdateNotificationRequest,
  updateNotificationsBulk,
} from '@core/sdk/client'
import {defineMutation, defineQuery, useMutation, useQueryCache} from '@pinia/colada'
import {type Ref} from 'vue'


export const useNotifications = (options?: {
  types?: Ref<string[] | undefined>,
  severities?: Ref<string[] | undefined>,
  read?: Ref<boolean | undefined>,
  done?: Ref<boolean | undefined>,
}) => {
  const types = options?.types
  const severities = options?.severities
  const read = options?.read
  const done = options?.done

  const {
    data: paginatedResponse,
    isPending: isLoading,
    refetch,
  } = useQuery<PaginatedNotificationsResponse>({
    key: () => ['notifications', types?.value, severities?.value, read?.value, done?.value],
    query: () => {
      return getNotifications({
        composable: '$fetch',
        query: {
          page: 1,
          page_size: 100,
          types: types?.value,
          severities: severities?.value,
          read: read?.value,
          done: done?.value,
        },
      })
    },
  })

  const notifications = computed(() => paginatedResponse.value?.notifications ?? [])

  return {
    notifications,
    isLoading,
    refetch,
  }
}


export const useUpdateNotification = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: ({id, payload}: { id: string, payload: Ref<UpdateNotificationRequest> }) =>
      updateNotification({
        composable: '$fetch',
        path: {notification_id: id},
        body: payload,
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({key: ['notifications']})
    },
  })
})


export const useUpdateMultipleNotifications = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: ({ids, payload}: { ids: string[], payload: Ref<UpdateNotificationRequest> }) =>
      updateNotificationsBulk({
        composable: '$fetch',
        body: {notification_ids: ids, updates: payload}
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({key: ['notifications']})
    },
  })
})


export const usePaginatedNotifications = defineQuery(() => {
  const currentPage = ref(1)
  const pageSize = ref(10)

  const query = useQuery({
    key: () => ['notifications_paginated', currentPage.value, pageSize.value],
    query: () => getNotifications({
      composable: '$fetch',
      query: {
        page: currentPage.value,
        page_size: pageSize.value,
      },
    }),
  })

  const notifications = computed(() => query.data.value?.notifications ?? [])
  const totalRecords = computed(() => query.data.value?.total ?? 0)

  const setPage = (newPage: number) => {
    currentPage.value = newPage
  }

  return {
    notifications,
    isLoading: query.isPending,
    refetch: query.refetch,
    totalRecords,
    pageSize,
    setPage,
  }
})
