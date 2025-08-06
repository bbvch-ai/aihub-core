import { getNotifications, type NotificationDto } from '@core/sdk/client'
import { useQuery, useQueryCache } from '@pinia/colada'
import { useToast } from 'primevue/usetoast'

export const useNotificationPoller = (options?: {
  pollingInterval?: number
  enabled?: boolean
}) => {
  const toast = useToast()
  const queryCache = useQueryCache()

  const knownUnreadIds = ref(new Set<string>())

  const { data: unreadResponse, refetch } = useQuery({
    key: () => ['notifications_poller_data'],
    query: () =>
      getNotifications({
        composable: '$fetch',
        query: { read: false, page_size: 100 },
      }),
    enabled: false,
  })

  watch(unreadResponse, (newData) => {
    const newNotifications = newData?.notifications
    if (!newNotifications) return

    let hasNew = false
    newNotifications.forEach((notification: NotificationDto) => {
      if (!knownUnreadIds.value.has(notification.id)) {
        hasNew = true
        toast.add({
          severity: notification.type,
          summary: notification.title,
          detail: notification.message,
          life: 5000,
        })
      }
    })

    knownUnreadIds.value = new Set(newNotifications.map(n => n.id))

    if (hasNew) {
      queryCache.invalidateQueries({ key: ['notifications'] })
    }
  })

  const pollingInterval = options?.pollingInterval ?? 30_000 // Default 30 seconds
  const enabled = options?.enabled ?? true

  onMounted(() => {
    if (!enabled) return

    const intervalId = setInterval(() => {
      refetch()
    }, pollingInterval)

    onUnmounted(() => {
      clearInterval(intervalId)
    })
  })
}
