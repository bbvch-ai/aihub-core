import {
  getNotifications,
  markAllDone,
  markAllRead,
  type NotificationDto,
  type PaginatedNotificationsResponse,
  updateNotification,
  type UpdateNotificationRequest,
} from '@core/sdk/client'
import {defineMutation, defineQuery, useInfiniteQuery, useMutation, useQueryCache} from '@pinia/colada'
import {type Ref} from 'vue'


export const useNotificationsInfinite = defineQuery((options?: {
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
    state,
    loadMore,
    isLoading,
  } = useInfiniteQuery({
    key: () => ['notifications_infinite', types?.value, severities?.value, read?.value, done?.value],
    query: async ({nextPage}) => {
      // The query function receives `nextPage`
      if (nextPage === null) return null

      return getNotifications({
        composable: '$fetch',
        query: {
          page: nextPage,
          page_size: 20,
          types: types?.value,
          severities: severities?.value,
          read: read?.value,
          done: done?.value,
        },
      })
    },
    initialPage: {
      notifications: [] as NotificationDto[],
      nextPage: 1 as number | null,
    },
    merge(accumulated, newData) {
      if (!newData) return accumulated

      return {
        notifications: [...accumulated.notifications, ...newData.notifications],
        nextPage: newData.page < newData.total_pages ? newData.page + 1 : null,
      }
    },
  })

  // 'hasMore' is a computed property, not a direct return value from the hook
  const hasMore = computed(() => state.value?.data?.nextPage !== null)
  const notifications = computed(() => state.value?.data?.notifications ?? [])
  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

  return {
    notifications,
    isLoading,
    hasMore,
    loadMore, // The function is named 'loadMore'
    unreadCount,
  }
})


const updateNotificationInCache = (queryCache: any, updatedNotification: NotificationDto) => {
  queryCache.setQueryData(['notifications_infinite'], (oldData: any) => {
    if (!oldData) return oldData
    return {
      ...oldData,
      pages: oldData.pages.map((page: PaginatedNotificationsResponse) => ({
        ...page,
        notifications: page.notifications.map((notification: NotificationDto) =>
          notification.id === updatedNotification.id ? updatedNotification : notification
        ),
      })),
    }
  })
}

export const useUpdateNotification = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: ({id, payload}: { id: string, payload: UpdateNotificationRequest }) =>
      updateNotification({
        composable: '$fetch',
        path: {notification_id: id},
        body: payload,
      }),
    onSuccess: data => updateNotificationInCache(queryCache, data),
  })
})


export const useMarkAllNotificationsAsRead = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: () => markAllRead({composable: '$fetch'}),
    onSuccess: () => queryCache.invalidateQueries({queryKey: ['notifications_infinite']}),
  })
})


export const useMarkAllNotificationsAsDone = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: () => markAllDone({composable: '$fetch'}),
    onSuccess: () => queryCache.invalidateQueries({queryKey: ['notifications_infinite']}),
  })
})
