import { updateNotification, type UpdateNotificationRequest } from '@core/sdk/client'

export const useUpdateNotification = defineMutation(() => {
  const queryCache = useQueryCache()
  const { tenantId } = useTenant()
  return useMutation({
    mutation: ({ id, payload, tenantId }: { id: string, payload: Ref<UpdateNotificationRequest>, tenantId: string }) =>
      updateNotification({
        composable: '$fetch',
        path: { tenant_id: tenantId, notification_id: id },
        body: payload,
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['tenant', tenantId.value, 'notifications'] })
    },
  })
})
