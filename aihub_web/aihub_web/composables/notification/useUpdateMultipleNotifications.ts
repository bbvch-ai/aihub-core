import { type UpdateNotificationRequest, updateNotificationsBulk } from '@core/sdk/client'

import type { Ref } from 'vue'

export const useUpdateMultipleNotifications = defineMutation(() => {
  const queryCache = useQueryCache()
  return useMutation({
    mutation: ({ ids, payload }: { ids: string[], payload: Ref<UpdateNotificationRequest> }) =>
      updateNotificationsBulk({
        composable: '$fetch',
        body: { notification_ids: ids, updates: payload },
      }),
    onSuccess: () => {
      queryCache.invalidateQueries({ key: ['notifications'] })
    },
  })
})
