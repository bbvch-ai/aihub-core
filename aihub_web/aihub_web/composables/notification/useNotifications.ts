import {
  getNotifications,
  markAllDone,
  markAllRead,
  updateNotification,
  type UpdateNotificationRequest,
} from '@core/sdk/client'
import {defineMutation, defineQuery, useMutation, useQueryCache} from '@pinia/colada'
import {type Ref} from 'vue'


export const useNotifications = defineQuery((options?: {
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
  } = useQuery({
    key: () => ['notifications'],
    query: async () => {
      return getNotifications({
        composable: '$fetch',
        query: {
          page: 1,
          page_size: 10,
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
})


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


export const useMarkAllNotificationsAsRead = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: () => markAllRead({composable: '$fetch'}),
    onSuccess: () => queryCache.invalidateQueries({key: ['notifications']}),
  })
})


export const useMarkAllNotificationsAsDone = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: () => markAllDone({composable: '$fetch'}),
    onSuccess: () => queryCache.invalidateQueries({key: ['notifications']}),
  })
})
