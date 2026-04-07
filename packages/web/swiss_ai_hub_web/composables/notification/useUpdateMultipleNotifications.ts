import { type UpdateNotificationRequest, updateNotificationsBulk } from '@core/sdk/client'

export const useUpdateMultipleNotifications = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: ({ ids, payload, tenantId }: { ids: string[], payload: Ref<UpdateNotificationRequest>, tenantId: string }) =>
      updateNotificationsBulk({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: { notification_ids: ids, updates: payload },
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['notifications'] })
    },
  })
})
