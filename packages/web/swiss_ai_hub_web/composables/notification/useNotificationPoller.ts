import { getNotifications, type NotificationDto } from '@core/sdk/client'
import { useQuery, useQueryCache } from '@pinia/colada'
import { useIntervalFn } from '@vueuse/core'
import { useToast } from 'primevue/usetoast'

export const useNotificationPoller = (options?: {
  pollingInterval?: number
  enabled?: boolean
}) => {
  const { tenantName } = useTenant()
  const toast = useToast()
  const queryCache = useQueryCache()

  const knownUnreadIds = ref(new Set<string>())

  const { data: unreadResponse, refetch } = useQuery({
    key: () => ['notifications_poller_data', tenantName.value],
    query: () =>
      getNotifications({
        composable: '$fetch',
        path: { tenant_id: tenantName.value! },
        query: { read: false, page_size: 100 },
      }),
    enabled: computed(() => !!tenantName.value),
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

  const pollingInterval = options?.pollingInterval ?? 30_000
  const enabled = options?.enabled ?? true

  useIntervalFn(() => {
    if (tenantName.value) {
      refetch()
    }
  }, pollingInterval, { immediate: enabled })
}
